import io
import json
import os
import zipfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from lxml import etree
from config import Config
from nfe.builder import NFeBuilder
from nfe.danfe import DANFEGenerator
from nfe.csv_parser import validar_csv, agrupar_por_nota, parsear_nota
from nfe.utils import CODIGOS_UF

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

HISTORICO_PATH = os.path.join(os.path.dirname(__file__), 'historico_nfe.json')
NUMERO_PATH = os.path.join(os.path.dirname(__file__), 'proximo_numero.json')


def carregar_historico():
    if os.path.exists(HISTORICO_PATH):
        with open(HISTORICO_PATH, 'r') as f:
            return json.load(f)
    return []


def salvar_historico(historico):
    with open(HISTORICO_PATH, 'w') as f:
        json.dump(historico, f, indent=2, ensure_ascii=False)


def proximo_numero():
    if os.path.exists(NUMERO_PATH):
        with open(NUMERO_PATH, 'r') as f:
            data = json.load(f)
            return data.get('proximo', Config.NFE_PROXIMO_NUMERO)
    return Config.NFE_PROXIMO_NUMERO


def salvar_proximo_numero(num):
    with open(NUMERO_PATH, 'w') as f:
        json.dump({'proximo': num}, f)


def gerar_nfe_xml(numero, destinatario, produtos, transporte, pagamento,
                  info_adicionais='', emitente=None, ambiente='1'):
    emit = emitente or Config.emitente()
    builder = NFeBuilder(emit, ambiente=ambiente, serie=Config.NFE_SERIE)
    nfe_xml = builder.build(numero, destinatario, produtos, transporte, pagamento, info_adicionais)
    chave_acesso = builder.chave_acesso

    os.makedirs(Config.XMLS_DIR, exist_ok=True)
    xml_path = os.path.join(Config.XMLS_DIR, f'NFe_{chave_acesso}.xml')
    with open(xml_path, 'wb') as f:
        f.write(etree.tostring(nfe_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

    v_nf = sum(float(p['valor_total']) for p in produtos)

    dados_danfe = {
        'emitente': emit,
        'destinatario': destinatario,
        'ide': {
            'numero': numero,
            'serie': Config.NFE_SERIE,
            'tipo_operacao': destinatario.get('tipo_operacao', '1'),
            'data_emissao': datetime.now().strftime('%d/%m/%Y'),
        },
        'produtos': produtos,
        'totais': {
            'v_bc': sum(float(p.get('icms_base', p['valor_total'])) for p in produtos),
            'v_icms': sum(float(p.get('icms_valor', 0)) for p in produtos),
            'v_prod': v_nf,
            'v_frete': 0,
            'v_desc': 0,
            'v_outros': 0,
            'v_pis': sum(float(p.get('pis_valor', 0)) for p in produtos),
            'v_cofins': sum(float(p.get('cofins_valor', 0)) for p in produtos),
            'v_nf': v_nf,
        },
        'transporte': transporte,
        'info_adicionais': info_adicionais,
    }

    danfe_path = ''
    try:
        danfe = DANFEGenerator(Config.DANFES_DIR)
        danfe_path = danfe.gerar(dados_danfe, chave_acesso)
    except Exception:
        pass

    registro = {
        'numero': numero,
        'serie': Config.NFE_SERIE,
        'chave_acesso': chave_acesso,
        'data': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'destinatario': destinatario['razao_social'],
        'emitente': emit.get('razao_social', ''),
        'ambiente': ambiente,
        'valor': v_nf,
        'xml_path': xml_path,
        'danfe_path': danfe_path,
    }

    historico = carregar_historico()
    historico.append(registro)
    salvar_historico(historico)

    return registro


@app.route('/')
def index():
    historico = carregar_historico()
    ultimas = historico[-10:][::-1]
    return render_template('index.html',
                           config=Config,
                           ultimas_nfes=ultimas,
                           proximo_numero=proximo_numero())


@app.route('/emitir', methods=['GET', 'POST'])
def emitir():
    if request.method == 'GET':
        return render_template('emitir.html',
                               config=Config,
                               proximo_numero=proximo_numero(),
                               codigos_uf=CODIGOS_UF)

    try:
        numero = int(request.form['numero'])

        destinatario = {
            'cnpj_cpf': request.form['dest_cnpj_cpf'],
            'razao_social': request.form['dest_razao_social'],
            'ie': request.form.get('dest_ie', ''),
            'ind_ie_dest': request.form.get('dest_ind_ie', '9'),
            'email': request.form.get('dest_email', ''),
            'logradouro': request.form['dest_logradouro'],
            'numero': request.form['dest_numero'],
            'complemento': request.form.get('dest_complemento', ''),
            'bairro': request.form['dest_bairro'],
            'cod_municipio': request.form['dest_cod_municipio'],
            'municipio': request.form['dest_municipio'],
            'uf': request.form['dest_uf'],
            'cep': request.form.get('dest_cep', ''),
            'telefone': request.form.get('dest_telefone', ''),
            'natureza_operacao': request.form.get('natureza_operacao', 'VENDA DE MERCADORIA'),
            'tipo_operacao': request.form.get('tipo_operacao', '1'),
            'finalidade': request.form.get('finalidade', '1'),
            'consumidor_final': request.form.get('consumidor_final', '0'),
            'presenca': request.form.get('presenca', '1'),
        }

        qtd_produtos = int(request.form.get('qtd_produtos', 1))
        produtos = []
        for i in range(1, qtd_produtos + 1):
            prefix = f'prod_{i}_'
            vl_unit = float(request.form.get(f'{prefix}valor_unitario', 0))
            qtd = float(request.form.get(f'{prefix}quantidade', 0))
            vl_total = round(vl_unit * qtd, 2)

            icms_base = vl_total
            icms_aliq = float(request.form.get(f'{prefix}icms_aliquota', 0))
            icms_valor = round(icms_base * icms_aliq / 100, 2)

            pis_cst = request.form.get(f'{prefix}pis_cst', '07')
            pis_aliq = float(request.form.get(f'{prefix}pis_aliquota', 0))
            pis_valor = round(vl_total * pis_aliq / 100, 2) if pis_cst in ('01', '02') else 0

            cofins_cst = request.form.get(f'{prefix}cofins_cst', '07')
            cofins_aliq = float(request.form.get(f'{prefix}cofins_aliquota', 0))
            cofins_valor = round(vl_total * cofins_aliq / 100, 2) if cofins_cst in ('01', '02') else 0

            prod = {
                'codigo': request.form.get(f'{prefix}codigo', str(i)),
                'descricao': request.form[f'{prefix}descricao'],
                'ncm': request.form[f'{prefix}ncm'],
                'cfop': request.form[f'{prefix}cfop'],
                'unidade': request.form.get(f'{prefix}unidade', 'UN'),
                'quantidade': qtd,
                'valor_unitario': vl_unit,
                'valor_total': vl_total,
                'ean': request.form.get(f'{prefix}ean', 'SEM GTIN'),
                'icms_orig': request.form.get(f'{prefix}icms_orig', '0'),
                'icms_cst': request.form.get(f'{prefix}icms_cst', '00'),
                'icms_csosn': request.form.get(f'{prefix}icms_csosn', ''),
                'icms_base': icms_base,
                'icms_aliquota': icms_aliq,
                'icms_valor': icms_valor,
                'pis_cst': pis_cst,
                'pis_aliquota': pis_aliq,
                'pis_valor': pis_valor,
                'cofins_cst': cofins_cst,
                'cofins_aliquota': cofins_aliq,
                'cofins_valor': cofins_valor,
            }
            if request.form.get(f'{prefix}cest'):
                prod['cest'] = request.form[f'{prefix}cest']

            produtos.append(prod)

        transporte = {
            'mod_frete': request.form.get('mod_frete', '9'),
            'transportadora_cnpj': request.form.get('transp_cnpj', ''),
            'transportadora_nome': request.form.get('transp_nome', ''),
            'transportadora_uf': request.form.get('transp_uf', ''),
            'volumes_qtd': request.form.get('volumes_qtd', ''),
            'volumes_especie': request.form.get('volumes_especie', ''),
            'volumes_peso_liq': request.form.get('volumes_peso_liq', ''),
            'volumes_peso_bruto': request.form.get('volumes_peso_bruto', ''),
        }

        forma_pgto = request.form.get('forma_pagamento', '01')
        if forma_pgto == '90':
            valor_pgto = 0
        else:
            valor_pgto_form = request.form.get('valor_pagamento', '').strip()
            if valor_pgto_form:
                valor_pgto = float(valor_pgto_form)
            else:
                valor_pgto = sum(float(p['valor_total']) for p in produtos)

        pagamento = {'forma': forma_pgto, 'valor': valor_pgto}
        info_adicionais = request.form.get('info_adicionais', '')
        ambiente = request.form.get('ambiente', '1')

        registro = gerar_nfe_xml(numero, destinatario, produtos, transporte, pagamento,
                                 info_adicionais, ambiente=ambiente)
        salvar_proximo_numero(numero + 1)

        return render_template('resultado.html',
                               titulo='XML gerado com sucesso',
                               registro=registro,
                               config=Config)

    except Exception as e:
        flash(f'Erro ao gerar XML: {str(e)}', 'danger')
        return redirect(url_for('emitir'))


@app.route('/importar-csv', methods=['GET', 'POST'])
def importar_csv():
    if request.method == 'GET':
        return render_template('importar_csv.html', config=Config)

    arquivo = request.files.get('arquivo_csv')
    if not arquivo or not arquivo.filename:
        flash('Selecione um arquivo CSV', 'danger')
        return redirect(url_for('importar_csv'))

    try:
        conteudo = arquivo.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            arquivo.seek(0)
            conteudo = arquivo.read().decode('latin-1')
        except Exception:
            flash('Nao foi possivel ler o arquivo. Use codificacao UTF-8.', 'danger')
            return redirect(url_for('importar_csv'))

    linhas, erro = validar_csv(conteudo)
    if erro:
        flash(f'Erro no CSV: {erro}', 'danger')
        return redirect(url_for('importar_csv'))

    notas_agrupadas = agrupar_por_nota(linhas)
    notas_parseadas = {}
    for num, linhas_nota in sorted(notas_agrupadas.items(), key=lambda x: int(x[0])):
        try:
            notas_parseadas[num] = parsear_nota(num, linhas_nota)
        except Exception as e:
            flash(f'Erro ao processar nota {num}: {str(e)}', 'danger')
            return redirect(url_for('importar_csv'))

    acao = request.form.get('acao', 'validar')

    if acao == 'validar':
        preview = []
        for num, nota in notas_parseadas.items():
            preview.append({
                'numero': nota['numero'],
                'destinatario': nota['destinatario']['razao_social'],
                'cnpj_cpf': nota['destinatario']['cnpj_cpf'],
                'qtd_produtos': len(nota['produtos']),
                'valor_total': sum(p['valor_total'] for p in nota['produtos']),
            })
        flash(f'CSV validado com sucesso! {len(preview)} nota(s) pronta(s) para gerar.', 'success')
        return render_template('importar_csv.html', config=Config, preview=preview)

    resultados = []
    maior_numero = 0
    for num, nota in notas_parseadas.items():
        try:
            registro = gerar_nfe_xml(
                nota['numero'],
                nota['destinatario'],
                nota['produtos'],
                nota['transporte'],
                nota['pagamento'],
                nota['info_adicionais'],
                emitente=nota.get('emitente'),
                ambiente=nota.get('ambiente') or '1',
            )
            resultados.append(registro)
            if nota['numero'] > maior_numero:
                maior_numero = nota['numero']
        except Exception as e:
            resultados.append({
                'numero': nota['numero'],
                'destinatario': nota['destinatario']['razao_social'],
                'valor': sum(p['valor_total'] for p in nota['produtos']),
                'erro': str(e),
                'chave_acesso': '',
            })

    if maior_numero > 0:
        salvar_proximo_numero(maior_numero + 1)

    gerados = sum(1 for r in resultados if r.get('chave_acesso'))
    total = len(resultados)
    if gerados == total:
        flash(f'Todos os {total} XML(s) gerado(s) com sucesso!', 'success')
    elif gerados > 0:
        flash(f'{gerados} de {total} XML(s) gerado(s). Verifique os erros abaixo.', 'warning')
    else:
        flash(f'Nenhum XML gerado. Verifique os erros abaixo.', 'danger')

    chaves = [r['chave_acesso'] for r in resultados if r.get('chave_acesso')]

    return render_template('importar_csv.html',
                           config=Config,
                           resultados=resultados,
                           chaves_zip=chaves)


@app.route('/modelo-csv')
def download_modelo_csv():
    filepath = os.path.join(os.path.dirname(__file__), 'modelo_nfe.csv')
    return send_file(filepath, as_attachment=True, download_name='modelo_nfe.csv')


@app.route('/guia-campos')
def download_guia_campos():
    filepath = os.path.join(os.path.dirname(__file__), 'CAMPOS_CSV.md')
    return send_file(filepath, as_attachment=True, download_name='GUIA_CAMPOS_CSV.md')


@app.route('/referencia-campos-csv')
def download_referencia_csv():
    filepath = os.path.join(os.path.dirname(__file__), 'REFERENCIA_CAMPOS_CSV.csv')
    return send_file(filepath, as_attachment=True, download_name='REFERENCIA_CAMPOS_CSV.csv')


@app.route('/xml/<chave>')
def download_xml(chave):
    filepath = os.path.join(Config.XMLS_DIR, f'NFe_{chave}.xml')
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    flash('XML nao encontrado', 'danger')
    return redirect(url_for('index'))


@app.route('/danfe/<chave>')
def download_danfe(chave):
    filepath = os.path.join(Config.DANFES_DIR, f'DANFE_{chave}.pdf')
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    flash('DANFE (previa) nao encontrado', 'danger')
    return redirect(url_for('index'))


@app.route('/zip', methods=['POST'])
def download_zip():
    chaves = request.form.getlist('chaves')
    if not chaves:
        flash('Nenhuma nota selecionada', 'warning')
        return redirect(url_for('index'))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for chave in chaves:
            xml_path = os.path.join(Config.XMLS_DIR, f'NFe_{chave}.xml')
            if os.path.exists(xml_path):
                zf.write(xml_path, f'NFe_{chave}.xml')
    buffer.seek(0)

    nome_zip = f'NFes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    return send_file(buffer, as_attachment=True, download_name=nome_zip, mimetype='application/zip')


@app.template_filter('fmt_valor')
def fmt_valor(value):
    try:
        return f'{float(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return '0,00'


@app.template_filter('fmt_cnpj')
def fmt_cnpj(cnpj):
    cnpj = str(cnpj).zfill(14)
    return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'


@app.template_filter('fmt_chave')
def fmt_chave(chave):
    return ' '.join(chave[i:i+4] for i in range(0, len(chave), 4))


if __name__ == '__main__':
    os.makedirs(Config.XMLS_DIR, exist_ok=True)
    os.makedirs(Config.DANFES_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)

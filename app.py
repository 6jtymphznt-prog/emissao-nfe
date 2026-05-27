import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from lxml import etree
from config import Config
from nfe.builder import NFeBuilder
from nfe.signer import NFeSigner
from nfe.transmitter import NFeTransmitter
from nfe.danfe import DANFEGenerator
from nfe.csv_parser import validar_csv, agrupar_por_nota, parsear_nota
from nfe.utils import CODIGOS_UF, UF_POR_CODIGO

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


def get_signer():
    return NFeSigner(Config.CERT_PFX_PATH, Config.CERT_PFX_PASSWORD)


def get_transmitter(signer):
    return NFeTransmitter(Config.EMIT_UF, Config.NFE_AMBIENTE, signer)


@app.route('/')
def index():
    historico = carregar_historico()
    ultimas = historico[-10:][::-1]
    return render_template('index.html',
                           config=Config,
                           ultimas_nfes=ultimas,
                           proximo_numero=proximo_numero())


@app.route('/status')
def status_servico():
    try:
        signer = get_signer()
        transmitter = get_transmitter(signer)
        resultado = transmitter.status_servico()
        return render_template('resultado.html',
                               titulo='Status do Servico SEFAZ',
                               resultado=resultado,
                               config=Config)
    except Exception as e:
        flash(f'Erro ao consultar status: {str(e)}', 'danger')
        return redirect(url_for('index'))


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

        pagamento = {
            'forma': request.form.get('forma_pagamento', '01'),
            'valor': sum(float(p['valor_total']) for p in produtos),
        }

        info_adicionais = request.form.get('info_adicionais', '')

        registro = emitir_nota(numero, destinatario, produtos, transporte, pagamento, info_adicionais)
        salvar_proximo_numero(numero + 1)

        resultado = {
            'cStat': registro['status'],
            'xMotivo': registro['motivo'],
            'nProt': registro['protocolo'],
            'chNFe': registro['chave_acesso'],
        }

        return render_template('resultado.html',
                               titulo='Resultado da Emissao',
                               resultado=resultado,
                               registro=registro,
                               config=Config)

    except FileNotFoundError:
        flash('Certificado digital nao encontrado. Verifique o caminho no .env', 'danger')
        return redirect(url_for('emitir'))
    except Exception as e:
        flash(f'Erro na emissao: {str(e)}', 'danger')
        return redirect(url_for('emitir'))


def emitir_nota(numero, destinatario, produtos, transporte, pagamento, info_adicionais=''):
    builder = NFeBuilder(Config.emitente(), Config.NFE_AMBIENTE, Config.NFE_SERIE)
    nfe_xml = builder.build(numero, destinatario, produtos, transporte, pagamento, info_adicionais)
    chave_acesso = builder.chave_acesso

    os.makedirs(Config.XMLS_DIR, exist_ok=True)
    xml_path = os.path.join(Config.XMLS_DIR, f'NFe_{chave_acesso}_sem_assinatura.xml')
    with open(xml_path, 'wb') as f:
        f.write(etree.tostring(nfe_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

    signer = get_signer()
    nfe_signed = signer.sign_nfe(nfe_xml)

    xml_signed_path = os.path.join(Config.XMLS_DIR, f'NFe_{chave_acesso}_assinada.xml')
    with open(xml_signed_path, 'wb') as f:
        f.write(etree.tostring(nfe_signed, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

    transmitter = get_transmitter(signer)
    resultado = transmitter.autorizar(nfe_signed)

    protocolo = resultado.get('nProt', '')
    status = resultado.get('cStat', '')
    motivo = resultado.get('xMotivo', '')

    if status == '100':
        nfe_proc_path = os.path.join(Config.XMLS_DIR, f'NFe_{chave_acesso}_autorizada.xml')
        with open(nfe_proc_path, 'wb') as f:
            f.write(etree.tostring(nfe_signed, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

    v_nf = sum(float(p['valor_total']) for p in produtos)

    dados_danfe = {
        'emitente': Config.emitente(),
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
        danfe_path = danfe.gerar(dados_danfe, chave_acesso, protocolo)
    except Exception:
        pass

    registro = {
        'numero': numero,
        'serie': Config.NFE_SERIE,
        'chave_acesso': chave_acesso,
        'protocolo': protocolo,
        'status': status,
        'motivo': motivo,
        'data': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'destinatario': destinatario['razao_social'],
        'valor': v_nf,
        'danfe_path': danfe_path,
    }

    historico = carregar_historico()
    historico.append(registro)
    salvar_historico(historico)

    return registro


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
        flash(f'CSV validado com sucesso! {len(preview)} nota(s) pronta(s) para emissao.', 'success')
        return render_template('importar_csv.html', config=Config, preview=preview)

    resultados = []
    maior_numero = 0
    for num, nota in notas_parseadas.items():
        try:
            registro = emitir_nota(
                nota['numero'],
                nota['destinatario'],
                nota['produtos'],
                nota['transporte'],
                nota['pagamento'],
                nota['info_adicionais'],
            )
            resultados.append(registro)
            if nota['numero'] > maior_numero:
                maior_numero = nota['numero']
        except Exception as e:
            resultados.append({
                'numero': nota['numero'],
                'destinatario': nota['destinatario']['razao_social'],
                'valor': sum(p['valor_total'] for p in nota['produtos']),
                'status': 'ERRO',
                'motivo': str(e),
                'protocolo': '',
                'chave_acesso': '',
            })

    if maior_numero > 0:
        salvar_proximo_numero(maior_numero + 1)

    autorizadas = sum(1 for r in resultados if r.get('status') == '100')
    total = len(resultados)
    if autorizadas == total:
        flash(f'Todas as {total} nota(s) foram autorizadas com sucesso!', 'success')
    elif autorizadas > 0:
        flash(f'{autorizadas} de {total} nota(s) autorizada(s). Verifique os erros abaixo.', 'warning')
    else:
        flash(f'Nenhuma nota foi autorizada. Verifique os erros abaixo.', 'danger')

    return render_template('importar_csv.html', config=Config, resultados=resultados)


@app.route('/modelo-csv')
def download_modelo_csv():
    filepath = os.path.join(os.path.dirname(__file__), 'modelo_nfe.csv')
    return send_file(filepath, as_attachment=True, download_name='modelo_nfe.csv')


@app.route('/consultar', methods=['GET', 'POST'])
def consultar():
    if request.method == 'GET':
        return render_template('consultar.html', config=Config)

    chave = request.form.get('chave_acesso', '').replace(' ', '')
    if len(chave) != 44:
        flash('Chave de acesso deve ter 44 digitos', 'danger')
        return redirect(url_for('consultar'))

    try:
        signer = get_signer()
        transmitter = get_transmitter(signer)
        resultado = transmitter.consultar_protocolo(chave)
        return render_template('resultado.html',
                               titulo='Consulta de NFe',
                               resultado=resultado,
                               config=Config)
    except Exception as e:
        flash(f'Erro na consulta: {str(e)}', 'danger')
        return redirect(url_for('consultar'))


@app.route('/cancelar', methods=['GET', 'POST'])
def cancelar():
    if request.method == 'GET':
        return render_template('cancelar.html', config=Config)

    chave = request.form.get('chave_acesso', '').replace(' ', '')
    protocolo = request.form.get('protocolo', '')
    justificativa = request.form.get('justificativa', '')

    if len(chave) != 44:
        flash('Chave de acesso deve ter 44 digitos', 'danger')
        return redirect(url_for('cancelar'))
    if len(justificativa) < 15:
        flash('Justificativa deve ter no minimo 15 caracteres', 'danger')
        return redirect(url_for('cancelar'))

    try:
        signer = get_signer()
        transmitter = get_transmitter(signer)
        resultado = transmitter.cancelar(chave, protocolo, justificativa, Config.EMIT_CNPJ)
        return render_template('resultado.html',
                               titulo='Cancelamento de NFe',
                               resultado=resultado,
                               config=Config)
    except Exception as e:
        flash(f'Erro no cancelamento: {str(e)}', 'danger')
        return redirect(url_for('cancelar'))


@app.route('/danfe/<chave>')
def download_danfe(chave):
    filepath = os.path.join(Config.DANFES_DIR, f'DANFE_{chave}.pdf')
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    flash('DANFE nao encontrado', 'danger')
    return redirect(url_for('index'))


@app.route('/diagnostico')
def diagnostico():
    resultados = []

    # 1. Verificar se o arquivo do certificado existe
    cert_path = Config.CERT_PFX_PATH
    cert_existe = os.path.exists(cert_path)
    resultados.append({
        'teste': 'Arquivo do certificado',
        'detalhe': cert_path,
        'ok': cert_existe,
        'msg': 'Encontrado' if cert_existe else 'Arquivo NAO encontrado. Verifique o caminho no .env',
    })

    if not cert_existe:
        return render_template('diagnostico.html', config=Config, resultados=resultados)

    # 2. Verificar se consegue abrir o certificado com a senha
    cert_info = {}
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        with open(cert_path, 'rb') as f:
            pfx_data = f.read()
        private_key, certificate, additional = pkcs12.load_key_and_certificates(
            pfx_data, Config.CERT_PFX_PASSWORD.encode()
        )
        cert_info['subject'] = certificate.subject.rfc4514_string()
        cert_info['issuer'] = certificate.issuer.rfc4514_string()
        cert_info['validade_inicio'] = certificate.not_valid_before_utc.strftime('%d/%m/%Y %H:%M')
        cert_info['validade_fim'] = certificate.not_valid_after_utc.strftime('%d/%m/%Y %H:%M')

        from datetime import datetime, timezone
        agora = datetime.now(timezone.utc)
        vencido = agora > certificate.not_valid_after_utc
        ainda_nao_valido = agora < certificate.not_valid_before_utc

        qtd_cadeia_pfx = len(additional) if additional else 0

        try:
            signer_test = get_signer()
            qtd_cadeia_total = signer_test.chain_count
        except Exception:
            qtd_cadeia_total = qtd_cadeia_pfx

        cert_info['qtd_cadeia'] = qtd_cadeia_total

        if qtd_cadeia_pfx > 0:
            detalhe_cadeia = f'{qtd_cadeia_pfx} intermediario(s) no PFX'
        elif qtd_cadeia_total > 0:
            detalhe_cadeia = f'{qtd_cadeia_total} intermediario(s) baixado(s) automaticamente da internet'
        else:
            detalhe_cadeia = 'Nenhum intermediario encontrado (pode causar erro de conexao)'

        resultados.append({
            'teste': 'Senha do certificado',
            'detalhe': detalhe_cadeia,
            'ok': True,
            'msg': 'Senha correta',
        })

        resultados.append({
            'teste': 'Titular do certificado',
            'detalhe': cert_info['subject'],
            'ok': True,
            'msg': cert_info['subject'],
        })

        resultados.append({
            'teste': 'Validade do certificado',
            'detalhe': f"De {cert_info['validade_inicio']} ate {cert_info['validade_fim']}",
            'ok': not vencido and not ainda_nao_valido,
            'msg': 'VENCIDO!' if vencido else ('Ainda nao esta valido' if ainda_nao_valido else 'Dentro da validade'),
        })
    except Exception as e:
        resultados.append({
            'teste': 'Senha do certificado',
            'detalhe': str(e),
            'ok': False,
            'msg': 'Senha INCORRETA ou arquivo corrompido. Verifique CERT_PFX_PASSWORD no .env',
        })
        return render_template('diagnostico.html', config=Config, resultados=resultados, cert_info=cert_info)

    # 3. Verificar URLs SEFAZ
    from nfe.sefaz_urls import obter_urls_sefaz
    urls = obter_urls_sefaz(Config.EMIT_UF, Config.NFE_AMBIENTE)
    url_status = urls.get('NfeStatusServico', '')
    resultados.append({
        'teste': 'URL SEFAZ Status',
        'detalhe': url_status,
        'ok': bool(url_status),
        'msg': f'UF={Config.EMIT_UF} Ambiente={"Homologacao" if Config.NFE_AMBIENTE == "2" else "Producao"}',
    })

    # 4. Verificar proxy da rede
    import os as _os
    proxy_http = _os.environ.get('HTTP_PROXY', _os.environ.get('http_proxy', ''))
    proxy_https = _os.environ.get('HTTPS_PROXY', _os.environ.get('https_proxy', ''))
    if proxy_http or proxy_https:
        resultados.append({
            'teste': 'Proxy detectado',
            'detalhe': f'HTTP={proxy_http or "nenhum"} HTTPS={proxy_https or "nenhum"}',
            'ok': True,
            'msg': 'Proxy configurado no sistema',
        })

    # 5. Testar conexao SEM certificado
    import requests as req
    try:
        resp = req.get(url_status, timeout=15, verify=True)
        resultados.append({
            'teste': 'Rede ate SEFAZ (sem certificado)',
            'detalhe': f'HTTP {resp.status_code}',
            'ok': True,
            'msg': 'Rede OK.',
        })
    except req.exceptions.SSLError:
        resultados.append({
            'teste': 'Rede ate SEFAZ (sem certificado)',
            'detalhe': 'SEFAZ respondeu pedindo certificado (normal)',
            'ok': True,
            'msg': 'Rede OK.',
        })
    except req.exceptions.ConnectionError:
        resultados.append({
            'teste': 'Rede ate SEFAZ (sem certificado)',
            'detalhe': 'Sem conexao',
            'ok': False,
            'msg': 'Sem acesso a internet ou SEFAZ fora do ar.',
        })
    except Exception as e:
        resultados.append({
            'teste': 'Rede ate SEFAZ (sem certificado)',
            'detalhe': str(e)[:200],
            'ok': False,
            'msg': str(e)[:100],
        })

    # 6. Testar download dos intermediarios
    try:
        from cryptography.x509.oid import AuthorityInformationAccessOID, ExtensionOID
        aia = certificate.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS)
        ca_urls = [
            desc.access_location.value
            for desc in aia.value
            if desc.access_method == AuthorityInformationAccessOID.CA_ISSUERS
        ]
        if ca_urls:
            try:
                resp_aia = req.get(ca_urls[0], timeout=10)
                resp_aia.raise_for_status()
                resultados.append({
                    'teste': 'Download certificado intermediario',
                    'detalhe': f'{ca_urls[0]} => HTTP {resp_aia.status_code} ({len(resp_aia.content)} bytes)',
                    'ok': True,
                    'msg': 'Download OK',
                })
            except Exception as e:
                resultados.append({
                    'teste': 'Download certificado intermediario',
                    'detalhe': f'URL: {ca_urls[0]} Erro: {str(e)[:200]}',
                    'ok': False,
                    'msg': 'Falhou - rede da empresa pode estar bloqueando',
                })
        else:
            resultados.append({
                'teste': 'Download certificado intermediario',
                'detalhe': 'Certificado nao possui URL de intermediarios (AIA)',
                'ok': False,
                'msg': 'Sem URL de intermediarios',
            })
    except Exception as e:
        resultados.append({
            'teste': 'Download certificado intermediario',
            'detalhe': str(e)[:200],
            'ok': False,
            'msg': f'Erro ao ler extensao AIA: {str(e)[:100]}',
        })

    # 7. Testar conexao COM certificado - multiplas abordagens
    import ssl
    import certifi
    from nfe.transmitter import SefazTLSAdapter

    signer = get_signer()
    cert_pem, key_pem = signer.get_cert_key_temp_files()

    def _test_connection(label, session_factory):
        try:
            session = session_factory()
            resp = session.post(
                url_status,
                data=b'<test/>',
                headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
                timeout=15,
            )
            return True, f'HTTP {resp.status_code}', f'Conexao OK (HTTP {resp.status_code})'
        except req.exceptions.SSLError as e:
            err = str(e)
            if 'CERTIFICATE_REQUIRED' in err or 'certificate required' in err.lower():
                return False, err[:300], 'SEFAZ recusou o certificado'
            return False, err[:300], 'Erro SSL/TLS'
        except req.exceptions.ConnectionError as e:
            return False, str(e)[:300], 'Conexao recusada'
        except Exception as e:
            return False, str(e)[:300], str(e)[:100]

    # Teste A: TLS 1.2 + certificado (padrao)
    def factory_tls12():
        s = req.Session()
        s.mount('https://', SefazTLSAdapter(cert_pem, key_pem))
        return s
    ok, det, msg = _test_connection('TLS 1.2', factory_tls12)
    resultados.append({'teste': 'SEFAZ com cert (TLS 1.2)', 'detalhe': det, 'ok': ok, 'msg': msg})

    # Teste B: TLS 1.2 + cert + sem verificacao do servidor (proxy corporativo)
    def factory_tls12_noverify():
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        s = req.Session()
        s.mount('https://', SefazTLSAdapter(cert_pem, key_pem, verify_server=False))
        return s
    ok, det, msg = _test_connection('TLS 1.2 sem verify', factory_tls12_noverify)
    resultados.append({'teste': 'SEFAZ com cert (sem verify - proxy corp.)', 'detalhe': det, 'ok': ok, 'msg': msg})

    # Teste C: Sem forcar TLS (deixar Python negociar) + cert
    def factory_auto_tls():
        s = req.Session()
        s.cert = (cert_pem, key_pem)
        return s
    ok, det, msg = _test_connection('TLS auto', factory_auto_tls)
    resultados.append({'teste': 'SEFAZ com cert (TLS automatico)', 'detalhe': det, 'ok': ok, 'msg': msg})

    # Teste D: Sem forcar TLS + cert + sem proxy
    def factory_noproxy():
        s = req.Session()
        s.cert = (cert_pem, key_pem)
        s.trust_env = False
        return s
    ok, det, msg = _test_connection('Sem proxy', factory_noproxy)
    resultados.append({'teste': 'SEFAZ com cert (sem proxy do sistema)', 'detalhe': det, 'ok': ok, 'msg': msg})

    signer.cleanup_temp_files(cert_pem, key_pem)

    # (fim dos testes, sem o bloco antigo de "sem certificado")
    dummy_var = None  # placeholder para nao quebrar indentacao

    return render_template('diagnostico.html', config=Config, resultados=resultados, cert_info=cert_info)


@app.route('/xml/<chave>')
def download_xml(chave):
    for suffix in ('_autorizada.xml', '_assinada.xml'):
        filepath = os.path.join(Config.XMLS_DIR, f'NFe_{chave}{suffix}')
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
    flash('XML nao encontrado', 'danger')
    return redirect(url_for('index'))


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
    os.makedirs('certificados', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)

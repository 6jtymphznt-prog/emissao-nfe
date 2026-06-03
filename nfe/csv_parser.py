import csv
import io


def _float(value, default=0):
    if value is None or str(value).strip() == '':
        return default
    return float(value)


def _int(value, default=0):
    if value is None or str(value).strip() == '':
        return default
    return int(value)


COLUNAS_OBRIGATORIAS = [
    'numero', 'dest_cnpj_cpf', 'dest_razao_social',
    'dest_logradouro', 'dest_numero', 'dest_bairro',
    'dest_cod_municipio', 'dest_municipio', 'dest_uf',
    'prod_codigo', 'prod_descricao', 'prod_ncm', 'prod_cfop',
    'prod_quantidade', 'prod_valor_unitario',
]


def validar_csv(conteudo_texto):
    reader = csv.DictReader(io.StringIO(conteudo_texto), delimiter=';')

    colunas = reader.fieldnames or []
    colunas_limpos = [c.strip() for c in colunas]

    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in colunas_limpos]
    if faltando:
        return None, f"Colunas obrigatorias ausentes: {', '.join(faltando)}"

    linhas = []
    for i, row in enumerate(reader, start=2):
        row_limpo = {k.strip(): (v.strip() if v else '') for k, v in row.items() if k is not None}
        for campo in COLUNAS_OBRIGATORIAS:
            if not row_limpo.get(campo):
                return None, f"Linha {i}: campo obrigatorio '{campo}' esta vazio"
        linhas.append(row_limpo)

    if not linhas:
        return None, "O arquivo CSV esta vazio (sem linhas de dados)"

    return linhas, None


def agrupar_por_nota(linhas):
    notas = {}
    for row in linhas:
        num = row['numero']
        if num not in notas:
            notas[num] = []
        notas[num].append(row)
    return notas


def parsear_nota(numero, linhas_nota):
    primeira = linhas_nota[0]

    destinatario = {
        'cnpj_cpf': primeira.get('dest_cnpj_cpf', ''),
        'razao_social': primeira.get('dest_razao_social', ''),
        'ie': primeira.get('dest_ie', ''),
        'ind_ie_dest': primeira.get('dest_ind_ie', '') or '9',
        'email': primeira.get('dest_email', ''),
        'logradouro': primeira.get('dest_logradouro', ''),
        'numero': primeira.get('dest_numero', ''),
        'complemento': primeira.get('dest_complemento', ''),
        'bairro': primeira.get('dest_bairro', ''),
        'cod_municipio': primeira.get('dest_cod_municipio', ''),
        'municipio': primeira.get('dest_municipio', ''),
        'uf': primeira.get('dest_uf', ''),
        'cep': primeira.get('dest_cep', ''),
        'telefone': primeira.get('dest_telefone', ''),
        'natureza_operacao': primeira.get('natureza_operacao', '') or 'VENDA DE MERCADORIA',
        'tipo_operacao': primeira.get('tipo_operacao', '') or '1',
        'finalidade': primeira.get('finalidade', '') or '1',
        'consumidor_final': primeira.get('consumidor_final', '') or '0',
        'presenca': primeira.get('presenca', '') or '1',
    }

    produtos = []
    for row in linhas_nota:
        qtd = _float(row.get('prod_quantidade'))
        vl_unit = _float(row.get('prod_valor_unitario'))
        vl_total = round(qtd * vl_unit, 2)

        icms_aliq = _float(row.get('prod_icms_aliquota'))
        icms_valor = round(vl_total * icms_aliq / 100, 2)

        pis_cst = row.get('prod_pis_cst', '') or '07'
        pis_aliq = _float(row.get('prod_pis_aliquota'))
        pis_valor = round(vl_total * pis_aliq / 100, 2) if pis_cst in ('01', '02') else 0

        cofins_cst = row.get('prod_cofins_cst', '') or '07'
        cofins_aliq = _float(row.get('prod_cofins_aliquota'))
        cofins_valor = round(vl_total * cofins_aliq / 100, 2) if cofins_cst in ('01', '02') else 0

        prod = {
            'codigo': row.get('prod_codigo', ''),
            'descricao': row.get('prod_descricao', ''),
            'ncm': row.get('prod_ncm', ''),
            'cfop': row.get('prod_cfop', ''),
            'unidade': row.get('prod_unidade', '') or 'UN',
            'quantidade': qtd,
            'valor_unitario': vl_unit,
            'valor_total': vl_total,
            'ean': row.get('prod_ean', '') or 'SEM GTIN',
            'icms_orig': row.get('prod_icms_orig', '') or '0',
            'icms_cst': row.get('prod_icms_cst', '') or '00',
            'icms_csosn': row.get('prod_icms_csosn', ''),
            'icms_base': vl_total,
            'icms_aliquota': icms_aliq,
            'icms_valor': icms_valor,
            'pis_cst': pis_cst,
            'pis_aliquota': pis_aliq,
            'pis_valor': pis_valor,
            'cofins_cst': cofins_cst,
            'cofins_aliquota': cofins_aliq,
            'cofins_valor': cofins_valor,
        }
        if row.get('prod_cest'):
            prod['cest'] = row['prod_cest']
        produtos.append(prod)

    transporte = {
        'mod_frete': primeira.get('mod_frete', '') or '9',
        'transportadora_cnpj': primeira.get('transp_cnpj', ''),
        'transportadora_nome': primeira.get('transp_nome', ''),
        'transportadora_uf': primeira.get('transp_uf', ''),
        'volumes_qtd': primeira.get('volumes_qtd', ''),
        'volumes_especie': primeira.get('volumes_especie', ''),
        'volumes_peso_liq': primeira.get('volumes_peso_liq', ''),
        'volumes_peso_bruto': primeira.get('volumes_peso_bruto', ''),
    }

    forma_pgto = primeira.get('forma_pagamento', '') or '01'
    if forma_pgto == '90':
        valor_pgto = 0
    else:
        valor_pgto = _float(primeira.get('valor_pagamento'), sum(p['valor_total'] for p in produtos))

    pagamento = {
        'forma': forma_pgto,
        'valor': valor_pgto,
    }

    info_adicionais = primeira.get('info_adicionais', '')

    ambiente = primeira.get('ambiente', '').strip() or None

    emitente = None
    if primeira.get('emit_cnpj', '').strip():
        emitente = {
            'cnpj': primeira.get('emit_cnpj', '').strip(),
            'razao_social': primeira.get('emit_razao_social', ''),
            'nome_fantasia': primeira.get('emit_nome_fantasia', ''),
            'ie': primeira.get('emit_ie', ''),
            'crt': primeira.get('emit_crt', '') or '3',
            'endereco': {
                'logradouro': primeira.get('emit_logradouro', ''),
                'numero': primeira.get('emit_numero', ''),
                'complemento': primeira.get('emit_complemento', ''),
                'bairro': primeira.get('emit_bairro', ''),
                'cod_municipio': primeira.get('emit_cod_municipio', ''),
                'municipio': primeira.get('emit_municipio', ''),
                'uf': primeira.get('emit_uf', ''),
                'cep': primeira.get('emit_cep', ''),
                'cod_pais': primeira.get('emit_cod_pais', '') or '1058',
                'pais': primeira.get('emit_pais', '') or 'BRASIL',
                'telefone': primeira.get('emit_telefone', ''),
            },
        }

    return {
        'numero': _int(numero),
        'emitente': emitente,
        'ambiente': ambiente,
        'destinatario': destinatario,
        'produtos': produtos,
        'transporte': transporte,
        'pagamento': pagamento,
        'info_adicionais': info_adicionais,
    }

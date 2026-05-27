import csv
import io


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
        'ind_ie_dest': primeira.get('dest_ind_ie', '9'),
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
        'natureza_operacao': primeira.get('natureza_operacao', 'VENDA DE MERCADORIA'),
        'tipo_operacao': primeira.get('tipo_operacao', '1'),
        'finalidade': primeira.get('finalidade', '1'),
        'consumidor_final': primeira.get('consumidor_final', '0'),
        'presenca': primeira.get('presenca', '1'),
    }

    produtos = []
    for row in linhas_nota:
        qtd = float(row.get('prod_quantidade', 0))
        vl_unit = float(row.get('prod_valor_unitario', 0))
        vl_total = round(qtd * vl_unit, 2)

        icms_aliq = float(row.get('prod_icms_aliquota', 0))
        icms_valor = round(vl_total * icms_aliq / 100, 2)

        pis_cst = row.get('prod_pis_cst', '07')
        pis_aliq = float(row.get('prod_pis_aliquota', 0))
        pis_valor = round(vl_total * pis_aliq / 100, 2) if pis_cst in ('01', '02') else 0

        cofins_cst = row.get('prod_cofins_cst', '07')
        cofins_aliq = float(row.get('prod_cofins_aliquota', 0))
        cofins_valor = round(vl_total * cofins_aliq / 100, 2) if cofins_cst in ('01', '02') else 0

        prod = {
            'codigo': row.get('prod_codigo', ''),
            'descricao': row.get('prod_descricao', ''),
            'ncm': row.get('prod_ncm', ''),
            'cfop': row.get('prod_cfop', ''),
            'unidade': row.get('prod_unidade', 'UN'),
            'quantidade': qtd,
            'valor_unitario': vl_unit,
            'valor_total': vl_total,
            'ean': row.get('prod_ean', 'SEM GTIN'),
            'icms_orig': row.get('prod_icms_orig', '0'),
            'icms_cst': row.get('prod_icms_cst', '00'),
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
        'mod_frete': primeira.get('mod_frete', '9'),
        'transportadora_cnpj': primeira.get('transp_cnpj', ''),
        'transportadora_nome': primeira.get('transp_nome', ''),
        'transportadora_uf': primeira.get('transp_uf', ''),
        'volumes_qtd': primeira.get('volumes_qtd', ''),
        'volumes_especie': primeira.get('volumes_especie', ''),
        'volumes_peso_liq': primeira.get('volumes_peso_liq', ''),
        'volumes_peso_bruto': primeira.get('volumes_peso_bruto', ''),
    }

    pagamento = {
        'forma': primeira.get('forma_pagamento', '01'),
        'valor': sum(p['valor_total'] for p in produtos),
    }

    info_adicionais = primeira.get('info_adicionais', '')

    return {
        'numero': int(numero),
        'destinatario': destinatario,
        'produtos': produtos,
        'transporte': transporte,
        'pagamento': pagamento,
        'info_adicionais': info_adicionais,
    }

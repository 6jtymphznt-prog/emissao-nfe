from lxml import etree
from datetime import datetime
from .utils import gerar_chave_acesso, agora_sefaz

NAMESPACE_NFE = 'http://www.portalfiscal.inf.br/nfe'
NSMAP = {None: NAMESPACE_NFE}


class NFeBuilder:

    def __init__(self, emitente, ambiente='1', serie='1'):
        self.emitente = emitente
        self.ambiente = ambiente
        self.serie = serie
        self.chave_acesso = None
        self.cnf = None

    def build(self, numero, destinatario, produtos, transporte, pagamento, info_adicionais=''):
        cuf = self.emitente['endereco']['uf']
        from .utils import CODIGOS_UF
        cuf_cod = CODIGOS_UF.get(cuf, '35')
        aamm = datetime.now().strftime('%y%m')
        cnpj = self.emitente['cnpj']

        self.chave_acesso, self.cnf = gerar_chave_acesso(
            cuf=cuf_cod,
            aamm=aamm,
            cnpj=cnpj,
            mod='55',
            serie=self.serie,
            nnf=numero,
            tp_emis='1',
        )

        nfe = etree.Element('NFe', nsmap=NSMAP)
        inf_nfe = etree.SubElement(nfe, 'infNFe', versao='4.00', Id='NFe' + self.chave_acesso)

        self._build_ide(inf_nfe, numero, cuf_cod, destinatario)
        self._build_emit(inf_nfe)
        self._build_dest(inf_nfe, destinatario)

        for i, prod in enumerate(produtos, 1):
            self._build_det(inf_nfe, i, prod)

        self._build_total(inf_nfe, produtos)
        self._build_transp(inf_nfe, transporte)
        self._build_pag(inf_nfe, pagamento)

        if info_adicionais:
            inf_adic = etree.SubElement(inf_nfe, 'infAdic')
            etree.SubElement(inf_adic, 'infCpl').text = info_adicionais[:5000]

        return nfe

    def _build_ide(self, parent, numero, cuf_cod, destinatario):
        ide = etree.SubElement(parent, 'ide')
        etree.SubElement(ide, 'cUF').text = cuf_cod
        etree.SubElement(ide, 'cNF').text = self.cnf
        etree.SubElement(ide, 'natOp').text = destinatario.get('natureza_operacao', 'VENDA DE MERCADORIA')
        etree.SubElement(ide, 'mod').text = '55'
        etree.SubElement(ide, 'serie').text = str(self.serie)
        etree.SubElement(ide, 'nNF').text = str(numero)
        etree.SubElement(ide, 'dhEmi').text = agora_sefaz()
        etree.SubElement(ide, 'dhSaiEnt').text = agora_sefaz()
        etree.SubElement(ide, 'tpNF').text = destinatario.get('tipo_operacao', '1')
        etree.SubElement(ide, 'idDest').text = self._id_destino(destinatario)
        etree.SubElement(ide, 'cMunFG').text = self.emitente['endereco']['cod_municipio']
        etree.SubElement(ide, 'tpImp').text = '1'
        etree.SubElement(ide, 'tpEmis').text = '1'
        etree.SubElement(ide, 'cDV').text = self.chave_acesso[-1]
        etree.SubElement(ide, 'tpAmb').text = self.ambiente
        etree.SubElement(ide, 'finNFe').text = destinatario.get('finalidade', '1')
        etree.SubElement(ide, 'indFinal').text = destinatario.get('consumidor_final', '0')
        etree.SubElement(ide, 'indPres').text = destinatario.get('presenca', '1')
        etree.SubElement(ide, 'procEmi').text = '0'
        etree.SubElement(ide, 'verProc').text = 'NFe-Contingencia-1.0'

    def _id_destino(self, destinatario):
        uf_emit = self.emitente['endereco']['uf']
        uf_dest = destinatario.get('uf', uf_emit)
        if uf_dest == 'EX':
            return '3'
        if uf_dest != uf_emit:
            return '2'
        return '1'

    def _build_emit(self, parent):
        emit = etree.SubElement(parent, 'emit')
        etree.SubElement(emit, 'CNPJ').text = self.emitente['cnpj']
        etree.SubElement(emit, 'xNome').text = self.emitente['razao_social']
        if self.emitente.get('nome_fantasia'):
            etree.SubElement(emit, 'xFant').text = self.emitente['nome_fantasia']

        ender = self.emitente['endereco']
        ender_emit = etree.SubElement(emit, 'enderEmit')
        etree.SubElement(ender_emit, 'xLgr').text = ender['logradouro']
        etree.SubElement(ender_emit, 'nro').text = ender['numero']
        if ender.get('complemento'):
            etree.SubElement(ender_emit, 'xCpl').text = ender['complemento']
        etree.SubElement(ender_emit, 'xBairro').text = ender['bairro']
        etree.SubElement(ender_emit, 'cMun').text = ender['cod_municipio']
        etree.SubElement(ender_emit, 'xMun').text = ender['municipio']
        etree.SubElement(ender_emit, 'UF').text = ender['uf']
        etree.SubElement(ender_emit, 'CEP').text = ender['cep']
        etree.SubElement(ender_emit, 'cPais').text = ender.get('cod_pais', '1058')
        etree.SubElement(ender_emit, 'xPais').text = ender.get('pais', 'BRASIL')
        if ender.get('telefone'):
            etree.SubElement(ender_emit, 'fone').text = ender['telefone']

        etree.SubElement(emit, 'IE').text = self.emitente['ie']
        etree.SubElement(emit, 'CRT').text = self.emitente['crt']

    def _build_dest(self, parent, dest):
        dest_el = etree.SubElement(parent, 'dest')

        doc = dest.get('cnpj_cpf', '').replace('.', '').replace('-', '').replace('/', '')
        if len(doc) == 14:
            etree.SubElement(dest_el, 'CNPJ').text = doc
        elif len(doc) == 11:
            etree.SubElement(dest_el, 'CPF').text = doc

        if self.ambiente == '2':
            etree.SubElement(dest_el, 'xNome').text = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'
        else:
            etree.SubElement(dest_el, 'xNome').text = dest['razao_social']

        ender_dest = etree.SubElement(dest_el, 'enderDest')
        etree.SubElement(ender_dest, 'xLgr').text = dest['logradouro']
        etree.SubElement(ender_dest, 'nro').text = dest['numero']
        if dest.get('complemento'):
            etree.SubElement(ender_dest, 'xCpl').text = dest['complemento']
        etree.SubElement(ender_dest, 'xBairro').text = dest['bairro']
        etree.SubElement(ender_dest, 'cMun').text = dest['cod_municipio']
        etree.SubElement(ender_dest, 'xMun').text = dest['municipio']
        etree.SubElement(ender_dest, 'UF').text = dest['uf']
        etree.SubElement(ender_dest, 'CEP').text = dest.get('cep', '')
        etree.SubElement(ender_dest, 'cPais').text = '1058'
        etree.SubElement(ender_dest, 'xPais').text = 'BRASIL'
        if dest.get('telefone'):
            etree.SubElement(ender_dest, 'fone').text = dest['telefone']

        etree.SubElement(dest_el, 'indIEDest').text = dest.get('ind_ie_dest', '9')
        if dest.get('ie') and dest.get('ind_ie_dest') == '1':
            etree.SubElement(dest_el, 'IE').text = dest['ie']
        if dest.get('email'):
            etree.SubElement(dest_el, 'email').text = dest['email']

    def _build_det(self, parent, n_item, prod_data):
        det = etree.SubElement(parent, 'det', nItem=str(n_item))

        prod = etree.SubElement(det, 'prod')
        etree.SubElement(prod, 'cProd').text = prod_data['codigo']
        etree.SubElement(prod, 'cEAN').text = prod_data.get('ean', 'SEM GTIN')
        etree.SubElement(prod, 'xProd').text = prod_data['descricao']
        etree.SubElement(prod, 'NCM').text = prod_data['ncm']
        if prod_data.get('cest'):
            etree.SubElement(prod, 'CEST').text = prod_data['cest']
        etree.SubElement(prod, 'CFOP').text = prod_data['cfop']
        etree.SubElement(prod, 'uCom').text = prod_data['unidade']
        etree.SubElement(prod, 'qCom').text = self._fmt_qtd(prod_data['quantidade'])
        etree.SubElement(prod, 'vUnCom').text = self._fmt_valor_un(prod_data['valor_unitario'])
        etree.SubElement(prod, 'vProd').text = self._fmt_valor(prod_data['valor_total'])
        etree.SubElement(prod, 'cEANTrib').text = prod_data.get('ean_trib', 'SEM GTIN')
        etree.SubElement(prod, 'uTrib').text = prod_data.get('unidade_trib', prod_data['unidade'])
        etree.SubElement(prod, 'qTrib').text = self._fmt_qtd(prod_data.get('qtd_trib', prod_data['quantidade']))
        etree.SubElement(prod, 'vUnTrib').text = self._fmt_valor_un(prod_data.get('valor_un_trib', prod_data['valor_unitario']))
        etree.SubElement(prod, 'indTot').text = '1'

        imposto = etree.SubElement(det, 'imposto')

        icms_group = etree.SubElement(imposto, 'ICMS')
        cst_icms = prod_data.get('icms_cst', '00')
        csosn = prod_data.get('icms_csosn', '')

        if csosn:
            self._build_icms_simples(icms_group, csosn, prod_data)
        else:
            self._build_icms_normal(icms_group, cst_icms, prod_data)

        pis_group = etree.SubElement(imposto, 'PIS')
        cst_pis = prod_data.get('pis_cst', '07')
        if cst_pis in ('01', '02'):
            pis_aliq = etree.SubElement(pis_group, 'PISAliq')
            etree.SubElement(pis_aliq, 'CST').text = cst_pis
            etree.SubElement(pis_aliq, 'vBC').text = self._fmt_valor(prod_data.get('pis_base', prod_data['valor_total']))
            etree.SubElement(pis_aliq, 'pPIS').text = self._fmt_aliq(prod_data.get('pis_aliquota', 1.65))
            etree.SubElement(pis_aliq, 'vPIS').text = self._fmt_valor(prod_data.get('pis_valor', 0))
        else:
            pis_outros = etree.SubElement(pis_group, 'PISNT')
            etree.SubElement(pis_outros, 'CST').text = cst_pis

        cofins_group = etree.SubElement(imposto, 'COFINS')
        cst_cofins = prod_data.get('cofins_cst', '07')
        if cst_cofins in ('01', '02'):
            cofins_aliq = etree.SubElement(cofins_group, 'COFINSAliq')
            etree.SubElement(cofins_aliq, 'CST').text = cst_cofins
            etree.SubElement(cofins_aliq, 'vBC').text = self._fmt_valor(prod_data.get('cofins_base', prod_data['valor_total']))
            etree.SubElement(cofins_aliq, 'pCOFINS').text = self._fmt_aliq(prod_data.get('cofins_aliquota', 7.60))
            etree.SubElement(cofins_aliq, 'vCOFINS').text = self._fmt_valor(prod_data.get('cofins_valor', 0))
        else:
            cofins_outros = etree.SubElement(cofins_group, 'COFINSNT')
            etree.SubElement(cofins_outros, 'CST').text = cst_cofins

    def _build_icms_normal(self, parent, cst, prod_data):
        if cst == '00':
            icms = etree.SubElement(parent, 'ICMS00')
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CST').text = '00'
            etree.SubElement(icms, 'modBC').text = '3'
            etree.SubElement(icms, 'vBC').text = self._fmt_valor(prod_data.get('icms_base', prod_data['valor_total']))
            etree.SubElement(icms, 'pICMS').text = self._fmt_aliq(prod_data.get('icms_aliquota', 18))
            etree.SubElement(icms, 'vICMS').text = self._fmt_valor(prod_data.get('icms_valor', 0))
        elif cst in ('10', '30', '70', '90'):
            tag = 'ICMS' + cst
            icms = etree.SubElement(parent, tag)
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CST').text = cst
            etree.SubElement(icms, 'modBC').text = '3'
            etree.SubElement(icms, 'vBC').text = self._fmt_valor(prod_data.get('icms_base', prod_data['valor_total']))
            etree.SubElement(icms, 'pICMS').text = self._fmt_aliq(prod_data.get('icms_aliquota', 18))
            etree.SubElement(icms, 'vICMS').text = self._fmt_valor(prod_data.get('icms_valor', 0))
        elif cst in ('20',):
            icms = etree.SubElement(parent, 'ICMS20')
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CST').text = '20'
            etree.SubElement(icms, 'modBC').text = '3'
            etree.SubElement(icms, 'pRedBC').text = self._fmt_aliq(prod_data.get('icms_red_bc', 0))
            etree.SubElement(icms, 'vBC').text = self._fmt_valor(prod_data.get('icms_base', prod_data['valor_total']))
            etree.SubElement(icms, 'pICMS').text = self._fmt_aliq(prod_data.get('icms_aliquota', 18))
            etree.SubElement(icms, 'vICMS').text = self._fmt_valor(prod_data.get('icms_valor', 0))
        elif cst in ('40', '41', '50'):
            icms = etree.SubElement(parent, 'ICMS40')
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CST').text = cst
        elif cst == '60':
            icms = etree.SubElement(parent, 'ICMS60')
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CST').text = '60'
        else:
            icms = etree.SubElement(parent, 'ICMS00')
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CST').text = '00'
            etree.SubElement(icms, 'modBC').text = '3'
            etree.SubElement(icms, 'vBC').text = self._fmt_valor(prod_data.get('icms_base', prod_data['valor_total']))
            etree.SubElement(icms, 'pICMS').text = self._fmt_aliq(prod_data.get('icms_aliquota', 18))
            etree.SubElement(icms, 'vICMS').text = self._fmt_valor(prod_data.get('icms_valor', 0))

    def _build_icms_simples(self, parent, csosn, prod_data):
        if csosn == '102':
            icms = etree.SubElement(parent, 'ICMSSN102')
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CSOSN').text = csosn
        elif csosn == '101':
            icms = etree.SubElement(parent, 'ICMSSN101')
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CSOSN').text = csosn
            etree.SubElement(icms, 'pCredSN').text = self._fmt_aliq(prod_data.get('icms_aliquota', 0))
            etree.SubElement(icms, 'vCredICMSSN').text = self._fmt_valor(prod_data.get('icms_valor', 0))
        elif csosn == '500':
            icms = etree.SubElement(parent, 'ICMSSN500')
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CSOSN').text = csosn
        else:
            icms = etree.SubElement(parent, 'ICMSSN102')
            etree.SubElement(icms, 'orig').text = prod_data.get('icms_orig', '0')
            etree.SubElement(icms, 'CSOSN').text = csosn

    def _build_total(self, parent, produtos):
        total = etree.SubElement(parent, 'total')
        icms_tot = etree.SubElement(total, 'ICMSTot')

        v_bc = sum(float(p.get('icms_base', p['valor_total'])) for p in produtos if p.get('icms_cst') in ('00', '10', '20', '70', '90', None))
        v_icms = sum(float(p.get('icms_valor', 0)) for p in produtos)
        v_prod = sum(float(p['valor_total']) for p in produtos)
        v_pis = sum(float(p.get('pis_valor', 0)) for p in produtos)
        v_cofins = sum(float(p.get('cofins_valor', 0)) for p in produtos)
        v_frete = sum(float(p.get('valor_frete', 0)) for p in produtos)
        v_seg = sum(float(p.get('valor_seguro', 0)) for p in produtos)
        v_desc = sum(float(p.get('valor_desconto', 0)) for p in produtos)
        v_outros = sum(float(p.get('valor_outros', 0)) for p in produtos)
        v_nf = v_prod + v_frete + v_seg + v_outros - v_desc

        etree.SubElement(icms_tot, 'vBC').text = self._fmt_valor(v_bc)
        etree.SubElement(icms_tot, 'vICMS').text = self._fmt_valor(v_icms)
        etree.SubElement(icms_tot, 'vICMSDeson').text = '0.00'
        etree.SubElement(icms_tot, 'vFCPUFDest').text = '0.00'
        etree.SubElement(icms_tot, 'vICMSUFDest').text = '0.00'
        etree.SubElement(icms_tot, 'vICMSUFRemet').text = '0.00'
        etree.SubElement(icms_tot, 'vFCP').text = '0.00'
        etree.SubElement(icms_tot, 'vBCST').text = '0.00'
        etree.SubElement(icms_tot, 'vST').text = '0.00'
        etree.SubElement(icms_tot, 'vFCPST').text = '0.00'
        etree.SubElement(icms_tot, 'vFCPSTRet').text = '0.00'
        etree.SubElement(icms_tot, 'vProd').text = self._fmt_valor(v_prod)
        etree.SubElement(icms_tot, 'vFrete').text = self._fmt_valor(v_frete)
        etree.SubElement(icms_tot, 'vSeg').text = self._fmt_valor(v_seg)
        etree.SubElement(icms_tot, 'vDesc').text = self._fmt_valor(v_desc)
        etree.SubElement(icms_tot, 'vII').text = '0.00'
        etree.SubElement(icms_tot, 'vIPI').text = '0.00'
        etree.SubElement(icms_tot, 'vIPIDevol').text = '0.00'
        etree.SubElement(icms_tot, 'vPIS').text = self._fmt_valor(v_pis)
        etree.SubElement(icms_tot, 'vCOFINS').text = self._fmt_valor(v_cofins)
        etree.SubElement(icms_tot, 'vOutro').text = self._fmt_valor(v_outros)
        etree.SubElement(icms_tot, 'vNF').text = self._fmt_valor(v_nf)

    def _build_transp(self, parent, transporte):
        transp = etree.SubElement(parent, 'transp')
        etree.SubElement(transp, 'modFrete').text = transporte.get('mod_frete', '9')

        if transporte.get('transportadora_cnpj'):
            transporta = etree.SubElement(transp, 'transporta')
            doc = transporte['transportadora_cnpj'].replace('.', '').replace('-', '').replace('/', '')
            if len(doc) == 14:
                etree.SubElement(transporta, 'CNPJ').text = doc
            elif len(doc) == 11:
                etree.SubElement(transporta, 'CPF').text = doc
            if transporte.get('transportadora_nome'):
                etree.SubElement(transporta, 'xNome').text = transporte['transportadora_nome']
            if transporte.get('transportadora_uf'):
                etree.SubElement(transporta, 'UF').text = transporte['transportadora_uf']

        if transporte.get('volumes_qtd'):
            vol = etree.SubElement(transp, 'vol')
            etree.SubElement(vol, 'qVol').text = str(transporte['volumes_qtd'])
            if transporte.get('volumes_especie'):
                etree.SubElement(vol, 'esp').text = transporte['volumes_especie']
            if transporte.get('volumes_peso_liq'):
                etree.SubElement(vol, 'pesoL').text = self._fmt_peso(transporte['volumes_peso_liq'])
            if transporte.get('volumes_peso_bruto'):
                etree.SubElement(vol, 'pesoB').text = self._fmt_peso(transporte['volumes_peso_bruto'])

    def _build_pag(self, parent, pagamento):
        pag = etree.SubElement(parent, 'pag')
        det_pag = etree.SubElement(pag, 'detPag')
        etree.SubElement(det_pag, 'tPag').text = pagamento.get('forma', '01')
        etree.SubElement(det_pag, 'vPag').text = self._fmt_valor(pagamento.get('valor', 0))

    def to_xml_string(self, nfe_element):
        return etree.tostring(nfe_element, encoding='unicode', xml_declaration=False)

    @staticmethod
    def _fmt_valor(v):
        return f'{float(v):.2f}'

    @staticmethod
    def _fmt_valor_un(v):
        return f'{float(v):.4f}'

    @staticmethod
    def _fmt_qtd(v):
        return f'{float(v):.4f}'

    @staticmethod
    def _fmt_aliq(v):
        return f'{float(v):.2f}'

    @staticmethod
    def _fmt_peso(v):
        return f'{float(v):.3f}'

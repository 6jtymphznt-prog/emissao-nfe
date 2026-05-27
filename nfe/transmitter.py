import requests
from lxml import etree
from .sefaz_urls import obter_urls_sefaz

SOAP_NS = 'http://www.w3.org/2003/05/soap-envelope'
NFE_NS = 'http://www.portalfiscal.inf.br/nfe'

WSDL_ACTIONS = {
    'NfeAutorizacao': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4',
    'NfeRetAutorizacao': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4',
    'NfeConsultaProtocolo': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4',
    'NfeStatusServico': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4',
    'NfeInutilizacao': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeInutilizacao4',
    'RecepcaoEvento': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4',
}


class NFeTransmitter:

    def __init__(self, uf, ambiente, signer):
        self.uf = uf
        self.ambiente = ambiente
        self.signer = signer
        self.urls = obter_urls_sefaz(uf, ambiente)
        self._cert_path = None
        self._key_path = None

    def _get_cert_files(self):
        if not self._cert_path:
            self._cert_path, self._key_path = self.signer.get_cert_key_temp_files()
        return self._cert_path, self._key_path

    def _cleanup(self):
        if self._cert_path:
            self.signer.cleanup_temp_files(self._cert_path, self._key_path)
            self._cert_path = None
            self._key_path = None

    def _build_soap_envelope(self, servico, xml_content):
        wsdl_ns = WSDL_ACTIONS[servico]

        envelope = etree.Element(
            '{%s}Envelope' % SOAP_NS,
            nsmap={'soap12': SOAP_NS}
        )
        body = etree.SubElement(envelope, '{%s}Body' % SOAP_NS)
        dados_msg = etree.SubElement(body, '{%s}nfeDadosMsg' % wsdl_ns)

        if isinstance(xml_content, str):
            inner = etree.fromstring(xml_content.encode('utf-8'))
        else:
            inner = xml_content

        dados_msg.append(inner)

        return '<?xml version="1.0" encoding="UTF-8"?>' + etree.tostring(envelope, encoding='unicode')

    def _send(self, servico, xml_content, timeout=60):
        url = self.urls[servico]
        soap_xml = self._build_soap_envelope(servico, xml_content)
        cert_path, key_path = self._get_cert_files()

        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
        }

        try:
            response = requests.post(
                url,
                data=soap_xml.encode('utf-8'),
                headers=headers,
                cert=(cert_path, key_path),
                timeout=timeout,
                verify=True,
            )
            response.raise_for_status()
            return self._parse_response(response.content)
        finally:
            self._cleanup()

    def _parse_response(self, content):
        root = etree.fromstring(content)

        body = root.find('.//{%s}Body' % SOAP_NS)
        if body is None:
            return {'erro': 'Resposta SOAP invalida', 'xml_raw': content.decode('utf-8', errors='replace')}

        result = {}

        for elem in body.iter():
            tag = etree.QName(elem.tag).localname if '}' in str(elem.tag) else elem.tag

            if tag == 'cStat':
                result['cStat'] = elem.text
            elif tag == 'xMotivo':
                result['xMotivo'] = elem.text
            elif tag == 'nProt':
                result['nProt'] = elem.text
            elif tag == 'dhRecbto':
                result['dhRecbto'] = elem.text
            elif tag == 'chNFe':
                result['chNFe'] = elem.text
            elif tag == 'nRec':
                result['nRec'] = elem.text
            elif tag == 'cOrgao':
                result['cOrgao'] = elem.text

        result['xml_raw'] = content.decode('utf-8', errors='replace')
        return result

    def status_servico(self):
        cons_stat = etree.Element('{%s}consStatServ' % NFE_NS, versao='4.00')
        etree.SubElement(cons_stat, '{%s}tpAmb' % NFE_NS).text = self.ambiente
        etree.SubElement(cons_stat, '{%s}cUF' % NFE_NS).text = self._cod_uf()
        etree.SubElement(cons_stat, '{%s}xServ' % NFE_NS).text = 'STATUS'
        return self._send('NfeStatusServico', cons_stat)

    def autorizar(self, nfe_signed_element, id_lote=None):
        if id_lote is None:
            import random
            id_lote = str(random.randint(1, 999999999999999))

        envi_nfe = etree.Element('{%s}enviNFe' % NFE_NS, versao='4.00')
        etree.SubElement(envi_nfe, '{%s}idLote' % NFE_NS).text = id_lote
        etree.SubElement(envi_nfe, '{%s}indSinc' % NFE_NS).text = '1'
        envi_nfe.append(nfe_signed_element)

        return self._send('NfeAutorizacao', envi_nfe)

    def consultar_protocolo(self, chave_acesso):
        cons_sit = etree.Element('{%s}consSitNFe' % NFE_NS, versao='4.00')
        etree.SubElement(cons_sit, '{%s}tpAmb' % NFE_NS).text = self.ambiente
        etree.SubElement(cons_sit, '{%s}xServ' % NFE_NS).text = 'CONSULTAR'
        etree.SubElement(cons_sit, '{%s}chNFe' % NFE_NS).text = chave_acesso
        return self._send('NfeConsultaProtocolo', cons_sit)

    def cancelar(self, chave_acesso, protocolo, justificativa, cnpj):
        from .utils import CODIGOS_UF
        from datetime import datetime

        cod_uf = CODIGOS_UF.get(self.uf, '35')

        evento = etree.Element('{%s}envEvento' % NFE_NS, versao='1.00')
        etree.SubElement(evento, '{%s}idLote' % NFE_NS).text = '1'

        ev = etree.SubElement(evento, '{%s}evento' % NFE_NS, versao='1.00')
        inf_evento = etree.SubElement(ev, '{%s}infEvento' % NFE_NS, Id='ID110111' + chave_acesso + '01')
        etree.SubElement(inf_evento, '{%s}cOrgao' % NFE_NS).text = cod_uf
        etree.SubElement(inf_evento, '{%s}tpAmb' % NFE_NS).text = self.ambiente
        etree.SubElement(inf_evento, '{%s}CNPJ' % NFE_NS).text = cnpj
        etree.SubElement(inf_evento, '{%s}chNFe' % NFE_NS).text = chave_acesso
        from .utils import agora_sefaz
        etree.SubElement(inf_evento, '{%s}dhEvento' % NFE_NS).text = agora_sefaz()
        etree.SubElement(inf_evento, '{%s}tpEvento' % NFE_NS).text = '110111'
        etree.SubElement(inf_evento, '{%s}nSeqEvento' % NFE_NS).text = '1'
        etree.SubElement(inf_evento, '{%s}verEvento' % NFE_NS).text = '1.00'

        det_evento = etree.SubElement(inf_evento, '{%s}detEvento' % NFE_NS, versao='1.00')
        etree.SubElement(det_evento, '{%s}descEvento' % NFE_NS).text = 'Cancelamento'
        etree.SubElement(det_evento, '{%s}nProt' % NFE_NS).text = protocolo
        etree.SubElement(det_evento, '{%s}xJust' % NFE_NS).text = justificativa

        self.signer.sign_nfe(ev)

        return self._send('RecepcaoEvento', evento)

    def _cod_uf(self):
        from .utils import CODIGOS_UF
        return CODIGOS_UF.get(self.uf, '35')

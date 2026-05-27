import ssl
import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
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


class SefazTLSAdapter(HTTPAdapter):

    def __init__(self, cert_pem_path, key_pem_path, verify_server=True, **kwargs):
        self.cert_pem_path = cert_pem_path
        self.key_pem_path = key_pem_path
        self.verify_server = verify_server
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        if not self.verify_server:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            ctx.load_verify_locations(certifi.where())
        ctx.load_cert_chain(certfile=self.cert_pem_path, keyfile=self.key_pem_path)
        kwargs['ssl_context'] = ctx
        super().init_poolmanager(*args, **kwargs)

    def send(self, request, **kwargs):
        if not self.verify_server:
            kwargs['verify'] = False
        return super().send(request, **kwargs)


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

    def _create_session(self):
        cert_path, key_path = self._get_cert_files()
        session = requests.Session()
        adapter = SefazTLSAdapter(cert_path, key_path, verify_server=False)
        session.mount('https://', adapter)
        return session

    def _build_soap_envelope(self, servico, xml_content):
        wsdl_ns = WSDL_ACTIONS[servico]

        envelope = etree.Element(
            '{%s}Envelope' % SOAP_NS,
            nsmap={'soap12': SOAP_NS}
        )
        body = etree.SubElement(envelope, '{%s}Body' % SOAP_NS)
        dados_msg = etree.SubElement(body, 'nfeDadosMsg', nsmap={None: wsdl_ns})

        if isinstance(xml_content, str):
            inner = etree.fromstring(xml_content.encode('utf-8'))
        else:
            inner = xml_content

        dados_msg.append(inner)

        return '<?xml version="1.0" encoding="UTF-8"?>' + etree.tostring(envelope, encoding='unicode')

    def _send(self, servico, xml_content, timeout=60):
        url = self.urls[servico]
        soap_xml = self._build_soap_envelope(servico, xml_content)

        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
        }

        try:
            session = self._create_session()
            response = session.post(
                url,
                data=soap_xml.encode('utf-8'),
                headers=headers,
                timeout=timeout,
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
        nfemap = {None: NFE_NS}
        cons_stat = etree.Element('consStatServ', versao='4.00', nsmap=nfemap)
        etree.SubElement(cons_stat, 'tpAmb').text = self.ambiente
        etree.SubElement(cons_stat, 'cUF').text = self._cod_uf()
        etree.SubElement(cons_stat, 'xServ').text = 'STATUS'
        return self._send('NfeStatusServico', cons_stat)

    def autorizar(self, nfe_signed_element, id_lote=None):
        if id_lote is None:
            import random
            id_lote = str(random.randint(1, 999999999999999))

        nfemap = {None: NFE_NS}
        envi_nfe = etree.Element('enviNFe', versao='4.00', nsmap=nfemap)
        etree.SubElement(envi_nfe, 'idLote').text = id_lote
        etree.SubElement(envi_nfe, 'indSinc').text = '1'
        envi_nfe.append(nfe_signed_element)

        return self._send('NfeAutorizacao', envi_nfe)

    def consultar_protocolo(self, chave_acesso):
        nfemap = {None: NFE_NS}
        cons_sit = etree.Element('consSitNFe', versao='4.00', nsmap=nfemap)
        etree.SubElement(cons_sit, 'tpAmb').text = self.ambiente
        etree.SubElement(cons_sit, 'xServ').text = 'CONSULTAR'
        etree.SubElement(cons_sit, 'chNFe').text = chave_acesso
        return self._send('NfeConsultaProtocolo', cons_sit)

    def cancelar(self, chave_acesso, protocolo, justificativa, cnpj):
        from .utils import CODIGOS_UF

        cod_uf = CODIGOS_UF.get(self.uf, '35')
        nfemap = {None: NFE_NS}

        evento = etree.Element('envEvento', versao='1.00', nsmap=nfemap)
        etree.SubElement(evento, 'idLote').text = '1'

        ev = etree.SubElement(evento, 'evento', versao='1.00')
        inf_evento = etree.SubElement(ev, 'infEvento', Id='ID110111' + chave_acesso + '01')
        etree.SubElement(inf_evento, 'cOrgao').text = cod_uf
        etree.SubElement(inf_evento, 'tpAmb').text = self.ambiente
        etree.SubElement(inf_evento, 'CNPJ').text = cnpj
        etree.SubElement(inf_evento, 'chNFe').text = chave_acesso
        from .utils import agora_sefaz
        etree.SubElement(inf_evento, 'dhEvento').text = agora_sefaz()
        etree.SubElement(inf_evento, 'tpEvento').text = '110111'
        etree.SubElement(inf_evento, 'nSeqEvento').text = '1'
        etree.SubElement(inf_evento, 'verEvento').text = '1.00'

        det_evento = etree.SubElement(inf_evento, 'detEvento', versao='1.00')
        etree.SubElement(det_evento, 'descEvento').text = 'Cancelamento'
        etree.SubElement(det_evento, 'nProt').text = protocolo
        etree.SubElement(det_evento, 'xJust').text = justificativa

        self.signer.sign_nfe(ev)

        return self._send('RecepcaoEvento', evento)

    def _cod_uf(self):
        from .utils import CODIGOS_UF
        return CODIGOS_UF.get(self.uf, '35')

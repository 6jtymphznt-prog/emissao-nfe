import base64
import hashlib
import tempfile
import os
import requests as http_requests
from lxml import etree
from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import AuthorityInformationAccessOID

NAMESPACE_DS = 'http://www.w3.org/2000/09/xmldsig#'
C14N_ALG = 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
ENVELOPED_SIG = 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
RSA_SHA1 = 'http://www.w3.org/2000/09/xmldsig#rsa-sha1'
SHA1 = 'http://www.w3.org/2000/09/xmldsig#sha1'


class NFeSigner:

    def __init__(self, pfx_path, pfx_password):
        self.pfx_path = pfx_path
        self.pfx_password = pfx_password
        self._private_key = None
        self._certificate = None
        self._cert_pem = None
        self._key_pem = None
        self._chain_certs = []
        self._load_certificate()

    def _load_certificate(self):
        with open(self.pfx_path, 'rb') as f:
            pfx_data = f.read()

        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            pfx_data, self.pfx_password.encode()
        )

        self._private_key = private_key
        self._certificate = certificate

        chain = list(additional_certs or [])
        if not chain:
            chain = self._fetch_intermediate_chain(certificate)
        self._chain_certs = chain

        cert_pem = certificate.public_bytes(Encoding.PEM)
        for ca_cert in self._chain_certs:
            cert_pem += ca_cert.public_bytes(Encoding.PEM)
        self._cert_pem = cert_pem
        self._key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())

    def _fetch_intermediate_chain(self, cert):
        chain = []
        current = cert
        for _ in range(5):
            try:
                aia = current.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS
                )
                ca_urls = [
                    desc.access_location.value
                    for desc in aia.value
                    if desc.access_method == AuthorityInformationAccessOID.CA_ISSUERS
                ]
                if not ca_urls:
                    break

                resp = http_requests.get(ca_urls[0], timeout=10)
                resp.raise_for_status()

                parsed_certs = self._parse_cert_response(resp.content)
                if not parsed_certs:
                    break

                chain.extend(parsed_certs)
                issuer_cert = parsed_certs[0]

                if issuer_cert.issuer == issuer_cert.subject:
                    break

                current = issuer_cert
            except Exception:
                break
        return chain

    @staticmethod
    def _parse_cert_response(data):
        try:
            return [x509.load_der_x509_certificate(data)]
        except Exception:
            pass
        try:
            return [x509.load_pem_x509_certificate(data)]
        except Exception:
            pass
        try:
            from cryptography.hazmat.primitives.serialization import pkcs7
            return pkcs7.load_der_pkcs7_certificates(data)
        except Exception:
            pass
        try:
            from cryptography.hazmat.primitives.serialization import pkcs7
            return pkcs7.load_pem_pkcs7_certificates(data)
        except Exception:
            pass
        return []

    @property
    def chain_count(self):
        return len(self._chain_certs)

    def sign_nfe(self, nfe_element):
        inf_nfe = nfe_element.find('{http://www.portalfiscal.inf.br/nfe}infNFe')
        if inf_nfe is None:
            inf_nfe = nfe_element.find('infNFe')
        if inf_nfe is None:
            raise ValueError('Elemento infNFe nao encontrado')

        uri = '#' + inf_nfe.get('Id')

        c14n_inf = etree.tostring(inf_nfe, method='c14n', exclusive=False, with_comments=False)
        digest_value = base64.b64encode(hashlib.sha1(c14n_inf).digest()).decode()

        nsmap_ds = {'ds': NAMESPACE_DS}

        signed_info = etree.Element('{%s}SignedInfo' % NAMESPACE_DS, nsmap=nsmap_ds)
        c14n_method = etree.SubElement(signed_info, '{%s}CanonicalizationMethod' % NAMESPACE_DS)
        c14n_method.set('Algorithm', C14N_ALG)
        sig_method = etree.SubElement(signed_info, '{%s}SignatureMethod' % NAMESPACE_DS)
        sig_method.set('Algorithm', RSA_SHA1)

        reference = etree.SubElement(signed_info, '{%s}Reference' % NAMESPACE_DS)
        reference.set('URI', uri)

        transforms = etree.SubElement(reference, '{%s}Transforms' % NAMESPACE_DS)
        transform1 = etree.SubElement(transforms, '{%s}Transform' % NAMESPACE_DS)
        transform1.set('Algorithm', ENVELOPED_SIG)
        transform2 = etree.SubElement(transforms, '{%s}Transform' % NAMESPACE_DS)
        transform2.set('Algorithm', C14N_ALG)

        digest_method = etree.SubElement(reference, '{%s}DigestMethod' % NAMESPACE_DS)
        digest_method.set('Algorithm', SHA1)
        digest_el = etree.SubElement(reference, '{%s}DigestValue' % NAMESPACE_DS)
        digest_el.text = digest_value

        c14n_signed_info = etree.tostring(signed_info, method='c14n', exclusive=False, with_comments=False)

        signature_value = self._private_key.sign(
            c14n_signed_info,
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        sig_value_b64 = base64.b64encode(signature_value).decode()

        signature = etree.SubElement(nfe_element, '{%s}Signature' % NAMESPACE_DS)

        signature.append(signed_info)

        sig_value_el = etree.SubElement(signature, '{%s}SignatureValue' % NAMESPACE_DS)
        sig_value_el.text = sig_value_b64

        key_info = etree.SubElement(signature, '{%s}KeyInfo' % NAMESPACE_DS)
        x509_data = etree.SubElement(key_info, '{%s}X509Data' % NAMESPACE_DS)
        x509_cert = etree.SubElement(x509_data, '{%s}X509Certificate' % NAMESPACE_DS)

        cert_der = self._certificate.public_bytes(Encoding.DER)
        x509_cert.text = base64.b64encode(cert_der).decode()

        return nfe_element

    def get_cert_key_temp_files(self):
        cert_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        cert_file.write(self._cert_pem)
        cert_file.close()

        key_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        key_file.write(self._key_pem)
        key_file.close()

        return cert_file.name, key_file.name

    def cleanup_temp_files(self, cert_path, key_path):
        for path in (cert_path, key_path):
            try:
                os.unlink(path)
            except OSError:
                pass

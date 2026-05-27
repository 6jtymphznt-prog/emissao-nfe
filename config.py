import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'chave-padrao-troque-em-producao')
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    EMIT_CNPJ = os.getenv('EMIT_CNPJ', '')
    EMIT_RAZAO_SOCIAL = os.getenv('EMIT_RAZAO_SOCIAL', '')
    EMIT_NOME_FANTASIA = os.getenv('EMIT_NOME_FANTASIA', '')
    EMIT_IE = os.getenv('EMIT_IE', '')
    EMIT_CRT = os.getenv('EMIT_CRT', '3')

    EMIT_LOGRADOURO = os.getenv('EMIT_LOGRADOURO', '')
    EMIT_NUMERO = os.getenv('EMIT_NUMERO', '')
    EMIT_COMPLEMENTO = os.getenv('EMIT_COMPLEMENTO', '')
    EMIT_BAIRRO = os.getenv('EMIT_BAIRRO', '')
    EMIT_COD_MUNICIPIO = os.getenv('EMIT_COD_MUNICIPIO', '')
    EMIT_MUNICIPIO = os.getenv('EMIT_MUNICIPIO', '')
    EMIT_UF = os.getenv('EMIT_UF', '')
    EMIT_CEP = os.getenv('EMIT_CEP', '')
    EMIT_COD_PAIS = os.getenv('EMIT_COD_PAIS', '1058')
    EMIT_PAIS = os.getenv('EMIT_PAIS', 'BRASIL')
    EMIT_TELEFONE = os.getenv('EMIT_TELEFONE', '')

    CERT_PFX_PATH = os.getenv('CERT_PFX_PATH', 'certificados/certificado.pfx')
    CERT_PFX_PASSWORD = os.getenv('CERT_PFX_PASSWORD', '')

    NFE_AMBIENTE = os.getenv('NFE_AMBIENTE', '1')
    NFE_SERIE = os.getenv('NFE_SERIE', '1')
    NFE_PROXIMO_NUMERO = int(os.getenv('NFE_PROXIMO_NUMERO', '1'))
    NFE_CUF = os.getenv('NFE_CUF', '35')

    XMLS_DIR = os.path.join(os.path.dirname(__file__), 'xmls')
    DANFES_DIR = os.path.join(os.path.dirname(__file__), 'danfes')

    @classmethod
    def emitente(cls):
        return {
            'cnpj': cls.EMIT_CNPJ,
            'razao_social': cls.EMIT_RAZAO_SOCIAL,
            'nome_fantasia': cls.EMIT_NOME_FANTASIA,
            'ie': cls.EMIT_IE,
            'crt': cls.EMIT_CRT,
            'endereco': {
                'logradouro': cls.EMIT_LOGRADOURO,
                'numero': cls.EMIT_NUMERO,
                'complemento': cls.EMIT_COMPLEMENTO,
                'bairro': cls.EMIT_BAIRRO,
                'cod_municipio': cls.EMIT_COD_MUNICIPIO,
                'municipio': cls.EMIT_MUNICIPIO,
                'uf': cls.EMIT_UF,
                'cep': cls.EMIT_CEP,
                'cod_pais': cls.EMIT_COD_PAIS,
                'pais': cls.EMIT_PAIS,
                'telefone': cls.EMIT_TELEFONE,
            }
        }

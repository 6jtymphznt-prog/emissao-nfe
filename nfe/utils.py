import random
from datetime import datetime

CODIGOS_UF = {
    'AC': '12', 'AL': '27', 'AM': '13', 'AP': '16', 'BA': '29',
    'CE': '23', 'DF': '53', 'ES': '32', 'GO': '52', 'MA': '21',
    'MG': '31', 'MS': '50', 'MT': '51', 'PA': '15', 'PB': '25',
    'PE': '26', 'PI': '22', 'PR': '41', 'RJ': '33', 'RN': '24',
    'RO': '11', 'RR': '14', 'RS': '43', 'SC': '42', 'SE': '28',
    'SP': '35', 'TO': '17',
}

UF_POR_CODIGO = {v: k for k, v in CODIGOS_UF.items()}


def calcular_digito_verificador(chave_sem_dv):
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    idx = 0
    for digito in reversed(chave_sem_dv):
        soma += int(digito) * pesos[idx % 8]
        idx += 1
    resto = soma % 11
    if resto < 2:
        return 0
    return 11 - resto


def gerar_chave_acesso(cuf, aamm, cnpj, mod, serie, nnf, tp_emis, cnf=None):
    if cnf is None:
        cnf = str(random.randint(10000000, 99999999))

    chave_sem_dv = (
        str(cuf).zfill(2)
        + str(aamm).zfill(4)
        + str(cnpj).zfill(14)
        + str(mod).zfill(2)
        + str(serie).zfill(3)
        + str(nnf).zfill(9)
        + str(tp_emis).zfill(1)
        + str(cnf).zfill(8)
    )

    dv = calcular_digito_verificador(chave_sem_dv)
    return chave_sem_dv + str(dv), cnf


def validar_cnpj(cnpj):
    cnpj = ''.join(c for c in cnpj if c.isdigit())
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False

    def calc_dv(digits, weights):
        s = sum(int(d) * w for d, w in zip(digits, weights))
        r = s % 11
        return 0 if r < 2 else 11 - r

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    if calc_dv(cnpj[:12], w1) != int(cnpj[12]):
        return False
    if calc_dv(cnpj[:13], w2) != int(cnpj[13]):
        return False
    return True


def validar_cpf(cpf):
    cpf = ''.join(c for c in cpf if c.isdigit())
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False

    def calc_dv(digits, start_weight):
        s = sum(int(d) * w for d, w in zip(digits, range(start_weight, 1, -1)))
        r = s % 11
        return 0 if r < 2 else 11 - r

    if calc_dv(cpf[:9], 10) != int(cpf[9]):
        return False
    if calc_dv(cpf[:10], 11) != int(cpf[10]):
        return False
    return True


def formatar_chave_acesso(chave):
    return ' '.join(chave[i:i+4] for i in range(0, len(chave), 4))


def agora_sefaz():
    now = datetime.now()
    offset = now.astimezone().strftime('%z')
    offset_formatted = offset[:3] + ':' + offset[3:]
    return now.strftime('%Y-%m-%dT%H:%M:%S') + offset_formatted


def limpar_documento(doc):
    return ''.join(c for c in doc if c.isdigit())

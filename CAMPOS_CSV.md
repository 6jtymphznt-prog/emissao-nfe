# Guia de Campos do CSV - Gerador de XML NFe

Este documento descreve **cada campo** do arquivo CSV usado para gerar XMLs de
NFe em lote.

## Como usar este guia

1. Cada linha do CSV representa **um produto** de uma nota
2. Notas com **mais de um produto**: repita os dados da nota com o **mesmo numero**
3. Campos marcados como **Obrigatorio** sempre devem estar preenchidos
4. Campos **opcionais** podem ficar em branco - o sistema usara um valor padrao
5. Use **ponto** (`.`) como separador decimal (ex: `150.00`, nao `150,00`)
6. Datas: nao precisa preencher, o sistema usa a data/hora atual
7. Codigos numericos (CFOP, NCM, CST): **sem pontos** ou tracos
8. CNPJ/CPF/CEP: **somente numeros**, sem formatacao

---

## IDENTIFICACAO DA NOTA

| Campo | Obrigatorio | Descricao | Exemplo |
|-------|:-----------:|-----------|---------|
| `numero` | **Sim** | Numero da NFe. Notas com mesmo numero sao agrupadas | `1` |
| `ambiente` | Nao | `1` = Producao (real), `2` = Homologacao (teste). Padrao: `1` | `1` |
| `natureza_operacao` | Nao | Texto que descreve a operacao. Padrao: `VENDA DE MERCADORIA` | `VENDA DE MERCADORIA` |
| `tipo_operacao` | Nao | `0` = Entrada, `1` = Saida. Padrao: `1` | `1` |
| `finalidade` | Nao | `1` = Normal, `2` = Complementar, `3` = Ajuste, `4` = Devolucao | `1` |
| `consumidor_final` | Nao | `0` = Nao, `1` = Sim | `0` |
| `presenca` | Nao | `0` = Nao se aplica, `1` = Presencial, `2` = Internet, `3` = Teleatendimento, `4` = NFC-e domicilio, `5` = Presencial fora estabelecimento, `9` = Outros | `1` |

### Ambiente (importante!)

- **Producao (1):** a nota tem valor fiscal. Use para emissoes reais
- **Homologacao (2):** a nota e de teste, **sem valor fiscal**. A SEFAZ exige
  que o nome do destinatario seja substituido por
  `NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL`. O sistema
  faz essa substituicao automaticamente

---

## EMITENTE (FILIAL - opcional)

> **Quando usar:** se quiser emitir notas de uma filial diferente da empresa
> configurada no arquivo `.env`. Se TODAS as colunas `emit_*` ficarem vazias,
> o sistema usa os dados da matriz (do .env).

| Campo | Obrigatorio | Descricao | Exemplo |
|-------|:-----------:|-----------|---------|
| `emit_cnpj` | Nao | CNPJ da filial (14 digitos, sem pontuacao) | `12345678000299` |
| `emit_razao_social` | Nao | Razao social da filial | `MINHA EMPRESA FILIAL SP LTDA` |
| `emit_nome_fantasia` | Nao | Nome fantasia | `MINHA EMPRESA SP` |
| `emit_ie` | Nao | Inscricao Estadual da filial | `123456789` |
| `emit_crt` | Nao | Regime tributario: `1` = Simples Nacional, `2` = Simples Nacional excesso, `3` = Regime Normal | `3` |
| `emit_logradouro` | Nao | Rua/avenida | `Rua da Filial` |
| `emit_numero` | Nao | Numero do endereco | `200` |
| `emit_complemento` | Nao | Complemento (sala, andar, etc) | `Sala 1` |
| `emit_bairro` | Nao | Bairro | `Centro` |
| `emit_cod_municipio` | Nao | Codigo IBGE do municipio (7 digitos) | `3550308` |
| `emit_municipio` | Nao | Nome do municipio | `SAO PAULO` |
| `emit_uf` | Nao | Sigla da UF | `SP` |
| `emit_cep` | Nao | CEP (8 digitos, sem traco) | `01001000` |
| `emit_telefone` | Nao | Telefone (DDD + numero, somente digitos) | `11999999999` |

> **Importante:** se preencher `emit_cnpj`, recomenda-se preencher TODOS os
> outros campos `emit_*` para que o XML fique completo.

---

## DESTINATARIO

| Campo | Obrigatorio | Descricao | Exemplo |
|-------|:-----------:|-----------|---------|
| `dest_cnpj_cpf` | **Sim** | CNPJ (14 digitos) ou CPF (11 digitos), sem pontuacao | `12345678000199` |
| `dest_razao_social` | **Sim** | Razao social ou nome completo (em homologacao sera substituido pela SEFAZ) | `CLIENTE ABC LTDA` |
| `dest_ie` | Nao | Inscricao Estadual (somente se for contribuinte) | `123456789` |
| `dest_ind_ie` | Nao | `1` = Contribuinte ICMS, `2` = Isento, `9` = Nao contribuinte. Padrao: `9` | `9` |
| `dest_email` | Nao | Email do destinatario | `cliente@email.com` |
| `dest_logradouro` | **Sim** | Rua/avenida | `Rua das Flores` |
| `dest_numero` | **Sim** | Numero do endereco | `100` |
| `dest_complemento` | Nao | Complemento | `Apto 5` |
| `dest_bairro` | **Sim** | Bairro | `Centro` |
| `dest_cod_municipio` | **Sim** | Codigo IBGE do municipio (7 digitos) | `3304557` |
| `dest_municipio` | **Sim** | Nome do municipio | `RIO DE JANEIRO` |
| `dest_uf` | **Sim** | Sigla da UF | `RJ` |
| `dest_cep` | Nao | CEP (8 digitos) | `20040020` |
| `dest_telefone` | Nao | Telefone | `21999998888` |

### Onde encontrar o codigo IBGE do municipio?

Acesse https://www.ibge.gov.br/explica/codigos-dos-municipios.php ou pesquise
no Google: "codigo ibge [nome da cidade]".

---

## TRANSPORTE

| Campo | Obrigatorio | Descricao | Exemplo |
|-------|:-----------:|-----------|---------|
| `mod_frete` | Nao | `0` = Por conta do emitente, `1` = Por conta do destinatario, `2` = Por conta de terceiros, `3` = Proprio remetente, `4` = Proprio destinatario, `9` = Sem frete. Padrao: `9` | `9` |
| `transp_cnpj` | Nao | CNPJ da transportadora (se houver) | `12345678000199` |
| `transp_nome` | Nao | Nome da transportadora | `TRANSPORTADORA XYZ` |
| `transp_uf` | Nao | UF da transportadora | `SP` |
| `volumes_qtd` | Nao | Quantidade de volumes | `1` |
| `volumes_especie` | Nao | Especie dos volumes | `CAIXA` |
| `volumes_peso_liq` | Nao | Peso liquido em kg (3 decimais) | `5.500` |
| `volumes_peso_bruto` | Nao | Peso bruto em kg (3 decimais) | `6.000` |

---

## PAGAMENTO

| Campo | Obrigatorio | Descricao | Exemplo |
|-------|:-----------:|-----------|---------|
| `forma_pagamento` | Nao | Codigo da forma de pagamento. Padrao: `01` (Dinheiro) | `01` |
| `valor_pagamento` | Nao | Valor do pagamento. Se vazio, usa o total dos produtos. Se `forma_pagamento` = `90`, sempre 0 | `620.50` |
| `info_adicionais` | Nao | Texto livre com informacoes complementares | `Pedido n. 12345` |

### Codigos de forma de pagamento

| Codigo | Descricao |
|:------:|-----------|
| `01` | Dinheiro |
| `02` | Cheque |
| `03` | Cartao de Credito |
| `04` | Cartao de Debito |
| `05` | Credito Loja |
| `10` | Vale Alimentacao |
| `11` | Vale Refeicao |
| `12` | Vale Presente |
| `13` | Vale Combustivel |
| `15` | Boleto Bancario |
| `16` | Deposito Bancario |
| `17` | PIX |
| `18` | Transferencia bancaria/carteira digital |
| `19` | Programa de fidelidade |
| `90` | **Sem Pagamento** (use para doacao, transferencia, bonificacao) |
| `99` | Outros |

---

## PRODUTO

> **Importante:** uma linha do CSV = um produto. Se a nota tem 3 produtos,
> serao 3 linhas com o mesmo `numero`.

| Campo | Obrigatorio | Descricao | Exemplo |
|-------|:-----------:|-----------|---------|
| `prod_codigo` | **Sim** | Codigo interno do produto | `001` |
| `prod_descricao` | **Sim** | Descricao do produto | `CAMISETA ALGODAO TAM M` |
| `prod_ncm` | **Sim** | Codigo NCM (8 digitos, sem pontos) | `61091000` |
| `prod_cfop` | **Sim** | CFOP (4 digitos) | `5102` |
| `prod_unidade` | Nao | Unidade comercial. Padrao: `UN` | `UN` |
| `prod_ean` | Nao | Codigo de barras EAN/GTIN. Padrao: `SEM GTIN` | `7891234567890` |
| `prod_quantidade` | **Sim** | Quantidade (use ponto decimal) | `2` |
| `prod_valor_unitario` | **Sim** | Valor unitario em reais (use ponto decimal) | `150.00` |
| `prod_icms_orig` | Nao | Origem da mercadoria. Padrao: `0` (Nacional) | `0` |
| `prod_icms_cst` | Nao | CST ICMS (regime normal). Padrao: `00` | `00` |
| `prod_icms_csosn` | Nao | CSOSN (apenas Simples Nacional, ex: 101, 102, 500) | `102` |
| `prod_icms_aliquota` | Nao | Aliquota ICMS em % | `18` |
| `prod_cest` | Nao | Codigo CEST (se aplicavel a substituicao tributaria) | `0100100` |
| `prod_pis_cst` | Nao | CST PIS. Padrao: `07` (Isenta) | `07` |
| `prod_pis_aliquota` | Nao | Aliquota PIS em % | `0` ou `1.65` |
| `prod_cofins_cst` | Nao | CST COFINS. Padrao: `07` (Isenta) | `07` |
| `prod_cofins_aliquota` | Nao | Aliquota COFINS em % | `0` ou `7.60` |

### Codigos de CFOP mais comuns

| CFOP | Descricao |
|:----:|-----------|
| `5102` | Venda de mercadoria dentro do estado |
| `6102` | Venda de mercadoria para outro estado |
| `5101` | Venda de producao do estabelecimento dentro do estado |
| `5405` | Venda de mercadoria com ST dentro do estado |
| `5910` | Remessa em bonificacao/doacao dentro do estado |
| `6910` | Remessa em bonificacao/doacao para outro estado |
| `5152` | Transferencia de mercadoria dentro do estado |
| `6152` | Transferencia de mercadoria para outro estado |
| `5949` | Outra saida nao especificada |

### Codigos de Origem da Mercadoria

| Codigo | Descricao |
|:------:|-----------|
| `0` | Nacional |
| `1` | Importacao direta |
| `2` | Importacao indireta |
| `3` | Nacional com 40-70% de conteudo importado |
| `4` | Nacional Lei 288/67 ou 8.248/91 |
| `5` | Nacional com menos de 40% de conteudo importado |
| `6` | Importacao direta sem similar nacional |
| `7` | Importacao indireta sem similar nacional |
| `8` | Nacional com mais de 70% de conteudo importado |

### CST ICMS (Regime Normal)

| CST | Descricao |
|:---:|-----------|
| `00` | Tributada integralmente |
| `10` | Tributada e com cobranca de ICMS por ST |
| `20` | Com reducao de base de calculo |
| `30` | Isenta ou nao tributada com ICMS por ST |
| `40` | Isenta |
| `41` | Nao tributada |
| `50` | Suspensao |
| `51` | Diferimento |
| `60` | ICMS cobrado anteriormente por ST |
| `70` | Com reducao de BC e cobranca por ST |
| `90` | Outros |

### CSOSN (Simples Nacional)

| CSOSN | Descricao |
|:-----:|-----------|
| `101` | Tributada com permissao de credito |
| `102` | Tributada sem permissao de credito |
| `103` | Isencao do ICMS para faixa de receita bruta |
| `201` | Tributada com permissao de credito e ST |
| `202` | Tributada sem permissao de credito e ST |
| `203` | Isencao para faixa de receita bruta e ST |
| `300` | Imune |
| `400` | Nao tributada |
| `500` | ICMS cobrado anteriormente por ST ou antecipacao |
| `900` | Outros |

### CST PIS/COFINS

| CST | Descricao |
|:---:|-----------|
| `01` | Operacao tributavel com aliquota basica |
| `02` | Operacao tributavel com aliquota diferenciada |
| `04` | Operacao tributavel monofasica - aliquota zero |
| `05` | Operacao tributavel ST |
| `06` | Operacao tributavel aliquota zero |
| `07` | Operacao isenta da contribuicao |
| `08` | Operacao sem incidencia da contribuicao |
| `09` | Operacao com suspensao da contribuicao |
| `49` | Outras operacoes de saida |
| `99` | Outras operacoes |

---

## EXEMPLOS PRATICOS

### Exemplo 1: Venda simples (1 produto)

```
numero;ambiente;dest_cnpj_cpf;dest_razao_social;dest_logradouro;dest_numero;dest_bairro;dest_cod_municipio;dest_municipio;dest_uf;forma_pagamento;prod_codigo;prod_descricao;prod_ncm;prod_cfop;prod_quantidade;prod_valor_unitario;prod_icms_cst;prod_icms_aliquota
1;1;12345678000199;CLIENTE ABC LTDA;Rua A;100;Centro;3304557;RIO DE JANEIRO;RJ;01;001;PRODUTO TESTE;84719012;5102;1;100.00;00;18
```

### Exemplo 2: Venda com 2 produtos (mesmo numero)

```
1;1;12345678000199;CLIENTE ABC LTDA;...;001;PRODUTO A;84719012;5102;2;150.00;00;18
1;1;12345678000199;CLIENTE ABC LTDA;...;002;PRODUTO B;84713012;5102;1;320.50;00;18
```

### Exemplo 3: Doacao (sem pagamento)

```
2;1;...;90;0;...;001;PRODUTO DOADO;84719012;6910;5;80.00;41;0
```
(forma_pagamento = 90, valor_pagamento = 0, CFOP 6910, CST 41 = nao tributada)

### Exemplo 4: Emissao por filial em homologacao

```
3;2;DOACAO DE MERCADORIA;1;1;0;1;00000000000299;FILIAL SP LTDA;FILIAL SP;000000000;3;Rua Filial;200;;Centro;3550308;SAO PAULO;SP;01001000;...
```
(ambiente = 2, emit_cnpj preenchido com dados da filial)

---

## DICAS IMPORTANTES

1. **Sempre valide primeiro:** use o botao "Apenas Validar" antes de gerar
   os XMLs. Isso evita erros em lote
2. **Salve no formato CSV correto:** ao salvar no Excel, escolha
   "CSV (separado por ponto e virgula)"
3. **Codificacao UTF-8:** se houver caracteres acentuados nos dados,
   prefira salvar como UTF-8
4. **Numeros decimais:** use ponto (`.`), nao virgula (`,`)
5. **Notas com varios produtos:** repita o `numero` em cada linha de produto
6. **Filial diferente:** preencha TODAS as colunas `emit_*` para evitar
   campos faltantes no XML
7. **Homologacao:** o nome do destinatario sera substituido automaticamente
   no XML pela SEFAZ - voce pode preencher o nome real no CSV mesmo assim

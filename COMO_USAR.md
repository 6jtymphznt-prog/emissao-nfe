# Como Usar - Sistema de Emissao de NFe (Contingencia)

## O que e este sistema?

Este e um programa que roda no seu computador e permite emitir Notas Fiscais
Eletronicas (NFe, modelo 55) quando o sistema emissor principal da sua empresa
estiver fora do ar. Ele abre uma pagina no navegador (como um site) onde voce
preenche os dados e emite a nota.

---

## Passo a Passo para Instalar

### 1. Instalar o Python

O programa precisa do Python (versao 3.9 ou superior) instalado.

**Windows:**
1. Acesse https://www.python.org/downloads/
2. Clique em "Download Python 3.x.x"
3. Execute o instalador
4. **IMPORTANTE:** Marque a opcao "Add Python to PATH" antes de clicar em Install
5. Clique em "Install Now"

**Mac:**
1. Abra o Terminal
2. Digite: `brew install python3` (se tiver Homebrew)
3. Ou baixe de https://www.python.org/downloads/

### 2. Baixar este projeto

**Opcao A - Download direto (mais facil):**
1. Na pagina do projeto no GitHub, clique no botao verde **"Code"**
2. Clique em **"Download ZIP"**
3. Extraia o ZIP numa pasta do seu computador (ex: `C:\EmissaoNFe`)

**Opcao B - Via Git (se tiver instalado):**
```
git clone <URL_DO_REPOSITORIO>
```

### 3. Instalar as dependencias

1. Abra o **Prompt de Comando** (Windows) ou **Terminal** (Mac/Linux)
2. Navegue ate a pasta do projeto:
   ```
   cd C:\EmissaoNFe
   ```
   (ou o caminho onde voce extraiu)
3. Execute:
   ```
   pip install -r requirements.txt
   ```
   Aguarde a instalacao terminar (pode levar alguns minutos).

### 4. Configurar os dados da sua empresa

1. Na pasta do projeto, encontre o arquivo `.env.example`
2. **Copie** este arquivo e renomeie a copia para `.env` (sem o .example)
   - Windows: clique com botao direito > Copiar, depois Cole e renomeie
3. Abra o `.env` com o **Bloco de Notas** (ou qualquer editor de texto)
4. Preencha os dados da sua empresa:

```
# Dados da empresa
EMIT_CNPJ=12345678000199        <-- CNPJ da sua empresa (so numeros)
EMIT_RAZAO_SOCIAL=MINHA EMPRESA LTDA
EMIT_NOME_FANTASIA=MINHA EMPRESA
EMIT_IE=123456789012            <-- Inscricao Estadual
EMIT_CRT=3                      <-- 1=Simples Nacional, 3=Regime Normal

# Endereco
EMIT_LOGRADOURO=Rua da Empresa
EMIT_NUMERO=100
EMIT_COMPLEMENTO=Sala 1
EMIT_BAIRRO=Centro
EMIT_COD_MUNICIPIO=3550308      <-- Codigo IBGE da sua cidade
EMIT_MUNICIPIO=SAO PAULO
EMIT_UF=SP
EMIT_CEP=01001000
EMIT_TELEFONE=11999999999

# Certificado digital
CERT_PFX_PATH=certificados/certificado.pfx
CERT_PFX_PASSWORD=senha_do_certificado

# Ambiente (CUIDADO!)
NFE_AMBIENTE=1                  <-- 1=PRODUCAO (vale de verdade), 2=TESTE

# Numeracao
NFE_SERIE=1
NFE_PROXIMO_NUMERO=1            <-- Proximo numero de nota a usar
NFE_CUF=35                      <-- Codigo IBGE do seu estado

# Seguranca
FLASK_SECRET_KEY=coloque-qualquer-frase-longa-aqui
```

5. Salve o arquivo

### 5. Colocar o certificado digital

1. Na pasta do projeto, existe uma pasta chamada `certificados`
2. Copie o seu arquivo de certificado digital A1 (arquivo `.pfx` ou `.p12`) para dentro dessa pasta
3. Renomeie o arquivo para `certificado.pfx`
   (ou altere o nome no `.env` para corresponder)

### 6. Iniciar o sistema

1. Abra o Prompt de Comando / Terminal
2. Navegue ate a pasta do projeto:
   ```
   cd C:\EmissaoNFe
   ```
3. Execute:
   ```
   python app.py
   ```
4. Voce vera uma mensagem como:
   ```
   * Running on http://0.0.0.0:5000
   ```
5. Abra o navegador (Chrome, Firefox, Edge) e acesse:
   ```
   http://localhost:5000
   ```

Pronto! O sistema esta rodando.

---

## Como Emitir uma NFe (pelo formulario)

1. Acesse http://localhost:5000
2. Clique em **"Emitir NFe"**
3. Preencha os campos:
   - **Numero**: o sistema ja sugere o proximo
   - **Destinatario**: CNPJ/CPF, nome, endereco completo
   - **Produtos**: codigo, descricao, NCM, CFOP, quantidade, valor
   - **Transporte**: modalidade do frete
   - **Pagamento**: forma de pagamento
4. Clique em **"Emitir NFe"**
5. Aguarde a resposta da SEFAZ
6. Se autorizada, voce pode baixar o **DANFE (PDF)** e o **XML**

---

## Como Emitir NFe via CSV (planilha)

Esta opcao e ideal quando voce ja tem os dados organizados em planilha
(Excel, Google Sheets) ou precisa emitir varias notas de uma vez.

### Passo a passo:

1. Acesse http://localhost:5000
2. Clique em **"Importar CSV"**
3. Clique em **"Baixar Modelo CSV"** para pegar o arquivo de exemplo
4. Abra o arquivo no **Excel** ou **Google Planilhas**:
   - No Excel: Arquivo > Abrir > selecione o arquivo > ao importar,
     escolha "Delimitado" e marque **"Ponto e virgula"**
   - No Google Sheets: Arquivo > Importar > Upload > arraste o arquivo
5. Preencha os dados das notas (veja a referencia de colunas na pagina)
6. **Se a nota tiver mais de um produto**, use uma linha por produto,
   repetindo os dados do destinatario e colocando o **mesmo numero** de nota
7. Salve como CSV:
   - Excel: Arquivo > Salvar Como > tipo "CSV (separado por ponto e virgula)"
   - Google Sheets: Arquivo > Fazer download > CSV
8. Volte na pagina "Importar CSV"
9. Clique em **"Apenas Validar"** primeiro para conferir se esta tudo certo
10. Se estiver OK, envie novamente e clique em **"Validar e Emitir"**

### Exemplo de CSV:

Uma nota com 2 produtos:

| numero | dest_cnpj_cpf | dest_razao_social | ... | prod_codigo | prod_descricao | prod_quantidade | prod_valor_unitario |
|--------|---------------|-------------------|-----|-------------|----------------|-----------------|---------------------|
| 1      | 12345678000199| CLIENTE LTDA      | ... | 001         | PRODUTO A      | 2               | 150.00              |
| 1      | 12345678000199| CLIENTE LTDA      | ... | 002         | PRODUTO B      | 1               | 320.50              |

Note que o **numero "1"** se repete nas duas linhas porque ambos os produtos
pertencem a mesma nota.

---

## Codigos Importantes

### CFOP (mais comuns)
- **5102** - Venda de mercadoria dentro do estado
- **6102** - Venda de mercadoria para outro estado
- **5405** - Venda de mercadoria com ST dentro do estado
- **5949** - Outra saida nao especificada
- **1102** - Compra dentro do estado
- **2102** - Compra de outro estado

### CST ICMS
- **00** - Tributada integralmente
- **10** - Tributada com cobranca de ST
- **20** - Com reducao de base de calculo
- **40** - Isenta
- **41** - Nao tributada
- **60** - ICMS cobrado anteriormente por ST

### Forma de Pagamento
- **01** - Dinheiro
- **02** - Cheque
- **03** - Cartao de Credito
- **04** - Cartao de Debito
- **15** - Boleto Bancario
- **17** - PIX
- **90** - Sem Pagamento
- **99** - Outros

---

## Para Parar o Sistema

No terminal onde ele esta rodando, pressione **Ctrl + C**.

---

## Problemas Comuns

**"Certificado digital nao encontrado"**
- Verifique se o arquivo .pfx esta na pasta `certificados/`
- Verifique se o nome do arquivo esta correto no `.env`

**"Erro na comunicacao com SEFAZ"**
- Verifique sua conexao com a internet
- Use "Status SEFAZ" para verificar se o servico esta no ar
- Verifique se o certificado nao esta vencido

**"Rejeicao 539 - Duplicidade de NF-e"**
- Ja existe uma nota com esse numero. Aumente o numero no campo ou no `.env`

**Pagina nao abre no navegador**
- Verifique se o terminal mostra "Running on http://..."
- Tente acessar http://127.0.0.1:5000 em vez de localhost

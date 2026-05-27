# Como Usar - Sistema de Emissao de NFe (Contingencia)

## O que e este sistema?

Este e um programa que roda no seu computador e permite emitir Notas Fiscais
Eletronicas (NFe, modelo 55) quando o sistema emissor principal da sua empresa
estiver fora do ar. Ele abre uma pagina no navegador (como um site) onde voce
preenche os dados e emite a nota.

---

## Passo a Passo para Instalar

### 1. Instalar o Python

O programa precisa do Python instalado.

**IMPORTANTE:** Use o **Python 3.12** (versao estavel). NAO use o Python 3.14
(versao experimental) pois as bibliotecas ainda nao funcionam com ele.

**Windows:**
1. Acesse https://www.python.org/downloads/release/python-31210/
2. Role ate o final da pagina e clique em **"Windows installer (64-bit)"**
3. Execute o instalador
4. **IMPORTANTE:** Marque a opcao **"Add Python to PATH"** antes de clicar em Install
5. Clique em "Install Now"

**Como verificar a versao instalada:**
Abra o Prompt de Comando e digite:
```
python --version
```
Deve aparecer algo como `Python 3.12.10`. Se aparecer `Python 3.14.x`,
desinstale primeiro (Configuracoes > Aplicativos > Python 3.14 > Desinstalar)
e instale o 3.12 conforme acima.

**Mac:**
1. Abra o Terminal
2. Digite: `brew install python@3.12` (se tiver Homebrew)
3. Ou baixe de https://www.python.org/downloads/release/python-31210/

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

1. Abra o **Prompt de Comando**:
   - No Windows: aperte a tecla **Windows** do teclado, digite **cmd** e
     aperte Enter
   - No Mac: abra o aplicativo **Terminal** (esta em Aplicativos > Utilitarios)

2. Navegue ate a pasta onde voce extraiu o projeto.
   Para isso, use o comando `cd` (significa "change directory" = mudar de pasta).

   **Como descobrir o caminho da pasta:**
   - Abra a pasta do projeto no Explorador de Arquivos (Windows) ou Finder (Mac)
   - **Windows:** clique na barra de endereco no topo da janela - ela vai
     mostrar o caminho completo (ex: `C:\Users\SeuNome\Downloads\emissao-nfe`).
     Copie esse texto.
   - **Mac:** clique com botao direito na pasta > "Obter Informacoes" e veja
     o campo "Onde".

   Agora no Prompt de Comando / Terminal, digite `cd ` (com espaco) e cole o
   caminho. Exemplos:

   ```
   cd C:\Users\SeuNome\Downloads\emissao-nfe
   ```

   ou se estiver em outra unidade de disco (ex: D:), primeiro troque de unidade:

   ```
   D:
   cd D:\MinhasPastas\emissao-nfe
   ```

   **Dica:** voce pode tambem arrastar a pasta do Explorador de Arquivos para
   dentro da janela do Prompt de Comando - o caminho sera colado automaticamente.

3. Para confirmar que esta na pasta certa, digite:
   ```
   dir
   ```
   (Windows) ou `ls` (Mac/Linux). Voce deve ver os arquivos do projeto listados
   (app.py, requirements.txt, etc).

4. Agora instale as dependencias:
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

1. Abra o **Prompt de Comando** (Windows: tecla Windows > digite cmd > Enter)
2. Navegue ate a pasta do projeto (mesmo comando que usou no passo 3):
   ```
   cd C:\Users\SeuNome\Downloads\emissao-nfe
   ```
3. Digite o comando abaixo e aperte Enter:
   ```
   python app.py
   ```
4. Voce vera uma mensagem parecida com esta:
   ```
   * Running on http://0.0.0.0:5000
   ```
   **NAO feche esta janela!** Ela precisa ficar aberta enquanto voce usa o sistema.

5. Abra o navegador (Chrome, Firefox, Edge) e na barra de endereco digite:
   ```
   http://localhost:5000
   ```
   e aperte Enter.

Pronto! O sistema esta rodando. A pagina inicial vai aparecer no navegador.

**Para usar da proxima vez:** repita apenas os passos 1 a 5 desta secao
(nao precisa instalar nada de novo).

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

**Erro ao instalar: "Failed building wheel for lxml" / "Failed building wheel for Pillow"**
- Voce provavelmente esta usando o **Python 3.14** (versao experimental).
- Solucao: desinstale o Python 3.14 e instale o **Python 3.12**.
  Veja o passo 1 da instalacao acima.
- Para verificar sua versao, digite no Prompt de Comando: `python --version`

**Erro ao instalar: "Microsoft Visual C++ 14.0 or greater is required"**
- Mesmo problema: use o **Python 3.12** que ja tem pacotes prontos para Windows
  e nao precisa compilar nada.

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

**"python nao e reconhecido como comando interno"**
- O Python nao foi adicionado ao PATH durante a instalacao.
- Desinstale o Python, instale novamente e dessa vez marque a opcao
  **"Add Python to PATH"** antes de clicar em Install.

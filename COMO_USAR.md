# Como Usar - Gerador de XML NFe

## O que e este sistema?

E uma ferramenta que **gera o arquivo XML** da Nota Fiscal Eletronica (NFe,
modelo 55) a partir de um formulario web ou de uma planilha CSV.

O XML gerado **nao tem assinatura digital** e **nao e transmitido a SEFAZ**.
Voce deve importar o XML em um **emissor externo** (gratuito ou pago) que
faca a assinatura e a transmissao.

Junto com o XML, o sistema gera tambem uma **previa do DANFE** em PDF
(com marca d'agua "PREVIA - SEM VALOR FISCAL") para conferencia visual.

---

## Instalacao

### 1. Instalar o Python 3.12

Baixe de https://www.python.org/downloads/release/python-31213/ e instale.
**MARQUE** a opcao "Add Python to PATH" durante a instalacao.

Para confirmar, abra o **Prompt de Comando** e digite:
```
python --version
```
Deve aparecer `Python 3.12.x`.

### 2. Baixar este projeto

1. Na pagina do projeto no GitHub, clique no botao verde **"Code"**
2. Clique em **"Download ZIP"**
3. Extraia o ZIP numa pasta (ex: `C:\Users\SeuNome\Downloads\emissao-nfe`)

### 3. Instalar as dependencias

1. Abra o **Prompt de Comando**:
   - Aperte a tecla **Windows** > digite **cmd** > Enter
2. Navegue ate a pasta do projeto:
   - Abra a pasta no Explorador de Arquivos
   - Clique na barra de endereco para ver o caminho completo
   - No cmd, digite `cd ` (com espaco) e cole o caminho. Exemplo:
     ```
     cd C:\Users\SeuNome\Downloads\emissao-nfe
     ```
   - Dica: voce pode **arrastar a pasta** do Explorador para dentro do cmd
3. Instale as dependencias:
   ```
   pip install -r requirements.txt
   ```

### 4. Configurar dados da empresa

1. Na pasta do projeto, copie o arquivo `.env.example` para `.env`
   (sem o `.example`)
2. Abra o `.env` no Bloco de Notas e preencha os dados:

```
EMIT_CNPJ=12345678000199
EMIT_RAZAO_SOCIAL=MINHA EMPRESA LTDA
EMIT_NOME_FANTASIA=MINHA EMPRESA
EMIT_IE=123456789012
EMIT_CRT=3

EMIT_LOGRADOURO=Rua da Empresa
EMIT_NUMERO=100
EMIT_COMPLEMENTO=Sala 1
EMIT_BAIRRO=Centro
EMIT_COD_MUNICIPIO=3304557
EMIT_MUNICIPIO=RIO DE JANEIRO
EMIT_UF=RJ
EMIT_CEP=20040020
EMIT_TELEFONE=21999999999

NFE_SERIE=1
NFE_PROXIMO_NUMERO=1
```

### 5. Iniciar o sistema

No Prompt de Comando, dentro da pasta do projeto, digite:
```
python app.py
```

Voce vera:
```
* Running on http://127.0.0.1:5000
```

**NAO feche essa janela!** Ela precisa ficar aberta enquanto voce usa o sistema.

Abra o navegador (Chrome, Edge, Firefox) e acesse:
```
http://localhost:5000
```

---

## Gerar XML pelo formulario

1. Acesse `http://localhost:5000`
2. Clique em **"Gerar XML"**
3. Preencha os dados: destinatario, produtos, transporte, pagamento
4. Clique em **"Gerar XML"** no fim da pagina
5. Voce sera direcionado a uma pagina com os botoes:
   - **Baixar XML** - o arquivo .xml para importar no emissor externo
   - **Previa do DANFE** - PDF para conferencia visual

---

## Gerar XMLs em lote via CSV

1. Acesse `http://localhost:5000`
2. Clique em **"Importar CSV"**
3. Clique em **"Baixar Modelo CSV"** para pegar o arquivo de exemplo
4. Abra o arquivo no **Excel** ou **Google Planilhas**:
   - Excel: Arquivo > Abrir > selecione o arquivo > escolha "Delimitado" e marque **"Ponto e virgula"**
   - Google Sheets: Arquivo > Importar > Upload > arraste o arquivo
5. Preencha os dados (uma linha por **produto**, mesmo numero para produtos da mesma nota)
6. Salve como CSV:
   - Excel: Arquivo > Salvar Como > tipo **"CSV (separado por ponto e virgula)"**
   - Google Sheets: Arquivo > Fazer download > **CSV**
7. Na pagina "Importar CSV", clique em **"Apenas Validar"** primeiro
8. Se estiver tudo certo, envie de novo e clique em **"Validar e Gerar XMLs"**
9. Apos gerar, voce vera a lista das notas com:
   - **Botao XML** para baixar individualmente
   - **Botao Previa** para o DANFE em PDF
   - **Botao "Baixar todos (ZIP)"** no topo - todos os XMLs num arquivo ZIP

---

## Importar no emissor externo

Apos gerar o XML aqui, voce precisa de um **emissor que assine e transmita**.
Alguns emissores gratuitos populares:

- **EmissorNF-e da SEFAZ-SP** (gratuito, oficial)
- **NFe-Facil** (versao gratuita)
- **Bling** (versao gratuita limitada)

A maioria desses emissores tem opcao **"Importar XML"** ou similar. Importe
o XML gerado aqui, o emissor ira:
1. Assinar com seu certificado digital
2. Transmitir para a SEFAZ
3. Gerar o DANFE final autorizado

---

## Codigos importantes

### CFOP (mais comuns)
- **5102** - Venda dentro do estado
- **6102** - Venda para outro estado
- **5910** - Doacao/bonificacao dentro do estado
- **6910** - Doacao/bonificacao para outro estado
- **5949** - Outra saida nao especificada
- **5152** - Transferencia dentro do estado
- **6152** - Transferencia para outro estado

### Forma de Pagamento
- **01** - Dinheiro
- **03** - Cartao de Credito
- **04** - Cartao de Debito
- **15** - Boleto
- **17** - PIX
- **90** - Sem Pagamento (use para doacao/transferencia)

### CST ICMS
- **00** - Tributada integralmente
- **40** - Isenta
- **41** - Nao tributada

---

## Problemas comuns

**"python nao e reconhecido"**
- O Python nao foi adicionado ao PATH durante a instalacao
- Desinstale e reinstale marcando "Add Python to PATH"

**Erro ao instalar dependencias**
- Use **Python 3.12** (Python 3.14 ainda nao tem todos os pacotes prontos)

**Pagina nao abre**
- Confira se o terminal mostra "Running on http://..."
- Tente `http://127.0.0.1:5000` em vez de `localhost`

**Erro "could not convert string to float"**
- Algum campo numerico no CSV esta com texto invalido
- Confira a coluna `prod_quantidade` e `prod_valor_unitario`

**"Colunas obrigatorias ausentes"**
- O CSV nao tem todas as colunas necessarias
- Baixe novamente o modelo CSV e copie o cabecalho exato

---

## Parar o sistema

No Prompt de Comando onde ele esta rodando, aperte **Ctrl + C**.

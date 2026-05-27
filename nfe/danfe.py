import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import barcode
from barcode.writer import ImageWriter


class DANFEGenerator:

    def __init__(self, output_dir='danfes'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._setup_styles()

    def _setup_styles(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='DANFETitle',
            fontSize=10,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            leading=12,
        ))
        self.styles.add(ParagraphStyle(
            name='DANFESmall',
            fontSize=6,
            fontName='Helvetica',
            alignment=TA_LEFT,
            leading=7,
        ))
        self.styles.add(ParagraphStyle(
            name='DANFESmallBold',
            fontSize=6,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            leading=7,
        ))
        self.styles.add(ParagraphStyle(
            name='DANFEValue',
            fontSize=8,
            fontName='Helvetica',
            alignment=TA_LEFT,
            leading=10,
        ))
        self.styles.add(ParagraphStyle(
            name='DANFEValueBold',
            fontSize=8,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            leading=10,
        ))
        self.styles.add(ParagraphStyle(
            name='DANFELabel',
            fontSize=5,
            fontName='Helvetica',
            alignment=TA_LEFT,
            leading=6,
            textColor=colors.grey,
        ))
        self.styles.add(ParagraphStyle(
            name='DANFEValueCenter',
            fontSize=8,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            leading=10,
        ))
        self.styles.add(ParagraphStyle(
            name='DANFEValueRight',
            fontSize=8,
            fontName='Helvetica',
            alignment=TA_RIGHT,
            leading=10,
        ))
        self.styles.add(ParagraphStyle(
            name='DANFEChave',
            fontSize=7,
            fontName='Helvetica',
            alignment=TA_CENTER,
            leading=9,
        ))

    def gerar(self, dados_nfe, chave_acesso, protocolo='', filename=None):
        if filename is None:
            filename = f'DANFE_{chave_acesso}.pdf'

        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=8 * mm,
            rightMargin=8 * mm,
            topMargin=8 * mm,
            bottomMargin=8 * mm,
        )

        elements = []
        page_width = A4[0] - 16 * mm

        elements.append(self._header(dados_nfe, chave_acesso, protocolo, page_width))
        elements.append(Spacer(1, 2 * mm))
        elements.append(self._destinatario(dados_nfe, page_width))
        elements.append(Spacer(1, 2 * mm))
        elements.append(self._produtos(dados_nfe, page_width))
        elements.append(Spacer(1, 2 * mm))
        elements.append(self._totais(dados_nfe, page_width))
        elements.append(Spacer(1, 2 * mm))
        elements.append(self._transporte(dados_nfe, page_width))
        elements.append(Spacer(1, 2 * mm))
        elements.append(self._info_adicionais(dados_nfe, page_width))

        doc.build(elements)
        return filepath

    def _gerar_barcode_image(self, chave):
        code128 = barcode.get('code128', chave, writer=ImageWriter())
        buffer = BytesIO()
        code128.write(buffer, options={
            'module_width': 0.3,
            'module_height': 10,
            'font_size': 0,
            'text_distance': 1,
            'quiet_zone': 2,
        })
        buffer.seek(0)
        return Image(buffer, width=160 * mm, height=12 * mm)

    def _cell(self, label, value, style='DANFEValue'):
        return [
            Paragraph(label, self.styles['DANFELabel']),
            Paragraph(str(value), self.styles[style]),
        ]

    def _header(self, dados, chave, protocolo, width):
        emit = dados.get('emitente', {})
        ender = emit.get('endereco', {})
        ide = dados.get('ide', {})

        col1_content = []
        col1_content.append(Paragraph(emit.get('razao_social', ''), self.styles['DANFEValueBold']))
        if emit.get('nome_fantasia'):
            col1_content.append(Paragraph(emit['nome_fantasia'], self.styles['DANFEValue']))
        endereco_str = f"{ender.get('logradouro', '')}, {ender.get('numero', '')} - {ender.get('bairro', '')}"
        col1_content.append(Paragraph(endereco_str, self.styles['DANFESmall']))
        mun_str = f"{ender.get('municipio', '')} - {ender.get('uf', '')} CEP: {ender.get('cep', '')}"
        col1_content.append(Paragraph(mun_str, self.styles['DANFESmall']))
        col1_content.append(Paragraph(f"CNPJ: {self._fmt_cnpj(emit.get('cnpj', ''))} IE: {emit.get('ie', '')}", self.styles['DANFESmall']))

        col2_content = []
        col2_content.append(Paragraph('DANFE', self.styles['DANFETitle']))
        col2_content.append(Paragraph('Documento Auxiliar da<br/>Nota Fiscal Eletronica', self.styles['DANFESmall']))
        tipo = 'ENTRADA' if ide.get('tipo_operacao') == '0' else 'SAIDA'
        col2_content.append(Paragraph(f'{tipo}', self.styles['DANFEValueCenter']))
        col2_content.append(Paragraph(f"N. {str(ide.get('numero', '')).zfill(9)}", self.styles['DANFEValueCenter']))
        col2_content.append(Paragraph(f"Serie {ide.get('serie', '1')}", self.styles['DANFEValueCenter']))

        chave_fmt = ' '.join(chave[i:i+4] for i in range(0, len(chave), 4))

        col3_content = []
        try:
            barcode_img = self._gerar_barcode_image(chave)
            col3_content.append(barcode_img)
        except Exception:
            col3_content.append(Paragraph('CODIGO DE BARRAS', self.styles['DANFEValueCenter']))
        col3_content.append(Paragraph(f'CHAVE DE ACESSO', self.styles['DANFELabel']))
        col3_content.append(Paragraph(chave_fmt, self.styles['DANFEChave']))
        if protocolo:
            col3_content.append(Paragraph(f'Protocolo: {protocolo}', self.styles['DANFESmall']))

        data = [[col1_content, col2_content, col3_content]]
        col_widths = [width * 0.35, width * 0.15, width * 0.50]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 1 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))
        return t

    def _destinatario(self, dados, width):
        dest = dados.get('destinatario', {})
        doc = dest.get('cnpj_cpf', '')

        data = [
            [Paragraph('DESTINATARIO/REMETENTE', self.styles['DANFESmallBold']), '', '', ''],
            [
                self._cell('NOME/RAZAO SOCIAL', dest.get('razao_social', '')),
                self._cell('CNPJ/CPF', self._fmt_doc(doc)),
                self._cell('DATA EMISSAO', dados.get('ide', {}).get('data_emissao', '')),
                [],
            ],
            [
                self._cell('ENDERECO', f"{dest.get('logradouro', '')}, {dest.get('numero', '')}"),
                self._cell('BAIRRO', dest.get('bairro', '')),
                self._cell('CEP', dest.get('cep', '')),
                self._cell('UF', dest.get('uf', '')),
            ],
            [
                self._cell('MUNICIPIO', dest.get('municipio', '')),
                self._cell('TELEFONE', dest.get('telefone', '')),
                self._cell('IE', dest.get('ie', '')),
                [],
            ],
        ]

        col_widths = [width * 0.40, width * 0.25, width * 0.20, width * 0.15]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 * mm),
        ]))
        return t

    def _produtos(self, dados, width):
        produtos = dados.get('produtos', [])

        header = [
            Paragraph('CODIGO', self.styles['DANFESmallBold']),
            Paragraph('DESCRICAO', self.styles['DANFESmallBold']),
            Paragraph('NCM', self.styles['DANFESmallBold']),
            Paragraph('CFOP', self.styles['DANFESmallBold']),
            Paragraph('UN', self.styles['DANFESmallBold']),
            Paragraph('QTD', self.styles['DANFESmallBold']),
            Paragraph('VL UNIT', self.styles['DANFESmallBold']),
            Paragraph('VL TOTAL', self.styles['DANFESmallBold']),
        ]

        data = [
            [Paragraph('DADOS DOS PRODUTOS/SERVICOS', self.styles['DANFESmallBold']),
             '', '', '', '', '', '', ''],
            header,
        ]

        for p in produtos:
            row = [
                Paragraph(str(p.get('codigo', '')), self.styles['DANFESmall']),
                Paragraph(str(p.get('descricao', '')), self.styles['DANFESmall']),
                Paragraph(str(p.get('ncm', '')), self.styles['DANFESmall']),
                Paragraph(str(p.get('cfop', '')), self.styles['DANFESmall']),
                Paragraph(str(p.get('unidade', '')), self.styles['DANFESmall']),
                Paragraph(self._fmt_number(p.get('quantidade', 0), 4), self.styles['DANFESmall']),
                Paragraph(self._fmt_number(p.get('valor_unitario', 0), 4), self.styles['DANFESmall']),
                Paragraph(self._fmt_number(p.get('valor_total', 0), 2), self.styles['DANFESmall']),
            ]
            data.append(row)

        col_widths = [
            width * 0.10, width * 0.30, width * 0.10, width * 0.07,
            width * 0.05, width * 0.10, width * 0.14, width * 0.14,
        ]
        t = Table(data, colWidths=col_widths)
        style = [
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 1), (-1, -1), 0.25, colors.grey),
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('BACKGROUND', (0, 1), (-1, 1), colors.Color(0.95, 0.95, 0.95)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 * mm),
            ('ALIGN', (5, 2), (-1, -1), 'RIGHT'),
        ]
        t.setStyle(TableStyle(style))
        return t

    def _totais(self, dados, width):
        totais = dados.get('totais', {})

        data = [
            [Paragraph('CALCULO DO IMPOSTO', self.styles['DANFESmallBold']),
             '', '', '', ''],
            [
                self._cell('BASE CALCULO ICMS', self._fmt_number(totais.get('v_bc', 0))),
                self._cell('VALOR ICMS', self._fmt_number(totais.get('v_icms', 0))),
                self._cell('VALOR PRODUTOS', self._fmt_number(totais.get('v_prod', 0))),
                self._cell('VALOR FRETE', self._fmt_number(totais.get('v_frete', 0))),
                self._cell('VALOR TOTAL NF', self._fmt_number(totais.get('v_nf', 0)), 'DANFEValueBold'),
            ],
            [
                self._cell('VALOR PIS', self._fmt_number(totais.get('v_pis', 0))),
                self._cell('VALOR COFINS', self._fmt_number(totais.get('v_cofins', 0))),
                self._cell('VALOR DESCONTO', self._fmt_number(totais.get('v_desc', 0))),
                self._cell('OUTRAS DESPESAS', self._fmt_number(totais.get('v_outros', 0))),
                [],
            ],
        ]

        col_widths = [width * 0.20] * 5
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 * mm),
        ]))
        return t

    def _transporte(self, dados, width):
        transp = dados.get('transporte', {})
        mod_frete_map = {
            '0': 'Emitente', '1': 'Destinatario', '2': 'Terceiros',
            '3': 'Proprio Remetente', '4': 'Proprio Destinatario', '9': 'Sem Frete',
        }
        mod = mod_frete_map.get(transp.get('mod_frete', '9'), 'Sem Frete')

        data = [
            [Paragraph('TRANSPORTADOR/VOLUMES', self.styles['DANFESmallBold']), '', '', ''],
            [
                self._cell('FRETE', mod),
                self._cell('TRANSPORTADORA', transp.get('transportadora_nome', '')),
                self._cell('VOLUMES', str(transp.get('volumes_qtd', ''))),
                self._cell('ESPECIE', transp.get('volumes_especie', '')),
            ],
        ]

        col_widths = [width * 0.15, width * 0.45, width * 0.15, width * 0.25]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 * mm),
        ]))
        return t

    def _info_adicionais(self, dados, width):
        info = dados.get('info_adicionais', '')
        data = [
            [Paragraph('INFORMACOES ADICIONAIS', self.styles['DANFESmallBold'])],
            [Paragraph(info, self.styles['DANFESmall'])],
        ]
        t = Table(data, colWidths=[width])
        t.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]))
        return t

    @staticmethod
    def _fmt_cnpj(cnpj):
        cnpj = str(cnpj).zfill(14)
        return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'

    @staticmethod
    def _fmt_doc(doc):
        doc = ''.join(c for c in doc if c.isdigit())
        if len(doc) == 14:
            return f'{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}'
        if len(doc) == 11:
            return f'{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}'
        return doc

    @staticmethod
    def _fmt_number(value, decimals=2):
        try:
            return f'{float(value):,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        except (ValueError, TypeError):
            return '0,00'

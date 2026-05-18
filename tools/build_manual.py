#!/usr/bin/env python3
"""Build the GB-Tracker Pro user manual as a PDF.

Design system:
  Palette ripresa dal ROM (navy/cyan/magenta/yellow/green/orange).
  Tipografia: Helvetica per il corpo, Courier per shortcut/tabelle.
  Header colorati, callout box per Tips/Note, layout aerato.
"""

import os
import sys
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image,
        Table, TableStyle, KeepTogether, Flowable
    )
    from reportlab.pdfgen import canvas
except ImportError:
    print("Installing reportlab...")
    os.system(f"{sys.executable} -m pip install reportlab")
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image,
        Table, TableStyle, KeepTogether, Flowable
    )
    from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent.parent.resolve()
SHOTS = ROOT / 'manual' / 'screenshots'
OUTPUT = ROOT / 'GB_TRACKER_PRO_Manual.pdf'

# ----- Design System -----
NAVY    = colors.HexColor('#1A2454')
CYAN    = colors.HexColor('#5BD9DF')
MAGENTA = colors.HexColor('#E16ABE')
YELLOW  = colors.HexColor('#FCE94F')
GREEN   = colors.HexColor('#73D216')
ORANGE  = colors.HexColor('#F57900')
DARKRED = colors.HexColor('#8B0000')
PURPLE  = colors.HexColor('#9F50C7')
INK     = colors.HexColor('#1B1B1F')
PAPER   = colors.HexColor('#FAFAF7')
SUBTLE  = colors.HexColor('#E6E6DF')
ACCENT  = colors.HexColor('#403A87')

PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
MARGIN_Y = 18 * mm


# ----- Custom Flowables -----
class HRule(Flowable):
    def __init__(self, width=None, thickness=0.6, color=None, top=4, bottom=6):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color or SUBTLE
        self.top = top
        self.bottom = bottom

    def wrap(self, availWidth, availHeight):
        self.W = self.width or availWidth
        self.H = self.thickness + self.top + self.bottom
        return self.W, self.H

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        y = self.bottom
        self.canv.line(0, y, self.W, y)


class SectionBanner(Flowable):
    """Colored banner with section title."""
    def __init__(self, number, title, bg=NAVY, fg=YELLOW, width=None, height=14*mm):
        Flowable.__init__(self)
        self.number = number
        self.title = title
        self.bg = bg
        self.fg = fg
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        self.W = self.width or availWidth
        return self.W, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.rect(0, 0, self.W, self.height, fill=1, stroke=0)
        # Number block
        c.setFillColor(MAGENTA)
        c.rect(0, 0, self.height, self.height, fill=1, stroke=0)
        c.setFillColor(YELLOW)
        c.setFont('Helvetica-Bold', 16)
        nstr = str(self.number)
        # Center number in the square
        tw = c.stringWidth(nstr, 'Helvetica-Bold', 16)
        c.drawString((self.height - tw) / 2, self.height / 2 - 5, nstr)
        # Title
        c.setFillColor(self.fg)
        c.setFont('Helvetica-Bold', 13)
        c.drawString(self.height + 6, self.height / 2 - 4, self.title)


class GlyphSwatch(Flowable):
    """A row of color swatches showing the ROM palette."""
    def __init__(self, width=None, height=18*mm):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.swatches = [
            ('NAVY',    NAVY,    'background'),
            ('CYAN',    CYAN,    'normal text'),
            ('MAGENTA', MAGENTA, 'title bar'),
            ('YELLOW',  YELLOW,  'column hdr'),
            ('GREEN',   GREEN,   'cursor cell'),
            ('DARKRED', DARKRED, 'cursor row'),
            ('ORANGE',  ORANGE,  'playing row'),
            ('PURPLE',  PURPLE,  'dim text'),
        ]

    def wrap(self, availWidth, availHeight):
        self.W = self.width or availWidth
        return self.W, self.height

    def draw(self):
        c = self.canv
        n = len(self.swatches)
        sw = (self.W - 4 * (n - 1)) / n
        for i, (name, col, role) in enumerate(self.swatches):
            x = i * (sw + 4)
            # Color block
            c.setFillColor(col)
            c.rect(x, self.height - 12*mm, sw, 12*mm, fill=1, stroke=0)
            # Name
            c.setFillColor(INK)
            c.setFont('Helvetica-Bold', 7)
            c.drawString(x + 2, self.height - 16*mm, name)
            # Role
            c.setFillColor(colors.gray)
            c.setFont('Helvetica', 6.5)
            c.drawString(x + 2, self.height - 18*mm, role)


# ----- Page template with footer -----
def add_page_chrome(canvas_obj, doc):
    canvas_obj.saveState()
    # Header band — thin coloured strip
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, PAGE_H - 5*mm, PAGE_W, 5*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(MAGENTA)
    canvas_obj.rect(0, PAGE_H - 5*mm, 25*mm, 5*mm, fill=1, stroke=0)

    # Footer
    canvas_obj.setFillColor(SUBTLE)
    canvas_obj.rect(0, 0, PAGE_W, 8*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(INK)
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.drawString(MARGIN_X, 3*mm, 'GB-Tracker Pro · User Manual')
    canvas_obj.drawRightString(PAGE_W - MARGIN_X, 3*mm, f'Pagina {doc.page}')
    canvas_obj.restoreState()


def add_cover_chrome(canvas_obj, doc):
    """Cover page only — no footer."""
    canvas_obj.saveState()
    # Full-bleed navy background
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Magenta band at top
    canvas_obj.setFillColor(MAGENTA)
    canvas_obj.rect(0, PAGE_H - 22*mm, PAGE_W, 22*mm, fill=1, stroke=0)
    # Cyan accent band
    canvas_obj.setFillColor(CYAN)
    canvas_obj.rect(0, PAGE_H - 26*mm, PAGE_W, 2*mm, fill=1, stroke=0)
    # Bottom yellow strip
    canvas_obj.setFillColor(YELLOW)
    canvas_obj.rect(0, 0, PAGE_W, 6*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(GREEN)
    canvas_obj.rect(0, 6*mm, PAGE_W, 1.5*mm, fill=1, stroke=0)
    canvas_obj.restoreState()


# ----- Styles -----
def make_styles():
    base = getSampleStyleSheet()
    styles = {}
    styles['Body'] = ParagraphStyle(
        'Body', parent=base['Normal'], fontName='Helvetica', fontSize=10.5,
        leading=14.5, textColor=INK, alignment=TA_LEFT, spaceAfter=4)
    styles['BodyJustify'] = ParagraphStyle(
        'BodyJustify', parent=styles['Body'], alignment=TA_JUSTIFY)
    styles['H2'] = ParagraphStyle(
        'H2', parent=base['Heading2'], fontName='Helvetica-Bold', fontSize=13,
        leading=18, textColor=NAVY, spaceBefore=8, spaceAfter=4)
    styles['H3'] = ParagraphStyle(
        'H3', parent=base['Heading3'], fontName='Helvetica-Bold', fontSize=11,
        leading=14, textColor=ACCENT, spaceBefore=6, spaceAfter=2)
    styles['Caption'] = ParagraphStyle(
        'Caption', parent=base['Italic'], fontName='Helvetica-Oblique',
        fontSize=8.5, leading=11, textColor=colors.gray, alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=8)
    styles['Code'] = ParagraphStyle(
        'Code', parent=base['Code'], fontName='Courier', fontSize=9.5,
        leading=12, textColor=INK, backColor=SUBTLE, borderColor=SUBTLE,
        borderPadding=4, spaceAfter=4)
    styles['CoverTitle'] = ParagraphStyle(
        'CoverTitle', parent=base['Title'], fontName='Helvetica-Bold',
        fontSize=42, leading=46, textColor=YELLOW, alignment=TA_LEFT)
    styles['CoverSubtitle'] = ParagraphStyle(
        'CoverSubtitle', parent=base['Normal'], fontName='Helvetica',
        fontSize=14, leading=18, textColor=CYAN, alignment=TA_LEFT)
    styles['CoverTag'] = ParagraphStyle(
        'CoverTag', parent=base['Normal'], fontName='Helvetica-Bold',
        fontSize=10, leading=12, textColor=MAGENTA, alignment=TA_LEFT)
    styles['CoverFoot'] = ParagraphStyle(
        'CoverFoot', parent=base['Normal'], fontName='Helvetica',
        fontSize=9, leading=12, textColor=PAPER, alignment=TA_LEFT)
    styles['TipTitle'] = ParagraphStyle(
        'TipTitle', parent=base['Normal'], fontName='Helvetica-Bold',
        fontSize=9, leading=11, textColor=PAPER)
    styles['TipBody'] = ParagraphStyle(
        'TipBody', parent=base['Normal'], fontName='Helvetica',
        fontSize=9.5, leading=12, textColor=INK)
    return styles


def callout(styles, kind, body_html):
    """Coloured callout box.  kind ∈ {tip, note, warn}."""
    palette = {
        'tip':  (GREEN,   'SUGGERIMENTO'),
        'note': (NAVY,    'NOTA'),
        'warn': (ORANGE,  'ATTENZIONE'),
    }
    color, label = palette[kind]
    head = Paragraph(label, styles['TipTitle'])
    body = Paragraph(body_html, styles['TipBody'])
    inner = Table([[head], [body]], colWidths=['*'])
    inner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), color),
        ('TEXTCOLOR',  (0, 0), (0, 0), PAPER),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING',  (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -1), PAPER),
        ('BOX', (0, 0), (-1, -1), 0.6, color),
    ]))
    return KeepTogether(inner)


def screenshot_image(name, width_mm):
    """Return just the Image flowable (no caption)."""
    img_path = SHOTS / name
    return Image(str(img_path), width=width_mm * mm,
                 height=width_mm * mm * 144 / 160)


def screenshot(name, width_mm, caption=None, styles=None):
    """Return a list with the image + optional caption."""
    items = [screenshot_image(name, width_mm)]
    if caption and styles is not None:
        items.append(Paragraph(caption, styles['Caption']))
    return items


def two_image_row(name_left, caption_left, name_right, caption_right, styles, width_mm=75):
    """Two-image row implemented as a Table of Images + Paragraphs in
    separate cells (no nested KeepTogether)."""
    img_l = screenshot_image(name_left, width_mm)
    img_r = screenshot_image(name_right, width_mm)
    cap_l = Paragraph(caption_left, styles['Caption'])
    cap_r = Paragraph(caption_right, styles['Caption'])
    inner_w = PAGE_W - 2 * MARGIN_X
    cw = inner_w / 2
    t = Table(
        [[img_l, img_r], [cap_l, cap_r]],
        colWidths=[cw, cw]
    )
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


def image_with_text_row(image_name, image_width_mm, text_paragraphs, styles):
    """Image left, text right.  Use a simple Table with flowable cells."""
    img = screenshot_image(image_name, image_width_mm)
    inner_w = PAGE_W - 2 * MARGIN_X
    left_w = image_width_mm * mm + 4 * mm
    right_w = inner_w - left_w
    # Wrap text paragraphs in a nested Table so the cell receives one Flowable.
    text_cell = Table([[p] for p in text_paragraphs], colWidths=[right_w])
    text_cell.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t = Table(
        [[img, text_cell]],
        colWidths=[left_w, right_w]
    )
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    return t


def kv_table(rows, bg_header=NAVY):
    t = Table(rows, colWidths=[45*mm, '*'])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('FONTNAME', (0, 0), (0, -1), 'Courier-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), ACCENT),
        ('TEXTCOLOR', (1, 0), (1, -1), INK),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, SUBTLE),
        ('BACKGROUND', (0, 0), (-1, -1), PAPER),
    ]))
    return t


def num_table(headers, rows, col_widths=None):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), YELLOW),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (0, 1), (0, -1), 'Courier-Bold'),
        ('TEXTCOLOR', (0, 1), (0, -1), ACCENT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PAPER, SUBTLE]),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


# ============================================================
# Build the document
# ============================================================
def build():
    styles = make_styles()
    story = []

    # ===== COVER =====
    story.append(Spacer(1, 60*mm))
    story.append(Paragraph('GB-TRACKER<br/>PRO', styles['CoverTitle']))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'Un tracker musicale a 4 canali per Game Boy Color',
        styles['CoverSubtitle']))
    story.append(Spacer(1, 12*mm))
    story.append(Paragraph('VERSIONE 1.0 · MANUALE UTENTE', styles['CoverTag']))
    story.append(Spacer(1, 90*mm))
    story.append(Paragraph(
        'Compatibile con qualunque emulatore Game Boy Color o cartuccia '
        'flash MBC5 con SRAM e batteria. ROM: 32 KB · SRAM: 32 KB.',
        styles['CoverFoot']))
    story.append(PageBreak())

    # ===== Indice =====
    story.append(SectionBanner(0, 'INDICE'))
    story.append(Spacer(1, 4*mm))
    toc_rows = [
        ('1', 'Panoramica',                                    '3'),
        ('2', 'Controlli (mappatura tasti)',                   '4'),
        ('3', "L'interfaccia del pattern editor",              '5'),
        ('4', 'Strumenti, banco wave e drum kit',              '6'),
        ('5', 'Editing del pattern',                           '8'),
        ('6', 'Salvataggio e richiamo dei brani',              '9'),
        ('7', "La cover demo — Per Elisa (Beethoven)",   '10'),
        ('8', 'Uso su flashcart + tool fts_tool.py',          '11'),
        ('9', 'Riferimento tecnico',                          '12'),
    ]
    toc_data = [['#', 'Sezione', 'Pag.']] + toc_rows
    toc = Table(toc_data, colWidths=[15*mm, '*', 18*mm])
    toc.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), YELLOW),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10.5),
        ('TEXTCOLOR', (0, 1), (0, -1), ACCENT),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, SUBTLE),
    ]))
    story.append(toc)
    story.append(Spacer(1, 8*mm))
    story.append(HRule())
    story.append(Paragraph(
        'Palette dell\'interfaccia (vedi sezione 3):', styles['H3']))
    story.append(GlyphSwatch())
    story.append(PageBreak())

    # ===== 1. Panoramica =====
    story.append(SectionBanner(1, 'PANORAMICA'))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'GB-Tracker Pro è un porting ridotto del leggendario tracker FastTracker II '
        'per il Game Boy Color. Sfrutta in pieno i 4 canali audio hardware del GBC '
        'e una palette CGB a 8 colori, offrendo una workstation portatile '
        'minimale ma completa.',
        styles['BodyJustify']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        'Le canzoni sono composte da <b>4 pattern</b> di 32 righe ciascuno. '
        'Ogni riga ha 4 colonne, una per ciascun canale (P1, P2, WV, NO). '
        'Una <b>order list</b> determina la sequenza con cui i pattern '
        'vengono suonati. Il <b>banco strumenti</b> contiene 32 waveform '
        'per il canale wave, 16 profili envelope/duty per i due canali pulse '
        'e 16 percussioni per il canale noise.',
        styles['BodyJustify']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        'All\'accensione il ROM parte con un <b>brano vuoto</b>, pronto per essere '
        'composto. Una <b>cover demo della canzone tradizionale russa Per Elisa</b> '
        '(1810, di pubblico dominio) viene pre-installata nello <b>Slot 4</b> dei '
        'salvataggi al primo boot, e si carica con due pressioni di tasto.',
        styles['BodyJustify']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        'I brani vengono salvati in <b>4 slot persistenti</b> nella SRAM con '
        'batteria tampone (32 KB totali; ogni slot occupa 2 KB e contiene tutti '
        'e 4 i pattern + order list + speed). Su flashcart tipo <i>EZ-Flash Junior</i> '
        'o <i>Everdrive</i>, i salvataggi vengono automaticamente esportati come '
        'file <code>.sav</code> su microSD — vedi sezione 8.',
        styles['BodyJustify']))

    story.append(Spacer(1, 4*mm))
    story.append(callout(styles, 'tip',
        'Il ROM è <i>CGB-only</i>: deve girare su un emulatore o hardware Game Boy Color. '
        'I principali emulatori desktop (BGB, SameBoy, mGBA) sono pienamente supportati. '
        'Su EZ-Flash Junior e tutte le flashcart serie con MBC5+RAM+battery i salvataggi '
        'vengono preservati come <code>GB_TRACKER_PRO.sav</code> sulla microSD.'))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('Architettura hardware sfruttata', styles['H2']))
    arch = num_table(
        ['Risorsa', 'Uso'],
        [
            ['CPU SM83 (~4 MHz)', 'Engine pattern + UI, interrupt VBlank a 59.7 Hz'],
            ['CGB BG palettes (×8)', 'Riempite ciascuna con 4 colori RGB555: title bar, pattern, cursor cell, cursor row, playing row, status, ecc.'],
            ['Tile data $8000', '128 tile font 8×8 a 2bpp generate da gen_font.py'],
            ['Channel 1 / 2 (Pulse)', 'Lead e counter-melody, 4 duty + envelope hardware'],
            ['Channel 3 (Wave)', 'PCM 32 sample × 4 bit: cambio waveform per nota'],
            ['Channel 4 (Noise)', 'Drum kit a 16 slot, envelope + LFSR programmabile'],
            ['MBC5 SRAM (32 KB)', 'Magic header "FTGB" v2 + 4 slot da 2 KB ognuno'],
            ['Battery backup', "Mantiene i 4 slot fra accensioni; su flashcart il .sav viene esportato su microSD"],
        ],
        col_widths=[55*mm, '*'])
    story.append(arch)

    story.append(PageBreak())

    # ===== 2. Controlli =====
    story.append(SectionBanner(2, 'CONTROLLI'))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'Tutto il flusso si controlla con il D-pad e i quattro tasti del Game Boy. '
        'Il tasto <b>Select</b> agisce come modificatore: tenutolo premuto, le altre '
        'combinazioni cambiano funzione.',
        styles['BodyJustify']))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('In modalità pattern editor', styles['H3']))
    p_ctrls = num_table(
        ['Tasto', 'Funzione'],
        [
            ['↑ / ↓',              'Sposta il cursore in alto/basso fra le righe.'],
            ['← / →',              'Sposta il cursore fra i 4 canali (P1, P2, WV, NO).'],
            ['A',                  "Inserisce la nota corrente nella cella sotto il cursore e fa avanzare di una riga (auto-step)."],
            ['B',                  'Cancella il contenuto della cella sotto il cursore.'],
            ['Start',              'Avvia o ferma la riproduzione del brano.'],
            ['Select + ↑ / ↓',     'Cambia la nota corrente di un semitono (verso l\'alto/basso).'],
            ['Select + ← / →',     'Cambia lo strumento corrente (1..16, ciclico).'],
            ['Select + A',         'Anteprima sonora della nota corrente sul canale del cursore.'],
            ['Select + B',         'Cambia il pattern corrente in modifica (0..3).'],
            ['Select + Start',     'Apre il menu Salva/Carica brano.'],
        ],
        col_widths=[40*mm, '*'])
    story.append(p_ctrls)

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Nel menu Salva/Carica', styles['H3']))
    m_ctrls = num_table(
        ['Tasto', 'Funzione'],
        [
            ['↑ / ↓',              'Seleziona lo slot (1..4).'],
            ['A',                  'Carica il brano salvato nello slot evidenziato. Niente accade se lo slot è vuoto.'],
            ['B',                  'Salva il brano corrente nello slot evidenziato (sovrascrive).'],
            ['Select',             'Torna al pattern editor.'],
        ],
        col_widths=[40*mm, '*'])
    story.append(m_ctrls)

    story.append(Spacer(1, 4*mm))
    story.append(callout(styles, 'note',
        'Sulla maggior parte degli emulatori la mappatura tasti predefinita è: '
        '<b>frecce</b> = D-pad, <b>Z</b> = B, <b>X</b> = A, <b>Invio</b> = Start, '
        '<b>Tab</b> = Select. Su hardware reale è chiaramente fisica.'))

    story.append(PageBreak())

    # ===== 3. L'interfaccia del pattern editor =====
    story.append(SectionBanner(3, 'L\'INTERFACCIA DEL PATTERN EDITOR'))
    story.append(Spacer(1, 4*mm))

    # Image + description (image on left, text on right)
    desc_paragraphs = [
        Paragraph('Lo schermo è organizzato in 5 fasce orizzontali:', styles['Body']),
        Paragraph(
            '<b>1. Title bar</b> (rosa) — Nome del programma e versione.', styles['Body']),
        Paragraph(
            '<b>2. Status bar</b> (verde su nero) — Pattern corrente '
            '(<font face="Courier">PT:XX</font>), nota selezionata '
            '(<font face="Courier">N:NNN</font>) e tempo della canzone in '
            '<b>BPM</b> (<font face="Courier">BPM:XXX</font>), calcolato come '
            '900 ÷ Speed (es. Speed 8 → 112 BPM, Speed 6 → 150 BPM).',
            styles['Body']),
        Paragraph(
            '<b>3. Column header</b> (giallo) — Canali: P1, P2 (pulse), WV (wave), NO (noise).',
            styles['Body']),
        Paragraph(
            '<b>4. Pattern view</b> — 12 righe visibili che scorrono insieme al cursore. '
            'Riga cursore in <font color="#8B0000"><b>rosso scuro</b></font>, '
            'cella attiva in <font color="#73D216"><b>verde</b></font>, '
            "riga in playback in <font color='#F57900'><b>arancione</b></font>.",
            styles['Body']),
        Paragraph(
            '<b>5. Help bar</b> — Promemoria comandi e indicatore <font face="Courier">R</font> '
            'della riga di playback.',
            styles['Body']),
    ]
    story.append(image_with_text_row('02_pattern_main.png', 75, desc_paragraphs, styles))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('Lettura di una cella', styles['H3']))
    story.append(Paragraph(
        'Ogni cella mostra tre caratteri: il nome della nota (<font face="Courier">C-, C#, D-, …</font>) '
        'più la cifra dell\'ottava (2..6). Es. <font face="Courier"><b>C-5</b></font> = Do della 5ª ottava. '
        'Una cella vuota appare come <font face="Courier"><b>...</b></font>, una cella "note-off" come '
        '<font face="Courier"><b>OFF</b></font>. Sul canale Noise il valore della nota viene ignorato — '
        'è il numero strumento a scegliere il drum.',
        styles['BodyJustify']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Stato iniziale e cursore in azione', styles['H3']))
    story.append(two_image_row(
        '01_boot_empty.png', 'Schermata di boot: brano vuoto, cursore a 00/P1.',
        '03_pattern_cursor.png', 'Per Elisa caricata, cursore a riga 08 / WV.',
        styles, width_mm=68))

    story.append(PageBreak())

    # ===== 4. Strumenti =====
    story.append(SectionBanner(4, 'STRUMENTI, BANCO WAVE E DRUM KIT'))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'Ogni canale interpreta il numero di strumento (1..N) in base al proprio banco. '
        'Lo stesso numero produce timbri diversi su canali diversi.',
        styles['BodyJustify']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Canali Pulse 1 e Pulse 2 — 16 profili duty/envelope', styles['H3']))
    pulse_rows = [
        ['01', 'Sustain50',  'Duty 50% · vol max · nessun decay'],
        ['02', 'Pluck50',    'Duty 50% · pluck con decay medio'],
        ['03', 'Sustain25',  'Duty 25% · vol max'],
        ['04', 'Pluck25',    'Duty 25% · decay medio'],
        ['05', 'Sustain12',  'Duty 12.5% · tono sottile'],
        ['06', 'Stab12',     'Duty 12.5% · decay velocissimo'],
        ['07', 'Sustain75',  'Duty 75% · timbro più rotondo'],
        ['08', 'Smooth75',   'Duty 75% · decay lento'],
        ['09', 'Soft50',     'Duty 50% · vol metà'],
        ['10', 'Stac50',     'Duty 50% · staccato (decay extra fast)'],
        ['11', 'Pluck25b',   'Duty 25% · pluck più tagliente'],
        ['12', 'Hit12',      'Duty 12.5% · hit secco'],
        ['13', 'Slow50',     'Duty 50% · decay lento (pad)'],
        ['14', 'Pad25',      'Duty 25% · pad morbido'],
        ['15', 'Decay75',    'Duty 75% · decay medio'],
        ['16', 'Whisper',    'Duty 50% · vol basso (whisper)'],
    ]
    story.append(num_table(['#', 'Nome', 'Carattere'], pulse_rows,
                            col_widths=[12*mm, 30*mm, '*']))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('Canale Wave — 32 waveform PCM', styles['H3']))
    wave_rows = [
        ['01', 'Sine',     'Onda sinusoidale pulita'],
        ['02', 'Tri',      'Triangolo'],
        ['03', 'Saw',      'Dente di sega ascendente'],
        ['04', 'SawDown',  'Dente di sega discendente'],
        ['05', 'Sq50',     'Quadra al 50%'],
        ['06', 'Sq25',     'Quadra al 25%'],
        ['07', 'Sq12',     'Quadra al 12.5%'],
        ['08', 'SoftSq',   'Quadra con transizioni dolci'],
        ['09', 'Bell',     'Campana (somma di armoniche)'],
        ['10', 'Bass',     'Bass acuto'],
        ['11', 'Vowel',    'Vocale formantica'],
        ['12', 'Noisy',    'Pseudo-rumore deterministico'],
        ['13', 'Step',     'Scala a 4 livelli'],
        ['14', 'Hollow',   'Triangolo con vertici tondi'],
        ['15', 'Pluck',    'Karplus-strong (sintesi a corda)'],
        ['16', 'Solid',    'DC (silenzio modulabile)'],
        ['17', 'Organ',    'Organo Hammond-ish con armoniche dispari'],
        ['18', 'EPiano',   'E-piano (FM 2-op morbido)'],
        ['19', 'Brass',    'Ottone (saw addolcito)'],
        ['20', 'Strings',  'Archi (saw detunate)'],
        ['21', 'SubBass',  'Sub-bass pieno e profondo'],
        ['22', 'FM',       'FM ad indice 3'],
        ['23', 'GlsBel',   'Campana vetrosa (armoniche alte)'],
        ['24', 'Reed',     'Ancia (clarinetto)'],
        ['25', 'Piano',    'Piano con decay armonico'],
        ['26', 'SynLed',   'Synth lead bright'],
        ['27', 'Buzz',     'Tone "buzz" Casio'],
        ['28', 'Thunk',    'Sinusoide saturata (warm)'],
        ['29', 'PWM',      'Pulse asimmetrico PWM'],
        ['30', 'Gritty',   'Sinusoide bitcrushed'],
        ['31', 'Harp',     'Arpa (pluck + body)'],
        ['32', 'Bass2',    'Bass con 3ª armonica'],
    ]
    story.append(num_table(['#', 'Nome', 'Carattere'], wave_rows,
                            col_widths=[12*mm, 30*mm, '*']))

    story.append(PageBreak())

    story.append(Paragraph('Canale Noise — Drum kit a 16 slot', styles['H3']))
    story.append(Paragraph(
        'Sul canale Noise il <b>valore della nota</b> in pattern viene ignorato; '
        'è il <b>numero dello strumento</b> a scegliere quale percussione suonare. '
        'Una qualunque nota non vuota (per esempio C-2) attiva il drum.',
        styles['BodyJustify']))
    story.append(Spacer(1, 2*mm))
    drum_rows = [
        ['01', 'Kick',     'Cassa profonda, breve'],
        ['02', 'Snare',    'Rullante medio (white noise)'],
        ['03', 'ClHat',    'Hi-hat chiuso (decay rapido)'],
        ['04', 'OpHat',    'Hi-hat aperto (decay lungo)'],
        ['05', 'Crash',    'Piatto crash brillante e lungo'],
        ['06', 'TomHi',    'Tom alto'],
        ['07', 'TomLo',    'Tom basso'],
        ['08', 'Clap',     'Battito mani'],
        ['09', 'Kick2',    'Cassa più "clicky"'],
        ['10', 'SnareM',   'Rullante metallico (LFSR 7-bit)'],
        ['11', 'Tick',     'Click brevissimo (ghost note)'],
        ['12', 'Cym',      'Piatto lungo metallico'],
        ['13', 'TomMid',   'Tom centrale'],
        ['14', 'Rim',      'Rim shot'],
        ['15', 'Boom',     'Boom grasso'],
        ['16', 'Sizzle',   'Sizzle acuto'],
    ]
    story.append(num_table(['#', 'Nome', 'Carattere'], drum_rows,
                            col_widths=[12*mm, 30*mm, '*']))

    story.append(Spacer(1, 4*mm))
    story.append(callout(styles, 'tip',
        'Per creare un groove credibile usa <b>strumento 1 (Kick)</b> sul battito 1, '
        '<b>strumento 2 (Snare)</b> sul battito 3, e <b>strumento 3 (ClHat)</b> '
        'per gli off-beat. Aggiungi <b>strumento 4 (OpHat)</b> o '
        '<b>strumento 5 (Crash)</b> per i fill.'))

    story.append(PageBreak())

    # ===== 5. Editing del pattern =====
    story.append(SectionBanner(5, 'EDITING DEL PATTERN'))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'Il flusso tipico per scrivere o modificare un pattern segue questi passi:',
        styles['BodyJustify']))
    story.append(Spacer(1, 2*mm))

    steps = [
        ('1. Scegli il pattern', 'Premi <b>Select + B</b> per ciclare fra i 4 pattern (0..3). Lo status bar mostra il pattern corrente come <font face="Courier">PT:00</font>.'),
        ('2. Posiziona il cursore', 'Usa il <b>D-pad</b> per spostare il cursore (rettangolo verde) sulla riga e la colonna che vuoi modificare.'),
        ('3. Scegli la nota', 'Tenendo premuto <b>Select</b>, usa <b>↑/↓</b> per cambiare la nota di un semitono. La nota viene mostrata in status bar come <font face="Courier">N:C-4</font>.'),
        ('4. Scegli lo strumento', 'Sempre con <b>Select</b>, usa <b>←/→</b> per ciclare gli strumenti (1..16). Mostrato come <font face="Courier">I:0X</font>.'),
        ('5. Inserisci', 'Premi <b>A</b>: la nota viene stampata nella cella sotto il cursore e il cursore avanza di una riga (auto-step).'),
        ('6. Cancella', 'Premi <b>B</b> per pulire la cella sotto il cursore.'),
        ('7. Ascolta', 'Premi <b>Select + A</b> per un\'anteprima singola, oppure <b>Start</b> per avviare la riproduzione completa. La riga arancione segue il playback.'),
    ]
    step_rows = [[Paragraph('<b>' + a + '</b>', styles['Body']),
                  Paragraph(b, styles['Body'])] for (a, b) in steps]
    step_tab = Table(step_rows, colWidths=[50*mm, '*'])
    step_tab.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [PAPER, SUBTLE]),
    ]))
    story.append(step_tab)

    story.append(Spacer(1, 4*mm))
    story.append(callout(styles, 'tip',
        "Per inserire una sequenza di note rapidamente: imposta la prima nota, "
        "premi A più volte (la nota si ripete e il cursore avanza), poi usa "
        "<b>Select + ↑</b> per cambiare nota e premi di nuovo A."))
    story.append(Spacer(1, 2*mm))
    story.append(callout(styles, 'note',
        'Il valore speciale <font face="Courier">OFF</font> (note-off) interrompe '
        'la nota in corso sul canale. Si inserisce dal codice; nelle versioni '
        'attuali del programma non c\'è un tasto dedicato per stamparlo a runtime.'))

    story.append(PageBreak())

    # ===== 6. Save / Load =====
    story.append(SectionBanner(6, 'SALVATAGGIO E RICHIAMO DEI BRANI'))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'La cartuccia espone 32 KB di SRAM con batteria tampone, di cui GB-Tracker Pro '
        'usa <b>4 slot da 2 KB</b> ciascuno. Ogni slot memorizza un brano completo: '
        'i <b>4 pattern</b> da 256 byte, la order list da 16 byte, e lo speed.',
        styles['BodyJustify']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        'Al primo avvio del ROM, la SRAM viene formattata e nello <b>Slot 4</b> viene '
        'pre-installata una cover chiptune di <i>Per Elisa</i> di Ludwig van Beethoven '
        '(WoO 59, 1810 — pubblico dominio; vedi sezione 7). Gli altri tre slot (1, 2, 3) '
        'iniziano vuoti, pronti per i tuoi brani.',
        styles['BodyJustify']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Aprire il menu', styles['H3']))
    story.append(Paragraph(
        'Dal pattern editor premi <b>Select + Start</b> (tieni premuto Select e premi '
        'Start). Si apre la modalità modale Save/Load con i 4 slot in elenco.',
        styles['Body']))

    story.append(Spacer(1, 4*mm))
    story.append(two_image_row(
        '04_menu_initial.png', 'Stato iniziale: Slot 4 = demo Per Elisa, Slot 1-3 vuoti.',
        '05_menu_select.png',  'Dopo qualche sessione: navighi con ↑/↓ sui tuoi brani.',
        styles, width_mm=68))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('Caricare la demo Per Elisa', styles['H3']))
    step_load = [
        ('1. Apri il menu', 'Dal pattern editor: <b>Select + Start</b>.'),
        ('2. Posizionati su Slot 4', 'Premi <b>↓</b> tre volte per portare la riga rossa su <font face="Courier">SLOT 4: SAVED</font>.'),
        ('3. Premi A', 'La demo viene copiata in memoria e parte automaticamente. Compare il toast <font face="Courier"><b>>>> LOADED &lt;&lt;&lt;</b></font>.'),
        ('4. Torna all\'editor', 'Premi <b>Select</b>: vedrai il pattern editor con le note di Per Elisa visibili e l\'indicatore di playback che scorre.'),
    ]
    rows_t = [[Paragraph('<b>'+a+'</b>', styles['Body']),
               Paragraph(b, styles['Body'])] for (a, b) in step_load]
    t = Table(rows_t, colWidths=[42*mm, '*'])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [PAPER, SUBTLE]),
    ]))
    story.append(t)

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Salvare un tuo brano', styles['H3']))
    story.append(Paragraph(
        'Posiziona la riga rossa su uno degli slot vuoti (1, 2 o 3 — lo Slot 4 contiene '
        'la demo di default) e premi <b>B</b>. Tutti e 4 i pattern + order list + speed '
        'vengono scritti in SRAM. Lo slot vuoto diventa <font face="Courier">SAVED</font> '
        'e compare il toast <font face="Courier"><b>>>> SAVED &lt;&lt;&lt;</b></font>.',
        styles['Body']))

    story.append(Spacer(1, 4*mm))
    story.append(two_image_row(
        '06_menu_saved.png',  'Toast di salvataggio.',
        '07_menu_loaded.png', 'Toast di caricamento.',
        styles, width_mm=68))

    story.append(Spacer(1, 4*mm))
    story.append(callout(styles, 'warn',
        'Salvare su uno slot già occupato <b>sovrascrive</b> il brano precedente '
        'senza chiedere conferma. Per non perdere la demo Per Elisa, salva i tuoi '
        'brani in Slot 1, 2 o 3 e lascia lo <b>Slot 4</b> intatto.'))
    story.append(Spacer(1, 2*mm))
    story.append(callout(styles, 'note',
        'La SRAM ha un magic header <font face="Courier">"FTGB"</font> v2. Se per '
        'qualunque ragione (batteria scarica, prima accensione, cambio di versione '
        'incompatibile) il magic non corrisponde, il ROM riformatta automaticamente '
        'la SRAM e reinstalla la demo Per Elisa nello Slot 4.'))

    story.append(PageBreak())

    # ===== 7. Cover demo Per Elisa =====
    story.append(SectionBanner(7, "LA COVER DEMO — PER ELISA (BEETHOVEN)"))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '<b>Per Elisa</b> (in tedesco <i>Für Elise</i>, WoO 59) è una bagatella '
        "per pianoforte composta da Ludwig van Beethoven attorno al 1810. Caduta "
        "nel dominio pubblico da decenni, è una delle melodie classiche più "
        "note in Italia: la riconoscibile frase iniziale "
        '<font face="Courier">Mi–Re#–Mi–Re#–Mi–Si–Re–Do–La</font> è '
        "letteralmente da pubblicità, suonerie e prime lezioni di pianoforte.",
        styles['BodyJustify']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "L'arrangiamento incluso è in <b>La minore</b>, ~112 BPM (Speed 8 con "
        "grid 1/16, 4 row per beat), 4 canali GBC sfruttati al massimo.",
        styles['BodyJustify']))

    story.append(Spacer(1, 4*mm))
    story.append(image_with_text_row('02_pattern_main.png', 78, [
        Paragraph('Pattern 0 (Frase A) appena caricato. La status bar mostra '
                  '<font face="Courier">BPM:112</font>. La melodia attacca su '
                  '<font face="Courier">E-5</font> seguita da '
                  '<font face="Courier">D#5 E-5 D#5 E-5 B-4 D-5 C-5 A-4</font>: '
                  'è la prima frase di Per Elisa, riconoscibile in pochi colpi. '
                  "Sotto al lead, il <b>sub-bass</b> alterna La-Mi-La a sostegno "
                  "della progressione Am→E7→Am. Nessun drum nel Pattern 0 per "
                  "preservare il carattere classico.",
                  styles['Body']),
    ], styles))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('Order list e struttura', styles['H3']))
    order_rows = [
        ['0', 'Frase A pura',     'Lead PianoSoft + counter Soft25 (arpeggio C-E-A) + SubBass warm, no drums'],
        ['1', 'Frase A pumped',   'Stessa frase A con kick + snare + hi-hat che pompano'],
        ['0', 'Frase A pura',     'Ripresa pulita'],
        ['2', 'Frase B (Do magg.)','Sezione brillante: C–D–D#–D–C–A–G–F–E poi rientro alla A'],
        ['0', 'Frase A pura',     'Ultima ripresa, energia controllata'],
        ['3', 'Outro',            'Arpeggio Am finale (La–Do–Mi–La↑) + ultima frase A + crash'],
    ]
    story.append(num_table(['Order', 'Pattern', 'Contenuto'], order_rows,
                            col_widths=[15*mm, 30*mm, '*']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Strumenti scelti nei 4 canali', styles['H3']))
    inst_rows = [
        ['ch0 — Pulse 1',  'inst 2 (PianoSoft)',
         'lead — 50% duty, vol 10 + slow decay → suono pianistico'],
        ['ch1 — Pulse 2',  'inst 3 (Soft25)',
         'counter — 25% duty, vol 9 sustained → arpeggio in sottofondo'],
        ['ch2 — Wave',     'inst 21 (SubBass), inst 17 (Organ) in P2',
         'bass warm con sine + 2°/3° armonica; volume Wave 50%'],
        ['ch3 — Noise',    '1 (Kick), 2 (Snare), 3 (ClHat), 5 (Crash)',
         'drum kit attivo solo in P1 e P3 (P0 senza drum)'],
    ]
    story.append(num_table(['Canale', 'Strumento', 'Ruolo'], inst_rows,
                            col_widths=[33*mm, 55*mm, '*']))

    story.append(Spacer(1, 4*mm))
    story.append(callout(styles, 'tip',
        "Vuoi farne una tua variazione? La cover si carica subito al boot "
        "del ROM (auto-play da WRAM). Modificala con cursore + A, e salva "
        "in <b>Slot 1, 2 o 3</b> dal menu Save/Load per non sovrascrivere "
        "l'originale (sempre richiamabile dallo <b>Slot 4</b>)."))

    story.append(PageBreak())

    # ===== 8. Flashcart + fts_tool =====
    story.append(SectionBanner(8, 'USO SU FLASHCART + TOOL FTS_TOOL.PY'))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'Tutte le flashcart serie che emulano <b>MBC5 + RAM + battery</b> '
        '(EZ-Flash Junior, Everdrive GB, BennVenn ElCheapoSD, Krikzz, ecc.) '
        'salvano automaticamente il contenuto della SRAM su microSD come file '
        '<code>.sav</code> ogni volta che il Game Boy viene spento. '
        'I tuoi brani escono quindi <b>fuori dalla cartuccia</b> senza nessun '
        'passaggio manuale.',
        styles['BodyJustify']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Workflow tipico su EZ-Flash Junior', styles['H3']))
    fc_rows = [
        ['1', 'Copia <code>GB_TRACKER_PRO.gbc</code> sulla microSD della cartuccia.'],
        ['2', "Avvia il gioco, componi e salva i tuoi brani in Slot 1/2/3 (lo Slot 4 contiene la demo Per Elisa)."],
        ['3', 'Spegni il Game Boy. Il firmware della flashcart scrive automaticamente <code>GB_TRACKER_PRO.sav</code> (32 KB) accanto al ROM sulla microSD.'],
        ['4', 'Estrai la microSD e inseriscila nel PC.'],
        ['5', 'Trasferisci, archivia o condividi i brani con i tool descritti sotto.'],
        ['6', 'Per re-iniettare un brano altrui: copia/aggiorna il <code>.sav</code> sulla microSD e rimetti la microSD nella flashcart.'],
    ]
    story.append(num_table(['#', 'Azione'], fc_rows, col_widths=[12*mm, '*']))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('Il tool fts_tool.py — manipolazione dei .sav', styles['H3']))
    story.append(Paragraph(
        'Lo script Python <code>tools/fts_tool.py</code> permette di ispezionare un '
        'file <code>.sav</code> generato dalla flashcart, di estrarre i singoli slot '
        'come file <code>.fts</code> (GB-Tracker Pro Song), e viceversa di '
        'importare un <code>.fts</code> in uno qualunque dei 4 slot di un '
        '<code>.sav</code>. Comandi principali:',
        styles['BodyJustify']))

    cmd_rows = [
        ['<code>info FILE.sav</code>',
         'Mostra cosa contiene un .sav: status di ognuno dei 4 slot, conteggio note per pattern, '
         'order list, e una preview delle prime 8 righe del Pattern 0.'],
        ['<code>extract FILE.sav DIR/</code>',
         'Estrae tutti gli slot occupati come file <code>slot_N.fts</code> nella cartella indicata.'],
        ['<code>import FILE.sav N FILE.fts</code>',
         'Inserisce il brano <code>.fts</code> nello slot N (1..4) del .sav. Sovrascrive se occupato.'],
        ['<code>clear FILE.sav N</code>',
         'Svuota lo slot N del .sav (lo marca EMPTY).'],
        ['<code>blank FILE.sav</code>',
         'Crea un .sav nuovo vuoto (32 KB con header formattato).'],
    ]
    cmd_table_data = [['Comando', 'Cosa fa']] + [[Paragraph(c, styles['Body']),
                                                  Paragraph(d, styles['Body'])]
                                                 for (c, d) in cmd_rows]
    cmd_table = Table(cmd_table_data, colWidths=[55*mm, '*'])
    cmd_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), YELLOW),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PAPER, SUBTLE]),
    ]))
    story.append(cmd_table)

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Formato del file .fts', styles['H3']))
    fts_rows = [
        ['+0..+7',   'magic <code>"FTGBSONG"</code> (8 byte ASCII)'],
        ['+8',       'versione formato (2)'],
        ['+9..+15',  'reserved (zero)'],
        ['+16..+2059', "payload da 2044 byte — formato identico a uno slot SRAM (magic $FE + speed + order_len + order list + 4 pattern)"],
    ]
    story.append(num_table(['Offset', 'Contenuto'], fts_rows,
                            col_widths=[28*mm, '*']))

    story.append(Spacer(1, 4*mm))
    story.append(callout(styles, 'tip',
        "Un file <code>.fts</code> è autoportante: contiene il brano <b>completo</b> "
        "(tutti i 4 pattern, order list e speed), quindi è perfetto per condividerlo "
        "via e-mail, Discord, archiviarlo su Git, o crearne una libreria personale."))

    story.append(PageBreak())

    # ===== 9. Tech reference =====
    story.append(SectionBanner(9, 'RIFERIMENTO TECNICO'))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('Layout della SRAM (versione 2)', styles['H3']))
    story.append(Paragraph(
        'La SRAM (banco 0, $A000..$BFFF, 8 KB) è organizzata così:',
        styles['Body']))
    sram_rows = [
        ['$A000..$A003', 'Magic <code>"FTGB"</code>'],
        ['$A004',         'Versione formato (2)'],
        ['$A005',         'Numero slot (4)'],
        ['$A006..$A00F',  'Riservato (zero)'],
        ['$A010..$A80B',  'Slot 0 (2044 byte)'],
        ['$A80C..$B007',  'Slot 1'],
        ['$B008..$B803',  'Slot 2'],
        ['$B804..$BFFF',  'Slot 3'],
    ]
    story.append(num_table(['Indirizzo', 'Contenuto'], sram_rows,
                            col_widths=[40*mm, '*']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Layout di uno slot (2044 byte)', styles['H3']))
    slot_rows = [
        ['+0',            'Magic byte $FE (segnala slot occupato)'],
        ['+1',            'Song speed (tick per riga)'],
        ['+2',            'Order list length'],
        ['+3',            'Riservato'],
        ['+4..+19',       'Order list (16 byte; $FF = end-of-song)'],
        ['+20..+275',     'Pattern 0 (32 righe × 8 byte = 256 byte)'],
        ['+276..+531',    'Pattern 1 (256 byte)'],
        ['+532..+787',    'Pattern 2 (256 byte)'],
        ['+788..+1043',   'Pattern 3 (256 byte)'],
        ['+1044..+2043',  'Riservato per espansioni future (1000 byte)'],
    ]
    story.append(num_table(['Offset', 'Contenuto'], slot_rows,
                            col_widths=[40*mm, '*']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Formato di una cella pattern', styles['H3']))
    story.append(Paragraph(
        'Ogni cella occupa <b>2 byte</b>: il primo è la nota, il secondo è lo strumento.',
        styles['Body']))
    cell_rows = [
        ['$00',         'Cella vuota (mantieni stato precedente)'],
        ['$01..$3C',    'Nota 1..60: $01=C-2, $0D=C-3, $19=C-4, $25=C-5, $31=C-6'],
        ['$FD',         'Note-off: spegne il canale'],
    ]
    story.append(num_table(['Valore', 'Significato'], cell_rows,
                            col_widths=[35*mm, '*']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Ricompilare la ROM', styles['H3']))
    story.append(Paragraph(
        'Dalla cartella del progetto, eseguendo <font face="Courier">python build.py</font> '
        'si rigenera la <font face="Courier">GB_TRACKER_PRO.gbc</font>. Il toolchain è RGBDS '
        '(rgbasm + rgblink + rgbfix). Gli script in <font face="Courier">tools/</font> '
        'rigenerano font, tabelle di periodo nota e banco wave da Python.',
        styles['Body']))

    story.append(Spacer(1, 6*mm))
    story.append(HRule())
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '<i>GB-Tracker Pro v1.0 — © 2026. Documento generato in Python con reportlab.</i>',
        styles['Caption']))

    # ===== Build =====
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=12*mm, bottomMargin=12*mm,
        title='GB-Tracker Pro User Manual',
        author='GB-Tracker Pro project',
    )

    # The cover page needs its own background; subsequent pages get the page chrome.
    def first_page(canv, doc):
        add_cover_chrome(canv, doc)

    def later_pages(canv, doc):
        add_page_chrome(canv, doc)

    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
    print(f'Saved {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    build()

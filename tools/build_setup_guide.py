#!/usr/bin/env python3
"""Build the GB-Tracker Pro development-environment setup guide (PDF, Italian).

Covers Windows 10/11 and macOS (Apple Silicon + Intel).
Same design system as the user manual (palette from the ROM).
Versions verified June 2026: RGBDS v1.0.1, Python 3.14.5, SameBoy v1.0.3,
mGBA 0.10.5.
"""

import os
import sys
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak,
        Table, TableStyle, KeepTogether, Flowable
    )
except ImportError:
    print("Installing reportlab...")
    os.system(f"{sys.executable} -m pip install reportlab")
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak,
        Table, TableStyle, KeepTogether, Flowable
    )

ROOT = Path(__file__).parent.parent.resolve()
OUTPUT = ROOT / 'GB_TRACKER_PRO_Guida_Sviluppo.pdf'

# ----- Design System (same as the manual) -----
NAVY    = colors.HexColor('#1A2454')
CYAN    = colors.HexColor('#5BD9DF')
MAGENTA = colors.HexColor('#E16ABE')
YELLOW  = colors.HexColor('#FCE94F')
GREEN   = colors.HexColor('#73D216')
ORANGE  = colors.HexColor('#F57900')
INK     = colors.HexColor('#1B1B1F')
PAPER   = colors.HexColor('#FAFAF7')
SUBTLE  = colors.HexColor('#E6E6DF')
ACCENT  = colors.HexColor('#403A87')

PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
MARGIN_Y = 18 * mm
INNER_W = PAGE_W - 2 * MARGIN_X


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
        c.setFillColor(MAGENTA)
        c.rect(0, 0, self.height, self.height, fill=1, stroke=0)
        c.setFillColor(YELLOW)
        c.setFont('Helvetica-Bold', 16)
        nstr = str(self.number)
        tw = c.stringWidth(nstr, 'Helvetica-Bold', 16)
        c.drawString((self.height - tw) / 2, self.height / 2 - 5, nstr)
        c.setFillColor(self.fg)
        c.setFont('Helvetica-Bold', 13)
        c.drawString(self.height + 6, self.height / 2 - 4, self.title)


class OSBadge(Flowable):
    """Small colored pill: WINDOWS / MACOS."""
    def __init__(self, label, bg):
        Flowable.__init__(self)
        self.label = label
        self.bg = bg
        self.height = 7 * mm

    def wrap(self, availWidth, availHeight):
        self.W = availWidth
        return self.W, self.height + 4

    def draw(self):
        c = self.canv
        w = c.stringWidth(self.label, 'Helvetica-Bold', 9) + 14
        c.setFillColor(self.bg)
        c.roundRect(0, 2, w, self.height, 2.5, fill=1, stroke=0)
        c.setFillColor(PAPER)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(7, 2 + self.height / 2 - 3.2, self.label)


# ----- Page chrome -----
def add_page_chrome(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, PAGE_H - 5*mm, PAGE_W, 5*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(MAGENTA)
    canvas_obj.rect(0, PAGE_H - 5*mm, 25*mm, 5*mm, fill=1, stroke=0)

    canvas_obj.setFillColor(SUBTLE)
    canvas_obj.rect(0, 0, PAGE_W, 8*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(INK)
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.drawString(MARGIN_X, 3*mm,
                          'GB-Tracker Pro · Guida all\'ambiente di sviluppo · Luigi Massari')
    canvas_obj.drawRightString(PAGE_W - MARGIN_X, 3*mm, f'Pagina {doc.page}')
    canvas_obj.restoreState()


def add_cover_chrome(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas_obj.setFillColor(MAGENTA)
    canvas_obj.rect(0, PAGE_H - 22*mm, PAGE_W, 22*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(CYAN)
    canvas_obj.rect(0, PAGE_H - 26*mm, PAGE_W, 2*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(YELLOW)
    canvas_obj.rect(0, 0, PAGE_W, 6*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(GREEN)
    canvas_obj.rect(0, 6*mm, PAGE_W, 1.5*mm, fill=1, stroke=0)
    canvas_obj.restoreState()


def on_page(canvas_obj, doc):
    if doc.page == 1:
        add_cover_chrome(canvas_obj, doc)
    else:
        add_page_chrome(canvas_obj, doc)


# ----- Styles -----
def make_styles():
    base = getSampleStyleSheet()
    s = {}
    s['Body'] = ParagraphStyle(
        'Body', parent=base['Normal'], fontName='Helvetica', fontSize=10.5,
        leading=14.5, textColor=INK, alignment=TA_LEFT, spaceAfter=4)
    s['BodyJustify'] = ParagraphStyle(
        'BodyJustify', parent=s['Body'], alignment=TA_JUSTIFY)
    s['H2'] = ParagraphStyle(
        'H2', parent=base['Heading2'], fontName='Helvetica-Bold', fontSize=13,
        leading=18, textColor=NAVY, spaceBefore=8, spaceAfter=4)
    s['H3'] = ParagraphStyle(
        'H3', parent=base['Heading3'], fontName='Helvetica-Bold', fontSize=11,
        leading=14, textColor=ACCENT, spaceBefore=6, spaceAfter=2)
    s['Code'] = ParagraphStyle(
        'Code', parent=base['Code'], fontName='Courier', fontSize=9.5,
        leading=13, textColor=INK)
    s['CodeComment'] = ParagraphStyle(
        'CodeComment', parent=s['Code'], textColor=colors.HexColor('#6B6B60'))
    s['CoverTitle'] = ParagraphStyle(
        'CoverTitle', parent=base['Title'], fontName='Helvetica-Bold',
        fontSize=40, leading=44, textColor=YELLOW, alignment=TA_LEFT)
    s['CoverSubtitle'] = ParagraphStyle(
        'CoverSubtitle', parent=base['Normal'], fontName='Helvetica',
        fontSize=15, leading=20, textColor=CYAN, alignment=TA_LEFT)
    s['CoverTag'] = ParagraphStyle(
        'CoverTag', parent=base['Normal'], fontName='Helvetica-Bold',
        fontSize=10, leading=13, textColor=MAGENTA, alignment=TA_LEFT)
    s['CoverFoot'] = ParagraphStyle(
        'CoverFoot', parent=base['Normal'], fontName='Helvetica',
        fontSize=9.5, leading=13, textColor=PAPER, alignment=TA_LEFT)
    s['TipTitle'] = ParagraphStyle(
        'TipTitle', parent=base['Normal'], fontName='Helvetica-Bold',
        fontSize=9, leading=11, textColor=PAPER)
    s['TipBody'] = ParagraphStyle(
        'TipBody', parent=base['Normal'], fontName='Helvetica',
        fontSize=9.5, leading=12, textColor=INK)
    s['Cell'] = ParagraphStyle(
        'Cell', parent=base['Normal'], fontName='Helvetica', fontSize=9,
        leading=11.5, textColor=INK)
    s['CellBold'] = ParagraphStyle(
        'CellBold', parent=s['Cell'], fontName='Helvetica-Bold')
    s['CellCode'] = ParagraphStyle(
        'CellCode', parent=s['Cell'], fontName='Courier', fontSize=8.5)
    s['CellHead'] = ParagraphStyle(
        'CellHead', parent=base['Normal'], fontName='Helvetica-Bold',
        fontSize=9, leading=11, textColor=PAPER)
    s['Sig'] = ParagraphStyle(
        'Sig', parent=base['Normal'], fontName='Helvetica-BoldOblique',
        fontSize=18, leading=22, textColor=NAVY, alignment=TA_CENTER)
    s['SigSub'] = ParagraphStyle(
        'SigSub', parent=base['Normal'], fontName='Helvetica',
        fontSize=9.5, leading=13, textColor=colors.gray, alignment=TA_CENTER)
    return s


def callout(styles, kind, body_html):
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


def code_block(styles, lines):
    """Terminal-style code box.  Lines starting with '#' render as comments.
    Runs of 2+ spaces are preserved (alignment); single spaces still wrap."""
    import re
    rows = []
    for ln in lines:
        style = styles['CodeComment'] if ln.lstrip().startswith('#') else styles['Code']
        ln = re.sub(r'  +', lambda m: '&nbsp;' * len(m.group()), ln)
        rows.append([Paragraph(ln, style)])
    t = Table(rows, colWidths=[INNER_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F0EA')),
        ('BOX', (0, 0), (-1, -1), 0.6, SUBTLE),
        ('LINEBEFORE', (0, 0), (0, -1), 2.5, CYAN),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
    ]))
    return KeepTogether(t)


def make_table(styles, headers, rows, col_widths, header_bg=NAVY):
    data = [[Paragraph(h, styles['CellHead']) for h in headers]]
    for row in rows:
        data.append([cell if isinstance(cell, Paragraph) else
                     Paragraph(cell, styles['Cell']) for cell in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.4, SUBTLE),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F4F4EF')))
    t.setStyle(TableStyle(style))
    return t


C = lambda s: f'<font face="Courier">{s}</font>'           # inline code
CB = lambda s: f'<font face="Courier"><b>{s}</b></font>'   # inline code bold


def build():
    styles = make_styles()
    story = []

    # ================= COVER =================
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph('GB-TRACKER PRO', styles['CoverTitle']))
    story.append(Spacer(1, 6))
    story.append(Paragraph('Guida all\'ambiente di sviluppo',
                           styles['CoverSubtitle']))
    story.append(Paragraph('Windows 10/11 &amp; macOS (Apple Silicon e Intel)',
                           styles['CoverSubtitle']))
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        'EDIZIONE GIUGNO 2026 · RGBDS v1.0.1 · PYTHON 3.14 · SAMEBOY v1.0.3',
        styles['CoverTag']))
    story.append(Spacer(1, 70 * mm))
    story.append(Paragraph('a cura di <b>Luigi Massari</b>', styles['CoverFoot']))
    story.append(Paragraph(
        'Progetto personale open source · Licenza MIT · '
        'github.com/luigismith/gb-tracker-pro', styles['CoverFoot']))
    story.append(PageBreak())

    # ================= 1. PANORAMICA =================
    story.append(SectionBanner(1, 'PANORAMICA: COSA SERVE'))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'GB-Tracker Pro è un music tracker a 4 canali per Game Boy Color, scritto '
        'interamente in assembly SM83 e compilato con il toolchain open source '
        '<b>RGBDS</b>. L\'intero ambiente di sviluppo è gratuito, leggero '
        '(meno di 100 MB in totale) e funziona identico su Windows e macOS. '
        'Questa guida ti porta da zero a una ROM compilata e funzionante in '
        'circa 15 minuti.', styles['BodyJustify']))
    story.append(Spacer(1, 6))
    story.append(make_table(
        styles,
        ['Componente', 'Versione (giu 2026)', 'Ruolo', 'Richiesto'],
        [
            [Paragraph('<b>RGBDS</b>', styles['CellBold']),
             'v1.0.1 (1 gen 2026)',
             'Assembler + linker + header fixer (rgbasm, rgblink, rgbfix)',
             'Sì'],
            [Paragraph('<b>Python</b>', styles['CellBold']),
             '3.8+ (consigliata 3.14.5)',
             'Script di build e generatori di asset (font, note, waveform)',
             'Sì'],
            [Paragraph('<b>Git</b>', styles['CellBold']),
             'qualsiasi recente',
             'Clonare il repository e gestire le versioni',
             'Sì'],
            [Paragraph('<b>reportlab + Pillow</b>', styles['CellBold']),
             'ultime da pip',
             'Solo per rigenerare manuale PDF e screenshot',
             'No'],
            [Paragraph('<b>Emulatore</b>', styles['CellBold']),
             'SameBoy v1.0.3 / BGB / mGBA 0.10.5',
             'Eseguire e testare la ROM (serve accuratezza CGB)',
             'Sì'],
        ],
        [28*mm, 36*mm, INNER_W - 28*mm - 36*mm - 22*mm, 22*mm]))
    story.append(Spacer(1, 6))
    story.append(callout(styles, 'note',
        'La compilazione della ROM richiede <b>solo Python standard + RGBDS</b>: '
        'nessuna dipendenza pip. I pacchetti reportlab e Pillow servono '
        'esclusivamente se vuoi rigenerare il manuale PDF o gli screenshot.'))
    story.append(Spacer(1, 10))

    # ================= 2. WINDOWS =================
    story.append(SectionBanner(2, 'INSTALLAZIONE SU WINDOWS 10 / 11'))
    story.append(Spacer(1, 6))
    story.append(OSBadge('WINDOWS', colors.HexColor('#0067B8')))
    story.append(Spacer(1, 2))

    story.append(Paragraph('2.1 — Python e Git con winget', styles['H3']))
    story.append(Paragraph(
        'Apri un <b>Terminale</b> (Windows Terminal o PowerShell) e installa '
        'Python e Git con il package manager integrato di Windows:',
        styles['Body']))
    story.append(code_block(styles, [
        'winget install -e --id Python.Python.3.14',
        'winget install -e --id Git.Git',
    ]))
    story.append(Spacer(1, 4))
    story.append(callout(styles, 'warn',
        'Se preferisci l\'installer da <b>python.org</b>, spunta la casella '
        '<b>"Add python.exe to PATH"</b> nella prima schermata: senza, il '
        'comando ' + C('python') + ' non verrà riconosciuto dal terminale.'))
    story.append(Spacer(1, 4))

    story.append(Paragraph('2.2 — RGBDS v1.0.1', styles['H3']))
    story.append(Paragraph(
        'Scarica il pacchetto Windows a 64 bit '
        f'({CB("rgbds-win64.zip")}) dalla pagina release ufficiale:',
        styles['Body']))
    story.append(code_block(styles, [
        '# Browser:',
        'https://github.com/gbdev/rgbds/releases/tag/v1.0.1',
        '# oppure da terminale:',
        'curl -LO https://github.com/gbdev/rgbds/releases/download/'
        'v1.0.1/rgbds-win64.zip',
    ]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        'Estrai dallo zip questi file nella cartella ' + CB('tools/') +
        ' del progetto (lo script di build li cerca lì per primo):',
        styles['Body']))
    story.append(code_block(styles, [
        'rgbasm.exe    rgblink.exe    rgbfix.exe    rgbgfx.exe',
        'libpng16.dll  zlib1.dll',
    ]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        'In alternativa puoi estrarli in una cartella qualsiasi (es. '
        + C('C:\\rgbds') + ') e aggiungerla al PATH di sistema: '
        + C('build.py') + ' usa prima gli eseguibili in ' + C('tools/') +
        ', poi quelli nel PATH.', styles['Body']))
    story.append(Spacer(1, 4))

    story.append(Paragraph('2.3 — Clona e compila', styles['H3']))
    story.append(code_block(styles, [
        'git clone https://github.com/luigismith/gb-tracker-pro.git',
        'cd gb-tracker-pro',
        'python build.py',
    ]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        'Se tutto è a posto l\'ultima riga sarà:', styles['Body']))
    story.append(code_block(styles, [
        '[OK] Built GB_TRACKER_PRO.gbc (32768 bytes)',
    ]))
    story.append(Spacer(1, 4))

    story.append(Paragraph('2.4 — Dipendenze opzionali (manuale e screenshot)',
                           styles['H3']))
    story.append(code_block(styles, [
        'python -m pip install reportlab pillow',
    ]))
    story.append(Spacer(1, 10))

    # ================= 3. MACOS =================
    story.append(SectionBanner(3, 'INSTALLAZIONE SU MACOS'))
    story.append(Spacer(1, 6))
    story.append(OSBadge('MACOS · APPLE SILICON & INTEL', colors.HexColor('#555555')))
    story.append(Spacer(1, 2))

    story.append(Paragraph('3.1 — Homebrew', styles['H3']))
    story.append(Paragraph(
        'Tutto il toolchain si installa con <b>Homebrew</b>. Se non lo hai già, '
        'apri il Terminale ed esegui:', styles['Body']))
    story.append(code_block(styles, [
        '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/'
        'Homebrew/install/HEAD/install.sh)"',
    ]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        'L\'installer di Homebrew scarica automaticamente anche i Command Line '
        'Tools di Xcode se mancano. Su Apple Silicon, al termine, segui le '
        'istruzioni a video per aggiungere ' + C('/opt/homebrew/bin') +
        ' al PATH.', styles['Body']))
    story.append(Spacer(1, 4))

    story.append(Paragraph('3.2 — RGBDS, Git e Python', styles['H3']))
    story.append(code_block(styles, [
        'brew install rgbds git python',
        '# verifica: deve stampare "rgbasm v1.0.1"',
        'rgbasm --version',
    ]))
    story.append(Spacer(1, 3))
    story.append(callout(styles, 'tip',
        'La formula Homebrew di RGBDS è mantenuta dagli stessi sviluppatori '
        'gbdev: ' + C('brew install rgbds') + ' installa sempre l\'ultima '
        'release stabile, già compilata per la tua architettura (arm64 o x86_64). '
        'Niente Gatekeeper, niente quarantena.'))
    story.append(Spacer(1, 4))

    story.append(Paragraph('3.3 — Clona e compila', styles['H3']))
    story.append(Paragraph(
        'Su macOS non serve copiare nulla in ' + C('tools/') + ': lo script '
        'di build rileva automaticamente i binari RGBDS nel PATH.',
        styles['Body']))
    story.append(code_block(styles, [
        'git clone https://github.com/luigismith/gb-tracker-pro.git',
        'cd gb-tracker-pro',
        'python3 build.py',
        '# atteso: [OK] Built GB_TRACKER_PRO.gbc (32768 bytes)',
    ]))
    story.append(Spacer(1, 4))

    story.append(Paragraph('3.4 — Dipendenze opzionali (in virtual env)',
                           styles['H3']))
    story.append(Paragraph(
        'Il Python di Homebrew è "externally managed" (PEP 668): '
        + C('pip install') + ' diretto viene bloccato. Usa un virtual '
        'environment dentro al progetto:', styles['Body']))
    story.append(code_block(styles, [
        'python3 -m venv .venv',
        'source .venv/bin/activate',
        'pip install reportlab pillow',
    ]))
    story.append(Spacer(1, 4))

    story.append(Paragraph('3.5 — Emulatore: SameBoy', styles['H3']))
    story.append(Paragraph(
        '<b>SameBoy</b> è l\'emulatore Game Boy più accurato in assoluto ed è '
        'nativo macOS — la scelta ideale:', styles['Body']))
    story.append(code_block(styles, [
        'brew install --cask sameboy',
        'open GB_TRACKER_PRO.gbc -a SameBoy',
    ]))
    story.append(Spacer(1, 10))

    # ================= 4. VERIFICA =================
    story.append(SectionBanner(4, 'VERIFICA DELL\'INSTALLAZIONE'))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'Checklist finale: esegui questi comandi dalla cartella del progetto '
        'e confronta l\'output.', styles['Body']))
    story.append(make_table(
        styles,
        ['Comando', 'Output atteso'],
        [
            [Paragraph(C('rgbasm --version'), styles['CellCode']),
             Paragraph(C('rgbasm v1.0.1'), styles['CellCode'])],
            [Paragraph(C('python --version') + ' &nbsp;(Win) / ' +
                       C('python3 --version') + ' (mac)', styles['CellCode']),
             Paragraph(C('Python 3.x.y') + ' (almeno 3.8)', styles['CellCode'])],
            [Paragraph(C('git --version'), styles['CellCode']),
             Paragraph(C('git version 2.x'), styles['CellCode'])],
            [Paragraph(C('python build.py'), styles['CellCode']),
             Paragraph(C('[OK] Built GB_TRACKER_PRO.gbc (32768 bytes)'),
                       styles['CellCode'])],
        ],
        [INNER_W * 0.48, INNER_W * 0.52]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'Infine apri ' + CB('GB_TRACKER_PRO.gbc') + ' nell\'emulatore: deve '
        'comparire il pattern editor con il titolo <b>GB-TRACKER PRO</b> e un '
        'brano vuoto. Premi <b>Select + Start</b> per aprire il menu Save/Load: '
        'lo <b>Slot 4</b> deve risultare ' + C('SAVED') + ' — contiene la demo '
        '"Per Elisa". Selezionala con <b>A</b>: se senti la melodia, '
        'l\'ambiente è perfettamente funzionante.', styles['BodyJustify']))
    story.append(Spacer(1, 6))
    story.append(make_table(
        styles,
        ['Emulatore', 'Piattaforma', 'Note'],
        [
            ['SameBoy v1.0.3', 'macOS (nativo), Windows, SDL',
             'Il più accurato; debugger integrato'],
            ['BGB', 'Windows',
             'Debugger eccellente, ottimo per sviluppo assembly'],
            ['mGBA 0.10.5', 'Windows, macOS, Linux',
             'Veloce e multipiattaforma'],
            ['binjgb', 'Browser (WebAssembly)',
             'Zero installazione, utile per test rapidi'],
        ],
        [32*mm, 48*mm, INNER_W - 32*mm - 48*mm]))
    story.append(Spacer(1, 6))
    story.append(callout(styles, 'note',
        'Per provare la ROM su <b>hardware reale</b> basta copiare '
        + C('GB_TRACKER_PRO.gbc') + ' sulla microSD di una flashcart MBC5 '
        '(EZ-Flash Junior, Everdrive GB, ElCheapoSD). I salvataggi finiscono '
        'in un file ' + C('.sav') + ' da 32 KB gestibile con '
        + C('tools/fts_tool.py') + '.'))
    story.append(Spacer(1, 10))

    # ================= 5. STRUTTURA =================
    story.append(SectionBanner(5, 'STRUTTURA DEL PROGETTO'))
    story.append(Spacer(1, 6))
    story.append(code_block(styles, [
        'gb-tracker-pro/',
        '|-- build.py              build completo in un comando',
        '|-- src/                  sorgenti assembly SM83',
        '|     |-- main.asm        boot, main loop, VBlank ISR',
        '|     |-- player.asm      motore audio + demo song',
        '|     |-- ui.asm          rendering pattern editor e menu',
        '|     |-- input.asm       joypad e dispatch comandi',
        '|     |-- save.asm        salvataggi SRAM (4 slot)',
        '|     +-- font/notes/waves.asm   (auto-generati, non editare)',
        '|-- inc/hardware.inc      registri hardware GBC',
        '|-- tools/                generatori Python + RGBDS (Windows)',
        '+-- manual/               screenshot per manuale e README',
    ]))
    story.append(Spacer(1, 4))
    story.append(callout(styles, 'warn',
        'I file ' + C('font.asm') + ', ' + C('notes.asm') + ' e '
        + C('waves.asm') + ' vengono <b>rigenerati a ogni build</b> dagli '
        'script in ' + C('tools/') + ': qualsiasi modifica manuale viene '
        'sovrascritta. Modifica invece i generatori.'))
    story.append(Spacer(1, 10))

    # ================= 6. TROUBLESHOOTING =================
    story.append(SectionBanner(6, 'RISOLUZIONE DEI PROBLEMI'))
    story.append(Spacer(1, 6))
    story.append(make_table(
        styles,
        ['Sintomo', 'Causa', 'Soluzione'],
        [
            [Paragraph(C('rgbasm not found'), styles['CellCode']),
             'RGBDS non installato o fuori PATH',
             Paragraph('Win: estrai gli exe in ' + C('tools/') +
                       '. mac: ' + C('brew install rgbds'), styles['Cell'])],
            [Paragraph('Errore DLL all\'avvio di rgbgfx (Win)', styles['Cell']),
             'Mancano le librerie a fianco degli exe',
             Paragraph('Copia anche ' + C('libpng16.dll') + ' e ' +
                       C('zlib1.dll') + ' dallo zip in ' + C('tools/'),
                       styles['Cell'])],
            [Paragraph(C('python non riconosciuto') + ' (Win)',
                       styles['CellCode']),
             'PATH non aggiornato dall\'installer',
             Paragraph('Reinstalla spuntando "Add to PATH", oppure usa il '
                       'launcher: ' + C('py build.py'), styles['Cell'])],
            [Paragraph(C('externally-managed-environment') + ' (mac)',
                       styles['CellCode']),
             'PEP 668: il Python di Homebrew blocca pip globale',
             Paragraph('Usa il venv come in §3.4', styles['Cell'])],
            [Paragraph('"App non verificata" (mac)', styles['Cell']),
             'Gatekeeper sui binari scaricati a mano',
             Paragraph(C('xattr -dr com.apple.quarantine <file>') +
                       ' — oppure usa brew, che non ha questo problema',
                       styles['Cell'])],
            [Paragraph('La ROM compila ma il manuale no', styles['Cell']),
             'reportlab / Pillow non installati',
             Paragraph(C('pip install reportlab pillow') +
                       ' (sono opzionali, la ROM non li richiede)',
                       styles['Cell'])],
            [Paragraph('Lo slot 4 non contiene la demo', styles['Cell']),
             'SRAM non ancora formattata dall\'emulatore',
             Paragraph('Chiudi e riapri la ROM: al primo boot la SRAM viene '
                       'formattata e la demo installata', styles['Cell'])],
        ],
        [INNER_W * 0.30, INNER_W * 0.30, INNER_W * 0.40]))
    story.append(Spacer(1, 10))

    # ================= 7. RISORSE =================
    story.append(SectionBanner(7, 'RISORSE UTILI'))
    story.append(Spacer(1, 6))
    story.append(make_table(
        styles,
        ['Risorsa', 'URL'],
        [
            ['Repository del progetto',
             Paragraph(C('github.com/luigismith/gb-tracker-pro'),
                       styles['CellCode'])],
            ['RGBDS — documentazione ufficiale',
             Paragraph(C('rgbds.gbdev.io'), styles['CellCode'])],
            ['Pan Docs — riferimento hardware GB/GBC',
             Paragraph(C('gbdev.io/pandocs'), styles['CellCode'])],
            ['Community gbdev (tutorial, esempi, Discord)',
             Paragraph(C('gbdev.io'), styles['CellCode'])],
            ['SameBoy', Paragraph(C('sameboy.github.io'), styles['CellCode'])],
            ['BGB', Paragraph(C('bgb.bircd.org'), styles['CellCode'])],
            ['mGBA', Paragraph(C('mgba.io'), styles['CellCode'])],
        ],
        [INNER_W * 0.55, INNER_W * 0.45]))

    # ================= FIRMA =================
    story.append(Spacer(1, 18 * mm))
    story.append(HRule(width=INNER_W * 0.4, thickness=0.8, color=MAGENTA,
                       top=2, bottom=8))
    story.append(Paragraph(
        'Buon divertimento, e buona musica a 8 bit!', styles['SigSub']))
    story.append(Spacer(1, 6))
    story.append(Paragraph('Luigi Massari', styles['Sig']))
    story.append(Paragraph(
        'Giugno 2026 · progetto personale, rilasciato con licenza MIT',
        styles['SigSub']))

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_Y, bottomMargin=MARGIN_Y,
        title='GB-Tracker Pro — Guida all\'ambiente di sviluppo',
        author='Luigi Massari',
        subject='Setup del toolchain RGBDS + Python su Windows e macOS')
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'[OK] {OUTPUT.name} ({OUTPUT.stat().st_size} bytes)')


if __name__ == '__main__':
    build()

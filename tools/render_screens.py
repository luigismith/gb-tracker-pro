#!/usr/bin/env python3
"""Render manual screenshots that match the ROM's UI exactly.

Reads the same font.asm and palette constants used by the ROM and
draws each tilemap-equivalent screen as a 160x144 PNG (then upscaled).
"""

import os
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    os.system(f"{sys.executable} -m pip install Pillow")
    from PIL import Image

ROOT = Path(__file__).parent.parent.resolve()
SRC = ROOT / 'src'
OUT = ROOT / 'manual' / 'screenshots'
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Parse font.asm — extract 128 tiles (16 bytes each, 2bpp planar).
# We only use plane 0 (plane 1 is 0 throughout our font).
# ------------------------------------------------------------
def load_font():
    text = (SRC / 'font.asm').read_text()
    tiles = []
    for line in text.splitlines():
        m = re.match(r'\s*DB\s+(.+?)\s*(?:;.*)?$', line)
        if not m:
            continue
        nums = [int(x.strip().lstrip('$'), 16) for x in m.group(1).split(',')]
        if len(nums) == 16:
            tiles.append(nums)
    return tiles


# CGB palettes (RGB555 word → RGB888 tuple).
def rgb555_to_rgb(word):
    r = (word & 0x1F)
    g = (word >> 5) & 0x1F
    b = (word >> 10) & 0x1F
    return (r * 255 // 31, g * 255 // 31, b * 255 // 31)


C_BLACK   = 0x0000
C_WHITE   = 0x7FFF
C_NAVY    = 0x3063
C_CYAN    = 0x7380
C_DIMCYAN = 0x4A8A
C_MAGENTA = 0x701C
C_YELLOW  = 0x03FF
C_GREEN   = 0x0380
C_DARKRED = 0x0012
C_ORANGE  = 0x025F
C_PURPLE  = 0x7018

PALETTES = [
    # 0: pattern normal
    [C_NAVY, C_CYAN, C_DIMCYAN, C_WHITE],
    # 1: title bar
    [C_MAGENTA, C_YELLOW, C_WHITE, C_WHITE],
    # 2: cursor cell
    [C_GREEN, C_BLACK, C_BLACK, C_WHITE],
    # 3: cursor row
    [C_DARKRED, C_WHITE, C_YELLOW, C_WHITE],
    # 4: playing row
    [C_ORANGE, C_BLACK, C_BLACK, C_WHITE],
    # 5: dim
    [C_NAVY, C_PURPLE, C_WHITE, C_WHITE],
    # 6: column header
    [C_BLACK, C_YELLOW, C_WHITE, C_WHITE],
    # 7: status / help
    [C_BLACK, C_GREEN, C_WHITE, C_WHITE],
]
PALETTES_RGB = [[rgb555_to_rgb(c) for c in p] for p in PALETTES]


# Tile slot for a printable character.
def tile_index(ch):
    return ord(ch) - 0x20


# ------------------------------------------------------------
# Render a screen.
# Screen is 20x18 tiles, each 8x8 pixels = 160x144.
# tilemap: 18 rows of 20 strings (each char becomes a tile).
# attrmap: 18 rows of 20 ints (palette indices 0..7).
# ------------------------------------------------------------
def render(tiles, tilemap, attrmap, scale=4):
    W, H = 160, 144
    img = Image.new('RGB', (W, H))
    pixels = img.load()
    for ty in range(18):
        for tx in range(20):
            ch = tilemap[ty][tx] if tx < len(tilemap[ty]) else ' '
            tindex = tile_index(ch)
            if not (0 <= tindex < len(tiles)):
                tindex = 0
            pal = PALETTES_RGB[attrmap[ty][tx]]
            tile = tiles[tindex]
            for py in range(8):
                plane0 = tile[py * 2]
                plane1 = tile[py * 2 + 1]
                for px in range(8):
                    bit = 7 - px
                    color_idx = ((plane0 >> bit) & 1) | (((plane1 >> bit) & 1) << 1)
                    color = pal[color_idx]
                    pixels[tx * 8 + px, ty * 8 + py] = color
    if scale != 1:
        img = img.resize((W * scale, H * scale), Image.NEAREST)
    return img


# ------------------------------------------------------------
# Build the pattern editor screen.
# ------------------------------------------------------------
def build_pattern_screen(view_top=0, cursor_row=0, cursor_col=0,
                         player_row=4, current_pat='00', order='00',
                         note='C-4', bpm=112,
                         show_playing=True, song='perelisa'):
    """Render the pattern editor.

    song='blank'     : all cells '...' (boot state)
    song='perelisa'  : Pattern 0 of Per Elisa (demo cover in slot 1)
    """
    rows = []
    attrs = []
    blank_row = list('                    ')

    if song == 'blank':
        pattern = [['...', '...', '...', '...'] for _ in range(32)]
    else:
        # Per Elisa Pattern 0 — see DemoPattern0 in player.asm
        # ch0=lead (E D# E D# E B D C A) , ch1=counter arpeggio,
        # ch2=sub-bass (A-3/E-3), ch3=no drums in P0
        pattern = [
            ['E-5', '...', 'A-3', '...'],  # 00
            ['D#5', '...', '...', '...'],  # 01
            ['E-5', '...', '...', '...'],  # 02
            ['D#5', '...', '...', '...'],  # 03
            ['E-5', '...', '...', '...'],  # 04
            ['B-4', '...', '...', '...'],  # 05
            ['D-5', '...', '...', '...'],  # 06
            ['C-5', '...', '...', '...'],  # 07
            ['A-4', '...', 'A-3', '...'],  # 08
            ['...', '...', '...', '...'],  # 09
            ['...', '...', '...', '...'],  # 0A
            ['...', 'C-4', '...', '...'],  # 0B
            ['...', 'E-4', '...', '...'],  # 0C
            ['...', 'A-4', '...', '...'],  # 0D
            ['B-4', '...', '...', '...'],  # 0E
            ['...', '...', '...', '...'],  # 0F
            ['...', '...', 'E-3', '...'],  # 10
            ['...', '...', '...', '...'],  # 11
            ['...', 'E-4', '...', '...'],  # 12
            ['...', 'G#4', '...', '...'],  # 13
            ['...', 'B-4', '...', '...'],  # 14
            ['C-5', '...', '...', '...'],  # 15
            ['...', '...', '...', '...'],  # 16
            ['...', '...', '...', '...'],  # 17
            ['B-4', '...', 'A-3', '...'],  # 18
            ['...', '...', '...', '...'],
            ['...', '...', '...', '...'],
            ['...', '...', '...', '...'],
            ['...', '...', '...', '...'],
            ['...', '...', '...', '...'],
            ['...', '...', '...', '...'],
            ['...', '...', '...', '...'],
        ]

    # Row 0 — title
    title = list(('  GB-TRACKER PRO    ').ljust(20))
    rows.append(title)
    attrs.append([1] * 20)

    # Row 1 — status:  "PT:00 N:C-4 BPM:112"
    status_str = f'PT:{current_pat} N:{note} BPM:{bpm:03d}'
    status = list(status_str.ljust(20)[:20])
    rows.append(status)
    attrs.append([7] * 20)

    # Row 2 — blank
    rows.append(blank_row.copy())
    attrs.append([0] * 20)

    # Row 3 — column header
    hdr = list('## P1  P2  WV  NO  ')
    while len(hdr) < 20: hdr.append(' ')
    rows.append(hdr)
    attrs.append([6] * 20)

    # Rows 4..15 — 12 visible pattern rows
    for visual in range(12):
        prow = view_top + visual
        if prow >= 32:
            rows.append(blank_row.copy())
            attrs.append([0] * 20)
            continue
        hex_row = f'{prow:02X}'
        cells = pattern[prow]
        line = f'{hex_row} {cells[0]} {cells[1]} {cells[2]} {cells[3]}  '
        rline = list(line[:20].ljust(20))
        # Determine palette
        if prow == cursor_row:
            pal = 3  # cursor row
        elif show_playing and prow == player_row:
            pal = 4  # playing row
        else:
            pal = 0
        attr = [pal] * 20
        # cursor cell (3 tiles wide on cursor_col channel)
        if prow == cursor_row:
            ch_x = [3, 7, 11, 15][cursor_col]
            for i in range(3):
                attr[ch_x + i] = 2
        rows.append(rline)
        attrs.append(attr)

    # Row 16 — blank
    rows.append(blank_row.copy())
    attrs.append([0] * 20)

    # Row 17 — help
    help_str = f'A:NOTE  B:DEL  R:{player_row:02X}'
    help_line = list(help_str.ljust(20)[:20])
    rows.append(help_line)
    attrs.append([7] * 20)

    return rows, attrs


def build_menu_screen(selected_slot=0, slot_status=('SAVED', 'EMPTY', 'EMPTY', 'EMPTY'),
                      toast=None):
    """Build save/load menu screen.

    toast: None | 'SAVED' | 'LOADED'
    """
    rows = []
    attrs = []
    blank_row = list(' ' * 20)
    blank_attr = [0] * 20

    # Row 0 — title bar
    rows.append(list(' SAVE / LOAD SONGS  '))
    attrs.append([1] * 20)

    # Row 1 — subtitle
    rows.append(list('Choose a slot       '))
    attrs.append([7] * 20)

    # Row 2 — blank
    rows.append(blank_row.copy()); attrs.append([0] * 20)
    rows.append(blank_row.copy()); attrs.append([0] * 20)

    # Slot rows at 4, 6, 8, 10
    for slot in range(4):
        row_idx = 4 + slot * 2
        # Pad screen rows up to row_idx
        while len(rows) < row_idx:
            rows.append(blank_row.copy()); attrs.append([0] * 20)
        text = f' SLOT {slot+1}: {slot_status[slot]}  '
        line = list(text.ljust(20)[:20])
        pal = 3 if slot == selected_slot else 0
        rows.append(line)
        attrs.append([pal] * 20)

    # Fill up to row 13
    while len(rows) < 13:
        rows.append(blank_row.copy()); attrs.append([0] * 20)

    # Row 13 — toast
    if toast == 'SAVED':
        rows.append(list('     >>> SAVED <<<  '))
    elif toast == 'LOADED':
        rows.append(list('    >>> LOADED <<<  '))
    else:
        rows.append(blank_row.copy())
    attrs.append([7] * 20)

    # Fill 14
    rows.append(blank_row.copy()); attrs.append([0] * 20)

    # Rows 15..17 — help
    rows.append(list('A: LOAD slot        ')); attrs.append([7] * 20)
    rows.append(list('B: SAVE slot        ')); attrs.append([7] * 20)
    rows.append(list('SELECT: back        ')); attrs.append([7] * 20)

    # Pad if short
    while len(rows) < 18:
        rows.append(blank_row.copy()); attrs.append([0] * 20)

    return rows[:18], attrs[:18]


def main():
    tiles = load_font()
    print(f'Loaded {len(tiles)} font tiles')

    # Screenshot 1: Boot — pattern editor vuoto (stato di partenza)
    rows, attrs = build_pattern_screen(view_top=0, cursor_row=0, cursor_col=0,
                                       player_row=0, show_playing=False,
                                       song='blank', note='C-4', bpm=112)
    render(tiles, rows, attrs, scale=4).save(OUT / '01_boot_empty.png')

    # Screenshot 2: Per Elisa caricata e in riproduzione
    rows, attrs = build_pattern_screen(view_top=0, cursor_row=0, cursor_col=0,
                                       player_row=4, song='perelisa',
                                       note='C-4', bpm=112)
    render(tiles, rows, attrs, scale=4).save(OUT / '02_pattern_main.png')

    # Screenshot 3: Per Elisa, cursore su riga 08 canale WV (sub-bass)
    rows, attrs = build_pattern_screen(view_top=0, cursor_row=8, cursor_col=2,
                                       player_row=16, song='perelisa',
                                       note='C-4', bpm=112)
    render(tiles, rows, attrs, scale=4).save(OUT / '03_pattern_cursor.png')

    # Screenshot 4: Save/Load menu — boot, slot 4 ha la demo, gli altri vuoti
    rows, attrs = build_menu_screen(selected_slot=0,
                                     slot_status=('EMPTY','EMPTY','EMPTY','SAVED'))
    render(tiles, rows, attrs, scale=4).save(OUT / '04_menu_initial.png')

    # Screenshot 5: Menu — utente naviga a slot 4 per caricare la demo
    rows, attrs = build_menu_screen(selected_slot=3,
                                     slot_status=('SAVED','EMPTY','EMPTY','SAVED'))
    render(tiles, rows, attrs, scale=4).save(OUT / '05_menu_select.png')

    # Screenshot 6: Toast SAVED dopo aver premuto B sullo slot 1
    rows, attrs = build_menu_screen(selected_slot=0,
                                     slot_status=('SAVED','EMPTY','EMPTY','SAVED'),
                                     toast='SAVED')
    render(tiles, rows, attrs, scale=4).save(OUT / '06_menu_saved.png')

    # Screenshot 7: Toast LOADED dopo aver caricato la demo (slot 4)
    rows, attrs = build_menu_screen(selected_slot=3,
                                     slot_status=('EMPTY','EMPTY','EMPTY','SAVED'),
                                     toast='LOADED')
    render(tiles, rows, attrs, scale=4).save(OUT / '07_menu_loaded.png')

    print(f'Saved 7 screenshots to {OUT}')


if __name__ == '__main__':
    main()

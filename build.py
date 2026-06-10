#!/usr/bin/env python3
"""Build FastTracker GB ROM.

Steps:
  1. Regenerate auto-generated asm (font, notes, waves)
  2. Assemble each .asm with rgbasm
  3. Link with rgblink
  4. Patch header with rgbfix (CGB-only, MBC5+RAM+battery)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
TOOLS = ROOT / 'tools'
SRC = ROOT / 'src'
INC = ROOT / 'inc'
BUILD = ROOT / 'build'

def find_tool(name):
    """Locate an RGBDS binary: vendored tools/*.exe first (Windows),
    then the system PATH (macOS/Linux, e.g. `brew install rgbds`)."""
    exe = TOOLS / f'{name}.exe'
    if exe.exists():
        return str(exe)
    found = shutil.which(name)
    if found:
        return found
    sys.exit(f'! {name} not found: place {name}.exe in tools/ '
             f'or install RGBDS so that `{name}` is in your PATH')


RGBASM = find_tool('rgbasm')
RGBLINK = find_tool('rgblink')
RGBFIX = find_tool('rgbfix')

# Source assembly files (order doesn't matter — rgblink resolves)
SOURCES = [
    'header.asm',
    'main.asm',
    'player.asm',
    'ui.asm',
    'input.asm',
    'save.asm',
    'font.asm',
    'notes.asm',
    'waves.asm',
]

ROM_NAME = 'GB_TRACKER_PRO.gbc'


def run(cmd, **kw):
    print('>', ' '.join(str(c) for c in cmd))
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(r.returncode)
    return r


def main():
    BUILD.mkdir(exist_ok=True)

    # 1. Regen generated sources
    run([sys.executable, str(TOOLS / 'gen_font.py'), str(SRC / 'font.asm')])
    run([sys.executable, str(TOOLS / 'gen_notes.py'), str(SRC / 'notes.asm')])
    run([sys.executable, str(TOOLS / 'gen_waves.py'), str(SRC / 'waves.asm')])

    # 2. Assemble
    obj_files = []
    for src in SOURCES:
        src_path = SRC / src
        if not src_path.exists():
            print(f'! Missing {src_path}, skipping')
            continue
        obj_path = BUILD / (src + '.o')
        run([str(RGBASM), '-i', str(INC), '-o', str(obj_path), str(src_path)])
        obj_files.append(str(obj_path))

    # 3. Link
    rom_path = BUILD / ROM_NAME
    map_path = BUILD / 'rom.map'
    sym_path = BUILD / 'rom.sym'
    run([str(RGBLINK), '-o', str(rom_path),
         '-m', str(map_path), '-n', str(sym_path),
         '-p', '0xFF'] + obj_files)

    # 4. Fix header
    #  -v : validate logo + fix checksums
    #  -p 0xFF : pad
    #  -C : force CGB-only mode flag
    #  -m 0x1B : MBC5 + RAM + battery
    #  -r 0x03 : ROM size 256KiB (rgbfix will set this from actual size too)
    #  -t TITLE
    run([str(RGBFIX), '-v', '-p', '0xFF', '-C',
         '-m', '0x1B', '-r', '0x03',
         '-t', 'GBTRACKERPRO',
         str(rom_path)])

    # Also copy to project root for convenience
    shutil.copy(rom_path, ROOT / ROM_NAME)
    print(f'\n[OK] Built {ROM_NAME} ({rom_path.stat().st_size} bytes)')


if __name__ == '__main__':
    main()

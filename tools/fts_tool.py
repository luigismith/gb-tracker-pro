#!/usr/bin/env python3
"""FastTracker GB save/song toolkit.

Legge e scrive i file .sav generati dalle flashcart (EZ-Flash Junior,
Everdrive, ecc.) e li converte da/verso brani singoli .fts.

File `.sav`  : 32 KB raw SRAM dump.  Banco 0 ($A000..$BFFF) contiene
               magic "FTGB" + 4 slot di 512 byte ognuno.
File `.fts`  : un singolo slot (512 byte) preceduto da un header di
               16 byte:
                   bytes 0..7   = magic "FTGBSONG"
                   byte 8       = format version (1)
                   bytes 9..11  = reserved
                   bytes 12..15 = name padding zero
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple


# --- Layout costants (in sync con src/save.asm) ---
SAV_SIZE          = 32 * 1024              # 32 KB total SRAM
HEADER_OFFSET     = 0
HEADER_MAGIC      = b'FTGB'
HEADER_VERSION    = 2                      # bumped: slot ora 2044 byte (4 pattern)
HEADER_SLOT_COUNT = 4
SLOT0_OFFSET      = 16                     # $A010 in SRAM
SLOT_SIZE         = 2044
SLOT_MAGIC        = 0xFE
PAT_BYTES         = 256
NUM_PATTERNS      = 4

FTS_MAGIC   = b'FTGBSONG'
FTS_VERSION = 2
FTS_HEADER  = 16                           # 8 magic + 1 ver + 7 reserved
FTS_SIZE    = FTS_HEADER + SLOT_SIZE       # 2060 bytes total

NOTE_NAMES = ['C-','C#','D-','D#','E-','F-','F#','G-','G#','A-','A#','B-']


# ------------------------------------------------------------
def fresh_sav() -> bytearray:
    """Return a 32 KB blank .sav with a freshly formatted header."""
    sav = bytearray(SAV_SIZE)
    sav[0:4] = HEADER_MAGIC
    sav[4]   = HEADER_VERSION
    sav[5]   = HEADER_SLOT_COUNT
    return sav


def slot_addr(slot: int) -> int:
    if not 0 <= slot < HEADER_SLOT_COUNT:
        raise ValueError(f'slot must be 0..{HEADER_SLOT_COUNT-1}')
    return SLOT0_OFFSET + slot * SLOT_SIZE


def slot_used(sav: bytes, slot: int) -> bool:
    return sav[slot_addr(slot)] == SLOT_MAGIC


def load_sav(path: Path) -> bytearray:
    data = bytearray(path.read_bytes())
    if len(data) < SAV_SIZE:
        # Pad short files (some flashcarts only write back used bytes).
        data.extend(b'\x00' * (SAV_SIZE - len(data)))
    elif len(data) > SAV_SIZE:
        data = data[:SAV_SIZE]
    return data


def save_sav(path: Path, sav: bytes) -> None:
    path.write_bytes(bytes(sav[:SAV_SIZE]))


def is_valid_header(sav: bytes) -> bool:
    return sav[0:4] == HEADER_MAGIC and sav[4] == HEADER_VERSION


# ------------------------------------------------------------
def decode_note(byte: int) -> str:
    if byte == 0x00:
        return '---'
    if byte == 0xFD:
        return 'OFF'
    if not 1 <= byte <= 60:
        return '???'
    semi  = (byte - 1) % 12
    octv  = 2 + (byte - 1) // 12
    return f'{NOTE_NAMES[semi]}{octv}'


def summarize_slot(slot: bytes) -> str:
    """Render a slot's metadata + a compact preview of its rows."""
    if slot[0] != SLOT_MAGIC:
        return 'EMPTY'
    speed   = slot[1]
    order_n = slot[2]
    order   = list(slot[4:4+16])
    # Count non-empty cells across all 4 patterns
    pats_base = 20
    total_notes = 0
    per_pat = []
    for p in range(NUM_PATTERNS):
        off = pats_base + p * PAT_BYTES
        pat = slot[off:off + PAT_BYTES]
        n = sum(1 for i in range(0, PAT_BYTES, 2) if pat[i] not in (0, 0xFD))
        per_pat.append(n)
        total_notes += n
    # Preview first 8 rows of pattern 0
    pat = slot[pats_base:pats_base + PAT_BYTES]
    rows = []
    for r in range(8):
        cells = []
        for c in range(4):
            offset = r * 8 + c * 2
            note = pat[offset]
            inst = pat[offset + 1]
            if note == 0:
                cells.append('---/--')
            elif note == 0xFD:
                cells.append('OFF/--')
            else:
                cells.append(f'{decode_note(note)}/{inst:02X}')
        rows.append(f'    {r:02X} : ' + '  '.join(cells))
    order_str = " ".join(f"{x:02X}" for x in order if x != 0xFF)
    pat_str = " / ".join(f"P{i}:{n}" for i, n in enumerate(per_pat))
    return (
        f'SAVED  (speed={speed}, order_len={order_n}, '
        f'{total_notes} note totali — {pat_str})\n'
        f'    Order: {order_str}\n'
        f'    Pattern 0 (prime 8 righe):\n' + '\n'.join(rows)
    )


# ------------------------------------------------------------
def slot_to_fts(sav: bytes, slot: int) -> bytes:
    base = slot_addr(slot)
    slot_bytes = sav[base:base + SLOT_SIZE]
    if slot_bytes[0] != SLOT_MAGIC:
        raise ValueError(f'Slot {slot+1} è vuoto, non c\'è nulla da esportare')
    out = bytearray(FTS_SIZE)
    out[0:8]  = FTS_MAGIC
    out[8]    = FTS_VERSION
    # bytes 9..15 reserved (zero)
    out[FTS_HEADER:FTS_HEADER + SLOT_SIZE] = slot_bytes
    return bytes(out)


def fts_to_slot(fts_bytes: bytes) -> bytes:
    if len(fts_bytes) < FTS_SIZE:
        raise ValueError(f'.fts troppo corto ({len(fts_bytes)} byte, attesi {FTS_SIZE})')
    if fts_bytes[0:8] != FTS_MAGIC:
        raise ValueError('Magic .fts mancante: il file non è un brano FastTracker GB')
    if fts_bytes[8] != FTS_VERSION:
        raise ValueError(f'Versione .fts non supportata: {fts_bytes[8]}')
    return fts_bytes[FTS_HEADER:FTS_HEADER + SLOT_SIZE]


# ============================================================
# CLI commands
# ============================================================
def cmd_info(args):
    sav = load_sav(Path(args.sav))
    if not is_valid_header(sav):
        print('!  Header non valido: il .sav non è stato formattato dal ROM,')
        print('   oppure è corrotto. Eseguilo prima sul ROM per inizializzarlo.')
        return 1
    print(f'File: {args.sav}')
    print(f'Magic: {sav[0:4].decode()}  ver={sav[4]}  slot_count={sav[5]}')
    print()
    for slot in range(HEADER_SLOT_COUNT):
        print(f'-- Slot {slot+1} --')
        base = slot_addr(slot)
        print(summarize_slot(sav[base:base + SLOT_SIZE]))
        print()


def cmd_extract(args):
    sav = load_sav(Path(args.sav))
    if not is_valid_header(sav):
        print('Header non valido', file=sys.stderr)
        return 1
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for slot in range(HEADER_SLOT_COUNT):
        if not slot_used(sav, slot):
            continue
        fts = slot_to_fts(sav, slot)
        target = out_dir / f'slot_{slot+1}.fts'
        target.write_bytes(fts)
        written.append(target)
    if not written:
        print('Nessuno slot occupato — niente da esportare.')
        return 0
    for w in written:
        print(f'  OK Estratto: {w}')


def cmd_import(args):
    sav_path = Path(args.sav)
    if sav_path.exists():
        sav = load_sav(sav_path)
        if not is_valid_header(sav):
            print(f'Il file {sav_path} esiste ma non ha header valido; lo riformatto.')
            sav = fresh_sav()
    else:
        print(f'{sav_path} non esiste, creo un nuovo .sav vuoto.')
        sav = fresh_sav()

    slot = args.slot - 1
    fts_data = Path(args.fts).read_bytes()
    slot_bytes = fts_to_slot(fts_data)
    base = slot_addr(slot)
    sav[base:base + SLOT_SIZE] = slot_bytes
    save_sav(sav_path, sav)
    print(f'  OK Importato {args.fts} in slot {slot+1} di {sav_path}')


def cmd_clear(args):
    sav = load_sav(Path(args.sav))
    if not is_valid_header(sav):
        sav = fresh_sav()
    slot = args.slot - 1
    base = slot_addr(slot)
    sav[base:base + SLOT_SIZE] = b'\x00' * SLOT_SIZE
    save_sav(Path(args.sav), sav)
    print(f'  OK Slot {slot+1} svuotato in {args.sav}')


def cmd_blank(args):
    out = Path(args.sav)
    save_sav(out, fresh_sav())
    print(f'  OK Creato .sav vuoto: {out}')


def main():
    p = argparse.ArgumentParser(
        prog='fts_tool',
        description='FastTracker GB — manipolazione file .sav e brani .fts'
    )
    sub = p.add_subparsers(dest='cmd', required=True)

    sp = sub.add_parser('info', help='Mostra il contenuto di un .sav')
    sp.add_argument('sav', help='File .sav da analizzare')
    sp.set_defaults(func=cmd_info)

    sp = sub.add_parser('extract', help='Estrae gli slot occupati come .fts')
    sp.add_argument('sav', help='File .sav di input')
    sp.add_argument('out', nargs='?', default='.',
                    help='Cartella di output (default: ./)')
    sp.set_defaults(func=cmd_extract)

    sp = sub.add_parser('import', help='Importa un .fts in uno slot del .sav')
    sp.add_argument('sav', help='File .sav (creato se non esiste)')
    sp.add_argument('slot', type=int, help='Numero slot 1..4')
    sp.add_argument('fts', help='File .fts da importare')
    sp.set_defaults(func=cmd_import)

    sp = sub.add_parser('clear', help='Svuota uno slot nel .sav')
    sp.add_argument('sav', help='File .sav')
    sp.add_argument('slot', type=int, help='Numero slot 1..4')
    sp.set_defaults(func=cmd_clear)

    sp = sub.add_parser('blank', help='Crea un .sav vuoto pronto all\'uso')
    sp.add_argument('sav', help='Path dove scrivere il .sav vuoto')
    sp.set_defaults(func=cmd_blank)

    args = p.parse_args()
    return args.func(args) or 0


if __name__ == '__main__':
    sys.exit(main())

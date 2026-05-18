; ============================================================
;  FastTracker GB — ROM header + boot vectors
; ============================================================

INCLUDE "hardware.inc"

; --------- Reset / interrupt vectors ---------
SECTION "RST_00", ROM0[$0000]
    jp Start
SECTION "RST_08", ROM0[$0008]
    jp Start
SECTION "RST_10", ROM0[$0010]
    jp Start
SECTION "RST_18", ROM0[$0018]
    jp Start
SECTION "RST_20", ROM0[$0020]
    jp Start
SECTION "RST_28", ROM0[$0028]
    jp Start
SECTION "RST_30", ROM0[$0030]
    jp Start
SECTION "RST_38", ROM0[$0038]
    jp Start

SECTION "INT_VBLANK", ROM0[$0040]
    jp VBlankInterrupt

SECTION "INT_STAT",   ROM0[$0048]
    reti
SECTION "INT_TIMER",  ROM0[$0050]
    reti
SECTION "INT_SERIAL", ROM0[$0058]
    reti
SECTION "INT_JOYPAD", ROM0[$0060]
    reti

; --------- Cartridge header ---------
; rgbfix will fill the Nintendo logo and checksums; we just need
; the bytes from $0100 onward.

SECTION "Header", ROM0[$0100]

EntryPoint:
    nop
    jp Start

; $0104-$0133 Nintendo logo (rgbfix -p will fill / fix)
    DS $30, 0

; $0134-$0142 Title (15 bytes — rgbfix -t will write this)
    DS 15, 0
; $0143 CGB flag — $C0 = CGB only
    DB $C0
; $0144-$0145 New licensee code
    DB "00"
; $0146 SGB flag
    DB $00
; $0147 Cartridge type — MBC5 + RAM + Battery
    DB $1B
; $0148 ROM size — 256 KiB (16 banks)
    DB $03
; $0149 RAM size — 32 KiB (4 banks of 8K)
    DB $03
; $014A Destination code
    DB $01
; $014B Old licensee code
    DB $33
; $014C Mask ROM version
    DB $00
; $014D Header checksum (rgbfix -v will compute)
    DB $00
; $014E-$014F Global checksum (rgbfix -v will compute)
    DW $0000

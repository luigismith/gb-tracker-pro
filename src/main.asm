; ============================================================
;  FastTracker GB — main entry, init, main loop
; ============================================================

INCLUDE "hardware.inc"

; ------------------------------------------------------------
;  CGB BGR555 color constants (must come before any reference)
;  word = (B<<10) | (G<<5) | R    (R,G,B are 5-bit values 0..31)
; ------------------------------------------------------------
DEF C_BLACK     EQU $0000
DEF C_WHITE     EQU $7FFF
DEF C_NAVY      EQU $3063        ; R=3,  G=3,  B=12   dark blue
DEF C_CYAN      EQU $7380        ; R=0,  G=28, B=28   bright cyan
DEF C_DIMCYAN   EQU $4A8A        ; R=10, G=20, B=18   greenish cyan
DEF C_MAGENTA   EQU $701C        ; R=28, G=0,  B=28   pink/magenta
DEF C_YELLOW    EQU $03FF        ; R=31, G=31, B=0
DEF C_GREEN     EQU $0380        ; R=0,  G=28, B=0
DEF C_DARKRED   EQU $0012        ; R=18, G=0,  B=0
DEF C_ORANGE    EQU $025F        ; R=31, G=18, B=0
DEF C_PURPLE    EQU $7018        ; R=24, G=0,  B=28

; ------------------------------------------------------------
;  WRAM layout (Bank 0)
; ------------------------------------------------------------
SECTION "WRAM_Globals", WRAM0[$C100]

IsCGB::         DS 1         ; 1 if running on CGB, 0 on DMG
AppMode::       DS 1         ; 0=pattern editor, 1=save/load menu
MenuSlot::      DS 1         ; selected slot 0..3 in the menu
MenuFlash::     DS 1         ; non-zero shows a "Saved!" / "Loaded!" toast
MenuDirty::     DS 1         ; menu needs a heavy redraw (clear + chrome)
VBlankFlag::    DS 1         ; nonzero when VBlank has fired this frame
FrameCounter::  DS 1         ; increments every VBlank
JoyState::      DS 1         ; current held bits (bit set = pressed)
JoyDown::       DS 1         ; bits that transitioned 0->1 this frame
JoyPrev::       DS 1         ; previous frame held state
CursorRow::     DS 1         ; pattern editor cursor row (0..31)
CursorCol::     DS 1         ; pattern editor cursor channel (0..3)
ViewTopRow::    DS 1         ; first row currently shown on screen
CurrentPattern::DS 1         ; pattern index being edited (0..3)
CurrentNote::   DS 1         ; note index to stamp on A press (1..60)
CurrentInst::   DS 1         ; instrument index to stamp (1..16)
CurrentOctave:: DS 1         ; selected octave (2..6)
RedrawFlags::   DS 1         ; bit 0 = redraw pattern, bit 1 = redraw status
PlayMode::      DS 1         ; 0 = stopped, 1 = playing
LastNotePlayed::DS 1         ; for jam mode
BpmDisplay::    DS 1         ; cached BPM = 900 / SongSpeed
LastCursorRow:: DS 1         ; previous frame's cursor row (for dirty check)
LastCursorCol:: DS 1
LastPlayerRow:: DS 1
LastPattern::   DS 1
Padding1::      DS 32

; ------------------------------------------------------------
;  Stack at top of WRAM0
; ------------------------------------------------------------
SECTION "Stack", WRAM0[$CF00]
StackBase:: DS 256
StackTop::

; ------------------------------------------------------------
;  Cartridge code start
; ------------------------------------------------------------
SECTION "Main", ROM0

Start::
    di
    ld sp, StackTop

    ; --- CGB detection ---
    ; Boot ROM leaves A=$11 on CGB, $01 on DMG.
    ; Remember whether we're on CGB for later (palette setup, VBK use).
    ld [IsCGB], a              ; preserves the boot-ROM A value byte
    cp $11
    jr z, .is_cgb
    xor a
    ld [IsCGB], a              ; not CGB

.is_cgb:
    ; --- Initialize joypad for reading ---
    ld a, P1F_GET_NONE
    ldh [rP1], a

    ; --- Turn LCD off so VRAM is freely writable ---
    call WaitVBlank
    xor a
    ldh [rLCDC], a

    ; --- Zero OAM ---
    ld hl, $FE00
    ld bc, 160
    xor a
    call MemFill

    ; --- Zero WRAM (skip the stack area to be safe) ---
    ld hl, $C000
    ld bc, $0F00
    xor a
    call MemFill

    ; --- Copy font tiles into VRAM ---
    ld hl, FontTiles
    ld de, $8000
    ld bc, FontTiles_End - FontTiles
    call MemCopy

    ; --- Set up CGB BG palettes ---
    call SetupPalettes

    ; --- Clear BG tilemap with space tile (0) ---
    xor a
    ldh [rVBK], a
    ld hl, $9800
    ld bc, $0400
    xor a
    call MemFill

    ; --- Clear BG attribute map with palette 0 ---
    ld a, 1
    ldh [rVBK], a
    ld hl, $9800
    ld bc, $0400
    xor a
    call MemFill
    xor a
    ldh [rVBK], a

    ; --- Init game state ---
    ld a, 5
    ld [CurrentOctave], a
    ld a, $19                ; A-4 (octave 4, semitone 9 -> index 12*2 + 9 = 33? )
    ld [CurrentNote], a
    ld a, 1
    ld [CurrentInst], a
    xor a
    ld [CursorRow], a
    ld [CursorCol], a
    ld [ViewTopRow], a
    ld [CurrentPattern], a
    ld [PlayMode], a

    ; --- Init save system + song + player ---
    call SaveSystem_Init
    call SongInitDefault             ; pre-load Per Elisa demo in WRAM
    call PlayerInit
    call PlayerStart                 ; start playback immediately

    ; Force a pattern redraw on the very first UI_Update tick.
    ld a, $FF
    ld [LastCursorRow], a
    ld [LastCursorCol], a
    ld [LastPlayerRow], a
    ld [LastPattern], a

    ; --- Draw initial UI (LCD still off — safe to write VRAM) ---
    call UI_DrawAll

    ; --- LCD setup ---
    ld a, %11100100
    ldh [rBGP], a
    xor a
    ldh [rSCY], a
    ldh [rSCX], a

    ; --- Enable VBlank interrupt ---
    ld a, IEF_VBLANK
    ldh [rIE], a
    xor a
    ldh [rIF], a
    ei

    ; --- LCD on, BG enabled, tilemap at $9800, tile data at $8000 ---
    ld a, LCDCF_ON | LCDCF_BG9800 | LCDCF_BLK21 | LCDCF_BGON
    ldh [rLCDC], a

; ------------------------------------------------------------
;  Main loop
; ------------------------------------------------------------
MainLoop::
    halt
    nop
    ld a, [VBlankFlag]
    or a
    jr z, MainLoop
    xor a
    ld [VBlankFlag], a

    call ReadJoypad
    call HandleInput
    call UI_Update
    jr MainLoop


; ============================================================
;  VBlank interrupt — drives the audio engine and incremental
;  attribute repaints (we are inside the VBlank window here, so
;  VRAM writes are always safe).
; ============================================================
VBlankInterrupt::
    push af
    push bc
    push de
    push hl

    ld hl, FrameCounter
    inc [hl]
    ld a, 1
    ld [VBlankFlag], a

    call PlayerTick

    ; If the player advanced the row, repaint the playing-row band
    ; right now while we're still inside VBlank.  Only ~40 attribute
    ; writes — well within the available 4500 cycles.
    ld a, [AppMode]
    or a
    jr nz, .skip_vblank_paint     ; menu mode, skip
    ld a, [PlayerCurrentRow]
    ld b, a
    ld a, [LastPlayerRow]
    cp b
    jr z, .skip_vblank_paint
    call UI_RepaintPlayingBand
    call UI_DrawCursor             ; re-stamp green cursor cell
    ld a, [PlayerCurrentRow]
    ld [LastPlayerRow], a
.skip_vblank_paint:

    pop hl
    pop de
    pop bc
    pop af
    reti


; ============================================================
;  Helpers
; ============================================================

WaitVBlank::
.loop
    ldh a, [rLY]
    cp 144
    jr c, .loop
    ret

; MemFill: fill BC bytes at HL with value A.  Clobbers A,B,C,HL.
MemFill::
    inc b
    inc c
    jr .start
.loop
    ld [hl+], a
.start
    dec c
    jr nz, .loop
    dec b
    jr nz, .loop
    ret

; MemCopy: copy BC bytes from HL to DE.  Clobbers A,B,C,DE,HL.
MemCopy::
    inc b
    inc c
    jr .start
.loop
    ld a, [hl+]
    ld [de], a
    inc de
.start
    dec c
    jr nz, .loop
    dec b
    jr nz, .loop
    ret


; ============================================================
;  CGB Palette setup (8 palettes × 4 colors × 2 bytes = 64 bytes)
; ============================================================
SetupPalettes::
    ld a, $80                 ; auto-increment, index 0
    ldh [rBCPS], a
    ld hl, PaletteData
    ld b, 64
.next
    ld a, [hl+]
    ldh [rBCPD], a
    dec b
    jr nz, .next
    ret

PaletteData:
    ; Palette 0: pattern view normal — navy bg / cyan text
    DW C_NAVY, C_CYAN,    C_DIMCYAN, C_WHITE
    ; Palette 1: title bar — magenta bg / yellow text
    DW C_MAGENTA, C_YELLOW, C_WHITE, C_WHITE
    ; Palette 2: cursor cell — green bg / black text
    DW C_GREEN, C_BLACK, C_BLACK, C_WHITE
    ; Palette 3: cursor row — dark red bg / white text
    DW C_DARKRED, C_WHITE, C_YELLOW, C_WHITE
    ; Palette 4: playing row — orange bg / black text
    DW C_ORANGE, C_BLACK, C_BLACK, C_WHITE
    ; Palette 5: dim text — navy bg / purple text
    DW C_NAVY, C_PURPLE, C_WHITE, C_WHITE
    ; Palette 6: column header — black bg / yellow text
    DW C_BLACK, C_YELLOW, C_WHITE, C_WHITE
    ; Palette 7: status bar — black bg / green text
    DW C_BLACK, C_GREEN, C_WHITE, C_WHITE

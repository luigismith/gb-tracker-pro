; ============================================================
;  FastTracker GB — UI drawing
; ============================================================

INCLUDE "hardware.inc"

DEF SCREEN_TILES_W EQU 20
DEF TILEMAP_BASE   EQU $9800

DEF PATTERN_VIEW_ROWS  EQU 12
DEF PATTERN_VIEW_TOP_Y EQU 4

; X tile offsets for channel notes (each note is 3 tiles wide)
DEF CH0_X EQU 3
DEF CH1_X EQU 7
DEF CH2_X EQU 11
DEF CH3_X EQU 15

SECTION "UI", ROM0

; ------------------------------------------------------------
; UI_DrawAll — full redraw.  We turn the LCD off so the long
; VRAM writes (clearing 1 KB tilemap, then redrawing 4 sub-views)
; aren't dropped during PPU mode 3.  This causes a single frame of
; black flash but produces a clean, artifact-free result.
; ------------------------------------------------------------
UI_DrawAll::
    ; If LCD is currently on, wait for VBlank then turn it off.
    ldh a, [rLCDC]
    bit 7, a
    jr z, .lcd_already_off
    call WaitVBlank
    xor a
    ldh [rLCDC], a
.lcd_already_off:

    ; Clear tilemap with space tile
    xor a
    ldh [rVBK], a
    ld hl, TILEMAP_BASE
    ld bc, $0400
    ld a, ' ' - $20
    call MemFill

    ; Clear attribute map with palette 0
    ld a, 1
    ldh [rVBK], a
    ld hl, TILEMAP_BASE
    ld bc, $0400
    xor a
    call MemFill
    xor a
    ldh [rVBK], a

    call UI_DrawTitleBar
    call UI_DrawStatusLine
    call UI_DrawColumnHeader
    call UI_DrawHelpLine
    call UI_DrawPattern
    call UI_DrawCursor

    ; LCD back on with the same bits as boot
    ld a, LCDCF_ON | LCDCF_BG9800 | LCDCF_BLK21 | LCDCF_BGON
    ldh [rLCDC], a
    ret


UI_Update::
    ld a, [AppMode]
    or a
    jr nz, .menu

    call UI_RecenterView
    call UI_DrawStatusLine
    call UI_DrawHelpLine

    ; The VBlank ISR has already done the incremental playing-row
    ; repaint when needed.  Here we only handle structural changes
    ; (cursor/pattern) that require a full pattern redraw.
    ld a, [CursorRow]
    ld b, a
    ld a, [LastCursorRow]
    cp b
    jr nz, .full
    ld a, [CursorCol]
    ld b, a
    ld a, [LastCursorCol]
    cp b
    jr nz, .full
    ld a, [CurrentPattern]
    ld b, a
    ld a, [LastPattern]
    cp b
    ret z                     ; no structural change

.full:
    ; Save new Last* values
    ld a, [CursorRow]
    ld [LastCursorRow], a
    ld a, [CursorCol]
    ld [LastCursorCol], a
    ld a, [PlayerCurrentRow]
    ld [LastPlayerRow], a
    ld a, [CurrentPattern]
    ld [LastPattern], a

    ; Full redraw with LCD off — rare event (user input, pattern switch).
    ; The brief blink is invisible because it only happens on key press.
    ldh a, [rLCDC]
    bit 7, a
    jr z, .skip_lcd_off
    call WaitVBlank
    xor a
    ldh [rLCDC], a
.skip_lcd_off:
    call UI_DrawPattern
    call UI_DrawCursor
    ld a, LCDCF_ON | LCDCF_BG9800 | LCDCF_BLK21 | LCDCF_BGON
    ldh [rLCDC], a
    ret

.menu:
    ; Only redraw the menu when something has changed.
    ld a, [MenuDirty]
    or a
    ret z
    xor a
    ld [MenuDirty], a
    call UI_DrawSaveMenu
    ret


; ------------------------------------------------------------
;  UI_DrawSaveMenu — modal listing of 4 save slots.
;  Called every frame while AppMode = 1.
; ------------------------------------------------------------
UI_DrawSaveMenu::
    ; Clear tilemap + attribute map.  We spegniamo brevemente il LCD
    ; per evitare il VRAM-blocking durante PPU mode 3.
    ldh a, [rLCDC]
    bit 7, a
    jr z, .menu_lcd_already_off
    call WaitVBlank
    xor a
    ldh [rLCDC], a
.menu_lcd_already_off:

    xor a
    ldh [rVBK], a
    ld hl, TILEMAP_BASE
    ld bc, $0400
    ld a, ' ' - $20
    call MemFill

    ld a, 1
    ldh [rVBK], a
    ld hl, TILEMAP_BASE
    ld bc, $0400
    xor a
    call MemFill
    xor a
    ldh [rVBK], a

    ; --- Title row (row 0, palette 1) ---
    ld a, 1
    ldh [rVBK], a
    ld hl, TILEMAP_BASE
    ld a, 1
    call FillRowAttr_LCD_safe
    xor a
    ldh [rVBK], a
    ld hl, TILEMAP_BASE + 2
    ld de, StrMenuTitle
    call UI_PrintZ

    ; --- Subtitle row (row 1, palette 7) ---
    ld a, 1
    ldh [rVBK], a
    ld hl, TILEMAP_BASE + 32*1
    ld a, 7
    call FillRowAttr_LCD_safe
    xor a
    ldh [rVBK], a
    ld hl, TILEMAP_BASE + 32*1
    ld de, StrMenuSubtitle
    call UI_PrintZ

    ; --- 4 slot rows (rows 4, 6, 8, 10) ---
    ld c, 0                   ; C = slot index
.slot_loop:
    push bc
    ; HL = tilemap row addr = $9800 + 32*(4 + C*2)
    ld a, c
    add a                     ; *2
    add 4
    ld l, a
    ld h, 0
    add hl, hl    ; *2
    add hl, hl    ; *4
    add hl, hl    ; *8
    add hl, hl    ; *16
    add hl, hl    ; *32
    ld bc, TILEMAP_BASE
    add hl, bc
    pop bc
    push bc
    push hl                   ; save tilemap addr

    ; Set palette for this row: highlight selected slot in palette 3
    ld a, 1
    ldh [rVBK], a
    pop hl                    ; tilemap addr
    push hl

    ; Determine palette: 3 if C == MenuSlot, 0 otherwise
    ld a, [MenuSlot]
    cp c
    jr nz, .pal_normal
    ld a, 3
    jr .write_attr
.pal_normal:
    xor a
.write_attr:
    call FillRowAttr_LCD_safe
    xor a
    ldh [rVBK], a

    pop hl                    ; tilemap addr
    pop bc                    ; restore C
    push bc

    ; Print "Slot N: ..."
    inc hl                    ; column 1
    ld a, 'S' - $20
    ld [hl+], a
    ld a, 'L' - $20
    ld [hl+], a
    ld a, 'O' - $20
    ld [hl+], a
    ld a, 'T' - $20
    ld [hl+], a
    ld a, ' ' - $20
    ld [hl+], a
    ld a, c
    add '1' - $20             ; "1".."4"
    ld [hl+], a
    ld a, ':' - $20
    ld [hl+], a
    ld a, ' ' - $20
    ld [hl+], a

    ; Slot status — IsSlotValid clobbers HL AND BC (GetSlotAddr uses ld bc).
    ; We push hl AND bc, plus call IsSlotValid which preserves Z.
    push bc                   ; preserve visual slot counter
    push hl                   ; preserve tilemap pointer
    ld a, c                   ; A = slot index
    call IsSlotValid          ; sets Z flag
    pop hl                    ; restore tilemap
    pop bc                    ; restore BC (C = slot)
    jr nz, .empty_slot
    ld de, StrSlotUsed
    jr .print_status
.empty_slot:
    ld de, StrSlotEmpty
.print_status:
    call UI_PrintZ

    pop bc
    inc c
    ld a, c
    cp 4
    jr c, .slot_loop

    ; --- Tempo + hint rows ---
    ld a, 1
    ldh [rVBK], a
    ld hl, TILEMAP_BASE + 32*12
    ld a, 6                    ; palette 6 = black/yellow, makes tempo pop
    call FillRowAttr_LCD_safe
    ld hl, TILEMAP_BASE + 32*13
    ld a, 7
    call FillRowAttr_LCD_safe
    ld hl, TILEMAP_BASE + 32*15
    ld a, 7
    call FillRowAttr_LCD_safe
    ld hl, TILEMAP_BASE + 32*16
    ld a, 7
    call FillRowAttr_LCD_safe
    ld hl, TILEMAP_BASE + 32*17
    ld a, 7
    call FillRowAttr_LCD_safe
    xor a
    ldh [rVBK], a

    ; Row 12 — live tempo "TEMPO: XXX BPM" (digits overwrite the "000" at col 7)
    ld hl, TILEMAP_BASE + 32*12
    ld de, StrMenuTempo
    call UI_PrintZ
    ld hl, TILEMAP_BASE + 32*12 + 7
    ld a, [BpmDisplay]
    call UI_PrintByte3

    ld hl, TILEMAP_BASE + 32*13
    ld de, StrMenuFlashLine
    call UI_PrintZ
    ; Flash text if MenuFlash != 0
    ld a, [MenuFlash]
    or a
    jr z, .no_flash
    cp 1
    jr nz, .flash_load
    ld hl, TILEMAP_BASE + 32*13 + 5
    ld de, StrSaved
    call UI_PrintZ
    jr .no_flash
.flash_load:
    ld hl, TILEMAP_BASE + 32*13 + 5
    ld de, StrLoaded
    call UI_PrintZ
.no_flash:

    ld hl, TILEMAP_BASE + 32*15
    ld de, StrMenuHelp1
    call UI_PrintZ
    ld hl, TILEMAP_BASE + 32*16
    ld de, StrMenuHelp2
    call UI_PrintZ
    ld hl, TILEMAP_BASE + 32*17
    ld de, StrMenuHelp3
    call UI_PrintZ

    ; LCD on
    ld a, LCDCF_ON | LCDCF_BG9800 | LCDCF_BLK21 | LCDCF_BGON
    ldh [rLCDC], a
    ret

StrMenuTitle:
    DB " SAVE / LOAD SONGS", 0
StrMenuSubtitle:
    DB "Choose a slot", 0
StrSlotUsed:
    DB "SAVED", 0
StrSlotEmpty:
    DB "EMPTY", 0
StrSaved:
    DB ">>> SAVED <<<", 0
StrLoaded:
    DB ">>> LOADED <<<", 0
StrMenuFlashLine:
    DB "                    ", 0
StrMenuTempo:
    DB "TEMPO: 000 BPM", 0
StrMenuHelp1:
    DB "A:LOAD  B:SAVE", 0
StrMenuHelp2:
    DB "<>: change tempo", 0
StrMenuHelp3:
    DB "SELECT: back", 0


; ------------------------------------------------------------
; Recenter the pattern view so the cursor stays visible.
; ------------------------------------------------------------
UI_RecenterView::
    ld a, [CursorRow]
    ld b, a
    ld a, [ViewTopRow]
    ld c, a
    cp b
    jr z, .check_below
    jr c, .check_below
    ; cursor < view_top
    ld a, b
    ld [ViewTopRow], a
    ret
.check_below
    ; if cursor >= view_top + PATTERN_VIEW_ROWS, scroll down
    ld a, c
    add PATTERN_VIEW_ROWS
    dec a
    cp b
    ret nc                    ; cursor still in band
    ld a, b
    sub PATTERN_VIEW_ROWS - 1
    ld [ViewTopRow], a
    ret


; ------------------------------------------------------------
; Helpers: write attribute byte to a single tilemap row.
;   in: A = palette number, HL = tilemap addr (already in attr bank)
; ------------------------------------------------------------
FillRowAttr_LCD_safe:
    ld b, SCREEN_TILES_W
.l:
    ld [hl+], a
    dec b
    jr nz, .l
    ret


; ------------------------------------------------------------
UI_DrawTitleBar::
    ld a, 1
    ldh [rVBK], a
    ld hl, TILEMAP_BASE
    ld a, 1
    call FillRowAttr_LCD_safe
    xor a
    ldh [rVBK], a

    ld hl, TILEMAP_BASE
    ld de, StrTitle
    call UI_PrintZ
    ret


UI_DrawColumnHeader::
    ld a, 1
    ldh [rVBK], a
    ld hl, TILEMAP_BASE + 32*3
    ld a, 6
    call FillRowAttr_LCD_safe
    xor a
    ldh [rVBK], a

    ld hl, TILEMAP_BASE + 32*3
    ld de, StrColHeader
    call UI_PrintZ
    ret


UI_DrawHelpLine::
    ld a, 1
    ldh [rVBK], a
    ld hl, TILEMAP_BASE + 32*17
    ld a, 7
    call FillRowAttr_LCD_safe
    xor a
    ldh [rVBK], a
    ld hl, TILEMAP_BASE + 32*17
    ld de, StrHelp
    call UI_PrintZ
    ; Live playing-row indicator at the right edge
    ld hl, TILEMAP_BASE + 32*17 + 18
    ld a, [PlayerCurrentRow]
    call UI_PrintHex8
    ret


UI_DrawStatusLine::
    ld a, 1
    ldh [rVBK], a
    ld hl, TILEMAP_BASE + 32*1
    ld a, 7
    call FillRowAttr_LCD_safe
    xor a
    ldh [rVBK], a

    ld hl, TILEMAP_BASE + 32*1
    ld de, StrStatus
    call UI_PrintZ

    ld hl, TILEMAP_BASE + 32*1 + 3
    ld a, [CurrentPattern]
    call UI_PrintHex8                 ; PT:XX (col 3-4)

    ld hl, TILEMAP_BASE + 32*1 + 8
    ld a, [CurrentNote]
    call UI_PrintNote                 ; N:NNN (col 8-10)

    ld hl, TILEMAP_BASE + 32*1 + 16
    ld a, [BpmDisplay]
    call UI_PrintByte3                ; BPM:XXX (col 16-18)
    ret


; ------------------------------------------------------------
;  UI_DrawPattern
;  Draws PATTERN_VIEW_ROWS pattern rows starting at ViewTopRow.
; ------------------------------------------------------------
UI_DrawPattern::
    ld c, 0                   ; C = visual row 0..VIEW_ROWS-1
.row_loop:
    push bc                   ; save visual row

    ; pattern_row = ViewTopRow + C  → keep in WRAM scratch
    ld a, [ViewTopRow]
    add c
    ld [Scratch_PatternRow], a

    ; Compute tilemap addr for this visual row.
    ;   HL = $9800 + (PATTERN_VIEW_TOP_Y + C) * 32
    ld a, PATTERN_VIEW_TOP_Y
    add c
    ld l, a
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld bc, TILEMAP_BASE
    add hl, bc

    push hl                   ; save tilemap addr (row start)

    ; --- Print 2-digit row number ---
    ld a, [Scratch_PatternRow]
    call UI_PrintHex8         ; HL += 2

    ; --- Get pattern row data into BC ---
    ld a, [CurrentPattern]
    ld d, a
    ld a, [Scratch_PatternRow]
    ld e, a
    call PatternGetRowAddr    ; in: D=pat, E=row; out: HL=row addr
    ld b, h
    ld c, l

    pop hl                    ; tilemap addr (row start)
    push hl                   ; keep a second copy for attr pass

    ; advance HL to first channel column
    ld a, l
    add CH0_X
    ld l, a
    ld a, h
    adc 0
    ld h, a

    ; Channel 0
    ld a, [bc]
    inc bc
    inc bc
    call UI_PrintNote         ; HL += 3
    inc hl                    ; gap
    ; Channel 1
    ld a, [bc]
    inc bc
    inc bc
    call UI_PrintNote
    inc hl
    ; Channel 2
    ld a, [bc]
    inc bc
    inc bc
    call UI_PrintNote
    inc hl
    ; Channel 3
    ld a, [bc]
    call UI_PrintNote

    ; --- Attribute pass for this row ---
    pop hl                    ; tilemap addr (row start)
    ld a, 1
    ldh [rVBK], a

    ld a, [Scratch_PatternRow]
    ld d, a
    ld a, [CursorRow]
    cp d
    jr z, .pal_cursor
    ld a, [PlayMode]
    or a
    jr z, .pal_normal
    ld a, [PlayerCurrentRow]
    cp d
    jr z, .pal_playing
.pal_normal:
    xor a
    jr .write_attr
.pal_cursor:
    ld a, 3
    jr .write_attr
.pal_playing:
    ld a, 4
.write_attr:
    call FillRowAttr_LCD_safe
    xor a
    ldh [rVBK], a

    pop bc                    ; restore visual row in C
    inc c
    ld a, c
    cp PATTERN_VIEW_ROWS
    jr c, .row_loop
    ret


; ------------------------------------------------------------
;  UI_RepaintRow — set palette of all 20 tiles of one pattern-view
;  row.  In:  D = pattern row (0..31), A = palette (0/3/4).  If the
;  row is off-screen this is a no-op.
;  Writes 20 attribute bytes — small enough to finish entirely within
;  a VBlank window without LCD flicker.
; ------------------------------------------------------------
UI_RepaintRow::
    push af
    ; visual row = D - ViewTopRow.  If negative or >= PATTERN_VIEW_ROWS, bail.
    ld a, [ViewTopRow]
    ld c, a
    ld a, d
    sub c                     ; A = visual offset
    jr c, .skip               ; D < ViewTopRow
    cp PATTERN_VIEW_ROWS
    jr nc, .skip              ; offscreen below

    ; tilemap addr = $9800 + 32 * (PATTERN_VIEW_TOP_Y + A)
    add PATTERN_VIEW_TOP_Y
    ld l, a
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld bc, TILEMAP_BASE
    add hl, bc

    ; Switch to attribute bank
    ld a, 1
    ldh [rVBK], a
    pop af                    ; recover palette number
    push af                   ; (re-push so .skip path also pops)
    ld b, SCREEN_TILES_W
.fill:
    ld [hl+], a
    dec b
    jr nz, .fill
    xor a
    ldh [rVBK], a
.skip:
    pop af
    ret


; ------------------------------------------------------------
;  UI_RepaintPlayingBand — repaint old + new playing-row bands.
;  Reads LastPlayerRow and PlayerCurrentRow.  Restores the old row
;  to palette 0 (or 3 if it is the cursor row), and paints the new
;  row in palette 4.
;  This is the hot path during playback — only ~40 attribute writes
;  per advance, all done while STAT is still in VBlank (the caller
;  invokes this right after main wakes from VBlank IRQ).
; ------------------------------------------------------------
UI_RepaintPlayingBand::
    ; --- Clear old playing row ---
    ld a, [LastPlayerRow]
    ld d, a
    ; Determine which palette to restore: 3 if D == CursorRow, else 0.
    ld a, [CursorRow]
    cp d
    ld a, 0
    jr nz, .old_pal_set
    ld a, 3
.old_pal_set:
    call UI_RepaintRow

    ; --- Paint new playing row ---
    ld a, [PlayerCurrentRow]
    ld d, a
    ; If new playing row coincides with cursor row, the cursor palette
    ; (3) wins — DrawCursor stamp will re-apply later anyway.
    ld a, [CursorRow]
    cp d
    ld a, 4                    ; playing
    jr nz, .new_pal_set
    ld a, 3                    ; cursor row wins
.new_pal_set:
    call UI_RepaintRow
    ret


; ------------------------------------------------------------
;  UI_DrawCursor — highlight the single cell under the cursor
;  with palette 2.
; ------------------------------------------------------------
UI_DrawCursor::
    ld a, [CursorRow]
    ld b, a
    ld a, [ViewTopRow]
    ld c, a
    ld a, b
    sub c                     ; visual offset
    ret c                     ; cursor above view
    cp PATTERN_VIEW_ROWS
    ret nc                    ; cursor below view

    ; Tilemap row addr = $9800 + 32*(PATTERN_VIEW_TOP_Y + A)
    add PATTERN_VIEW_TOP_Y
    ld l, a
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld bc, TILEMAP_BASE
    add hl, bc

    ; Add channel X offset
    ld a, [CursorCol]
    and 3
    ld c, a
    ld b, 0
    ld de, ChannelXOffsets
    ld a, e
    add c
    ld e, a
    ld a, d
    adc 0
    ld d, a
    ld a, [de]
    ld c, a
    ld b, 0
    add hl, bc

    ; Switch to attr bank and write palette 2 across 3 tiles
    ld a, 1
    ldh [rVBK], a
    ld a, 2
    ld [hl+], a
    ld [hl+], a
    ld [hl], a
    xor a
    ldh [rVBK], a
    ret

ChannelXOffsets:
    DB CH0_X, CH1_X, CH2_X, CH3_X


; ============================================================
;  Low-level print routines
; ============================================================

; UI_PrintZ: print zero-terminated string at HL.
;   Each ASCII byte translated to tile = (char - $20).
UI_PrintZ::
.loop:
    ld a, [de]
    or a
    ret z
    sub $20
    ld [hl+], a
    inc de
    jr .loop


; UI_PrintByte3: print A (0..255) as 3 decimal digits at HL.  HL += 3.
UI_PrintByte3::
    push bc
    ; Hundreds
    ld b, 100
    ld c, 0
.h_loop:
    cp b
    jr c, .h_done
    sub b
    inc c
    jr .h_loop
.h_done:
    push af
    ld a, c
    add '0' - $20
    ld [hl+], a
    pop af
    ; Tens
    ld b, 10
    ld c, 0
.t_loop:
    cp b
    jr c, .t_done
    sub b
    inc c
    jr .t_loop
.t_done:
    push af
    ld a, c
    add '0' - $20
    ld [hl+], a
    pop af
    ; Units
    add '0' - $20
    ld [hl+], a
    pop bc
    ret


; UI_PrintHex8: print A as 2 hex digits at HL.  HL += 2.
UI_PrintHex8::
    push af
    swap a
    and $0F
    call .nibble
    pop af
    and $0F
    jr .nibble
.nibble:
    cp 10
    jr c, .digit
    add 'A' - $20 - 10
    jr .write
.digit:
    add '0' - $20
.write:
    ld [hl+], a
    ret


; UI_PrintNote: print a 3-char note glyph at HL.
;   A = $00 -> "...",  $FD -> "OFF",  $01..$3C -> note name + octave digit.
UI_PrintNote::
    push bc                   ; preserve BC for the caller
    or a
    jr z, .empty
    cp $FD
    jr z, .off
    cp $3D
    jr nc, .empty             ; out of range -> empty

    ; A = 1..60.  Compute (semitone, octave).
    dec a
    ld b, a                   ; B = note-1
    ld c, 0
.divloop:
    ld a, b
    cp 12
    jr c, .div_done
    sub 12
    ld b, a
    inc c
    jr .divloop
.div_done:
    ; B = semitone (0..11), C = octave (0..4)
    push hl
    ld hl, NoteNameTable
    ld a, b
    add a
    add l
    ld l, a
    ld a, 0
    adc h
    ld h, a
    ld a, [hl+]
    ld d, a
    ld a, [hl]
    ld e, a
    pop hl

    ld a, d
    sub $20
    ld [hl+], a
    ld a, e
    sub $20
    ld [hl+], a

    ld a, c
    add '2' - $20             ; octave 0 in table = C-2
    ld [hl+], a
    pop bc
    ret

.empty:
    ld a, '.' - $20
    ld [hl+], a
    ld [hl+], a
    ld [hl+], a
    pop bc
    ret
.off:
    ld a, 'O' - $20
    ld [hl+], a
    ld a, 'F' - $20
    ld [hl+], a
    ld [hl+], a
    pop bc
    ret


; ============================================================
;  Static string data
; ============================================================
StrTitle:
    DB "  GB-TRACKER PRO    ", 0
StrColHeader:
    DB "## P1  P2  WV  NO  ", 0
StrStatus:
    DB "PT:00 N:A-4 BPM:000", 0
StrHelp:
    DB "A:NOTE  B:DEL  R:", 0

NoteNameTable::
    DB "C-"
    DB "C#"
    DB "D-"
    DB "D#"
    DB "E-"
    DB "F-"
    DB "F#"
    DB "G-"
    DB "G#"
    DB "A-"
    DB "A#"
    DB "B-"

; ------------------------------------------------------------
; Scratch byte for the pattern drawing routine.
; ------------------------------------------------------------
SECTION "UI_Scratch", WRAM0[$C0F0]
Scratch_PatternRow:: DS 1
Scratch_Misc::       DS 15

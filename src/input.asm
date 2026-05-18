; ============================================================
;  FastTracker GB — Joypad input + key dispatch
; ============================================================

INCLUDE "hardware.inc"

; Standard button bits (matching DMG convention):
;   bit 7 = Down, 6 = Up, 5 = Left, 4 = Right
;   bit 3 = Start, 2 = Select, 1 = B, 0 = A
DEF PAD_A      EQU $01
DEF PAD_B      EQU $02
DEF PAD_SEL    EQU $04
DEF PAD_START  EQU $08
DEF PAD_RIGHT  EQU $10
DEF PAD_LEFT   EQU $20
DEF PAD_UP     EQU $40
DEF PAD_DOWN   EQU $80

SECTION "Input", ROM0

; ------------------------------------------------------------
;  ReadJoypad — populate JoyState and JoyDown.
; ------------------------------------------------------------
ReadJoypad::
    ; Read D-pad
    ld a, P1F_GET_DPAD
    ldh [rP1], a
    ldh a, [rP1]
    ldh a, [rP1]              ; settle reads
    cpl                       ; invert (bits become 1 when pressed)
    and $0F
    swap a                    ; move to high nibble
    ld b, a

    ; Read buttons
    ld a, P1F_GET_BTN
    ldh [rP1], a
    ldh a, [rP1]
    ldh a, [rP1]
    cpl
    and $0F
    or b                      ; combine D-pad (high) + buttons (low)
    ld b, a                   ; B = current pad

    ; Done reading
    ld a, P1F_GET_NONE
    ldh [rP1], a

    ; Compute pressed-this-frame edge: down = current & ~previous
    ld a, [JoyPrev]
    cpl
    and b
    ld [JoyDown], a

    ld a, b
    ld [JoyState], a
    ld [JoyPrev], a
    ret


; ============================================================
;  HandleInput — interpret JoyDown / JoyState into actions.
;  Updates RedrawFlags as needed.
; ============================================================
HandleInput::
    ld a, [JoyDown]
    ld b, a                   ; B = edges this frame
    ld a, [JoyState]
    ld c, a                   ; C = held

    ; --- Dispatch on AppMode ---
    ld a, [AppMode]
    or a
    jr z, .mode_pattern
    jp Input_SaveMenu         ; mode 1 = save/load menu

.mode_pattern:
    ; Decay MenuFlash so the "Saved!" toast fades when we get back
    ld a, [MenuFlash]
    or a
    jr z, .no_flash_decay
    dec a
    ld [MenuFlash], a
.no_flash_decay:

    ; --- Start: open save/load menu if Select is held, else toggle play ---
    bit 3, b                  ; PAD_START edge
    jr z, .no_start
    bit 2, c                  ; PAD_SELECT held?
    jr nz, .open_menu
    call PlayerToggle
    jr .no_start
.open_menu:
    ld a, 1
    ld [AppMode], a
    ld [MenuDirty], a         ; force a heavy redraw next UI_Update
    xor a
    ld [MenuSlot], a
    ld [MenuFlash], a
    ret                       ; skip the rest of pattern-mode input this frame
.no_start:

    ; --- D-pad navigation (use held with simple repeat) ---
    bit 6, b                  ; UP edge
    jr z, .no_up
    call CursorUp
.no_up:
    bit 7, b                  ; DOWN edge
    jr z, .no_down
    call CursorDown
.no_down:
    bit 5, b                  ; LEFT edge
    jr z, .no_left
    call CursorLeft
.no_left:
    bit 4, b                  ; RIGHT edge
    jr z, .no_right
    call CursorRight
.no_right:

    ; --- Select held: modifier ---
    bit 2, c                  ; SELECT held
    jr nz, .sel_mod

    ; --- A pressed: stamp current note at cursor (and jam) ---
    bit 0, b
    jr z, .no_a
    call StampNote
.no_a:

    ; --- B pressed: erase cell at cursor ---
    bit 1, b
    jr z, .no_b
    call EraseCell
.no_b:
    ret

.sel_mod:
    ; Select+Up/Down -> change current note (semitone)
    bit 6, b
    jr z, .sm_no_up
    ld a, [CurrentNote]
    cp 60
    jr nc, .sm_no_up
    inc a
    ld [CurrentNote], a
    call PreviewCurrent
.sm_no_up:
    bit 7, b
    jr z, .sm_no_down
    ld a, [CurrentNote]
    cp 2
    jr c, .sm_no_down
    dec a
    ld [CurrentNote], a
    call PreviewCurrent
.sm_no_down:
    ; Select+Left/Right -> change current instrument
    bit 5, b                  ; LEFT
    jr z, .sm_no_left
    ld a, [CurrentInst]
    cp 2
    jr c, .sm_no_left
    dec a
    ld [CurrentInst], a
.sm_no_left:
    bit 4, b                  ; RIGHT
    jr z, .sm_no_right
    ld a, [CurrentInst]
    cp 16
    jr nc, .sm_no_right
    inc a
    ld [CurrentInst], a
.sm_no_right:
    ; Select+A -> preview the current note on the cursor's channel
    bit 0, b
    jr z, .sm_no_a
    call PreviewCurrent
.sm_no_a:
    ; Select+B -> change current pattern
    bit 1, b
    jr z, .sm_no_b
    ld a, [CurrentPattern]
    inc a
    and 3
    ld [CurrentPattern], a
.sm_no_b:
    ret


; ============================================================
;  Input_SaveMenu — input handler while AppMode == 1
;    A = JoyDown is in B, JoyState is in C
; ============================================================
Input_SaveMenu::
    ; SELECT: exit back to pattern editor
    bit 2, b                  ; PAD_SELECT edge
    jr z, .no_select
    xor a
    ld [AppMode], a
    ld [MenuFlash], a
    ; Force full redraw of pattern view next frame
    ld a, $FF
    ld [LastCursorRow], a
    ld [LastCursorCol], a
    ld [LastPlayerRow], a
    ld [LastPattern], a
    call UI_DrawAll
    ret
.no_select:

    ; UP: previous slot
    bit 6, b
    jr z, .no_up
    ld a, [MenuSlot]
    or a
    jr z, .no_up
    dec a
    ld [MenuSlot], a
    xor a
    ld [MenuFlash], a
    ld a, 1
    ld [MenuDirty], a
.no_up:

    ; DOWN: next slot
    bit 7, b
    jr z, .no_down
    ld a, [MenuSlot]
    cp 3
    jr nc, .no_down
    inc a
    ld [MenuSlot], a
    xor a
    ld [MenuFlash], a
    ld a, 1
    ld [MenuDirty], a
.no_down:

    ; A: LOAD selected slot (only if valid)
    bit 0, b
    jr z, .no_a
    ld a, [MenuSlot]
    push af
    call IsSlotValid
    jr nz, .skip_load
    pop af
    call LoadSlot
    ld a, 2                   ; 2 = LOADED toast
    ld [MenuFlash], a
    ld a, 1
    ld [MenuDirty], a
    ret
.skip_load:
    pop af
.no_a:

    ; B: SAVE selected slot
    bit 1, b
    ret z
    ld a, [MenuSlot]
    call SaveSlot
    ld a, 1                   ; 1 = SAVED toast
    ld [MenuFlash], a
    ld a, 1
    ld [MenuDirty], a
    ret


; ============================================================
;  Cursor manipulation
; ============================================================
CursorUp::
    ld a, [CursorRow]
    or a
    ret z
    dec a
    ld [CursorRow], a
    ret

CursorDown::
    ld a, [CursorRow]
    cp 31
    ret nc
    inc a
    ld [CursorRow], a
    ret

CursorLeft::
    ld a, [CursorCol]
    or a
    ret z
    dec a
    ld [CursorCol], a
    ret

CursorRight::
    ld a, [CursorCol]
    cp 3
    ret nc
    inc a
    ld [CursorCol], a
    ret


; ============================================================
;  StampNote — write the current note at the cursor cell
; ============================================================
StampNote::
    ld a, [CurrentPattern]
    ld d, a
    ld a, [CursorRow]
    ld e, a
    call PatternGetRowAddr    ; HL = row
    ld a, [CursorCol]
    add a                     ; *2 (each cell = 2 bytes)
    ld c, a
    ld b, 0
    add hl, bc                ; HL = cell in row
    ld a, [CurrentNote]
    ld [hl+], a
    ld a, [CurrentInst]
    ld [hl], a
    ; Preview the note so the user hears it
    call PreviewCurrent
    ; Auto-advance cursor down one row
    call CursorDown
    ret


; ============================================================
;  EraseCell — clear note + inst at cursor
; ============================================================
EraseCell::
    ld a, [CurrentPattern]
    ld d, a
    ld a, [CursorRow]
    ld e, a
    call PatternGetRowAddr
    ld a, [CursorCol]
    add a
    ld c, a
    ld b, 0
    add hl, bc
    xor a
    ld [hl+], a
    ld [hl], a
    call CursorDown
    ret


; ============================================================
;  PreviewCurrent — jam current note on cursor's channel
; ============================================================
PreviewCurrent::
    ld a, [CurrentNote]
    ld b, a
    ld a, [CurrentInst]
    ld c, a
    ld a, [CursorCol]
    and 3
    jp PlayNoteNow

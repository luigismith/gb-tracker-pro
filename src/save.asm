; ============================================================
;  FastTracker GB — Save / Load to MBC5 battery-backed SRAM
;
;  Cartridge has 32 KB SRAM (4 banks of 8 KB).  We use bank 0.
;
;  SRAM layout (bank 0, $A000-$BFFF = 8192 bytes):
;    $A000..$A00F : Header (16 byte)
;      $A000..$A003 : magic "FTGB"
;      $A004        : format version (2)
;      $A005        : slot count (4)
;      $A006..$A00F : reserved (zero)
;    $A010..$A80B : Slot 0 (2044 byte)   contains full song
;    $A80C..$B007 : Slot 1
;    $B008..$B803 : Slot 2
;    $B804..$BFFF : Slot 3
;
;  Slot layout (2044 byte):
;    +0:    slot magic ($FE)
;    +1:    speed
;    +2:    order length
;    +3:    reserved
;    +4..19: order list (16 byte)
;    +20..1043: 4 × pattern (256 byte each) = 1024 byte
;    +1044..2043: reserved (1000 byte)
;
;  Format version is now 2 because the slot layout grew.
;  On boot, if the header version != 2 (or magic missing) we reformat.
; ============================================================

INCLUDE "hardware.inc"

DEF SRAM_BASE         EQU $A000
DEF SLOT_SIZE         EQU 2044
DEF SLOT0_ADDR        EQU SRAM_BASE + 16
DEF SAVE_MAGIC_0      EQU $46     ; 'F'
DEF SAVE_MAGIC_1      EQU $54     ; 'T'
DEF SAVE_MAGIC_2      EQU $47     ; 'G'
DEF SAVE_MAGIC_3      EQU $42     ; 'B'
DEF SAVE_FORMAT_VER   EQU 2
DEF SAVE_SLOT_COUNT   EQU 4
DEF SLOT_MAGIC        EQU $FE

DEF PAT_BYTES         EQU 256                ; bytes per pattern
DEF NUM_PATTERNS      EQU 4
DEF ALL_PATTERN_BYTES EQU PAT_BYTES * NUM_PATTERNS  ; 1024

SECTION "SaveCode", ROM0

; ------------------------------------------------------------
;  SRAM_Enable / SRAM_Disable
; ------------------------------------------------------------
SRAM_Enable::
    ld a, $0A
    ld [$0000], a
    xor a
    ld [$4000], a
    ret

SRAM_Disable::
    xor a
    ld [$0000], a
    ret


; ------------------------------------------------------------
;  SaveSystem_Init
;  Check magic + version.  If wrong, reformat and install the
;  demo cover into slot 1 (index 0).
; ------------------------------------------------------------
SaveSystem_Init::
    call SRAM_Enable

    ; Check magic + version
    ld hl, SRAM_BASE
    ld a, [hl+]
    cp SAVE_MAGIC_0
    jr nz, .format
    ld a, [hl+]
    cp SAVE_MAGIC_1
    jr nz, .format
    ld a, [hl+]
    cp SAVE_MAGIC_2
    jr nz, .format
    ld a, [hl+]
    cp SAVE_MAGIC_3
    jr nz, .format
    ld a, [hl]
    cp SAVE_FORMAT_VER
    jr nz, .format
    ret

.format:
    ; Wipe entire bank
    ld hl, SRAM_BASE
    ld bc, 8192
    xor a
    call MemFill

    ; Write header
    ld hl, SRAM_BASE
    ld a, SAVE_MAGIC_0
    ld [hl+], a
    ld a, SAVE_MAGIC_1
    ld [hl+], a
    ld a, SAVE_MAGIC_2
    ld [hl+], a
    ld a, SAVE_MAGIC_3
    ld [hl+], a
    ld a, SAVE_FORMAT_VER
    ld [hl+], a
    ld a, SAVE_SLOT_COUNT
    ld [hl], a

    ; Install demo cover into slot 1 (index 0)
    call SaveSystem_InstallDemo
    ret


; ------------------------------------------------------------
;  GetSlotAddr — HL = SLOT0_ADDR + A * SLOT_SIZE
;    in: A = slot (0..3)
;  SLOT_SIZE = 2044 = $7FC.  HL = A * 2044 + SLOT0_ADDR.
;  Build by: H,L pair = A*2044, then add base.
;  A * 2044 = A * 2048 - A * 4 = (A << 11) - (A << 2)
;  We implement via repeated 16-bit shift.
; ------------------------------------------------------------
GetSlotAddr::
    ; Compute A * 2044 in HL
    ld h, 0
    ld l, a            ; HL = A
    add hl, hl         ; *2
    add hl, hl         ; *4
    ld b, h
    ld c, l            ; BC = A*4
    add hl, hl         ; *8
    add hl, hl         ; *16
    add hl, hl         ; *32
    add hl, hl         ; *64
    add hl, hl         ; *128
    add hl, hl         ; *256
    add hl, hl         ; *512
    add hl, hl         ; *1024
    add hl, hl         ; *2048
    ; HL = A * 2048, BC = A * 4 -> result = HL - BC
    ; subtract 16-bit: invert BC and add 1 then add
    ld a, l
    sub c
    ld l, a
    ld a, h
    sbc b
    ld h, a
    ; HL now = A * 2044
    ld bc, SLOT0_ADDR
    add hl, bc
    ret


; ------------------------------------------------------------
;  IsSlotValid — Z=1 if slot magic byte is SLOT_MAGIC
;    in: A = slot index
; ------------------------------------------------------------
IsSlotValid::
    call GetSlotAddr
    ld a, [hl]
    cp SLOT_MAGIC
    ret


; ------------------------------------------------------------
;  SaveSlot — copy current song state to slot A in SRAM
;    in: A = slot index
; ------------------------------------------------------------
SaveSlot::
    push af
    call GetSlotAddr            ; HL = slot base
    pop af

    ; Magic
    ld a, SLOT_MAGIC
    ld [hl+], a
    ; Speed
    ld a, [SongSpeed]
    ld [hl+], a
    ; Order length
    ld a, [SongOrderLength]
    ld [hl+], a
    ; Reserved
    xor a
    ld [hl+], a

    ; Order list — 16 bytes
    ld de, SongOrderList
    ld b, 16
.order_loop:
    ld a, [de]
    ld [hl+], a
    inc de
    dec b
    jr nz, .order_loop

    ; Pattern data — 1024 bytes (4 patterns × 256)
    ld de, PatternData
    ld bc, ALL_PATTERN_BYTES
.pat_loop:
    ld a, [de]
    ld [hl+], a
    inc de
    dec bc
    ld a, b
    or c
    jr nz, .pat_loop
    ret


; ------------------------------------------------------------
;  LoadSlot — load slot A from SRAM into current song state
;    in:  A = slot index
;    out: Z=1 on success
; ------------------------------------------------------------
LoadSlot::
    push af
    call IsSlotValid
    pop bc
    ret nz                      ; invalid -> bail with NZ
    ld a, b
    call GetSlotAddr
    inc hl                      ; skip magic

    ; Speed
    ld a, [hl+]
    ld [SongSpeed], a
    ; Order length
    ld a, [hl+]
    ld [SongOrderLength], a
    inc hl                      ; reserved

    ; Order list
    ld de, SongOrderList
    ld b, 16
.order_loop:
    ld a, [hl+]
    ld [de], a
    inc de
    dec b
    jr nz, .order_loop

    ; Pattern data
    ld de, PatternData
    ld bc, ALL_PATTERN_BYTES
.pat_loop:
    ld a, [hl+]
    ld [de], a
    inc de
    dec bc
    ld a, b
    or c
    jr nz, .pat_loop

    ; Reset playback to start of song
    xor a
    ld [PlayerCurrentRow], a
    ld [SongOrderIndex], a
    ld a, [SongOrderList]
    ld [SongPatternNow], a

    ; Update BPM cache after speed change
    call RecomputeBpm

    xor a                       ; return Z=1
    ret


; ------------------------------------------------------------
;  ClearSlot — wipe slot A
;    in: A = slot index
; ------------------------------------------------------------
ClearSlot::
    call GetSlotAddr
    ld bc, SLOT_SIZE
.l:
    xor a
    ld [hl+], a
    dec bc
    ld a, b
    or c
    jr nz, .l
    ret


; ------------------------------------------------------------
;  SaveSystem_InstallDemo
;  Copy the ROM-resident demo song image directly into slot 1
;  (index 0).  The image is laid out exactly like a slot:
;    +0 magic, +1 speed, +2 order_len, +3 reserved,
;    +4..19 order list, +20..1043 pattern data, rest reserved.
;  We only copy the 1044 meaningful bytes; the rest is already zero
;  from the bank wipe above.
; ------------------------------------------------------------
SaveSystem_InstallDemo::
    ld a, 3                     ; slot index 3 = "Slot 4" in user terms
    call GetSlotAddr
    ld de, DemoSlotImage
    ld bc, 1044
.copy:
    ld a, [de]
    ld [hl+], a
    inc de
    dec bc
    ld a, b
    or c
    jr nz, .copy
    ret

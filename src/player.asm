; ============================================================
;  FastTracker GB — Pattern playback engine
;
;  Channel 0 -> NR1x (Pulse 1)
;  Channel 1 -> NR2x (Pulse 2)
;  Channel 2 -> NR3x (Wave)
;  Channel 3 -> NR4x (Noise)
; ============================================================

INCLUDE "hardware.inc"

DEF SONG_MAX_ORDER     EQU 16
DEF PATTERN_ROWS       EQU 32
DEF PATTERN_BYTES_ROW  EQU 8        ; 4 channels × 2 bytes
DEF PATTERN_BYTES      EQU 256      ; 32 rows × 8
DEF SONG_PATTERN_COUNT EQU 4

; ------------------------------------------------------------
;  Player state in WRAM
; ------------------------------------------------------------
SECTION "PlayerState", WRAM0[$C200]

PlayerTickCounter::  DS 1     ; counts down per VBlank; 0 -> advance row
SongSpeed::          DS 1     ; ticks per row (1..15)
PlayerCurrentRow::   DS 1     ; row index inside current pattern
SongOrderIndex::     DS 1     ; index into SongOrderList
SongOrderLength::    DS 1     ; number of valid orders
SongPatternNow::     DS 1     ; pattern currently being played

; Per-channel state (8 bytes per channel × 4 = 32 bytes)
ChannelStateBase::   DS 32

DEF CS_NOTE        EQU 0     ; current playing note (0=silent)
DEF CS_INST        EQU 1     ; current instrument
DEF CS_PERIOD_LO   EQU 2
DEF CS_PERIOD_HI   EQU 3
DEF CS_FLAGS       EQU 4
DEF CS_AGE         EQU 5
DEF CS_PAD0        EQU 6
DEF CS_PAD1        EQU 7

; ------------------------------------------------------------
;  Song data — order list & metadata (live in WRAM so the user
;  could edit it later).
; ------------------------------------------------------------
SECTION "SongData", WRAM0[$C300]

SongOrderList::      DS SONG_MAX_ORDER

; ------------------------------------------------------------
;  Pattern data — 4 patterns × 256 bytes, aligned at $C400.
; ------------------------------------------------------------
SECTION "PatternData", WRAM0[$C400]

PatternData::        DS PATTERN_BYTES * SONG_PATTERN_COUNT


; ============================================================
;  ROM-side demo song image (laid out exactly like a save slot).
;
;  Cover chiptune di "Per Elisa" (Beethoven, WoO 59, 1810 —
;  pubblico dominio), arrangiamento per 4 canali GBC:
;    ch0 Pulse1 = melody       (inst 2 = Pluck50)
;    ch1 Pulse2 = counter/harmony (inst 3 = Sustain25)
;    ch2 Wave   = bass         (inst 21 = SubBass / 17 = Organ)
;    ch3 Noise  = drums leggeri quando attivi
;  Tonalità: La minore.  Tempo: Speed=8 → 7.5 row/s.  1 row = 1/16,
;  8 row per misura 2/4 → ~112 BPM (tradizionale Per Elisa).
; ============================================================
SECTION "DemoSong", ROM0

DemoSlotImage::
    ; --- Slot header (20 byte) ---
    DB $FE                      ; slot magic
    DB 8                        ; speed (~112 BPM)
    DB 6                        ; order length
    DB 0                        ; reserved
    ; Order list: 0 1 0 2 0 3 — Frase A → A+drum → A → Frase B → A → Outro
    DB 0, 1, 0, 2, 0, 3, $FF, 0, 0, 0, 0, 0, 0, 0, 0, 0

; ============================================================
;  Note hex cheatsheet (1 row = 1/16; 8 rows per misura 2/4):
;    A2=$0A  E3=$11  A3=$16  C4=$19  D4=$1B  E4=$1D
;    G#4=$21 A4=$22  B4=$24  C5=$25  D5=$27  D#5=$28  E5=$29
;
;  Per Elisa frase A (4 misure):
;    m1: E D# E D# E B D C   (sedicesime ribattute, melodia che fluttua)
;    m2: A . . [bassi C E A B] (note staccate, l'A4 risuona poi arpeggio)
;    m3: . [bassi E G# B] C . .
;    m4: . [B held] . [silenzio finale]
; ============================================================

; --- Pattern 0 — Frase A "pura" (intro classica, no drums) ---
;       ch0 = lead Pluck50 (inst 2)
;       ch1 = silent on melody rows, holds bass arpeggio on rest rows
;       ch2 = sub-bass A/E sustained (Am - E7 - Am)
;       ch3 = no drums per autenticità
DemoPattern0::
    ; m1  rows 00-07  E D# E D# E B D C
    DB $29, 2,   0, 0,  $16,21,   0, 0     ; E5 / A3 sub
    DB $28, 2,   0, 0,    0, 0,   0, 0     ; D#5
    DB $29, 2,   0, 0,    0, 0,   0, 0     ; E5
    DB $28, 2,   0, 0,    0, 0,   0, 0     ; D#5
    DB $29, 2,   0, 0,    0, 0,   0, 0     ; E5
    DB $24, 2,   0, 0,    0, 0,   0, 0     ; B4
    DB $27, 2,   0, 0,    0, 0,   0, 0     ; D5
    DB $25, 2,   0, 0,    0, 0,   0, 0     ; C5
    ; m2  rows 08-15  A held + counter arpeggio C E A B
    DB $22, 2,   0, 0,  $16,21,   0, 0     ; A4 / A3 sub
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,$19, 3,    0, 0,   0, 0     ; counter C4
    DB    0, 0,$1D, 3,    0, 0,   0, 0     ; counter E4
    DB    0, 0,$22, 3,    0, 0,   0, 0     ; counter A4
    DB $24, 2,   0, 0,    0, 0,   0, 0     ; B4 (next melody)
    DB    0, 0,  0, 0,    0, 0,   0, 0
    ; m3  rows 16-23  rest + counter E G# B, then C5
    DB    0, 0,  0, 0,  $11,21,   0, 0     ; E3 sub (E7 chord)
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,$1D, 3,    0, 0,   0, 0     ; counter E4
    DB    0, 0,$21, 3,    0, 0,   0, 0     ; counter G#4
    DB    0, 0,$24, 3,    0, 0,   0, 0     ; counter B4
    DB $25, 2,   0, 0,    0, 0,   0, 0     ; C5 melody
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    ; m4  rows 24-31  B held resolving, gentle close
    DB $24, 2,   0, 0,  $16,21,   0, 0     ; B4 / back to A3 sub
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0

; --- Pattern 1 — Frase A con drum kit leggero ("pump up") ---
;     Stessa melodia di P0, con kick on beat 1 di ogni misura e
;     snare on beat 2, hi-hat sui sedicesimi "off".
DemoPattern1::
    ; m1
    DB $29, 2,   0, 0,  $16,21,   1, 1     ; E5 + kick
    DB $28, 2,   0, 0,    0, 0,   1, 3     ; D#5 + hat
    DB $29, 2,   0, 0,    0, 0,   0, 0
    DB $28, 2,   0, 0,    0, 0,   1, 3
    DB $29, 2,   0, 0,    0, 0,   1, 2     ; snare on beat 2
    DB $24, 2,   0, 0,    0, 0,   1, 3
    DB $27, 2,   0, 0,    0, 0,   0, 0
    DB $25, 2,   0, 0,    0, 0,   1, 3
    ; m2
    DB $22, 2,   0, 0,  $16,21,   1, 1     ; A4 + kick
    DB    0, 0,  0, 0,    0, 0,   1, 3
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,$19, 3,    0, 0,   1, 3
    DB    0, 0,$1D, 3,    0, 0,   1, 2     ; counter E4 + snare
    DB    0, 0,$22, 3,    0, 0,   1, 3
    DB $24, 2,   0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   1, 3
    ; m3
    DB    0, 0,  0, 0,  $11,21,   1, 1     ; E3 + kick
    DB    0, 0,  0, 0,    0, 0,   1, 3
    DB    0, 0,$1D, 3,    0, 0,   0, 0
    DB    0, 0,$21, 3,    0, 0,   1, 3
    DB    0, 0,$24, 3,    0, 0,   1, 2
    DB $25, 2,   0, 0,    0, 0,   1, 3
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   1, 3
    ; m4
    DB $24, 2,   0, 0,  $16,21,   1, 1     ; B4 + kick
    DB    0, 0,  0, 0,    0, 0,   1, 3
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   1, 3
    DB    0, 0,  0, 0,    0, 0,   1, 2
    DB    0, 0,  0, 0,    0, 0,   1, 3
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   1, 5     ; crash transition

; --- Pattern 2 — Frase B (sezione brillante, do maggiore) ---
;       Per Elisa parte centrale: C D D# D C A G F E D E5
;       ch2 = organ bass (inst 17), drums più rilassati
DemoPattern2::
    ; m1  C D D#  - up
    DB $25, 2,   0, 0,  $19,17,   1, 1     ; C5 / C4 organ / kick
    DB    0, 0,  0, 0,    0, 0,   1, 3
    DB $27, 2,   0, 0,    0, 0,   0, 0     ; D5
    DB    0, 0,  0, 0,    0, 0,   1, 3
    DB $28, 2,   0, 0,    0, 0,   1, 8     ; D#5 + clap
    DB $27, 2,   0, 0,    0, 0,   0, 0     ; D5
    DB $25, 2,   0, 0,    0, 0,   0, 0     ; C5
    DB $22, 2,   0, 0,    0, 0,   1, 3
    ; m2  A G F E - down
    DB    0, 0,  0, 0,  $16,17,   1, 1     ; A3 organ / kick
    DB    0, 0,  0, 0,    0, 0,   1, 3
    DB $20, 2,   0, 0,    0, 0,   0, 0     ; G4
    DB    0, 0,  0, 0,    0, 0,   1, 3
    DB $1E, 2,   0, 0,    0, 0,   1, 8     ; F4 + clap
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB $1D, 2,   0, 0,    0, 0,   0, 0     ; E4
    DB    0, 0,  0, 0,    0, 0,   1, 3
    ; m3  return to frase A
    DB $29, 2,   0, 0,  $11,17,   1, 1     ; E5 + kick (E7 area)
    DB $28, 2,   0, 0,    0, 0,   1, 3     ; D#5
    DB $29, 2,   0, 0,    0, 0,   0, 0
    DB $28, 2,   0, 0,    0, 0,   1, 3
    DB $29, 2,   0, 0,    0, 0,   1, 8     ; clap
    DB $24, 2,   0, 0,    0, 0,   0, 0     ; B4
    DB $27, 2,   0, 0,    0, 0,   0, 0     ; D5
    DB $25, 2,   0, 0,    0, 0,   1, 3
    ; m4  resolution
    DB $22, 2,   0, 0,  $16,17,   1, 1     ; A4 / A3 / kick
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,$19, 3,    0, 0,   1, 3
    DB    0, 0,$1D, 3,    0, 0,   0, 0
    DB    0, 0,$22, 3,    0, 0,   1, 8
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   1, 3

; --- Pattern 3 — Outro: cadenza finale Am ---
;     Lascia respirare la chiusura: A4 / E4 / A4 arpeggio in arco
;     + ultimo crash su fine.
DemoPattern3::
    ; m1  Arpeggio A minor finale: A C E A . . . .
    DB $22, 2,   0, 0,  $16,21,   1, 1     ; A4 / A3 / Kick
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB $25, 2,   0, 0,    0, 0,   0, 0     ; C5
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB $29, 2,   0, 0,    0, 0,   0, 0     ; E5
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB $2E, 2,   0, 0,    0, 0,   0, 0     ; A5 high
    DB    0, 0,  0, 0,    0, 0,   0, 0
    ; m2  hold A5 con counter ad arpeggio
    DB    0, 0,$19, 3,  $16,21,   0, 0     ; counter C4
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,$1D, 3,    0, 0,   0, 0     ; E4
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,$22, 3,    0, 0,   0, 0     ; A4
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,$25, 3,    0, 0,   0, 0     ; C5
    DB    0, 0,  0, 0,    0, 0,   0, 0
    ; m3  ultima frase: E D# E D# E B D C
    DB $29, 2,   0, 0,  $16,21,   1, 1
    DB $28, 2,   0, 0,    0, 0,   0, 0
    DB $29, 2,   0, 0,    0, 0,   0, 0
    DB $28, 2,   0, 0,    0, 0,   0, 0
    DB $29, 2,   0, 0,    0, 0,   0, 0
    DB $24, 2,   0, 0,    0, 0,   0, 0
    DB $27, 2,   0, 0,    0, 0,   0, 0
    DB $25, 2,   0, 0,    0, 0,   0, 0
    ; m4  cadenza finale A held + crash
    DB $22, 2,   0, 0,  $16,21,   1, 1     ; A4 final / A3 / kick
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   1, 5     ; CRASH
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB    0, 0,  0, 0,    0, 0,   0, 0
    DB $FD, 0,$FD, 0,  $FD, 0,   0, 0     ; note-off finale
DemoSlotImage_End::



; ============================================================
;  SongInitDefault — load the Korobeiniki demo straight from ROM
;  into WRAM at boot, so the user hears the cover immediately.
;
;  The demo also lives in SRAM slot 1 (for the Save/Load menu)
;  but we don't rely on that path — we always pre-load WRAM from
;  the ROM-resident image.
; ============================================================
SECTION "SongInit", ROM0

SongInitDefault::
    ; Copy speed from DemoSlotImage[+1]
    ld a, [DemoSlotImage + 1]
    ld [SongSpeed], a
    ; Copy order length from DemoSlotImage[+2]
    ld a, [DemoSlotImage + 2]
    ld [SongOrderLength], a

    ; Copy 16-byte order list
    ld hl, DemoSlotImage + 4
    ld de, SongOrderList
    ld bc, 16
    call MemCopy_DE

    ; Copy 1024 bytes of pattern data (4 patterns × 256 byte)
    ld hl, DemoSlotImage + 20
    ld de, PatternData
    ld bc, PATTERN_BYTES * SONG_PATTERN_COUNT
    call MemCopy_DE

    ; Pre-compute BPM from speed for the status display
    call RecomputeBpm
    ret


; ------------------------------------------------------------
;  RecomputeBpm — BpmDisplay = 900 / SongSpeed (with 4 row/beat).
;  Speed=4 → 225 BPM, Speed=8 → 112 BPM, Speed=15 → 60 BPM.
;  Call after any change to SongSpeed.
; ------------------------------------------------------------
RecomputeBpm::
    ld a, [SongSpeed]
    or a
    jr z, .zero
    ld c, a                  ; C = divisor
    ld hl, 900               ; HL = dividend
    ld b, 0                  ; B = quotient (0..255)
.loop:
    ld a, h
    or a
    jr nz, .sub              ; high byte > 0 → definitely >= C
    ld a, l
    cp c
    jr c, .done              ; L < C → exit
.sub:
    ld a, l
    sub c
    ld l, a
    ld a, h
    sbc 0
    ld h, a
    inc b
    jr .loop
.done:
    ld a, b
    ld [BpmDisplay], a
    ret
.zero:
    xor a
    ld [BpmDisplay], a
    ret


; MemCopy_DE: copy BC bytes from HL to DE (counted-correct version
; that handles any BC, unlike the original main.asm MemCopy which uses
; the inc-b/inc-c trick).
MemCopy_DE::
.loop:
    ld a, [hl+]
    ld [de], a
    inc de
    dec bc
    ld a, b
    or c
    jr nz, .loop
    ret


; ============================================================
;  PatternGetRowAddr
;    in: D = pattern index (0..3), E = row index (0..31)
;    out: HL = base of 8-byte row data
;    destroys: A, B, C
; ============================================================
SECTION "PatternHelpers", ROM0

PatternGetRowAddr::
    ; HL = PatternData + D*256 + E*8
    ld h, d
    ld l, 0
    ld a, e
    add a                     ; *2
    add a                     ; *4
    add a                     ; *8
    ld c, a
    ld b, 0
    add hl, bc
    ld bc, PatternData
    add hl, bc
    ret


; ============================================================
;  PlayerInit
; ============================================================
SECTION "PlayerCode", ROM0

PlayerInit::
    ; Audio hardware on, max volume, all channels left+right
    ld a, $80
    ldh [rNR52], a
    ld a, $77
    ldh [rNR50], a
    ld a, $FF
    ldh [rNR51], a

    ; Zero channel state
    ld hl, ChannelStateBase
    ld bc, 32
    xor a
    call MemFill

    ; Mute all 4 hardware channels by zeroing their envelopes.
    xor a
    ldh [rNR12], a
    ldh [rNR22], a
    ldh [rNR32], a            ; wave volume off (NR32 actually is 0..3 shifted)
    ldh [rNR42], a
    ; Force trigger on each so envelope updates take effect
    ld a, $80
    ldh [rNR14], a
    ldh [rNR24], a
    ldh [rNR34], a
    ldh [rNR44], a

    ; Init song state
    xor a
    ld [SongOrderIndex], a
    ld [PlayerCurrentRow], a
    ld a, [SongOrderList]
    ld [SongPatternNow], a

    ld a, [SongSpeed]
    ld [PlayerTickCounter], a
    ret


; ============================================================
;  PlayerStart / PlayerStop / PlayerToggle
; ============================================================
PlayerStart::
    ld a, 1
    ld [PlayMode], a
    xor a
    ld [PlayerCurrentRow], a
    ld [SongOrderIndex], a
    ld a, [SongOrderList]
    ld [SongPatternNow], a
    ld a, 1                   ; trigger immediate row on next tick
    ld [PlayerTickCounter], a
    ret

PlayerStop::
    xor a
    ld [PlayMode], a
    call PlayerSilenceAll
    ret

PlayerToggle::
    ld a, [PlayMode]
    or a
    jr nz, .stop
    jp PlayerStart
.stop:
    jp PlayerStop


; Silence: zero all envelopes and trigger.
PlayerSilenceAll::
    xor a
    ldh [rNR12], a
    ld a, $80
    ldh [rNR14], a
    xor a
    ldh [rNR22], a
    ld a, $80
    ldh [rNR24], a
    xor a
    ldh [rNR32], a
    xor a
    ldh [rNR42], a
    ld a, $80
    ldh [rNR44], a
    ret


; ============================================================
;  PlayerTick — called once per VBlank.
; ============================================================
PlayerTick::
    ld a, [PlayMode]
    or a
    ret z                    ; not playing -> nothing to do

    ; Decrement tick counter; only process row when it hits zero
    ld hl, PlayerTickCounter
    dec [hl]
    ret nz

    ; Reset tick counter
    ld a, [SongSpeed]
    ld [PlayerTickCounter], a

    ; Process current row
    call PlayerProcessRow

    ; Advance row
    ld hl, PlayerCurrentRow
    inc [hl]
    ld a, [hl]
    cp PATTERN_ROWS
    ret c                    ; still in pattern

    ; Row wrapped -> advance order
    xor a
    ld [PlayerCurrentRow], a
    ld hl, SongOrderIndex
    inc [hl]
    ld a, [hl]
    ld c, a
    ld a, [SongOrderLength]
    cp c
    jr nz, .order_ok
    xor a
    ld [SongOrderIndex], a
    ld c, a
.order_ok:
    ld hl, SongOrderList
    ld b, 0
    add hl, bc
    ld a, [hl]
    cp $FF
    jr nz, .have_pat
    xor a
    ld [SongOrderIndex], a
    ld a, [SongOrderList]
.have_pat:
    ld [SongPatternNow], a
    ret


; ============================================================
;  PlayerProcessRow — read the 4 channels of the current row
;  and apply any new notes.
; ============================================================
PlayerProcessRow::
    ld a, [SongPatternNow]
    ld d, a
    ld a, [PlayerCurrentRow]
    ld e, a
    call PatternGetRowAddr   ; HL = row data (8 bytes)

    ; Channel 0
    ld a, [hl+]
    ld b, a                  ; note
    ld a, [hl+]
    ld c, a                  ; inst
    push hl
    ld a, 0
    call TriggerChannel
    pop hl

    ; Channel 1
    ld a, [hl+]
    ld b, a
    ld a, [hl+]
    ld c, a
    push hl
    ld a, 1
    call TriggerChannel
    pop hl

    ; Channel 2
    ld a, [hl+]
    ld b, a
    ld a, [hl+]
    ld c, a
    push hl
    ld a, 2
    call TriggerChannel
    pop hl

    ; Channel 3
    ld a, [hl+]
    ld b, a
    ld a, [hl]
    ld c, a
    ld a, 3
    call TriggerChannel
    ret


; ============================================================
;  TriggerChannel
;    in: A = channel (0..3), B = note (0=empty, $FD=off), C = inst
; ============================================================
TriggerChannel::
    ld e, a                  ; E = channel index
    ld a, b
    or a
    ret z                    ; empty -> no change
    cp $FD
    jr z, .note_off

    ; Active note — store into channel state, then dispatch.
    push bc
    ld c, e                  ; channel idx
    ; pointer to channel state = ChannelStateBase + channel*8
    ld a, c
    swap a                   ; *16
    rrca                     ; /2 -> *8
    and $F8
    ld l, a
    ld h, 0
    ld de, ChannelStateBase
    add hl, de
    pop bc

    ; HL = channel state base
    ld a, b
    ld [hl], a               ; CS_NOTE
    inc hl
    ld a, c
    ld [hl], a               ; CS_INST

    ; Dispatch by channel
    ld a, e
    or a
    jr z, .ch0
    cp 1
    jr z, .ch1
    cp 2
    jr z, .ch2
.ch3:
    jp Trigger_Noise
.ch0:
    jp Trigger_Pulse1
.ch1:
    jp Trigger_Pulse2
.ch2:
    jp Trigger_Wave

.note_off:
    ; Silence channel E
    ld a, e
    or a
    jr z, .off0
    cp 1
    jr z, .off1
    cp 2
    jr z, .off2
    ; ch3
    xor a
    ldh [rNR42], a
    ld a, $80
    ldh [rNR44], a
    ret
.off0:
    xor a
    ldh [rNR12], a
    ld a, $80
    ldh [rNR14], a
    ret
.off1:
    xor a
    ldh [rNR22], a
    ld a, $80
    ldh [rNR24], a
    ret
.off2:
    xor a
    ldh [rNR32], a
    ret


; ============================================================
;  Trigger_Pulse1 / Pulse2 / Wave / Noise
;    B = note (1..60), C = instrument (1..16, 0 = use 1)
; ============================================================

; ------------------------------------------------------------
; Pulse instrument bank — for both NR1x and NR2x.
;   Each entry = (duty_byte_for_NR11/NR21, envelope_byte_for_NR12/NR22).
;     duty bits 6-7:  00=12.5%, 01=25%, 10=50%, 11=75%
;     env: bits 4-7 = start volume, bit 3 = direction (0=down),
;          bits 0-2 = sweep step time (0 = no change).
; 16 instrument slots.
; ------------------------------------------------------------
PulseInstrTable::
    DB $80, $F0    ; 01 Sustain50  — 50% duty, full volume, no decay
    DB $80, $A2    ; 02 PianoSoft  — 50% duty, vol 10, slow decay (piano-like)
    DB $40, $90    ; 03 Soft25     — 25% duty, vol 9, sustained (background counter)
    DB $40, $A2    ; 04 Pluck25    — 25% duty, vol 10, slow decay (delicate)
    DB $00, $F0    ; 05 Sustain12  — thin
    DB $00, $F6    ; 06 Stab12     — very fast decay
    DB $C0, $F0    ; 07 Sustain75
    DB $C0, $A2    ; 08 Smooth75   — vol 10, slow decay
    DB $80, $80    ; 09 Soft50     — vol 8 sustained, very quiet
    DB $80, $F7    ; 10 Stac50     — staccato (very fast decay)
    DB $40, $C2    ; 11 PluckMid   — 25% duty, vol 12, medium decay
    DB $00, $F4    ; 12 Hit12
    DB $80, $E1    ; 13 LeadSoft   — 50% duty, vol 14, very slow decay (lead "morbido")
    DB $40, $90    ; 14 Pad25      — vol 9 sustained pad
    DB $C0, $F4    ; 15 Decay75
    DB $80, $50    ; 16 Whisper    — very quiet

Trigger_Pulse1::
    push bc
    call LookupSquarePeriod   ; in: B=note  out: DE = period (D=hi, E=lo)
    pop bc

    ld a, c
    or a
    jr nz, .inst_ok1
    ld c, 1
.inst_ok1:
    ld a, c
    dec a
    and $0F                   ; clamp to 16 instruments
    add a                     ; *2 (entries are 2 bytes)
    ld l, a
    ld h, 0
    ld bc, PulseInstrTable
    add hl, bc
    ld a, [hl+]               ; duty byte
    ldh [rNR11], a
    ld a, [hl]                ; envelope
    ldh [rNR12], a
    ld a, e
    ldh [rNR13], a
    ld a, d
    or $80
    ldh [rNR14], a
    ret


Trigger_Pulse2::
    push bc
    call LookupSquarePeriod
    pop bc

    ld a, c
    or a
    jr nz, .inst_ok2
    ld c, 1
.inst_ok2:
    ld a, c
    dec a
    and $0F
    add a
    ld l, a
    ld h, 0
    ld bc, PulseInstrTable
    add hl, bc
    ld a, [hl+]
    ldh [rNR21], a
    ld a, [hl]
    ldh [rNR22], a
    ld a, e
    ldh [rNR23], a
    ld a, d
    or $80
    ldh [rNR24], a
    ret


Trigger_Wave::
    push bc
    call LookupWavePeriod
    pop bc

    ; Disable wave channel while writing wave RAM.
    xor a
    ldh [rNR30], a

    ; Choose wave preset = (inst - 1) & 15
    ld a, c
    or a
    jr nz, .inst_okw
    ld c, 1
.inst_okw:
    ld a, c
    dec a
    and $1F                    ; 32 wave presets
    add a                      ; *2
    add a                      ; *4
    add a                      ; *8
    add a                      ; *16  (16-byte preset stride)
    ld l, a
    ld h, 0
    ld bc, WavePresetTable
    add hl, bc

    ; Copy 16 bytes from [HL] to wave RAM at $FF30..$FF3F
    ld c, $30                  ; FF30 low
    ld b, 16
.copywave:
    ld a, [hl+]
    ldh [c], a
    inc c
    dec b
    jr nz, .copywave

    ; Re-enable wave
    ld a, $80
    ldh [rNR30], a

    ; NR31 length = 0
    xor a
    ldh [rNR31], a
    ; NR32 volume = 50% ($40) — più discreto sotto la melodia
    ld a, $40
    ldh [rNR32], a
    ; NR33 = period lo
    ld a, e
    ldh [rNR33], a
    ; NR34 = trigger | period hi
    ld a, d
    or $80
    ldh [rNR34], a
    ret


; ------------------------------------------------------------
; Drum kit for the noise channel.
;   Each entry = (NR42 envelope, NR43 freq+width+divisor).
;   NR42: bits 4-7 vol, bit 3 dir (0=down), bits 0-2 sweep rate.
;   NR43: bits 4-7 shift, bit 3 width (1=metallic 7-bit), bits 0-2 divisor.
; 16 drum slots.  Instrument byte selects the drum, note value is ignored.
; ------------------------------------------------------------
DrumKitTable::
    DB $F2, $77    ; 01 Kick       — deep, short
    DB $F2, $45    ; 02 Snare      — mid white-noise
    DB $F4, $34    ; 03 ClHat      — closed hi-hat, fast decay
    DB $F1, $34    ; 04 OpHat      — open hi-hat, longer
    DB $F1, $23    ; 05 Crash      — bright, long
    DB $F3, $55    ; 06 TomHi
    DB $F3, $75    ; 07 TomLo
    DB $F4, $25    ; 08 Clap
    DB $F2, $66    ; 09 Kick2      — clickier
    DB $F2, $4D    ; 10 SnareM     — metallic snare (width=1)
    DB $F5, $30    ; 11 Tick       — very short tick
    DB $F1, $1A    ; 12 Cym        — long metallic cymbal
    DB $F3, $58    ; 13 TomMid
    DB $F2, $36    ; 14 Rim        — rim shot
    DB $F4, $7F    ; 15 Boom       — fat boom
    DB $F1, $0A    ; 16 Sizzle     — high sizzle

Trigger_Noise::
    ; C = instrument (drum index 1..16).  Note value is ignored.
    ld a, c
    or a
    jr nz, .inst_okn
    ld c, 1
.inst_okn:
    ld a, c
    dec a
    and $0F                    ; clamp to 16 drums
    add a                      ; *2 entries
    ld l, a
    ld h, 0
    ld bc, DrumKitTable
    add hl, bc
    ld a, [hl+]                ; NR42 envelope
    ldh [rNR42], a
    ld a, [hl]                 ; NR43 freq
    ldh [rNR43], a

    ; NR41 length = max
    ld a, $3F
    ldh [rNR41], a
    ; NR44 trigger
    ld a, $80
    ldh [rNR44], a
    ret


; ------------------------------------------------------------
; LookupSquarePeriod / LookupWavePeriod
;   in: B = note (1..60)
;   out: D = period hi, E = period lo
; ------------------------------------------------------------
LookupSquarePeriod::
    ld a, b
    dec a
    add a                      ; *2 (each entry is 2 bytes)
    ld l, a
    ld h, 0
    ld bc, NotePeriodsSquare
    add hl, bc
    ld a, [hl+]
    ld e, a
    ld a, [hl]
    ld d, a
    ret

LookupWavePeriod::
    ld a, b
    dec a
    add a
    ld l, a
    ld h, 0
    ld bc, NotePeriodsWave
    add hl, bc
    ld a, [hl+]
    ld e, a
    ld a, [hl]
    ld d, a
    ret


; ============================================================
;  Jam-mode note trigger (for UI live preview).
;    in: A = channel (0..3), B = note, C = inst
; ============================================================
PlayNoteNow::
    or a
    jr nz, .nc0
    jp Trigger_Pulse1
.nc0:
    cp 1
    jr nz, .nc1
    jp Trigger_Pulse2
.nc1:
    cp 2
    jr nz, .nc2
    jp Trigger_Wave
.nc2:
    jp Trigger_Noise

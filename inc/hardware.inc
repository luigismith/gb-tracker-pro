; Game Boy / Game Boy Color hardware definitions
; Subset of the standard hardware.inc — only what FastTrackerGB uses.

IF !DEF(HARDWARE_INC)
DEF HARDWARE_INC EQU 1

; ---------- Joypad ----------
DEF rP1            EQU $FF00
DEF P1F_GET_BTN    EQU %00010000
DEF P1F_GET_DPAD   EQU %00100000
DEF P1F_GET_NONE   EQU %00110000

; ---------- Serial ----------
DEF rSB            EQU $FF01
DEF rSC            EQU $FF02

; ---------- Timer ----------
DEF rDIV           EQU $FF04
DEF rTIMA          EQU $FF05
DEF rTMA           EQU $FF06
DEF rTAC           EQU $FF07

; ---------- Interrupts ----------
DEF rIF            EQU $FF0F
DEF rIE            EQU $FFFF
DEF IEF_VBLANK     EQU %00000001
DEF IEF_STAT       EQU %00000010
DEF IEF_TIMER      EQU %00000100
DEF IEF_SERIAL     EQU %00001000
DEF IEF_HILO       EQU %00010000

; ---------- Audio: square 1 ----------
DEF rNR10          EQU $FF10
DEF rNR11          EQU $FF11
DEF rNR12          EQU $FF12
DEF rNR13          EQU $FF13
DEF rNR14          EQU $FF14
; ---------- Audio: square 2 ----------
DEF rNR21          EQU $FF16
DEF rNR22          EQU $FF17
DEF rNR23          EQU $FF18
DEF rNR24          EQU $FF19
; ---------- Audio: wave ----------
DEF rNR30          EQU $FF1A
DEF rNR31          EQU $FF1B
DEF rNR32          EQU $FF1C
DEF rNR33          EQU $FF1D
DEF rNR34          EQU $FF1E
; ---------- Audio: noise ----------
DEF rNR41          EQU $FF20
DEF rNR42          EQU $FF21
DEF rNR43          EQU $FF22
DEF rNR44          EQU $FF23
; ---------- Audio: control ----------
DEF rNR50          EQU $FF24
DEF rNR51          EQU $FF25
DEF rNR52          EQU $FF26
; ---------- Audio: wave RAM ----------
DEF _AUD3WAVERAM   EQU $FF30

; ---------- LCD ----------
DEF rLCDC          EQU $FF40
DEF LCDCF_ON       EQU %10000000
DEF LCDCF_WIN9C00  EQU %01000000
DEF LCDCF_WIN9800  EQU %00000000
DEF LCDCF_WINON    EQU %00100000
DEF LCDCF_WINOFF   EQU %00000000
DEF LCDCF_BLK21    EQU %00010000
DEF LCDCF_BLK01    EQU %00000000
DEF LCDCF_BG9C00   EQU %00001000
DEF LCDCF_BG9800   EQU %00000000
DEF LCDCF_OBJ16    EQU %00000100
DEF LCDCF_OBJ8     EQU %00000000
DEF LCDCF_OBJON    EQU %00000010
DEF LCDCF_OBJOFF   EQU %00000000
DEF LCDCF_BGON     EQU %00000001

DEF rSTAT          EQU $FF41
DEF rSCY           EQU $FF42
DEF rSCX           EQU $FF43
DEF rLY            EQU $FF44
DEF rLYC           EQU $FF45
DEF rDMA           EQU $FF46
DEF rBGP           EQU $FF47
DEF rOBP0          EQU $FF48
DEF rOBP1          EQU $FF49
DEF rWY            EQU $FF4A
DEF rWX            EQU $FF4B

; ---------- CGB only ----------
DEF rKEY1          EQU $FF4D
DEF rVBK           EQU $FF4F
DEF rHDMA1         EQU $FF51
DEF rHDMA2         EQU $FF52
DEF rHDMA3         EQU $FF53
DEF rHDMA4         EQU $FF54
DEF rHDMA5         EQU $FF55
DEF rBCPS          EQU $FF68
DEF rBCPD          EQU $FF69
DEF rOCPS          EQU $FF6A
DEF rOCPD          EQU $FF6B
DEF rSVBK          EQU $FF70

ENDC

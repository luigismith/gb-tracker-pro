# Macchina Lunare 🌙

Strumento audio-visuale monocanzone su **Teensy 4.1**: contiene solo
*Chiaro di luna* separata in stem e la si manipola con un encoder, il suo
pulsante e il tasto KEY0. Regalo di compleanno — uso strettamente privato.

## Stato del progetto

| Step | Descrizione | Stato |
|------|-------------|-------|
| 0 | Probe diagnostico hardware (`step0_probe/`) | ✅ pronto da flashare |
| 1 | Motore audio (4 stem sincronizzati, mixer, LPF, granular) | in attesa esito step 0 |
| 2 | Interazione (fase lunare, modalità, play/pausa) | — |
| 3 | Visual (luna procedurale, 30 fps, framebuffer) | — |

## Step 0 — Probe diagnostico

Sketch: [`step0_probe/step0_probe.ino`](step0_probe/step0_probe.ino)

### Requisiti

- Arduino IDE con **Teensyduino** (tutte le librerie usate — Audio, SD,
  ST7735_t3, Encoder — sono incluse in Teensyduino, niente da installare)
- Scheda: *Teensy 4.1*, USB Type *Serial*, monitor seriale a 115200 baud

### Configurazione uscita audio

In cima allo sketch:

```c
#define USCITA_AUDIO_SHIELD 1   // 1 = Audio Shield SGTL5000 rev D (I2S)
                                // 0 = MQS su pin 10 (R) e 12 (L)
```

Se lo shield non risponde sull'I2C lo sketch lo segnala su Serial:
in quel caso ricompila con `0` e prova l'uscita MQS.

### Collegamenti (Teensy 4.1)

| Modulo display | Pin Teensy | Note |
|----------------|-----------|------|
| VDD | **3.3 V** | ⚠️ MAI 5 V |
| GND | GND | |
| SCL | 13 (SCK) | SPI hardware |
| SDA | 11 (MOSI) | SPI hardware, bus write-only (no MISO) |
| CS  | 9 | |
| DC  | 14 | |
| RES | 15 | |
| BLK | 5 | PWM, dimmerabile |
| TRA | 2 | encoder A (pull-up 10K + RC a bordo) |
| TRB | 3 | encoder B |
| PSH | 4 | push encoder, attivo basso |
| K0  | 22 | KEY0, attivo basso |

Nessun conflitto con l'Audio Shield: I2S su 7/8/20/21/23, I2C su 18/19,
SPI condivisa su 11/13.

### Cosa fa e cosa verificare

1. **SD** — elenca il contenuto della microSD su Serial. ✔️ Verifica che
   compaiano i file che ti aspetti.
2. **Display** — mostra barre di colore *etichettate* + bordo bianco di
   1 px. Il **push dell'encoder** cicla BLACKTAB → GREENTAB → REDTAB.
   ✔️ La variante giusta è quella in cui i colori corrispondono alle
   etichette (ROSSO è rosso, BLU è blu…) **e** il bordo è visibile su
   tutti e 4 i lati. Il nome della variante attiva è a schermo e su Serial.
3. **Encoder / KEY0** — ogni rotazione, push e pressione di K0 viene
   stampata su Serial. La rotazione regola anche la luminosità del
   backlight (test pratico del PWM).
4. **Audio** — tono di test a 440 Hz. KEY0 breve = tono on/off.
5. **Backlight** — fade PWM 0 → 100% in 2 s all'avvio; ripetibile con
   pressione lunga (2 s) di KEY0.

### Da riferire dopo il test

- [ ] SD ok? contenuto elencato correttamente?
- [ ] Quale variante ST7735 è quella giusta? (BLACKTAB / GREENTAB / REDTAB)
- [ ] Encoder: rotazione fluida, uno scatto = un evento? push ok? KEY0 ok?
- [ ] Tono 440 Hz udibile e pulito? Con quale uscita (shield o MQS)?
- [ ] Fade del backlight visibile e regolare?

Con questi esiti si parte con lo **Step 1** (motore audio a 4 stem).

/*
 * ============================================================================
 *  MACCHINA LUNARE — STEP 0: SKETCH DIAGNOSTICO ("PROBE")
 * ============================================================================
 *  Target : Teensy 4.1 (iMXRT1062) + modulo display SPI 2.0" 128x160 (ST7735)
 *           con encoder EC11 e tasto KEY0 a bordo.
 *
 *  Cosa verifica questo sketch:
 *    1. microSD onboard  -> elenca il contenuto su Serial
 *    2. Display ST7735   -> prova le varianti BLACKTAB / GREENTAB / REDTAB:
 *                           barre di colore ETICHETTATE + bordo bianco di 1px.
 *                           Si passa alla variante successiva col PUSH
 *                           dell'encoder. La variante "vincente" e' quella in
 *                           cui: i colori corrispondono alle etichette E il
 *                           bordo e' visibile su TUTTI e 4 i lati (nessun
 *                           offset di pixel).
 *    3. Encoder + KEY0   -> ogni evento (rotazione, push, K0) su Serial
 *    4. Audio            -> tono di test 440 Hz sull'uscita configurata
 *                           (vedi USCITA_AUDIO qui sotto)
 *    5. Backlight (BLK)  -> fade PWM 0 -> 100% in 2 s all'avvio;
 *                           ripetibile con pressione lunga (2 s) di KEY0.
 *
 *  Comandi a runtime:
 *    - Rotazione encoder      : stampa evento + regola la luminosita' BLK
 *    - Push encoder (PSH)     : variante ST7735 successiva
 *    - KEY0 pressione breve   : accende/spegne il tono 440 Hz
 *    - KEY0 pressione lunga 2s: ripete il test di fade del backlight
 *
 *  ATTENZIONE: il modulo display va alimentato a 3.3 V — MAI 5 V.
 * ============================================================================
 */

// ---------------------------------------------------------------------------
// CONFIGURAZIONE USCITA AUDIO
//   1 = Audio Shield SGTL5000 rev D (I2S, pin 7/8/20/21/23 + I2C 18/19)
//   0 = MQS (Medium Quality Sound) sui pin 10 (destro) e 12 (sinistro),
//       filtro RC esterno consigliato — nessuno shield richiesto.
//   Se non sai ancora quale hardware userai, prova prima con 1: se lo shield
//   non risponde lo sketch lo segnala su Serial e puoi ricompilare con 0.
// ---------------------------------------------------------------------------
#define USCITA_AUDIO_SHIELD 1

#include <Arduino.h>
#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>
#include <ST7735_t3.h>   // libreria PJRC ottimizzata (framebuffer + DMA)
#include <Encoder.h>

// ---------------------------------------------------------------------------
// PIN MAPPING (Teensy 4.1 + Audio Shield rev D — nessun conflitto:
//   I2S 7/8/20/21/23, I2C 18/19, SPI 11/13 condivisa col display)
// ---------------------------------------------------------------------------
constexpr uint8_t PIN_TFT_CS  = 9;    // chip select display
constexpr uint8_t PIN_TFT_DC  = 14;   // data/command
constexpr uint8_t PIN_TFT_RST = 15;   // reset display
constexpr uint8_t PIN_TFT_BLK = 5;    // backlight, PWM (dimmerabile)
// SCL (clock)  -> 13 = SCK  hardware  \ gestiti dalla SPI hardware,
// SDA (dati)   -> 11 = MOSI hardware  / nessun pinMode necessario
constexpr uint8_t PIN_ENC_A   = 2;    // encoder TRA (RC + pull-up a bordo)
constexpr uint8_t PIN_ENC_B   = 3;    // encoder TRB (RC + pull-up a bordo)
constexpr uint8_t PIN_ENC_PSH = 4;    // push encoder, attivo basso
constexpr uint8_t PIN_KEY0    = 22;   // tasto KEY0,   attivo basso

// ---------------------------------------------------------------------------
// OGGETTI AUDIO — sinusoide di test -> uscita scelta
// ---------------------------------------------------------------------------
AudioSynthWaveformSine ondaTest;
#if USCITA_AUDIO_SHIELD
AudioOutputI2S         uscita;
AudioControlSGTL5000   sgtl5000;
#else
AudioOutputMQS         uscita;        // pin 10 = destro, pin 12 = sinistro
#endif
AudioConnection cavo1(ondaTest, 0, uscita, 0);
AudioConnection cavo2(ondaTest, 0, uscita, 1);

// ---------------------------------------------------------------------------
// DISPLAY — SPI hardware (CS, DC, RST); MISO non usato (bus write-only)
// ---------------------------------------------------------------------------
ST7735_t3 tft(PIN_TFT_CS, PIN_TFT_DC, PIN_TFT_RST);

// Varianti ST7735 da provare in sequenza (push encoder per avanzare)
const uint8_t VARIANTI[]      = { INITR_BLACKTAB, INITR_GREENTAB, INITR_REDTAB };
const char*   NOMI_VARIANTI[] = { "BLACKTAB",     "GREENTAB",     "REDTAB"     };
constexpr uint8_t N_VARIANTI  = sizeof(VARIANTI) / sizeof(VARIANTI[0]);
uint8_t varianteAttuale = 0;

// ---------------------------------------------------------------------------
// ENCODER e PULSANTI
// ---------------------------------------------------------------------------
Encoder encoder(PIN_ENC_A, PIN_ENC_B);
long posizioneEncoder = 0;            // in scatti (detent = 4 impulsi)

// Stato pulsanti con debounce software (l'RC a bordo aiuta, ma non costa nulla)
struct Pulsante {
  uint8_t  pin;
  bool     premuto        = false;    // stato logico corrente (true = premuto)
  bool     letturaPrec    = false;
  uint32_t ultimoCambio   = 0;
  uint32_t inizioPress    = 0;
  bool     lungaGestita   = false;
};
Pulsante pulsantePush { PIN_ENC_PSH };
Pulsante pulsanteKey0 { PIN_KEY0 };
constexpr uint32_t DEBOUNCE_MS   = 25;
constexpr uint32_t PRESS_LUNGA_MS = 2000;

// Evento restituito dalla lettura di un pulsante (definito qui, prima di
// setup(), perche' l'IDE Arduino genera i prototipi prima della prima funzione)
enum class EventoPulsante { NESSUNO, PREMUTO, RILASCIATO, LUNGA };

// ---------------------------------------------------------------------------
// STATO GENERALE
// ---------------------------------------------------------------------------
int  luminositaBLK = 255;             // 0..255, regolabile con l'encoder
bool tonoAttivo    = true;

// ===========================================================================
// SETUP
// ===========================================================================
void setup() {
  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) { /* attende il monitor seriale */ }

  Serial.println();
  Serial.println("=====================================================");
  Serial.println(" MACCHINA LUNARE — STEP 0 (probe diagnostico)");
  Serial.println("=====================================================");

  // --- Pin ---------------------------------------------------------------
  pinMode(PIN_ENC_PSH, INPUT);        // pull-up 10K + RC gia' sul modulo
  pinMode(PIN_KEY0,    INPUT_PULLUP); // pull-up interno: innocuo se esterno presente
  pinMode(PIN_TFT_BLK, OUTPUT);
  analogWrite(PIN_TFT_BLK, 0);        // backlight spento: partira' col fade

  // --- 1) microSD ---------------------------------------------------------
  testSD();

  // --- 4) Audio ------------------------------------------------------------
  testAudio();

  // --- 2) Display -----------------------------------------------------------
  Serial.println();
  Serial.println("[DISPLAY] Test varianti ST7735 a 128x160.");
  Serial.println("[DISPLAY] Premi il PUSH dell'encoder per cambiare variante.");
  Serial.println("[DISPLAY] La variante giusta: colori = etichette e bordo");
  Serial.println("[DISPLAY] bianco visibile su tutti e 4 i lati.");
  applicaVariante(varianteAttuale);

  // --- 5) Backlight ----------------------------------------------------------
  testFadeBacklight();

  Serial.println();
  Serial.println("[PRONTO] Rotazione = luminosita' BLK | PUSH = variante");
  Serial.println("[PRONTO] KEY0 breve = tono on/off | KEY0 lunga 2s = fade");
  Serial.println();
}

// ===========================================================================
// LOOP
// ===========================================================================
void loop() {
  gestisciEncoder();
  gestisciPulsanti();
}

// ===========================================================================
// 1) TEST microSD — inizializza e stampa il contenuto (ricorsivo)
// ===========================================================================
void testSD() {
  Serial.println();
  Serial.println("[SD] Inizializzazione microSD onboard...");
  if (!SD.begin(BUILTIN_SDCARD)) {
    Serial.println("[SD] ERRORE: SD non trovata o non leggibile!");
    Serial.println("[SD] Controlla che la card sia inserita e in FAT32/exFAT.");
    return;
  }
  Serial.println("[SD] OK. Contenuto:");
  File radice = SD.open("/");
  stampaDirectory(radice, 0);
  radice.close();
}

void stampaDirectory(File dir, int livello) {
  while (true) {
    File voce = dir.openNextFile();
    if (!voce) break;
    for (int i = 0; i < livello; i++) Serial.print("  ");
    Serial.print("  ");
    Serial.print(voce.name());
    if (voce.isDirectory()) {
      Serial.println("/");
      stampaDirectory(voce, livello + 1);    // scende nella sottocartella
    } else {
      Serial.print("  (");
      Serial.print(voce.size());
      Serial.println(" byte)");
    }
    voce.close();
  }
}

// ===========================================================================
// 4) TEST AUDIO — tono 440 Hz sull'uscita configurata
// ===========================================================================
void testAudio() {
  Serial.println();
  AudioMemory(12);
  ondaTest.frequency(440.0f);
  ondaTest.amplitude(0.3f);           // livello prudente, niente clipping

#if USCITA_AUDIO_SHIELD
  Serial.println("[AUDIO] Uscita: Audio Shield SGTL5000 (I2S).");
  if (sgtl5000.enable()) {
    sgtl5000.volume(0.5f);
    Serial.println("[AUDIO] SGTL5000 OK — tono 440 Hz in cuffia/linea.");
  } else {
    Serial.println("[AUDIO] ERRORE: SGTL5000 non risponde su I2C!");
    Serial.println("[AUDIO] Shield assente o mal saldato. In alternativa");
    Serial.println("[AUDIO] ricompila con USCITA_AUDIO_SHIELD 0 per MQS.");
  }
#else
  Serial.println("[AUDIO] Uscita: MQS su pin 10 (R) e 12 (L).");
  Serial.println("[AUDIO] Tono 440 Hz attivo.");
#endif
}

void impostaTono(bool attivo) {
  tonoAttivo = attivo;
  ondaTest.amplitude(attivo ? 0.3f : 0.0f);
  Serial.print("[AUDIO] Tono 440 Hz: ");
  Serial.println(attivo ? "ON" : "OFF");
}

// ===========================================================================
// 2) TEST DISPLAY — applica una variante e disegna il pattern di verifica
// ===========================================================================
void applicaVariante(uint8_t indice) {
  tft.initR(VARIANTI[indice]);
  tft.setRotation(0);                 // verticale: 128 x 160
  disegnaPatternTest(NOMI_VARIANTI[indice]);
  Serial.print("[DISPLAY] Variante attiva: ");
  Serial.print(NOMI_VARIANTI[indice]);
  Serial.println("  <- se colori e bordo sono giusti, e' questa!");
}

void disegnaPatternTest(const char* nomeVariante) {
  tft.fillScreen(ST7735_BLACK);

  // Nome della variante in alto
  tft.setTextColor(ST7735_WHITE);
  tft.setTextSize(1);
  tft.setCursor(4, 4);
  tft.print("VARIANTE:");
  tft.setCursor(4, 14);
  tft.setTextSize(2);
  tft.print(nomeVariante);

  // Barre di colore etichettate: se la variante e' sbagliata tipicamente
  // ROSSO e BLU risultano scambiati, o compaiono righe di pixel spurie.
  struct Barra { uint16_t colore; const char* nome; uint16_t testo; };
  const Barra barre[] = {
    { ST7735_RED,     "ROSSO",   ST7735_WHITE },
    { ST7735_GREEN,   "VERDE",   ST7735_BLACK },
    { ST7735_BLUE,    "BLU",     ST7735_WHITE },
    { ST7735_YELLOW,  "GIALLO",  ST7735_BLACK },
    { ST7735_CYAN,    "CIANO",   ST7735_BLACK },
    { ST7735_MAGENTA, "MAGENTA", ST7735_WHITE },
    { ST7735_WHITE,   "BIANCO",  ST7735_BLACK },
  };
  constexpr int N_BARRE   = sizeof(barre) / sizeof(barre[0]);
  constexpr int Y_INIZIO  = 34;
  constexpr int ALTEZZA   = 17;
  tft.setTextSize(1);
  for (int i = 0; i < N_BARRE; i++) {
    int y = Y_INIZIO + i * ALTEZZA;
    tft.fillRect(3, y, tft.width() - 6, ALTEZZA - 2, barre[i].colore);
    tft.setTextColor(barre[i].testo);
    tft.setCursor(8, y + 4);
    tft.print(barre[i].nome);
  }

  // Bordo di 1 px sull'estremo perimetro: se manca un lato c'e' un offset
  // di pixel (variante sbagliata per questo pannello).
  tft.drawRect(0, 0, tft.width(), tft.height(), ST7735_WHITE);
}

// ===========================================================================
// 5) TEST BACKLIGHT — fade PWM 0 -> 100% in 2 secondi (bloccante, e' un test)
// ===========================================================================
void testFadeBacklight() {
  Serial.println();
  Serial.println("[BLK] Fade backlight 0 -> 100% in 2 s...");
  const uint32_t DURATA_MS = 2000;
  uint32_t inizio = millis();
  while (true) {
    uint32_t trascorso = millis() - inizio;
    if (trascorso >= DURATA_MS) break;
    analogWrite(PIN_TFT_BLK, (trascorso * 255UL) / DURATA_MS);
    delay(10);
  }
  analogWrite(PIN_TFT_BLK, luminositaBLK);
  Serial.println("[BLK] Fade completato (ora regolabile con l'encoder).");
}

// ===========================================================================
// 3) EVENTI — encoder e pulsanti su Serial
// ===========================================================================
void gestisciEncoder() {
  long pos = encoder.read() / 4;      // 4 impulsi per scatto sull'EC11
  if (pos == posizioneEncoder) return;
  int delta = pos - posizioneEncoder;
  posizioneEncoder = pos;

  // La rotazione regola anche la luminosita': test pratico del PWM su BLK
  luminositaBLK = constrain(luminositaBLK + delta * 10, 10, 255);
  analogWrite(PIN_TFT_BLK, luminositaBLK);

  Serial.print("[ENCODER] pos=");
  Serial.print(pos);
  Serial.print(delta > 0 ? "  (orario)" : "  (antiorario)");
  Serial.print("  -> luminosita' BLK ");
  Serial.print((luminositaBLK * 100) / 255);
  Serial.println("%");
}

// Legge un pulsante attivo-basso con debounce; ritorna l'evento del ciclo
EventoPulsante leggiPulsante(Pulsante& p) {
  bool lettura = (digitalRead(p.pin) == LOW);   // attivo basso
  uint32_t ora = millis();

  if (lettura != p.letturaPrec) {
    p.ultimoCambio = ora;
    p.letturaPrec  = lettura;
  }
  if (ora - p.ultimoCambio < DEBOUNCE_MS) return EventoPulsante::NESSUNO;

  if (lettura && !p.premuto) {                  // fronte di pressione
    p.premuto      = true;
    p.inizioPress  = ora;
    p.lungaGestita = false;
    return EventoPulsante::PREMUTO;
  }
  if (lettura && p.premuto && !p.lungaGestita &&
      ora - p.inizioPress >= PRESS_LUNGA_MS) {  // soglia pressione lunga
    p.lungaGestita = true;
    return EventoPulsante::LUNGA;
  }
  if (!lettura && p.premuto) {                  // fronte di rilascio
    p.premuto = false;
    return EventoPulsante::RILASCIATO;
  }
  return EventoPulsante::NESSUNO;
}

void gestisciPulsanti() {
  // --- Push dell'encoder: cambia variante display ------------------------
  switch (leggiPulsante(pulsantePush)) {
    case EventoPulsante::PREMUTO:
      Serial.println("[PUSH] premuto");
      varianteAttuale = (varianteAttuale + 1) % N_VARIANTI;
      applicaVariante(varianteAttuale);
      break;
    case EventoPulsante::RILASCIATO:
      Serial.println("[PUSH] rilasciato");
      break;
    default: break;
  }

  // --- KEY0: breve = tono on/off, lunga 2 s = ripeti fade ----------------
  switch (leggiPulsante(pulsanteKey0)) {
    case EventoPulsante::PREMUTO:
      Serial.println("[KEY0] premuto");
      break;
    case EventoPulsante::LUNGA:
      Serial.println("[KEY0] pressione lunga (2 s) -> ripeto il fade BLK");
      testFadeBacklight();
      break;
    case EventoPulsante::RILASCIATO:
      Serial.println("[KEY0] rilasciato");
      if (!pulsanteKey0.lungaGestita) impostaTono(!tonoAttivo);
      break;
    default: break;
  }
}

#!/usr/bin/env python3
"""Generate GBC wave RAM presets.

Wave RAM = 16 bytes = 32 samples × 4 bits.
High nibble of each byte is the even-indexed sample (0,2,4,...),
low nibble is the odd-indexed sample (1,3,5,...).

We package N presets back-to-back. Each preset is 16 bytes.
A small directory at the start gives the count and names.
"""

import math
import sys
from pathlib import Path


def to_wave_ram(samples):
    """samples is a list of 32 nibble values (0..15). Returns 16 bytes."""
    assert len(samples) == 32
    out = []
    for i in range(16):
        hi = samples[i * 2] & 0x0F
        lo = samples[i * 2 + 1] & 0x0F
        out.append((hi << 4) | lo)
    return out


def clip(v):
    return max(0, min(15, int(round(v))))


def sine_wave():
    return [clip(7.5 + 7.5 * math.sin(2 * math.pi * i / 32)) for i in range(32)]


def triangle_wave():
    out = []
    for i in range(32):
        if i < 16:
            out.append(clip(i))
        else:
            out.append(clip(31 - i))
    return out


def saw_wave():
    return [clip(i * 15 / 31) for i in range(32)]


def saw_down_wave():
    return [clip((31 - i) * 15 / 31) for i in range(32)]


def square_wave(duty=0.5):
    return [15 if (i / 32) < duty else 0 for i in range(32)]


def soft_square():
    # Square with slewed transitions
    out = []
    for i in range(32):
        x = (i / 32) % 1
        if x < 0.45:
            out.append(13)
        elif x < 0.5:
            out.append(clip(13 - (x - 0.45) * 260))
        elif x < 0.95:
            out.append(2)
        else:
            out.append(clip(2 + (x - 0.95) * 260))
    return out


def bell_wave():
    # Sum of a few sines — bell-ish
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = (math.sin(t) + 0.5 * math.sin(2 * t) + 0.3 * math.sin(3 * t)
             + 0.2 * math.sin(5 * t))
        # normalize approx -2..2
        out.append(clip(7.5 + 3.5 * v))
    return out


def bass_wave():
    # Pulse with a bit of body
    out = []
    for i in range(32):
        x = i / 32
        if x < 0.15:
            out.append(15)
        elif x < 0.5:
            out.append(clip(15 - (x - 0.15) * 20))
        else:
            out.append(2)
    return out


def vowel_wave():
    # Two-formant 'a' approximation
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = (math.sin(t) + 0.7 * math.sin(3 * t + 1.2)
             + 0.3 * math.sin(5 * t + 0.5))
        out.append(clip(7.5 + 3.8 * v))
    return out


def noisy_wave():
    # Deterministic pseudo-noise pattern (so output is reproducible)
    seq = [0xB,0x3,0xE,0x1,0xC,0x6,0xA,0x2,
           0xF,0x4,0x9,0x0,0xD,0x7,0x8,0x5,
           0x2,0xE,0x6,0xB,0x1,0xC,0x3,0xA,
           0x5,0x9,0x0,0xF,0x7,0xD,0x4,0x8]
    return seq


def step_wave():
    # 4-level staircase
    out = []
    for i in range(32):
        q = i // 8
        out.append([1, 5, 10, 14][q])
    return out


def hollow_wave():
    # Triangle with rounded peaks (sin-shaped)
    out = []
    for i in range(32):
        t = math.pi * i / 32
        out.append(clip(15 * abs(math.sin(t))))
    return out


def pluck_wave():
    # Karplus-strong-ish: starts noisy, settles to triangle
    base = triangle_wave()
    noise = [0,3,1,2,0,2,1,3,0,3,1,2,0,2,1,3,
             0,3,1,2,0,2,1,3,0,3,1,2,0,2,1,3]
    return [clip(b + (n - 1.5)) for b, n in zip(base, noise)]


def organ_wave():
    # Sine + odd harmonics — classic Hammond-ish tone
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = (math.sin(t) + 0.6 * math.sin(3 * t) + 0.4 * math.sin(5 * t)
             + 0.25 * math.sin(7 * t))
        out.append(clip(7.5 + 3.5 * v))
    return out


def epiano_wave():
    # Fundamental + 2nd harmonic with phase offset (FM-flavored)
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = math.sin(t + 0.5 * math.sin(2 * t))
        out.append(clip(7.5 + 6.5 * v))
    return out


def brass_wave():
    # Saw-ish with slight rounding
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = math.sin(t) + 0.5 * math.sin(2 * t) + 0.33 * math.sin(3 * t) + 0.25 * math.sin(4 * t)
        out.append(clip(7.5 + 2.8 * v))
    return out


def strings_wave():
    # Multiple slightly detuned saws blended
    out = []
    for i in range(32):
        t = i / 32
        v = ((t * 1.0) % 1) + 0.7 * ((t * 1.01) % 1) + 0.7 * ((t * 0.99) % 1)
        v /= 2.4
        out.append(clip(v * 15))
    return out


def subbass_wave():
    # Warm piano-bass body: sine + moderate 2nd + light 3rd harmonic
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = (math.sin(t) * 0.80
             + math.sin(2 * t) * 0.25
             + math.sin(3 * t) * 0.10)
        out.append(clip(7.5 + 6.5 * v))
    return out


def fm_wave():
    # 2-op FM with index 3
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = math.sin(t + 3 * math.sin(2 * t))
        out.append(clip(7.5 + 7 * v))
    return out


def glassbell_wave():
    # High-harmonic-heavy bell, very metallic
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = (math.sin(t) + 0.7 * math.sin(4 * t) + 0.6 * math.sin(7 * t))
        out.append(clip(7.5 + 2.5 * v))
    return out


def reedy_wave():
    # Square folded — clarinet/reed feel
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = math.sin(t) + math.sin(3 * t) / 3 + math.sin(5 * t) / 5 + math.sin(7 * t) / 7
        out.append(clip(7.5 + 4.5 * v))
    return out


def piano_wave():
    # Quick-decay-like piano: damped sine + bright initial harmonics
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = math.sin(t) + 0.5 * math.sin(2 * t) * math.exp(-i / 16) + 0.3 * math.sin(3 * t) * math.exp(-i / 12)
        out.append(clip(7.5 + 3.5 * v))
    return out


def synthlead_wave():
    # Saw with 5th harmonic boost — bright lead
    out = []
    for i in range(32):
        t = i / 32
        saw = (t * 2) - 1
        v = saw + 0.4 * math.sin(2 * math.pi * 5 * t)
        out.append(clip(7.5 + 6 * v))
    return out


def buzz_wave():
    # Heavily harmonic — Casio buzz
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = sum(math.sin(n * t) / n for n in range(1, 8))
        out.append(clip(7.5 + 3 * v))
    return out


def thunk_wave():
    # Filtered sine — round, warm
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = math.tanh(2 * math.sin(t))
        out.append(clip(7.5 + 7 * v))
    return out


def pwm_wave():
    # Pulse with intentional asymmetry — chip-PWM style
    out = []
    for i in range(32):
        out.append(14 if i < 11 else (3 if i < 25 else 13))
    return out


def gritty_wave():
    # Quantized sine — bitcrushed
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        raw = 7.5 + 7.5 * math.sin(t)
        out.append(clip(int(raw / 4) * 4))
    return out


def harp_wave():
    # Pluck + soft body — short, sweet
    base = pluck_wave()
    env = [1 - 0.5 * (i / 32) for i in range(32)]
    return [clip(7.5 + (b - 7.5) * e) for b, e in zip(base, env)]


def bass2_wave():
    # Sub + 3rd harm — fuller bass
    out = []
    for i in range(32):
        t = 2 * math.pi * i / 32
        v = math.sin(t) + 0.25 * math.sin(3 * t)
        out.append(clip(7.5 + 6.5 * v))
    return out


PRESETS = [
    ('Sine',     sine_wave()),
    ('Tri',      triangle_wave()),
    ('Saw',      saw_wave()),
    ('SawDown',  saw_down_wave()),
    ('Sq50',     square_wave(0.5)),
    ('Sq25',     square_wave(0.25)),
    ('Sq12',     square_wave(0.125)),
    ('SoftSq',   soft_square()),
    ('Bell',     bell_wave()),
    ('Bass',     bass_wave()),
    ('Vowel',    vowel_wave()),
    ('Noisy',    noisy_wave()),
    ('Step',     step_wave()),
    ('Hollow',   hollow_wave()),
    ('Pluck',    pluck_wave()),
    ('Solid',    [15] * 32),
    # New presets 16..31
    ('Organ',    organ_wave()),
    ('EPiano',   epiano_wave()),
    ('Brass',    brass_wave()),
    ('String',   strings_wave()),
    ('SubBas',   subbass_wave()),
    ('FM',       fm_wave()),
    ('GlsBel',   glassbell_wave()),
    ('Reed',     reedy_wave()),
    ('Piano',    piano_wave()),
    ('SynLed',   synthlead_wave()),
    ('Buzz',     buzz_wave()),
    ('Thunk',    thunk_wave()),
    ('PWM',      pwm_wave()),
    ('Gritty',   gritty_wave()),
    ('Harp',     harp_wave()),
    ('Bass2',    bass2_wave()),
]


def main():
    out_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'src/waves.asm')
    lines = []
    lines.append('; Auto-generated by tools/gen_waves.py — do not edit by hand.')
    lines.append(f'DEF WAVE_PRESET_COUNT EQU {len(PRESETS)}')
    lines.append('SECTION "WavePresets", ROM0')
    lines.append('WavePresetTable::')
    for name, samples in PRESETS:
        bs = to_wave_ram(samples)
        line = '    DB ' + ', '.join(f'${b:02X}' for b in bs) + f'  ; {name}'
        lines.append(line)
    lines.append('WavePresetTable_End::')
    lines.append('')
    lines.append('; Names of presets (4 chars + null padding to 6 bytes per entry)')
    lines.append('WavePresetNames::')
    for name, _ in PRESETS:
        padded = (name[:6] + '      ')[:6]
        chars = ', '.join(f'"{c}"' for c in padded)
        lines.append(f'    DB {chars}')
    out_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Wrote {out_path} ({len(PRESETS)} presets)')


if __name__ == '__main__':
    main()

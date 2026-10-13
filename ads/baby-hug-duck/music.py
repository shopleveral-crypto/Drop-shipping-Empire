"""Original, royalty-free music bed + SFX for the ad, synthesized from scratch.

Warm ukulele-pop at 96 BPM (plucked strings via Karplus-Strong, glockenspiel,
soft kick, snaps, shaker). The arrangement is 7 bars plus a final resolved
chord, so cuts in the edit land on the beat grid.

Usage: python3 music.py <timeline.json> <out_music.wav> <out_sfx.wav>
"""
import json
import sys

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
rng = np.random.default_rng(7)


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pluck(freq, dur, vel=1.0, bright=0.6, decay=0.9965):
    """Karplus-Strong plucked string, vectorized through lfilter."""
    n = int(dur * SR)
    period = max(2, int(round(SR / freq - 0.5)))
    burst = rng.uniform(-1, 1, period)
    b, a = butter(1, 1500 + 6000 * bright, fs=SR)
    burst = lfilter(b, a, burst)
    x = np.zeros(n)
    x[:period] = burst
    den = np.zeros(period + 2)
    den[0] = 1.0
    den[period] = -decay / 2
    den[period + 1] = -decay / 2
    y = lfilter([1.0], den, x)
    y *= np.exp(-np.arange(n) / SR * 1.6)
    return vel * y / (np.max(np.abs(y)) + 1e-9)


def glock(freq, dur=1.6, vel=1.0):
    t = np.arange(int(dur * SR)) / SR
    partials = [(1, 1.0, 3.0), (2.76, 0.35, 7.0), (5.40, 0.15, 12.0), (8.93, 0.06, 18.0)]
    y = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t * d) for r, a, d in partials)
    y *= np.minimum(1, t / 0.002)
    return vel * y / 1.5


def bass(freq, dur=0.5, vel=1.0):
    t = np.arange(int(dur * SR)) / SR
    y = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    y *= np.exp(-t * 5) * np.minimum(1, t / 0.006)
    return vel * np.tanh(1.5 * y) / 1.2


def kick(vel=1.0):
    t = np.arange(int(0.35 * SR)) / SR
    f = 48 + 95 * np.exp(-t * 32)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)
    return vel * y


def snap(vel=1.0):
    t = np.arange(int(0.18 * SR)) / SR
    sos = butter(2, [1400, 5200], btype="band", fs=SR, output="sos")
    y = sosfilt(sos, rng.uniform(-1, 1, len(t))) * np.exp(-t * 38)
    return vel * y / (np.max(np.abs(y)) + 1e-9)


def shaker(vel=1.0):
    t = np.arange(int(0.07 * SR)) / SR
    sos = butter(2, 6500, btype="high", fs=SR, output="sos")
    y = sosfilt(sos, rng.uniform(-1, 1, len(t)))
    y *= np.minimum(1, t / 0.012) * np.exp(-t * 60)
    return vel * y / (np.max(np.abs(y)) + 1e-9)


def reverb_ir(seconds=1.3, seed=0):
    r = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    ir = r.uniform(-1, 1, len(t)) * np.exp(-t * 4.2)
    sos = butter(1, 5000, fs=SR, output="sos")
    return sosfilt(sos, ir) * 0.08


class Track:
    def __init__(self, dur):
        self.buf = np.zeros(int(dur * SR) + SR * 2)

    def add(self, sig, at, gain=1.0):
        i = int(at * SR)
        j = min(len(self.buf), i + len(sig))
        self.buf[i:j] += gain * sig[: j - i]


# Ukulele (GCEA) voicings, strings listed G-C-E-A.
CHORDS = {
    "C": [67, 60, 64, 72],
    "G": [67, 62, 67, 71],
    "Am": [69, 60, 64, 69],
    "F": [69, 60, 65, 69],
}
ROOT = {"C": 48, "G": 43, "Am": 45, "F": 41}
PROGRESSION = ["C", "G", "Am", "F", "C", "F", "G"]
# Glockenspiel melody per bar: (beat offset, midi note).
MELODY = [
    [(0, 76), (1, 79), (2, 84), (3, 79), (3.5, 76)],
    [(0, 74), (1, 79), (2, 83), (3, 86)],
    [(0, 84), (1, 83), (2, 81), (2.5, 79), (3, 76)],
    [(0, 77), (1, 81), (2, 84), (3, 81)],
    [(0, 88), (1, 86), (2, 84), (3, 79), (3.5, 81)],
    [(0, 81), (1, 84), (2, 89), (3, 88)],
    [(0, 86), (1, 83), (2, 79), (2.5, 83), (3, 86), (3.5, 88)],
]
STRUM = [(0, "D", 1.0), (1, "D", 0.8), (1.5, "U", 0.55), (2.5, "U", 0.6), (3, "D", 0.85), (3.5, "U", 0.5)]


def strum(trk, chord, at, direction, vel):
    notes = CHORDS[chord] if direction == "D" else CHORDS[chord][::-1][:3]
    for k, m in enumerate(notes):
        trk.add(pluck(midi_hz(m), 1.4, vel * (0.9 + 0.1 * rng.random()), bright=0.45 + 0.2 * vel), at + k * 0.011)


def build_music(bpm, total):
    beat = 60.0 / bpm
    bar = 4 * beat
    uke, gl, drums, low = Track(total), Track(total), Track(total), Track(total)
    for b, chord in enumerate(PROGRESSION):
        t0 = b * bar
        lift = 1.0 if b >= 4 else 0.85
        for off, d, v in STRUM:
            strum(uke, chord, t0 + off * beat + rng.normal(0, 0.004), d, v * lift)
        for off, m in MELODY[b]:
            gl.add(glock(midi_hz(m), vel=0.8 if off % 1 else 1.0), t0 + off * beat)
        for off in (0, 2):
            drums.add(kick(0.9 if b else 0.7), t0 + off * beat)
            low.add(bass(midi_hz(ROOT[chord]), 0.55, 0.9), t0 + off * beat)
        low.add(bass(midi_hz(ROOT[chord] + 7), 0.3, 0.6), t0 + 3.5 * beat)
        for off in (1, 3):
            drums.add(snap(0.55), t0 + off * beat + 0.005)
        if b >= 2:
            for e in range(8):
                drums.add(shaker(0.18 if e % 2 else 0.1), t0 + e * beat / 2)
    # Final resolved chord + sparkle arpeggio.
    tf = len(PROGRESSION) * bar
    strum(uke, "C", tf, "D", 1.0)
    for m in (60, 64, 67):
        uke.add(pluck(midi_hz(m), 1.8, 0.6, 0.5), tf + 0.02)
    for k, m in enumerate((84, 88, 91, 96)):
        gl.add(glock(midi_hz(m), 2.0, 0.9), tf + k * beat / 4)
    drums.add(kick(1.0), tf)
    low.add(bass(midi_hz(36), 1.4, 1.0), tf)

    dry = 0.55 * uke.buf + 0.32 * gl.buf + 0.55 * drums.buf + 0.5 * low.buf
    wet_src = 0.55 * uke.buf + 0.4 * gl.buf + 0.15 * drums.buf
    left = dry + fftconvolve(wet_src, reverb_ir(seed=1))[: len(dry)] + 0.04 * gl.buf
    right = dry + fftconvolve(wet_src, reverb_ir(seed=2))[: len(dry)] - 0.04 * gl.buf
    stereo = np.stack([left, right], axis=1)[: int(total * SR)]
    # Short fade at the very end so the ring-out closes cleanly.
    fade = int(0.6 * SR)
    stereo[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
    stereo = np.tanh(1.3 * stereo / (np.max(np.abs(stereo)) + 1e-9)) / np.tanh(1.3)
    return stereo * 0.89


def whoosh(dur=0.42):
    t = np.arange(int(dur * SR)) / SR
    noise = rng.uniform(-1, 1, len(t))
    # Rising band-pass sweep built from short filtered blocks.
    out = np.zeros_like(noise)
    blk = 256
    zi = np.zeros((2, 2))
    for i in range(0, len(t), blk):
        f = 400 + 5000 * (i / len(t)) ** 1.6
        sos = butter(2, [f * 0.7, min(f * 1.5, SR / 2 - 100)], btype="band", fs=SR, output="sos")
        out[i : i + blk], zi = sosfilt(sos, noise[i : i + blk], zi=zi)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    env *= np.where(t > dur * 0.7, np.exp(-(t - dur * 0.7) * 12), 1)
    y = out * env
    return y / (np.max(np.abs(y)) + 1e-9)


def pop():
    t = np.arange(int(0.12 * SR)) / SR
    f = 520 + 900 * np.exp(-t * 45)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32) * np.minimum(1, t / 0.002)
    return y


def ding():
    t = np.arange(int(1.2 * SR)) / SR
    y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in [(1318.5, 1, 3.5), (1975.5, 0.6, 4.5), (2637, 0.25, 7)])
    return y * np.minimum(1, t / 0.003) / 1.6


def build_sfx(tl, total):
    trk = Track(total)
    for c in tl["cuts"]:
        trk.add(whoosh(), max(0.0, c - 0.3), 0.32)
    for t in tl["sfx_pops"]:
        trk.add(pop(), t, 0.22)
    trk.add(ding(), tl["sfx_ding"], 0.28)
    mono = trk.buf[: int(total * SR)]
    return np.stack([mono, mono], axis=1)


def write_wav(path, stereo):
    import wave

    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    tl = json.load(open(sys.argv[1], encoding="utf-8"))
    total = tl["duration"]
    write_wav(sys.argv[2], build_music(tl["bpm"], total))
    write_wav(sys.argv[3], build_sfx(tl, total))

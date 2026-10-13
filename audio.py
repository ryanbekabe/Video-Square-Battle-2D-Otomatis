"""Sintesis efek suara dan musik latar untuk Square Battle (tanpa file aset)."""
import math
import random
import wave
from array import array

RATE = 44100
TAU = 2 * math.pi


def _hit(rng):
    dur = 0.14
    base = rng.uniform(150, 260)
    out = array("f")
    phase = 0.0
    for i in range(int(dur * RATE)):
        t = i / RATE
        phase += TAU * base * (1 - t * 3) / RATE
        env = math.exp(-t * 32)
        out.append((math.sin(phase) * 0.8 + rng.uniform(-1, 1) * 0.45) * env)
    return out


def _elimination():
    dur = 0.6
    out = array("f")
    phase = 0.0
    for i in range(int(dur * RATE)):
        t = i / RATE
        freq = 620 * (1 - t / dur) + 110 * (t / dur)
        phase += TAU * freq / RATE
        square = 1.0 if math.sin(phase) >= 0 else -1.0
        out.append(square * 0.35 * math.exp(-t * 3.5))
    return out


def _pickup():
    dur = 0.22
    out = array("f")
    phase = 0.0
    for i in range(int(dur * RATE)):
        t = i / RATE
        phase += TAU * (700 + 2600 * t) / RATE
        out.append(math.sin(phase) * 0.4 * math.exp(-t * 9))
    return out


def _victory():
    notes = [523.25, 659.25, 783.99, 1046.5]  # C5 E5 G5 C6
    dur = 1.8
    out = array("f", [0.0]) * int(dur * RATE)
    for k, freq in enumerate(notes):
        start = int(k * 0.12 * RATE)
        for i in range(start, len(out)):
            t = (i - start) / RATE
            env = min(t * 80, 1.0) * math.exp(-t * 1.8)
            out[i] += (math.sin(TAU * freq * t) + 0.3 * math.sin(TAU * freq * 2 * t)) * env * 0.22
    return out


def _music_loop():
    """Loop 4 birama (8 detik, 120 BPM): kick, hi-hat, dan bass."""
    beat = 0.5
    bass_notes = [110.0, 87.31, 130.81, 98.0]  # A2 F2 C3 G2
    out = array("f", [0.0]) * int(16 * beat * RATE)
    hat_rng = random.Random(7)
    for b in range(16):
        start = int(b * beat * RATE)
        bass = bass_notes[b // 4]
        for i in range(int(beat * RATE)):
            t = i / RATE
            kick = math.sin(TAU * (55 + 90 * math.exp(-t * 30)) * t) * math.exp(-t * 12) * 0.6
            bass_v = math.sin(TAU * bass * t) * 0.25 * math.exp(-t * 2.5)
            ht = t - beat / 2
            hat = hat_rng.uniform(-1, 1) * math.exp(-ht * 60) * 0.12 if ht >= 0 else 0.0
            out[start + i] += kick + bass_v + hat
    return out


def _add(buf, clip, start, gain=1.0):
    end = min(len(buf), start + len(clip))
    for i in range(start, end):
        buf[i] += clip[i - start] * gain


def build_soundtrack(path, events, fps, total_frames, seed=0, music_gain=0.35):
    """Tulis file WAV sepanjang video berdasarkan daftar event (jenis, frame)."""
    rng = random.Random(seed)
    n = int(total_frames / fps * RATE)
    loop = _music_loop()
    buf = (loop * (n // len(loop) + 1))[:n]
    for i in range(n):
        buf[i] *= music_gain
    fade = min(n, RATE)
    for i in range(fade):
        buf[n - fade + i] *= 1 - i / fade

    hits = [_hit(rng) for _ in range(6)]
    elim, win, pickup = _elimination(), _victory(), _pickup()
    for kind, frame in events:
        start = int(frame / fps * RATE)
        if kind == "hit":
            _add(buf, rng.choice(hits), start, 0.7)
        elif kind == "elim":
            _add(buf, elim, start)
        elif kind == "win":
            _add(buf, win, start)
        elif kind == "pickup":
            _add(buf, pickup, start)

    pcm = array("h", (int(max(-1.0, min(1.0, v * 0.8)) * 32767) for v in buf))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())

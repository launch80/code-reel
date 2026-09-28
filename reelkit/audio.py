"""audio — the soundtrack, derived from the compiled timeline's events.

Score presets (style pack picks one; timeline "audio": {"preset": ...} overrides):
  pulse      kick/hat/sub groove, pad, risers into glitch cuts   (dark tech)
  ambient    no drums: evolving pad, sparse plucks, swells       (editorial)
  minimal    woodblock clicks, marimba arps, sine bass           (swiss)
  glitch     crushed kick, stutter hats, square bass, bleeps     (terminal)
  lofi       swung hats, soft kick/snare, warm 7th chords, crackle (soft/storybook)
  cinematic  drone, string swells, taiko hits, boom             (blueprint)

Every picture event gets a sound: cut transitions (riser+impact / whoosh / swell),
slams, typing clicks, counter ticks, the end bell. Deterministic: all noise is
seeded from the timeline seed. A licensed music track can replace the score:
  "audio": {"track": "assets/music.mp3", "gain_db": -3, "sfx": true}
"""
import json
import os
import subprocess

import numpy as np

SR = 48000
NOTES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _lp(x, fc):
    try:
        from scipy.signal import butter, lfilter
        b, a = butter(2, min(0.99, fc / (SR / 2)), btype="low")
        return lfilter(b, a, x)
    except ImportError:
        a = np.exp(-2 * np.pi * fc / SR)
        y = np.zeros_like(x)
        s = 0.0
        for i in range(len(x)):
            s = (1 - a) * x[i] + a * s
            y[i] = s
        return y


def _hp(x, fc):
    return x - _lp(x, fc)


class Mix:
    def __init__(self, dur, seed):
        self.N = int(dur * SR) + SR // 10
        self.dur = dur
        self.bus = {k: np.zeros(self.N) for k in ("music", "drums", "sfx")}
        self.r = np.random.default_rng(int(seed) & 0xFFFFFFFF)

    def noise(self, n):
        return self.r.standard_normal(n)

    def add(self, bus, sig, t, g=1.0):
        i = int(round(t * SR))
        if i < 0:
            sig = sig[-i:]
            i = 0
        j = min(self.N, i + len(sig))
        if j > i:
            self.bus[bus][i:j] += sig[: j - i] * g


def env(n, a=0.005, d=0.2, curve=6.0):
    t = np.arange(n) / SR
    e = np.exp(-t / max(d, 1e-4) * (curve / 6.0) * 1.0)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def tone(f, dur, kind="sine", det=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * f * (1 + det) * t
    if kind == "sine":
        return np.sin(ph)
    if kind == "saw":
        return 2 * ((f * (1 + det) * t) % 1) - 1
    if kind == "square":
        return np.sign(np.sin(ph))
    if kind == "tri":
        return 2 * np.abs(2 * ((f * t) % 1) - 1) - 1
    raise ValueError(kind)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


# ------------------------------------------------------------------ instruments
def kick(m, crush=False):
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 26) + 42
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.28)
    if crush:
        s = np.round(s * 6) / 6
    return np.tanh(1.8 * s)


def snare(m):
    n = int(0.25 * SR)
    return (_hp(m.noise(n), 1500) * env(n, 0.001, 0.09) * 0.7 + tone(190, 0.25) * env(n, 0.001, 0.06) * 0.5)


def hat(m, dur=0.05):
    n = int(dur * SR)
    return _hp(m.noise(n), 7000) * env(n, 0.0005, dur / 3)


def click(m):
    n = int(0.018 * SR)
    return _hp(m.noise(n), 2000) * env(n, 0.0003, 0.004)


def wood(m, f=1800):
    n = int(0.08 * SR)
    return (tone(f, 0.08) * 0.6 + _hp(m.noise(n), 3000) * 0.2) * env(n, 0.0005, 0.018)


def pluck(f, dur=0.8, bright=4):
    n = int(dur * SR)
    s = sum(tone(f * h, dur) / h ** 1.3 * np.exp(-np.arange(n) / SR * (3 + h * bright)) for h in range(1, 6))
    return s * env(n, 0.002, dur)


def pad(freqs, dur, bright=900, det=0.004, a=0.6):
    n = int(dur * SR)
    s = np.zeros(n)
    for f in freqs:
        for dd in (-det, det):
            s += tone(f, dur, "saw", dd)
    s = _lp(s / (2 * len(freqs)), bright)
    e = np.minimum(1, np.arange(n) / (a * SR)) * np.minimum(1, (n - np.arange(n)) / (0.3 * SR))
    return s * e


def riser(m, dur, lo=200, hi=900):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(lo + (hi - lo) * (t / dur) ** 2) / SR) * 0.14 * (t / dur)
    return s + _hp(m.noise(n), 800 + 4000 * float(dur)) * 0.06 * (t / dur) ** 2


def impact(m, g=1.0, low=55):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(low + 50 * np.exp(-t * 18)) / SR) * env(n, 0.002, 0.35)
    return np.tanh(1.4 * (body + _lp(m.noise(n), 3000) * 0.4 * env(n, 0.001, 0.08))) * g


def whoosh(m, dur=0.45):
    n = int(dur * SR)
    t = np.arange(n) / SR
    shape = np.sin(np.pi * t / dur) ** 2
    s = _lp(m.noise(n), 2500) * shape
    return s * 0.5


def swell(m, dur=0.8, f=440):
    n = int(dur * SR)
    t = np.arange(n) / SR
    shape = (t / dur) ** 2 * np.exp(-(t / dur - 1) ** 2 * 3)
    return (tone(f, dur) * 0.5 + tone(f * 1.5, dur) * 0.3) * shape * 0.4 + _lp(m.noise(n), 1200) * shape * 0.15


def glitch_burst(m):
    n = int(0.18 * SR)
    s = np.sign(m.noise(n)) * env(n, 0.0005, 0.05)
    s = np.repeat(s[::40], 40)[:n]
    return s * 0.5


def bell(dur=1.4, f=880):
    n = int(dur * SR)
    return (tone(f, dur) + 0.5 * tone(f * 1.5, dur) + 0.3 * tone(f * 2.76, dur)) * 0.2 * env(n, 0.003, 0.5)


# ------------------------------------------------------------------ score
def chords(root, minor=True, seventh=False):
    q = [0, 3, 7] if minor else [0, 4, 7]
    prog = [0, 8, 3, 10] if minor else [0, 5, 9, 7]   # i-VI-III-VII  /  I-IV-vi-V
    out = []
    for p_ in prog:
        base = 48 + root + p_
        tri = [0, 3, 7] if (minor and p_ in (0,)) else ([0, 4, 7] if not minor or p_ in (8, 3, 10) else q)
        if seventh:
            tri = tri + [10 if tri[1] == 3 else 11]
        out.append([midi(base + x) for x in tri])
    return out


PRESETS = {
    "pulse": dict(drums="four", minor=True, pad=True, bright=900, plucks=False, cut="riser", sub=True),
    "ambient": dict(drums=None, minor=False, pad=True, bright=600, plucks=True, cut="swell", sub=False),
    "minimal": dict(drums="wood", minor=False, pad=False, bright=0, plucks="arp", cut="whoosh", sub=True),
    "glitch": dict(drums="glitch", minor=True, pad=False, bright=0, plucks="bleep", cut="glitch", sub=True),
    "lofi": dict(drums="lofi", minor=False, pad=True, bright=700, plucks=False, cut="swell", sub=True, seventh=True, crackle=True, swing=0.18),
    "cinematic": dict(drums="taiko", minor=True, pad=True, bright=1400, plucks=False, cut="riser", sub=False, drone=True),
}


def build(tl, out_path):
    ev = tl["events"]
    dur = tl["duration"]
    au = tl.get("audio") or {}
    preset = au.get("preset") or tl["style"].get("audio", "pulse")
    P = PRESETS.get(preset, PRESETS["pulse"])
    m = Mix(dur, tl.get("seed", 1))
    bpm = tl["bpm"]
    beat = 60.0 / bpm
    key = au.get("key") or "CDEFGAB"[int(tl.get("seed", 1)) % 7]
    root = NOTES.get(key[0].upper(), 9)
    ch = chords(root, P["minor"], P.get("seventh", False))
    cuts = ev["cuts"]
    start = cuts[0] if cuts else 0.0
    end = cuts[-1] if cuts else dur
    bar = 4 * beat
    swing = P.get("swing", 0.0)

    if not au.get("track"):
        # ---- harmony
        if P["pad"]:
            k = 0
            t = 0.0
            while t < dur:
                m.add("music", pad(ch[k % 4], bar + 0.4, P["bright"]), t, 0.35)
                t += bar
                k += 1
        if P.get("drone"):
            m.add("music", _lp(tone(midi(36 + root), dur, "saw") + tone(midi(24 + root), dur, "saw"), 300) * np.minimum(1, np.arange(int(dur * SR)) / SR / 1.5), 0, 0.25)
        # ---- rhythm between the first and last cut
        n_beats = int(round((end - start) / beat))
        for b in range(n_beats + 1):
            t = start + b * beat
            if t >= dur:
                break
            bb = b % 4
            dr = P["drums"]
            if dr == "four":
                m.add("drums", kick(m), t, 0.9)
                m.add("drums", hat(m), t + beat / 2, 0.35)
            elif dr == "glitch":
                m.add("drums", kick(m, crush=True), t, 0.85)
                for s16 in range(4):
                    if m.r.random() > 0.35:
                        m.add("drums", hat(m, 0.03), t + s16 * beat / 4, 0.25 + 0.2 * (s16 == 2))
            elif dr == "wood":
                if bb in (0, 2):
                    m.add("drums", wood(m, 1200), t, 0.5)
                m.add("drums", wood(m, 2400), t + beat / 2, 0.3)
            elif dr == "lofi":
                if bb in (0, 2):
                    m.add("drums", kick(m) * 0.7, t, 0.7)
                if bb in (1, 3):
                    m.add("drums", snare(m), t, 0.45)
                m.add("drums", hat(m), t + beat / 2 + swing * beat / 2, 0.22)
            elif dr == "taiko":
                if bb == 0:
                    m.add("drums", impact(m, 1.0, 45), t, 0.55)
            if P["sub"] and bb == 0:
                m.add("music", tone(midi(36 + root), beat * 1.5) * env(int(beat * 1.5 * SR), 0.01, beat * 0.8), t, 0.35)
            if P["plucks"] == "arp":
                chord = ch[(b // 4) % 4]
                m.add("music", pluck(chord[bb % len(chord)] * 2, 0.5, 6), t, 0.25)
                m.add("music", pluck(chord[(bb + 1) % len(chord)] * 2, 0.4, 6), t + beat / 2, 0.15)
            elif P["plucks"] == "bleep":
                if m.r.random() > 0.5:
                    m.add("music", tone(ch[(b // 4) % 4][bb % 3] * 4, 0.06, "square") * env(int(0.06 * SR), 0.001, 0.02), t + beat / 4, 0.12)
            elif P["plucks"] is True and bb == 0:
                m.add("music", pluck(ch[(b // 4) % 4][0] * 2, 1.6, 2), t, 0.3)
        if P.get("crackle"):
            n = int(dur * SR)
            cr = (m.r.random(n) > 0.9993).astype(float) * m.r.standard_normal(n)
            m.add("music", _hp(cr, 2000), 0, 0.25)

    # ---- sfx: every picture event gets a sound (also over a licensed track when sfx is on)
    if not au.get("track") or au.get("sfx", True):
        for tr in ev["transitions"]:
            c = tr["t"]
            kind = tr["type"]
            if kind == "glitch":
                m.add("sfx", riser(m, 0.9) if P["cut"] == "riser" else whoosh(m, 0.6), c - 0.9 if P["cut"] == "riser" else c - 0.6, 0.55)
                m.add("sfx", impact(m), c, 0.8)
                m.add("sfx", glitch_burst(m), c - 0.05, 0.45)
            elif kind == "flash":
                m.add("sfx", riser(m, 0.6), c - 0.6, 0.45)
                m.add("sfx", impact(m), c, 0.75)
            elif kind in ("push", "whip", "slide", "wipe", "shutter"):
                d = max(0.3, tr["dur"] + 0.1)
                m.add("sfx", whoosh(m, d), c - d / 2, 0.8 if kind == "whip" else 0.6)
            elif kind in ("dissolve", "zoom", "iris"):
                d = max(0.5, tr["dur"] + 0.3)
                m.add("sfx", swell(m, d, ch[0][2] * 2), c - d * 0.7, 0.55)
            elif kind == "cut":
                m.add("sfx", click(m), c, 0.4)
        for s in ev["slams"]:
            m.add("sfx", impact(m, 0.55, 60), s["t"], 0.55)
        for ty in ev["typing"]:
            n = max(1, int(ty["n"]))
            for k in range(n):
                m.add("sfx", click(m), ty["t"] + ty["dur"] * k / n + m.r.uniform(0, 0.004), 0.3)
        for tk in ev["ticks"]:
            k = 0
            while tk["a"] + k / 20 < tk["b"]:
                m.add("sfx", click(m), tk["a"] + k / 20, 0.18)
                k += 1
        if ev.get("bell") is not None:
            m.add("sfx", bell(1.6, ch[0][0] * 4), ev["bell"], 0.55)

    # ---- licensed track
    if au.get("track"):
        path = au["track"]
        tr = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True)
        if tr.returncode:
            raise RuntimeError("could not decode audio track %s: %s" % (path, tr.stderr.decode()[:300]))
        x = np.frombuffer(tr.stdout, dtype=np.float32).astype(np.float64)[: m.N]
        m.add("music", x, 0, 10 ** (float(au.get("gain_db", 0)) / 20))

    # ---- mix: duck music/drums under impacts, glue, fade
    duck = np.ones(m.N)
    for t in ev["impacts"]:
        i = int(t * SR)
        n = int(0.35 * SR)
        j = min(m.N, i + n)
        if j > i:
            duck[i:j] = np.minimum(duck[i:j], 0.45 + 0.55 * np.linspace(0, 1, j - i) ** 0.6)
    mix = (m.bus["music"] + m.bus["drums"]) * duck + m.bus["sfx"]
    mix = mix[: int(dur * SR)]
    fade = min(int(0.8 * SR), len(mix))
    mix[-fade:] *= np.linspace(1, 0, fade)
    fin = min(int(0.02 * SR), len(mix))
    mix[:fin] *= np.linspace(0, 1, fin)
    pk = np.abs(mix).max() or 1.0
    mix = np.tanh(mix / pk * 1.2) / np.tanh(1.2) * 0.89
    st = np.stack([mix, np.roll(mix, 23)], 1)          # a touch of width
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    import wave
    w = wave.open(out_path, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
    w.close()
    return {"preset": preset, "key": key, "seconds": round(len(mix) / SR, 3)}


def build_project(proj):
    tl = json.load(open(os.path.join(proj, ".reel", "timeline.resolved.json")))
    au = tl.get("audio") or {}
    if au.get("track") and not os.path.isabs(au["track"]):
        au["track"] = os.path.join(proj, au["track"])
        tl["audio"] = au
    out = os.path.join(proj, ".reel", "audio.wav")
    info = build(tl, out)
    return out, info

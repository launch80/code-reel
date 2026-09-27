"""Generate audio.wav from timeline.json — no hardcoded times.

Beats, kicks, hats, risers, impacts, typing clicks, counter ticks and the
closing bell are all DERIVED from the timeline (bpm, scene durations, scene
types, and each scene's slams/typing/counter params). A hand-written
audio.json in the same directory overrides the derived events entirely:
  {"beats": [...], "cuts": [...], "slams": [...], "typing": [[t, dur, n], ...],
   "ticks": [[t0, t1], ...], "bell": t}
"""
import json, os
import numpy as np
import scipy.io.wavfile as wv
from scipy.signal import butter, lfilter

from events import derive_events

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.environ.get("TIMELINE", os.path.join(HERE, "timeline.json"))))
FPS = TL.get("fps", 60)
BPM = TL.get("bpm", 120)
BP = 60.0 / BPM
D = sum(s["dur"] for s in TL["timeline"])
N = int(D * SR)
buf = np.zeros(N)

def add(sig, t, g=1.0):
    if t < 0:
        sig = sig[int(-t * SR):]
        t = 0.0
    i = int(t * SR)
    if i >= N:
        return
    j = min(N, i + len(sig))
    if j > i:
        buf[i:j] += sig[: j - i] * g

def env(n, a, d):
    e = np.exp(-np.linspace(0, 8, n) * (1.0 / max(a + d, 0.001)))
    rise = np.linspace(0, 1, max(1, int(a * SR)))
    e[: len(rise)] *= rise
    return e

def noise(n):
    return np.random.randn(n)

def sine(f, n, a=0.5):
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * a

def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 25) + 42
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.3)

def sub(f, dur):
    n = int(dur * SR)
    return sine(f, n, 0.3) * env(n, 0.02, dur * 0.5)

def hat():
    n = int(0.05 * SR)
    ns = noise(n) * env(n, 0.001, 0.05)
    b, a = butter(4, 6000 / (SR / 2), btype="high")
    return lfilter(b, a, ns)

def click():
    n = int(0.02 * SR)
    return noise(n) * env(n, 0.0005, 0.02)

def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(200 + 600 * t / dur) / SR) * 0.14 * (t / dur)
    return s + noise(n) * 0.05 * (t / dur)

def impact(dur=0.8, g=1.0):
    n = int(dur * SR)
    return (sine(55, n, 0.5) * env(n, 0.005, 0.3) + noise(n) * 0.3 * env(n, 0.002, 0.12)) * g

def bell():
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t)) * 0.12 * env(n, 0.005, 0.5)

# ---- derive events from the timeline (events.py = single source of truth) ----

ov = None
apath = os.path.join(HERE, "audio.json")
if os.path.exists(apath):
    ov = json.load(open(apath))
ev = derive_events(TL)
if ov:
    for k in ("beats", "cuts", "slams", "typing", "ticks"):
        if k in ov:
            ev[k] = ov[k]
    if "bell" in ov:
        ev["bell"] = ov["bell"]

# ---- score ----
for t in ev["beats"]:
    add(sub(55, 0.3), t, 0.2)
    add(kick(), t, 0.9)
    if t + 0.25 < D:
        add(hat(), t + 0.25, 0.4)

for t in ev["cuts"]:
    add(riser(0.9), max(0, t - 0.9), 0.5)
    add(impact(0.8), t, 0.8)
    add(sine(2000, 882, 0.12), t, 0.4)

for t in ev["slams"]:
    add(impact(0.45), t, 0.45)

for t, dur, n in ev["typing"]:
    add(sub(60, 0.2), t, 0.1)
    for k in range(int(n)):
        add(click(), t + (dur / n) * k, 0.3)

for t0, t1 in ev["ticks"]:
    for k in range(int((t1 - t0) * 20)):
        add(click(), t0 + k / 20, 0.2)

if ev.get("bell"):
    add(bell(), ev["bell"], 0.6)

# ---- amp: duck between beats, tame highs ----
clip = np.abs(buf) > 0.8
if clip.any():
    buf *= 0.85 / max(0.8, np.abs(buf).max())
b, a = butter(2, 6000 / (SR / 2), btype="low")
buf = lfilter(b, a, buf)
for k in range(0, int(D / BP), 4):
    t = k * BP
    i0, i1 = int(t * SR), int((t + 0.5) * SR)
    buf[i0:min(i1, N)] *= 0.2
fade = min(int(0.8 * SR), N)
buf[-fade:] *= np.linspace(1, 0, fade)

# ---- write wav ----
peak = np.abs(buf).max()
if peak > 0:
    buf *= 0.95 / peak
i16 = np.clip(buf * 32767, -32768, 32767).astype(np.int16)
out = os.environ.get("OUT", os.path.join(HERE, "audio.wav"))
wv.write(out, SR, i16)
print(f"wrote {out}: {len(i16) / SR:.1f}s (derived from {os.path.basename(os.environ.get('TIMELINE', 'timeline.json'))}, {len(ev['beats'])} beats, {len(ev['cuts'])} cuts, {len(ev['slams'])} slams)")

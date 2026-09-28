import hashlib
import json
import os

from conftest import reel

END = {"scene": "endcard", "dur": 2.0, "p": {"word1": "t", "word2": "", "url": "x.io"}}
Q = {"scene": "quote", "dur": 2.0, "p": {"text": "hi there", "author": "a"}}


def _h(p):
    return hashlib.sha256(open(os.path.join(p, ".reel", "audio.wav"), "rb").read()).hexdigest()


def test_deterministic_and_preset_variety(proj):
    p = proj({"timeline": [Q, dict(Q, transition="push"), dict(Q, transition="glitch"), END]})
    reel("audio", p, check=0)
    h1 = _h(p)
    reel("audio", p, check=0)
    assert _h(p) == h1, "same timeline + seed must give identical audio"
    hs = {h1}
    for preset in ("ambient", "minimal", "glitch", "lofi", "cinematic"):
        tl = json.load(open(p + "/timeline.json")); tl["audio"] = {"preset": preset}; json.dump(tl, open(p + "/timeline.json", "w"))
        reel("audio", p, check=0)
        hs.add(_h(p))
    assert len(hs) == 6


def test_bad_preset(proj):
    p = proj({"audio": {"preset": "polka"}, "timeline": [Q, END]})
    assert "audio preset 'polka'" in reel("compile", p, check=1).stdout


def test_hits_land_on_cuts(proj):
    import numpy as np
    import wave
    p = proj({"style": "swiss", "bpm": 120, "timeline": [Q, dict(Q, transition="glitch"), dict(Q, transition="cut"), END]})
    reel("audio", p, check=0)
    w = wave.open(p + "/.reel/audio.wav")
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2)[:, 0].astype(float)
    sr = w.getframerate()
    env = lambda t, win=0.03: np.abs(x[int(t * sr):int((t + win) * sr)]).mean()
    assert env(2.0) > 2 * env(1.7), "glitch cut at 2.0s should carry an impact"

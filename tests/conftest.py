"""Tests drive the SAME CLI an agent or a human runs (reel.py), so a green
suite means the real harness passes the same gates."""
import json
import os
import subprocess
import sys

import pytest

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REEL = os.path.join(SKILL, "reel.py")
sys.path.insert(0, SKILL)


def reel(*args, check=None, env=None):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run([sys.executable, REEL] + [str(a) for a in args], capture_output=True, text=True, env=e)
    if check is not None:
        assert r.returncode == check, "exit %d (want %d)\nSTDOUT:\n%s\nSTDERR:\n%s" % (r.returncode, check, r.stdout[-3000:], r.stderr[-3000:])
    return r


def make(tmp, timeline, claims=None, scenes=None):
    p = os.path.join(str(tmp), "proj")
    os.makedirs(os.path.join(p, "scenes"), exist_ok=True)
    tl = {"version": 2, "name": "TEST", "w": 1920, "h": 1080, "fps": 60, "seed": 5, "style": "signal", "hud": {"brand": "TEST"}}
    tl.update(timeline)
    json.dump(tl, open(os.path.join(p, "timeline.json"), "w"), indent=1)
    json.dump(claims or {}, open(os.path.join(p, "claims.json"), "w"), indent=1)
    for name, src in (scenes or {}).items():
        open(os.path.join(p, "scenes", name + ".js"), "w").write(src)
    return p


def resolved(p):
    return json.load(open(os.path.join(p, ".reel", "timeline.resolved.json")))


@pytest.fixture
def proj(tmp_path):
    return lambda *a, **k: make(tmp_path, *a, **k)

"""Every transition and every background/HUD/post/camera renders, audits clean, and differs."""
import hashlib
import json

import pytest

from conftest import reel, resolved

TRANS = ["cut", "glitch", "flash", "dissolve", "push", "whip", "wipe", "zoom", "iris", "shutter", "slide"]
S = lambda txt: {"scene": "statement", "dur": 2.0, "p": {"text": txt}}


def test_every_transition_renders(proj):
    tl = [S("scene zero")] + [dict(S("scene %d" % i), transition=t) for i, t in enumerate(TRANS, 1)] + [{"scene": "endcard", "dur": 2.0, "p": {"word1": "end"}}]
    p = proj({"timeline": tl})
    reel("compile", p, check=0)
    ev = resolved(p)["events"]["transitions"]
    assert [e["type"] for e in ev[:len(TRANS)]] == TRANS
    times = ",".join("%.3f" % e["t"] for e in ev if not e["self"])
    reel("stills", p, times, check=0)
    hashes = {hashlib.md5(open(p + "/.reel/stills/t%05.2f.png" % e["t"], "rb").read()).hexdigest() for e in ev if not e["self"]}
    assert len(hashes) == len([e for e in ev if not e["self"]]), "each transition should look different mid-way"


@pytest.mark.parametrize("key,values", [("bg", ["solid", "grid", "paper", "swiss", "blueprint", "mesh", "crt", "dots", "gradient", "shader"]),
                                        ("hud", ["none", "camera", "minimal", "editorial", "blueprint", "terminal"]),
                                        ("post", ["clean", "film", "paper", "crt", "print"]),
                                        ("camera", ["static", "push", "drift", "handheld", "dolly", "punch"])])
def test_look_registry(proj, key, values):
    p = proj({"timeline": [S("looks"), {"scene": "endcard", "dur": 2.0, "p": {"word1": "end"}}]})
    seen = set()
    for v in values:
        tl = json.load(open(p + "/timeline.json")); tl["style"] = {"pack": "signal", key: v}; json.dump(tl, open(p + "/timeline.json", "w"))
        r = reel("audit", p, check=0)
        assert "0 error(s)" in r.stdout, (v, r.stdout)
        at = "2.05" if key == "camera" else "1.10"      # cameras differ most right after an impact
        reel("stills", p, at, check=0)
        seen.add(hashlib.md5(open(p + "/.reel/stills/t0%s.png" % at, "rb").read()).hexdigest())
    assert len(seen) == len(values), "%s values must look different" % key

#!/usr/bin/env python3
"""Rebuild library/fingerprints.json — the novelty gate's memory.

Sources: library/sources/*.json (timelines; blueprints.json is rendered in several
style packs so a recolored blueprint is still recognized). Every final reel you
ship can be added with:  reel.py novelty <proj> --register
"""
import json
import os
import shutil
import sys
import tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL)
from reelkit import compile as K, render as R, novelty as N  # noqa: E402

STYLES_FOR_BLUEPRINTS = ["signal", "editorial", "swiss", "blueprint"]


def main():
    lib = []
    tmp = tempfile.mkdtemp()
    for f in sorted(os.listdir(os.path.join(SKILL, "library", "sources"))):
        tl = json.load(open(os.path.join(SKILL, "library", "sources", f)))
        variants = [(s, dict(tl, style=s, name="%s[%s]" % (tl.get("name", f), s))) for s in STYLES_FOR_BLUEPRINTS] if f == "blueprints.json" else [(None, tl)]
        for st, t in variants:
            p = os.path.join(tmp, f.replace(".json", "") + (("_" + st) if st else ""))
            os.makedirs(p, exist_ok=True)
            t = dict(t, policy={"beatGrid": False})
            json.dump(t, open(os.path.join(p, "timeline.json"), "w"))
            out = K.compile_project(p)
            if out["errors"]:
                print("skip", p, out["errors"][:2])
                continue
            R.audit(p)
            res = N.check(p, register=False, lib=[])
            au = json.load(open(os.path.join(p, ".reel", "audit.json")))
            lib += N.fingerprints(au, "%s#%s" % (out["name"], out["seed"]), out["style"]["pack"], out["w"], out["h"])
            print("added", p, len(lib))
    os.makedirs(os.path.dirname(N.LIB), exist_ok=True)
    json.dump(lib, open(N.LIB, "w"))
    shutil.rmtree(tmp)
    print("wrote", N.LIB, len(lib), "fingerprints")


if __name__ == "__main__":
    main()

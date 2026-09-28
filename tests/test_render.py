import hashlib
import json
import os

import pytest

from conftest import reel

END = {"scene": "endcard", "dur": 2.0, "p": {"word1": "t", "word2": "est", "url": "x.io"}}


def test_stills_every_style(proj):
    from reelkit.compile import styles
    p = proj({"timeline": [{"scene": "statement", "beats": 4, "p": {"text": "Every style renders", "emphasis": ["style"]}},
                           {"scene": "endcard", "beats": 4, "p": {"word1": "t", "word2": "est", "url": "x.io"}}]})
    for st in styles():
        tl = json.load(open(p + "/timeline.json")); tl["style"] = st; json.dump(tl, open(p + "/timeline.json", "w"))
        r = reel("audit", p, check=0)
        assert "0 error(s)" in r.stdout, (st, r.stdout)


def test_frame_determinism(proj):
    p = proj({"timeline": [{"scene": "statement", "dur": 2.0, "p": {"text": "same pixels twice"}}, END]})
    reel("stills", p, "1.23", check=0)
    a = hashlib.sha256(open(p + "/.reel/stills/t01.23.png", "rb").read()).hexdigest()
    reel("stills", p, "1.23", check=0)
    assert a == hashlib.sha256(open(p + "/.reel/stills/t01.23.png", "rb").read()).hexdigest()


OVERLAP = '''/* @meta {"name": "clash", "text": ["a", "b"]} */
defineScene("clash", (lt, d, p) => { txt(p.a, 300, 500, {f: F("sans", 80)}); txt(p.b, 320, 510, {f: F("sans", 80)}); });'''
OFFCANVAS = '''defineScene("wide", (lt, d, p) => { txt("THIS HEADLINE IS FAR TOO LONG FOR THE FRAME", 200, 500, {f: F("disp", 160)}); });'''
BLANK = '''defineScene("blank", (lt, d, p) => { txt("offscreen", -5000, -5000, {f: F("sans", 40)}); });'''
THROWS = '''defineScene("boom", (lt, d, p) => { p.nothing.here = 1; });'''


@pytest.mark.parametrize("name,src,expect", [("clash", OVERLAP, "text overlaps"), ("wide", OFFCANVAS, "off-canvas"),
                                             ("blank", BLANK, "blank"), ("boom", THROWS, "JS error")])
def test_audit_catches(proj, name, src, expect):
    p = proj({"timeline": [{"scene": name, "dur": 2.0, "p": {"a": "HELLO", "b": "WORLD"}}, END]}, scenes={name: src})
    r = reel("audit", p)
    assert r.returncode != 0 and expect in (r.stdout + r.stderr), r.stdout + r.stderr


def test_occluder_hides_text(proj):
    src = '''defineScene("card", (lt, d, p) => { txt("UNDER", 300, 500, {f: F("sans", 80)}); box(250, 400, 600, 200, {fill: "#ffffff"}); txt("ON TOP", 320, 520, {f: F("sans", 60), col: "#000"}); });'''
    p = proj({"timeline": [{"scene": "card", "dur": 2.0, "p": {}}, END]}, scenes={"card": src})
    assert "0 error(s)" in reel("audit", p, check=0).stdout


def test_vertical_blueprints(proj):
    p = proj({"w": 1080, "h": 1920, "timeline": [
        {"scene": "kinetic", "dur": 2.0, "p": {"intro": "vertical works", "words": [["ONE.", 0.5], ["TWO.", 1.0, "ACCENT", "note", "val"]]}},
        {"scene": "steps", "dur": 2.0, "p": {"title": "flow", "steps": [{"label": "a"}, {"label": "b"}, {"label": "c"}]}}, END]})
    r = reel("audit", p, check=0)
    assert "0 error(s)" in r.stdout, r.stdout

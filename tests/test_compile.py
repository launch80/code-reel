import json

from conftest import reel, resolved

END = {"scene": "endcard", "dur": 2.0, "p": {"word1": "test", "word2": "", "serif": "", "url": "", "footer": ""}}
QUOTE = {"scene": "quote", "dur": 2.0, "p": {"text": "hello world", "author": "a"}}


def test_minimal_ok(proj):
    p = proj({"timeline": [QUOTE, END]})
    reel("compile", p, check=0)
    tl = resolved(p)
    assert tl["duration"] == 4.0 and tl["style"]["pack"] == "signal"
    assert tl["events"]["cuts"] == [2.0] and tl["events"]["bell"] is not None


def test_unknown_style_and_scene(proj):
    p = proj({"style": "nope", "timeline": [{"scene": "nosuch", "dur": 2, "p": {}}, END]})
    r = reel("compile", p, check=1)
    assert "style pack 'nope'" in r.stdout and "unknown scene type" in r.stdout


def test_beat_grid(proj):
    p = proj({"timeline": [dict(QUOTE, dur=1.3), END]})
    assert "beat grid" in reel("compile", p, check=1).stdout


def test_claims_value_and_text(proj):
    claims = {"members": {"value": 2000, "source": "discord", "url": "https://x"}, "speed": {"value": 1.7, "display": "1.7×", "source": "article"}}
    p = proj({"policy": {"minCustomShare": 0}, "timeline": [{"scene": "counter", "dur": 2.0, "p": {"big": {"from": 0, "to": "@members", "fmt": "comma"}, "unit": "members", "sub": "speedup {{speed}}"}}, END]}, claims)
    reel("compile", p, "--final", check=0)
    tl = resolved(p)
    assert tl["scenes"][0]["p"]["big"]["to"] == 2000
    assert tl["scenes"][0]["p"]["sub"] == "speedup 1.7×"
    assert {u["claim"] for u in tl["claim_uses"]} == {"members", "speed"}


def test_unsourced_numbers(proj):
    p = proj({"timeline": [{"scene": "counter", "dur": 2.0, "p": {"big": {"from": 0, "to": 470}, "unit": "tok/s", "sub": "on 2 GPUs"}}, END]})
    r = reel("compile", p, check=0)
    assert r.stdout.count("unsourced number") == 2
    r = reel("compile", p, "--final", check=1)
    assert "unsourced number" in r.stdout


def test_final_requires_claim_source(proj):
    p = proj({"timeline": [QUOTE, END]}, {"x": {"value": 3}})
    assert "no source" in reel("compile", p, "--final", check=1).stdout


def test_literals_allow(proj):
    p = proj({"literals": ["2026"], "timeline": [dict(QUOTE, p={"text": "since 2026", "author": "a"}), END]})
    assert "unsourced" not in reel("compile", p, check=0).stdout


def test_seed_drives_transitions(proj, tmp_path):
    scenes = [dict(QUOTE) for _ in range(6)] + [END]
    a = proj({"seed": 1, "timeline": scenes})
    reel("compile", a, check=0)
    t1 = [x["type"] for x in resolved(a)["events"]["transitions"]]
    reel("compile", a, check=0)
    assert t1 == [x["type"] for x in resolved(a)["events"]["transitions"]], "same seed must reproduce"
    seen = {tuple(t1)}
    for s in range(2, 8):
        tl = json.load(open(a + "/timeline.json")); tl["seed"] = s; json.dump(tl, open(a + "/timeline.json", "w"))
        reel("compile", a, check=0)
        seen.add(tuple(x["type"] for x in resolved(a)["events"]["transitions"]))
    assert len(seen) > 2, "different seeds should vary the cut vocabulary"


def test_explicit_transition_and_limits(proj):
    p = proj({"timeline": [QUOTE, dict(QUOTE, transition={"type": "push", "dir": "up", "dur": 0.5}), dict(QUOTE, transition={"type": "iris", "dur": 3.0}), END]})
    r = reel("compile", p, check=1)
    assert "too long" in r.stdout
    tl = json.load(open(p + "/timeline.json")); tl["timeline"][2]["transition"] = "cut"; json.dump(tl, open(p + "/timeline.json", "w"))
    reel("compile", p, check=0)
    tr = resolved(p)["events"]["transitions"]
    assert tr[0]["type"] == "push" and tr[0]["opts"]["dir"] == "up" and tr[1]["type"] == "cut"


def test_custom_scene_meta_and_syntax(proj):
    good = '/* @meta {"name": "orbit", "required": ["items"], "slams": ["hit"]} */\ndefineScene("orbit", (lt, d, p) => { txt("x", 100, 100, {f: F("sans", 40)}); });'
    p = proj({"timeline": [{"scene": "orbit", "dur": 2.0, "p": {"hit": 1.0}}, END]}, scenes={"orbit": good})
    assert "missing required param p.items" in reel("compile", p, check=1).stdout
    tl = json.load(open(p + "/timeline.json")); tl["timeline"][0]["p"]["items"] = ["a"]; json.dump(tl, open(p + "/timeline.json", "w"))
    reel("compile", p, check=0)
    out = resolved(p)
    assert out["scenes"][0]["custom"] and 1.0 in out["events"]["impacts"]
    open(p + "/scenes/orbit.js", "w").write(good.replace("});", "}"))
    assert "syntax error" in reel("compile", p, check=1).stdout


def test_final_requires_custom_share(proj):
    p = proj({"timeline": [QUOTE, QUOTE, END]})
    assert "written for this video" in reel("compile", p, "--final", check=1).stdout


def test_builtin_name_collision(proj):
    p = proj({"timeline": [QUOTE, END]}, scenes={"q": 'defineScene("quote", () => {});'})
    assert "built-in blueprint name" in reel("compile", p, check=1).stdout

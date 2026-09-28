"""The director through its model-agnostic interface.

The fixture tests/fixtures/pi_small_core/llm is a REAL agent session (the answers
an agent wrote to the prompts reel.py produced). Replaying it with --backend mock
runs the exact prompts, gates and repair logic a local model or an agent gets —
so this suite passing means the real harness passes the same gates."""
import json
import os
import shutil

from conftest import SKILL, reel

FIX = os.path.join(SKILL, "tests", "fixtures", "pi_small_core")


def _init(tmp, seed=4242):
    p = os.path.join(str(tmp), "pi")
    reel("init", p, "--seed", seed, "--name", "pi", check=0)
    os.remove(os.path.join(p, "scenes", "opening.js"))
    shutil.copy(os.path.join(FIX, "brief.md"), os.path.join(p, "brief.md"))
    return p


def test_replay_agent_session_end_to_end(tmp_path):
    p = _init(tmp_path)
    r = reel("direct", p, "all", "--backend", "mock", "--fixtures", os.path.join(FIX, "llm"), check=0)
    assert "picked treatment 1" in r.stdout and r.stdout.count("passed gates") == 5, r.stdout
    tl = json.load(open(os.path.join(p, "timeline.json")))
    assert tl["seed"] == 4242 and {s["scene"] for s in tl["timeline"]} == {"monolith", "core_split", "tile_tally", "adapt_line", "install_end"}
    out = reel("compile", p, "--final", check=0).stdout
    assert "custom=100%" in out
    assert "0 error(s)" in reel("audit", p, check=0).stdout
    assert os.path.exists(os.path.join(p, ".reel", "treatments.png")) and os.path.exists(os.path.join(p, ".reel", "review", "tile_tally.png"))
    nv = reel("novelty", p, check=0).stdout
    assert "novelty: OK" in nv


def test_agent_backend_pauses_and_resumes(tmp_path):
    p = _init(tmp_path)
    r = reel("direct", p, "treat", "--backend", "agent")
    assert r.returncode == 10 and "treat-1.prompt.md" in r.stdout
    prompt = open(os.path.join(p, ".reel", "llm", "treat-1.prompt.md")).read()
    assert "Assignment" in prompt and "style pack" in prompt
    shutil.copy(os.path.join(FIX, "llm", "treat-1.answer.json"), os.path.join(p, ".reel", "llm"))
    r = reel("direct", p, "treat", "--backend", "agent", check=0)
    assert "wrote treatments.json (3)" in r.stdout


def test_same_prompts_for_every_backend(tmp_path):
    """agent and mock backends produce byte-identical prompt files for the same project."""
    a, b = _init(tmp_path / "a"), _init(tmp_path / "b")
    reel("direct", a, "treat", "--backend", "agent")
    reel("direct", b, "treat", "--backend", "mock", "--fixtures", os.path.join(FIX, "llm"), check=0)
    pa = open(os.path.join(a, ".reel", "llm", "treat-1.prompt.md")).read()
    pb = open(os.path.join(b, ".reel", "llm", "treat-1.prompt.md")).read()
    assert pa == pb


def test_seed_changes_the_assignment(tmp_path):
    seen = set()
    for s in (1, 2, 3, 4):
        p = _init(tmp_path / str(s), seed=s)
        reel("direct", p, "treat", "--backend", "agent")
        txt = open(os.path.join(p, ".reel", "llm", "treat-1.prompt.md")).read()
        seen.add(txt.split("## Assignment")[1].split("## Rules")[0])
    assert len(seen) >= 3, "different seeds must steer different treatments"


def test_repair_loop_fixes_a_bad_scene(tmp_path):
    fx = tmp_path / "fx"
    shutil.copytree(os.path.join(FIX, "llm"), fx)
    good = open(fx / "scene-adapt_line-1.answer.js").read()
    bad = good.replace("txt(w, x, y + (1 - a) * 30 * U", "txt(w, SAFE.l, y + (1 - a) * 30 * U")   # every word at the same x -> overlaps
    open(fx / "scene-adapt_line-1.answer.js", "w").write(bad)
    open(fx / "scene-adapt_line-2.answer.js", "w").write(good)
    p = _init(tmp_path)
    r = reel("direct", p, "all", "--backend", "mock", "--fixtures", str(fx), check=0)
    assert "scene adapt_line: 1 problem(s) -> repair 1" in r.stdout or "problem(s) -> repair 1" in r.stdout, r.stdout
    assert "scene adapt_line: passed gates (attempt 2)" in r.stdout
    rp = open(os.path.join(p, ".reel", "llm", "scene-adapt_line-2.prompt.md")).read()
    assert "text overlaps" in rp, "the repair prompt must carry the audit report"


def test_bad_treatments_are_sent_back(tmp_path):
    fx = tmp_path / "fx"
    shutil.copytree(os.path.join(FIX, "llm"), fx)
    good = json.load(open(fx / "treat-1.answer.json"))
    bad = json.loads(json.dumps(good))
    for t in bad["treatments"]:
        t["style"]["pack"] = "signal"
    json.dump(bad, open(fx / "treat-1.answer.json", "w"))
    p = _init(tmp_path)
    r = reel("direct", p, "treat", "--backend", "mock", "--fixtures", str(fx))
    assert r.returncode == 1 and "no fixture for treat-2" in r.stdout
    assert "different style packs" in open(os.path.join(p, ".reel", "llm", "treat-2.prompt.md")).read()
    json.dump(good, open(fx / "treat-2.answer.json", "w"))
    reel("direct", p, "treat", "--backend", "mock", "--fixtures", str(fx), check=0)

"""End-to-end: the exact command sequence an agent runs, on a tiny reel."""
import json
import os

from conftest import reel

SCENE = '''/* @meta {"name": "hello", "required": ["title"], "text": ["title"], "slams": ["hit"]} */
defineScene("hello", (lt, d, p) => {
  const e = M.in(prog(lt, 0, 0.6));
  circle(W / 2, H / 2, 200 * U * e, { fill: A(0.3) });
  txt(p.title, W / 2, H / 2 + 30 * U, { f: F("disp", 90 * U), col: C.cream, align: "center", a: e });
});'''


def test_run_draft_end_to_end(proj):
    p = proj({"fps": 30, "timeline": [{"scene": "hello", "dur": 1.5, "p": {"title": "{{n}} things", "hit": 0.5}},
                                      {"scene": "endcard", "dur": 1.5, "transition": "dissolve", "p": {"word1": "done", "word2": "", "url": "x.io"}}]},
             {"n": {"value": 3, "source": "test fixture"}}, scenes={"hello": SCENE})
    r = reel("run", p, "--draft", "--final", check=0)
    assert os.path.exists(os.path.join(p, "reel.mp4"))
    q = open(os.path.join(p, ".reel", "qc_report.md")).read()
    for must in ("Frame count (decoded) | PASS", "Color tags | PASS", "Integrated loudness | PASS", "Fast-start | PASS",
                 "layout audit: no overlaps / off-canvas text / blank scenes | PASS", "claims: every on-screen number sourced | PASS"):
        assert must in q, must + "\n" + q[:3000]

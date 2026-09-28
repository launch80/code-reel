import json
import os

from conftest import SKILL, reel


def test_brand_scan_maps_tokens(proj):
    p = proj({"timeline": [{"scene": "statement", "dur": 2.0, "p": {"text": "x"}}]})
    r = reel("brand", p, os.path.join(SKILL, "tests", "fixtures", "site", "index.html"), check=0)
    b = json.load(open(os.path.join(p, "brand.json")))
    pal = b["suggested_style"]["palette"]
    assert pal == {"bg": "#0d1116", "surf": "#161d27", "line": "#2a333d", "text": "#ebe7e4", "cream": "#ebe7e4",
                   "mute": "#9fa4ab", "accent": "#6a9fcc", "hot": "#8f3222"}
    assert b["suggested_style"]["fonts"] == {"mono": "DM Mono", "serif": "Instrument Serif"}
    assert "minimal terminal agent" in b["title"]

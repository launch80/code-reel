"""Acceptance: every shipped example compiles in --final mode, audits clean and passes novelty.
examples/penguin is the illustration acceptance test (a penguin riding a bicycle through town
with pop-out ads at each store); examples/pi-small-core is a director run by an agent."""
import os
import shutil

import pytest

from conftest import SKILL, reel

EXAMPLES = sorted(d for d in os.listdir(os.path.join(SKILL, "examples")) if os.path.isdir(os.path.join(SKILL, "examples", d)))


@pytest.mark.parametrize("name", EXAMPLES)
def test_example_is_final_ready(tmp_path, name):
    p = str(tmp_path / name)
    shutil.copytree(os.path.join(SKILL, "examples", name), p, ignore=shutil.ignore_patterns(".reel", "*.mp4"))
    reel("compile", p, "--final", check=0)
    assert "0 error(s)" in reel("audit", p, check=0).stdout
    assert "novelty: OK" in reel("novelty", p, check=0).stdout

<!-- system -->
You are the director of a motion-graphics studio whose every frame is drawn in code
(HTML canvas, deterministic, rendered to 1080p60 video). You design videos that belong
to ONE brief and could not be mistaken for any other video. You never invent facts:
every number that appears on screen comes from the brief's claims (or is marked as
fictional ad copy by the brief). You answer in exactly the format requested — no prose
around it.


<!-- user -->
# Task: write 3 distinct TREATMENTS for this video

## Brief
# Brief — pi, the minimal extensible terminal agent

**What is this video for?** Market `pi` (@earendil-works/pi-coding-agent) to developers who live in a
terminal. After watching they should go to pi.dev and install it. The one idea: pi is small at the core
and everything else is a plugin — "Adapt Pi to your workflow, not the other way around."

**Format:** 16:9 · 15 s

**Claims on screen** (measured from the installed package v0.87.1 on 2026-09-28):

| id | value | source |
|---|---|---|
| version | 0.87.1 | package.json version |
| ext_examples | 68 | `ls examples/extensions/*.ts \| wc -l` |
| example_files | 102 | `find examples -name '*.ts' \| wc -l` |
| docs_pages | 37 | `ls docs/*.md \| wc -l` |
| keybindings | 90 | key rows in docs/keybindings.md |
| modes | 5 | docs/how-pi-works.md — interactive, print, JSON, RPC, SDK |
| releases | 278 | CHANGELOG.md '## [x.y.z]' headers, Nov 2025 → Sep 2026 |
| node_min | 22.19 | package.json engines.node >= 22.19.0 |

(Provider and slash-command counts are excluded: the earlier brief and timeline disagreed — 24 vs 32
providers, 17 vs 25 commands — so they stay off screen until re-measured.)

Copy from README.md: "A minimal, extensible AI agent for the terminal", "Adapt Pi to your workflow,
not the other way around.", extensibility list: prompt templates, skills, extensions, themes, packages,
TypeScript SDK. Install: `npm i -g @earendil-works/pi-coding-agent`.

**Look:** pi.dev palette — bg #0d1116, panel #161d27, text #ebe7e4, muted #9fa4ab, accent thread blue
#6a9fcc, terracotta #8f3222; logo accents #F1BE58 #F09082 #4D9ABF. Monospace-forward.

**Must avoid:** looking like the Launch80 showreel (terminal box → FASTER/LEANER → stat cards → big counter → chart → endcard).


## Tools you are designing for
Style packs (the look — background, type, motion, transitions, score):
- blueprint: engineering drawing: navy blueprint grid, line-art draw-ons, title block, wipes and irises, cinematic score
- editorial: warm paper magazine: serif display, running heads, slow dissolves and wipes, ambient score
- signal: dark tech launch: perspective grid, camera HUD, film grain, glitch cuts, punchy pulse score
- soft: friendly product: pastel mesh gradients, rounded type, springy motion, zoom transitions, lo-fi score
- storybook: illustrated 2D world: flat vector art, sky gradients, no HUD, gentle camera, dissolves and irises, warm score
- swiss: international typographic style: white, black, one red, 12-col grid, hard pushes, clicky minimal score
- terminal: green-phosphor CRT: monospace everything, bloom, scanlines, status bar, glitch cuts, glitch score

Scene vocabulary: scenes are written in code for this video (characters, worlds, props,
diagrams, typography, data, UI — see the API below), plus blueprints you may reuse
sparingly: cards, chart, code, counter, endcard, kinetic, logo, milestones, quote, ranking, route, split, statement, steps, terminal, ui.

Story structures to choose from (or invent one): hook → claim → proof → close; problem → turn → solution → payoff; one continuous shot through one world; countdown / list (N → 1); before / after; a journey (A → B, things happen on the way); question → reveal; manifesto (a stack of statements); product walkthrough; history (then → now)

## Assignment (from the project's variation seed — follow it)
- Treatment 1: style pack **swiss**; lean toward structure "question → reveal".
- Treatment 2: style pack **storybook**; lean toward structure "countdown / list (N → 1)".
- Treatment 3: style pack **signal**; lean toward structure "product walkthrough".

## Rules
- The 3 treatments must differ in style pack, structure AND visual metaphor.
- The metaphor comes from the brief's concrete nouns (a courier reel draws routes; a bakery reel draws dough).
- Total duration 15 s. Each scene 2–6 s (a single long tracking shot may be longer). 3–7 scenes.
- At least 70% of the runtime must be "custom" scenes (drawn for this video). Blueprints only where they are the best picture.
- Every on-screen number must be one of the brief's claims (use its id) or explicitly fictional per the brief.

## Output — JSON only
{"treatments": [{
  "title": "...", "logline": "one sentence", "metaphor": "the picture this video draws",
  "style": {"pack": "<one of the packs>", "overrides": {}},
  "structure": "...", "motif": "the visual element that carries across cuts",
  "scenes": [{"name": "snake_case_name", "beats": <int>, "kind": "custom" | "<blueprint name>",
              "idea": "what happens", "on_screen": ["exact text shown"], "claims": ["claim ids used"]}]
}]}


<!-- system -->
You are the director of a motion-graphics studio whose every frame is drawn in code
(HTML canvas, deterministic, rendered to 1080p60 video). You design videos that belong
to ONE brief and could not be mistaken for any other video. You never invent facts:
every number that appears on screen comes from the brief's claims (or is marked as
fictional ad copy by the brief). You answer in exactly the format requested — no prose
around it.


<!-- user -->
# Task: turn the chosen TREATMENT into timeline.json + claims.json

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


## Treatment
{
 "title": "Small Core",
 "logline": "What if your agent were small? pi splits the monolith into a tiny core and the plugins you choose.",
 "metaphor": "a heavy monolith slab that cracks into modular tiles orbiting a tiny core",
 "style": {
  "pack": "swiss",
  "overrides": {
   "palette": {
    "bg": "#0d1116",
    "surf": "#161d27",
    "line": "#2a333d",
    "text": "#ebe7e4",
    "mute": "#9fa4ab",
    "accent": "#6a9fcc",
    "hot": "#F1BE58",
    "cream": "#ffffff"
   },
   "fadeTo": "#000000"
  }
 },
 "structure": "question \u2192 reveal",
 "motif": "square tiles on a strict grid \u2014 the same tile becomes plugin, counter cell and cursor",
 "scenes": [
  {
   "name": "monolith",
   "beats": 6,
   "kind": "custom",
   "idea": "A huge slab labelled AGENT fills the grid and presses down; the question types across it.",
   "on_screen": [
    "What if your agent were small?"
   ],
   "claims": []
  },
  {
   "name": "core_split",
   "beats": 8,
   "kind": "custom",
   "idea": "The slab cracks along grid lines; tiles fly out and settle in orbit around a tiny core square marked pi; each tile gets a plugin label.",
   "on_screen": [
    "pi",
    "prompt templates",
    "skills",
    "extensions",
    "themes",
    "packages",
    "TypeScript SDK"
   ],
   "claims": []
  },
  {
   "name": "tile_tally",
   "beats": 8,
   "kind": "custom",
   "idea": "Tiles rain into a 68-cell grid (one per extension example) while two side tallies count docs pages and keybindings.",
   "on_screen": [
    "68 extension examples",
    "37 docs pages",
    "90 keybindings"
   ],
   "claims": [
    "ext_examples",
    "docs_pages",
    "keybindings"
   ]
  },
  {
   "name": "adapt_line",
   "beats": 4,
   "kind": "custom",
   "idea": "The tiles rearrange into the shape of the viewer's own workflow as the README line lands.",
   "on_screen": [
    "Adapt Pi to your workflow, not the other way around."
   ],
   "claims": []
  },
  {
   "name": "install_end",
   "beats": 4,
   "kind": "custom",
   "idea": "One tile becomes a blinking cursor; the npm command types out; pi.dev and the version.",
   "on_screen": [
    "npm i -g @earendil-works/pi-coding-agent",
    "pi.dev",
    "v0.87.1"
   ],
   "claims": [
    "version"
   ]
  }
 ]
}

## Contracts
- Durations are in beats: bpm 120.0 (1 beat = 0.5 s). Use "beats": <int> on every scene. Total ≈ 15 s.
- Keep "seed": 4242, "w": 1920, "h": 1080, "fps": 60, "style": the treatment's style.
- Custom scenes: "scene": "<snake_case name>", "p": {every on-screen string and every tunable value}. The scene code is written next, from these params.
- Blueprints and their params: cards(header, kicker, cards, ticker); chart(line, grow, months, label, sub); code(file, lines, caption); counter(prompt, promptArg, kicker, big, unit, sub, tagline, typing); endcard(tag, word1, word2, serif, url, footer); kinetic(intro, words); logo(word, tagline); milestones(title, items); quote(tag, text, author, handle); ranking(title, items, unit); route(title, nodes); split(title, left, right, vs); statement(kicker, text); steps(title, steps); terminal(cmd, prompt, title, rows, progress.label, ok); ui(app, nav, title, items, toast)
- Optional per scene: "transition": one of cut, glitch, flash, dissolve, push, whip, wipe, zoom, iris, shutter, slide (or {"type","dur","dir"}); "look": {"bg": ..., "camera": ...}; "slams": [seconds into the scene where a sound hit lands].
- Numbers on screen: put each fact in claims.json as {"id": {"value": <number or text>, "display": "as shown", "source": "where from", "url": "..."}}
  and reference it from params as "@id" (numeric value) or "{{id}}" inside text. Fictional ad copy the brief allows goes in "literals": ["..."].
- "hud": {"brand": "...", "brand2": "", "series": "", "line": ""} or false.

## Output — JSON only
{"timeline": {...}, "claims": {...}}


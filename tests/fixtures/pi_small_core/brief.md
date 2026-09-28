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

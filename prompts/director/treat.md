# Task: write {{K}} distinct TREATMENTS for this video

## Brief
{{BRIEF}}

## Tools you are designing for
Style packs (the look — background, type, motion, transitions, score):
{{STYLES}}

Scene vocabulary: scenes are written in code for this video (characters, worlds, props,
diagrams, typography, data, UI — see the API below), plus blueprints you may reuse
sparingly: {{BLUEPRINTS}}.

Story structures to choose from (or invent one): {{STRUCTURES}}

## Assignment (from the project's variation seed — follow it)
{{ASSIGN}}

## Rules
- The {{K}} treatments must differ in style pack, structure AND visual metaphor.
- The metaphor comes from the brief's concrete nouns (a courier reel draws routes; a bakery reel draws dough).
- Total duration {{DURATION}} s. Each scene 2–6 s (a single long tracking shot may be longer). 3–7 scenes.
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

# Task: turn the chosen TREATMENT into timeline.json + claims.json

## Brief
{{BRIEF}}

## Treatment
{{TREATMENT}}

## Contracts
- Durations are in beats: bpm {{BPM}} (1 beat = {{BEAT}} s). Use "beats": <int> on every scene. Total ≈ {{DURATION}} s.
- Keep "seed": {{SEED}}, "w": {{W}}, "h": {{H}}, "fps": 60, "style": the treatment's style.
- Custom scenes: "scene": "<snake_case name>", "p": {every on-screen string and every tunable value}. The scene code is written next, from these params.
- Blueprints and their params: {{BLUEPRINT_PARAMS}}
- Optional per scene: "transition": one of cut, glitch, flash, dissolve, push, whip, wipe, zoom, iris, shutter, slide (or {"type","dur","dir"}); "look": {"bg": ..., "camera": ...}; "slams": [seconds into the scene where a sound hit lands].
- Numbers on screen: put each fact in claims.json as {"id": {"value": <number or text>, "display": "as shown", "source": "where from", "url": "..."}}
  and reference it from params as "@id" (numeric value) or "{{id}}" inside text. Fictional ad copy the brief allows goes in "literals": ["..."].
- "hud": {"brand": "...", "brand2": "", "series": "", "line": ""} or false.

## Output — JSON only
{"timeline": {...}, "claims": {...}}

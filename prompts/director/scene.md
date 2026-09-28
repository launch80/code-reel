# Task: write the scene file scenes/{{NAME}}.js

## Brief (short)
{{BRIEF}}

## Treatment
Title: {{TITLE}} — metaphor: {{METAPHOR}} — motif: {{MOTIF}} — style: {{STYLE}}

## This scene
{{SCENE}}
It runs {{DUR}} s ({{BEATS}} beats at {{BPM}} bpm) between: {{NEIGHBOURS}}.
Its params (p) from timeline.json:
```json
{{PARAMS}}
```

## Already written for this video (shared helpers / other scenes — reuse, don't duplicate)
{{EXISTING}}

## Scene API
{{API}}

## Example of the house standard (a different video — learn the craft, don't copy the picture)
```js
{{EXAMPLE}}
```

## Requirements
- One file: a `/* @meta {...} */` block, then `defineScene('{{NAME}}', (lt, d, p) => { ... })`. Helper functions allowed above it (prefix them with `{{NAME}}_`).
- Draw the treatment's metaphor for THIS scene — a picture, not a slide. One hero element, 2–4 supporting details, motion for the full duration.
- Every visible string comes from p. Text never overlaps text; everything readable stays inside SAFE.
- Deterministic. No Math.random, no Date.
Return ONLY the JavaScript file.

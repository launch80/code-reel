# Mode 2 — blueprint custom scene

`timeline.json` here is the standard Launch80 reel with the `chart` scene
replaced by a custom `orbit` scene (same 2.5s slot, on the beat grid).
`scene_custom.js` defines it with `defineScene('orbit', ...)` — the template
loads it automatically; nothing else changes.

    cp scene_custom.js timeline.json <project>/
    python3 validate.py timeline.json --allow-custom
    python3 render.py stills 4.6,5.2,6.4

See `references/blueprints.md` for the full contract.

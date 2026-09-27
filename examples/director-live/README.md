# Mode 1 — director output (live)

`brief.md` was given to `director.py --mode invent` with a local
`qwen36-q6` model over Ollama. The model produced 2 validation errors;
the repair round fixed them; `timeline.json` is the frozen result
(5 scenes, 15.00s, cuts on the beat grid). `timeline_meta.json` records
model, seed, prompt hash and `repair_used: true`.

    python3 director.py --mode invent --brief brief.md --model qwen36-q6 --out timeline.json

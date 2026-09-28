# Director — model-driven steps, identical for every backend

```bash
reel.py direct <proj> treat|pick|timeline|scenes|all [--backend agent|ollama|openai|mock] [--model m] [--base-url u]
                                                      [--fixtures dir] [--candidates 3] [--pick N] [--only a,b] [--max-repair 2]
```

| step | input | output | gate |
|---|---|---|---|
| treat | brief.md, style packs, structures, seed assignment | treatments.json, .reel/treatments.png (style frames) | K treatments, distinct packs, distinct metaphors, ≥70% custom beats, snake_case names — else one retry with the problems listed |
| pick | treatments.json | treatment.json | human/agent choice (`--pick N`) |
| timeline | treatment.json, brief, blueprint params | timeline.json, claims.json | compile (with blank stubs for unwritten scenes) → repair rounds carrying the exact errors |
| scenes | per custom scene: brief, treatment, its storyboard entry, params, neighbours, what's already written, API, one rotating example | scenes/<name>.js, .reel/review/<name>.png | node syntax → compile → layout audit (this scene) → novelty (this scene) → repair rounds carrying the report |
| all | — | everything above, resumable | — |

## Backends
- **agent** — the agent running the skill is the model. A step writes
  `.reel/llm/<key>.prompt.md` and exits 10 (`AWAITING AGENT`). Read the prompt,
  write the answer to `.reel/llm/<key>.answer.json|js` (JSON only / JS only —
  no prose), re-run the same command. Keys are stable (`treat-1`, `timeline-2`,
  `scene-orbit-1`, `scene-orbit-2` for a repair), so re-runs replay cached
  answers and continue where they stopped.
- **ollama / openai** — any local server (Ollama, vLLM, LM Studio, llama.cpp,
  MLX). Sampling temperature per step (treat 0.9, timeline 0.4, scenes 0.35,
  repairs lower) and a seed derived from the project seed + key, recorded in
  `<key>.meta.json`.
- **mock** — replays `<key>.answer.*` from `--fixtures`. Any real session's
  `.reel/llm/` is a fixture: `tests/fixtures/pi_small_core` is an agent
  session replayed by the test suite through the same prompts and gates.

## Variability
- The **seed** assigns each treatment's style pack and leaning structure, picks
  transitions for unpinned cuts, the score's key, and seeds model sampling.
  New seed → a different video, even with a deterministic model.
- `--candidates K` widens the search; the gate refuses treatments that share a
  pack or a metaphor.
- The scene prompt rotates its worked example by seed so no single example
  anchors every reel.
- Novelty compares every scene against `library/fingerprints.json` (blueprints
  in 4 styles + registered reels); `run --final --register` adds yours.

## After the director
Scenes are ordinary files. Critique with `reel.py review`, edit, re-review.
`direct scenes --only name` rewrites one scene with the model.

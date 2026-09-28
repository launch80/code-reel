# Interview — run it first, one question per message

Goal: a `brief.md` precise enough that the treatments can be different from each
other and still all right. Ask only about gaps; offer a default with every question;
if the user says "just do it", fill the rest with defaults and go.

1. **What is it for?** One product/event/story, who watches, what they do after. → brief purpose line
2. **Where will it play?** a) 16:9 (default) b) 9:16 c) 1:1 → `init --size`
3. **How long?** a) 15 s (default) b) 30 s c) custom → brief format line (durations become beats)
4. **What's on screen that could be checked?** Every number/claim + where it comes
   from (URL, file, "internal"). No source yet → it goes in as `"status": "placeholder"`
   and `--final` will refuse it until replaced. Fictional content (a story, ad copy for
   a made-up shop) is fine — say so and it becomes a literal. → claims.json
5. **Look?** a) match a brand — which site? (→ `reel.py brand`) b) a style pack —
   show `reel.py styles` c) surprise me (the seed picks) → style / brand.json
6. **Anything it must include or avoid?** (a mascot, a product shot, "don't look like
   our last reel") → brief must-include / must-avoid
7. **Who does the creative writing?** a) me, the agent (default) b) your local model
   (`--backend ollama --model …`) c) you, by hand → `--backend`
8. **Render plan?** a) draft → your OK → final (default) b) straight to final

Close by echoing a table (purpose, format, claims + sources, look, backend, plan, seed)
and saving it as `brief.md`. The seed is chosen at `init` — mention it: "say 'another
take' any time and I'll re-run with a new seed."

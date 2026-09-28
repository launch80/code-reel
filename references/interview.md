# The interview — run it FIRST, every invocation

The skill opens by interviewing the user, not by writing files. Goal: collect
the decisions that drive the pipeline (mode, content, format, look, quality,
facts) through a short **interactive conversation** — one question at a time —
then echo them back as a frozen brief and proceed.

## Rules of the interview

1. **One question per message.** Ask, then stop and wait. Never dump the
   seven questions as a form. This is a conversation, not a spec sheet —
   use the platform's interactive prompt/question tool if it has one.
2. **Every question carries its default and its cost**, so a one-word answer
   ("yeah", "b", "15s") is always sufficient. The user should never have to
   write a paragraph to get moving.
3. **Follow up when an answer opens a door.** "Match our brand" → *which
   site?* "We have a member count" → *what's the number and where does it
   come from?* A follow-up is one short question, not a new interview.
4. **Never ask what you already know.** If the request already answers a
   question (topic, aspect, numbers, brand), acknowledge it in one line
   ("got it — 16:9, 15 s") and move on. Interview about the *gaps*, not the
   transcript.
5. **Every question must drive a knob.** If an answer wouldn't change a
   file, a flag or an env var, don't ask it. (That's why there's no "what
   music vibe do you want?" — the score is derived, there is nothing to
   choose.)
6. Offer choices, not essays: 2–4 options per question, lettered, with the
   recommended one marked `(recommended)`.
7. **Close the loop before building**: echo the decision table (below), say
   what happens next (validate → stills → approval → full render → QC), and
   wait for the go. If at any point the user says "just do it / surprise me
   / stop asking", stop asking: fill the remaining answers with defaults,
   echo the table, and proceed.
8. **Save the brief.** Write the decision table to `brief.md` in the project
   dir. In mode 1 it becomes `director.py --brief brief.md` verbatim; in the
   fact-check it's the human record of what was asked and promised.
9. **Time-box it.** The whole interview should take under two minutes. If a
   question has stalled (user is away, or doesn't know), take the default,
   note it as *assumed* in the table, and keep going — the stills review is
   where things actually get corrected.

## The question bank

Ask one at a time, in this order, skipping any already answered. `→` marks
the knob it drives. Question 4 is the one worth slowing down for — dig with
short follow-ups until every on-screen number has a source or is marked a
placeholder.

**1. What is this reel for?** One product/event, one sentence — who should
watch it and what should they do after? Nothing else goes in this reel.
→ `brief.md` topic line, scene selection, QC fact-check scope

**2. Where will it play?**
   a. `16:9` — YouTube, embeds, desktop (recommended default)
   b. `9:16` — Reels / TikTok / Shorts
   c. `1:1` — feed posts
   → `timeline.json` `w`/`h`, `OUT_W`/`OUT_H` in build.sh. 9:16 and 1:1 need a
   vertical layout pass — say so, budget it, and still-check every scene.

**3. How long?**
   a. `15 s` at 120 bpm (recommended — the template's exact grid)
   b. `30 s` (two acts, still on the beat grid)
   c. custom seconds (must be a multiple of the beat, 0.5 s at 120 bpm)
   → `duration`, scene durations; longer means more scenes and more render
   minutes (~45 s of wall-clock per second of video at DPR=2).

**4. What do we claim on screen?** Give me the real numbers/stats, the three
   kinetic words, the end-card text, and where the numbers come from (URL or
   "internal"). If they don't have numbers yet, offer to write the reel with
   obvious placeholder stats and mark them `Medium risk` in the QC fact tab —
   *never* silently ship invented figures as fact.
   → every scene `p` object, the `"sources": {}` map in timeline.json,
   QC Fact Check tab

**5. Who writes the story?**
   a. **Director** — a local model invents the timeline from your one-liner
       (needs a local model; you review stills before anything is final)
   b. **I write it** — the agent composes `timeline.json` from your answers
       (recommended if no local model is configured)
   c. **Fill-in-the-blank** — you hand me the filled `blank.json`
   d. **New scene types** — we design them together in `scene_custom.js`
       (blueprint mode, see `references/blueprints.md`)
   → `director.py --mode invent` vs direct authoring vs blank.json vs
   `--allow-custom`

**6. Look?** Default is the house style: near-black background `#0b0b0c`,
   burnt-orange accent `#e85d04`, film grain + camera HUD, sound on.
   a. keep it (recommended)
   b. match a brand — give me the site, I'll scrape its palette and copy tone
   c. custom colors — give me two hexes (accent, background)
   d. clean look — HUD off, grain down; say "no HUD / no grain" and I'll set
   `hud:false` and the post-layer intensities in the theme block
   → `theme`, `hud` in timeline.json

**7. Render plan?**
   a. **Draft → approve → final** (recommended): fast DPR=1 stills and a
       DPR=1 MP4 now (~4 min), you approve, then DPR=2 final (~11 min)
   b. **Maximum quality now** — straight to DPR=2 (~11 min, and re-render if
       anything needs fixing)
   c. **Draft only** — you just want to see it move; final comes later
   → `DPR=1|2` for render.py + build.sh; approval gate before the long run

## The closing echo (always)

> Here's what I'm building:
>
> | | |
> |---|---|
> | Reel | <topic, one line> |
> | Format | <16:9 / 9:16 / 1:1> · <N> s · 60 fps · 120 bpm |
> | Story | <mode> · scenes: <terminal → kinetic → … > |
> | Claims | <list> — sources: <yes: map added / NO — flagged in QC> |
> | Look | <palette> · HUD on/off · sound on/off |
> | Plan | stills → your OK → <DPR> render → QC (22 auto + 25 manual tests) |
> | ETA | <minutes> for stills, <minutes> for the MP4 |
>
> <"Say go and I'll start." / "Starting with defaults — I'll show you stills
> before anything is final.">

## What the interview must NOT become

- Not a requirements doc, and not a form. One question, one answer, next.
- Not a design consultation. Offer defaults; let them pick.
- Not a gate when the user already gave the answers — the interview is a
  parser for what's missing, not a ritual.
- Never a promise to fix it later: if 9:16 is chosen, say the layout pass
  is part of the job; if stats have no sources, say the QC tab will flag it.

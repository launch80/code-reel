# Prompt: "Local vs Frontier" reel

Paste everything below the line into the skill (`/skill:code-reel ...`), or hand it to
any agent running the code-reel skill. Edit the STATS block freely — the numbers are the
only thing you should need to touch.

---

Use the code-reel skill to build a 15s motion reel comparing local AI vs frontier/cloud AI.

duration=15 bpm=120 fps=60 size=1920x1080 out=local-vs-frontier.mp4 theme=#e85d04 bg=#0b0b0c audio=on brand=launch80.com

Title: "LOCAL vs FRONTIER". Angle: local AI wins on privacy, cost, control, offline;
frontier AI's cons are: your data leaves the machine, per-token billing, rate limits,
silent model changes, kill-switch risk. Keep the template's 6-scene structure, cut
times, and audio sync — only rewrite content.

SCENES (keep CUTS=[1.5,4.0,7.0,10.0,12.5] and the existing beat grid):
1. BOOT (0–1.5): terminal typing `./compare --local --vs-frontier --since 2026`.
   Rows: [your prompts, "never leave the box"], [your bills, "$0.00 / token"],
   [your models, "never silently deleted"], [your hardware, "already in the room"].
2. KINETIC (1.5–4.0): intro line "the frontier models are great — at spending your data."
   Words: PRIVATE. (1.5→, "your prompts never leave", "0 uploads") ·
   FREE. (2.5→, "no per-token billing", "$0/mo") ·
   YOURS. (3.5→, "no kill-switch, no version drift", "pinned forever") — accent color
   on the last word.
3. THE STACK (4.0–7.0): header "// THE TRADE-OFF NOBODY SAYS OUT LOUD". Three stat
   cards:
   - card 1 tag "COST · 1M TOKENS/DAY": counter $312 → $0, unit "per year",
     sub "frontier API vs one RTX 3090", viz bars (before/after)
   - card 2 tag "PRIVACY · REQUESTS": counter 0 → 100, unit "%", sub "local never
     leaves the box · cloud: 100% uploaded", viz kv-style
   - card 3 tag "AVAILABILITY · PER YEAR": counter 41 → 300, unit "h+", sub "3
     outages, 1 ToS change, 1 deprecated model", viz growing ctx-bar
4. FROM THE LAB (7.0–10.0): big counter 27 → 100, unit "PRIVATE", label "PROMPTED
   LOCALLY, EVERY DAY"; oscilloscope curve; sub line "NO RATE LIMIT · NO LOGGING ·
   NO REVIEW"; typing line: "[@dev] frontier model deprecated my fine-tune — went
     local the same week".
5. THE COMMUNITY (10.0–12.5): line "and the people who left didn't go back."
   Big counter 2 → 2,000 (members, local-AI builders), chart FEB→SEP,
   label "LOCAL AI BUILDERS · EST. FEB 2026".
6. END CARD (12.5–15): tagline "THE FRONTIER RENTERS COMPUTE. YOU OWN YOURS."
   logo wordmark launch80, serif line "local ai, dialed in.", url launch80.com,
   footer "SHOWREEL · LOCAL VS FRONTIER · 2026".

STATS (the only numbers you may need to change — keep the digits' widths sane for
the big-number layout):
- API cost: $312/yr → $0/yr for 1M tokens/day
- privacy: 100% of prompts local vs 100% uploaded
- downtime: 3 outages / 1 ToS change / 1 deprecated model per year
- community: 2 → 2,000 members (reuse the GROW shape, just scale to 2,000)

Follow the skill's §4 review loop (PNG stills at DPR=2, check collisions/flash alpha,
then full render) and §3 audio-sync rules: every time list in audio.py must match the
final CUTS/IMPACTS/typing windows.

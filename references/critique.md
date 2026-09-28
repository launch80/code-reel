## Critique — answer these from the contact sheet before any full render

Look at `.reel/contact.png` (one frame per scene) with the brief open. Answer in
writing; every "no" is a fix, not a note.

1. **Mute test.** With the sound off and no narration, does each frame say
   something about THIS brief? Cover the text: is the picture still about the
   subject (its nouns — penguins, ports, GPUs), or is it generic cards/numbers?
2. **Swap test.** Could this frame be dropped into a different company's reel
   unchanged? If yes, it is a template frame — redraw it from the brief's nouns.
3. **One hero per scene.** Is there exactly one thing the eye lands on first?
   If two things compete, shrink or delay one.
4. **Hierarchy.** Read order = size order? Nothing important smaller than 24 px
   at 1080p; nothing decorative louder than the claim.
5. **Continuity.** Does each scene hand off to the next (a shared shape, color,
   direction of motion, or the transition's direction)? Name the handoff.
6. **Claims.** Every number on screen is in claims.json with a source, and the
   wording on screen does not claim more than the source says.
7. **Look.** Palette, type and motion match the chosen style pack/treatment.
   No leftover default brand strings (grep the stills for placeholder text).
8. **Audit + novelty.** `.reel/audit.json` has 0 errors; `novelty` is OK. If a
   scene is flagged RE-SKIN, the fix is a new picture, not a new color.

Record the answers in `review.md` in the project. Fix → `reel.py review` again.

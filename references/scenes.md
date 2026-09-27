# Scene library — params contract

A reel is a list of scenes in `timeline.json`. `reel.html` derives everything
(cuts, HUD scene list, impact flashes, camera shake, audio) from it — no drawing code
has to be touched to recompose a reel.

```json
{
  "name": "MY REEL", "w": 1920, "h": 1080, "fps": 60, "bpm": 120,
  "theme": { "accent": "#e85d04", "hot": "#ff8a3d", "bg": "#0b0b0c", "cream": "#faf9f7" },
  "hud": { "brand": "LAUNCH", "brand2": "80", "series": "SHOWREEL_2026", "line": "EP01" },
  "timeline": [ { "scene": "terminal", "dur": 1.5, "name": "BOOT", "slams": [], "p": { ... } } ]
}
```

- `bpm` drives the beat grid. **Every `dur` must be a multiple of 60/bpm seconds**
  (at 120bpm: 0.5, 1.0, 1.5, 2.0, 2.5, 3.0...) so cuts land on beats — `validate.py` checks this.
- `name` is the HUD label (defaults to the scene type). `slams` are optional extra
  impact times (seconds relative to the scene start); audio.py adds a hit there.
- All times inside `p` are **relative to the scene start**, not absolute.
- `theme` recolors the whole reel (accent/hot/bg/cream); HUD text comes from `hud`.

## Scene types

### terminal — boot/terminal window (opener)
`p`: `cmd` (typed line), `prompt` (default `launch80:~$`), `title` (window title),
`rows`: `[[label, value], ...]` (max 4), `progress`: `{label, pct}` optional.
Internal: prompt typed 0.12–0.48·dur, rows 0.52–0.78·dur, bar 0.72–0.90·dur, exits 0.86–1.0.

### kinetic — big word slam-ins
`p`: `intro` (serif line, optional), `words`: `[[text, offset, color, note, val], ...]`.
`offset` is seconds into the scene (each word slams — audio impact + flash are derived).
`color` is `""`/`null` for cream, `"ACCENT"` for the theme accent, or any CSS color
(the last word is conventionally `"ACCENT"` with a glowing value). Short form
`[text, offset, note, val]` also works if you don't need a per-word color.
Annotation goes to the right column (x≈1330) if it doesn't collide with the word,
below the word otherwise. Word size 180px Russo One; keep words ≤ 9 chars.

### cards — stat cards (the "stack")
`p`: `header` (mono line), `kicker` (serif line), `cards`: 2–3 objects:
`{tag, big: {from, to, fmt}, unit, sub, label, viz}`, `ticker`: `{label, items: [...]}`.
- `fmt`: `int` (1,234) · `x` (5.2×) · `k` (262K)
- `viz`: `bars` (before/after ratio) · `kv` (filling blocks; needs `vizFrom`/`vizTo` labels)
  · `ctx` (block sweep; `vizTo` label defaults to `fmt(to)`)
Big number auto-shrinks so the final string + unit fits the card. Cards exit 0.88–0.98·dur.

### counter — big counter + oscilloscope (the "lab" beat)
`p`: `prompt` (e.g. `~/projects`), `promptArg` (typed arg), `kicker` (serif),
`big: {from, to, fmt}` (the giant number, 440px), `unit`, `sub`, `tagline` (wipe line),
`typing` (chat line typed at bottom), `scope`: 120 values in 0–1 (oscilloscope curve).
The counter's big number is 440px — keep `to` ≤ 6 digits.

### chart — growth chart + burst
`p`: `line` (serif intro), `grow`: [values] monotonic, `months`: [labels] (same length),
`label` (big word), `sub` (mono line), `max` (chart ceiling; default = last value),
`impact` (time value hits max — flash + burst + audio slam derived from it), `seed`.
Keep the final value ≤ 7 digits (250px Russo One).

### quote — testimonial slam
`p`: `tag` (default `FROM THE FEED`), `text` (serif, wraps at 2 lines), `author`,
`handle`, `slam` (time of the impact; default 0.4·dur). Keep text ≤ ~14 words.

### split — two-column comparison (local vs cloud, before vs after)
`p`: `title` (mono, centered), `left`/`right`: `{label, items: [[label, value], ...], winner?}`.
`winner: true` gets the accent column (checkmarks, hot values); the other is muted.
Keep items ≤ 5 per side.

### endcard — brand close
`p`: `tag`, `word1` + `word2` (wordmark, word2 in accent, 800px DM Sans), `serif`
(italic line), `url` (typed), `footer`. Put it last; the audio bell is derived from it.

## Audio

`audio.py` derives everything from `timeline.json`: beats from `bpm`, risers at cuts,
impacts at cuts + `slams` + kinetic words + chart impact + quote slam, typing clicks
from the `cmd`/`typing` strings, counter ticks, bell from the endcard. A hand-written
`audio.json` in the template dir overrides the derived events (see audio.py docstring).

## Adding a new scene type

1. Add `REG.myscene = (lt, d, p) => {...}` in `reel.html` (lt = seconds into the scene,
   d = scene duration, p = params). Keep all timing relative to `d` so the scene
   works at any duration.
2. Add required params to `REQUIRED` in `validate.py`, and optional slam times to
   `sceneSlams()` in reel.html + the matching derivation in `audio.py` (`derive_events`).
3. Document it here.

## Timing conventions

- Durations on the beat grid (0.5s at 120bpm). 2–3s per scene is the max attention
  span; the default 15s reel uses 1.5 + 2.5 + 3 + 3 + 2.5 + 2.5.
- `p`-internal timings are fractions of `d` (0.12·d etc.) where the scene is generic;
  where the scene needs musical timing (chart impact at 1.8) it is an explicit param.
- Keep `slams`/word `offset`/`impact` values on 0.5s multiples at 120bpm so the hits land.

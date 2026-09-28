# Blueprint scenes — params contract

Blueprints are reference scenes (and occasional building blocks). A final reel is
mostly scenes written for that video — see `api.md`. All blueprints are responsive
(16:9, 9:16, 1:1), take fonts/colors/motion from the style, and have no brand defaults.

Scene entry in `timeline.json`:
```json
{"scene": "<type>", "beats": 6, "name": "HUD LABEL", "transition": "push" | {"type", "dur", "dir"},
 "look": {"bg": "paper", "camera": "static"}, "slams": [1.5], "p": { ...params... }}
```
(`"dur"` in seconds also works; beats survive bpm/style changes.) Times inside `p` are seconds from scene start.

| type | params (required first) | sound |
|---|---|---|
| terminal | **cmd**, prompt, title, rows [[label, value]], progress {label, pct}, ok | typing on cmd |
| kinetic | **words** [[text, offset, color?, note?, value?]], intro | a hit per word offset |
| cards | **cards** [{tag, big {from,to,fmt}, unit, sub, label, viz bars/kv/ctx, vizFrom, vizTo}], header, kicker, ticker {label, items} | ticks |
| counter | **big** {from,to,fmt}, prompt, promptArg, kicker, unit, sub, tagline, typing, scope [0..1 values] | typing + ticks |
| chart | **grow** [values], months, label, sub, line, max, impact, seed, fmt | hit at impact + ticks |
| quote | **text**, **author**, tag, handle, slam | hit at slam |
| split | **left**, **right** {label, badge, items [[label, value]], winner}, title, vs | — |
| endcard | **word1**, word2, tag, serif, url, footer | bell + typing on url |
| statement | **text**, kicker, emphasis [words], align left/center, reveal rise/wipe/scramble/type | — |
| code | **lines**, file, add [idx], del [idx], focus idx, caption | typing |
| ui | **items** [{title, meta, badge}], app, nav, title, clicks [{item, at}], toast | a hit per click |
| steps | **steps** [{label, sub}], title, active | — |
| milestones | **items** [{when, label}], title | — |
| logo | path (SVG d) + vb [w,h] or asset, word, tagline | bell |
| ranking | **items** [[label, value]], title, fmt, unit, highlight | ticks |
| route | **nodes** [{label, x, y} in 0..1], edges [[a,b]], path [i…], title | — |

fmt: int · comma · x (1.7×) · k (262K) · d ($) · pct · dec1 · dec2.
Numbers in params should be claims (`"@id"`, `{{id}}`) — see `claims.md`.

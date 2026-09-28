# Claims — every number on screen has a source

`claims.json` in the project is the ledger:

```json
{
  "members":  {"value": 2000, "display": "2,000", "source": "Discord server count", "url": "https://…", "date": "2026-09-25"},
  "mtp_gain": {"value": 1.7, "display": "1.7×", "source": "cloudmagazin, 2026-05-27", "url": "https://…"},
  "growth":   {"value": [0, 160, 430, 780], "source": "monthly export", "status": "placeholder"}
}
```

Reference claims from `timeline.json` params:
- `"@id"` — the whole value (numbers, lists): `"big": {"from": 0, "to": "@members", "fmt": "comma"}`
- `{{id}}` / `{{id:fmt}}` inside text: `"sub": "{{members}} builders and counting"`, fmt = comma int x k d pct

What compile enforces:
| check | draft | `--final` |
|---|---|---|
| a digit in on-screen text that is not from a claim or a declared literal | warning | **error** |
| a numeric data value (`to`, `from`≠0, `value`, `grow`, `series`…) not from a claim | warning | **error** |
| claim without `source`/`url` | warning | **error** |
| claim with `"status": "placeholder" | "illustrative" | "todo"` | warning | **error** |
| on-screen text with a number hard-coded inside scene JS | warning | **error** |

`"literals": ["2026", "v2"]` in the timeline declares strings that are not
claims (years in a tagline, product names with digits, fictional ad copy the
brief allows). HUD brand strings are literals automatically.

QC's **Fact Check** tab lists every claim use with its source; a claim with no
source is High risk. Rule of thumb: the on-screen wording may never say more
than the source does ("~2×" if the source says "1.4–2×").

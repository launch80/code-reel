# QC — the 66-test discipline, automated where a machine can look

`python3 qc.py reel.mp4 timeline.json` (env `QC_DIR` for output dir) writes
`qc_report.md` + `qc_report.xlsx` (openpyxl; markdown works without it). The
workbook mirrors a human post-QC: **Summary · Test Sequence · Cue Sheet ·
Tech Specs · Fact Check**.

## What is MEASURED (auto, can FAIL)

| Block | Tests | How |
|---|---|---|
| A · Pre-flight | timeline parses, `validate.py` passes (with `--allow-custom`), files present, frame count = dur × fps | direct |
| B · Tech specs | width/height/fps/nb_frames/codec/profile/pix_fmt, **color tags** (`bt709` ×3 — the classic FAIL), color range, bitrate sane, fast-start (moov before mdat), audio codec/rate/channels/bitrate, A/V length match, file size | `ffprobe`, top-level box scan |
| B · Content scans | black segments ≤ 0.15 s (head/tail fades only), zero freezes ≥ 0.4 s | `blackdetect`, `freezedetect` |
| E · Loudness | integrated −14 ± 1 LUFS, true peak ≤ −1 dBTP, LRA ≤ 8 | `ebur128=peak=true` |
| E · Sync | every impact lands on its cut | **by construction** — render and audio both derive from `events.py`; Pass unless one side is edited alone |

## What is PRE-FILLED for a human (status `Not run`)

- **C · Visual** — one row per scene with its timecode range, plus HUD,
  safe-area and spelling rows.
- **D · Transitions** — one row per cut with ±frame window.
- **E · subjective** — ducking, small speakers, mono compatibility, tail fade.
- **G · Delivery** — per-platform checks (Reddit, LinkedIn/X, embed, thumbnail, captions).
- **H · Sign-off** — zero open Blocker/Major + a human full watch with sound.

## Cue Sheet

Derived from the same `events.py` as the soundtrack: fade-in, typing windows,
riser→impact at every cut, slams (with the *picture cause* resolved — which
word slams, which counter lands), counter ticks, endcard bell, tail fade.
Frame + timecode + scene + tolerance. It is the sheet an editor would
manual-conform; here it can't drift.

## Fact Check

Every on-screen string is extracted from the scene `p` params (skipping
layout keys like `fmt`/`seed`/`viz`). Rules:

- found in `timeline.json`'s optional `"sources": {"claim": "url"}` map → **Verified / Low**
- contains a digit → **Medium risk — source required** before publishing
- text-only → **Low — brand text, no claim**

Add the `sources` map while you still remember where the numbers came from.
The Summary tab says `READY TO PUBLISH?` only when auto-fails are 0 **and**
every manual test is resolved — a green machine run means "nothing is wrong",
not "everything is right".

## Loop

fix → re-render → `qc.py` again → diff the Test Sequence status column.
`Blocker` severity (codec, pix_fmt, frame count, sync, sign-off) is
never publishable when red.

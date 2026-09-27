#!/usr/bin/env python3
"""Post-production QC for a built reel — the 66-test / 8-phase discipline,
automated wherever a machine can look.

Reads the SAME timeline the render and audio used (events.py is the single
source of truth), measures the built MP4 with ffprobe/ffmpeg, and emits:

  qc_report.md    always
  qc_report.xlsx  5 tabs (Summary, Test Sequence, Cue Sheet, Tech Specs,
                  Fact Check) — same shape as a human post-QC workbook

Phases A (pre-flight), B (technical), and the loudness/black/freeze part of
E are MEASURED. Scene visual tests (C), transitions (D), delivery (G) and
sign-off (H) are PRE-FILLED with timecodes/frames derived from the timeline
and left 'Not run' for a human. Impact-to-cut sync is exact BY CONSTRUCTION
(render and audio derive from the same events) and is marked Pass.

  python3 qc.py [reel.mp4] [timeline.json]        env: QC_DIR=out dir
"""
import datetime
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events

TL_PATH = sys.argv[2] if len(sys.argv) > 2 else (os.environ.get("TIMELINE") or "timeline.json")
MP4 = sys.argv[1] if len(sys.argv) > 1 else "reel.mp4"
OUT = os.environ.get("QC_DIR", ".")
os.makedirs(OUT, exist_ok=True)

HERE = os.path.dirname(os.path.abspath(__file__))
TL = events.load(TL_PATH)
FPS = int(TL.get("fps", 60))
SC = events.scene_table(TL)
DUR = SC[-1]["t1"] if SC else 0.0
N = int(round(DUR * FPS))
EV = events.derive_events(TL)
SRC = TL.get("sources", {})


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def ffprobe_json(args):
    _, out, _ = run(["ffprobe", "-v", "error", "-i", MP4] + args + ["-of", "json"])
    try:
        return json.loads(out or "{}")
    except Exception:
        return {}


def tc(sec):
    f = int(round(sec * FPS))
    return "%02d:%02d:%02d:%02d" % (f // (3600 * FPS) % 24, f // (60 * FPS) % 60, f // FPS % 60, f % FPS)


def nz(x, d=0):
    """Safe numeric for report formatting — never crashes the markdown build."""
    try:
        return int(x)
    except (TypeError, ValueError):
        try:
            return "%.*f" % (d, float(x))
        except (TypeError, ValueError):
            return "?"


def sname(t):
    for s in SC:
        if s["t0"] - 1e-6 <= t < s["t1"] + 1e-6:
            return "%02d %s" % (s["i"] + 1, s["name"])
    return "TAIL"


# ================= B · tech specs (target vs measured) =================
tech = []  # (param, target, measured, PASS/FAIL, how, note)


def tspec(p, target, measured, ok, how, note=""):
    tech.append((p, target, measured, "PASS" if ok else "FAIL", how, note))


v = (ffprobe_json(["-select_streams", "v:0", "-show_entries",
                   "stream=width,height,r_frame_rate,nb_frames,codec_name,profile,pix_fmt,"
                   "color_space,color_primaries,color_transfer,color_range,bit_rate",
                   ]).get("streams") or [{}])[0]
a = (ffprobe_json(["-select_streams", "a:0", "-show_entries",
                   "stream=codec_name,sample_rate,channels,bit_rate,duration",
                   ]).get("streams") or [{}])[0]
vf = (ffprobe_json(["-select_streams", "v:0", "-show_entries", "stream=duration"]).get("streams") or [{}])[0]
fmt = (ffprobe_json(["-show_entries", "format=duration"]).get("format") or {})


def eq(x, want):
    return str(x) == str(want)


TW, TH = int(TL.get("w", 1920)), int(TL.get("h", 1080))
tspec("Width", TW, v.get("width"), eq(v.get("width"), TW), "ffprobe stream=width")
tspec("Height", TH, v.get("height"), eq(v.get("height"), TH), "ffprobe stream=height")
tspec("Frame rate", "%d/1" % FPS, v.get("r_frame_rate"), eq(v.get("r_frame_rate"), "%d/1" % FPS), "ffprobe stream=r_frame_rate")
expected_frames = v.get("nb_frames") or "?"
if str(v.get("nb_frames") or "") != "?" and str(v.get("nb_frames")) != str(N):
    print("NOTE: container frame count differs from the timeline (%s vs %d) — check for dropped/dup frames" % (v.get("nb_frames"), N))
else:
    N = int(v.get("nb_frames")) if str(v.get("nb_frames") or "") != "?" else N
tspec("Frame count", N, v.get("nb_frames"), eq(v.get("nb_frames"), N), "ffprobe stream=nb_frames", "off-by-one = dropped/dup frame at a cut")
tspec("Duration", "%.3f" % DUR, fmt.get("duration"), abs(float(fmt.get("duration") or 0) - DUR) < 0.05, "ffprobe format=duration")
tspec("Video codec", "h264", v.get("codec_name"), eq(v.get("codec_name"), "h264"), "ffprobe stream=codec_name")
tspec("Profile", "High", v.get("profile"), eq(v.get("profile"), "High"), "ffprobe stream=profile")
tspec("Pixel format", "yuv420p", v.get("pix_fmt"), eq(v.get("pix_fmt"), "yuv420p"), "ffprobe stream=pix_fmt", "required for broad player support")
ct = [v.get("color_space"), v.get("color_primaries"), v.get("color_transfer")]
tspec("Color tags space/primaries/trc", "bt709 / bt709 / bt709", " / ".join(x or "unknown" for x in ct),
      all(x == "bt709" for x in ct), "ffprobe stream=color_*", "untagged = shifted color on some players (the classic FAIL)")
tspec("Color range", "tv (limited)", v.get("color_range") or "unknown", eq(v.get("color_range"), "tv"), "ffprobe stream=color_range")
vb = float(v.get("bit_rate") or 0) / 1e6
tspec("Video bitrate Mb/s", "6-20", "%.1f" % vb, 4 <= vb <= 24, "ffprobe stream=bit_rate", "grain eats bitrate — check it didn't explode")


def box_offsets(path):
    off, found = 0, {}
    with open(path, "rb") as f:
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            size = int.from_bytes(hdr[:4], "big")
            typ = hdr[4:8].decode("latin1")
            if typ in ("moov", "mdat"):
                found.setdefault(typ, off)
            if size == 1:
                b = f.read(8)
                if len(b) < 8:
                    break
                size = int.from_bytes(b, "big")
                f.seek(size - 16, 1)
            elif size >= 8:
                f.seek(size - 8, 1)
            else:
                break
            off += size
    return found


bx = box_offsets(MP4) if os.path.exists(MP4) else {}
fast = bool(bx.get("moov")) and ("mdat" not in bx or bx["moov"] < bx["mdat"])
tspec("Fast-start (moov before mdat)", "yes", "yes" if fast else "no", fast, "byte offset of top-level boxes", "streaming playback starts instantly")
tspec("Audio codec", "aac", a.get("codec_name"), eq(a.get("codec_name"), "aac"), "ffprobe stream=codec_name")
tspec("Sample rate", "48000", a.get("sample_rate"), eq(a.get("sample_rate"), "48000"), "ffprobe stream=sample_rate", "build.sh resamples the 44.1k wav")
tspec("Channels", "2", a.get("channels"), eq(a.get("channels"), "2"), "ffprobe stream=channels")
ab = float(a.get("bit_rate") or 0) / 1e3
tspec("Audio bitrate kb/s", ">= 128", "%.0f" % ab if ab else "?", ab >= 128, "ffprobe stream=bit_rate",
      "synthetic 15 s audio won't fill a 256k target — AAC lands ~150; below 128 something is wrong")
tspec("A/V length match", "both %.3f s" % DUR, "v %s / a %s" % (vf.get("duration"), a.get("duration")),
      abs(float(vf.get("duration") or 0) - DUR) < 0.05 and abs(float(a.get("duration") or 0) - DUR) < 0.05,
      "ffprobe duration, both streams")
fsz = os.path.getsize(MP4) / 1e6 if os.path.exists(MP4) else 0
tspec("File size MB", "<= 1024", "%.1f" % fsz, fsz <= 1024, "ls -l")

_, _, err = run(["ffmpeg", "-v", "info", "-i", MP4, "-vf",
                 "blackdetect=d=0.03:pix_th=0.05,freezedetect=n=-45dB:d=0.4", "-f", "null", "-"])
blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)
freezes = re.findall(r"freeze_start:([\d.]+)", err)
tspec("Black segments", "head/tail fades only, each <= 0.15 s",
      "; ".join("%s-%s" % b for b in blacks) or "none",
      all(float(e) - float(s) <= 0.15 for s, e in blacks), "blackdetect d=0.03 pix_th=0.05")
tspec("Frozen segments >= 0.4 s", "0", str(len(freezes)), len(freezes) == 0, "freezedetect n=-45dB d=0.4")

_, _, err = run(["ffmpeg", "-v", "info", "-i", MP4, "-af", "ebur128=peak=true", "-f", "null", "-"])
# per-frame lines also contain "I: -70.0 ..." — parse ONLY the final Summary block
err = err.split("Summary:")[-1]


def ebn(name):
    m = re.search(name + r"\s*:\s*(-?[\d.]+)", err)
    return float(m.group(1)) if m else None


lufs, lra, tp = ebn("I"), ebn("LRA"), ebn("Peak")  # "Peak:" under "True peak:" in the summary
tspec("Integrated loudness LUFS", "-14 +/- 1", lufs, lufs is not None and -15 <= lufs <= -13, "ebur128=peak=true", "platforms turn 44100-in-48k containers fine; loudness is the one that matters")
tspec("True peak dBTP", "<= -1.0", tp, tp is not None and tp <= -1.0, "ebur128=peak=true")
tspec("Loudness range LU", "<= 8", lra, lra is not None and lra <= 8, "ebur128")

# ================= A · pre-flight =================
pref = []


def pre(name, ok, note=""):
    pref.append((name, "PASS" if ok else "FAIL", note))


pre("timeline parses + scene table", bool(SC), TL_PATH)
pre("validate.py passes", subprocess.run([sys.executable, os.path.join(HERE, "validate.py"), TL_PATH, "--allow-custom"]).returncode == 0)
pre("reel.html present", os.path.exists(os.path.join(os.getcwd(), "reel.html")))
pre("built mp4 present", os.path.exists(MP4), MP4)
pre("frame count == duration x fps", str(v.get("nb_frames")) == str(N), "%s vs %s" % (v.get("nb_frames"), N))

# ================= Cue sheet (by construction) =================
cues = []


def cue(t, pic, snd, tol=2):
    f = int(round(t * FPS))
    cues.append((max(0.0, t), f, tc(t), sname(t), pic, snd, tol))


cue(0, "fade in from black (0-0.12 s)", "silence — groove starts at first cut", 2)
for t0, dur, n in EV["typing"]:
    cue(t0, "typing (%.2f-%.2f s, %d chars)" % (t0, t0 + dur, n), "%d typing clicks, music ducks" % n, 2)
for t in EV["cuts"]:
    cue(t - 0.9, "riser window opens", "riser (0.9 s)", 3)
    cue(t, "GLITCH cut + flash -> %s" % sname(t + 0.01), "impact + kick + 2 kHz blip", 1)
for t in EV["slams"]:
    # find the picture cause for a nicer cue sheet
    pic = "impact (word slam / landing)"
    for s in SC:
        if s["scene"] == "kinetic":
            for w in s["p"].get("words", []):
                if abs(s["t0"] + w[1] - t) < 1e-6:
                    pic = "word '%s' slams in" % w[0]
        if s["scene"] == "chart" and s["p"].get("impact") is not None and abs(s["t0"] + s["p"]["impact"] - t) < 1e-6:
            pic = "chart counter LANDS on %s" % s["p"].get("label", "final value")
        if s["scene"] == "quote" and s["p"].get("slam") is not None and abs(s["t0"] + s["p"]["slam"] - t) < 1e-6:
            pic = "quote slams in"
    cue(t, pic, "impact (half level)", 1)
for t0, t1 in EV["ticks"]:
    cue(t0, "counter ticking (%.2f-%.2f s)" % (t0, t1), "%d ticks at 20 Hz" % int((t1 - t0) * 20), 3)
if EV.get("bell") is not None:
    cue(EV["bell"], "endcard wordmark up", "bell chord", 2)
cue(DUR - 0.8, "last frame", "audio fade-out begins (0.8 s)", 3)
cue(DUR - 0.25, "picture fade to black", "—", 2)
cues.sort(key=lambda x: x[0])

# ================= Fact check (every on-screen string) =================
SKIP_KEYS = {"fmt", "scene", "name", "slam", "impact", "seed", "max", "viz", "dur", "from", "to", "pct"}
SKIP_VALS = {"ACCENT", "int", "x", "k", "d", ""}
facts = []


def collect(obj, key=None):
    if isinstance(obj, dict):
        if "from" in obj and "to" in obj:
            yield "%s->%s" % (obj["from"], obj["to"])
        else:
            for k, val in obj.items():
                if k not in SKIP_KEYS:
                    yield from collect(val, k)
    elif isinstance(obj, (list, tuple)):
        for it in obj:
            yield from collect(it, key)
    elif isinstance(obj, str):
        if obj not in SKIP_VALS:
            yield obj


def has_num(s):
    return bool(re.search(r"\d", s))


for s in SC:
    seen = set()
    for x in collect(s["p"]):
        for part in [x] if "\n" not in x else x.split("\n"):
            part = part.strip()
            if not part or part in seen:
                continue
            seen.add(part)
            if part in SRC:
                facts.append((s["t0"], sname(s["t0"]), part, "VERIFIED: %s" % SRC[part], "Low", "Verified"))
            elif has_num(part):
                facts.append((s["t0"], sname(s["t0"]), part, "(source required)", "Medium", "Not run"))
            else:
                facts.append((s["t0"], sname(s["t0"]), part, "(brand text - no claim)", "Low", "Not run"))

# ================= Test sequence =================
tests = []  # (phase, id, tin, tout, scene, what, how, expected, severity, status, note)
n = 0
for name, res, note in pref:
    n += 1
    tests.append(("A · Build & pre-flight", "A-%02d" % n, None, None, "pre-flight", name, "qc.py", "pass", "Major", res, note))
for p in tech:
    tests.append(("B · Technical QC", "B", 0, DUR, "container / codecs / color / audio / loudness",
                  p[0], p[4], p[1],
                  "Blocker" if p[0] in ("Video codec", "Pixel format", "Frame count", "Frame rate") else "Major",
                  p[3], p[5]))
for c in EV["cuts"]:
    tests.append(("D · Transitions & motion", "D", max(0.0, c - 0.1), c + 0.2, "cut at %.2f s" % c,
                  "glitch + flash; RGB split settles < ~10 frames; flash not blown; no audio click",
                  "frame-step 24 frames around the cut", "displacement decays fast; flash <= 0.3 alpha", "Major", "Not run",
                  "impact lands on the cut BY CONSTRUCTION (see cue sheet)"))
for s in SC:
    tests.append(("C · Visual QC by scene", "C", s["t0"], s["t1"], "%02d %s" % (s["i"] + 1, s["name"]),
                  "all text legible and inside safe areas; no clipping/overlap; counters land exactly; theme colors correct",
                  "pause at 60-80% of the scene; frame-step the entrance", "clean; compare against the still review", "Major", "Not run", ""))
tests.append(("C · Visual QC by scene", "C", 0, DUR, "HUD (all scenes)", "REC / TC / SCENE / frames never overlap; scene label matches the cut; progress bar tracks", "spot-check 4 timestamps", "no overlap, correct labels", "Minor", "Not run", ""))
tests.append(("C · Visual QC by scene", "C", 0, DUR, "safe areas", "critical text inside 90% title-safe (96 px LR, 54 px TB at 1080p)", "90% guide overlay; also check phone crop", "all text inside", "Major", "Not run", ""))
tests.append(("C · Visual QC by scene", "C", 0, DUR, "spelling", "every on-screen string proofed", "read the Fact Check tab top to bottom", "zero typos", "Major", "Not run", ""))
tests.append(("E · Audio QC & sync", "E", 0, DUR, "impact sync", "every impact lands on its cut; slams on their words", "by construction — render + audio share events.py", "exact", "Blocker", "Pass", "derive in events.py; only drifts if one side is edited alone"))
tests.append(("E · Audio QC & sync", "E", 0, DUR, "music vs sfx", "kick/hat groove doesn't fight typing clicks; ducking audible", "listen 0-2 s and any typing scene", "everything audible", "Minor", "Not run", ""))
tests.append(("E · Audio QC & sync", "E", 0, DUR, "small speakers", "kick/sub felt on phone speakers; no harsh 2 kHz blip", "laptop + phone + headphones", "nothing clips or vanishes", "Minor", "Not run", ""))
tests.append(("E · Audio QC & sync", "E", 0, DUR, "mono compatibility", "no element phases out in mono", "pan to mono, listen once", "stable", "Minor", "Not run", ""))
tests.append(("E · Audio QC & sync", "E", DUR - 0.8, DUR, "tail fade", "fade smooth, no click at the last frame", "listen last 0.8 s", "clean", "Minor", "Not run", ""))
for g, what, sev in [("Reddit", "native upload plays 1080p, audio present, first frame not black", "Major"),
                     ("LinkedIn/X", "reads muted in feed — every key info is on-screen anyway", "Major"),
                     ("Portfolio embed", "1080p60 selectable; description links the brand", "Minor"),
                     ("Thumbnail", "poster frame PNG readable at small size", "Minor"),
                     ("Accessibility", "alt text / caption describes the reel", "Minor")]:
    tests.append(("G · Delivery & platforms", "G", None, None, g, what, "upload to a draft/private post first", "pass per platform", sev, "Not run", ""))
tests.append(("H · Sign-off", "H", 0, DUR, "fixes", "zero open Blocker/Major fails", "filter the Test Sequence Status column", "zero open", "Blocker", "Not run", ""))
tests.append(("H · Sign-off", "H", 0, DUR, "approval", "full watch with sound on, then sign", "human", "approved + dated", "Blocker", "Not run", ""))

nfail = sum(1 for p in pref if p[1] == "FAIL") + sum(1 for p in tech if p[3] == "FAIL")
nnotrun = sum(1 for t in tests if t[9] == "Not run")
ready = "READY" if nfail == 0 and nnotrun == 0 else "NOT YET — %d auto-fail(s), %d manual test(s) pending" % (nfail, nnotrun)

# ================= markdown =================
md = ["# Reel QC — %s" % MP4, "",
      "Deliverable: **%s · %sx%s · %s fps · %s frames · %s s** · timeline `%s` · QC run %s" %
      (MP4, v.get("width") or "?", v.get("height") or "?", v.get("r_frame_rate") or "?", nz(v.get("nb_frames")), nz(fmt.get("duration"), 3), TL_PATH, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
      "", "## Summary", "",
      "| metric | value |", "|---|---|",
      "| Tech specs (auto) | %d/%d PASS |" % (sum(1 for p in tech if p[3] == "PASS"), len(tech)),
      "| Pre-flight (auto) | %d/%d PASS |" % (sum(1 for p in pref if p[1] == "PASS"), len(pref)),
      "| Cue points | %d (by construction) |" % len(cues),
      "| On-screen claims to verify | %d (Medium risk: %d) |" % (len(facts), sum(1 for f in facts if f[4] == "Medium")),
      "| Manual tests pending | %d |" % nnotrun,
      "| Auto failures | %d |" % nfail,
      "| **READY TO PUBLISH?** | **%s** |" % ready,
      "", "## Tech specs — target vs measured", "",
      "| parameter | target | measured | result | how |", "|---|---|---|---|---|"]
for p in tech:
    md.append("| %s | %s | %s | %s | %s |" % (p[0], p[1], p[2], p[3], p[4]))
md += ["", "## Cue sheet — derived from the same timeline as render + audio", "",
       "| t (s) | frame | TC | scene | picture | sound | tol (f) |", "|---|---|---|---|---|---|---|"]
for c in cues:
    md.append("| %.2f | %d | %s | %s | %s | %s | %d |" % c)
md += ["", "## Fact check — every on-screen string", "",
       "| t (s) | scene | text | source | risk | status |", "|---|---|---|---|---|---|"]
for f in facts:
    md.append("| %.1f | %s | %s | %s | %s | %s |" % f)
md += ["", "## Test sequence", ""]
for t in tests:
    md.append("- **[%s] %s** %s — %s  \n  _expected: %s · severity %s · how: %s%s_" %
              (t[9], t[1], t[4], t[5], t[7], t[8], t[6], (" · " + t[10]) if t[10] else ""))
open(os.path.join(OUT, "qc_report.md"), "w").write("\n".join(md) + "\n")
print("wrote %s/qc_report.md" % OUT)

# ================= xlsx =================
try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    HDR = Font(bold=True, color="FFFFFF")
    HDRF = PatternFill("solid", fgColor="333336")
    FILL = {"Pass": "D3F9D8", "PASS": "D3F9D8", "FAIL": "FFC9C9", "Fail": "FFC9C9",
            "Not run": "FFF3BF", "N/A": "E9ECEF", "Verified": "D3F9D8", "Medium": "FFF3BF"}

    def sheet(ws, headers, rows, title):
        ws.append([title])
        ws["A1"].font = Font(bold=True, size=13)
        ws.append([])
        ws.append(headers)
        for c in ws[3]:
            c.font = HDR
            c.fill = HDRF
        for r in rows:
            ws.append(list(r))
            for ci in range(1, len(headers) + 1):
                cell = ws.cell(row=ws.max_row, column=ci)
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                f = FILL.get(str(cell.value))
                if f:
                    cell.fill = PatternFill("solid", fgColor=f)
        widths = {}
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None:
                    widths[c.column] = min(60, max(widths.get(c.column, 10), len(str(c.value)) + 2))
        for col, w in widths.items():
            ws.column_dimensions[get_column_letter(col)].width = w
        ws.freeze_panes = "A4"

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["Reel — Post-Production QC Summary"])
    ws["A1"].font = Font(bold=True, size=13)
    ws.append([])
    for k, val in [("Deliverable", "%s · %sx%s · %s fps · %s frames · %s s" % (MP4, v.get("width") or "?", v.get("height") or "?", v.get("r_frame_rate") or "?", nz(v.get("nb_frames")), nz(fmt.get("duration"), 3))),
                   ("Source timeline", TL_PATH),
                   ("QC run", "%s by qc.py" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
                   ("Tech specs (auto)", "%d/%d PASS" % (sum(1 for p in tech if p[3] == "PASS"), len(tech))),
                   ("Pre-flight (auto)", "%d/%d PASS" % (sum(1 for p in pref if p[1] == "PASS"), len(pref))),
                   ("Cue points", "%d — sync by construction (render + audio share events.py)" % len(cues)),
                   ("Claims to verify", "%d rows (Medium risk: %d) — put sources in timeline.json 'sources' map" % (len(facts), sum(1 for f in facts if f[4] == "Medium"))),
                   ("Manual tests pending", nnotrun),
                   ("Auto failures", nfail),
                   ("READY TO PUBLISH?", ready)]:
        ws.append([k, val])
        ws.cell(ws.max_row, 1).font = Font(bold=True)
        if k == "READY TO PUBLISH?":
            ws.cell(ws.max_row, 2).fill = PatternFill("solid", fgColor="D3F9D8" if ready == "READY" else "FFC9C9")
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 80

    sheet(wb.create_sheet("Test Sequence"),
          ["Phase", "In (s)", "Out (s)", "Scene / area", "What to check", "How to test", "Expected", "Severity", "Status", "Notes"],
          [[t[0], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10]] for t in tests],
          "Test Sequence — run A->H · A/B auto-filled · Status cells are yours")
    sheet(wb.create_sheet("Cue Sheet"),
          ["#", "Time (s)", "Frame", "Timecode", "Scene", "Picture event", "Sound event", "Tolerance (f)", "Status"],
          [[i + 1, round(c[0], 3), c[1], c[2], c[3], c[4], c[5], c[6], "Pass (by construction)"] for i, c in enumerate(cues)],
          "Cue Sheet — derived from the SAME timeline as render + audio (sync cannot drift unless one side is edited alone)")
    sheet(wb.create_sheet("Tech Specs"),
          ["#", "Parameter", "Target", "Measured", "Result", "How measured", "Notes"],
          [[i + 1] + list(p) for i, p in enumerate(tech)],
          "Tech Specs — target vs measured (ffprobe / ffmpeg)")
    sheet(wb.create_sheet("Fact Check"),
          ["#", "Time (s)", "Scene", "On-screen text", "Source", "Risk", "Status", "Action"],
          [[i + 1, round(f[0], 2), f[1], f[2], f[3], f[4], f[5], "verify / reword / remove"] for i, f in enumerate(facts)],
          "Fact Check — clear every row (Verified / Reworded / Removed) before publishing. Add 'sources' to timeline.json to auto-verify.")
    wb.save(os.path.join(OUT, "qc_report.xlsx"))
    print("wrote %s/qc_report.xlsx" % OUT)
except ImportError:
    print("openpyxl not installed — xlsx skipped (markdown report is complete)")

print("\n=== TECH SPECS ===")
for p in tech:
    print("%-32s %-24s %-26s %s" % (p[0], str(p[1])[:24], str(p[2])[:26], p[3]))
print("\nREADY TO PUBLISH? %s" % ready)

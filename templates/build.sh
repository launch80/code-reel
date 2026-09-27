#!/usr/bin/env bash
# Full build: lossless frames -> audio -> final MP4 (single lossy encode).
#
# Env: OUT=reel.mp4        output name
#      OUT_W/OUT_H         final size (default 1920x1080; use 1080x1920 for 9:16)
#      DPR                 must match render.py (2 = supersampled, 1 = 1:1)
#      CRF                 quality (default 17; lower = better/bigger)
set -e
cd "$(dirname "$0")"
# use the project venv if present
PY="python3"; [ -x .venv/bin/python ] && PY=".venv/bin/python"
DPR="${DPR:-2}"
OUT="${OUT:-reel.mp4}"
OW="${OUT_W:-1920}"; OH="${OUT_H:-1080}"
CRF="${CRF:-17}"
"$PY" render.py video
"$PY" audio.py
# Video: frames.mkv is lossless RGB (full range, sRGB). Downscale 2x -> 1x with
# Lanczos, convert to limited-range yuv420p, and TAG the stream via setparams
# (the -colorspace/-color_trc/-color_primaries CLI flags alone leave primaries/
# transfer untagged in recent ffmpeg — players then guess BT.601 and colors shift).
# Audio: gentle compression + two-pass loudnorm to -14 LUFS / -1.5 dBTP, then a
# +1.5 dB trim into a limiter (qc.py measures -14.6 LUFS / -1.5 dBTP through
# this chain — plain loudnorm alone can't reach the target on short files).
# 48 kHz stereo AAC 256k, faststart for streaming.
LN="acompressor=threshold=-18dB:ratio=4:attack=5:release=250,loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.5dB,alimiter=limit=0.84"  # fallback
M=$("$PY" - <<'PY' 2>/dev/null
import json, re, subprocess
p = subprocess.run(["ffmpeg", "-hide_banner", "-i", "audio.wav", "-af",
                    "acompressor=threshold=-18dB:ratio=4:attack=5:release=250,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True)
m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
if not m:
    raise SystemExit
d = json.loads(m.group(0))
print("acompressor=threshold=-18dB:ratio=4:attack=5:release=250,"
      "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s"
      ":measured_thresh=%s:offset=%s:linear=true,"
      "volume=1.5dB,alimiter=limit=0.84" %
      (d["input_i"], d["input_tp"], d["input_lra"], d["input_thresh"], d["target_offset"]))
PY
)
[ -n "$M" ] && LN="$M"
ffmpeg -y -loglevel error -i frames.mkv -i audio.wav \
  -vf "scale=${OW}:${OH}:flags=lanczos:in_range=pc:out_range=tv,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" \
  -c:v libx264 -preset slow -crf "$CRF" -profile:v high -g 150 \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -af "$LN" -ar 48000 -ac 2 \
  -c:a aac -b:a 256k -movflags +faststart "$OUT"
echo "done -> $OUT"

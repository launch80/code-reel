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
ffmpeg -y -loglevel error -i frames.mkv -i audio.wav \
  -vf "scale=${OW}:${OH}:flags=lanczos:in_range=pc:out_range=tv,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" \
  -c:v libx264 -preset slow -crf "$CRF" -profile:v high -g 150 \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 256k -movflags +faststart "$OUT"
echo "done -> $OUT"

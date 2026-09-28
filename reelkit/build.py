"""build — the ONE lossy encode: frames.mkv + audio.wav -> reel.mp4.

Lanczos downscale (DPR 2 -> 1), full->limited range, yuv420p, BT.709 tags via
setparams (CLI color flags alone leave primaries/trc untagged), H.264 High,
AAC 48 kHz. Loudness is a closed loop: measure, normalize to -14 LUFS, verify,
and correct once more if the short-file bias leaves it outside -14 +/- 0.7.
"""
import json
import os
import re
import subprocess


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("ffmpeg failed: %s\n%s" % (" ".join(cmd[:6]), r.stderr[-800:]))
    return r


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    s = r.stderr.split("Summary:")[-1]
    g = lambda k: float(re.search(k + r"\s*:\s*(-?[\d.]+)", s).group(1))
    return {"I": g("I"), "LRA": g("LRA"), "TP": g("Peak")}


def encode(proj, out=None, w=None, h=None, crf=17, target=-14.0):
    rd = os.path.join(proj, ".reel")
    tl = json.load(open(os.path.join(rd, "timeline.resolved.json")))
    out = out or os.path.join(proj, "reel.mp4")
    w, h = w or tl["w"], h or tl["h"]
    frames, wav = os.path.join(rd, "frames.mkv"), os.path.join(rd, "audio.wav")
    for f in (frames, wav):
        if not os.path.exists(f):
            raise RuntimeError("missing %s — run render/audio first" % f)
    vtmp = os.path.join(rd, "video_only.mp4")
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", frames,
          "-vf", "scale=%d:%d:flags=lanczos:in_range=pc:out_range=tv,format=yuv420p,"
                 "setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" % (w, h),
          "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-g", str(int(tl["fps"]) * 2),
          "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-an", vtmp])
    tgt, tp = target, -1.6
    got = None
    for attempt in range(4):
        # loudnorm (dynamic) has a true-peak limiter; short files land a little off target,
        # so we measure the ENCODED output and nudge the target until it is inside the gate.
        _run(["ffmpeg", "-y", "-loglevel", "error", "-i", vtmp, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
              "-af", "acompressor=threshold=-21dB:ratio=3.5:attack=4:release=140:knee=4,loudnorm=I=%.2f:TP=%.2f:LRA=9,aresample=48000" % (tgt, tp),
              "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", out])
        got = measure(out)
        if abs(got["I"] - target) <= 0.6 and got["TP"] <= -1.0:
            break
        tgt = max(-24.0, min(-9.0, tgt + (target - got["I"]) * 0.9))
        if got["TP"] > -1.0:
            tp = max(-6.0, tp - (got["TP"] + 1.0) - 0.4)       # AAC adds inter-sample overshoot: aim lower
    os.remove(vtmp)
    return out, got

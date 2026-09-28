# QC

`reel.py qc <proj>` (also the last step of `run`) writes `.reel/qc_report.md` + `.reel/qc_report.xlsx`
(Summary · Test Sequence · Cue Sheet · Tech Specs · Fact Check).

Measured (can FAIL): size, fps, **decoded** frame count, duration, H.264 High, yuv420p,
BT.709 tags ×3, tv range, fast-start, AAC 48 kHz stereo, A/V length, black segments
(fades only), freezes, integrated loudness −14±1 LUFS, true peak ≤ −1 dBTP, LRA;
compile clean; every on-screen number sourced; layout audit (overlap / off-canvas /
blank); title-safe; novelty. Sync is by construction (render and audio read the same
compiled events).

Pre-filled for a human (status Not run, with timecodes): each scene ("would this frame
only belong to THIS video?"), each transition window, audio balance / small speakers /
mono / tail, delivery per platform, sign-off. READY only when auto-fails are 0 and every
human row is resolved.

Loudness is closed-loop in `build`: compress → loudnorm → encode → measure the MP4 →
adjust target/true-peak ceiling → re-mux (video encoded once).

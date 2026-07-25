# GoPro MAX / MAX2 support in MGT-python and ambiscape — design

Approved approach: pure remap tables + stock ffmpeg for video (MGT), and
best-audio-stream selection for ingest (ambiscape). No new binary or build
dependencies in either toolbox. Documentation-driven (no sample files
available yet): everything layout-specific is probed from the file, synthetic
fixtures stand in for real recordings, and unknown layouts fail with a
message that says exactly what was found.

## Facts and assumptions

- A GoPro MAX `.360` contains **two H.265 video tracks** (4096×1344 each) in
  GoPro's custom EAC cubemap layout: each track is a strip of three 1344×1344
  cube faces plus unstitched overlap zones (4096 − 3·1344 = 64 px of overlap
  per strip). Strip 1 holds left/front/right; strip 2 holds up/back/down
  (rotated). The authoritative per-pixel mapping is Paul Bourke's
  `max2sphere` (paulbourke.net/panorama/gopromax2sphere/, C source on
  GitHub); the implementation ports that math to numpy.
- Audio in the MAX `.360`: one **stereo AAC** stream (189 kb/s) and one
  **4-channel PCM s32 planar** stream (6,144 kb/s), plus three data streams
  (GPMF metadata, TCD timecode, SOS recovery). The `.LRV` proxy carries its
  own, different stereo AAC. Sources: the owner's format analysis (arj.no
  2023-05-25) and the lab's two studies — Guo, Riaz & Jensenius (SMC 2024,
  four-camera video comparison) and Riaz, Guo & Jensenius (spatial-audio
  comparison).
- **Verified fact (Riaz et al.):** the MAX 4-channel track is first-order
  B-format **AmbiX (ACN/SN3D, W-Y-Z-X)** — confirmed empirically via
  channel-amplitude norms. ambiscape's existing 4-channel → `ambix` mapping
  is therefore correct for GoPro. Garmin VIRB 360 4-channel is also AmbiX
  (with an empty Z — "planar spatial audio") and works as-is.
- **Insta360 caveat (Riaz et al.):** X3-era recordings may carry a
  4-channel AAC stream that is *not* B-format (amplitude norms don't match;
  mic orientation undocumented). ambiscape's channel-count heuristic will
  still label it `ambix`; the ingest docstring documents this mislabeling
  risk and recommends treating Insta360 4-channel spatial metrics as
  unreliable until the layout is established.
- **Chunking:** GoPro splits recordings at 4 GB and Insta360 at 1 minute;
  MGT already merges chunks losslessly (concat → MKV, from the SMC 2024
  work). The GoPro probe/flatten path must accept those merged MKVs, not
  only `.360` files — covered by making the probe container-agnostic and by
  a test case.
- **Free win, docs only:** the MAX `.LRV` is a single-file dual-fisheye
  (1408×704) — `stitch_dual_fisheye`/`v360` paths shipped this week already
  handle that projection for quick previews.
- **MAX2 is unknown territory:** presumed the same two-track EAC layout at
  higher (8K-class) resolution. Support is *probe-driven*: if a MAX2 file
  matches the two-strip pattern at any resolution, everything works
  unchanged; if the layout differs, the probe raises with the observed track
  inventory. MAX2 support is labeled experimental until a real file passes.

## MGT-python: `musicalgestures/_gopro360.py` (new module)

Three units, mirroring the Insta360 stitcher's structure (`_360video.py`):

1. `probe_gopro360(path) -> dict` — ffprobe the container; identify the two
   video streams (indices, width, height), derive face size `h` and per-seam
   overlap `(w − 3h) / 2`, and identify all audio streams (index, codec,
   channels). Raises `ValueError` naming the actual streams found when the
   file does not match the two-strip pattern (h·3 ≤ w, equal-sized tracks).
2. `build_gopro_remap(track_w, track_h, out_w, out_h, tmpdir) -> (xmap.pgm,
   ymap.pgm, blend_mask.png)` — numpy port of the max2sphere mapping from
   equirect output pixels to (stacked-strip) input pixels, written as
   16-bit PGM remap tables for ffmpeg's `remap` filter, plus a feathered
   blend mask for the four unstitched face seams. Pure numpy; sized from the
   probe, so MAX2 resolutions generate their own tables.
3. `flatten_gopro360(path, target_name=None, width=None, height=None,
   crf=21, preset="fast", print_cmd=False) -> str` — one ffmpeg run:
   `vstack` the two video tracks → `remap` with the generated tables →
   equirect H.264, mapping the best audio stream (most channels, AAC-encoded
   in the output). Default output size derived from input:
   `width = 3 · track_h`, `height = width // 2` (4032×2016 for MAX).
   Follows `stitch_dual_fisheye`'s conventions (generate_outfilename,
   ffmpeg_cmd progress, single-frame mask input, `-shortest` semantics).

Wiring: `Mg360Video.convert_projection` replaces the dead
`gopromax-conversion-tools/scripts` branch with `flatten_gopro360`; the
empty scripts directory is removed. `CAMERA` registry gains
`"gopro max2": {"ext": "360", "projection": Projection.gopro_360}`.

Tests (`tests/test_gopro360.py`): a synthetic fixture renders a known
equirect test pattern, inverse-maps it in numpy into two EAC strip videos,
muxes them with a stereo AAC track plus a 4-channel PCM track into a
`.360`-named MOV; then (a) probe returns the right geometry, (b)
`flatten_gopro360` output correlates > 0.9 with the source pattern away from
the poles, (c) a single-video-track file raises the informative ValueError.
The inverse mapping in the fixture and the forward mapping in the module are
written independently (fixture from the equirect→cube math, module from the
cube→equirect direction) so the round trip is a real check, not an identity.

## ambiscape: best-audio-stream selection in `_ensure_readable` (io.py)

Replace the fixed `-map a:0` with stream selection: ffprobe the container's
audio streams (`codec_name`, `channels`); choose the stream with the most
channels whose codec ffmpeg can decode (skip `none`/unknown codecs — the
iPhone APAC case); tie-break to the lower stream index. Decode to the cached
WAV as today, except the sample format follows the source: sources deeper
than 16-bit (the MAX's s32 ambisonic track) decode to `pcm_s24le`, others
stay `pcm_s16le`. Behavior for single-audio-stream files is unchanged; the
cache key/invalidation is unchanged. The module docstring gains two notes:
the stream-selection rule, and the Insta360 4-channel-is-not-B-format
caveat. Version bumps to 0.19.0 (user-facing ingest change).

Tests (`tests/test_io_features.py`): a fixture MOV named `.360` with a
stereo AAC stream *first* and a 4-channel PCM stream second → `open_session`
yields a 4-channel `ambix` take; a stereo-only container still ingests as
before.

## Error handling

- MGT probe failure: `ValueError("not a GoPro two-strip .360: found …")`
  listing the stream inventory — the message a MAX2 owner needs to file a
  useful report.
- ambiscape: if no audio stream is decodable, the existing RuntimeError path
  stays; the selection never silently falls back to a worse stream than
  today's `a:0` (a:0 is the floor).

## Out of scope (YAGNI)

GPMF metadata extraction, .LRV handling beyond what already works, GoPro
battery/HERO formats, gyro-based horizon leveling, and any GUI. No changes
to the `soundscape` adapter — it inherits the ingest fix for free.

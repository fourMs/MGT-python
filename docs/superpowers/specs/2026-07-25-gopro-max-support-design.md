# GoPro MAX / MAX2, Ricoh Theta legacy, and Garmin VIRB 360 support in MGT-python and ambiscape — design

Approved approach: pure remap tables + stock ffmpeg for video (MGT), and
best-audio-stream selection for ingest (ambiscape). No new binary or build
dependencies in either toolbox. Documentation-driven (no sample files
available yet): everything layout-specific is probed from the file where
detection is possible, synthetic fixtures stand in for real recordings, and
unknown layouts fail with a message that says exactly what was found. The
same remap-table machinery serves both legacy formats: GoPro's custom EAC
strips and the Ricoh Theta S single-file dual-fisheye.

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
- **Garmin VIRB 360 (SMC 2024 §3.3 + Riaz et al.):** the friendly one.
  Normal recordings are already **in-camera-stitched equirectangular**
  (`.MP4` 3840×2160 H.264 + `.GLV` 1280×720 proxy, one video + one audio
  stream each) — no flattening needed, and MGT's `CAMERA` registry already
  lists it as `erp`. ambiscape ingests both since Phase 1 added `.glv`; the
  single audio stream is 4-channel AAC AmbiX, so the existing 4-ch → ambix
  mapping is right. Three format quirks worth capturing:
  (a) the **Z channel is empty** ("planar spatial audio") — azimuth is
  valid, elevation is meaningless; documented so spatial metrics are read
  accordingly; (b) the **RAW 5.7K mode** writes the two 200° hemispheres as
  *separate fisheye files* — exactly the two-file case `stitch_dual_fisheye`
  already handles (its FOV calibration sweep must extend to ~205° to cover
  Garmin's 200° lenses; today's candidate list tops out at 203); (c) VIRB
  Edit's "360" export writes a 4-channel FOA track with only the first
  channel non-zero (a software bug found by Riaz et al.) — prefer in-camera
  originals over VIRB Edit exports; documented in the ingest notes.
- **Ricoh Theta S (legacy, SMC 2024 §3.4 + the owner's 2020 remap
  workflow):** one `.MP4` with a single H.264 video stream, 1920×1080 —
  16:9, not 2:1: two side-by-side fisheye circles with a black band at the
  bottom, and an unusual twist: **each spherical view is rotated 90° in
  plane**, which is why plain `v360=dfisheye` cannot unwrap it and the
  historical route was hand-made xmap/ymap PGM remap files
  (ThetaS-video-remap). Audio is mono AAC at 32 kHz — ambiscape ingests it
  already (mono mode); no audio work needed. Unlike GoPro, the layout is
  not reliably auto-detectable (any 16:9 MP4 could be anything), so Theta
  flattening is explicitly invoked, never probed-and-guessed.

## MGT-python: `musicalgestures/_remap360.py` (new module)

One module owns remap-table flattening for legacy 360 formats. A shared
`write_remap_pgm(xmap, ymap, tmpdir)` helper writes 16-bit PGM tables for
ffmpeg's `remap` filter; two format-specific generators feed it. GoPro
units, mirroring the Insta360 stitcher's structure (`_360video.py`):

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

Theta units in the same module:

4. `build_theta_remap(in_w, in_h, out_w, out_h) -> (xmap, ymap)` — mapping
   from equirect output pixels to the Theta S frame: two fisheye lenses
   side by side (each nominally 190° FOV), each with the 90° in-plane
   rotation, ignoring the black band below 960 px. Lens FOV and per-lens
   roll are parameters with Theta S defaults, so a real file can be
   fine-tuned the way the Insta360 FOV calibration works.
5. `flatten_theta360(path, target_name=None, width=1920, height=960,
   crf=21, preset="fast", print_cmd=False) -> str` — one ffmpeg run: `remap`
   with the generated tables → equirect H.264 (1920×960 default, matching
   the official app's export size), audio stream passed through as AAC.
   Explicit invocation only (no auto-probe — see facts).

Garmin work in existing modules (no new units): widen
`calibrate_dual_fisheye_fov`'s default candidate list to reach 205° so RAW
5.7K hemisphere pairs calibrate, and note the Garmin RAW case in
`stitch_dual_fisheye`'s docstring. Registry entry for the camera exists.

Wiring: `Mg360Video.convert_projection` replaces the dead
`gopromax-conversion-tools/scripts` branch with `flatten_gopro360`; the
empty scripts directory is removed. `CAMERA` registry gains
`"gopro max2": {"ext": "360", "projection": Projection.gopro_360}` and
`"ricoh theta s": {"ext": "MP4", "projection": Projection.dfisheye}` with a
comment pointing at `flatten_theta360` for the legacy rotated dual-fisheye
files (plain `v360=dfisheye` does not handle the 90° in-plane rotation).

Tests (`tests/test_remap360.py`): a synthetic fixture renders a known
equirect test pattern, inverse-maps it in numpy into two EAC strip videos,
muxes them with a stereo AAC track plus a 4-channel PCM track into a
`.360`-named MOV; then (a) probe returns the right geometry, (b)
`flatten_gopro360` output correlates > 0.9 with the source pattern away from
the poles, (c) a single-video-track file raises the informative ValueError.
For Theta: the same equirect pattern inverse-mapped into a synthetic
1920×1080 dual-fisheye frame (two rotated circles + black band) →
`flatten_theta360` → correlation > 0.9 away from poles and seams. In both
cases the fixture's inverse mapping and the module's forward mapping are
written independently (fixture from the equirect→lens math, module from the
lens→equirect direction) so the round trips are real checks, not
identities.

## ambiscape: best-audio-stream selection in `_ensure_readable` (io.py)

Replace the fixed `-map a:0` with stream selection: ffprobe the container's
audio streams (`codec_name`, `channels`); choose the stream with the most
channels whose codec ffmpeg can decode (skip `none`/unknown codecs — the
iPhone APAC case); tie-break to the lower stream index. Decode to the cached
WAV as today, except the sample format follows the source: sources deeper
than 16-bit (the MAX's s32 ambisonic track) decode to `pcm_s24le`, others
stay `pcm_s16le`. Behavior for single-audio-stream files is unchanged; the
cache key/invalidation is unchanged. The module docstring gains three
notes: the stream-selection rule; the Insta360 4-channel-is-not-B-format
caveat; and the Garmin notes (empty Z ⇒ elevation metrics meaningless;
prefer in-camera originals over VIRB Edit's bugged FOA exports). Version
bumps to 0.19.0 (user-facing ingest change).

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
battery/HERO formats, gyro-based horizon leveling, and any GUI. Newer Ricoh
Theta models (X and successors) already record standard equirectangular —
the existing `erp` registry entry covers them; only the legacy Theta S
dual-fisheye needs the remap path. No changes to the `soundscape` adapter —
it inherits the ingest fix for free.

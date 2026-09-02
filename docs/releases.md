# Release Notes

The current stable release is **MGT-python 1.31.0**.

Install or upgrade from PyPI:

```bash
pip install --upgrade musicalgestures
```

## Full changelog

The complete, version-by-version history—including every Added / Changed / Fixed entry—is
maintained in the [CHANGELOG](https://github.com/fourMs/MGT-python/blob/master/CHANGELOG.md),
which is the single source of truth for release notes.

## Recent highlights

### 1.31.0

Eye tracking joins the toolbox, on the video's clock.

Pupil Labs Neon exports from Pupil Cloud — gaze at 200 Hz, 3D eye states, IMU,
fixations, saccades, blinks and event markers — are read by the new `_pupillabs`
module and placed on a video's frame clock by naming the event the video starts
at. `pupil_to_frames` bins every stream to the frames (gaze position and angular
velocity, event flags with the export's ids, pupil size masked around blinks,
head rotation and orientation), `eyetracking_rates` counts events by onset per
bin, and `gazegram` draws where the wearer looked as the gaze counterpart of a
motiongram. Bound on `MgVideo` as `eyetracking()`, `gazegrams()` and
`eyetracking_timeline()`. Written for a live-painting concert in which the
painter wore the glasses for an hour while following two musicians. Also in this
release: the cross-modal pairings are renamed to match their level of
description (`motion_audio_coupling()`, `warp_audiomotion_beats()`), with the old
names kept for one release.

### 1.30.0

The static row: postures found, poses proposed.

The toolbox's motion/action/gesture ladder gains its static counterpart —
position, posture, pose, following *Sound Actions* and a five-field terminology
review. The new `_postures` module cuts landmark trajectories into held
configurations (`segment_postures`, on a Movement–Hold stationarity criterion in
body-normalised units), groups the configurations a body returns to
(`key_postures`), gives a recording's habitual carriage (`average_posture`), and
proposes poses by example as labels on postures (`match_postures`) — segmentation
kept apart from recognition, exactly as in `_actions`. Underneath,
`normalise_poses` now recognises the landmark topology by count, so MediaPipe,
YOLO and the OpenPose skeletons all feed the same higher-level analysis, and
stationarity is measured jitter-robustly after a seated dancer's 1 px knee
flutter taught the criterion the difference between a detector trembling and a
body moving.

### 1.29.0

The plate distrusts its own refinement, and the associator learns to look.

`room_plate` now measures how much its refinement changed the plate and backs off
with a warning when the change is material — on standstill material the frames
most like the first plate are the ones with the subject in place, so refinement
was concentrating the subject rather than cleaning the room; a new
`max_refine_change` argument sets the tolerance. And `associate_fragments` gains
appearance: `fragment_embeddings` collects one appearance vector per fragment, an
ambiguous crossing is decided only when one candidate is strictly more separated
than the material's own spread, and refusal remains output.

### 1.28.0

The third family, and fragments that become movers.

RTMPose joins as the third pose extractor on the same trajectory contract
(`pip install musicalgestures[rtmpose]`) — rtmlib over ONNX runtime, Apache
end to end, with the separate person detector that held 100% detection on a dark
stage. And `associate_fragments` chains track fragments into persistent movers
with position and time only, refusing where honesty demands: a crossing at a
fragment boundary becomes a recorded break, never a guess.

### 1.27.0

The qualities of movement, and identities that outlast confidence.

The Effort layer is MGT's own operationalisation of Laban's four factors — Time,
Weight, Space, Flow — as continuous windowed indices with every claim measured
first, plus Laban's eight basic effort actions as median-anchored proposals
(`musicalgestures._effort`; the docs' Effort page has the full account and the
limits). And YOLO pose gains per-person tracking: every identity separately via
`extract_pose_tracks_yolo`, or `track=True` to follow the most persistent body —
the cure for the per-frame selection flipping between two dancers, or between a
dancer and their projection on a screen.

### 1.26.0

The last deprecation batch, and a second pair of eyes.

`extract_pose_landmarks_yolo` is the Ultralytics twin of the MediaPipe extractor, on
the same trajectory-array contract, so two detectors can be compared on a shared
clock (`pip install musicalgestures[yolo]`). `motiongram_data` speaks x and y like
the rest of the toolbox, with the old words warning until 2.0 — which completes the
deprecation set: everything scheduled for removal now warns. And the motion envelope
(`MgMotionVectorViews.magnitude`) is documented as what it is: the encode's own
~12.6 Hz cadence for a tenth of a decode's cost, with its measured limits stated.

### 1.25.0

The room's texture, the floor made affordable, and pages of a time range.

`texture_mask` says which cells of a picture carry enough texture to trust motion
vectors on: an encoder's motion search is unconstrained where nothing textures the
block, so masking the flattest cells of the room removes motion that was never a
measurement. The zoomable page plays its recording (`player=`), builds for any video
in one call (`MgVideo.zoompage()`), and pages any time range on its own clock
(`start_s=`). And measuring a noise floor no longer holds every magnitude in memory:
a bounded uniform sample keeps the quantile and drops the 8 GB.

### 1.24.0

The grams put right, in number and in name.

Motion-vector displacements are corrected for the reference cadence: FFmpeg's `source`
carries only the sign of a vector's reference, so a P-frame following a run of B-frames
had reported its whole multi-frame displacement as one frame's — 3× to 4× over on
B-heavy encodes. Every motion-vector number on such encodes changes; arrays saved by
earlier versions should be re-derived.

The grams are drawn in the classic orientations and named by the position axis each
keeps: the x-motiongram keeps horizontal position, shows sideways travel, and is the
tall picture with time downward; the y-motiongram keeps vertical position and is the
wide one. Every picture-named attribute keeps working with a warning until 2.0.

`multishot(animate=True)` writes the chronophotograph as a looping GIF of its own
build-up, and `zoomable_page` gains an audio band — waveform and spectrogram on the
shared clock — plus named, switchable video strips.

And `extract_tracks_parallel` no longer leaks one live ffmpeg per finished chunk; 51 of
them once held 23 GB and took a 32 GB machine down mid-extraction.

### 1.23.0

Postures over time, and a capability that turned out not to be there.

`pose_timeline` draws postures and trajectories in three flat views: postures at regular
instants side by side, skeletons where they actually stood, and per-region joint angles so
**a held posture is a flat band** — which a posegram cannot show, because it carries speed
and a held limb has none. Gaps stay gaps rather than being interpolated into invented
posture.

`multishot` absorbed `stroboscope()`, which made the same picture a different way; that name
still works, warns, and goes at 2.0. `plate()` and `multishot()` are now methods like every
other view.

And **MediaPipe segmentation had been silently dead since MediaPipe 0.10** — the Solutions
API it asked for was removed, the lookup raised, a bare `except` swallowed it, and every
caller got background subtraction while being told otherwise. Rebuilt on the Tasks API, and
the fallback now says so out loud.

Note that **posegram's rows are reordered** — head, torso, arms, hands, legs — so a posegram
made before this release is not comparable row for row with one made after.

### 1.22.0

Many moments of a recording in one picture.

`multishot` recovers the room as a plate, cuts bodies out of frames spread through the
recording, and lays them all back onto it. **Frames are chosen for separation rather than at
intervals** — evenly spaced frames put bodies on top of each other as often as not, and two
overlapping silhouettes read as one smear rather than as two moments.

MGT has had chronophotography since 1.6 in `stroboscope()`, which samples evenly onto a mean
average frame and tints each silhouette by time. The two are documented side by side: reach
for `stroboscope()` when the time order matters and MediaPipe segmentation is wanted, and
for `multishot` when the bodies must not overlap and the background must be a genuinely
empty room rather than a mean that keeps a ghost of everyone who crossed.

It assumes a subject who moves through space, and says so: on a seated pianist it returns
moving limbs stacked in one place, which is the picture reflecting the recording.

### 1.21.0

A gate measured from the recording, and a room that is not one moment of it.

`noise_floor` takes a motion threshold from the material instead of a guess. The room plate
says which pixels have nobody in front of them, and whatever their frame-to-frame difference
shows, nothing there moved --- so the gate is a quantile of that, and the parameter is a
**false-positive rate** rather than a magnitude. `frame_difference_floor` returns it in grey
levels, `motion_vector_floor` in pixels of displacement. **It can refuse**: Otsu will split
pure noise and report a threshold with no sign of distress, so this declines when there are
too few samples or when the gate would keep almost none of the moving part, and a refusal
carries no number to reach for by accident.

Equalising the false-positive rate makes spatial **maps** comparable across recordings, and
makes **magnitudes** less comparable, since each recording lands at its own operating point.
Both approaches are kept: fixed thresholds when magnitudes are compared, measured floors when
pictures are.

`room_plate` now spreads its second pass over the recording. The emptiest frames are the right
ones to build a room from, but they cluster in whatever stretch nobody was working --- and a
stepladder that stood in one room for ten minutes of a two-hour session became part of "the
room", so that region read as occupied 18.6 per cent of the time. **This changes occupancy
figures**, by 0.2 to 1.3 per cent of pixels on six test recordings.

Motion vectors and pose also gained gates in their own units --- pixels of displacement, and
landmark confidence --- both **off by default**, since a gate switched on by default would
silently change results already computed.

### 1.18.0

The room, and what in a recording is not the person you are studying.

`room_plate` recovers the empty room as a per-pixel median over sampled frames --- median and
not mean, because a mean keeps a faint ghost of everyone who crossed and subtracting a ghost
leaves holes shaped like people. `occupancy_track` then says how much of the frame anybody
fills, which answers what quantity of motion cannot: a dancer standing still has no motion
and plenty of occupancy.

`restless_map` marks the pixels that change whatever is in front of them --- a screen showing
a video call, a window, somebody sitting at a table --- by median absolute deviation rather
than range, because a screen changes in nearly every frame while a dancer occupies a pixel
occasionally, and a range marks both alike. On the corpus this was written for, that
non-dancer motion is 2.8 to 7.1 per cent of the total.

`soundscape_features` now takes a **video** and not only an ambiscape session folder, and
carries the spectrum rather than level alone: centroid, flatness, peak, diffuseness and ten
octave bands, all on the same 1 Hz grid so they still join a motion series.

### 1.17.0

Figures that know about annotations, and one page that zooms.

Everything else in this toolbox for looking at a long recording is about the signal ---
motiongrams, videograms, self-similarity, tempograms, contact sheets. `Hierarchy` and the
ELAN exporter sat on the other side of a gap almost nothing crossed, and for somebody
annotating hours of video that crossing is the tool. `filmstrip` puts keyframes on the time
axis above the tiers. `concordance` puts every instance of one category side by side, which
is the linguist's concordance applied to video. `tier_map` draws every tier as a density
band, empty ones included. `structure_map` draws a coding on a self-similarity matrix.

`zoomable_page` writes one self-contained offline HTML file that zooms from a whole session
down to a single action, and says on the picture when you have zoomed past the data it
contains rather than drawing a smooth line that is not there.

`structure_map` carries a warning worth reading before use: it did not work on the corpus
it was written for until its features were changed, and the docstring gives the numbers.

### 1.16.0

Two detectors for things a recording contains besides motion, each shipped only because it
was measured first.

`laughter_segments` finds where laughter probably is, using the six AudioSet laughter
classes at a two-second window. `_voice` argues against a tagger for speech, and was right
to: on the same corpus a clip-level tag called dancers' breathing `Snort`, `Gasp`, `Animal`
and `Horse`. Both objections were about minute-long clips. Judged against 79 hand-coded
laughs, this reaches ROC AUC 0.823 against a loudness baseline's 0.741, and it says where
laughter is and nothing else --- not who laughed, or why.

`co_accentuation` asks whether motion accents land on sound accents, after Serdar and
Jensenius (MOCO '26): each motion peak tested for an audio onset within a tolerance. Two
additions to the published measure, both because a raw fraction of coincidence rises with
onset density: every index is judged against a circular-shift null, and a window with no
motion peaks reports NaN rather than zero, because "nothing was coordinated" and "nothing
was asked" are different answers.

### 1.15.0

Tools for building annotation material a person will work in, and for putting several
researchers' annotations on one clock.

`align_by_audio` locates a short recording inside a long one by loudness envelope, which
is how a hand-cut excerpt or a second camera is placed on the session's clock. It probes
rather than correlating whole files, because a file named `Cut` may be spliced and only
independent windows reveal that, and it summarises by the offset that recurs rather than
the median, because when most probes match nothing the middle of the list is nonsense.

`to_elan` can now write independent tiers instead of nesting every level inside the
previous one --- speech is not inside motion --- and can embed controlled vocabularies so
an annotator picks from a list instead of typing `ENJOYMENT`, `Enjoyment` and `enjoyment`
into one session. `read_elan_csv` reads ELAN's exported text and keeps the provenance line
saying which media the times belong to.

`lagged_correlation` reports a correlation across a lag range with both a
multiple-comparison correction and an effective sample size, because neighbouring samples
of a smooth envelope are not independent observations and treating them as such turns
autocorrelated noise into a finding. `cooccurrence_table` and `label_by_overlap` say which
annotation layers coincide and by how much. `render_timeline` can shade a span's extent
rather than only marking where it began.

### 1.14.2

`get_framecount` allowed ffprobe a flat ten seconds and, on timeout, escalated to
`-count_frames`, which fully decodes and is slower --- so that timed out too and the call
raised. **MGT could not open a video longer than about twenty minutes**, a ceiling on length
with nothing to do with any analysis. The allowance scales with the file now, and a timeout
falls back to the container's `nb_frames` with a warning instead of escalating. No measured
value changes.

### 1.14.1

Motion extraction is linear in frame count again. Every accumulator grew with `np.append`
inside the per-frame loop, which copies the whole array each time --- O(n^2) in frames, and
quadratic in bytes for the motiongrams. On 1080p that was 69 s, 148 s and 366 s for 30 s,
60 s and 120 s of video, extrapolating to about 215 hours for a 2 h 38 min recording; it is
now 64 s, 123 s and 242 s. **Output is byte-identical**, so no result changes.

### 1.14.0

Multi-view pose fusion: `fuse_pose_views` brings MediaPipe world landmarks from two or more
uncalibrated cameras into one consensus skeleton, with the cross-view residual in millimetres as a
quality measure. An `Action` layer gives motion-to-meaning work a place to put measured features
and claimed labels side by side. `motion_mp()` is retired --- it raised on its first call and had
never worked --- and the mypy step now blocks merges, having gone from 248 errors to zero.

### 1.13.0

Every result an analysis method stashes on `MgVideo` is declared on the class now and named after
what it holds, so an editor completes them and a type checker follows them. Nine attributes were
renamed and keep their old names as deprecated aliases until 2.0.

Two of those were bug fixes rather than tidying. `pixelarray` was both the method computing the
frame average and the name its result was stored under, so the result hid the method and a second
call raised `TypeError`; the result is `frameaverage_image` now. And the package no longer silences
every warning in the process at import, which had been hiding a crash on audio files over an hour
and tick labels losing a digit on whole minutes.

### 1.12.1

- **A test-only fix, released so the tag is green.** `v1.12.0` points at a commit whose Windows CI
  failed on a test fixture using `os.link` across drives. The package was correct; the tag was
  misleading. The publish workflow now refuses to run unless CI passed on the exact commit.

### 1.12.0

- **`contact_sheet()`** tiles one frame from each of many videos, so a corpus can be scanned by
  eye. `grid()` covers the other case, many frames from one video. An unreadable file gets a
  labelled tile rather than a black one, because the two look identical otherwise.
- **`fps=` no longer fails silently on a file input.** It never had any effect there — the rate
  is read from the file — and now it says so instead of letting code proceed on a false belief.
- **The release itself is guarded by tests**, after preparing 1.11.4 found this page four
  versions out of date and one published version with no git tag.

### 1.11.4

- **Two truncations that were quietly wrong are fixed.** Averaged frames are ROUNDED rather than
  truncated: every averaging path finished with `(acc / n).astype(np.uint8)`, putting the result
  0.497 levels below the true mean with half the pixels off by one, always downward, in a frame
  whose purpose is to be a clean background to subtract. And the frame rate is no longer read
  through `int()`: seven call sites turned 29.97 into 29 on NTSC footage, so every time and
  frequency they derived was 3.2 % low, and `_flow` and `_history` wrote the truncated rate into
  the output file as well.
- **Figures produced before this release are not comparable with figures after it** on
  non-integer-rate footage, and average images may differ by one level. Both changes are pinned by
  guard tests that fail if either pattern returns.

### 1.8.0

- **Quantity of motion over a group of markers returns a different number, and the old one was
  confounded.** `group_qom`, `pose_qom` and `normalized_qom` come from `micromotion`, which
  released 1.0.0 today. They used to average over every marker at every frame while gaps were
  interpolated, so an occluded marker contributed almost no speed and still counted in the divisor,
  and the result tracked camera coverage rather than movement. The new default excludes a marker at
  the frames where it was absent. Pass `normalize="worn"` to reproduce an older figure.

### 1.7.1

- **The published API pages described a band the package no longer uses.** They showed
  `group_qom(points, fs, lo=0.3, hi=15.0)` and linked into source lines that stopped existing when
  those functions moved to `micromotion`. The generated pages are rebuilt from the current source
  and the two hand-written user-guide pages, which the regeneration script does not touch, were
  corrected. The band is `micromotion.BAND`, 0.2–5 Hz.
- **The `micromotion` requirement was `>=0.3`.** No such release exists on PyPI below 0.6, and the
  functions this package re-exports arrived much later, so the constraint allowed installations in
  which importing them fails. It is now `>=0.15.2`.

### 1.7.0

- **GoPro MAX `.360` support.** `gopro360_to_dual_fisheye()` converts the two-strip equi-angular
  cubemap that stock ffmpeg cannot unwrap, with the field of view as a parameter, and
  `gopro360_dual_fisheye_average()` time-averages a recording straight to one dual-fisheye image
  without writing a video first. The average samples BEFORE the remap rather than after, which is
  about fifteen times faster for an identical result. Both have now run over a full year of daily
  standstill recordings, 365 days in three views.
- **Fixed: the remap-table scratch directories were never removed.** They were created in four
  places and deleted in none, and one call site discarded the path so there was no way to. A build
  over 364 recordings left 22 GB across 348 directories and filled the disk. The stage is now a
  context manager, so a future call site cannot forget.
- **Fixed: `cv2.imwrite` failures were discarded.** It reports failure by return value and every
  call in `_remap360` ignored it, so a full disk produced a PNG that was never written and an error
  several steps later that read like a corrupt recording. Writes now raise.
- Three regression tests for the above, each checked against the previous commit to confirm it
  fails there.

### 1.6.9

- New **`motiondescriptors()`**—scalar movement descriptors from the quantity-of-motion signal:
  motion energy, smoothness (SPARC), entropy, and spectral descriptors (dominant frequency +
  spectral centroid), as an `MgFigure` plus a CSV (#210).
- Documentation refresh: animated GIFs for the video outputs, a new examples **Gallery**, and
  README/user-guide/wiki updates.

### 1.6.8

- Accurate frame counts: `get_framecount()` (which sets `MgVideo.length`) now counts demuxed
  packets instead of trusting unreliable container metadata, fixing the spurious "extra frame
  after conversion" (off-by-one on AVIs, missing on WebM) without paying for a full decode
  (#242, #239).

### 1.6.7

- Faster import: `import musicalgestures` dropped from ~0.65s to ~0.52s by deferring `import numba`
  (it loads LLVM); the JIT kernels in directograms/impacts/warp now compile lazily on first use
  (#349). Continues the startup-speed work from 1.6.3.

### 1.6.6

- The **public API is now fully typed**: parameter annotations on every public analysis method
  (motion, flow, pose, space-time, audio and the audio–movement suite, and more), on top of the
  return types and `py.typed` marker shipped in 1.6.4, so IDEs and type checkers see complete
  signatures (#345). Hints are lazy (`from __future__ import annotations`), so import speed is
  unchanged.

### 1.6.5

- Faster chained space-time analyses: the average background frame (recomputed by
  `stroboscope`, `silhouette_waterfall` and `spacetime_volume`) is now decoded once and cached
  per `MgVideo`, joining the existing quantity-of-motion and audio-envelope caches (#347).

### 1.6.4

- Type hints on the core classes and ~45 public-method return types, plus a shipped `py.typed`
  marker so type checkers/IDEs use them.
- Extended the `resolve_filename()` output-path helper to the remaining single-target methods
  (~38 sites), eliminating the copy-paste `target_name`/`overwrite` bug class.

### 1.6.3

- Faster `import musicalgestures` (~1.5s → ~0.7s) via lazy-loaded heavy dependencies.
- Pose model weights now download via `urllib` (removed the bundled 3.8 MB `wget.exe`).
- Internal: shared `resolve_filename()` output-path helper and new regression tests (353 → 371).

### 1.6.2

- `pose()` falls back to OpenPose when MediaPipe isn't installed (works out of the box).
- Fixed method-shadowing (audio–movement reports / warp), `blend()`/`grid()` ignoring their
  filename/target arguments, and several docstring/quickstart errors.
- Informative `repr` for `MgVideo`/`MgAudio`; new `duration`/`n_frames` properties and
  `MgImage.save()`/`MgFigure.save()`.
- New docs: optional-extras matrix, core-class conveniences, and a "which method?" table.

### 1.6.1

- `pose_center()` (centre on the global centroid) and `pose_distance()` (per-marker cumulative
  distance travelled + average), both 2D ports of the MoCap Toolbox `mccenter`/`mccumdist`.
- Dedicated **Audio-Video Processing & Analysis** documentation page.
- Faster repeated audio–movement analyses (cached video/audio decode) and a leaner repo
  (removed committed example artifacts).

### 1.6.0

- New **audio–movement analysis suite** for single-dancer studies: `tempo_similarity()`,
  `phase_synchrony()`, `structure_comparison()`, `body_audio_coupling()`, `dynamics_coupling()`.
- `pose_segments()` — circular motion plots and statistics per body segment.
- `resample(fps=…, speed=…, skip=…)` returns a new retimed MgVideo.
- `pose_waterfall()` gains `markers`/`skeleton`/`both` styles plus `axes=False` and `crop=True`;
  `silhouette_waterfall()` gains the same `axes`/`crop` options.
- Average-pose image white frame removed; `pose(background='white')` now also whitens the
  trajectories image.

### 1.5.0

- Motiongram/videogram output files now use `_mgh`/`_vgh` (horizontal) and `_mgv`/`_vgv`
  (vertical) suffixes instead of the axis-based `_mgx`/`_mgy`/`_vgx`/`_vgy`.
- `silhouette_waterfall()` and `pose_waterfall()` gain `axes=False` for a clean, label-free 3D render.

### 1.4.9

- `pose_waterfall()` gains `'markers'`, `'skeleton'`, and `'both'` styles (in addition to
  `'trajectories'`).
- `pose(trajectory_background=...)` for black/white/transparent trajectory images; pose images
  decluttered (titles and the average-pose colorbar removed).
- `overwrite` now defaults to `True` everywhere; `MgVideo.beat_statistics()` defaults to
  `source='motion'`.
- `pose()` keeps the source container (mp4 in → mp4 out) and skips the AVI step for MediaPipe.
- Fixed the swapped `'horizontal'`/`'vertical'` motiongram/videogram `show()` keys; added
  `mgh`/`vgh` and `mgv`/`vgv` aliases.

### 1.4.8

- New `pose_waterfall()` — a 3D spatio-temporal waterfall of pose-marker trajectories.
- `pose()` now defaults to the MediaPipe backend (fast on plain CPU, 33 landmarks, no CUDA
  build needed); OpenPose remains available for multi-person scenes.
- `pose(marker_history=N)` motion trails, inverted black-on-white skeleton mode, and
  label-free trajectory images by default.
- `tempogram()` gains a colorbar and shows the estimated tempo (BPM) in the title.
- `motionhistory(normalize=...)` no longer over-brightens static clips.

### 1.4.x series

- GPU support fixes (CUDA detection, sparse optical flow), `pose(use_cache=True)`,
  C3D marker export, combined motion SSM, space-time displays (stroboscope, silhouette
  waterfall, Motion History Image, space-time volume), audio additions (chromagram, MFCC,
  tempo, beat statistics), and many CI and stability fixes.

See the [CHANGELOG](https://github.com/fourMs/MGT-python/blob/master/CHANGELOG.md) for the
full detail of every release.

## Support

For issues and support:

- [GitHub Issues](https://github.com/fourMs/MGT-python/issues)
- [Documentation](https://fourms.github.io/MGT-python/)

# Changelog

All notable changes to MGT-python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `fuse_pose_views()` fuses MediaPipe *world* landmarks from two or more uncalibrated camera
  views into one consensus skeleton: a single Umeyama rotation-and-scale alignment per view,
  estimated from the rigid torso landmarks and averaged over the take, then a
  visibility-weighted average per landmark, with the cross-view residual in millimetres as a
  quality measure. It takes `extract_pose_landmarks` result dicts or plain `(world, visibility)`
  arrays, so it is not tied to MediaPipe as a source. Closes #355.

  This consolidates `concert_fuse3d.py` and `reh_fuse3d.py` from the Westney-comparisons study,
  which held byte-identical copies of the algorithm and differed by one line, a hardcoded list
  of pieces. It reproduces that study's published fusion on all four concert excerpts to within
  float32 storage precision, rotations agreeing to 1e-9 and the residuals unchanged.

  Two guards the study code did not have. Its rotation average projected the mean matrix back
  with a bare `U @ Vt` and no determinant check, so a mean falling nearer a reflection than a
  rotation would have mirrored the skeleton silently; that is now rejected. And its gap filling
  said "fill short gaps" in a comment while filling every gap of any length and holding the ends
  flat, so a long dropout became a straight line through it with nothing marking it; `max_gap`
  now bounds this. The default is still fill-everything, because that is what the existing
  results were computed with.

  The residual measures *consistency*, not accuracy: views that agree can agree on a wrong pose.

### Removed
- `motion_mp()` is retired. It rendered a motion video across several processes, coordinating them
  with a socket server and an argparse child process, and it raised on its first call: two fields
  were read as one between the parent and the workers, and behind that failure it called
  `save_txt` and `save_analysis` with arguments in the wrong positions. It therefore produced
  nothing for anyone who tried it, and had no test. `motion()` does the same work in one process
  and is tested. The method remains as a stub that says all this and points there; the two modules
  behind it are gone. Closes #370.

### Changed
- **The mypy step in CI blocks merges now.** `mypy musicalgestures/` reports no issues across all
  69 source files, from 248 when issue #350 was opened, so the `|| true` that made it advisory is
  gone. The checker version is pinned alongside it, because the count this reports moves with the
  checker as well as with the code: on identical source, mypy 1.20.1 reported 169 errors where
  2.3.1 reported 90. Closes #350.
- The last of that backlog: two frame rates typed as integers, which they are not; two GPU objects
  created under a flag and used under the same flag, which a checker will not correlate; three
  output names resolved in one branch and used in another; and two functions carrying no return
  annotation at all.

## [1.13.0] — 2026-08-23

### Fixed
- Audio figures mislabelled their time axis, and crashed outright on files longer than an hour.
  `format_time` built its tick labels by assigning formatted strings into a numpy float array, so
  `'10.00'` became `10.0` and rendered as `10:0`, losing a digit on every tick that landed on a
  whole minute, while `'0.13.20'` on a file over an hour raised
  `ValueError: could not convert string to float`. The labels are built as strings now. The method
  is called from ten places, so this affected every audio figure.
- Tick labels are no longer merely near the ticks they describe. `format_time` paired a
  `FixedFormatter` with a `LinearLocator`, which matplotlib warns about because the pairing is by
  position and only defined against a `FixedLocator`. Ten ticks are placed explicitly across the
  axis and labelled with the corresponding times in the original file --- the two differ whenever
  frames were skipped, which is the case the method exists for.
- `musicalgestures` no longer silences warnings for the whole process. Importing it ran a bare
  `warnings.filterwarnings("ignore")`, which switched off every warning from that moment on,
  including warnings raised by this package and by the caller's own code. It is scoped to the
  `DeprecationWarning`s from `audioread` that it was presumably added for, which report that stdlib
  modules a librosa dependency imports are slated for removal, and which a user of this toolbox
  can do nothing about. The three bugs above were hidden behind it, and so were the deprecation
  warnings on the renamed attributes below, which now reach the people who need them.
- The cropping window raised `NameError: name 'ref_point' is not defined` if you pressed "c"
  without having dragged a rectangle first --- which is what its own on-screen prompt invites you
  to do. `ref_point` and `crop` were declared `global` inside the mouse callback but never bound
  at module scope, so they existed only once a mouse event had fired. They are bound now, beside
  the `drawing`/`xi`/`yi` that already were, and selecting nothing says what to do instead:
  "No crop area was selected. Drag a rectangle across the frame with the left mouse button held
  down, then press 'c' to crop."
- `pixelarray()` raised `TypeError: 'MgImage' object is not callable` on its second call.
  `pixelarray` is both the method that computes the frame average and the name it stored the
  result under, so the first call replaced the bound method on the instance with the `MgImage` it
  had just returned. The result now lives under `frameaverage_image`; the method keeps the
  `pixelarray` name and nothing shadows it. Unlike the other renames in this release, there is no
  deprecated alias for the old attribute name, deliberately: an alias here would be a property
  named `pixelarray` on the class itself, which reintroduces the exact collision this fixes,
  permanently. `pixelarray_cv2` had the same problem for the same reason and is fixed the same
  way, as `frameaverage_cv2_image`. This is the same class of bug commit 744169f fixed for
  `subtract` and `sonomotiongram`.

### Added
- `crop_box_from_points()` turns the two dragged corners into an ffmpeg crop box. The arithmetic
  was inline in `cropping_window`, where reaching it needed a window and a mouse, so none of it
  was tested. Either corner may be dragged first and all four directions normalise to the same
  box; that is now nine tests rather than an assumption.

### Changed
- Every result an analysis method stashes on `MgVideo` is now declared on the class and named
  after what it holds: `motion_plot_image`, `ssm_combined_image`, `movement_beat_statistics_figure`,
  `pose_average_image`, `pose_trajectories_image`, and the four grams below. Each old name keeps
  working as a deprecated alias and is removed in 2.0. Closes #346.
- The motiongrams and videograms are named for what they show rather than for the axis that was
  collapsed to make them: `motiongram_x` was the *vertical* gram and `motiongram_y` the
  *horizontal* one, which is why `show()` grew `mgh`/`mgv` aliases in the first place. They are
  `motiongram_vertical_image`, `motiongram_horizontal_image`, `videogram_vertical_image` and
  `videogram_horizontal_image` now. Every existing `show()` key, including the legacy `mgx`/`mgy`,
  resolves as before.
- Declaring the attributes made the producing functions typeable, and typing them turned the type
  checker on over code it had never read. mypy does not check the body of a function carrying no
  annotations at all, so annotating `self` in the producers opened ~31 pre-existing problems to
  view for the first time: `mypy musicalgestures/` reports 90 errors where it reported 74, and the
  difference is what it can now see rather than anything newly written. The errors this work set
  out to close did close --- `no-any-return` went from 25 to 7 --- and the toolbox's results now
  autocomplete in an editor. The remaining 90 are the real number to work against. The count is
  mypy-version-dependent: on the same code and config, mypy 1.20.1 reports 169 errors and mypy
  2.3.1 reports 90, and CI installs mypy unpinned, so anyone acting on these numbers should pin
  the version first.
- `ssm()` stores its result as `ssm_figure`, not `ssm_fig`. Every other stashed result on
  MgVideo already ends in `_video`, `_image` or `_figure`; this one did not, and `show(key='ssm')`
  resolves the result by attribute name, so the outlier was visible to users rather than internal.
  `ssm_fig` keeps working as a deprecated alias and is removed in 2.0. The alias is a property
  rather than a second attribute, so the two names cannot drift apart when either side is
  reassigned. Part of issue #346, which collects the remaining outliers (`motion_plot`,
  `ssm_combined`, `pixelarray`).
- Nine `MgAudio` figure methods are annotated `-> MgFigure | None` rather than `-> MgFigure`:
  `waveform`, `spectrogram`, `tempogram`, `hpss`, `descriptors`, `chromagram`, `mfcc`, `tempo`
  and `beat_statistics`. All nine already returned None when they could not compute a figure ---
  no audio track, an unknown `chroma_type`, too few beats --- so this documents what they did
  rather than changing it, and each docstring now says when you get None back instead of leaving
  it to be found through an `AttributeError` further down. Their bare `return` statements are
  explicit `return None`.
- Internal typing, issue #350: `mypy musicalgestures/` goes from 248 errors in 32 files to 74
  in 19, with `_video.py`, `_utils.py`, `_360video.py`, `_audio.py` and `_cropvideo.py` --- the
  five files that carried 69 per cent of the backlog --- all at zero. Mostly implicit `Optional`
  in signatures, cache annotations, and one name per branch where three subprocess types shared
  one. The class-scoped imports that bind methods on `MgVideo` are the toolbox's central idiom
  and carry permanent `# type: ignore[misc]` markers rather than being restructured. CI's mypy
  step stays non-blocking until the remaining 74 are dealt with; they are dominated by
  `no-any-return` (25) and `union-attr` (18), and each needs reading rather than a sweep.
- More return annotations corrected to match what the code has always done. `mg_ssm` returns
  `MgList | MgImage | None`, `mg_motionscore` returns `float | None` (as its own docstring
  already said), and `Flow.dense` returns `MgVideo | MgFigure` --- with `velocity=True` it has
  always handed back a figure, while both signature and docstring promised a video.

## [1.12.1] — 2026-08-22

### Fixed
- The contact-sheet test fixture used `os.link`, which cannot cross drives on Windows, so CI
  failed on all three Windows jobs. Test-only: the 1.12.0 package is correct and this changes
  nothing a user runs. It is released because the `v1.12.0` tag points at a commit whose CI is
  red, and a tag that fails its own checks is misleading whatever the wheel contains.

### Changed
- The PyPI publish workflow now refuses to run unless CI succeeded on the exact commit being
  released. Publishing fires on a published release, which was independent of CI, which is how
  1.12.0 went out from a red commit in the first place.

## [1.12.0] — 2026-08-22

### Added
- `contact_sheet()` tiles ONE frame from EACH of many videos into a sheet, so a corpus can be
  scanned by eye. `grid()` does the other case, many frames from one video. On a 366-day export
  of daily recordings every framing fault found was found by a person looking at a sheet like
  this and not by a measurement — a crop pointed at a colleague, a frame that cut the subject's
  feet — because a day framed unlike its neighbours announces itself without a threshold having
  to be chosen in advance.

  A file that cannot be read gets a tile labelled UNREADABLE rather than a black one. A dark day
  and an unopenable file look identical otherwise, and on that corpus a day was investigated as
  a fault when the sheet had simply been built while the file was still being written.

### Fixed
- `MgVideo('clip.mp4', fps=99)` now warns. `fps` is the rate an ARRAY is encoded at; for a file
  input the constructor reads the rate from the file and overwrites the argument, so it did
  nothing — and code written on the belief that it had set the rate was wrong with nothing in
  any output to show it. The docs had carried this as a standing warning. Use
  `resample(fps=...)` to change a file's rate.

### Changed
- Three tests now guard the release itself: that `__version__`, the newest changelog entry and
  `docs/releases.md` all name the same version, and that every released version in the changelog
  has a git tag. Preparing 1.11.4 found `docs/releases.md` announcing 1.8.0 while PyPI served
  1.11.3, and 1.11.3 published with no tag at all. Neither breaks an install, which is why
  neither had been noticed. v1.11.3 has since been tagged at its own release commit.

## [1.11.4] — 2026-08-22

### Fixed
- The frame rate is no longer truncated to an integer. Seven call sites read
  `int(vidcap.get(cv2.CAP_PROP_FPS))` — `_directograms`, `_flow` (twice), `_history`,
  `_impacts`, `_warp` and `_videoadjust`. On NTSC-rate footage that is `int(29.97) == 29`, so
  every time and frequency they derived was 3.2 % low, and `_flow` and `_history` also wrote
  the truncated value into the output file's declared rate, turning a 29.97 fps input into a
  29 fps file. The docs carried this as a known defect; it is fixed and the note now says so.

  Every use was checked to be safe with a non-integer rate: divisions, `cv2.VideoWriter`,
  ffmpeg `-r` and librosa `sr` all take a float, and `_impacts` already wrapped `int()` where
  it needed a whole number. Figures produced before this change are not comparable with
  figures produced after it on non-integer-rate footage.

- Averaged frames are ROUNDED rather than truncated. Every averaging path finished with
  `(acc / n).astype(np.uint8)`, which discards the fractional part instead of rounding it.
  On a synthetic stack the result sits 0.497 levels below the true mean and half the pixels
  differ by one from the rounded answer, always downward — a small, systematic bias in a
  frame whose purpose is to be a clean background to subtract. Seven places in four files:
  `_spacetime._average_frame`, `_heatmap`, the three pose average frames, and the two
  motiongram row and column means. `_remap360` already rounded, which is where the
  convention came from.

  Output pixel values may therefore change by one level. Nothing about the API changes.

  Pinned by two tests in `tests/test_average.py`, because the existing suite passed either
  way: that truncation is strictly below the true mean where rounding is not, and a guard
  that reads the package for any accumulator divided by a count and cast without rounding.

## [1.11.3] — 2026-08-19

### Changed
- `bandpass` and `xcorr_lag` now delegate to `micromotion`, which owns filtering and lag
  estimation for the toolbox family. Their signatures and return types are unchanged, so
  existing calls keep working, but there is one implementation behind both packages instead
  of two that had drifted apart.
- `bandpass` RAISES on a band that is unusable at the given sampling rate. It used to return
  the signal unfiltered, which handed back data the caller believed was band-limited and was
  not, a silent wrong answer propagating into everything computed from it. The argument
  orders still differ between the two packages: `musicalgestures.bandpass(signal, lo, hi,
  fs)` against `micromotion.bandpass(x, fs, lo, hi)`. micromotion validates against Nyquist,
  so a call moved between them without reordering raises rather than returning a plausible
  array.

### Fixed
- `xcorr_lag` and `micromotion.xcorr_lag` returned opposite signs for the same pair of
  signals. This package was the correct one, agreeing with its own docstring throughout, and
  micromotion is corrected in its 1.13.0. Requires `micromotion>=1.13.0`.
- The tie-breaking rule that prefers the smallest-magnitude lag among near-tied maxima, which
  originated here and matters for periodic envelopes, moved into micromotion with the
  delegation, so nothing was lost by it.

### Added
- `tests/test_analysis.py`. `musicalgestures._analysis` exports six functions at package top
  level and no test referenced it, which is why the two divergences above went unseen. The
  new tests pin the delegation, pin that `bandpass` really removes out-of-band energy rather
  than merely matching the owner, and pin the deliberate difference between this package's
  `dominant_frequency` (FFT peak, 0.5–8.0 Hz, for locomotion and dance) and micromotion's
  (Welch peak, 0.3–4.0 Hz, for postural micromotion). That difference is stated in the
  docstring now rather than only in a source comment in `__init__.py`.

## [1.11.2] — 2026-08-16

### Changed
- Documentation and citation metadata only; no change to any code path.
- `CITATION.cff` states the software's authors, its version and its DOI, and the README carries a
  DOI badge, so the record Zenodo archives is built from the repository rather than by hand.
- The one public definition without a docstring, `musicalgestures.examples`, is described.
- The documentation says where this package stops and its three sibling toolboxes start.

### Note on the archive
This is the first release since the Zenodo GitHub integration was switched on. The integration
cannot see a deposition it did not create, so this release begins a NEW concept DOI and the
hand-made lineage 10.5281/zenodo.21949007 is frozen at 1.11.1. The repository is repointed at the
new lineage immediately after this release, and `deposit/_curation/toolbox_doi_check.py` in the
Still Standing project verifies it.

## [1.11.1] — 2026-08-13

### Changed
- **The threshold figure recorded in 1.11.0 is superseded by the full corpus.** That release
  quoted a 0.4 % median cost at `threshold=0.05`, measured on 83 clips. The run finished at 345:
  the cost is **0.2 %**, the direction is still consistent and significant at the lower
  thresholds (202 of 345 at the default, sign test p = 0.002), and at `threshold=0.2` it stops
  being significant at all (187 of 345, p = 0.13). The conclusion is unchanged and stronger --- the
  picture-legible default is free, for practical purposes, for machine analysis of this material.
  The sequence is recorded in the docstring because it is the useful part: 6 clips said no effect,
  23 said 1.2 %, 83 said 0.4 %, 345 says 0.2 %.

## [1.11.0] — 2026-08-12

### Fixed
- **`pose()` on OpenCV 5 fails with a message instead of an `AttributeError`.** OpenCV removed its
  Caffe importer in 5.0: `cv2.dnn.readNetFromCaffe` no longer exists and `cv2.dnn.readNet` refuses
  the format rather than falling back. The OpenPose backends here — BODY_25, COCO and MPI — are
  Caffe models, so on such a build they cannot run at all. The failure used to surface as
  `AttributeError: module 'cv2.dnn' has no attribute 'readNetFromCaffe'` from deep inside the run,
  and only *after* offering to download 200 MB of weights that the environment could never load.

  The check now happens before the weights are looked for, and names both ways out: `pose(model=
  'mediapipe')` with `pip install musicalgestures[pose]`, or `pip install 'opencv-python<5'` to
  keep the OpenPose skeletons. It is deliberately **not** an automatic switch to MediaPipe — its 33
  landmarks are a different skeleton from BODY_25's 25, so a silent substitution would return data
  that looks like what was asked for and is not.

- **The MediaPipe fallback no longer falls back into a wall.** With MediaPipe missing, `pose()`
  announced a fallback to BODY_25 and then failed on it, because that fallback assumed OpenCV could
  always load a Caffe model. Where it cannot, there is nowhere to fall back to, and the error now
  says so and names the one install that would work.

- **`Test_pose_gpu` skips where OpenPose cannot run.** Its two cases had been failing with the bare
  `AttributeError` above on any OpenCV 5 machine, which is what made the incompatibility read as a
  fault in the pose code rather than in the environment. They test device selection on the OpenPose
  path, so where that path does not exist there is nothing to select and the tests skip with the
  reason stated.

### Documentation
- **What the visualisation threshold costs a measurement is now measured, not
  just flagged.** `_motionvideo`'s header said there was "no reason to think
  the value that looks best is the value that measures best". On 83 clips of a
  corpus of everyday sound-producing actions, scored by how far the action
  stands above the lead-in it interrupts: no threshold improves the
  separation, more clips lose contrast than gain it at every step (55 of 83 at
  `threshold=0.05`, sign test p = 0.004), and the median cost at the default is
  0.4 % against a per-clip spread of 0.39 to 2.66. The default is very nearly
  free for machine analysis of this material. Two cautions are recorded with
  it: one criterion was scored, and smaller samples of the same code gave 1.2 %
  at 23 clips and no effect at 6.
- Also recorded: a threshold moves any landmark computed from the same series,
  so a statistic measured across that landmark shows a much larger apparent
  effect than the signal loss --- 23 % against 9 % here.

MediaPipe is unaffected by any of this and remains the default backend; it carries its own weights
and never touches `cv2.dnn`. Verified end to end on OpenCV 5.0.0 with MediaPipe 1.0.0: 163 frames
of 33 landmarks off a real clip, a person found in 44 % of them.

## [1.10.0] — 2026-08-12

### Added
- **`normalize=False` on `mg_motion`, for machine analysis.** The exported quantity of motion has
  always been divided by each clip's own maximum, so every clip peaks at exactly 1.0. That is what a
  plot on a 0–1 axis wants — the same expression appears in the plotting code — and it is invisible
  in the numbers themselves, which is why it surprises people. It makes quantity of motion
  **incomparable between clips**: a small gesture and a violent one both reach 1.0, and one bright
  frame sets the scale for everything around it.

  `normalize=False` exports the untouched sum of pixel values instead. The column is **renamed to
  `QomRaw`** rather than merely rescaled, so that a file cannot be misread later: a `Qom` column is
  always per-clip normalised and a `QomRaw` column never is, whoever opens it and however long
  afterwards. `normalize` was already in `mg_motion`'s signature and had never been used.

### Fixed
- **TSV export wrote quantity of motion as 0 or 1.** The writer formatted the column with `%d` while
  the value had already been divided by its maximum, so `np.savetxt` truncated every fraction to an
  integer. Normalised values now write as floats; `QomRaw` writes as an integer, which is what it is.
  This changes the content of TSV exports, which ARJ confirms have not been relied on.

### Changed
- **`_motionvideo` states what its defaults are for.** They are tuned to produce a legible picture,
  not a measurement — the right choice for motion videos, motiongrams and plots, and worth saying
  now the same functions are used to produce numbers. Three are visualisation choices:
  `threshold=0.05`, which removes sensor noise and small real motion alike; `filtertype='Regular'`;
  and the per-clip normalisation above.

  Nothing is smoothed by default. The whole default chain is
  `format=gray → tblend=all_mode=difference → threshold`, and the smoothing that exists is off unless
  asked for — `atadenoise` (adaptive temporal averaging over 129 frames, the only temporal one),
  `use_median` (spatial), `blur` (spatial). A machine-analysis configuration is therefore a matter of
  `threshold` and `normalize`, not of turning filters off.

## [1.9.2] — 2026-08-08

### Added
- `musicalgestures.__version__`. The package exposed no version attribute
  at all, so code could only learn the version through the installed
  metadata, and a script run against a source checkout could not learn it
  at all.

### Fixed
- The version has one source. `pyproject.toml` reads
  `musicalgestures.__version__` through a dynamic version rather than
  carrying its own copy, so adding the attribute did not create a second
  number to drift. That drift is not hypothetical across these toolboxes:
  ambiscape shipped three releases reporting a version other than their
  own and musiscape shipped one, in both cases because a bump edited
  `pyproject.toml` alone. `tests/test_version.py` fails if a static
  version reappears there, if the build stops reading the module
  attribute, or if the two numbers diverge.


## [1.9.1] — 2026-08-06

### Added
- `get_pose_model_path()`: public helper for the shared MediaPipe pose-model
  download/cache, promoted from the private
  `MediaPipePoseEstimator._get_model_path` (#360).
- `extract_pose_landmarks()` accepts `t0`/`duration` parameters to analyse a
  sub-window of a long video without decoding the whole file; returned
  timestamps stay on the source clock (#354).

### Fixed
- `show(key='blur')` looked up a non-existent attribute and silently did
  nothing; it now shows the face-anonymised video, and raises
  `FileNotFoundError` when `blur_faces()` has not been run.
- `subtract()` and `sonomotiongram()` stored their results over their own
  bound methods, so a second call on the same object crashed. Results are now
  stored as `subtract_video` and `sonomotiongram_audio`.
- `info('summary')` reported the frame count as the duration in seconds.
- The default motion-data CSV is now written to `<name>_motion.csv`, matching
  the tsv/txt branches and the path `motiondata()` returns (previously
  `<name>_motiondata.csv`).
- The `autoshow` parameter on the `MgAudio` figure methods (`waveform()`,
  `spectrogram()`, `tempogram()`, `hpss()`, `descriptors()`, `chromagram()`,
  `mfcc()`, `tempo()`, `beat_statistics()`) was accepted but ignored; it now
  displays the figure inline when running in a notebook.

## [1.9.0] — 2026-08-06

### Added
- 360-degree directional analysis on `Mg360Video`: `anglegram()` (time by
  azimuth visual motion energy, cos-latitude weighted, ambisonics-aligned),
  `aem_overlay()` (audio energy maps from ambiscape exports rendered on the
  video or the anglegram via a file interface), `view()` (non-destructive
  perspective crops returning a regular `MgVideo`), and projection
  auto-detection.

### Changed
- API documentation migrated from handsdown-generated pages to mkdocstrings:
  docstrings now render at build time, page paths unchanged.
- Documentation overhaul: beginner-oriented README, thirteen doc-vs-code
  errors fixed (motiongram index order, `length` vs `duration`, and others),
  new demo figures and GIFs from genuine tool output.

## [1.8.0] — 2026-08-05

### Changed
- **`group_qom`, `pose_qom` and `normalized_qom` return different numbers.** They are re-exported
  from `micromotion`, which released 1.0.0 today, and the change is a correctness fix rather than a
  refinement. They averaged over every marker at every frame while the underlying
  `band_limited_qom` interpolates gaps, so an occluded marker contributed a near-zero speed and
  still counted in the divisor. The result tracked how much the cameras saw rather than how much
  the body moved: 16 to 17 per cent low on a realistic dropout pattern, with the speed series
  correlating up to +0.70 with the per-frame count of visible markers.

  The new default, `normalize="visible"`, excludes each marker at the frames where that marker was
  absent, and lands within 0.8 per cent of the unoccluded value. Pass `normalize="worn"` to
  reproduce a figure published with an earlier release, and say which you used. Pose data from a
  clean, well-lit recording with no dropouts is unaffected; occluded mocap is affected most.

- The `micromotion` floor is `>=1.0.0`, which is a correctness floor rather than a documentation
  one: below it the re-exported function returns the confounded number.

## [1.7.1] — 2026-08-05

### Fixed
- The committed API pages published a band this package no longer uses. They showed
  `group_qom(points, fs, lo=0.3, hi=15.0)` and deep-linked into `musicalgestures/_qom.py` at line
  numbers that stopped existing when those functions moved to `micromotion` on 2026-07-29. The
  pages are regenerated from the current source.
- `docs/user-guide/pose-tracking.md` and `docs/user-guide/sound-movement-toolkit.md` said the band
  is 0.3–5 Hz and passed `lo=0.3, hi=15.0`. It is `micromotion.BAND`, 0.2–5 Hz. The regeneration
  script does not touch hand-written pages, so these were corrected by hand.
- The `micromotion` floor was `>=0.3`. No such release exists on PyPI below 0.6, and the functions
  re-exported here arrived far later, so the constraint permitted installations in which
  `from musicalgestures import group_qom` fails. It is now `>=0.15.2`, which is also the floor that
  makes the committed API pages true, since they are generated from that package's docstrings.

### Changed
- The three re-export shims now point at <https://fourms.github.io/micromotion/> for the API
  reference. Their generated pages describe the shim rather than the functions, which is correct
  but left a reader with nowhere to go.

## [1.7.0] — 2026-08-03

### Added
- GoPro MAX `.360` support: `gopro360_to_dual_fisheye()` with the field of view as a parameter, and
  `gopro360_dual_fisheye_average()`, which time-averages a recording straight to a dual-fisheye
  image without writing a video first. It decimates BEFORE the remap rather than after, which is
  about fifteen times faster for an identical result.

### Fixed
- The remap-table scratch directories were created in four places and removed in none, and one call
  site discarded the path so there was no way to. A build over 364 recordings left 22 GB across 348
  directories and filled the disk. `_gopro_remap_stage` is now a context manager.
- `cv2.imwrite` failures were discarded throughout `_remap360`. It reports failure by return value,
  so a full disk produced a PNG that was never written and an error several steps later that read
  like a corrupt recording. Writes now raise.

### Tests
- Three regression tests for the above, each verified to fail against the previous commit.


### Added
- **Sound–movement analysis toolkit** (#351, #352, #353)—a family of plain-numpy functions
  ported from the author's ro / stillstanding / Westney / cymbal research pipelines, all
  importable directly from `musicalgestures`:
  - `_peaks.pick_peaks` — the canonical adaptive peak-picker shared by every detector below.
  - `_pulse` — `Cycle`, `group_strokes`, `segment_cycles`, `cycle_table`, `fit_accelerando`,
    `motion_onsets`: onset grouping into rhythmic cycles and accelerando fitting.
  - `_alignment` — `xcorr_lag`, `envelope_lag`, `per_cycle_motion_delta`, `anchor_and_match`,
    `offset_stats`, `sliding_correlation`, `envelope_agreement`: cross-modal lead/lag and
    coupling.
  - `_qom` — `band_limited_qom`, `accel_to_speed`, `group_qom`, `pose_qom`, `body_scale`,
    `normalized_qom`, `grid_qom`, `envelope`, `bin_series`: quantity-of-motion cores, including
    body-scale (framing-invariant) normalization.
  - `_audiofeatures` — `rms_envelope`, `spectral_flux`, `spectral_flux_onsets`, `energy_onsets`,
    `t60_backward_decay`, `attack_spectral_centroid`: scipy-only audio features and onsets.
  - `motiongram_data()` (`_motionanalysis`) gained an `orientation='vertical'|'horizontal'` option.
  - `_posture` — 12 posturography/sway-dynamics functions (`cop_sway_metrics`,
    `stabilogram_diffusion`, `dfa`, `sample_entropy`, ...).
  - `_physio` — `respiration_rate`, `spectral_band_fractions`.
  - `_mocap` — `read_qtm_tsv`, `compare_modality_envelopes` (its own `dominant_frequency` is
    intentionally not re-exported at top level to avoid shadowing `_analysis.dominant_frequency`).
  - `_posetools` — `extract_pose_landmarks` (needs the new optional `[pose]` extra:
    `pip install musicalgestures[pose]`; supports both the legacy MediaPipe Solutions API and the
    newer Tasks API), `midpoint`, `limb_speed_from_landmarks`, `impact_events`.

  See the README's "Sound–Movement Analysis Toolkit" section and the new
  [user guide page](https://fourms.github.io/MGT-python/user-guide/sound-movement-toolkit/) for
  usage; API reference pages were regenerated for all nine new modules.

---

## [1.6.9]–2026-06-28

### Added
- **`motiondescriptors()`** (#210)—higher-level scalar movement descriptors from the
  quantity-of-motion signal: **motion energy** (mean squared QoM), **motion smoothness**
  (SPARC, spectral arc length, a dimensionless validated smoothness metric), **motion entropy**
  (normalised 0–1 Shannon entropy of the QoM magnitude distribution), and **spectral descriptors**
  (dominant frequency + spectral centroid from the Hann-windowed QoM power spectrum). Returns an
  `MgFigure` (QoM time series + power spectrum) with the scalars and full spectrum in `.data`, and
  writes a `_motiondescriptors.csv`. Hann windowing is the documented default (with `window='none'`
  for rectangular), answering the windowing question raised in the issue; the dominant frequency
  and spectral centroid are searched within a movement band (`fmin`/`fmax`, default 0.2–10 Hz).

### Documentation
- Lightweight animated GIFs for the video-producing methods (motion, history, motion vectors,
  Eulerian magnification, dense/sparse optical flow), a `motiondescriptors` figure, and a new
  visual **Gallery** in the examples page; `scripts/generate_example_media.py` regenerates them.
  README, the video-analysis user guide and the wiki updated for `motiondescriptors()`.

---

## [1.6.8]–2026-06-28

### Fixed
- **Accurate frame counts** (#242, #239). `get_framecount(fast=True)`—used to set `MgVideo.length`—read the container's `nb_frames` metadata, which is unreliable (off by one on many AVIs, absent
  on WebM); this was the "extra frame after conversion" reported in #239. It now counts demuxed
  video packets (`-count_packets`), which matches the true decoded frame count across containers
  while still avoiding a full decode (it is in fact marginally *faster* than the old metadata
  query). `fast=False` still does the exhaustive decode-and-count. Added a regression test that
  pins `fast == exact` for AVI/MP4/WebM.

---

## [1.6.7]–2026-06-28

### Changed
- **Faster import** (#349): `import musicalgestures` dropped from ~0.65s to ~0.52s by deferring
  `import numba` (it pulls in LLVM). The `@jit` kernels in `_directograms`, `_impacts` and `_warp`
  are now compiled lazily on first use. The nested directogram case (`directogram` calls
  `matrix3D_norm`) is handled by compiling the inner kernel and rebinding the module global before
  the outer kernel compiles, the issue that reverted the first attempt. Adds
  `tests/test_numba_kernels.py` to pin the deferral and nested-jit behaviour.
- Also added the missing parameter type hints to `mg_warp_audiovisual_beats` (a follow-on to #345).

---

## [1.6.6]–2026-06-28

### Added
- **Parameter type hints across the public API** (#345). Every public analysis method now
  annotates its parameters (not just its return type): the motion methods, motiongrams/
  motionvideo/motiondata/motionplots, optical flow (`Flow.dense`/`sparse` and the velocity
  helpers), pose (`pose`, `pose_waterfall`/`segments`/`center`/`distance`), the space-time
  visualisations, directograms/impacts, SSM, cropping, heatmap, history, videograms, the audio
  methods and the audio–movement suite, plus the public `_utils` helpers and the `MgVideo`
  inline methods. Modules now use `from __future__ import annotations` so hints are lazy
  (no runtime/import-speed cost) and use modern `str | None` syntax. Combined with the `py.typed`
  marker shipped in 1.6.4, downstream IDEs and type checkers now see a fully-typed public API.

### Internal
- **Fixed the CI mypy step** (#345), which was aborting on a third-party file (`tifffile` ships
  3.12-only syntax, fatal on our 3.10 target) before it ever checked our code. Settings are now
  centralised in `[tool.mypy]` (`follow_imports=skip`, exclude deprecated/3rdparty) and shared by
  CI and `nox -s typecheck`. The step stays non-blocking while the internal-typing backlog is
  worked through (#350).

---

## [1.6.5]–2026-06-28

### Internal
- **Cached average-frame decode** for the space-time analyses (#347). `stroboscope`,
  `silhouette_waterfall` and `spacetime_volume` all reconstruct the same average background frame
  by decoding the whole video; this is now computed once and cached per `MgVideo` (keyed by
  filename, invalidated when it changes), so chained space-time calls reuse it instead of
  re-decoding. Joins the existing derived-signal caches (quantity-of-motion, audio envelope).
  Full raw-frame shared decoding is intentionally avoided. Caching the decoded frame stack is too
  memory-heavy for typical videos (>1 GB), so only small derived signals are cached.

---

## [1.6.4]–2026-06-28

### Added
- **Type hints + `py.typed`**—the `MgVideo`/`MgAudio`/`MgImage`/`MgFigure` constructors are typed
  and ~45 public methods now declare their return types (the audio suite, space-time
  visualisations, the audio–movement reports, motion/pose/flow/ssm/videograms, etc.). A `py.typed`
  marker is shipped (PEP 561) so the hints are consumed by downstream type checkers. (Parameter
  annotations and stricter CI mypy remain an ongoing follow-up; see #345.)

### Internal
- Extended the `resolve_filename()` output-path helper (1.6.3) to the remaining single-target
  methods: the space-time visualisations, the audio–movement reports, `beat_statistics`/
  `tempo_similarity`, both `videograms` passes, `history`/`history_cv2`, `pixelarray`/
  `pixelarray_cv2`, and `flow.dense`/`flow.sparse`/the velocity plot (#344). ~38 sites total now
  use the shared helper, removing the copy-paste `target_name`/`overwrite` bug class for all
  standard single-target outputs.

---

## [1.6.3]–2026-06-27

### Changed
- **Faster import**: `import musicalgestures` dropped from ~1.5s to ~0.7s by lazy-loading heavy
  dependencies (`scipy.signal`, `scipy.stats`, `IPython.display`) that are only needed by specific
  methods.
- **Pose model download** now uses Python's `urllib` instead of a bundled Windows `wget.exe` and
  platform-specific shell scripts, which removes the 3.8 MB binary from the wheel and is fully
  cross-platform.

### Internal
- Added a `resolve_filename()` helper that centralises the `target_name`/`overwrite` output-path
  logic (the pattern whose copy-paste variants caused the earlier `grid()`/`blend()` bugs); adopted
  it across the single-output video methods and all `MgAudio` methods.
- Added regression tests for the audio–movement suite, `resample()`, the pose renderers, and the
  core-class conveniences (353 → 371 tests).

---

## [1.6.2]–2026-06-27

### Fixed
- `pose()` defaults to the MediaPipe backend (the optional `[pose]` extra). On installs without
  MediaPipe it now **falls back to the OpenPose `body_25` backend** (with a clear message) instead
  of raising, so `pose()` works out of the box. (This also fixes the CI test jobs.)
- Several result attributes shadowed their own methods on the instance, so a second call failed:
  `tempo_similarity`, `phase_synchrony`, `structure_comparison`, `body_audio_coupling`,
  `dynamics_coupling` (now stored as `*_figure`) and the warp result (now `self.warp_video`).
- `blend()` ignored its `filename` argument (it always read `self.filename`).
- `grid()` ignored its `target_name` argument (it always wrote `<input>_grid.png`).
- Corrected stale `overwrite` docstrings (now default `True`), documented the previously
  undocumented `convert` parameter on `directograms`/`impacts`/`history_cv2`, and fixed several
  quickstart errors (invalid `scale=` example; `_motiondata.csv`/`_descriptors.csv`/`.avi` names).

### Added
- Informative `repr` for `MgVideo` (frames, fps, size, audio) and `MgAudio`.
- `MgVideo.duration` (seconds) and `MgVideo.n_frames` properties, and `MgAudio.duration` — clearing
  up the `length` footgun (frame count for video vs seconds for audio).
- `MgImage.save(path)` and `MgFigure.save(path)` to copy/save a result to a chosen location.
- Documentation: an optional-dependency/extras matrix, core-class conveniences, a "Which method
  should I use?" disambiguation table, and `pose_center()`/`pose_distance()` with examples + images.

---

## [1.6.1]–2026-06-27

### Added
- `pose_center()` — centre the pose data on its global centroid (a 2D port of the MoCap Toolbox
  `mccenter`); plots the centred trajectories and saves a CSV of centred coordinates.
- `pose_distance()` — per-marker cumulative distance travelled plus the across-marker average
  (a 2D port of `mccumdist`); plots cumulative curves + a ranked total-per-marker bar chart and
  saves a CSV.

### Changed
- Consolidated the audio–movement material into a dedicated **Audio-Video Processing & Analysis**
  documentation page; the docs module was renamed accordingly (the public `warp_audiovisual_beats()`
  method is unchanged).

### Fixed / internal
- Cache the movement quantity-of-motion and audio onset/RMS envelopes per `MgVideo`, so running
  several audio–movement analyses in a row no longer re-decodes the same video/audio (~6× faster
  on subsequent calls).
- Removed ~26 MB of generated test artifacts that had been committed under
  `musicalgestures/examples/` (and added `.gitignore` rules to keep them out); de-duplicated the
  pose-keypoint cache fallback across the `pose_*` methods; surfaced CSV-save errors as warnings.

---

## [1.6.0]–2026-06-27

### Added
- **Audio–movement analysis suite** for comparing a single performer's sound and motion:
  - `tempo_similarity()` — audio tempo vs movement tempo (ratio, nearest harmonic,
    cross-correlation peak/lag, zero-lag correlation), with a CSV.
  - `phase_synchrony()` — phase-locking value (PLV) between the audio and movement rhythm,
    with a polar phase-difference histogram.
  - `structure_comparison()` — audio self-similarity (MFCC) vs movement self-similarity
    (frame appearance) plus a difference map and structural-agreement score.
  - `body_audio_coupling()` — correlates each pose marker's speed with the audio onset
    envelope; body map + ranked bar chart + CSV.
  - `dynamics_coupling()` — audio loudness (RMS) vs quantity of motion, zero/best-lag correlation.
- `pose_segments()` — circular (polar rose) motion plots and per-segment circular statistics
  (mean angle, resultant length R, circular std, range of motion, mean angular speed) + CSV.
- `resample(fps=…, speed=…, skip=…)` — retime an already-loaded video and return a **new**
  MgVideo: duration-preserving frame-rate change, playback-speed factor (audio kept in sync),
  and/or integer frame decimation.
- `pose_waterfall(style=…)` gained `'markers'`, `'skeleton'`, and `'both'` styles (in addition
  to `'trajectories'`), plus `axes=False` (clean render) and `crop=True` (trim to the data).
- `silhouette_waterfall()` gained `axes=False` and `crop=True`.

### Changed
- `pose(background='white')` now also makes the trajectories image white (the trajectory
  background follows the pose `background`); use `trajectory_background` to override.

### Fixed
- Removed the white frame around the average-pose image (it now fills edge-to-edge).
- `pose_waterfall(crop=True)` no longer leaves a large empty margin (the 3D axes fills the
  figure and the data cube is zoomed), including with `axes=False`.

---

## [1.5.0]–2026-06-27

### Changed
- **Motiongram/videogram output filenames** now use direction-of-movement suffixes: `_mgh`/`_vgh`
  (horizontal) and `_mgv`/`_vgv` (vertical), replacing the axis-based `_mgy`/`_vgy` and
  `_mgx`/`_vgx`. Applied to `motion()`, `motiongrams()`, `videograms()`, `motion_mp()`, and the
  `ssm()` intermediates. The `show(key=...)` keys (`'horizontal'`/`'vertical'`,
  `mgh`/`mgv`/`vgh`/`vgv`, and the legacy `mgx`/`mgy`/`vgx`/`vgy`) all still resolve correctly.

### Added
- `silhouette_waterfall()` and `pose_waterfall()` accept `axes=False` to render without any axes,
  ticks, labels, panes, or title (a clean 3D image).

---

## [1.4.9]–2026-06-27

### Added
- `pose_waterfall(style=...)`: new `'markers'`, `'skeleton'`, and `'both'` styles that draw the
  pose at `n_samples` time slices (colour-by-time by default), in addition to the existing
  `'trajectories'` style.
- `pose(trajectory_background=...)`: choose the trajectories-image background — `'black'`,
  `'white'`, or `'transparent'` (legacy `transparent_trajectories` still honoured).
- Orientation aliases for `show(key=...)`: `mgh`/`vgh` (horizontal) and `mgv`/`vgv` (vertical).

### Changed
- `overwrite` now defaults to `True` for all functions: outputs are overwritten in place instead
  of auto-incrementing the filename. Pass `overwrite=False` for the old behaviour.
- `MgVideo.beat_statistics()` now defaults to `source='motion'` (analyses the movement rhythm),
  so it differs from `video.audio.beat_statistics()`. Use `source='audio'` for the audio track.
- `pose()`: `convert` defaults to `None` ("auto"). MediaPipe reads the source directly (no
  intermediate AVI), while OpenPose still converts for frame-accurate decoding. The result video is
  written in the **original container** (mp4 in → mp4 out; no avi→mp4 round-trip).
- Pose images decluttered: removed the titles from the trajectories and waterfall images and
  the average-pose image, and removed the average-pose colorbar. The trajectories image omits
  marker-name labels by default (`trajectory_labels=True` to re-enable).

### Fixed
- The `show(key=...)` orientation keys for motiongrams/videograms were swapped: `'horizontal'`
  now selects the horizontal-movement gram and `'vertical'` the vertical one, with correct titles
  (in both `MgVideo.show` and `MgList.show`).

---

## [1.4.8]–2026-06-27

### Added
- `pose_waterfall()`: a 3D spatio-temporal waterfall where each marker's trajectory flows
  through (x, time, y) space, a pose-based counterpart to `silhouette_waterfall()`. Reuses
  cached pose keypoints when available; `color_by='marker'/'time'`, marker subsets supported.
- `pose(marker_history=N)`: draw a motion trail for each marker over the last N frames
  (works in the OpenPose, MediaPipe, and cached re-render paths).
- `pose(trajectory_labels=True)`: re-enable per-marker name labels on the trajectories image.

### Changed
- `pose()` now defaults to the MediaPipe backend instead of OpenPose `body_25`. MediaPipe is
  fast on plain CPU, needs no CUDA-enabled OpenCV build, and gives 33 landmarks with depth +
  visibility. The OpenPose models (`body_25`/`coco`/`mpi`) remain available for multi-person
  scenes and CUDA setups.
- `pose(overlay=False, background='white')` now draws a black skeleton and markers (a
  print-friendly inverted look) instead of the previous dark-blue/dark-red scheme.
- The marker-trajectories image no longer shows per-marker name labels by default.
- `tempogram()`: added a colorbar (matching the chromagram), shows the estimated tempo rounded
  to one decimal with "BPM" in the title, and removed the dotted estimated-tempo line.
- `videograms()`/`motiongrams()` display keys are now `'horizontal'`/`'vertical'`.

### Fixed
- `motionhistory()`: `normalize` now defaults to `False` and is guarded so it no longer
  amplifies faint residual trails into a washed-out ("blown up") image when the final frames
  are static.
- Documentation: refreshed the docs site, wiki, and READMEs for the MediaPipe default and the
  new pose options; updated the stale `releases.md` page (was pinned to an old version) to track
  the changelog.

---

## [1.4.7]–2026-06-27

### Fixed
- **GPU detection**: `_utils.py` never imported `cv2`, so `get_cuda_device_count()` and
  `cuda_build_available()` always reported no CUDA. The GPU was never used even with a
  CUDA-enabled OpenCV. Now fixed: `pose(device='gpu')` (OpenPose), `flow.dense(use_gpu=True)`,
  and `flow.sparse(use_gpu=True)` use the GPU on a CUDA build.
- GPU sparse optical flow: corrected point shapes (1×N CV_32FC2) and `calc()` return
  handling so the CUDA path works (it was never exercised before the detection fix).
- `MgList.show(key='mgx'/'vgx'/…)` on motiongrams/videograms results no longer crashes. It
   selects the matching panel.
- CI on macOS/Windows: skip `.ogg` conversion tests when the FFmpeg build lacks libtheora;
  force the Matplotlib Agg backend in tests (no more Windows `_tkinter` crash).
- Audio cache: methods inherited by `MgVideo` (e.g. `video.spectrogram()`) no longer fail
  on a missing `_y_cache` attribute.

### Added
- `pose(use_cache=True)`: reuse cached keypoints to re-render a different
  `style`/`overlay`/`background` without re-running inference.
- `pose(data_format='c3d')`: export markers to a C3D motion-capture file (optional `c3d` dep).
- `tempogram(onset_strength=False)`: single-panel tempogram matching the chromagram size.
- `beat_statistics(source='motion')` on `MgVideo`: rhythmic-timing statistics from movement onsets.

### Changed
- Average-pose image: labels show numbers only (normalised QoM 0–1 | dominant frequency Hz),
  with stronger de-overlap; QoM reported normalised instead of px/frame.
- `motiontempo()`: QoM normalised to 0–1, panel renamed to "Motion spectrum", with average
  quantity-of-motion and average beat-frequency lines + numbers.

---

## [1.4.6]–2026-06-27

### Added
- Space-time person visualisations (`musicalgestures/_spacetime.py`): `stroboscope()`
  (chronophotography), `silhouette_waterfall()`, `motionhistory()` (Motion History Image),
  and `spacetime_volume()` (3D x,y,t silhouette point cloud). Silhouettes use MediaPipe
  selfie segmentation when available, falling back to background subtraction
  (`method='auto'|'mediapipe'|'bgsub'`).
- `ssm(features='motiongrams', combine=True)` — a single self-similarity matrix from the
  concatenated horizontal + vertical motiongram features (both axes of motion in one display).
- `pose()` `style` now also applies to the average-pose image (markers/skeleton/both).

### Changed
- `pose()`: the no-CUDA fallback now uses the MediaPipe CPU (XNNPACK) delegate (fast, reliable)
  rather than the fragile OpenGL-ES GPU delegate. New `quiet=True` suppresses MediaPipe's native
  C++/GL console logs; explicit `device='gpu'` prints a one-line caveat.

### Fixed
- **Orientation**: portrait/phone videos that store a rotation flag are now normalised at load
  (the rotation is baked into the pixels and the flag removed), so cv2-based processes no longer
  come out rotated 90°. All processes keep the original orientation.

---

## [1.4.5]–2026-06-26

### Added
- `pose()` now also exports an **average-pose image** (each marker coloured/labelled
  by its average quantity of motion in px/frame and dominant movement frequency in Hz,
  with a per-marker stats CSV) and an **all-trajectories image**. Marker labels are laid
  out to avoid overlapping (with leader lines). Options: `save_average_pose`,
  `save_trajectories`, `transparent_trajectories` (transparent background, auto-enabled
  when trajectories are the only export, for overlaying on video).
- `pose()` rendering controls: `style` (`'both'`/`'markers'`/`'skeleton'`), `overlay`
  (draw on the video or a plain background), and `background` (`'black'`/`'white'`, with
  contrast-adapted colours).
- `convert=False` flag on `pose()`, `flow.dense()`/`flow.sparse()`, `directograms()`,
  `impacts()`, `motion_mp()`, and `history_cv2()` to skip the AVI conversion and read the
  source (e.g. mp4) directly.

### Changed
- **Display model**: analysis results (`MgImage`/`MgFigure`) no longer auto-render as a
  notebook cell's last expression. Display happens only via `show()`. HTML is available
  via `to_html()`. `MgList.as_figure()` and `info('frame')` updated accordingly
  (`info('frame')` returns an `MgImage`).
- `blur_faces()` writes **MP4/libx264** (via the FFmpeg pipe) instead of MJPEG-AVI,
  keeping the source container by default.

### Performance
- `MgAudio` caches the decoded audio, so multiple audio analyses decode the file once.
- `ffprobe()` results are cached per file (path+mtime+size), so the metadata helpers share
  a single subprocess call.

### Fixed
- Fixed all "invalid escape sequence" `SyntaxWarning`s on import.
- Documented that `MgVideo.length` is a frame count (`MgAudio.length` is seconds).
- Removed 30 unused imports.

---

## [1.4.4]–2026-06-26

### Added
- `MgVideo.eulerian()` — Eulerian Video Magnification (Wu et al., SIGGRAPH 2012)
  to reveal subtle changes. `mode='color'` amplifies subtle colour changes
  (pulse/breathing) via a Gaussian pyramid + ideal FFT band-pass (two-pass, low
  memory); `mode='motion'` amplifies subtle motion via a Laplacian pyramid +
  streaming IIR band-pass with spatial-wavelength attenuation. Reads/writes through
  the FFmpeg pipe so any format works, addressing the format/memory limitations
  of existing PyEVM ports (closes #212).
- `MgVideo.sonomotiongram()` — sonifies the motiongram by treating it as a
  magnitude spectrogram (spatial position → frequency, motion intensity →
  amplitude) and resynthesising audio via inverse STFT (Griffin–Lim). Returns an
  MgAudio (closes #171).
- `MgVideo.motionvectors()` — visualises the motion vectors carried by inter-frame
  codecs (MPEG/H.264/H.265) using FFmpeg's codecview filter (closes #254).

### Fixed
- EVM/sonomotiongram timing: `MgVideo.length` is a frame count (not seconds), so
  audio duration is computed as `length/fps` and progress is tracked in frames.

---

## [1.4.3]–2026-06-26

### Added
- `MgVideo.heatmap()`: a motion heatmap showing which parts of the video change
  the most (accumulated frame differences, colour-mapped, optionally overlaid on
  the average frame).
- `MgVideo.motiontempo()`: estimates the dominant movement tempo from the quantity
  of motion via FFT, reported in Hz and BPM (addresses #158).
- `descriptors(save_data=True, data_format=...)`: save the per-frame audio
  descriptor time series to csv/tsv/txt, mirroring motiondata (closes #124).
- `pose()` GPU via MediaPipe: `MediaPipePoseEstimator` gains a `device` parameter
  and uses MediaPipe's GPU delegate (CPU fallback). When `device='gpu'` is requested
  for an OpenPose model but OpenCV lacks CUDA, `pose()` auto-switches to the
  MediaPipe backend so the GPU is actually used.
- `cuda_build_available()` and `cuda_unavailable_reason()` helpers.

### Changed
- Display model: `MgImage`/`MgFigure` no longer auto-render as a notebook cell's
  last expression (the rich `_repr_html_`/`_repr_mimebundle_` hooks were removed;
  the HTML helper is kept as `to_html()`). Display now happens only via `show()`,
  removing the duplicate (small + large) outputs for the audio figure methods and
  making `average()` display only when `show()` is called.
- Audio figure methods always close the pyplot figure after saving.
- `MgFigure.show()` renders the saved image (inline in notebooks).
- GPU-fallback messages in `pose()`, optical flow, and CenterFace now explain the
  real cause (pip OpenCV is built without CUDA) instead of implying a missing GPU.

### Fixed
- `spectrogram()`/`descriptors()`: pin the time axis to the actual spectrogram
  extent so a container duration longer than the decoded audio no longer leaves
  trailing whitespace or mislabels the timeline.

---

## [1.4.2]–2026-06-26

### Fixed
- **Critical:** repaired a `thresholdold` corruption (from a botched `thresh`→`threshold`
  replace) that broke the FFmpeg `threshold` filter, leaving `motion()`, `motiongrams()`
  and related functions producing no frames and crashing. Motion analysis works again.
- `skip` with large values no longer crashes: `atempo` filters are chained for ratios
  above FFmpeg's per-filter limit of 100, and colons are stripped from output filenames.
- Restored consistent behaviour of the threshold/filtertype options in `motiongrams()`.

### Added
- `info(type='summary')` now reports video codec/profile, pixel format, colour space,
  and audio codec/sample-rate/bit-rate alongside resolution, frames, fps, and duration.
- `audio.mfcc()`, `audio.tempo()` (beat tracking with tempo, beat times, inter-beat
  intervals and beat regularity), and `audio.beat_statistics()` (circular timing analysis).
- `musicalgestures/_analysis.py`: general signal/statistics utilities (`smooth`,
  `bandpass`, `dominant_frequency`, `circular_stats`, `rayleigh_test`, `synchrony`),
  exported at package level.

---

## [1.4.1]–2026-06-26

### Fixed
- `average()` now correctly ignores both `method=` and `normalize=` legacy kwargs (1.4.0 only filtered `normalize=`).
- Rename `cols` → `columns` parameter in `mg_grid`.
- Added `audio.chromagram()` method.

---

## [1.4.0]–2026-06-26

### Added

#### Phase 1–Foundation
- Migrated project metadata and build configuration to `pyproject.toml` (PEP 517/518/621).
  `setup.py` and `setup.cfg` are now stubs pointing to the new file.
- Raised minimum Python version to 3.10; updated CI matrix to test 3.10, 3.11, and 3.12.
- Added a separate `lint` CI job (ruff + mypy) to catch style and type issues early.
- Added `noxfile.py` for reproducible local development environments (`nox -s tests`, `nox -s lint`, `nox -s coverage`).
- Added optional dependency extras: `musicalgestures[pose]`, `[ml]`, `[cli]`, `[dev]`, `[full]`.
- Added `musicalgestures/_enums.py`: `StrEnum`-based enum types (`FilterType`, `BlurType`, `CropMode`, `PoseModel`, `PoseDevice`, `DataFormat`) with case-insensitive lookup. Fully backward-compatible with existing string parameters.
- Added `musicalgestures/_exceptions.py`: typed exception hierarchy (`MgError` → `MgInputError`, `MgProcessingError`, `MgIOError`, `MgDependencyError`).
- Added `musicalgestures/_logging.py`: module-level `logging.getLogger('musicalgestures')` logger with a `NullHandler` and a `set_log_level()` helper.

#### Phase 2–Data Structures
- Added `musicalgestures/_features.py`: `MgFeatures` – a named time-series container for motion and audio descriptors. Supports `to_numpy()`, `to_dataframe()`, `to_json()`, `from_json()`, `from_dataframe()`, NumPy array protocol, and a rich Jupyter `_repr_html_` display.
- Added `musicalgestures/_stream.py`: `MgVideoReader` – a context-manager-based streaming frame iterator (lazy, low-memory, FFmpeg-backed).
- Added `_repr_html_()` and `_repr_mimebundle_()` to `MgImage` and `MgFigure` for rich inline display in Jupyter notebooks.

#### Phase 3–Pose Modernisation
- Added `musicalgestures/_pose_estimator.py`: abstract `PoseEstimator` base class, `PoseEstimatorResult` container, `MediaPipePoseEstimator` (Google MediaPipe Pose, 33 landmarks, no model download required), `OpenPosePoseEstimator` (compatibility shim for the legacy OpenPose backend), and `get_pose_estimator()` factory function.

#### Phase 4–ML Integration
- Added `musicalgestures/_pipeline.py`: `MgPipeline` – a scikit-learn–style pipeline that chains named `MgStep` objects. Supports `transform()`, `fit()`, `fit_transform()`, and a `describe()` method.
- Added `musicalgestures/_dataset.py`: `MgDataset` – labelled collection of media files with `from_directory()`, `from_json()`, `train_test_split()`, `filter()`, `to_json()`, and Jupyter `_repr_html_`. Also includes `MgCorpus` (directory-scanning convenience subclass) and `MediaItem`.

#### Phase 5–Documentation
- Added `CHANGELOG.md` following the Keep-a-Changelog format.
- Added `CONTRIBUTING.md` with a complete developer guide.

#### Phase 6–Ecosystem
- Added `musicalgestures/cli.py`: click-based command-line interface (`musicalgestures info`, `motion`, `videograms`, `average`, `history`, `motiongrams`, `convert`).
- Updated `musicalgestures/__init__.py` to export all new public classes (`MgFeatures`, `MgVideoReader`, `MgPipeline`, `MgStep`, `MgDataset`, `MgCorpus`, `MediaItem`, `PoseEstimator`, `MediaPipePoseEstimator`, `PoseEstimatorResult`, `get_pose_estimator`, enums, exceptions, `set_log_level`).

### Changed
- `tqdm` added as a core dependency (progress bars in downstream usage).
- CI now installs the package from source (`pip install -e ".[dev]"`) and runs `pytest`.
- `threshold` parameter name is now consistent across all public APIs (previously some paths used `thresh`).
- `contrast` and `brightness` parameters use integer range −100 to 100 (previously ambiguous).
- `blur` parameter only accepts `'None'` and `'Average'` (removed undocumented `'Medium'`).

### Fixed
- `average()` method restored as an alias for `blend(component_mode='average')` (was accidentally removed in a prior refactor).
- `average()` silently accepts legacy kwargs `method=` and `normalize=` for backward compatibility.
- `motiongrams()` and `motion()` silently accept `normalize=` kwarg for backward compatibility.
- OGG video conversion now explicitly specifies `libtheora`/`libvorbis` codecs.
- `from_numpy()` path bug fixed when `path` attribute is set.
- Motiondata fallback corrected for invalid data formats.
- Optical flow video export fixed (replaced broken cv2.VideoWriter with FFmpeg subprocess).
- History feature string-weights parsing fixed.
- Cropping window on Linux no longer stalls on repeated use.
- All examples in `docs/examples.md` updated to match the current API.

### Deprecated
- Python 3.7 and 3.8 are no longer supported. The minimum required version is Python 3.10.

---

## [1.3.3]–2024-01-01

### Changed
- Minor changes for v1.3.3.

---

[Unreleased]: https://github.com/fourMs/MGT-python/compare/v1.12.1...HEAD
[1.12.1]: https://github.com/fourMs/MGT-python/compare/v1.12.0...v1.12.1
[1.12.0]: https://github.com/fourMs/MGT-python/compare/v1.11.4...v1.12.0
[1.11.4]: https://github.com/fourMs/MGT-python/compare/v1.11.3...v1.11.4
[1.6.4]: https://github.com/fourMs/MGT-python/compare/v1.6.3...v1.6.4
[1.6.3]: https://github.com/fourMs/MGT-python/compare/v1.6.2...v1.6.3
[1.6.2]: https://github.com/fourMs/MGT-python/compare/v1.6.1...v1.6.2
[1.6.1]: https://github.com/fourMs/MGT-python/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/fourMs/MGT-python/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/fourMs/MGT-python/compare/v1.4.9...v1.5.0
[1.4.9]: https://github.com/fourMs/MGT-python/compare/v1.4.8...v1.4.9
[1.4.8]: https://github.com/fourMs/MGT-python/compare/v1.4.7...v1.4.8
[1.4.7]: https://github.com/fourMs/MGT-python/compare/v1.4.6...v1.4.7
[1.4.6]: https://github.com/fourMs/MGT-python/compare/v1.4.5...v1.4.6
[1.4.5]: https://github.com/fourMs/MGT-python/compare/v1.4.4...v1.4.5
[1.4.4]: https://github.com/fourMs/MGT-python/compare/v1.4.3...v1.4.4
[1.4.3]: https://github.com/fourMs/MGT-python/compare/v1.4.2...v1.4.3
[1.4.2]: https://github.com/fourMs/MGT-python/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/fourMs/MGT-python/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/fourMs/MGT-python/compare/v1.3.3...v1.4.0
[1.3.3]: https://github.com/fourMs/MGT-python/releases/tag/v1.3.3

# Changelog

All notable changes to MGT-python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [1.6.3] – 2026-06-27

### Changed
- **Faster import**: `import musicalgestures` dropped from ~1.5s to ~0.7s by lazy-loading heavy
  dependencies (`scipy.signal`, `scipy.stats`, `IPython.display`) that are only needed by specific
  methods.
- **Pose model download** now uses Python's `urllib` instead of a bundled Windows `wget.exe` and
  platform-specific shell scripts — removes the 3.8 MB binary from the wheel and is fully
  cross-platform.

### Internal
- Added a `resolve_filename()` helper that centralises the `target_name`/`overwrite` output-path
  logic (the pattern whose copy-paste variants caused the earlier `grid()`/`blend()` bugs); adopted
  it across the single-output video methods and all `MgAudio` methods.
- Added regression tests for the audio–movement suite, `resample()`, the pose renderers, and the
  core-class conveniences (353 → 371 tests).

---

## [1.6.2] – 2026-06-27

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

## [1.6.1] – 2026-06-27

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

## [1.6.0] – 2026-06-27

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

## [1.5.0] – 2026-06-27

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

## [1.4.9] – 2026-06-27

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
- `pose()`: `convert` defaults to `None` ("auto") — MediaPipe reads the source directly (no
  intermediate AVI), OpenPose still converts for frame-accurate decoding. The result video is
  written in the **original container** (mp4 in → mp4 out; no avi→mp4 round-trip).
- Pose images decluttered: removed the titles from the trajectories and waterfall images and
  the average-pose image, and removed the average-pose colorbar. The trajectories image omits
  marker-name labels by default (`trajectory_labels=True` to re-enable).

### Fixed
- The `show(key=...)` orientation keys for motiongrams/videograms were swapped: `'horizontal'`
  now selects the horizontal-movement gram and `'vertical'` the vertical one, with correct titles
  (in both `MgVideo.show` and `MgList.show`).

---

## [1.4.8] – 2026-06-27

### Added
- `pose_waterfall()`: a 3D spatio-temporal waterfall where each marker's trajectory flows
  through (x, time, y) space — a pose-based counterpart to `silhouette_waterfall()`. Reuses
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

## [1.4.7] – 2026-06-27

### Fixed
- **GPU detection**: `_utils.py` never imported `cv2`, so `get_cuda_device_count()` and
  `cuda_build_available()` always reported no CUDA — GPU was never used even with a
  CUDA-enabled OpenCV. Now fixed: `pose(device='gpu')` (OpenPose), `flow.dense(use_gpu=True)`,
  and `flow.sparse(use_gpu=True)` use the GPU on a CUDA build.
- GPU sparse optical flow: corrected point shapes (1×N CV_32FC2) and `calc()` return
  handling so the CUDA path works (it was never exercised before the detection fix).
- `MgList.show(key='mgx'/'vgx'/…)` on motiongrams/videograms results no longer crashes —
  it selects the matching panel.
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

## [1.4.6] – 2026-06-27

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

## [1.4.5] – 2026-06-26

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
  notebook cell's last expression — display happens only via `show()`. HTML is available
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

## [1.4.4] – 2026-06-26

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

## [1.4.3] – 2026-06-26

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

## [1.4.2] – 2026-06-26

### Fixed
- **Critical:** repaired a `thresholdold` corruption (from a botched `thresh`→`threshold`
  replace) that broke the FFmpeg `threshold` filter, leaving `motion()`, `motiongrams()`
  and related functions producing no frames and crashing. Motion analysis works again.
- `skip` with large values no longer crashes: `atempo` filters are chained for ratios
  above FFmpeg's per-filter limit of 100, and colons are stripped from output filenames.
- Restored consistent behaviour of the threshold/filtertype options in `motiongrams()`.

### Added
- `info(type='summary')` now reports video codec/profile, pixel format, color space,
  and audio codec/sample-rate/bit-rate alongside resolution, frames, fps, and duration.
- `audio.mfcc()`, `audio.tempo()` (beat tracking with tempo, beat times, inter-beat
  intervals and beat regularity), and `audio.beat_statistics()` (circular timing analysis).
- `musicalgestures/_analysis.py`: general signal/statistics utilities (`smooth`,
  `bandpass`, `dominant_frequency`, `circular_stats`, `rayleigh_test`, `synchrony`),
  exported at package level.

---

## [1.4.1] – 2026-06-26

### Fixed
- `average()` now correctly ignores both `method=` and `normalize=` legacy kwargs (1.4.0 only filtered `normalize=`).
- Rename `cols` → `columns` parameter in `mg_grid`.
- Added `audio.chromagram()` method.

---

## [1.4.0] – 2026-06-26

### Added

#### Phase 1 – Foundation
- Migrated project metadata and build configuration to `pyproject.toml` (PEP 517/518/621).
  `setup.py` and `setup.cfg` are now stubs pointing to the new file.
- Raised minimum Python version to 3.10; updated CI matrix to test 3.10, 3.11, and 3.12.
- Added a separate `lint` CI job (ruff + mypy) to catch style and type issues early.
- Added `noxfile.py` for reproducible local development environments (`nox -s tests`, `nox -s lint`, `nox -s coverage`).
- Added optional dependency extras: `musicalgestures[pose]`, `[ml]`, `[cli]`, `[dev]`, `[full]`.
- Added `musicalgestures/_enums.py`: `StrEnum`-based enum types (`FilterType`, `BlurType`, `CropMode`, `PoseModel`, `PoseDevice`, `DataFormat`) with case-insensitive lookup. Fully backward-compatible with existing string parameters.
- Added `musicalgestures/_exceptions.py`: typed exception hierarchy (`MgError` → `MgInputError`, `MgProcessingError`, `MgIOError`, `MgDependencyError`).
- Added `musicalgestures/_logging.py`: module-level `logging.getLogger('musicalgestures')` logger with a `NullHandler` and a `set_log_level()` helper.

#### Phase 2 – Data Structures
- Added `musicalgestures/_features.py`: `MgFeatures` – a named time-series container for motion and audio descriptors. Supports `to_numpy()`, `to_dataframe()`, `to_json()`, `from_json()`, `from_dataframe()`, NumPy array protocol, and a rich Jupyter `_repr_html_` display.
- Added `musicalgestures/_stream.py`: `MgVideoReader` – a context-manager-based streaming frame iterator (lazy, low-memory, FFmpeg-backed).
- Added `_repr_html_()` and `_repr_mimebundle_()` to `MgImage` and `MgFigure` for rich inline display in Jupyter notebooks.

#### Phase 3 – Pose Modernisation
- Added `musicalgestures/_pose_estimator.py`: abstract `PoseEstimator` base class, `PoseEstimatorResult` container, `MediaPipePoseEstimator` (Google MediaPipe Pose, 33 landmarks, no model download required), `OpenPosePoseEstimator` (compatibility shim for the legacy OpenPose backend), and `get_pose_estimator()` factory function.

#### Phase 4 – ML Integration
- Added `musicalgestures/_pipeline.py`: `MgPipeline` – a scikit-learn–style pipeline that chains named `MgStep` objects. Supports `transform()`, `fit()`, `fit_transform()`, and a `describe()` method.
- Added `musicalgestures/_dataset.py`: `MgDataset` – labelled collection of media files with `from_directory()`, `from_json()`, `train_test_split()`, `filter()`, `to_json()`, and Jupyter `_repr_html_`. Also includes `MgCorpus` (directory-scanning convenience subclass) and `MediaItem`.

#### Phase 5 – Documentation
- Added `CHANGELOG.md` following the Keep-a-Changelog format.
- Added `CONTRIBUTING.md` with a complete developer guide.

#### Phase 6 – Ecosystem
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

## [1.3.3] – 2024-01-01

### Changed
- Minor changes for v1.3.3.

---

[Unreleased]: https://github.com/fourMs/MGT-python/compare/v1.6.3...HEAD
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

# Changelog

All notable changes to MGT-python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/fourMs/MGT-python/compare/v1.4.5...HEAD
[1.4.5]: https://github.com/fourMs/MGT-python/compare/v1.4.4...v1.4.5
[1.4.4]: https://github.com/fourMs/MGT-python/compare/v1.4.3...v1.4.4
[1.4.3]: https://github.com/fourMs/MGT-python/compare/v1.4.2...v1.4.3
[1.4.2]: https://github.com/fourMs/MGT-python/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/fourMs/MGT-python/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/fourMs/MGT-python/compare/v1.3.3...v1.4.0
[1.3.3]: https://github.com/fourMs/MGT-python/releases/tag/v1.3.3

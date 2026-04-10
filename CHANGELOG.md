# Changelog

All notable changes to MGT-python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

### Deprecated
- Python 3.7 and 3.8 are no longer supported. The minimum required version is Python 3.10.

---

## [1.3.3] – 2024-01-01

### Changed
- Minor changes for v1.3.3.

---

[Unreleased]: https://github.com/fourMs/MGT-python/compare/v1.3.3...HEAD
[1.3.3]: https://github.com/fourMs/MGT-python/releases/tag/v1.3.3

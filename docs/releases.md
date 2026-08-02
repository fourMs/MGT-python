# Release Notes

The current stable release is **MGT-python 1.6.9**.

Install or upgrade from PyPI:

```bash
pip install --upgrade musicalgestures
```

## Full changelog

The complete, version-by-version history—including every Added / Changed / Fixed entry—is
maintained in the [CHANGELOG](https://github.com/fourMs/MGT-python/blob/master/CHANGELOG.md),
which is the single source of truth for release notes.

## Recent highlights

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

# Release Notes

The current stable release is **MGT-python 1.6.0**.

Install or upgrade from PyPI:

```bash
pip install --upgrade musicalgestures
```

## Full changelog

The complete, version-by-version history — including every Added / Changed / Fixed entry — is
maintained in the [CHANGELOG](https://github.com/fourMs/MGT-python/blob/master/CHANGELOG.md),
which is the single source of truth for release notes.

## Recent highlights

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

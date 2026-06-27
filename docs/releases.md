# Release Notes

The current stable release is **MGT-python 1.4.8**.

Install or upgrade from PyPI:

```bash
pip install --upgrade musicalgestures
```

## Full changelog

The complete, version-by-version history — including every Added / Changed / Fixed entry — is
maintained in the [CHANGELOG](https://github.com/fourMs/MGT-python/blob/master/CHANGELOG.md),
which is the single source of truth for release notes.

## Recent highlights

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

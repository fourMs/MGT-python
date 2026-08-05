# Audio Video

> Auto-generated documentation for [musicalgestures._audio_video](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio_video.py) module.

Audio–movement comparison reports for a single performer: tools to reveal how a dancer's
movement relates to the sound — phase synchrony, structural similarity, per-body-part coupling,
and energy/dynamics coupling.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Audio Video
    - [mg_body_audio_coupling](#mg_body_audio_coupling)
    - [mg_dynamics_coupling](#mg_dynamics_coupling)
    - [mg_phase_synchrony](#mg_phase_synchrony)
    - [mg_structure_comparison](#mg_structure_comparison)

All functions are bound as ``MgVideo`` methods and return an ``MgFigure`` (with the numeric
results in ``.data``); most also save a CSV next to the image.

## mg_body_audio_coupling

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio_video.py#L238)

```python
def mg_body_audio_coupling(
    self,
    dpi: int = 300,
    cmap: str = 'coolwarm',
    dot_size: int = 260,
    autoshow: bool = True,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
    **pose_kwargs,
) -> 'MgFigure':
```

Map which body parts are most rhythmically coupled to the music.

For every pose marker the per-frame speed is correlated with the audio onset-strength
envelope (sampled at the video frame rate). The result is shown as a body map — the average
pose with each marker coloured by its correlation — plus a sorted bar chart, and a CSV of the
per-marker correlations. Uses cached pose keypoints when available, otherwise runs ``pose()``
first (``**pose_kwargs`` are forwarded).

Returns an MgFigure (per-marker correlations in ``.data``), or None if the video has no audio.

## mg_dynamics_coupling

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio_video.py#L337)

```python
def mg_dynamics_coupling(
    self,
    fs: float = 50.0,
    max_lag: float = 2.0,
    dpi: int = 300,
    autoshow: bool = True,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgFigure':
```

Compare audio **loudness** with movement **quantity** — does the dancer move more when the
music is louder?

Aligns the audio RMS-loudness envelope with the quantity-of-motion envelope and reports their
correlation (at zero lag and at the best lag within ``max_lag`` seconds). The figure overlays
the two normalised envelopes and shows a scatter of loudness vs. motion.

Returns an MgFigure (metrics in ``.data``), or None if the video has no audio.

## mg_phase_synchrony

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio_video.py#L67)

```python
def mg_phase_synchrony(
    self,
    fmin: float = 0.5,
    fmax: float = 4.0,
    fs: float = 50.0,
    n_bins: int = 36,
    dpi: int = 300,
    autoshow: bool = True,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgFigure':
```

Quantify how phase-locked the movement is to the audio rhythm.

Both the audio onset-strength envelope and the movement quantity-of-motion envelope are
band-pass filtered to the tempo band [``fmin``, ``fmax``] Hz, and their instantaneous phases
(via the Hilbert transform) are compared. The **phase-locking value** (PLV, 0–1) summarises the
consistency of the audio↔movement phase difference; a polar histogram shows its distribution.

Returns an MgFigure (metrics in ``.data``), or None if the video has no audio.

## mg_structure_comparison

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio_video.py#L158)

```python
def mg_structure_comparison(
    self,
    n: int = 200,
    dpi: int = 300,
    cmap: str = 'magma',
    autoshow: bool = True,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgFigure':
```

Compare the temporal **structure** of the audio with that of the movement.

Builds a self-similarity matrix (SSM) of the audio (from MFCC frames) and of the video
(from low-resolution frame appearance), resampled to the same ``n`` time points, and shows
them side by side with their absolute **difference map** — bright regions in the difference
are where the musical structure and the movement structure diverge.

Returns an MgFigure (mean structural agreement in ``.data``), or None if the video has no audio.

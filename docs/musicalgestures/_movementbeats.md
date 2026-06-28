# Movementbeats

> Auto-generated documentation for [musicalgestures._movementbeats](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_movementbeats.py) module.

Movement-based beat statistics: detect rhythmic onsets in a video's quantity of motion
and compute the same circular timing statistics as the audio ``beat_statistics()``.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Movementbeats
    - [mg_beat_statistics](#mg_beat_statistics)
    - [mg_tempo_similarity](#mg_tempo_similarity)

This lets ``MgVideo.beat_statistics(source='motion')`` reveal how consistent the *movement*
rhythm is, analogous to the audio version.

## mg_beat_statistics

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_movementbeats.py#L54)

```python
def mg_beat_statistics(
    self,
    source: str = 'motion',
    n_bins: int = 32,
    cmap: str = 'YlOrRd',
    dpi: int = 300,
    autoshow: bool = True,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
    fmin: float = 0.2,
    fmax: float = 8.0,
) -> 'MgFigure':
```

Circular statistics of beat-timing consistency, from the **audio** or from the **movement**.

Fits an ideal isochronous beat grid to the detected beats and visualises how each beat
deviates from it (a polar phase histogram with the mean resultant vector, plus a
millisecond-deviation time series), revealing whether the rhythm rushes, drags, or stays
steady. Requires at least four detected beats.

#### Arguments

- `source` *str, optional* - `'motion'` (default) detects rhythmic onsets in the video's
    quantity of motion and analyses the **movement** rhythm; `'audio'` analyses the
    audio track instead (same as `MgAudio.beat_statistics` / `video.audio.beat_statistics`).
- `n_bins` *int, optional* - Bins in the polar phase histogram. Defaults to 32.
- `cmap` *str, optional* - Colormap for the polar histogram. Defaults to 'YlOrRd'.
- `dpi` *int, optional* - Output DPI. Defaults to 300.
- `autoshow` *bool, optional* - Kept for API parity (display is via show()). Defaults to True.
- `title` *str, optional* - Optional figure title; use 'filename' for the file name. Defaults to None.
- `target_name` *str, optional* - Output image name. Defaults to None.
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.
- `fmin` *float, optional* - Lowest movement-onset rate to consider (Hz), 'motion' only. Defaults to 0.2.
- `fmax` *float, optional* - Highest movement-onset rate to consider (Hz), 'motion' only. Defaults to 8.0.

#### Returns

- `MgFigure` - figure with the beat statistics in ``.data``, or None if too few beats.

## mg_tempo_similarity

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_movementbeats.py#L202)

```python
def mg_tempo_similarity(
    self,
    dpi: int = 300,
    autoshow: bool = True,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgFigure':
```

Compare the **audio** tempo/rhythm with the **movement** tempo/rhythm and report how similar
they are.

Estimates the tempo of the audio track (from its onset-strength envelope) and of the movement
(from the quantity-of-motion envelope), then aligns the two normalised envelopes and
cross-correlates them to measure rhythmic agreement. The figure shows the two envelopes
overlaid and their cross-correlation; the report (also saved as a CSV) lists the audio tempo,
movement tempo, their ratio and nearest harmonic relationship, the peak cross-correlation, and
the lag (s) at which the movement best aligns with the audio.

#### Arguments

- `dpi` *int, optional* - Output DPI. Defaults to 300.
- `autoshow` *bool, optional* - Kept for API parity (display via show()). Defaults to True.
- `title` *str, optional* - Optional figure title; 'filename' uses the file name. Defaults to None.
- `target_name` *str, optional* - Output image name. Defaults to None ("_tempo_similarity.png").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.

#### Returns

- `MgFigure` - the report figure (metrics in ``.data``), or None if the video has no audio.

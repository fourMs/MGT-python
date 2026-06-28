# Motiontempo

> Auto-generated documentation for [musicalgestures._motiontempo](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motiontempo.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Motiontempo
    - [mg_motiontempo](#mg_motiontempo)

## mg_motiontempo

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motiontempo.py#L8)

```python
def mg_motiontempo(
    self,
    fmin=0.2,
    fmax=8.0,
    dpi=300,
    autoshow=True,
    title=None,
    target_name=None,
    overwrite=True,
) -> 'MgFigure':
```

Estimates the dominant movement tempo of a video from its quantity of motion.

A quantity-of-motion (QoM) signal is computed as the mean absolute difference
between consecutive frames. Its dominant periodicity within ``[fmin, fmax]`` is
found with an FFT and reported both in Hz and in beats per minute (BPM), giving a
simple estimate of the overall movement tempo (e.g. step rate of a dancer).

#### Arguments

- `fmin` *float, optional* - Lowest movement frequency to consider (Hz). Defaults to 0.2.
- `fmax` *float, optional* - Highest movement frequency to consider (Hz). Defaults to 8.0.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add a title to the figure. Use 'filename' for the file name. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None
    (which uses the input filename with the suffix "_motiontempo.png").
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to
    automatically increment the target filename. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object. Numeric results are available in ``.data``:
    'tempo_bpm', 'dominant_frequency', 'qom', 'times', 'freqs', 'spectrum', 'fps'.

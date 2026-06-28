# Motiondescriptors

> Auto-generated documentation for [musicalgestures._motiondescriptors](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motiondescriptors.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Motiondescriptors
    - [mg_motiondescriptors](#mg_motiondescriptors)

## mg_motiondescriptors

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motiondescriptors.py#L86)

```python
def mg_motiondescriptors(
    self,
    window: str = 'hann',
    entropy_bins: int = 50,
    save_data: bool = True,
    save_plot: bool = True,
    data_format: str = 'csv',
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgFigure':
```

Scalar movement descriptors derived from the quantity-of-motion (QoM) signal.

Computes a compact set of higher-level descriptors that summarise *how* something moves,
complementing the per-frame motion data from :func:`motion`:

- **motion_energy** — mean squared QoM; the overall amount of movement.
- **motion_smoothness** — SPARC (spectral arc length) of the QoM profile; a dimensionless,
  validated smoothness metric (less negative = smoother, more negative = jerkier).
- **motion_entropy** — normalised (0–1) Shannon entropy of the QoM magnitude distribution;
  the complexity/variedness of the motion.
- **spectral descriptors** of the QoM signal (Hann-windowed by default): the **dominant
  frequency** (Hz, the main movement-rhythm rate) and the **spectral centroid** (Hz, the
  "centre of mass" of the movement spectrum).

#### Arguments

- `window` *str, optional* - FFT window for the spectral descriptors — 'hann' (default,
    recommended to reduce leakage) or 'none' for a rectangular window.
- `entropy_bins` *int, optional* - Number of histogram bins for the entropy estimate. Defaults to 50.
- `save_data` *bool, optional* - Save the descriptors to a data file. Defaults to True.
- `save_plot` *bool, optional* - Save the figure (QoM time series + power spectrum). Defaults to True.
- `data_format` *str, optional* - Data file format: 'csv', 'tsv' or 'txt'. Defaults to 'csv'.
- `target_name` *str, optional* - Output image name. Defaults to None (``<name>_motiondescriptors.png``).
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.

#### Returns

- `MgFigure` - figure whose ``.data`` holds the scalar descriptors and the spectrum arrays
(``frequencies``, ``power``), or None if there are too few frames.

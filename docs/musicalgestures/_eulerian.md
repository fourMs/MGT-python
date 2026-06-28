# Eulerian

> Auto-generated documentation for [musicalgestures._eulerian](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_eulerian.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Eulerian
    - [mg_eulerian](#mg_eulerian)

## mg_eulerian

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_eulerian.py#L54)

```python
def mg_eulerian(
    self,
    mode='color',
    freq_low=0.83,
    freq_high=1.0,
    amplification=50,
    levels=4,
    chroma_attenuation=1.0,
    lambda_cutoff=16,
    target_name=None,
    overwrite=True,
) -> 'musicalgestures.MgVideo':
```

Applies Eulerian Video Magnification (EVM) to reveal subtle changes in a video.

EVM amplifies small temporal variations that are normally invisible. Two modes are
available:

* ``mode='color'`` — amplifies subtle **colour** changes (e.g. blood flow / pulse,
  breathing). Uses a Gaussian pyramid and an ideal (FFT) temporal band-pass filter.
  Processed in two passes so only a small down-sampled stack is held in memory.
* ``mode='motion'`` — amplifies subtle **motion**. Uses a Laplacian pyramid with a
  streaming IIR temporal band-pass filter and spatial-wavelength attenuation, so it
  runs frame-by-frame with low memory use.

Based on Wu et al., "Eulerian Video Magnification for Revealing Subtle Changes in the
World" (SIGGRAPH 2012).

#### Arguments

- `mode` *str, optional* - 'color' or 'motion'. Defaults to 'color'.
- `freq_low` *float, optional* - Lower temporal cutoff in Hz. Defaults to 0.83 (~50 bpm).
- `freq_high` *float, optional* - Upper temporal cutoff in Hz. Defaults to 1.0 (~60 bpm).
- `amplification` *float, optional* - Amplification factor (alpha). Defaults to 50.
- `levels` *int, optional* - Number of spatial pyramid levels. Defaults to 4.
- `chroma_attenuation` *float, optional* - Chrominance attenuation in [0, 1] (color mode).
    Lower values reduce colour artefacts. Defaults to 1.0.
- `lambda_cutoff` *float, optional* - Spatial wavelength cutoff for amplitude attenuation
    (motion mode). Defaults to 16.
- `target_name` *str, optional* - Target output name. Defaults to None (input filename with
    the suffix "_evm").
- `overwrite` *bool, optional* - Whether to allow overwriting or auto-increment the filename.
    Defaults to True.

#### Returns

- `MgVideo` - An MgVideo pointing to the magnified output video.

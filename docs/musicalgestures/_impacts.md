# Impacts

> Auto-generated documentation for [musicalgestures._impacts](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_impacts.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Impacts
    - [impact_detection](#impact_detection)
    - [impact_envelope](#impact_envelope)
    - [mg_impacts](#mg_impacts)

## impact_detection

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_impacts.py#L44)

```python
def impact_detection(envelopes, time, fps, local_mean=0.1, local_maxima=0.15):
```

## impact_envelope

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_impacts.py#L26)

```python
def impact_envelope(directogram: np.ndarray, kernel_size: int = 5):
```

## mg_impacts

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_impacts.py#L64)

```python
def mg_impacts(
    self,
    title: str | None = None,
    detection: bool = True,
    local_mean: float = 0.1,
    local_maxima: float = 0.15,
    filtertype: str = 'Adaptative',
    threshold: float = 0.05,
    kernel_size: int = 5,
    convert: bool = True,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgFigure':
```

Compute a visual analogue of an onset envelope, aslo known as an impact envelope (Abe Davis).
This is computed by summing over positive entries in the columns of the directogram. This gives an impact envelope with precisely the same
form as an onset envelope. To account for large outlying spikes that sometimes happen at shot boundaries (i.e., cuts), the 99th percentile
of the impact envelope values are clipped to the 98th percentile. Then, the impact envelopes are normalised by their maximum to make calculations
more consistent across video resolutions. Fianlly, the local mean of the impact envelopes are calculated using a 0.1-second window, and local maxima
using a 0.15-second window. Impacts are defined as local maxima that are above their local mean by at least 10% of the envelope’s global maximum.

Source: Abe Davis -- [Visual Rhythm and Beat](http://www.abedavis.com/files/papers/VisualRhythm_Davis18.pdf) (section 4.2 and 4.3)

#### Arguments

- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses 'Directogram' as a title. Defaults to None.
- `detection` *bool, optional* - Whether to allow the detection of impacts based on local mean and local maxima or not.
- `local_mean` *float, optional* - Size of the local mean window in seconds which reduces the amount of intensity variation between one impact and the next.
- `local_maxima` *float, optional* - Size of the local maxima window in seconds for the impact envelopes
- `filtertype` *str, optional* - 'Regular' turns all values below `threshold` to 0. 'Binary' turns all values below `threshold` to 0, above `threshold` to 1. 'Blob' removes individual pixels with erosion method. 'Adaptative' perform adaptative threshold as the weighted sum of 11 neighborhood pixels where weights are a Gaussian window. Defaults to 'Adaptative'.
- `threshold` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `kernel_size` *int, optional* - Size of structuring element. Defaults to 5.
- `convert` *bool, optional* - If True (default), non-AVI input is first converted to an all-intra MJPEG `.avi` (cached as `self.as_avi`) for frame-accurate decoding. Set to False to read the source file directly. Defaults to True.
- `target_name` *str, optional* - Target output name for the impacts figure. Defaults to None (which assumes that the input filename with the suffix "_impacts" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

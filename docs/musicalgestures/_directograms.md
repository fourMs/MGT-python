# Directograms

> Auto-generated documentation for [musicalgestures._directograms](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_directograms.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Directograms
    - [directogram](#directogram)
    - [matrix3D_norm](#matrix3d_norm)
    - [mg_directograms](#mg_directograms)

## directogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_directograms.py#L24)

```python
@jit(nopython=True)
def directogram(optical_flow):
```

## matrix3D_norm

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_directograms.py#L14)

```python
@jit(nopython=True)
def matrix3D_norm(matrix):
```

## mg_directograms

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_directograms.py#L39)

```python
def mg_directograms(
    self,
    title=None,
    filtertype='Adaptative',
    thresh=0.05,
    kernel_size=5,
    target_name=None,
    overwrite=False,
):
```

Compute a directogram to factor the magnitude of motion into different angles.
Each columun of the directogram is computed as the weighted histogram (HISTOGRAM_BINS) of angles for the optical flow of an input frame.

Source: Abe Davis -- [Visual Rhythm and Beat](http://www.abedavis.com/files/papers/VisualRhythm_Davis18.pdf) (section 4.1)

#### Arguments

- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses 'Directogram' as a title. Defaults to None.
- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. 'Adaptative' perform adaptative threshold as the weighted sum of 11 neighborhood pixels where weights are a Gaussian window. Defaults to 'Adaptative'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `kernel_size` *int, optional* - Size of structuring element. Defaults to 5.
- `target_name` *str, optional* - Target output name for the directogram. Defaults to None (which assumes that the input filename with the suffix "_dg" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - A MgFigure object referring to the internal figure and its data.

# Warp

> Auto-generated documentation for [musicalgestures._warp](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_warp.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Warp
    - [beats_diff](#beats_diff)
    - [mg_warp_audiovisual_beats](#mg_warp_audiovisual_beats)

## beats_diff

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_warp.py#L14)

```python
@jit(nopython=True)
def beats_diff(beats, media):
```

## mg_warp_audiovisual_beats

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_warp.py#L21)

```python
def mg_warp_audiovisual_beats(
    self,
    audio_file,
    speed=(0.5, 2),
    data=None,
    filtertype='Adaptative',
    thresh=0.05,
    kernel_size=5,
    target_name=None,
    overwrite=False,
):
```

Warp audio beats with visual beats (patterns of motion that can be shifted in time to control visual rhythm).
Visual beats are warped after computing a directogram which factors the magnitude of motion in the video into different angles.

Source: Abe Davis -- [Visual Rhythm and Beat](http://www.abedavis.com/files/papers/VisualRhythm_Davis18.pdf) (section 5)

#### Arguments

- `audio_file` *str* - Path to the audio file.
- `speed` *tuple, optional* - Speed's change between the audiovisual beats which can be adjusted to slow down or speed up the visual rhythms. Defaults to (0.5,2).
- `data` *array_like, optional* - Computed directogram data can be added separately to avoid the directogram processing time (which can be quite long). Defaults to None.
- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. 'Adaptative' perform adaptative threshold as the weighted sum of 11 neighborhood pixels where weights are a Gaussian window. Defaults to 'Adaptative'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `kernel_size` *int, optional* - Size of structuring element. Defaults to 5.
- `target_name` *str, optional* - Target output name for the directogram. Defaults to None (which assumes that the input filename with the suffix "_dg" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgVideo` - A MgVideo as warp_audiovisual_beats for parent MgVideo

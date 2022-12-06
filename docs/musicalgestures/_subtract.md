# Subtract

> Auto-generated documentation for [musicalgestures._subtract](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_subtract.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Subtract
    - [mg_subtract](#mg_subtract)

## mg_subtract

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_subtract.py#L8)

```python
def mg_subtract(
    self,
    color=True,
    filtertype=None,
    threshold=0.05,
    blur=False,
    curves=0.15,
    use_median=False,
    kernel_size=5,
    bg_img=None,
    bg_color='#000000',
    target_name=None,
    overwrite=False,
):
```

Renders horizontal and vertical motiongrams using ffmpeg.

#### Arguments

- `color` *bool, optional* - If False the input is converted to grayscale at the start of the process. This can significantly reduce render time. Defaults to True.
- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `threshold` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *bool, optional* - Whether to apply a smartblur ffmpeg filter or not. Defaults to False.
- `curves` *int, optional* - Apply curves and equalisation threshold filter to subtract the background. Ranges from 0 to 1. Defaults to 0.15.
- `use_median` *bool, optional* - If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
- `kernel_size` *int, optional* - Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
- `bg_img` *str, optional* - Path to a background image (.png) that needs to be subtracted from the video. If set to None, it uses an average image of all frames in the video. Defaults to None.
- `bg_color` *str, optional* - Set the background color in the video file in hex value. Defaults to '#000000' (black).
- `target_name` *str, optional* - Target output name for the motiongram. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the output horizontal motiongram.

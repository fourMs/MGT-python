# Filter

> Auto-generated documentation for [musicalgestures._filter](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_filter.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Filter
    - [filter_frame](#filter_frame)
    - [filter_frame_ffmpeg](#filter_frame_ffmpeg)

## filter_frame

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_filter.py#L7)

```python
def filter_frame(motion_frame, filtertype, threshold, kernel_size):
```

Applies a threshold filter and then a median filter (of `kernel_size`x`kernel_size`) to an image or videoframe.

#### Arguments

- `motion_frame` *np.array(uint8)* - Input motion image.
- `filtertype` *str* - 'Regular' turns all values below `threshold` to 0. 'Binary' turns all values below `threshold` to 0, above `threshold` to 1. 'Blob' removes individual pixels with erosion method.
- `threshold` *float* - A number in the range of 0 to 1. Eliminates pixel values less than given threshold.
- `kernel_size` *int* - Size of structuring element.

#### Returns

- `np.array(uint8)` - The filtered frame.

## filter_frame_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_filter.py#L32)

```python
def filter_frame_ffmpeg(
    filename,
    cmd,
    color,
    blur,
    filtertype,
    threshold,
    kernel_size,
    use_median,
    invert=False,
):
```

Builds an FFmpeg filter-complex string for frame differencing, thresholding and optional median filtering.

#### Arguments

- `filename` *str* - Path to the input video file (used to derive frame dimensions).
- `cmd` *list* - Base FFmpeg command list to which extra inputs are appended in-place.
- `color` *bool* - If True, use gbrp pixel format; otherwise gray.
- `blur` *str* - 'Average' applies a 10×10 box blur before differencing; 'None' skips it.
- `filtertype` *str* - 'Regular' thresholds frame differences; 'Binary' binarises them; 'Blob' erodes.
- `threshold` *float* - Pixel-value threshold in the range 0–1.
- `kernel_size` *int* - Radius for the median or erosion filter.
- `use_median` *bool* - If True, apply a median filter after thresholding.
- `invert` *bool, optional* - If True, negate the output. Defaults to False.

#### Returns

- `tuple[list,` *str]* - Updated `cmd` list and the assembled filter-complex string.

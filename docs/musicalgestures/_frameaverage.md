# Frameaverage

> Auto-generated documentation for [musicalgestures._frameaverage](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_frameaverage.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Frameaverage
    - [mg_pixelarray](#mg_pixelarray)
    - [mg_pixelarray_cv2](#mg_pixelarray_cv2)
    - [mg_pixelarray_stats](#mg_pixelarray_stats)

## mg_pixelarray

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_frameaverage.py#L7)

```python
def mg_pixelarray(self, width=640, target_name=None, overwrite=False):
```

Creates a 'Frame-Averaged Pixel Array' of a video by reducing each frame to a single pixel
and arranging all frames into a single image. This is equivalent to the bash script that
scales each frame to 1x1 pixel and then tiles them into a grid.

Based on the original bash script concept:
- Each frame is reduced to a single pixel (average color of the frame)
- All pixel values are arranged in a grid with specified width
- Height is calculated automatically based on total frames and width

#### Arguments

- `width` *int, optional* - Width of the output image in pixels (number of frame-pixels per row).
                      Defaults to 640.
- `target_name` *str, optional* - The name of the output image file. If None, uses input filename
                           with '_framearray_<width>' suffix. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically
                          increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgImage` - A new MgImage pointing to the output frame-averaged pixel array image file.

## mg_pixelarray_cv2

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_frameaverage.py#L62)

```python
def mg_pixelarray_cv2(self, width=640, target_name=None, overwrite=False):
```

Alternative implementation using OpenCV for more control over the process.
Creates a 'Frame-Averaged Pixel Array' by reading each frame, calculating its average color,
and arranging these average colors in a grid.

#### Arguments

- `width` *int, optional* - Width of the output image in pixels. Defaults to 640.
- `target_name` *str, optional* - The name of the output image file. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files. Defaults to False.

#### Returns

- `MgImage` - A new MgImage pointing to the output frame-averaged pixel array image file.

## mg_pixelarray_stats

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_frameaverage.py#L144)

```python
def mg_pixelarray_stats(self, width=640, include_stats=True):
```

Creates a frame-averaged pixel array and optionally returns statistics about the video.
This function provides additional information similar to the bash script's output.

#### Arguments

- `width` *int, optional* - Width of the output image in pixels. Defaults to 640.
- `include_stats` *bool, optional* - Whether to return detailed statistics. Defaults to True.

#### Returns

- `dict` - Dictionary containing the generated MgImage and optional statistics.

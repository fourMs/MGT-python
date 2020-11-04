# Filter

> Auto-generated documentation for [\_filter](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_filter.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Filter
  - [filter_frame](#filter_frame)

## filter_frame

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_filter.py#L6)

```python
def filter_frame(motion_frame, filtertype, thresh, kernel_size):
```

Applies a threshold filter and then a median filter (of `kernel_size`x`kernel_size`) to an image or videoframe.

#### Arguments

- `motion_frame` _np.array(uint8)_ - Input motion image.
- `filtertype` _str_ - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method.
- `thresh` _float_ - A number in the range of 0 to 1. Eliminates pixel values less than given threshold.
- `kernel_size` _int_ - Size of structuring element.

#### Returns

- `np.array(uint8)` - The filtered frame.

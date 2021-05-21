# Filter

> Auto-generated documentation for [_filter](git config --get remote.origin.url_filter.py) module.

- [musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Filter
    - [filter_frame](#filter_frame)

## filter_frame

[[find in source code]](git config --get remote.origin.url_filter.py#L6)

```python
def filter_frame(motion_frame, filtertype, thresh, kernel_size):
```

Applies a threshold filter and then a median filter (of `kernel_size`x`kernel_size`) to an image or videoframe.

#### Arguments

- `motion_frame` *np.array(uint8)* - Input motion image.
- `filtertype` *str* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method.
- `thresh` *float* - A number in the range of 0 to 1. Eliminates pixel values less than given threshold.
- `kernel_size` *int* - Size of structuring element.

#### Returns

- `np.array(uint8)` - The filtered frame.

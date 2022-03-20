# Centroid

> Auto-generated documentation for [_centroid](https://github.com/fourMs/MGT-python/blob/main/_centroid.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Centroid
    - [centroid](#centroid)

## centroid

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_centroid.py#L5)

```python
def centroid(image, width, height):
```

Computes the centroid of an image or frame.

#### Arguments

- `image` *np.array(uint8)* - The input image matrix for the centroid estimation function.
- `width` *int* - The pixel width of the input video capture.
- `height` *int* - The pixel height of the input video capture.

#### Returns

- `np.array(2)` - X and Y coordinates of the centroid of motion.
- `int` - Quantity of motion: How large the change was in pixels.

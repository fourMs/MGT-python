# Motionanalysis

> Auto-generated documentation for [musicalgestures._motionanalysis](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motionanalysis.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Motionanalysis
    - [area](#area)
    - [centroid](#centroid)

## area

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motionanalysis.py#L41)

```python
def area(motion_frame, height, width):
```

## centroid

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motionanalysis.py#L5)

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

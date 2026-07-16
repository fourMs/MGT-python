# Motionanalysis

> Auto-generated documentation for [musicalgestures._motionanalysis](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motionanalysis.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Motionanalysis
    - [area](#area)
    - [centroid](#centroid)
    - [motiongram_data](#motiongram_data)

## area

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motionanalysis.py#L96)

```python
def area(motion_frame, height, width):
```

## centroid

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motionanalysis.py#L59)

```python
def centroid(image, width, height):
```

Computes the centroid and quantity of motion in an image or frame.

#### Arguments

- `image` *np.array(uint8)* - The input image matrix for the centroid estimation function.
- `width` *int* - The pixel width of the input video capture.
- `height` *int* - The pixel height of the input video capture.

#### Returns

- `np.array(2)` - X and Y coordinates of the centroid of motion.
- `int` - Quantity of motion: How large the change was in pixels.

## motiongram_data

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motionanalysis.py#L5)

```python
def motiongram_data(
    frames,
    orientation='vertical',
    frame_diff=True,
    normalize=True,
):
```

Compute a motiongram as a plain numpy array from a stack of grayscale
frames, with a selectable orientation.

With `orientation="vertical"` each (motion) frame is collapsed to its
per-row mean (the mean across image columns), and the resulting column
vectors are stacked over time into an (height, n) array -- image row vs
time. This "vertical approach" variant renders vertical trajectories
(e.g. a mallet's approach-and-rebound path toward an instrument)
directly. With `orientation="horizontal"` each frame is collapsed to
its per-column mean, giving a (width, n) array -- image column vs time
-- which renders horizontal (side-to-side) motion.

This is the numpy-level counterpart of the image-producing motiongram
pipelines (`MgVideo.motiongrams`, whose `_mgh`/`_mgv` PNGs correspond to
the "vertical" and "horizontal" collapses here, up to transposition and
post-processing): use this function when you want the motiongram as
data for further analysis rather than as a rendered image.

Source: cymbal-comparison study (Jensenius) -- vertical motiongram of
the mallet trajectory; building on the classic fourMs motiongram.

#### Arguments

- `frames` *np.ndarray* - Grayscale frames of shape (T, H, W).
- `orientation` *str, optional* - "vertical" (per-row mean; image row vs
    time; shows vertical motion) or "horizontal" (per-column mean;
    image column vs time; shows horizontal motion). Defaults to "vertical".
- `frame_diff` *bool, optional* - If True, collapse the absolute inter-frame
    differences (a motiongram, T-1 time steps); if False, collapse the
    frames themselves (a videogram, T time steps). Defaults to True.
- `normalize` *bool, optional* - If True, scale the result to [0, 1] by its
    maximum. Defaults to True.

#### Returns

- `np.ndarray` - The motiongram, of shape (H, T-1) for "vertical" or
    (W, T-1) for "horizontal" (T instead of T-1 when `frame_diff` is
    False). Time runs along the second axis.

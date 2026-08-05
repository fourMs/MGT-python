# Spacetime

> Auto-generated documentation for [musicalgestures._spacetime](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_spacetime.py) module.

Space-time visualisations of a person in a video: stroboscope (chronophotography),
silhouette waterfall, motion history image (MHI), and a 3D space-time silhouette volume.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Spacetime
    - [mg_motionhistory](#mg_motionhistory)
    - [mg_silhouette_waterfall](#mg_silhouette_waterfall)
    - [mg_spacetime_volume](#mg_spacetime_volume)
    - [mg_stroboscope](#mg_stroboscope)

Silhouettes are extracted with MediaPipe selfie segmentation when available, falling back
to background subtraction against the average frame (good for static-camera recordings).

## mg_motionhistory

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_spacetime.py#L322)

```python
def mg_motionhistory(
    self,
    threshold: float = 0.05,
    decay: float = 0.3,
    normalize: bool = False,
    blur: int = 0,
    cmap: str = 'hot',
    dpi: int = 300,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgImage':
```

Renders a Motion History Image (Bobick & Davis): a single image where intensity encodes
how recently motion occurred at each pixel (recent motion bright, older motion fades out).

A motion mark is set to full intensity where motion occurs and then **decays** linearly to
zero over a window set by ``decay``, so old motion disappears instead of accumulating and
washing out the image. Raise ``threshold`` to ignore background noise, and lower ``decay``
for shorter (less crowded) trails.

#### Arguments

- `threshold` *float, optional* - Motion threshold (0–1) on frame differences. Higher rejects
    more background noise. Defaults to 0.05.
- `decay` *float, optional* - Fade window as a fraction of the clip length (0–1): a motion
    mark fully fades after this fraction of the video. Smaller = shorter trails, less
    blow-out. Defaults to 0.3.
- `normalize` *bool, optional* - Stretch the result to the full intensity range. Defaults to False.
    The MHI is already built in [0, 1], so normalization is rarely needed; when the final
    frames are static it amplifies faint residual trails and over-brightens ("blows up") the
    image, so it is guarded to skip when the peak intensity is very low.
- `blur` *int, optional* - Optional Gaussian smoothing radius for the difference mask (0 = off).
    Helps suppress speckle noise. Defaults to 0.
- `cmap` *str, optional* - Matplotlib colormap. Defaults to 'hot'.
- `dpi` *int, optional* - Output DPI. Defaults to 300.
- `target_name` *str, optional* - Output name. Defaults to None ("_mhi.png").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.

#### Returns

- `MgImage` - the motion history image.

## mg_silhouette_waterfall

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_spacetime.py#L207)

```python
def mg_silhouette_waterfall(
    self,
    n_samples: int = 40,
    method: str = 'auto',
    threshold: float = 0.1,
    kernel_size: int = 5,
    keep_largest: bool = False,
    axis: str = 'horizontal',
    cmap: str = 'viridis',
    dpi: int = 200,
    elev: float = 35,
    azim: float = -60,
    axes: bool = True,
    crop: bool = False,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgFigure':
```

Renders a 3D silhouette waterfall: the per-frame silhouette projected onto one spatial
axis and stacked as cascading curves along a time (depth) axis, so the body's occupancy
profile "flows" through time — like a 3D spectrogram waterfall.

For a single person on a static background, raise ``threshold`` and/or set
``keep_largest=True`` for a cleaner profile.

#### Arguments

- `n_samples` *int, optional* - Number of time slices (profiles) to stack. Defaults to 40.
- `method` *str, optional* - Silhouette extraction: 'auto', 'mediapipe', or 'bgsub'. Defaults to 'auto'.
- `threshold` *float, optional* - Foreground threshold (0–1). Higher rejects more background. Defaults to 0.1.
- `kernel_size` *int, optional* - Morphological cleanup kernel (0 disables). Defaults to 5.
- `keep_largest` *bool, optional* - Keep only the largest blob (the person). Defaults to False.
- `axis` *str, optional* - 'horizontal' profiles over x (collapse y); 'vertical' profiles over y. Defaults to 'horizontal'.
- `cmap` *str, optional* - Matplotlib colormap (by time). Defaults to 'viridis'.
- `dpi` *int, optional* - Output DPI. Defaults to 200.
- `elev` *float, optional* - 3D elevation angle. Defaults to 35.
- `azim` *float, optional* - 3D azimuth angle. Defaults to -60.
- `axes` *bool, optional* - Draw the axes, tick labels, and title. Set to False for a clean
    render with all axes and text removed. Defaults to True.
- `crop` *bool, optional* - Tighten the spatial axis to the occupied (nonzero) extent and trim
    the surrounding whitespace, so the figure shows mostly the data. Defaults to False.
- `target_name` *str, optional* - Output name. Defaults to None ("_silhouette_waterfall.png").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.

#### Returns

- `MgFigure` - the 3D waterfall figure (the stacked profiles are in ``.data``).

## mg_spacetime_volume

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_spacetime.py#L405)

```python
def mg_spacetime_volume(
    self,
    n_samples: int = 50,
    downsample: int = 8,
    method: str = 'auto',
    threshold: float = 0.1,
    kernel_size: int = 5,
    keep_largest: bool = False,
    cmap: str = 'viridis',
    dpi: int = 200,
    elev: float = 20,
    azim: float = -60,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgFigure':
```

Renders a 3D space-time scatter of the person's silhouette: points (x, y, t) where the
silhouette is present, with time on the depth axis and colour, showing how the body
occupies space through time.

#### Arguments

- `n_samples` *int, optional* - Number of time samples (depth slices). Defaults to 50.
- `downsample` *int, optional* - Spatial downsampling factor for the silhouette points. Defaults to 8.
- `method` *str, optional* - Silhouette extraction: 'auto', 'mediapipe', or 'bgsub'. Defaults to 'auto'.
- `threshold` *float, optional* - Foreground threshold (0–1). Higher rejects more background. Defaults to 0.1.
- `kernel_size` *int, optional* - Morphological cleanup kernel for the silhouette (0 disables). Defaults to 5.
- `keep_largest` *bool, optional* - Keep only the largest blob (the person). Defaults to False.
- `cmap` *str, optional* - Matplotlib colormap for time. Defaults to 'viridis'.
- `dpi` *int, optional* - Output DPI. Defaults to 200.
- `elev` *float, optional* - 3D elevation angle. Defaults to 20.
- `azim` *float, optional* - 3D azimuth angle. Defaults to -60.
- `target_name` *str, optional* - Output name. Defaults to None ("_spacetime_volume.png").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.

#### Returns

- `MgFigure` - the 3D space-time figure (data holds the point cloud).

## mg_stroboscope

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_spacetime.py#L131)

```python
def mg_stroboscope(
    self,
    n_samples: int = 12,
    method: str = 'auto',
    threshold: float = 0.1,
    kernel_size: int = 5,
    keep_largest: bool = False,
    colorize: bool = True,
    background: str = 'average',
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgImage':
```

Renders a stroboscope / chronophotography image: the person's silhouette at evenly
sampled times composited onto a single frame, showing the body moving through space
over time (Muybridge-style).

For a clean result with a single person on a static background, raise ``threshold`` and
set ``keep_largest=True`` so only the person's blob is composited (avoids the image
"blowing up" from background noise).

#### Arguments

- `n_samples` *int, optional* - Number of time samples (silhouettes) to composite. Defaults to 12.
- `method` *str, optional* - Silhouette extraction: 'auto', 'mediapipe', or 'bgsub'. Defaults to 'auto'.
- `threshold` *float, optional* - Foreground threshold (0–1). Higher rejects more background. Defaults to 0.1.
- `kernel_size` *int, optional* - Morphological cleanup kernel for the silhouette (0 disables). Defaults to 5.
- `keep_largest` *bool, optional* - Keep only the largest blob (the person). Defaults to False.
- `colorize` *bool, optional* - Tint each silhouette by time (early→late) for a temporal cue. Defaults to True.
- `background` *str, optional* - 'average' (clean plate), 'first' (first frame), 'black' or 'white'. Defaults to 'average'.
- `target_name` *str, optional* - Output name. Defaults to None ("_stroboscope.png").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.

#### Returns

- `MgImage` - the stroboscope image.

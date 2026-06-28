# Heatmap

> Auto-generated documentation for [musicalgestures._heatmap](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_heatmap.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Heatmap
    - [mg_heatmap](#mg_heatmap)

## mg_heatmap

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_heatmap.py#L10)

```python
def mg_heatmap(
    self,
    colormap: str = 'inferno',
    overlay: bool = True,
    alpha: float = 0.75,
    background_dim: float = 0.4,
    blur: int = 0,
    normalize: bool = True,
    gamma: float = 0.5,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgImage':
```

Renders a motion heatmap showing which parts of the video change the most.

The function accumulates the absolute pixel difference between consecutive frames
over the whole video, producing a single image where bright/hot regions mark areas
of frequent or large change and dark/cool regions mark areas that stay still. When
``overlay`` is True the heat is composited on top of a dimmed average frame, so the
activity is shown in the spatial context of the scene.

#### Arguments

- `colormap` *str, optional* - Any matplotlib colormap name used to colour the heat
    (e.g. 'inferno', 'jet', 'viridis', 'hot', 'magma'). Defaults to 'inferno'.
- `overlay` *bool, optional* - If True, composite the heatmap over a dimmed grayscale
    average frame so the motion is shown in context. If False, render the bare
    heatmap on a black background. Defaults to True.
- `alpha` *float, optional* - Maximum opacity of the heat overlay in [0, 1]. Hotter
    pixels are more opaque. Only used when ``overlay=True``. Defaults to 0.75.
- `background_dim` *float, optional* - Brightness multiplier for the average-frame
    background in [0, 1]. Lower values make the heat stand out more. Only used
    when ``overlay=True``. Defaults to 0.4.
- `blur` *int, optional* - Radius of an optional Gaussian smoothing applied to the
    accumulated motion (0 disables). Gives a smoother, less speckled heatmap.
    Defaults to 0.
- `normalize` *bool, optional* - If True, scale the accumulated motion so the most
    active pixel maps to the top of the colormap. Defaults to True.
- `gamma` *float, optional* - Gamma applied to the normalised heat before colouring.
    Values < 1 boost faint motion so subtle activity is visible; 1.0 is linear.
    Defaults to 0.5.
- `target_name` *str, optional* - The name of the output image. Defaults to None
    (which uses the input filename with the suffix "_heatmap.png").
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to
    automatically increment the target filename to avoid overwriting.
    Defaults to True.

#### Returns

- `MgImage` - A new MgImage pointing to the output heatmap image file.

# Grid

> Auto-generated documentation for [musicalgestures._grid](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_grid.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Grid
    - [mg_grid](#mg_grid)

## mg_grid

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_grid.py#L6)

```python
def mg_grid(
    self,
    height=300,
    rows=3,
    cols=3,
    padding=0,
    margin=0,
    target_name=None,
    overwrite=False,
    return_array=False,
):
```

Generates frame strip video preview using ffmpeg.

#### Arguments

- `height` *int, optional* - Frame height, width is adjusted automatically to keep the correct aspect ratio. Defaults to 300.
- `rows` *int, optional* - Number of rows of the grid. Defaults to 3.
- `cols` *int, optional* - Number of columns of the grid. Defaults to 3.
- `padding` *int, optional* - Padding size between the frames. Defaults to 0.
- `margin` *int, optional* - Margin size for the grid. Defaults to 0.
- `target_name` *[type], optional* - Target output name for the grid image. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.
- `return_array` *bool, optional* - Whether to return an array of not. If set to False the function writes the grid image to disk. Defaults to False.

#### Returns

- `MgImage` - An MgImage object referring to the internal grid image.

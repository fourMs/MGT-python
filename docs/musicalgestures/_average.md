# Average

> Auto-generated documentation for [musicalgestures._average](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_average.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Average
    - [mg_average_image](#mg_average_image)

## mg_average_image

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_average.py#L8)

```python
def mg_average_image(
    self,
    filename=None,
    normalize=True,
    target_name=None,
    overwrite=False,
):
```

Finds and saves an average image of an input video file.

#### Arguments

- `filename` *str, optional* - Path to the input video file. If None, the video file of the MgObject is used. Defaults to None.
- `normalize` *bool, optional* - If True, normalizes pixel values in the output image. Defaults to True.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_average" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgImage` - A new MgImage pointing to the output image file.

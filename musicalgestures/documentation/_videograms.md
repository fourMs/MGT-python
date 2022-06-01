# Videograms

> Auto-generated documentation for [_videograms](https://github.com/fourMs/MGT-python/blob/master/_videograms.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Videograms
    - [videograms_ffmpeg](#videograms_ffmpeg)

## videograms_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_videograms.py#L10)

```python
def videograms_ffmpeg(
    self,
    target_name_x=None,
    target_name_y=None,
    overwrite=False,
):
```

Renders horizontal and vertical videograms of the source video using ffmpeg. Averages videoframes by axes,
and creates two images of the horizontal-axis and vertical-axis stacks. In these stacks, a single row or
column corresponds to a frame from the source video, and the index of the row or column corresponds to
the index of the source frame.

#### Arguments

- `target_name_x` *str, optional* - Target output name for the videogram on the X axis. Defaults to None (which assumes that the input filename with the suffix "_vgx" should be used).
- `target_name_y` *str, optional* - Target output name for the videogram on the Y axis. Defaults to None (which assumes that the input filename with the suffix "_vgy" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgList` - An MgList with the MgImage objects referring to the horizontal and vertical videograms respectively.

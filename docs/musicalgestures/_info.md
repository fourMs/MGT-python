# Info

> Auto-generated documentation for [musicalgestures._info](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_info.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Info
    - [mg_info](#mg_info)
    - [plot_frames](#plot_frames)

## mg_info

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_info.py#L8)

```python
def mg_info(self, type=None, autoshow=True, overwrite=False):
```

Returns info about video/audio/format file using ffprobe.

#### Arguments

- `type` *str, optional* - Type of information to retrieve. Possible choice are 'audio', 'video', 'format' or 'frame'. Defaults to None (which gives info about video, audio and format).
- `autoshow` *bool, optional* - Whether to show the I/P/B frames figure automatically. Defaults to True. NB: The type argument needs to be set to 'frame'.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - decoded ffprobe output (stdout) as a list containing three dictionaries for video, audio and format metadata.

## plot_frames

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_info.py#L116)

```python
def plot_frames(
    df,
    label,
    color_list=['#636EFA', '#00CC96', '#EF553B'],
    index=0,
):
```

# Videoadjust

> Auto-generated documentation for [musicalgestures._videoadjust](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Videoadjust
    - [contrast_brightness_ffmpeg](#contrast_brightness_ffmpeg)
    - [skip_frames_ffmpeg](#skip_frames_ffmpeg)

## contrast_brightness_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py#L6)

```python
def contrast_brightness_ffmpeg(
    filename,
    contrast=0,
    brightness=0,
    target_name=None,
    overwrite=False,
):
```

Applies contrast and brightness adjustments on the source video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the video to process.
- `contrast` *int/float, optional* - Increase or decrease contrast. Values range from -100 to 100. Defaults to 0.
- `brightness` *int/float, optional* - Increase or decrease brightness. Values range from -100 to 100. Defaults to 0.
- `target_name` *str, optional* - Defaults to None (which assumes that the input filename with the suffix "_cb" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the output video.

## skip_frames_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py#L61)

```python
def skip_frames_ffmpeg(filename, skip=0, target_name=None, overwrite=False):
```

Time-shrinks the video by skipping (discarding) every n frames determined by `skip`.
To discard half of the frames (ie. double the speed of the video) use `skip=1`.

#### Arguments

- `filename` *str* - Path to the video to process.
- `skip` *int, optional* - Discard `skip` frames before keeping one. Defaults to 0.
- `target_name` *str, optional* - Defaults to None (which assumes that the input filename with the suffix "_skip" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the output video.
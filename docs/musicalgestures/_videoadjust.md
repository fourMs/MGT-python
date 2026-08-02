# Videoadjust

> Auto-generated documentation for [musicalgestures._videoadjust](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Videoadjust
    - [contrast_brightness_ffmpeg](#contrast_brightness_ffmpeg)
    - [fixed_frames_ffmpeg](#fixed_frames_ffmpeg)
    - [mg_resample](#mg_resample)
    - [skip_frames_ffmpeg](#skip_frames_ffmpeg)

## contrast_brightness_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py#L7)

```python
def contrast_brightness_ffmpeg(
    filename,
    contrast=0,
    brightness=0,
    target_name=None,
    overwrite=True,
):
```

Applies contrast and brightness adjustments on the source video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the video to process.
- `contrast` *int/float, optional* - Increase or decrease contrast. Values range from -100 to 100. Defaults to 0.
- `brightness` *int/float, optional* - Increase or decrease brightness. Values range from -100 to 100. Defaults to 0.
- `target_name` *str, optional* - Defaults to None (which assumes that the input filename with the suffix "_cb" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output video.

## fixed_frames_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py#L121)

```python
def fixed_frames_ffmpeg(filename, frames=0, target_name=None, overwrite=True):
```

Specify a fixed target number frames to extract from the video.
To extract only keyframes from the video, set the parameter keyframes to True.

#### Arguments

- `filename` *str* - Path to the video to process.
- `frames` *int), optional* - Number frames to extract from the video. If set to -1, it will only extract the keyframes of the video. Defaults to 0.
- `target_name` *str, optional* - Defaults to None (which assumes that the input filename with the suffix "_fixed" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output video.

## mg_resample

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py#L181)

```python
def mg_resample(
    self,
    fps=None,
    speed=None,
    skip=None,
    target_name=None,
    overwrite=True,
) -> 'musicalgestures.MgVideo':
```

Resample the (already loaded) video and return a **new** MgVideo, leaving the original
object untouched.

Three independent, combinable operations:

* ``fps``: retime to a target frame rate using FFmpeg's ``fps`` filter, **duration-preserving**
  (frames are dropped/duplicated to hit the rate), e.g. 30 → 25 fps.
* ``speed``: change playback speed by a factor (>1 faster/shorter, <1 slower/longer); the video
  is retimed with ``setpts`` and the audio with ``atempo`` so they stay in sync.
* ``skip``: integer frame decimation, discarding ``skip`` frames for every one kept (this also
  shortens/speeds up the clip), matching the loader's ``skip`` parameter.

When more than one is given they are applied in order: ``skip`` → ``speed``/``fps``.

#### Arguments

- `fps` *float, optional* - Target frame rate (duration-preserving). Defaults to None.
- `speed` *float, optional* - Playback-speed factor. Defaults to None.
- `skip` *int, optional* - Discard ``skip`` frames for every one kept. Defaults to None.
- `target_name` *str, optional* - Output name. Defaults to None (input filename + "_resampled").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.

#### Returns

- `MgVideo` - a new MgVideo pointing to the resampled file.

## skip_frames_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py#L77)

```python
def skip_frames_ffmpeg(filename, skip=0, target_name=None, overwrite=True):
```

Time-shrinks the video by skipping (discarding) every n frames determined by `skip`.
To discard half of the frames (ie. double the speed of the video) use `skip=1`.

#### Arguments

- `filename` *str* - Path to the video to process.
- `skip` *int, optional* - Discard `skip` frames before keeping one. Defaults to 0.
- `target_name` *str, optional* - Defaults to None (which assumes that the input filename with the suffix "_skip" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output video.

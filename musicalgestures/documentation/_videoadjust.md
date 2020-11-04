# Videoadjust

> Auto-generated documentation for [\_videoadjust](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Videoadjust
  - [contrast_brightness_ffmpeg](#contrast_brightness_ffmpeg)
  - [skip_frames_ffmpeg](#skip_frames_ffmpeg)

## contrast_brightness_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py#L6)

```python
def contrast_brightness_ffmpeg(filename, contrast=0, brightness=0):
```

Applies contrast and brightness adjustments on the source video using ffmpeg.

#### Arguments

- `filename` _str_ - Path to the video to process.
  contrast (int or float, optional): Increase or decrease contrast. Values range from -100 to 100. Defaults to 0.
  brightness (int or float, optional): Increase or decrease brightness. Values range from -100 to 100. Defaults to 0.

#### Outputs

- `filename`\_cb.\<file extension\>

## skip_frames_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoadjust.py#L54)

```python
def skip_frames_ffmpeg(filename, skip=0):
```

Time-shrinks the video by skipping (discarding) every n frames determined by `skip`. To discard half of the frames (ie. double the speed of the video) use `skip=1`.

#### Arguments

- `filename` _str_ - Path to the video to process.
- `skip` _int, optional_ - Discard `skip` frames before keeping one. Defaults to 0.

#### Outputs

- `filename`\_skip.\<file extension\>

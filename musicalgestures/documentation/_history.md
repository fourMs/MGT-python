# History

> Auto-generated documentation for [_history](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_history.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / History
    - [ParameterError](#parametererror)
    - [history_cv2](#history_cv2)
    - [history_ffmpeg](#history_ffmpeg)

## ParameterError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_history.py#L8)

```python
class ParameterError(Exception):
```

Base class for argument errors.

## history_cv2

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_history.py#L110)

```python
def history_cv2(
    self,
    filename=None,
    history_length=10,
    weights=1,
    target_name=None,
    overwrite=False,
):
```

This function  creates a video where each frame is the average of the N previous frames, where n is determined by `history_length`. The history frames are summed up and normalized, and added to the current frame to show the history. Uses cv2.

#### Arguments

- `filename` *str, optional* - Path to the input video file. If None, the video file of the MgVideo is used. Defaults to None.
- `history_length` *int, optional* - Number of frames to be saved in the history tail. Defaults to 10.
- `weights` *int/float/list, optional* - Defines the weight or weights applied to the frames in the history tail. If given as list the first element in the list will correspond to the weight of the newest frame in the tail. Defaults to 1.
- `target_name` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_history" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgVideo` - A new MgVideo pointing to the output video file.

## history_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_history.py#L13)

```python
def history_ffmpeg(
    self,
    filename=None,
    history_length=10,
    weights=1,
    normalize=False,
    norm_strength=1,
    norm_smooth=0,
    target_name=None,
    overwrite=False,
):
```

This function  creates a video where each frame is the average of the N previous frames, where n is determined by `history_length`. The history frames are summed up and normalized, and added to the current frame to show the history. Uses ffmpeg.

#### Arguments

- `filename` *str, optional* - Path to the input video file. If None, the video file of the MgVideo is used. Defaults to None.
- `history_length` *int, optional* - Number of frames to be saved in the history tail. Defaults to 10.
- `weights` *int/float/list/str, optional* - Defines the weight or weights applied to the frames in the history tail. If given as list the first element in the list will correspond to the weight of the newest frame in the tail. If given as a str - like "3 1.2 1" - it will be automatically converted to a list - like [3, 1.2, 1]. Defaults to 1.
- `normalize` *bool, optional* - If True, the history video will be normalized. This can be useful when processing motion (frame difference) videos. Defaults to False.
- `norm_strength` *int/float, optional* - Defines the strength of the normalization where 1 represents full strength. Defaults to 1.
- `norm_smooth` *int, optional* - Defines the number of previous frames to use for temporal smoothing. The input range of each channel is smoothed using a rolling average over the current frame and the `norm_smooth` previous frames. Defaults to 0.
- `target_name` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_history" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgVideo` - A new MgVideo pointing to the output video file.

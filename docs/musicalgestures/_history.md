# History

> Auto-generated documentation for [musicalgestures._history](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_history.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / History
    - [history_cv2](#history_cv2)
    - [history_ffmpeg](#history_ffmpeg)

## history_cv2

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_history.py#L106)

```python
def history_cv2(
    self,
    filename: str | None = None,
    history_length: int = 10,
    weights: int | float | list = 1,
    convert: bool = True,
    target_name: str | None = None,
    overwrite: bool = True,
):
```

This function  creates a video where each frame is the average of the N previous frames, where n is determined by `history_length`. The history frames are summed up and normalised, and added to the current frame to show the history. Uses cv2.

#### Arguments

- `filename` *str, optional* - Path to the input video file. If None, the video file of the MgVideo is used. Defaults to None.
- `history_length` *int, optional* - Number of frames to be saved in the history tail. Defaults to 10.
- `weights` *int/float/list, optional* - Defines the weight or weights applied to the frames in the history tail. If given as list the first element in the list will correspond to the weight of the newest frame in the tail. Defaults to 1.
- `convert` *bool, optional* - If True (default), non-AVI input is first converted to an all-intra MJPEG `.avi` (cached as `self.as_avi`) for frame-accurate decoding. Set to False to read the source file directly. Defaults to True.
- `target_name` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_history" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgVideo` - A new MgVideo pointing to the output video file.

## history_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_history.py#L11)

```python
def history_ffmpeg(
    self,
    filename: str | None = None,
    history_length: int = 10,
    weights: int | float | list | str = 1,
    normalize: bool = False,
    norm_strength: int | float = 1,
    norm_smooth: int = 0,
    target_name: str | None = None,
    overwrite: bool = True,
):
```

This function  creates a video where each frame is the average of the N previous frames, where n is determined by `history_length`. The history frames are summed up and normalised, and added to the current frame to show the history. Uses ffmpeg.

#### Arguments

- `filename` *str, optional* - Path to the input video file. If None, the video file of the MgVideo is used. Defaults to None.
- `history_length` *int, optional* - Number of frames to be saved in the history tail. Defaults to 10.
- `weights` *int/float/list/str, optional* - Defines the weight or weights applied to the frames in the history tail. If given as list the first element in the list will correspond to the weight of the newest frame in the tail. If given as a str - like "3 1.2 1" - it will be automatically converted to a list - like [3, 1.2, 1]. Defaults to 1.
- `normalize` *bool, optional* - If True, the history video will be normalised. This can be useful when processing motion (frame difference) videos. Defaults to False.
- `norm_strength` *int/float, optional* - Defines the strength of the normalisation where 1 represents full strength. Defaults to 1.
- `norm_smooth` *int, optional* - Defines the number of previous frames to use for temporal smoothing. The input range of each channel is smoothed using a rolling average over the current frame and the `norm_smooth` previous frames. Defaults to 0.
- `target_name` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_history" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgVideo` - A new MgVideo pointing to the output video file.

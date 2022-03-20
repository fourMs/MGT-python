# Cropvideo

> Auto-generated documentation for [_cropvideo](https://github.com/fourMs/MGT-python/blob/main/_cropvideo.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Cropvideo
    - [async_subprocess](#async_subprocess)
    - [find_motion_box_ffmpeg](#find_motion_box_ffmpeg)
    - [manual_text_input](#manual_text_input)
    - [mg_cropvideo_ffmpeg](#mg_cropvideo_ffmpeg)
    - [run_cropping_window](#run_cropping_window)

## async_subprocess

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_cropvideo.py#L161)

```python
async def async_subprocess(command):
```

## find_motion_box_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_cropvideo.py#L10)

```python
def find_motion_box_ffmpeg(
    filename,
    motion_box_thresh=0.1,
    motion_box_margin=12,
):
```

Helper function to find the area of motion in a video, using ffmpeg.

#### Arguments

- `filename` *str* - Path to the video file.
- `motion_box_thresh` *float, optional* - Pixel threshold to apply to the video before assessing the area of motion. Defaults to 0.1.
- `motion_box_margin` *int, optional* - Margin (in pixels) to add to the detected motion box. Defaults to 12.

#### Raises

- `KeyboardInterrupt` - In case we stop the process manually.

#### Returns

- `int` - The width of the motion box.
- `int` - The height of the motion box.
- `int` - The X coordinate of the top left corner of the motion box.
- `int` - The Y coordinate of the top left corner of the motion box.

## manual_text_input

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_cropvideo.py#L206)

```python
def manual_text_input():
```

Helper function for mg_crop_video_ffmpeg when its crop_movement is 'manual', but the environment is in Colab.
In this case we can't display the windowed cropping UI, so we ask for the values as a text input.

#### Returns

- `list` - x, y, w, h for crop_ffmpeg.

## mg_cropvideo_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_cropvideo.py#L99)

```python
def mg_cropvideo_ffmpeg(
    filename,
    crop_movement='Auto',
    motion_box_thresh=0.1,
    motion_box_margin=12,
    target_name=None,
    overwrite=False,
):
```

Crops the video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the video file.
- `crop_movement` *str, optional* - 'Auto' finds the bounding box that contains the total motion in the video. Motion threshold is given by motion_box_thresh. 'Manual' opens up a simple GUI that is used to crop the video manually by looking at the first frame. Defaults to 'Auto'.
- `motion_box_thresh` *float, optional* - Only meaningful if `crop_movement='Auto'`. Takes floats between 0 and 1, where 0 includes all the motion and 1 includes none. Defaults to 0.1.
- `motion_box_margin` *int, optional* - Only meaningful if `crop_movement='Auto'`. Adds margin to the bounding box. Defaults to 12.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_crop" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the cropped video.

## run_cropping_window

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_cropvideo.py#L181)

```python
def run_cropping_window(imgpath, scale_ratio, scaled_width, scaled_height):
```

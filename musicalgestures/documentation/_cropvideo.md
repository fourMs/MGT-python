# Cropvideo

> Auto-generated documentation for [_cropvideo](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_cropvideo.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Cropvideo
    - [draw_rectangle](#draw_rectangle)
    - [find_motion_box](#find_motion_box)
    - [find_motion_box_ffmpeg](#find_motion_box_ffmpeg)
    - [find_total_motion_box](#find_total_motion_box)
    - [mg_cropvideo](#mg_cropvideo)
    - [mg_cropvideo_ffmpeg](#mg_cropvideo_ffmpeg)

## draw_rectangle

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_cropvideo.py#L101)

```python
def draw_rectangle(event, x, y, flags, param):
```

Helper function to render a cropping window to the user in case of manual cropping, using cv2.

## find_motion_box

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_cropvideo.py#L124)

```python
def find_motion_box(grayimage, width, height, motion_box_margin):
```

Helper function to find the area of motion in a single frame, using cv2.

## find_motion_box_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_cropvideo.py#L224)

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

## find_total_motion_box

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_cropvideo.py#L187)

```python
def find_total_motion_box(
    vid2findbox,
    width,
    height,
    length,
    motion_box_thresh,
    motion_box_margin,
):
```

Helper function to find the area of motion in a video, using cv2.

## mg_cropvideo

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_cropvideo.py#L9)

```python
def mg_cropvideo(
    fps,
    width,
    height,
    length,
    of,
    fex,
    crop_movement='Auto',
    motion_box_thresh=0.1,
    motion_box_margin=1,
):
```

Crops the video using cv2.

#### Arguments

- `fps` *int* - The FPS (frames per second) of the input video capture.
- `width` *int* - The pixel width of the input video capture.
- `height` *int* - The pixel height of the input video capture.
- `length` *int* - The number of frames in the input video capture.
- `of` *str* - 'Only filename' without extension (but with path to the file).
- `fex` *str* - File extension.
- `crop_movement` *str, optional* - 'Auto' finds the bounding box that contains the total motion in the video. Motion threshold is given by motion_box_thresh. 'Manual' opens up a simple GUI that is used to crop the video manually by looking at the first frame. Defaults to 'Auto'.
- `motion_box_thresh` *float, optional* - Only meaningful if `crop_movement='Auto'`. Takes floats between 0 and 1, where 0 includes all the motion and 1 includes none. Defaults to 0.1.
- `motion_box_margin` *int, optional* - Only meaningful if `crop_movement='Auto'`. Adds margin to the bounding box. Defaults to 1.

#### Returns

- `cv2.VideoCapture` - The cropped video as a cv2.Videocapture
- `int` - The pixel width of the cropped video
- `int` - The pixel height of the cropped video

## mg_cropvideo_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_cropvideo.py#L313)

```python
def mg_cropvideo_ffmpeg(
    filename,
    crop_movement='Auto',
    motion_box_thresh=0.1,
    motion_box_margin=12,
):
```

Crops the video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the video file.
- `crop_movement` *str, optional* - 'Auto' finds the bounding box that contains the total motion in the video. Motion threshold is given by motion_box_thresh. 'Manual' opens up a simple GUI that is used to crop the video manually by looking at the first frame. Defaults to 'Auto'.
- `motion_box_thresh` *float, optional* - Only meaningful if `crop_movement='Auto'`. Takes floats between 0 and 1, where 0 includes all the motion and 1 includes none. Defaults to 0.1.
- `motion_box_margin` *int, optional* - Only meaningful if `crop_movement='Auto'`. Adds margin to the bounding box. Defaults to 12.

#### Returns

- `str` - Path to the cropped video.

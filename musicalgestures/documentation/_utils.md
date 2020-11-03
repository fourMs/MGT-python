# Utils

> Auto-generated documentation for [_utils](..\_utils.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Utils
    - [MgFigure](#mgfigure)
        - [MgFigure().show](#mgfigureshow)
    - [MgImage](#mgimage)
    - [MgProgressbar](#mgprogressbar)
        - [MgProgressbar().get_now](#mgprogressbarget_now)
        - [MgProgressbar().over_time_limit](#mgprogressbarover_time_limit)
        - [MgProgressbar().progress](#mgprogressbarprogress)
    - [audio_dilate](#audio_dilate)
    - [cast_into_avi](#cast_into_avi)
    - [clamp](#clamp)
    - [convert_to_avi](#convert_to_avi)
    - [convert_to_grayscale](#convert_to_grayscale)
    - [convert_to_mp4](#convert_to_mp4)
    - [crop_ffmpeg](#crop_ffmpeg)
    - [embed_audio_in_video](#embed_audio_in_video)
    - [extract_subclip](#extract_subclip)
    - [extract_wav](#extract_wav)
    - [ffmpeg_cmd](#ffmpeg_cmd)
    - [frame2ms](#frame2ms)
    - [framediff_ffmpeg](#framediff_ffmpeg)
    - [get_first_frame_as_image](#get_first_frame_as_image)
    - [get_fps](#get_fps)
    - [get_frame_planecount](#get_frame_planecount)
    - [get_framecount](#get_framecount)
    - [get_length](#get_length)
    - [get_screen_resolution_scaled](#get_screen_resolution_scaled)
    - [get_screen_video_ratio](#get_screen_video_ratio)
    - [get_widthheight](#get_widthheight)
    - [has_audio](#has_audio)
    - [motiongrams_ffmpeg](#motiongrams_ffmpeg)
    - [motionvideo_ffmpeg](#motionvideo_ffmpeg)
    - [rotate_video](#rotate_video)
    - [roundup](#roundup)
    - [scale_array](#scale_array)
    - [scale_num](#scale_num)
    - [str2sec](#str2sec)
    - [threshold_ffmpeg](#threshold_ffmpeg)

## MgFigure

[[find in source code]](..\_utils.py#L215)

```python
class MgFigure():
    def __init__(
        figure=None,
        figure_type=None,
        data=None,
        layers=None,
        image=None,
    ):
```

Class for working with figures and plots within the Musical Gestures Toolbox.

### MgFigure().show

[[find in source code]](..\_utils.py#L240)

```python
def show():
```

Shows the internal matplotlib.pyplot.figure.

## MgImage

[[find in source code]](..\_utils.py#L193)

```python
class MgImage():
    def __init__(filename):
```

Class for handling images in the Musical Gestures Toolbox.

## MgProgressbar

[[find in source code]](..\_utils.py#L1)

```python
class MgProgressbar():
    def __init__(
        total=100,
        time_limit=0.1,
        prefix='Progress',
        suffix='Complete',
        decimals=1,
        length=40,
        fill='█',
    ):
```

Calls in a loop to create terminal progress bar.

### MgProgressbar().get_now

[[find in source code]](..\_utils.py#L38)

```python
def get_now():
```

Gets the current time.

#### Returns

- `datetime.datetime.timestamp` - The current time.

### MgProgressbar().over_time_limit

[[find in source code]](..\_utils.py#L48)

```python
def over_time_limit():
```

Checks if we should redraw the progress bar at this moment.

#### Returns

- `bool` - True if equal or more time has passed than `self.time_limit` since the last redraw.

### MgProgressbar().progress

[[find in source code]](..\_utils.py#L58)

```python
def progress(iteration):
```

Progresses the progress bar to the next step.

#### Arguments

iteration (int or float): The current iteration. For example, the 57th out of 100 steps, or 12.3s out of the total 60s.

## audio_dilate

[[find in source code]](..\_utils.py#L897)

```python
def audio_dilate(filename, dilation_ratio=1):
```

Time-stretches or -shrinks (dilates) an audio file using ffmpeg.

#### Arguments

- `filename` *str* - Path to the audio file to dilate.
dilation_ratio (int or float, optional): The source file's length divided by the resulting file's length. Defaults to 1.

Outputs:
    <file name>_dilated.<file extension>

#### Returns

- `str` - The path to the output audio file.

## cast_into_avi

[[find in source code]](..\_utils.py#L290)

```python
def cast_into_avi(filename):
```

*Experimental*
Casts a video into and .avi container using ffmpeg. Much faster than [convert_to_avi](#convert_to_avi),
but does not always work well with cv2 or built-in video players.

#### Arguments

- `filename` *str* - Path to the input video file.

Outputs:
    `filename`.avi

#### Returns

- `str` - The path to the output '.avi' file.

## clamp

[[find in source code]](..\_utils.py#L110)

```python
def clamp(num, min_value, max_value):
```

Clamps a number between a minimum and maximum value.

#### Arguments

num (int or float): The number to clamp.
min_value (int or float): The minimum allowed value.
max_value (int or float): The maximum allowed value.

#### Returns

int or float: The clamped number.

## convert_to_avi

[[find in source code]](..\_utils.py#L247)

```python
def convert_to_avi(filename):
```

Converts a video to one with .avi extension using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.

Outputs:
    `filename`.avi

#### Returns

- `str` - The path to the output '.avi' file.

## convert_to_grayscale

[[find in source code]](..\_utils.py#L376)

```python
def convert_to_grayscale(filename):
```

Converts a video to grayscale using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.

Outputs:
    `filename`_gray.<file extension>

#### Returns

- `str` - The path to the grayscale video file.

## convert_to_mp4

[[find in source code]](..\_utils.py#L269)

```python
def convert_to_mp4(filename):
```

Converts a video to one with .mp4 extension using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.

Outputs:
    `filename`.mp4

#### Returns

- `str` - The path to the output '.mp4' file.

## crop_ffmpeg

[[find in source code]](..\_utils.py#L671)

```python
def crop_ffmpeg(filename, w, h, x, y, outname=None):
```

Crops a video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `w` *int* - The desired width.
- `h` *int* - The desired height.
- `x` *int* - The horizontal coordinate of the top left pixel of the cropping rectangle.
- `y` *int* - The vertical coordinate of the top left pixel of the cropping rectangle.
- `outname` *str, optional* - The name of the output video. If None, the output name will be <input video>_crop.<file extension>. Defaults to None.

Outputs:
    The cropped video.

#### Returns

- `str` - Path to the output video.

## embed_audio_in_video

[[find in source code]](..\_utils.py#L921)

```python
def embed_audio_in_video(source_audio, destination_video, dilation_ratio=1):
```

Embeds an audio file as the audio channel of a video file using ffmpeg.

#### Arguments

- `source_audio` *str* - Path to the audio file to embed.
- `destination_video` *str* - Path to the video file to embed the audio file in.
dilation_ratio (int or float, optional): The source file's length divided by the resulting file's length. Defaults to 1.

Outputs:
    `destination_video` with the embedded audio file.

## extract_subclip

[[find in source code]](..\_utils.py#L313)

```python
def extract_subclip(filename, t1, t2, targetname=None):
```

Extracts a section of the video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
t1 (int or float): The start of the section to extract in seconds.
t2 (int or float): The end of the section to extract in seconds.
- `targetname` *str, optional* - The name for the output file. If None, the name will be <input name>SUB<start time in ms>_<end time in ms>.<file extension>. Defaults to None.

Outputs:
    The extracted section as a video.

## extract_wav

[[find in source code]](..\_utils.py#L705)

```python
def extract_wav(filename):
```

Extracts audio from video into a .wav file via ffmpeg.

#### Arguments

- `filename` *str* - Path to the video file from which the audio track shall be extracted.

Outputs:
    `filename`.wav

#### Returns

- `str` - The path to the output audio file.

## ffmpeg_cmd

[[find in source code]](..\_utils.py#L961)

```python
def ffmpeg_cmd(command, total_time, pb_prefix='Progress'):
```

[summary]

#### Arguments

- `command` *list* - The ffmpeg command to execute as a list. Eg. ['ffmpeg', '-y', '-i', 'myVid.mp4', 'myVid.mov']
total_time (int or float): The length of the output. Needed mainly for the progress bar.
- `pb_prefix` *str, optional* - The prefix for the progress bar. Defaults to 'Progress'.

#### Raises

- `KeyboardInterrupt` - If the user stops the process.

## frame2ms

[[find in source code]](..\_utils.py#L178)

```python
def frame2ms(frame, fps):
```

Converts frames to milliseconds.

#### Arguments

- `frame` *int* - The index of the frame to be converted to milliseconds.
- `fps` *int* - Frames per second.

#### Returns

- `int` - The rounded millisecond value of the input frame index.

## framediff_ffmpeg

[[find in source code]](..\_utils.py#L400)

```python
def framediff_ffmpeg(filename, outname=None, color=True):
```

Renders a frame difference video from the input using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `outname` *str, optional* - The name of the output video. If None, the output name will be <input video>_framediff.<file extension>. Defaults to None.
- `color` *bool, optional* - If False, the output will be grayscale. Defaults to True.

Outputs:
    The frame difference video.

#### Returns

- `str` - Path to the output video.

## get_first_frame_as_image

[[find in source code]](..\_utils.py#L801)

```python
def get_first_frame_as_image(filename, outname=None, pict_format='.png'):
```

Extracts the first frame of a video and saves it as an image using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `outname` *str, optional* - The name for the output image. If None, the output name will be <input name>`pict_format`. Defaults to None.
- `pict_format` *str, optional* - The format to use for the output image. Defaults to '.png'.

Outputs:
    The first frame of the input video as an image file.

#### Returns

- `str` - Path to the output image file.

## get_fps

[[find in source code]](..\_utils.py#L764)

```python
def get_fps(filename):
```

Gets the FPS (frames per second) value of a video using moviepy.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `float` - The FPS value of the input video file.

## get_frame_planecount

[[find in source code]](..\_utils.py#L163)

```python
def get_frame_planecount(frame):
```

Gets the planecount (color channel count) of a video frame.

#### Arguments

frame (numpy array): A frame extracted by `cv2.VideoCapture().read()`.

#### Returns

- `int` - The planecount of the input frame, 3 or 1.

## get_framecount

[[find in source code]](..\_utils.py#L746)

```python
def get_framecount(filename):
```

Returns the number of frames in a video using moviepy.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `int` - The number of frames in the input video file.

## get_length

[[find in source code]](..\_utils.py#L728)

```python
def get_length(filename):
```

Gets the length (in seconds) of a video using moviepy.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `float` - The length of the input video file in seconds.

## get_screen_resolution_scaled

[[find in source code]](..\_utils.py#L830)

```python
def get_screen_resolution_scaled():
```

Gets the scaled screen resolution. Respects display scaling on high DPI displays.

#### Returns

- `int` - The scaled width of the screen.
- `int` - The scaled height of the screen.

## get_screen_video_ratio

[[find in source code]](..\_utils.py#L851)

```python
def get_screen_video_ratio(filename):
```

Gets the screen-to-video ratio. Useful to fit windows on the screen.

#### Arguments

- `filename` *str* - Path to the input video file.

#### Returns

- `int` - The smallest ratio (ie. the one to use for scaling the window to fit the screen).

## get_widthheight

[[find in source code]](..\_utils.py#L782)

```python
def get_widthheight(filename):
```

Gets the width and height of a video using moviepy.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `int` - The width of the input video file.
- `int` - The height of the input video file.

## has_audio

[[find in source code]](..\_utils.py#L876)

```python
def has_audio(filename):
```

Checks if video has audio track using moviepy.

#### Arguments

- `filename` *str* - Path to the video file to check.

#### Returns

- `bool` - True if `filename` has an audio track, False otherwise.

## motiongrams_ffmpeg

[[find in source code]](..\_utils.py#L570)

```python
def motiongrams_ffmpeg(
    filename,
    color=True,
    filtertype='regular',
    threshold=0.05,
    blur='none',
    use_median=False,
    kernel_size=5,
    invert=False,
):
```

Renders horizontal and vertical motiongrams using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `color` *bool, optional* - If False the input is converted to grayscale at the start of the process. This can significantly reduce render time. Defaults to True.
- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `use_median` *bool, optional* - If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
- `kernel_size` *int, optional* - Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
- `invert` *bool, optional* - If True, inverts colors of the motiongrams. Defaults to False.

Outputs:
    `filename`_vgx.png
    `filename`_vgy.png

#### Returns

- `str` - Path to the output horizontal motiongram (_mgx).
- `str` - Path to the output vertical motiongram (_mgy).

## motionvideo_ffmpeg

[[find in source code]](..\_utils.py#L474)

```python
def motionvideo_ffmpeg(
    filename,
    color=True,
    filtertype='regular',
    threshold=0.05,
    blur='none',
    use_median=False,
    kernel_size=5,
    invert=False,
    outname=None,
):
```

Renders a motion video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `color` *bool, optional* - If False the input is converted to grayscale at the start of the process. This can significantly reduce render time. Defaults to True.
- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `use_median` *bool, optional* - If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
- `kernel_size` *int, optional* - Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
- `invert` *bool, optional* - If True, inverts colors of the motion video. Defaults to False.
- `outname` *str, optional* - If None the name of the output video will be <file name>_motion.<file extension>. Defaults to None.

Outputs:
    The motion video.

#### Returns

- `str` - Path to the output video.

## rotate_video

[[find in source code]](..\_utils.py#L348)

```python
def rotate_video(filename, angle):
```

Rotates a video by an `angle` using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
angle (int or float): The angle (in degrees) specifying the amount of rotation. Positive values rotate clockwise.

Outputs:
    `filename`_rot.<file extension>

#### Returns

- `str` - The path to the rotated video file.

## roundup

[[find in source code]](..\_utils.py#L95)

```python
def roundup(num, modulo_num):
```

Rounds up a number to the next integer multiple of another.

#### Arguments

- `num` *int* - The number to round up.
- `modulo_num` *int* - The number whose next integer multiple we want.

#### Returns

- `int` - The rounded-up number.

## scale_array

[[find in source code]](..\_utils.py#L143)

```python
def scale_array(array, out_low, out_high):
```

Scales an array linearly.

#### Arguments

- `array` *arraylike* - The array to be scaled.
out_low (int or float): Minimum of output range.
out_high (int or float): Maximum of output range.

#### Returns

- `arraylike` - The scaled array.

## scale_num

[[find in source code]](..\_utils.py#L125)

```python
def scale_num(val, in_low, in_high, out_low, out_high):
```

Scales a number linearly.

#### Arguments

val (int or float): The value to be scaled.
in_low (int or float): Minimum of input range.
in_high (int or float): Maximum of input range.
out_low (int or float): Minimum of output range.
out_high (int or float): Maximum of output range.

#### Returns

int or float: The scaled number.

## str2sec

[[find in source code]](..\_utils.py#L1004)

```python
def str2sec(time_string):
```

Converts a time code string into seconds.

#### Arguments

- `time_string` *str* - The time code to convert. Eg. '01:33:42'.

#### Returns

int or float: The time code converted to seconds.

## threshold_ffmpeg

[[find in source code]](..\_utils.py#L432)

```python
def threshold_ffmpeg(filename, threshold=0.1, outname=None, binary=False):
```

Renders a pixel-thresholded video from the input using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `threshold` *float, optional* - The normalized pixel value to use as the threshold. Pixels below the threshold will turn black. Defaults to 0.1.
- `outname` *str, optional* - The name of the output video. If None, the output name will be <input video>_thresh.<file extension>. Defaults to None.
- `binary` *bool, optional* - If True, the pixels above the threshold will turn white. Defaults to False.

Outputs:
    The thresholded video.

#### Returns

- `str` - Path to the output video.

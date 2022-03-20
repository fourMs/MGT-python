# Utils

> Auto-generated documentation for [_utils](https://github.com/fourMs/MGT-python/blob/main/_utils.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Utils
    - [FFmpegError](#ffmpegerror)
    - [FFprobeError](#ffprobeerror)
    - [MgFigure](#mgfigure)
        - [MgFigure().show](#mgfigureshow)
    - [MgImage](#mgimage)
    - [MgProgressbar](#mgprogressbar)
        - [MgProgressbar().adjust_printlength](#mgprogressbaradjust_printlength)
        - [MgProgressbar().get_now](#mgprogressbarget_now)
        - [MgProgressbar().over_time_limit](#mgprogressbarover_time_limit)
        - [MgProgressbar().progress](#mgprogressbarprogress)
    - [NoDurationError](#nodurationerror)
    - [NoStreamError](#nostreamerror)
    - [WrongContainer](#wrongcontainer)
    - [audio_dilate](#audio_dilate)
    - [cast_into_avi](#cast_into_avi)
    - [clamp](#clamp)
    - [convert](#convert)
    - [convert_to_avi](#convert_to_avi)
    - [convert_to_grayscale](#convert_to_grayscale)
    - [convert_to_mp4](#convert_to_mp4)
    - [convert_to_webm](#convert_to_webm)
    - [crop_ffmpeg](#crop_ffmpeg)
    - [embed_audio_in_video](#embed_audio_in_video)
    - [extract_subclip](#extract_subclip)
    - [extract_wav](#extract_wav)
    - [ffmpeg_cmd](#ffmpeg_cmd)
    - [ffprobe](#ffprobe)
    - [frame2ms](#frame2ms)
    - [framediff_ffmpeg](#framediff_ffmpeg)
    - [generate_outfilename](#generate_outfilename)
    - [get_box_video_ratio](#get_box_video_ratio)
    - [get_first_frame_as_image](#get_first_frame_as_image)
    - [get_fps](#get_fps)
    - [get_frame_planecount](#get_frame_planecount)
    - [get_framecount](#get_framecount)
    - [get_length](#get_length)
    - [get_widthheight](#get_widthheight)
    - [has_audio](#has_audio)
    - [in_colab](#in_colab)
    - [motiongrams_ffmpeg](#motiongrams_ffmpeg)
    - [motionvideo_ffmpeg](#motionvideo_ffmpeg)
    - [pass_if_container_is](#pass_if_container_is)
    - [pass_if_containers_match](#pass_if_containers_match)
    - [rotate_video](#rotate_video)
    - [roundup](#roundup)
    - [scale_array](#scale_array)
    - [scale_num](#scale_num)
    - [str2sec](#str2sec)
    - [threshold_ffmpeg](#threshold_ffmpeg)
    - [unwrap_str](#unwrap_str)
    - [wrap_str](#wrap_str)

## FFmpegError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1382)

```python
class FFmpegError(Exception):
    def __init__(message):
```

## FFprobeError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1050)

```python
class FFprobeError(Exception):
    def __init__(message):
```

## MgFigure

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L360)

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

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L385)

```python
def show():
```

Shows the internal matplotlib.pyplot.figure.

## MgImage

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L338)

```python
class MgImage():
    def __init__(filename):
```

Class for handling images in the Musical Gestures Toolbox.

## MgProgressbar

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1)

```python
class MgProgressbar():
    def __init__(
        total=100,
        time_limit=0.5,
        prefix='Progress',
        suffix='Complete',
        decimals=1,
        length=40,
        fill='█',
    ):
```

Calls in a loop to create terminal progress bar.

### MgProgressbar().adjust_printlength

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L62)

```python
def adjust_printlength():
```

### MgProgressbar().get_now

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L42)

```python
def get_now():
```

Gets the current time.

#### Returns

- `datetime.datetime.timestamp` - The current time.

### MgProgressbar().over_time_limit

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L52)

```python
def over_time_limit():
```

Checks if we should redraw the progress bar at this moment.

#### Returns

- `bool` - True if equal or more time has passed than `self.time_limit` since the last redraw.

### MgProgressbar().progress

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L124)

```python
def progress(iteration):
```

Progresses the progress bar to the next step.

#### Arguments

- `iteration` *float* - The current iteration. For example, the 57th out of 100 steps, or 12.3s out of the total 60s.

## NoDurationError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1059)

```python
class NoDurationError(FFprobeError):
```

#### See also

- [FFprobeError](#ffprobeerror)

## NoStreamError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1055)

```python
class NoStreamError(FFprobeError):
```

#### See also

- [FFprobeError](#ffprobeerror)

## WrongContainer

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L392)

```python
class WrongContainer(Exception):
    def __init__(message):
```

## audio_dilate

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1315)

```python
def audio_dilate(
    filename,
    dilation_ratio=1,
    target_name=None,
    overwrite=False,
):
```

Time-stretches or -shrinks (dilates) an audio file using ffmpeg.

#### Arguments

- `filename` *str* - Path to the audio file to dilate.
- `dilation_ratio` *float, optional* - The source file's length divided by the resulting file's length. Defaults to 1.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_dilated" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - The path to the output audio file.

## cast_into_avi

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L546)

```python
def cast_into_avi(filename, target_name=None, overwrite=False):
```

*Experimental*
Casts a video into and .avi container using ffmpeg. Much faster than [convert_to_avi](#convert_to_avi),
but does not always work well with cv2 or built-in video players.

#### Arguments

- `filename` *str* - Path to the input video file.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - The path to the output '.avi' file.

## clamp

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L191)

```python
def clamp(num, min_value, max_value):
```

Clamps a number between a minimum and maximum value.

#### Arguments

- `num` *float* - The number to clamp.
- `min_value` *float* - The minimum allowed value.
- `max_value` *float* - The maximum allowed value.

#### Returns

- `float` - The clamped number.

## convert

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L431)

```python
def convert(filename, target_name, overwrite=False):
```

Converts a video to another format/container using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.
- `target_name` *str* - Target filename as path.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - The path to the output file.

## convert_to_avi

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L459)

```python
def convert_to_avi(filename, target_name=None, overwrite=False):
```

Converts a video to one with .avi extension using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - The path to the output '.avi' file.

## convert_to_grayscale

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L656)

```python
def convert_to_grayscale(filename, target_name=None, overwrite=False):
```

Converts a video to grayscale using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename with the suffix "_gray" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - The path to the grayscale video file.

## convert_to_mp4

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L488)

```python
def convert_to_mp4(filename, target_name=None, overwrite=False):
```

Converts a video to one with .mp4 extension using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - The path to the output '.mp4' file.

## convert_to_webm

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L517)

```python
def convert_to_webm(filename, target_name=None, overwrite=False):
```

Converts a video to one with .webm extension using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - The path to the output '.webm' file.

## crop_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L981)

```python
def crop_ffmpeg(filename, w, h, x, y, target_name=None, overwrite=False):
```

Crops a video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `w` *int* - The desired width.
- `h` *int* - The desired height.
- `x` *int* - The horizontal coordinate of the top left pixel of the cropping rectangle.
- `y` *int* - The vertical coordinate of the top left pixel of the cropping rectangle.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_crop" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the output video.

## embed_audio_in_video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1345)

```python
def embed_audio_in_video(source_audio, destination_video, dilation_ratio=1):
```

Embeds an audio file as the audio channel of a video file using ffmpeg.

#### Arguments

- `source_audio` *str* - Path to the audio file to embed.
- `destination_video` *str* - Path to the video file to embed the audio file in.
- `dilation_ratio` *float, optional* - The source file's length divided by the resulting file's length. Defaults to 1.

## extract_subclip

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L573)

```python
def extract_subclip(filename, t1, t2, target_name=None, overwrite=False):
```

Extracts a section of the video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `t1` *float* - The start of the section to extract in seconds.
- `t2` *float* - The end of the section to extract in seconds.
- `target_name` *str, optional* - The name for the output file. If None, the name will be \<input name\>SUB\<start time in ms\>_\<end time in ms\>.\<file extension\>. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the extracted section as a video.

## extract_wav

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1017)

```python
def extract_wav(filename, target_name=None, overwrite=False):
```

Extracts audio from video into a .wav file via ffmpeg.

#### Arguments

- `filename` *str* - Path to the video file from which the audio track shall be extracted.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - The path to the output audio file.

## ffmpeg_cmd

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1387)

```python
def ffmpeg_cmd(
    command,
    total_time,
    pb_prefix='Progress',
    print_cmd=False,
    stream=True,
):
```

Run an ffmpeg command in a subprocess and show progress using an MgProgressbar.

#### Arguments

- `command` *list* - The ffmpeg command to execute as a list. Eg. ['ffmpeg', '-y', '-i', 'myVid.mp4', 'myVid.mov']
- `total_time` *float* - The length of the output. Needed mainly for the progress bar.
- `pb_prefix` *str, optional* - The prefix for the progress bar. Defaults to 'Progress'.
- `print_cmd` *bool, optional* - Whether to print the full ffmpeg command to the console before executing it. Good for debugging. Defaults to False.
- `stream` *bool, optional* - Whether to have a continuous output stream or just (the last) one. Defaults to True (continuous stream).

#### Raises

- `KeyboardInterrupt` - If the user stops the process.
- `FFmpegError` - If the ffmpeg process was unsuccessful.

## ffprobe

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1063)

```python
def ffprobe(filename):
```

Returns info about video/audio file using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `str` - decoded FFprobe output (stdout) as one string.

## frame2ms

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L323)

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

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L686)

```python
def framediff_ffmpeg(filename, target_name=None, color=True, overwrite=False):
```

Renders a frame difference video from the input using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_framediff" should be used).
- `color` *bool, optional* - If False, the output will be grayscale. Defaults to True.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the output video.

## generate_outfilename

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L244)

```python
def generate_outfilename(requested_name):
```

Returns a unique filepath to avoid overwriting existing files. Increments requested
filename if necessary by appending an integer, like "_0" or "_1", etc to the file name.

#### Arguments

- `requested_name` *str* - Requested file name as path string.

#### Returns

- `str` - If file at requested_name is not present, then requested_name, else an incremented filename.

## get_box_video_ratio

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1289)

```python
def get_box_video_ratio(filename, box_width=800, box_height=600):
```

Gets the box-to-video ratio between an arbitrarily defind box and the video dimensions. Useful to fit windows into a certain area.

#### Arguments

- `filename` *str* - Path to the input video file.
- `box_width` *int, optional* - The width of the box to fit the video into.
- `box_height` *int, optional* - The height of the box to fit the video into.

#### Returns

- `int` - The smallest ratio (ie. the one to use for scaling the video window to fit into the box).

## get_first_frame_as_image

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1257)

```python
def get_first_frame_as_image(
    filename,
    target_name=None,
    pict_format='.png',
    overwrite=False,
):
```

Extracts the first frame of a video and saves it as an image using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `target_name` *str, optional* - The name for the output image. Defaults to None (which assumes that the input filename should be used).
- `pict_format` *str, optional* - The format to use for the output image. Defaults to '.png'.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the output image file.

## get_fps

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1224)

```python
def get_fps(filename):
```

Gets the FPS (frames per second) value of a video using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `float` - The FPS value of the input video file.

## get_frame_planecount

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L308)

```python
def get_frame_planecount(frame):
```

Gets the planecount (color channel count) of a video frame.

#### Arguments

frame (numpy array): A frame extracted by `cv2.VideoCapture().read()`.

#### Returns

- `int` - The planecount of the input frame, 3 or 1.

## get_framecount

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1174)

```python
def get_framecount(filename, fast=True):
```

Returns the number of frames in a video using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `int` - The number of frames in the input video file.

## get_length

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1146)

```python
def get_length(filename):
```

Gets the length (in seconds) of a video using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `float` - The length of the input video file in seconds.

## get_widthheight

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1092)

```python
def get_widthheight(filename):
```

Gets the width and height of a video using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `int` - The width of the input video file.
- `int` - The height of the input video file.

## has_audio

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1120)

```python
def has_audio(filename):
```

Checks if video has audio track using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to check.

#### Returns

- `bool` - True if `filename` has an audio track, False otherwise.

## in_colab

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1508)

```python
def in_colab():
```

Check's if the environment is a Google Colab document.

#### Returns

- `bool` - True if the environment is a Colab document, otherwise False.

## motiongrams_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L862)

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
    target_name_x=None,
    target_name_y=None,
    overwrite=False,
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
- `target_name_x` *str, optional* - Target output name for the motiongram on the X axis. Defaults to None (which assumes that the input filename with the suffix "_mgx_ffmpeg" should be used).
- `target_name_y` *str, optional* - Target output name for the motiongram on the Y axis. Defaults to None (which assumes that the input filename with the suffix "_mgy_ffmpeg" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the output horizontal motiongram (_mgx).
- `str` - Path to the output vertical motiongram (_mgy).

## motionvideo_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L763)

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
    target_name=None,
    overwrite=False,
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
- `target_name` *str, optional* - Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the output video.

## pass_if_container_is

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L415)

```python
def pass_if_container_is(container, file):
```

Checks if a file's extension matches a desired one. Passes if so, raises WrongContainer if not.

#### Arguments

- `container` *str* - The container to match.
- `file` *str* - Path to the file to inspect.

#### Raises

- `WrongContainer` - If the file extension (container) matches the desired one.

## pass_if_containers_match

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L397)

```python
def pass_if_containers_match(file_1, file_2):
```

Checks if file extensions match between two files. If they do it passes, is they don't it raises WrongContainer exception.

#### Arguments

- `file_1` *str* - First file in comparison.
- `file_2` *str* - Second file in comparison.

#### Raises

- `WrongContainer` - If file extensions (containers) mismatch.

## rotate_video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L624)

```python
def rotate_video(filename, angle, target_name=None, overwrite=False):
```

Rotates a video by an `angle` using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `angle` *float* - The angle (in degrees) specifying the amount of rotation. Positive values rotate clockwise.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename with the suffix "_rot" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - The path to the rotated video file.

## roundup

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L176)

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

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L224)

```python
def scale_array(array, out_low, out_high):
```

Scales an array linearly.

#### Arguments

- `array` *arraylike* - The array to be scaled.
- `out_low` *float* - Minimum of output range.
- `out_high` *float* - Maximum of output range.

#### Returns

- `arraylike` - The scaled array.

## scale_num

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L206)

```python
def scale_num(val, in_low, in_high, out_low, out_high):
```

Scales a number linearly.

#### Arguments

- `val` *float* - The value to be scaled.
- `in_low` *float* - Minimum of input range.
- `in_high` *float* - Maximum of input range.
- `out_low` *float* - Minimum of output range.
- `out_high` *float* - Maximum of output range.

#### Returns

- `float` - The scaled number.

## str2sec

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1455)

```python
def str2sec(time_string):
```

Converts a time code string into seconds.

#### Arguments

- `time_string` *str* - The time code to convert. Eg. '01:33:42'.

#### Returns

- `float` - The time code converted to seconds.

## threshold_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L719)

```python
def threshold_ffmpeg(
    filename,
    threshold=0.1,
    target_name=None,
    binary=False,
    overwrite=False,
):
```

Renders a pixel-thresholded video from the input using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `threshold` *float, optional* - The normalized pixel value to use as the threshold. Pixels below the threshold will turn black. Defaults to 0.1.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_thresh" should be used).
- `binary` *bool, optional* - If True, the pixels above the threshold will turn white. Defaults to False.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `str` - Path to the output video.

## unwrap_str

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1490)

```python
def unwrap_str(string):
```

Unwraps a string from quotes.

#### Arguments

- `string` *str* - The string to inspect.

#### Returns

- `str` - The (unwrapped) string.

## wrap_str

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_utils.py#L1469)

```python
def wrap_str(string, matchers=[' ', '(', ')']):
```

Wraps a string in double quotes if it contains any of `matchers` - by default: space or parentheses.
Useful when working with shell commands.

#### Arguments

- `string` *str* - The string to inspect.
- `matchers` *list, optional* - The list of characters to look for in the string. Defaults to [" ", "(", ")"].

#### Returns

- `str` - The (wrapped) string.

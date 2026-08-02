# Utils

> Auto-generated documentation for [musicalgestures._utils](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Utils
    - [FFmpegError](#ffmpegerror)
    - [FFprobeError](#ffprobeerror)
    - [FilesNotMatchError](#filesnotmatcherror)
    - [MgFigure](#mgfigure)
        - [MgFigure().save](#mgfiguresave)
        - [MgFigure().show](#mgfigureshow)
        - [MgFigure().to_html](#mgfigureto_html)
    - [MgImage](#mgimage)
        - [MgImage().save](#mgimagesave)
        - [MgImage().to_html](#mgimageto_html)
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
    - [cuda_build_available](#cuda_build_available)
    - [cuda_unavailable_reason](#cuda_unavailable_reason)
    - [embed_audio_in_video](#embed_audio_in_video)
    - [extract_frame](#extract_frame)
    - [extract_subclip](#extract_subclip)
    - [extract_wav](#extract_wav)
    - [ffmpeg_cmd](#ffmpeg_cmd)
    - [ffmpeg_has_encoder](#ffmpeg_has_encoder)
    - [ffprobe](#ffprobe)
    - [frame2ms](#frame2ms)
    - [framediff_ffmpeg](#framediff_ffmpeg)
    - [generate_outfilename](#generate_outfilename)
    - [get_box_video_ratio](#get_box_video_ratio)
    - [get_cuda_device_count](#get_cuda_device_count)
    - [get_first_frame_as_image](#get_first_frame_as_image)
    - [get_fps](#get_fps)
    - [get_frame_planecount](#get_frame_planecount)
    - [get_framecount](#get_framecount)
    - [get_length](#get_length)
    - [get_rotation](#get_rotation)
    - [get_widthheight](#get_widthheight)
    - [has_audio](#has_audio)
    - [in_colab](#in_colab)
    - [in_ipynb](#in_ipynb)
    - [merge_videos](#merge_videos)
    - [motiongrams_ffmpeg](#motiongrams_ffmpeg)
    - [motionvideo_ffmpeg](#motionvideo_ffmpeg)
    - [normalize_rotation](#normalize_rotation)
    - [pass_if_container_is](#pass_if_container_is)
    - [pass_if_containers_match](#pass_if_containers_match)
    - [quality_metrics](#quality_metrics)
    - [resolve_filename](#resolve_filename)
    - [rotate_video](#rotate_video)
    - [roundup](#roundup)
    - [scale_array](#scale_array)
    - [scale_num](#scale_num)
    - [show_progress](#show_progress)
    - [str2sec](#str2sec)
    - [threshold_ffmpeg](#threshold_ffmpeg)
    - [unwrap_str](#unwrap_str)
    - [wrap_str](#wrap_str)

## FFmpegError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1713)

```python
class FFmpegError(Exception):
    def __init__(message):
```

## FFprobeError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1223)

```python
class FFprobeError(Exception):
    def __init__(message):
```

## FilesNotMatchError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1952)

```python
class FilesNotMatchError(Exception):
    def __init__(message):
```

## MgFigure

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L268)

```python
class MgFigure():
    def __init__(
        figure=None,
        figure_type: str = None,
        data: dict = None,
        layers: list = None,
        image=None,
    ):
```

Class for working with figures and plots within the Musical Gestures Toolbox.

### MgFigure().save

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L294)

```python
def save(target_name: str):
```

Save the rendered figure to ``target_name``.

Copies the rendered PNG if one exists, otherwise re-saves the internal matplotlib
figure. Returns an MgImage pointing to the saved file (or None if nothing to save).

### MgFigure().show

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L312)

```python
def show(**kwargs):
```

Display the rendered figure.

In a Jupyter notebook the saved image is shown inline; otherwise it is opened
in a viewer window. Additional keyword arguments are forwarded to the underlying
MgImage.show(). If no rendered image is available, the internal matplotlib figure
is returned instead.

### MgFigure().to_html

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L330)

```python
def to_html() -> str:
```

Return an HTML snippet embedding the rendered figure (base64-encoded).

NB: This is intentionally **not** exposed as ``_repr_html_``, so an MgFigure
is not auto-rendered as the last expression of a Jupyter cell. Use ``show()``
to display the figure.

## MgImage

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L214)

```python
class MgImage():
    def __init__(filename: str):
```

Class for handling images in the Musical Gestures Toolbox.

### MgImage().save

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L235)

```python
def save(target_name: str) -> 'MgImage':
```

Save (copy) the image to ``target_name`` and return a new MgImage pointing to it.

### MgImage().to_html

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L244)

```python
def to_html() -> str:
```

Return an HTML snippet embedding the image (base64-encoded).

NB: This is intentionally **not** exposed as ``_repr_html_``, so an MgImage
is not auto-rendered as the last expression of a Jupyter cell. Use ``show()``
to display the image.

## MgProgressbar

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L36)

```python
class MgProgressbar():
    def __init__(
        total: int = 100,
        time_limit: float = 0.5,
        prefix: str = 'Progress',
        suffix: str = 'Complete',
        decimals: int = 1,
        length: int = 40,
        fill: str = '█',
    ):
```

Calls in a loop to create terminal progress bar.

### MgProgressbar().adjust_printlength

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L97)

```python
def adjust_printlength() -> None:
```

### MgProgressbar().get_now

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L77)

```python
def get_now():
```

Gets the current time.

#### Returns

- `datetime.datetime.timestamp` - The current time.

### MgProgressbar().over_time_limit

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L87)

```python
def over_time_limit() -> bool:
```

Checks if we should redraw the progress bar at this moment.

#### Returns

- `bool` - True if equal or more time has passed than `self.time_limit` since the last redraw.

### MgProgressbar().progress

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L159)

```python
def progress(iteration: float) -> None:
```

Progresses the progress bar to the next step.

#### Arguments

- `iteration` *float* - The current iteration. For example, the 57th out of 100 steps, or 12.3s out of the total 60s.

## NoDurationError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1232)

```python
class NoDurationError(FFprobeError):
```

#### See also

- [FFprobeError](#ffprobeerror)

## NoStreamError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1228)

```python
class NoStreamError(FFprobeError):
```

#### See also

- [FFprobeError](#ffprobeerror)

## WrongContainer

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L555)

```python
class WrongContainer(Exception):
    def __init__(message):
```

## audio_dilate

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1643)

```python
def audio_dilate(
    filename: str,
    dilation_ratio: float = 1,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Time-stretches or -shrinks (dilates) an audio file using ffmpeg.

#### Arguments

- `filename` *str* - Path to the audio file to dilate.
- `dilation_ratio` *float, optional* - The source file's length divided by the resulting file's length. Defaults to 1.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_dilated" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - The path to the output audio file.

## cast_into_avi

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L744)

```python
def cast_into_avi(
    filename: str,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

*Experimental*
Casts a video into and .avi container using ffmpeg. Much faster than [convert_to_avi](#convert_to_avi),
but does not always work well with cv2 or built-in video players.

#### Arguments

- `filename` *str* - Path to the input video file.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - The path to the output '.avi' file.

## clamp

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L378)

```python
def clamp(num: float, min_value: float, max_value: float) -> float:
```

Clamps a number between a minimum and maximum value.

#### Arguments

- `num` *float* - The number to clamp.
- `min_value` *float* - The minimum allowed value.
- `max_value` *float* - The maximum allowed value.

#### Returns

- `float` - The clamped number.

## convert

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L619)

```python
def convert(filename: str, target_name: str, overwrite: bool = True) -> str:
```

Converts a video to another format/container using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.
- `target_name` *str* - Target filename as path.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - The path to the output file.

## convert_to_avi

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L657)

```python
def convert_to_avi(
    filename: str,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Converts a video to one with .avi extension using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - The path to the output '.avi' file.

## convert_to_grayscale

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L918)

```python
def convert_to_grayscale(
    filename: str,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Converts a video to grayscale using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename with the suffix "_gray" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - The path to the grayscale video file.

## convert_to_mp4

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L686)

```python
def convert_to_mp4(
    filename: str,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Converts a video to one with .mp4 extension using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - The path to the output '.mp4' file.

## convert_to_webm

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L715)

```python
def convert_to_webm(
    filename: str,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Converts a video to one with .webm extension using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file to convert.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - The path to the output '.webm' file.

## crop_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1155)

```python
def crop_ffmpeg(
    filename: str,
    w: int,
    h: int,
    x: int,
    y: int,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Crops a video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `w` *int* - The desired width.
- `h` *int* - The desired height.
- `x` *int* - The horizontal coordinate of the top left pixel of the cropping rectangle.
- `y` *int* - The vertical coordinate of the top left pixel of the cropping rectangle.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_crop" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output video.

## cuda_build_available

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1875)

```python
def cuda_build_available() -> bool:
```

Returns whether the installed OpenCV was compiled with CUDA support.

#### Returns

- `bool` - True if OpenCV's build information reports CUDA support, else False.

## cuda_unavailable_reason

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1894)

```python
def cuda_unavailable_reason() -> str:
```

Returns a short, actionable explanation of why the OpenCV CUDA backend is unavailable.

Distinguishes the common case (the pip OpenCV wheels are built without CUDA) from the
case where OpenCV has CUDA but no GPU/driver is detected.

#### Returns

- `str` - A human-readable explanation.

## embed_audio_in_video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1673)

```python
def embed_audio_in_video(
    source_audio: str,
    destination_video: str,
    dilation_ratio: float = 1,
) -> None:
```

Embeds an audio file as the audio channel of a video file using ffmpeg.

#### Arguments

- `source_audio` *str* - Path to the audio file to embed.
- `destination_video` *str* - Path to the video file to embed the audio file in.
- `dilation_ratio` *float, optional* - The source file's length divided by the resulting file's length. Defaults to 1.

## extract_frame

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L771)

```python
def extract_frame(
    filename: str,
    frame: int = None,
    time: Union[str, float] = None,
    target_name: str = None,
    overwrite: bool = False,
) -> str:
```

Extracts a single frame from a video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `frame` *int* - The frame number to extract.
time (Union[str, float]): The time in HH:MM:ss.ms where to extract the frame from. If float, it is interpreted as seconds from the start of the video.
- `target_name` *str, optional* - The name for the output file. If None, the name will be <input name>FRAME<frame number>.<file extension>. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

## extract_subclip

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L827)

```python
def extract_subclip(
    filename: str,
    t1: float,
    t2: float,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Extracts a section of the video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `t1` *float* - The start of the section to extract in seconds.
- `t2` *float* - The end of the section to extract in seconds.
- `target_name` *str, optional* - The name for the output file. If None, the name will be <input name>SUB<start time in ms>_<end time in ms>.<file extension>. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the extracted section as a video.

## extract_wav

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1191)

```python
def extract_wav(
    filename: str,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Extracts audio from video into a .wav file via ffmpeg.

#### Arguments

- `filename` *str* - Path to the video file from which the audio track shall be extracted.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - The path to the output audio file.

## ffmpeg_cmd

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1718)

```python
def ffmpeg_cmd(
    command: list,
    total_time: float,
    pb_prefix: str = 'Progress',
    print_cmd: bool = False,
    stream: bool = True,
    pipe: str | None = None,
):
```

Run an ffmpeg command in a subprocess and show progress using an MgProgressbar.

#### Arguments

- `command` *list* - The ffmpeg command to execute as a list. Eg. ['ffmpeg', '-y', '-i', 'myVid.mp4', 'myVid.mov']
- `total_time` *float* - The length of the output. Needed mainly for the progress bar.
- `pb_prefix` *str, optional* - The prefix for the progress bar. Defaults to 'Progress'.
- `print_cmd` *bool, optional* - Whether to print the full ffmpeg command to the console before executing it. Good for debugging. Defaults to False.
- `stream` *bool, optional* - Whether to have a continuous output stream or just (the last) one. Defaults to True (continuous stream).
- `pipe` *str, optional* - Whether to pipe video frames from FFmpeg to numpy array. Possible to read the video frame by frame with pipe='read', to load video in memory with pipe='load', or to write the frames of a numpy array to a video file with pipe='write'. Defaults to None.

#### Raises

- `KeyboardInterrupt` - If the user stops the process.
- `FFmpegError` - If the ffmpeg process was unsuccessful.

## ffmpeg_has_encoder

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L597)

```python
def ffmpeg_has_encoder(name: str) -> bool:
```

Returns True if the installed FFmpeg has the named encoder (e.g. 'libtheora').

Useful for guarding format conversions whose codec may be missing from a given
FFmpeg build (notably libtheora/libvorbis for .ogg on some macOS/Windows builds).

## ffprobe

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1241)

```python
def ffprobe(filename: str) -> str:
```

Returns info about video/audio file using FFprobe.

The result is cached per file (keyed by path + modification time + size), so
repeated probes of an unchanged file don't spawn a new subprocess each time.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `str` - decoded FFprobe output (stdout) as one string.

## frame2ms

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L540)

```python
def frame2ms(frame: int, fps: int) -> int:
```

Converts frames to milliseconds.

#### Arguments

- `frame` *int* - The index of the frame to be converted to milliseconds.
- `fps` *int* - Frames per second.

#### Returns

- `int` - The rounded millisecond value of the input frame index.

## framediff_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L946)

```python
def framediff_ffmpeg(
    filename: str,
    target_name: str | None = None,
    color: bool = True,
    overwrite: bool = True,
) -> str:
```

Renders a frame difference video from the input using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_framediff" should be used).
- `color` *bool, optional* - If False, the output will be grayscale. Defaults to True.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output video.

## generate_outfilename

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L431)

```python
def generate_outfilename(requested_name: str) -> str:
```

Returns a unique filepath to avoid overwriting existing files. Increments requested
filename if necessary by appending an integer, like "_0" or "_1", etc to the file name.

#### Arguments

- `requested_name` *str* - Requested file name as path string.

#### Returns

- `str` - If file at requested_name is not present, then requested_name, else an incremented filename.

## get_box_video_ratio

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1568)

```python
def get_box_video_ratio(
    filename: str,
    box_width: int = 800,
    box_height: int = 600,
) -> float:
```

Gets the box-to-video ratio between an arbitrarily defind box and the video dimensions. Useful to fit windows into a certain area.

#### Arguments

- `filename` *str* - Path to the input video file.
- `box_width` *int, optional* - The width of the box to fit the video into.
- `box_height` *int, optional* - The height of the box to fit the video into.

#### Returns

- `int` - The smallest ratio (ie. the one to use for scaling the video window to fit into the box).

## get_cuda_device_count

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1860)

```python
def get_cuda_device_count() -> int:
```

Returns the number of CUDA-capable GPU devices visible to OpenCV.

#### Returns

- `int` - Number of available CUDA devices, or 0 if the OpenCV CUDA
     module is unavailable or no devices are detected.

## get_first_frame_as_image

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1536)

```python
def get_first_frame_as_image(
    filename: str,
    target_name: str | None = None,
    pict_format: str = '.png',
    overwrite: bool = True,
) -> str:
```

Extracts the first frame of a video and saves it as an image using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `target_name` *str, optional* - The name for the output image. Defaults to None (which assumes that the input filename should be used).
- `pict_format` *str, optional* - The format to use for the output image. Defaults to '.png'.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output image file.

## get_fps

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1503)

```python
def get_fps(filename: str) -> float:
```

Gets the FPS (frames per second) value of a video using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `float` - The FPS value of the input video file.

## get_frame_planecount

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L525)

```python
def get_frame_planecount(frame: np.ndarray) -> int:
```

Gets the planecount (color channel count) of a video frame.

#### Arguments

frame (numpy array): A frame extracted by `cv2.VideoCapture().read()`.

#### Returns

- `int` - The planecount of the input frame, 3 or 1.

## get_framecount

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1445)

```python
def get_framecount(filename: str, fast: bool = True) -> int:
```

Returns the number of frames in a video using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to measure.
- `fast` *bool, optional* - If True (default), count demuxed video packets
    (``-count_packets``). This is fast (no decoding) and—unlike the container's
    ``nb_frames`` metadata, which is unreliable (e.g. off by one on many AVIs, or absent
    on WebM)—matches the true decoded frame count for normal video streams. If False,
    fully decode and count frames (``-count_frames``): the ground truth, but slower.
    Defaults to True.

#### Returns

- `int` - The number of frames in the input video file.

## get_length

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1417)

```python
def get_length(filename: str) -> float:
```

Gets the length (in seconds) of a video using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `float` - The length of the input video file in seconds.

## get_rotation

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1352)

```python
def get_rotation(filename: str) -> int:
```

Returns the display rotation (degrees) stored in a video's metadata.

Phone/portrait videos often store landscape pixels plus a rotation flag (display
matrix). FFmpeg's frame pipe applies this automatically while OpenCV's VideoCapture
does not, which can leave some processes rotated. This reads the flag so the
orientation can be normalised.

#### Returns

- `int` - rotation in degrees (e.g. 0, 90, 180, 270), or 0 if none/unknown.

## get_widthheight

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1285)

```python
def get_widthheight(filename: str) -> Tuple[int, int]:
```

Gets the width and height of a video using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to measure.

#### Returns

- `int` - The width of the input video file.
- `int` - The height of the input video file.

## has_audio

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1326)

```python
def has_audio(filename: str) -> bool:
```

Checks if video has audio track using FFprobe.

#### Arguments

- `filename` *str* - Path to the video file to check.

#### Returns

- `bool` - True if `filename` has an audio track, False otherwise.

## in_colab

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1917)

```python
def in_colab() -> bool:
```

Check's if the environment is a Google Colab document.

#### Returns

- `bool` - True if the environment is a Colab document, otherwise False.

## in_ipynb

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1932)

```python
def in_ipynb() -> bool:
```

Check if the environment is a Jupyter notebook.
Taken from https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook.

#### Returns

- `bool` - True if the environment is a Jupyter notebook, otherwise False.

## merge_videos

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1957)

```python
def merge_videos(
    media_paths: list,
    target_name: str = None,
    overwrite: bool = False,
    print_cmd: bool = False,
) -> str:
```

Merges a list of video files into a single video file using ffmpeg.

#### Arguments

- `media_paths` *list* - List of paths to the video files to merge.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_merged" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output video.

## motiongrams_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1079)

```python
def motiongrams_ffmpeg(
    filename: str,
    color: bool = True,
    filtertype: str = 'regular',
    threshold: float = 0.05,
    blur: str = 'none',
    use_median: bool = False,
    kernel_size: int = 5,
    invert: bool = False,
    target_name_x: str | None = None,
    target_name_y: str | None = None,
    overwrite: bool = True,
) -> tuple:
```

Renders horizontal and vertical motiongrams using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `color` *bool, optional* - If False the input is converted to grayscale at the start of the process. This can significantly reduce render time. Defaults to True.
- `filtertype` *str, optional* - 'Regular' turns all values below `threshold` to 0. 'Binary' turns all values below `threshold` to 0, above `threshold` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `threshold` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `use_median` *bool, optional* - If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
- `kernel_size` *int, optional* - Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
- `invert` *bool, optional* - If True, inverts colors of the motiongrams. Defaults to False.
- `target_name_x` *str, optional* - Target output name for the motiongram on the X axis. Defaults to None (which assumes that the input filename with the suffix "_mgx_ffmpeg" should be used).
- `target_name_y` *str, optional* - Target output name for the motiongram on the Y axis. Defaults to None (which assumes that the input filename with the suffix "_mgy_ffmpeg" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output horizontal motiongram (_mgx).
- `str` - Path to the output vertical motiongram (_mgy).

## motionvideo_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1023)

```python
def motionvideo_ffmpeg(
    filename: str,
    color: bool = True,
    filtertype: str = 'regular',
    threshold: float = 0.05,
    blur: str = 'none',
    use_median: bool = False,
    kernel_size: int = 5,
    invert: bool = False,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Renders a motion video using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `color` *bool, optional* - If False the input is converted to grayscale at the start of the process. This can significantly reduce render time. Defaults to True.
- `filtertype` *str, optional* - 'Regular' turns all values below `threshold` to 0. 'Binary' turns all values below `threshold` to 0, above `threshold` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `threshold` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `use_median` *bool, optional* - If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
- `kernel_size` *int, optional* - Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
- `invert` *bool, optional* - If True, inverts colors of the motion video. Defaults to False.
- `target_name` *str, optional* - Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output video.

## normalize_rotation

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1382)

```python
def normalize_rotation(filename: str, overwrite: bool = True) -> str:
```

If a video carries a display-rotation flag (e.g. a phone portrait recording with
landscape pixels), re-encode it so the rotation is baked into the pixels and the
flag removed. This makes every downstream reader (FFmpeg pipe, OpenCV, filters)
agree on the orientation, preventing some processes from coming out rotated.

#### Arguments

- `filename` *str* - Path to the video file.
- `overwrite` *bool* - Overwrite the "_oriented" output if it exists. Defaults to True.

#### Returns

- `str` - Path to an upright video—the original if it had no rotation, otherwise a
    new "_oriented" copy.

## pass_if_container_is

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L578)

```python
def pass_if_container_is(container: str, file: str) -> None:
```

Checks if a file's extension matches a desired one. Passes if so, raises WrongContainer if not.

#### Arguments

- `container` *str* - The container to match.
- `file` *str* - Path to the file to inspect.

#### Raises

- `WrongContainer` - If the file extension (container) matches the desired one.

## pass_if_containers_match

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L560)

```python
def pass_if_containers_match(file_1: str, file_2: str) -> None:
```

Checks if file extensions match between two files. If they do it passes, is they don't it raises WrongContainer exception.

#### Arguments

- `file_1` *str* - First file in comparison.
- `file_2` *str* - Second file in comparison.

#### Raises

- `WrongContainer` - If file extensions (containers) mismatch.

## quality_metrics

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1594)

```python
def quality_metrics(
    original: str,
    processed: str,
    metric: str | None = None,
) -> None:
```

Compute video quality metrics between two video files for comparing the quality of video codecs or measuring the efficacy of encoding configuration.
Possible to compute three major video quality metrics used for objective evaluation, namely:

- PSNR: It is the most commonly used video quality metric. But it has the lowest predictive value, so the results are inconsistent.
  Used by major platforms like Netflix and Facebook to compare different codecs and for similar use cases. Overall usage is declining.
- SSIM: Mostly used by technical experts like codec researchers and compression engineers.
  Usage is declining steadily. However, it has a higher predictive value than PSNR.
- VMAF: Introduced first by Netflix but then converted into an open-source asset. VMAF is easily accessible and widely used.
  Designed specifically for evaluating the video quality of streams encoded for multiple-resolution rungs.

#### Arguments

- `original` *str* - Path to the original/reference video file.
- `processed` *str* - Path to the processed/distorted video file.
- `metric` *str, optional* - Type of quality metric to compute ('vmaf', 'ssim', or 'psnr'). Defaults to None (which computes all the metrics).

## resolve_filename

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L495)

```python
def resolve_filename(
    stem: str,
    suffix: str,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Resolve an output filename for a rendered result.

Centralises the ``target_name``/``overwrite`` logic that most methods repeat: use
``stem + suffix`` when no name is given, otherwise honour the provided ``target_name`` but
enforce the extension from ``suffix``; when ``overwrite`` is False, auto-increment the name so
nothing is clobbered.

#### Arguments

- `stem` *str* - Input filename stem (e.g. ``self.of``), used when ``target_name`` is None.
- `suffix` *str* - Suffix incl. extension to append to ``stem`` (e.g. ``'_grid.png'``); its
    extension is also the one enforced on a provided ``target_name``.
- `target_name` *str, optional* - Explicit output path (its extension is normalised to the
    ``suffix`` extension). Defaults to None.
- `overwrite` *bool, optional* - If False, auto-increment to avoid overwriting. Defaults to True.

#### Returns

- `str` - The resolved output path.

## rotate_video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L880)

```python
def rotate_video(
    filename: str,
    angle: float,
    target_name: str | None = None,
    overwrite: bool = True,
) -> str:
```

Rotates a video by an `angle` using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `angle` *float* - The angle (in degrees) specifying the amount of rotation. Positive values rotate clockwise.
- `target_name` *str, optional* - Target filename as path. Defaults to None (which assumes that the input filename with the suffix "_rot" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - The path to the rotated video file.

## roundup

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L363)

```python
def roundup(num: int, modulo_num: int) -> int:
```

Rounds up a number to the next integer multiple of another.

#### Arguments

- `num` *int* - The number to round up.
- `modulo_num` *int* - The number whose next integer multiple we want.

#### Returns

- `int` - The rounded-up number.

## scale_array

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L411)

```python
def scale_array(
    array: np.ndarray,
    out_low: float,
    out_high: float,
) -> np.ndarray:
```

Scales an array linearly.

#### Arguments

- `array` *arraylike* - The array to be scaled.
- `out_low` *float* - Minimum of output range.
- `out_high` *float* - Maximum of output range.

#### Returns

- `arraylike` - The scaled array.

## scale_num

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L393)

```python
def scale_num(
    val: float,
    in_low: float,
    in_high: float,
    out_low: float,
    out_high: float,
) -> float:
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

## show_progress

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L15)

```python
def show_progress(enabled: bool) -> None:
```

Enable or disable the MGT progress bars globally.

Disabling the progress bars is useful when running batch processing jobs or
when the output is captured by a logging framework where the repeated
``\r`` updates would clutter the log.

#### Arguments

- `enabled` *bool* - Pass ``True`` to show progress bars (default behaviour)
    or ``False`` to suppress them.

#### Examples

```python
>>> import musicalgestures as mg
>>> mg.show_progress(False)  # suppress all progress bars
>>> # … batch processing …
>>> mg.show_progress(True)   # re-enable for interactive use

## str2sec

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1807)

```python
def str2sec(time_string: str) -> float:
```

Converts a time code string into seconds.

#### Arguments

- `time_string` *str* - The time code to convert. Eg. '01:33:42'.

#### Returns

- `float` - The time code converted to seconds.

## threshold_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L979)

```python
def threshold_ffmpeg(
    filename: str,
    threshold: float = 0.1,
    target_name: str | None = None,
    binary: bool = False,
    overwrite: bool = True,
) -> str:
```

Renders a pixel-thresholded video from the input using ffmpeg.

#### Arguments

- `filename` *str* - Path to the input video file.
- `threshold` *float, optional* - The normalized pixel value to use as the threshold. Pixels below the threshold will turn black. Defaults to 0.1.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_thresh" should be used).
- `binary` *bool, optional* - If True, the pixels above the threshold will turn white. Defaults to False.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `str` - Path to the output video.

## unwrap_str

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1842)

```python
def unwrap_str(string: str) -> str:
```

Unwraps a string from quotes.

#### Arguments

- `string` *str* - The string to inspect.

#### Returns

- `str` - The (unwrapped) string.

## wrap_str

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_utils.py#L1821)

```python
def wrap_str(string: str, matchers: list = [' ', '(', ')']) -> str:
```

Wraps a string in double quotes if it contains any of `matchers` - by default: space or parentheses.
Useful when working with shell commands.

#### Arguments

- `string` *str* - The string to inspect.
- `matchers` *list, optional* - The list of characters to look for in the string. Defaults to [" ", "(", ")"].

#### Returns

- `str` - The (wrapped) string.

# Videoreader

> Auto-generated documentation for [musicalgestures._videoreader](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoreader.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Videoreader
    - [ReadError](#readerror)
    - [mg_videoreader](#mg_videoreader)

## ReadError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoreader.py#L9)

```python
class ReadError(Exception):
```

Base class for file read errors.

## mg_videoreader

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videoreader.py#L14)

```python
def mg_videoreader(
    filename,
    starttime=0,
    endtime=0,
    skip=0,
    frames=0,
    rotate=0,
    contrast=0,
    brightness=0,
    crop='None',
    color=True,
    keep_all=False,
    returned_by_process=False,
):
```

Reads in a video file, and optionally apply several different processes on it. These include:
- trimming,
- skipping,
- fixing,
- rotating,
- applying brightness and contrast,
- cropping,
- converting to grayscale.

#### Arguments

- `filename` *str* - Path to the input video file.
- `starttime` *int/float, optional* - Trims the video from this start time (s). Defaults to 0.
- `endtime` *int/float, optional* - Trims the video until this end time (s). Defaults to 0 (which will make the algorithm use the full length of the input video instead).
- `skip` *int, optional* - Time-shrinks the video by skipping (discarding) every n frames determined by `skip`. Defaults to 0.
- `frames` *int, optional* - Specify a fixed target number of frames to extract from the video. Defaults to 0.
- `rotate` *int/float, optional* - Rotates the video by a `rotate` degrees. Defaults to 0.
- `contrast` *int/float, optional* - Applies +/- 100 contrast to video. Defaults to 0.
- `brightness` *int/float, optional* - Applies +/- 100 brightness to video. Defaults to 0.
- `crop` *str, optional* - If 'manual', opens a window displaying the first frame of the input video file, where the user can draw a rectangle to which cropping is applied. If 'auto' the cropping function attempts to determine the area of significant motion and applies the cropping to that area. Defaults to 'None'.
- `color` *bool, optional* - If False, converts the video to grayscale and sets every method in grayscale mode. Defaults to True.
- `keep_all` *bool, optional* - If True, preserves an output video file after each used preprocessing stage. Defaults to False.
- `returned_by_process` *bool, optional* - This parameter is only for internal use, do not use it. Defaults to False.

#### Returns

- `int` - The number of frames in the output video file.
- `int` - The pixel width of the output video file.
- `int` - The pixel height of the output video file.
- `int` - The FPS (frames per second) of the output video file.
- `float` - The length of the output video file in seconds.
- `str` - The path to the output video file without its extension. The file name gets a suffix for each used process.
- `str` - The file extension of the output video file.
- `bool` - Whether the video has an audio track.

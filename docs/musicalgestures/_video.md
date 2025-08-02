# Video

> Auto-generated documentation for [musicalgestures._video](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Video
    - [MgVideo](#mgvideo)
        - [MgVideo().average](#mgvideoaverage)
        - [MgVideo().extract_frame](#mgvideoextract_frame)
        - [MgVideo().from_numpy](#mgvideofrom_numpy)
        - [MgVideo().get_video](#mgvideoget_video)
        - [MgVideo().numpy](#mgvideonumpy)
        - [MgVideo().test_input](#mgvideotest_input)

## MgVideo

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L19)

```python
class MgVideo(MgAudio):
    def __init__(
        filename: str | list[str],
        array=None,
        fps=None,
        path=None,
        filtertype='Regular',
        thresh=0.05,
        starttime=0,
        endtime=0,
        blur='None',
        skip=0,
        frames=0,
        rotate=0,
        color=True,
        contrast=0,
        brightness=0,
        crop='None',
        keep_all=False,
        returned_by_process=False,
        sr=22050,
        n_fft=2048,
        hop_length=512,
    ):
```

This is the class for working with video files in the Musical Gestures Toolbox. It inherites from the class MgAudio for working with audio files as well.
There is a set of preprocessing tools you can use when you load a video, such as:
- trimming: to extract a section of the video,
- skipping: to shrink the video by skipping N frames after keeping one,
- rotating: to rotate the video by N degrees,
- applying brightness and contrast
- cropping: to crop the video either automatically (by assessing the area of motion) or manually with a pop-up user interface,
- converting to grayscale

These preprocesses will apply upon creating the MgVideo. Further processes are available as class methods.

#### See also

- [MgAudio](_audio.md#mgaudio)

### MgVideo().average

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L161)

```python
def average(**kwargs):
```

Backward compatibility alias for blend(component_mode='average').
Creates an average image of all frames in the video.

#### Arguments

- `**kwargs` - Additional arguments passed to blend method.
         - `Note` - 'normalize' parameter is accepted for backward compatibility but ignored.

#### Returns

- `MgImage` - A new MgImage pointing to the output average image file.

### MgVideo().extract_frame

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L329)

```python
def extract_frame(**kwargs):
```

Extracts a frame from the video at a given time.
see _utils.extract_frame for details.

#### Arguments

- `frame` *int* - The frame number to extract.
- `time` *str* - The time in HH:MM:ss.ms where to extract the frame from.
- `target_name` *str, optional* - The name for the output file. If None, the name will be \<input name\>FRAME\<frame number\>.\<file extension\>. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

#### Returns

- `MgImage` - An MgImage object referring to the extracted frame.

### MgVideo().from_numpy

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L289)

```python
def from_numpy(array, fps, target_name=None):
```

### MgVideo().get_video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L193)

```python
def get_video():
```

Creates a video attribute to the Musical Gestures object with the given correct settings.

### MgVideo().numpy

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L276)

```python
def numpy():
```

Pipe all video frames from FFmpeg to numpy array

### MgVideo().test_input

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L178)

```python
def test_input():
```

Gives feedback to user if initialization from input went wrong.

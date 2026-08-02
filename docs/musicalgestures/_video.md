# Video

> Auto-generated documentation for [musicalgestures._video](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Video
    - [MgVideo](#mgvideo)
        - [MgVideo().average](#mgvideoaverage)
        - [MgVideo().duration](#mgvideoduration)
        - [MgVideo().extract_frame](#mgvideoextract_frame)
        - [MgVideo().from_numpy](#mgvideofrom_numpy)
        - [MgVideo().get_video](#mgvideoget_video)
        - [MgVideo().n_frames](#mgvideon_frames)
        - [MgVideo().numpy](#mgvideonumpy)
        - [MgVideo().test_input](#mgvideotest_input)

## MgVideo

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L21)

```python
class MgVideo(MgAudio):
    def __init__(
        filename: Union[str, List[str]],
        array=None,
        fps: float = None,
        path: str = None,
        filtertype: str = 'Regular',
        threshold: float = 0.05,
        starttime: float = 0,
        endtime: float = 0,
        blur: str = 'None',
        skip: int = 0,
        frames: int = 0,
        rotate: float = 0,
        color: bool = True,
        contrast: float = 0,
        brightness: float = 0,
        crop: str = 'None',
        keep_all: bool = False,
        returned_by_process: bool = False,
        sr: int = 22050,
        n_fft: int = 2048,
        hop_length: int = 512,
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

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L214)

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

### MgVideo().duration

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L205)

```python
@property
def duration() -> float:
```

Video duration in **seconds** (``length / fps``).

Note ``self.length`` is the frame *count* for an MgVideo (it is the duration in
seconds for an MgAudio); use this property when you want seconds.

### MgVideo().extract_frame

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L414)

```python
def extract_frame(**kwargs):
```

Extracts a frame from the video at a given time.
see _utils.extract_frame for details.

#### Arguments

- `frame` *int* - The frame number to extract.
- `time` *str* - The time in HH:MM:ss.ms where to extract the frame from.
- `target_name` *str, optional* - The name for the output file. If None, the name will be <input name>FRAME<frame number>.<file extension>. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

#### Returns

- `MgImage` - An MgImage object referring to the extracted frame.

### MgVideo().from_numpy

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L359)

```python
def from_numpy(
    array: np.ndarray,
    fps: float,
    target_name: str | None = None,
) -> None:
```

Writes a numpy array of video frames to a video file using FFmpeg.

After writing, updates ``self.filename``, ``self.of``, and ``self.fex`` to
reflect the actual output path so that subsequent operations on this object
refer to the newly created file.

#### Arguments

- `array` *np.ndarray* - Video frames array with shape (N, H, W, 3) in BGR format.
- `fps` *float* - Frames per second for the output video.
- `target_name` *str, optional* - Full path for the output file. If None, uses
    ``self.path/self.filename`` (or just ``self.filename`` if path is None).
    Defaults to None.

### MgVideo().get_video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L246)

```python
def get_video():
```

Creates a video attribute to the Musical Gestures object with the given correct settings.

NB: For an [MgVideo](#mgvideo), ``self.length`` is the number of **frames** (from
``get_framecount``), whereas for ``MgAudio`` ``self.length`` is the duration in
**seconds**. To get the video duration in seconds use ``self.length / self.fps``.

### MgVideo().n_frames

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L200)

```python
@property
def n_frames() -> int:
```

Number of frames in the video (an alias for the frame-count ``length``).

### MgVideo().numpy

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L340)

```python
def numpy():
```

Read all video frames into a numpy array using FFmpeg.

#### Returns

- `tuple` - A tuple ``(array, fps)`` where ``array`` is a ``numpy.ndarray``
    of shape ``(N, H, W, 3)`` in BGR format (uint8) containing all N
    frames, and ``fps`` is the frame rate of the video.

### MgVideo().test_input

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_video.py#L231)

```python
def test_input():
```

Gives feedback to user if initialisation from input went wrong.

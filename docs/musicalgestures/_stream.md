# Stream

> Auto-generated documentation for [musicalgestures._stream](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_stream.py) module.

Streaming video reader for MGT-python.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Stream
    - [MgVideoReader](#mgvideoreader)
        - [MgVideoReader().\_\_iter\_\_](#mgvideoreader__iter__)
        - [MgVideoReader().fps](#mgvideoreaderfps)
        - [MgVideoReader().height](#mgvideoreaderheight)
        - [MgVideoReader().width](#mgvideoreaderwidth)

class `MgVideoReader` is a context-manager-based iterator that yields video
frames lazily using FFmpeg pipes.  This avoids loading an entire video into
RAM, making it suitable for long recordings.

Examples
--------

```python
>>> from musicalgestures._stream import MgVideoReader
>>> with MgVideoReader("dancer.avi") as reader:
...     for i, (frame, ts) in enumerate(reader):
...         # frame: np.ndarray, shape (H, W, 3), dtype uint8
...         # ts:    float, timestamp in seconds
...         if i >= 5:
...             break

## MgVideoReader

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_stream.py#L46)

```python
class MgVideoReader():
    def __init__(
        filename: str | Path,
        start: float = 0.0,
        end: float | None = None,
        grayscale: bool = False,
        scale: float = 1.0,
        batch_size: int = 1,
    ) -> None:
```

Context-manager that streams frames from a video file via FFmpeg.

Parameters
----------
filename:
    Path to the video file to read.
start:
    Start time in seconds. Defaults to 0.
end:
    End time in seconds. Defaults to *None* (read to end of file).
grayscale:
    If *True*, convert frames to grayscale before yielding.
    Default: False.
scale:
    Downscale factor (e.g. 0.5 → half resolution). Default: 1.0.
batch_size:
    Number of frames to read per FFmpeg read call.  Larger values
    reduce subprocess overhead at the cost of more memory.
    Default: 1.

Yields
------
frame : np.ndarray
    Video frame as a NumPy array, shape ``(H, W, 3)`` (BGR) or
    ``(H, W)`` if *grayscale=True*.
timestamp : float
    Approximate frame timestamp in seconds.

Examples
--------

```python
>>> import numpy as np
>>> # Collect every frame as a numpy array:
>>> frames = []
>>> with MgVideoReader("dancer.avi") as reader:
...     for frame, ts in reader:
...         frames.append(frame)
>>> arr = np.stack(frames)  # shape (N, H, W, 3)

### MgVideoReader().\_\_iter\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_stream.py#L167)

```python
def __iter__() -> Generator[tuple[np.ndarray, float], None, None]:
```

Yield ``(frame, timestamp)`` pairs.

### MgVideoReader().fps

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_stream.py#L205)

```python
@property
def fps() -> float:
```

Frames per second of the source video.

### MgVideoReader().height

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_stream.py#L200)

```python
@property
def height() -> int:
```

Frame height in pixels (after optional scaling).

### MgVideoReader().width

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_stream.py#L195)

```python
@property
def width() -> int:
```

Frame width in pixels (after optional scaling).

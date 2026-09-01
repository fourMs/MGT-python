# Loading and Showing Videos

The `MgVideo` class is the entry point for working with video files: it holds a reference to the file, applies preprocessing at load time, and exposes all analysis methods. This page is a task reference; the topic is taught in course form in [chapter 2 of the wiki](https://github.com/fourMs/MGT-python/wiki/2-%E2%80%90-Loading-and-showing-videos).

## Loading

```python
import musicalgestures as mg

mv = mg.MgVideo('/path/to/video.mp4')
```

Returns an `MgVideo` object. Most common formats are accepted (MP4, AVI, MOV, MKV, etc.); see [Preprocessing](preprocessing.md) for the options you can apply at load time.

## Showing

```python
mv.show()                   # opens in a separate window (default)
mv.show(mode='notebook')    # embeds inline in a Jupyter notebook
mv.show(key='motion')       # shows a previously computed result
```

In notebook environments (Jupyter, Colab), notebook mode is always used, and non-browser-compatible formats are converted to MP4 automatically. The `key` parameter shows the latest rendering of a result attached to the source `MgVideo`.

Supported key values:

| Key | Result shown |
|---|---|
| `'motion'` | Motion video |
| `'history'` | History video |
| `'motionhistory'` | Motion history video (chained) |
| `'horizontal'` | Horizontal-movement motiongram/videogram |
| `'vertical'` | Vertical-movement motiongram/videogram |
| `'mgh'` / `'vgh'` | Horizontal motiongram / videogram (alias of `'horizontal'`) |
| `'mgv'` / `'vgv'` | Vertical motiongram / videogram (alias of `'vertical'`) |
| `'mgx'` / `'mgy'` | Literal x / y motiongram file (legacy) |
| `'vgx'` / `'vgy'` | Literal x / y videogram file (legacy) |
| `'ssm'` | Self-similarity matrix |
| `'blend'` | Blended image |
| `'plot'` | Motion plot image |
| `'sparse'` | Sparse optical flow video |
| `'dense'` | Dense optical flow video |
| `'pose'` | Pose estimation video |
| `'warp'` | Warped audiovisual beats video |
| `'subtract'` | Background-subtracted video |
| `'blur'` | Face-anonymised video |

The orientation keys select by direction of movement; the legacy `'mgx'`/`'mgy'`/`'vgx'`/`'vgy'` keys resolve to the literal x/y files.

## Getting video metadata

```python
mv.info()                           # prints all metadata (video + audio + format)
mv.info('video')                    # one section only ('audio' and 'format' likewise)
summary = mv.info('summary')        # human-readable overview, returned as a dict
mv.info('frame')                    # renders a plot of I/P/B frame types
mv.info('frame', autoshow=False)    # returns the frame-type dataframe without plotting
```

`info('summary')` prints resolution, frame count, fps, colour mode, codecs and file size, and returns the values as a dict (keys such as `fps` and `video_codec`). The summary's `duration` field is derived from `mv.length`, which is the frame count; use `mv.duration` for the duration in seconds.

## Key properties

```python
mv.filename     # full file path
mv.width        # frame width in pixels
mv.height       # frame height in pixels
mv.length       # frame count (use mv.n_frames as a clearer alias)
mv.duration     # duration in seconds
mv.fps          # frame rate
mv.color        # True for colour, False for grayscale
```

## The frame rate, and what it costs to be wrong about it

Almost every number MGT produces from a video is a rate or a frequency, and every one of them is the frame rate multiplied or divided by something. A wrong frame rate does not produce an error or an implausible figure—it rescales the answer linearly and leaves it looking entirely normal. Take the rate from the file rather than typing it:

```python
mv = mg.MgVideo('/path/to/video.mp4')
freq = mg.dominant_frequency(signal, mv.fps, fmin=0.2, fmax=8.0)   # not fps=25
```

### Where the number comes from

There are three sources and they do not consult each other.

| Source | Used by | What it is |
|---|---|---|
| `get_fps(filename)` | `mv.fps`, and everything reading it | the rate ffprobe prints in its banner, which is the container's declared average, rounded as printed (`29.97`, not `30000/1001`) |
| `cv2.CAP_PROP_FPS` | the analyses that open their own `VideoCapture` | OpenCV's reading of the same container, at full precision (`29.970029970…`) |
| the `fps` argument | every function in the list below | whatever the caller passed |

The first two normally agree to within the rounding. The third is not checked against anything.

### Functions that take a frame rate

These take an `fps` value and use it to build a time or a frequency axis, so the value goes straight into the result: `dominant_frequency`, `_qom_spectrum`, `impact_detection`, `impact_events`, `limb_speed_from_landmarks`, `_per_marker_stats`, `_ideal_bandpass` (Eulerian magnification), `Flow.get_acceleration`, `frame2ms`, `extract_pose_landmarks(fps=...)` and `MgVideo.from_numpy`. None of them can tell whether the number matches the file, because most of them never see the file. On a 29.97 fps clip, passing 25 scales every reported frequency down by 16.6 %, and passing 15 halves it; the resulting figures still look publishable.

!!! note "Fractional frame rates are kept exact"
    Every analysis reads the frame rate as a float, so NTSC-rate footage at 29.97 fps
    keeps its true rate in every derived time, frequency and output file. A guard test
    in `tests/test_average.py` fails if any module ever reads the rate through `int()`.
    Figures made with a truncated rate are about 3.2 % off on such footage and should
    not be mixed with exact ones.

### Checking a file's rate against its own contents

`get_framecount` counts demuxed packets, or fully decoded frames with `fast=False`, rather than trusting the container's `nb_frames`; `get_length` reads the duration:

```python
from musicalgestures import get_fps, get_framecount, get_length

fps, frames, seconds = get_fps(f), get_framecount(f), get_length(f)
print(fps, frames / seconds)        # these should agree
```

A disagreement means the container is describing a stream it does not contain, which happens with variable-frame-rate phone captures and with remuxed files. Agreement is not proof, though: the count and the duration are often derived from the declared rate, so a self-consistently wrong file passes. Distinguishing a padded rate means decoding and comparing consecutive frames; the reasoning is taught in [chapter 1 of the wiki](https://github.com/fourMs/MGT-python/wiki/1-%E2%80%90-Video-Basics).

## Further

- Course: [chapter 2 of the wiki](https://github.com/fourMs/MGT-python/wiki/2-%E2%80%90-Loading-and-showing-videos)
- [Preprocessing](preprocessing.md)—trim, crop, rotate, and adjust before analysis
- [Video Analysis](video-analysis.md)—motion, optical flow, pose, and more
- [Working with Results](results.md)—MgFigure, MgImage, MgList, and method chaining
- API: [_video](../musicalgestures/_video.md), [_show](../musicalgestures/_show.md), [_info](../musicalgestures/_info.md), [_utils](../musicalgestures/_utils.md) (get_fps, get_framecount, get_length)

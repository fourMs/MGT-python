# Loading and Showing Videos

The `MgVideo` class is the main entry point for working with video files. It holds a reference to the file, applies preprocessing, and exposes all analysis methods.

## Loading

Pass the path to your video file to create an `MgVideo`:

```python
import musicalgestures as mg

mv = mg.MgVideo('/path/to/video.mp4')
```

`MgVideo` accepts most common video formats (MP4, AVI, MOV, MKV, etc.). See [Preprocessing](preprocessing.md) for options you can apply at load time.

## Showing

Call `show()` on any `MgVideo` to display it:

```python
mv = mg.MgVideo('/path/to/video.mp4')
mv.show()                   # opens in a separate window (default)
mv.show(mode='notebook')    # embeds inline in a Jupyter notebook
```

In notebook mode, `show()` converts the video to MP4 automatically if the format is not browser-compatible. In notebook environments (Jupyter, Colab), notebook mode is always used regardless of the `mode` argument.

### Referencing results by key

After running a process on a video, the result is attached to the source `MgVideo`. The `key` parameter on `show()` lets you display a previously computed result without keeping a reference to the return value:

```python
mv = mg.MgVideo('/path/to/video.mp4')
mv.motionvideo()
mv.flow.dense()

mv.show(key='motion')   # shows the motion video
mv.show(key='dense')    # shows the dense optical flow video

mv.motionvideo(threshold=0.15)
mv.show(key='motion')   # shows the newly rendered motion video
```

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

The orientation keys select by *direction of movement*: `'horizontal'` (with aliases `'mgh'`/`'vgh'`) shows the horizontal-movement gram and `'vertical'` (aliases `'mgv'`/`'vgv'`) the vertical one. The legacy `'mgx'`/`'mgy'`/`'vgx'`/`'vgy'` keys still resolve to the literal x/y files.

## Getting video metadata

`info()` returns technical metadata about the file:

```python
mv = mg.MgVideo('/path/to/video.avi')
mv.info()           # prints all metadata (video + audio + format)
mv.info('video')    # video stream metadata only
mv.info('audio')    # audio stream metadata only
mv.info('format')   # container/format metadata only
```

For a quick human-readable overview, use `info('summary')`, which prints resolution, frame count, fps, colour mode, video codec/profile, colour profile, and audio codec/sample-rate/bit-rate, and returns the values as a dict:

```python
summary = mv.info('summary')
# File:         video.avi
# Resolution:   1920 × 1080 px
# Frames:       750  @  25 fps
# Color:        color
# Video codec:  h264 (High)
# Audio:        aac (48,000 Hz, 192 kbps)
# File size:    42.3 MB
print(summary['fps'], summary['video_codec'])
```

Note that the summary's `duration` field is derived from `mv.length`, which for `MgVideo` is the frame count; use `mv.duration` for the duration in seconds.

### I/P/B frame types

To inspect the compression frame types in the video:

```python
mv.info('frame')                    # renders a plot of I/P/B frame distribution
mv.info('frame', autoshow=False)    # returns the dataframe without plotting
```

## Key properties

```python
mv = mg.MgVideo('/path/to/video.mp4')

mv.filename     # full file path
mv.width        # frame width in pixels
mv.height       # frame height in pixels
mv.length       # frame count (use mv.n_frames as a clearer alias)
mv.duration     # duration in seconds
mv.fps          # frame rate
mv.color        # True for colour, False for grayscale
```

## The frame rate, and what it costs to be wrong about it

Almost every number MGT produces from a video is a rate or a frequency, and every one of them is
the frame rate multiplied or divided by something. A wrong frame rate does not produce an error or
an implausible figure — it rescales the answer linearly and leaves it looking entirely normal.

### Where the number comes from

There are three sources and they do not consult each other.

| Source | Used by | What it is |
|---|---|---|
| `get_fps(filename)` | `mv.fps`, and everything reading it | the rate ffprobe prints in its banner, which is the container's declared average, rounded as printed — `29.97`, not `30000/1001` |
| `cv2.CAP_PROP_FPS` | the analyses that open their own `VideoCapture` | OpenCV's reading of the same container, at full precision — `29.970029970…` |
| the `fps` argument | every function in the table below | whatever the caller passed |

The first two normally agree to within the rounding. The third is not checked against anything.

### Passing a frame rate

These take one and use it to build a time or a frequency axis, so the value goes straight into the
result: `dominant_frequency`, `_qom_spectrum`, `impact_detection`, `impact_events`,
`limb_speed_from_landmarks`, `_per_marker_stats`, `_ideal_bandpass` (Eulerian magnification),
`Flow.get_acceleration`, `frame2ms`, `extract_pose_landmarks(fps=...)` and `MgVideo.from_numpy`.
None of them can tell whether the number matches the file, because most of them never see the file.

Measured on a 30-second 29.97 fps clip whose brightness pulses at a known rate, so the
quantity-of-motion signal has a true dominant frequency of 2.00 Hz:

| what was passed as `fps` | reported dominant frequency | error |
|---|---|---|
| `cv2.CAP_PROP_FPS`, 29.970030 | 2.0002 Hz (120.0 BPM) | +0.01 % |
| `get_fps`, 29.97 | 2.0002 Hz (120.0 BPM) | +0.01 % |
| `int(cv2.CAP_PROP_FPS)`, 29 | 1.9355 Hz (116.1 BPM) | −3.23 % |
| 25 | 1.6685 Hz (100.1 BPM) | −16.6 % |
| 20 | 1.3348 Hz (80.1 BPM) | −33.3 % |
| 15 | 1.0011 Hz (60.1 BPM) | −49.9 % |

Every one of those is a publishable-looking movement tempo. The bottom two rows are not
hypothetical: two analysis scripts in a standstill study held the frame rate as a constant, 20 in
one and 15 in the other, against video that was 25 throughout, and nothing in either run announced
it.

Take the rate from the file rather than typing it:

```python
mv = mg.MgVideo('/path/to/video.mp4')
freq = mg.dominant_frequency(signal, mv.fps, fmin=0.2, fmax=8.0)   # not fps=25
```

!!! note "Seven analyses used to truncate the rate to an integer — fixed 2026-08-22"
    `_directograms`, `_flow` (both call sites), `_history`, `_impacts`, `_warp` and
    `_videoadjust` read the rate as `int(cv2.CAP_PROP_FPS)`. On any NTSC-rate source that was
    `int(29.97) == 29`, so every time and frequency they derived was 3.2 % low, and in `_flow`
    and `_history` the truncated value was written into the output file's declared rate, so a
    29.97 fps input came back out as a 29 fps file. All seven now keep the true rate.

    Figures produced by those modules BEFORE this fix are rate-approximate on non-integer-rate
    footage and are not comparable with figures produced after it. A guard test in
    `tests/test_average.py` fails if any module reads the rate through `int()` again.

### Checking a file's rate against its own contents

Nothing in MGT does this, and the pieces for it are all here. `get_framecount` counts demuxed
packets, or fully decoded frames with `fast=False`, rather than trusting the container's
`nb_frames`; `get_length` reads the duration:

```python
from musicalgestures import get_fps, get_framecount, get_length

fps, frames, seconds = get_fps(f), get_framecount(f), get_length(f)
print(fps, frames / seconds)        # these should agree
```

A disagreement means the container is describing a stream it does not contain, which happens with
variable-frame-rate phone captures and with files that have been remuxed.

!!! note "Agreement here is not proof"
    The frame count and the duration are often derived from the declared rate, so a file whose
    rate is wrong in a self-consistent way passes this check. A clip encoded at 25 fps from a
    source that only changed five times a second reports 500 frames over 20 seconds and a rate of
    exactly 25.000 — and four fifths of its frames are repeats. The header is not evidence about
    the contents. Distinguishing the two means decoding and comparing consecutive frames, which
    is cheap: 500 frames of 320×240 took 0.08 s.

## Next steps

- [Preprocessing](preprocessing.md)—trim, crop, rotate, and adjust before analysis
- [Video Analysis](video-analysis.md)—motion, optical flow, pose, and more
- [Working with Results](results.md)—MgFigure, MgImage, MgList, and method chaining

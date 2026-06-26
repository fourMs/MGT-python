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

In notebook mode, `show()` converts the video to MP4 automatically if the format is not browser-compatible. In Google Colab, notebook mode is always used regardless of the `mode` argument.

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
| `'mgx'` | Horizontal motiongram |
| `'mgy'` | Vertical motiongram |
| `'vgx'` | Horizontal videogram |
| `'vgy'` | Vertical videogram |
| `'ssm'` | Self-similarity matrix |
| `'blend'` | Blended image |
| `'plot'` | Motion plot image |
| `'sparse'` | Sparse optical flow video |
| `'dense'` | Dense optical flow video |
| `'pose'` | Pose estimation video |
| `'warp'` | Warped audiovisual beats video |
| `'blur'` | Face-anonymized video |
| `'subtract'` | Background-subtracted video |

## Getting video metadata

`info()` returns technical metadata about the file:

```python
mv = mg.MgVideo('/path/to/video.avi')
mv.info()           # prints all metadata (video + audio + format)
mv.info('video')    # video stream metadata only
mv.info('audio')    # audio stream metadata only
mv.info('format')   # container/format metadata only
```

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
mv.length       # duration in seconds
mv.fps          # frame rate
mv.framecount   # total number of frames
mv.color        # True for colour, False for grayscale
```

## Next steps

- [Preprocessing](preprocessing.md) — trim, crop, rotate, and adjust before analysis
- [Video Analysis](video-analysis.md) — motion, optical flow, pose, and more
- [Working with Results](results.md) — MgFigure, MgImage, MgList, and method chaining

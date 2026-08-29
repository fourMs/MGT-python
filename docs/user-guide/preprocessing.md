# Preprocessing

All preprocessing is applied at load time by passing arguments to `MgVideo`. Steps execute in a fixed order: trim → skip → fix → rotate → contrast/brightness → crop → grayscale.

```python
import musicalgestures as mg

mv = mg.MgVideo(
    '/path/to/video.avi',
    starttime=5,
    endtime=15,
    skip=3,
    rotate=90,
    contrast=100,
    brightness=20,
    crop='auto',
    color=False,
)
```

## Trimming

Use `starttime` and `endtime` (in seconds) to work on a portion of the video:

```python
mv = mg.MgVideo('/path/to/video.avi', starttime=5, endtime=15)
```

## Frame skipping

`skip=n` keeps every (n+1)th frame, reducing processing time:

```python
mv = mg.MgVideo('/path/to/video.avi', skip=2)
```

## Fixing a frame count

`frames` extracts a fixed number of frames, useful for batch processing files of different lengths:

```python
mv = mg.MgVideo('/path/to/video.avi', frames=1000)
mv = mg.MgVideo('/path/to/video.avi', frames=-1)    # keyframes only
```

## Rotation

`rotate` accepts any angle in degrees:

```python
mv = mg.MgVideo('/path/to/video.avi', rotate=90)
mv = mg.MgVideo('/path/to/video.avi', rotate=5.31)
```

## Contrast and brightness

Both parameters are percentages in the range −100 to 100. A value of 0 leaves the video unchanged:

```python
mv = mg.MgVideo('/path/to/video.avi', contrast=100, brightness=20)
```

## Cropping

`crop='auto'` detects the region of motion and crops to it. `crop='manual'` opens a window where you draw the crop rectangle, then press `c` to confirm or `r` to reset:

```python
mv = mg.MgVideo('/path/to/video.avi', crop='auto')
mv = mg.MgVideo('/path/to/video.avi', crop='manual')
```

## Grayscale

`color=False` converts the video to grayscale and keeps all subsequent processes in grayscale mode, which can reduce processing time:

```python
mv = mg.MgVideo('/path/to/video.avi', color=False)
```

## Resampling (frame rate, speed, frame decimation)

Unlike the options above, `resample()` is a method called on an already-loaded `MgVideo`. It returns a new `MgVideo` and leaves the original object untouched, so you can branch off a re-timed copy:

```python
mv = mg.MgVideo('/path/to/video.avi')

mv25 = mv.resample(fps=25)         # retime to 25 fps (duration-preserving)
fast = mv.resample(speed=2.0)      # play 2× faster (video + audio retimed in sync)
slow = mv.resample(speed=0.5)      # play 2× slower / longer
dec  = mv.resample(skip=2)         # discard 2 frames for every one kept
mv25.show()
```

Three independent, combinable operations:

- `fps`: retime to a target frame rate via FFmpeg's `fps` filter, duration-preserving (frames are dropped/duplicated to hit the rate), e.g. 30 → 25 fps.
- `speed`: change playback speed by a factor (`>1` faster/shorter, `<1` slower/longer); the video (`setpts`) and the audio (`atempo`) are retimed together so they stay in sync.
- `skip`: integer frame decimation, discarding `skip` frames for every one kept (this also shortens/speeds up the clip), matching the loader's `skip` parameter.

When more than one is given they are applied in order: `skip` → `speed`/`fps`. The output filename defaults to the input name with a `_resampled` suffix; `target_name` and `overwrite` work as for the other methods.

## Keeping intermediate files

By default only the final preprocessed video is kept. Set `keep_all=True` to retain the result of each step:

```python
mv = mg.MgVideo('/path/to/video.avi', starttime=5, endtime=15, skip=3,
                rotate=90, contrast=100, brightness=20, crop='auto',
                color=False, keep_all=True)
```

This produces files like `video_trim.avi`, `video_trim_skip.avi`, `video_trim_skip_rot.avi`, and so on.

## Output file names and overwriting

Every analysis method accepts `target_name` and `overwrite`:

- `target_name` sets the output file path. If `None` (default), a suffix is appended to the source name. For example, `history` on `dance.avi` produces `dance_history.avi` in the same directory.
- `overwrite=True` (default) replaces the existing file in place, so re-running a method overwrites the previous result instead of leaving stale copies behind.
- `overwrite=False` silently increments the filename if one already exists: `dance_history.avi` → `dance_history_0.avi` → `dance_history_1.avi`, and so on, keeping every run.

```python
mv = mg.MgVideo('/path/to/video.avi')
mv.history(target_name='/output/my_history.avi', overwrite=False)   # keep every run
```

## Next steps

- [Video Analysis](video-analysis.md)—run motion analysis, optical flow, and more
- [Loading & Showing](loading.md)—how to load and display results

# Preprocessing

All preprocessing is applied at load time by passing arguments to `MgVideo`. Steps execute in a fixed order: trim → skip → fix → rotate → contrast/brightness → crop → grayscale. This page is a task reference; the topic is taught in course form in [chapter 3 of the wiki](https://github.com/fourMs/MGT-python/wiki/3-%E2%80%90-Preprocessing).

## Trim, skip, rotate, adjust

```python
import musicalgestures as mg

mv = mg.MgVideo('/path/to/video.avi', starttime=5, endtime=15, skip=3,
                rotate=90, contrast=100, brightness=20)
```

`starttime` and `endtime` are in seconds; `skip=n` keeps every (n+1)th frame; `rotate` accepts any angle in degrees (including fractional values such as `5.31`); `contrast` and `brightness` are percentages in the range −100 to 100, where 0 leaves the video unchanged.

## Crop and grayscale

```python
mv = mg.MgVideo('/path/to/video.avi', crop='auto')      # crop to the region of motion
mv = mg.MgVideo('/path/to/video.avi', crop='manual')    # draw the rectangle yourself
mv = mg.MgVideo('/path/to/video.avi', color=False)      # grayscale mode
```

`crop='manual'` opens a window where you draw the crop rectangle, then press `c` to confirm or `r` to reset. `color=False` keeps all subsequent processes in grayscale mode, which can reduce processing time.

## Fix a frame count

```python
mv = mg.MgVideo('/path/to/video.avi', frames=1000)
mv = mg.MgVideo('/path/to/video.avi', frames=-1)    # keyframes only
```

Extracts a fixed number of frames, useful for batch processing files of different lengths.

## Resample (frame rate, speed, frame decimation)

```python
mv25 = mv.resample(fps=25)         # retime to 25 fps (duration-preserving)
fast = mv.resample(speed=2.0)      # play 2× faster (video + audio retimed in sync)
dec  = mv.resample(skip=2)         # discard 2 frames for every one kept
```

`resample()` returns a new `MgVideo` and leaves the original untouched. When operations are combined they apply in order `skip` → `speed`/`fps`; the output name defaults to the input name with a `_resampled` suffix, and `target_name` and `overwrite` work as for the other methods.

## Keep intermediate files

```python
mv = mg.MgVideo('/path/to/video.avi', starttime=5, endtime=15, skip=3,
                rotate=90, crop='auto', keep_all=True)
```

By default only the final preprocessed video is kept; `keep_all=True` retains each step's result as files like `video_trim.avi`, `video_trim_skip.avi`, `video_trim_skip_rot.avi`, and so on.

## Output file names and overwriting

```python
mv = mg.MgVideo('/path/to/video.avi')
mv.history(target_name='/output/my_history.avi', overwrite=False)   # keep every run
```

Every analysis method accepts these two parameters. `target_name` sets the output path; if `None` (default), a suffix is appended to the source name, so `history` on `dance.avi` produces `dance_history.avi`. `overwrite=True` (default) replaces the existing file in place; `overwrite=False` silently increments the name (`dance_history_0.avi`, `dance_history_1.avi`, …), keeping every run.

## Further

- Course: [chapter 3 of the wiki](https://github.com/fourMs/MGT-python/wiki/3-%E2%80%90-Preprocessing)
- [Loading & Showing](loading.md)—how to load and display results
- [Video Analysis](video-analysis.md)—run motion analysis, optical flow, and more
- API: [_video](../musicalgestures/_video.md), [_cropvideo](../musicalgestures/_cropvideo.md), [_videoadjust](../musicalgestures/_videoadjust.md)

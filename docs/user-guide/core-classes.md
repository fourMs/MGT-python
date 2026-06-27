# Core Classes

MGT-python is built around a small set of classes. `MgVideo` is the main entry point; all other classes are either returned by its methods or used as direct entry points for audio-only work.

## Class hierarchy

```
MgVideo (inherits from MgAudio)
└── MgAudio

Result types (returned by methods, not instantiated directly):
├── MgFigure  — wraps a Matplotlib figure with its data
├── MgImage   — wraps a saved image file
└── MgList    — ordered collection of the above
```

---

## MgVideo

`MgVideo` points to a video file, applies optional preprocessing, and exposes all analysis methods.

```python
import musicalgestures as mg

mg.MgVideo(
    filename,             # str — path to video file
    array=None,           # np.ndarray — load from array instead of file
    fps=None,             # float — override detected frame rate
    path=None,            # str — output directory
    filtertype='Regular', # 'Regular', 'Binary', or 'Blob'
    threshold=0.05,       # float 0–1 — motion pixel threshold
    starttime=0,          # float — trim start in seconds
    endtime=0,            # float — trim end in seconds (0 = full video)
    blur='None',          # 'None' or 'Average'
    skip=0,               # int — keep every (skip+1)th frame
    frames=0,             # int — target frame count (0=all, -1=keyframes only)
    rotate=0,             # float — rotation angle in degrees
    color=True,           # bool — False for grayscale
    contrast=0,           # float -100 to 100
    brightness=0,         # float -100 to 100
    crop=None,            # None, 'auto', or 'manual'
    keep_all=False,       # bool — keep intermediate preprocessing files
    target_name=None,     # str — output file name
    overwrite=True,       # bool — overwrite outputs in place (False = auto-increment)
)
```

### Key properties

```python
mv = mg.MgVideo('/path/to/video.mp4')

mv.filename     # full file path
mv.width        # frame width in pixels
mv.height       # frame height in pixels
mv.length       # frame COUNT (number of frames — see the gotcha below)
mv.n_frames     # frame count (clear alias for length)
mv.duration     # duration in SECONDS (length / fps)
mv.fps          # frame rate
mv.framecount   # total number of frames
mv.color        # True for colour, False for grayscale
mv.audio        # MgAudio object for the video's audio track
mv.flow         # Flow object exposing flow.dense() and flow.sparse()
```

`MgVideo` also has an informative `repr`, so printing one tells you everything at a glance:

```python
mv = mg.MgVideo('dance.avi')
print(mv)   # MgVideo('dance.avi', 1572 frames, 25fps, 518x496, audio=True)
```

!!! warning "`length` means different things on `MgVideo` and `MgAudio`"
    `MgVideo.length` is the frame **count**, whereas `MgAudio.length` is the duration in
    **seconds**. To avoid the confusion, prefer the unambiguous members:

    - `.duration` — duration in **seconds** on **both** classes.
    - `.n_frames` — frame **count** (on `MgVideo`).

    ```python
    mv.duration        # seconds        e.g. 62.88
    mv.n_frames        # frame count    e.g. 1572
    mv.audio.duration  # seconds — same units as mv.duration
    ```

---

## MgAudio

`MgAudio` handles audio analysis. It is accessible as `mv.audio` from any `MgVideo`, or can be instantiated directly for audio-only files.

```python
audio = mg.MgAudio('/path/to/audio.mp3')
print(audio)           # MgAudio('audio.mp3', 62.88s, sr=22050)
print(audio.duration)  # duration in seconds (for MgAudio this equals .length)
```

---

## Result types

`MgFigure`, `MgImage`, and `MgList` are returned by analysis methods. You do not normally create them yourself. See [Working with Results](results.md) for how to use them.

### Saving a result to a chosen path

Both `MgImage` and `MgFigure` have a `save(target_name)` method that copies the rendered
result to a path you choose and returns an `MgImage` pointing to it. This is handy for
collecting outputs into a folder without hunting for the auto-named files next to the source
video:

```python
mv = mg.MgVideo('dance.avi')

mv.average().save('out/average.png')        # MgImage.save  → MgImage('out/average.png')
mv.motiontempo().save('out/tempo.png')      # MgFigure.save → MgImage('out/tempo.png')

# save() returns an MgImage, so it chains straight into show()
mv.heatmap().save('out/heatmap.png').show()
```

---

## Next steps

- [Loading & Showing](loading.md) — how to load videos and display results
- [Preprocessing](preprocessing.md) — trim, crop, rotate, and adjust at load time
- [Video Analysis](video-analysis.md) — motion, optical flow, pose estimation, and more
- [Audio Analysis](audio-analysis.md) — waveforms, spectrograms, and audio features
- [Working with Results](results.md) — MgFigure, MgImage, MgList, and chaining
- [API Reference](../musicalgestures/index.md) — complete method documentation

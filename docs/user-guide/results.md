# Working with Results

MGT-python analysis methods return one of three result types: `MgFigure`, `MgImage`, or `MgList`. All three implement `show()` and can be combined into stacked, time-aligned figures.

!!! note "Display happens via `show()`"
    Result objects do **not** auto-render as the last expression of a notebook cell. Call `show()` to display them. This keeps a single, predictable display and avoids duplicate output. (An HTML snippet is still available programmatically via `to_html()` on `MgImage`/`MgFigure`.)

---

## MgFigure

`MgFigure` wraps a Matplotlib figure alongside its data, so you can display, inspect, and reuse it.

```python
import musicalgestures as mg

mv = mg.MgVideo('/path/to/video.avi')
spectrogram = mv.audio.spectrogram()

spectrogram.show()              # display the figure
spectrogram.figure              # the underlying matplotlib.pyplot.Figure object
print(spectrogram)              # MgFigure(figure_type='audio.spectrogram')
print(spectrogram.data.keys()) # dict_keys(['hop_size', 'sr', 'of', 'S', 'length'])
print(spectrogram.image)       # MgImage pointing to the saved PNG
```

`figure_type` identifies what kind of figure it is. `data` holds the raw arrays needed to reconstruct or reuse the figure. `layers` contains any child figures when the `MgFigure` is itself a composition.

---

## MgImage

`MgImage` is a lightweight wrapper around a saved image file.

```python
img = mg.MgImage('path/to/image.png')
img.show()
img.show(mode='notebook')
print(img.filename)   # path/to/image.png
print(img.of)         # path/to/image  (no extension)
print(img.fex)        # .png
```

Methods that return still images—`average()`, `motionplots()`, `grid()`, `motiongrams()[0]`—return `MgImage`.

---

## MgList

`MgList` is an ordered collection of `MgFigure`, `MgImage`, or other `MgList` objects. Many methods return an `MgList` when they produce more than one output.

```python
spectrogram = mv.audio.spectrogram()
tempogram   = mv.audio.tempogram()
my_list = mg.MgList(spectrogram, tempogram)

print(len(my_list))     # 2
print(my_list[1])       # MgFigure(figure_type='audio.tempogram')
my_list.show()          # calls show() on each item in order
```

Standard list operations work as expected:

```python
descriptors = mv.audio.descriptors()
my_list += descriptors              # append a single item
print(len(my_list))                 # 3

combined = my_list + mg.MgList(spectrogram)   # concatenate two MgLists
```

`motiongrams()` and `videograms()` both return `MgList`:

```python
motiongrams = mv.motiongrams()
motiongrams[0].show()   # vertical motiongram
motiongrams[1].show()   # horizontal motiongram
```

---

## Combining figures into a stacked plot

`MgList.as_figure()` stacks its contents into a single time-aligned figure. The first element appears at the top, the last at the bottom.

```python
videograms  = mv.videograms()
spectrogram = mv.audio.spectrogram()
descriptors = mv.audio.descriptors()

everything = videograms + mg.MgList(spectrogram, descriptors)
fig = everything.as_figure(title='My Video Analysis')
fig.show()
```

---

## Custom titles

Every method that produces a figure accepts a `title` argument:

```python
motionplots = mv.motionplots(title='My Video - Motion Plots')
spectrogram = mv.audio.spectrogram(title='My Video - Spectrogram')
tempogram   = mv.audio.tempogram(title='My Video - Tempogram')
```

---

## Results are also kept on the object

Every analysis method returns its result, and it also stores it on the video it
was called on. The stored name says what the result is: `_video` for an
`MgVideo`, `_image` for an `MgImage`, `_figure` for an `MgFigure`, `_audio` for
an `MgAudio`.

```python
mv = mg.MgVideo('/path/to/video.avi')
mv.motion()
mv.motion_video        # the MgVideo the call produced
mv.motion_plot_image   # and the plot it drew along the way
```

One call often stores several results, since a method that renders a motion
video also draws the motiongrams and the plot on its way through.

The attributes are declared on the class, so an editor completes them and a type
checker follows them. They come into existence when the method that produces
them runs, which is what `show(key=...)` checks: `mv.show(key='plot')` finds the
motion plot only if `motionplots()` has been called.

| method | stores |
|---|---|
| `motion()`, `motiongrams()`, `motion_mp()` | `motion_video`, `motion_plot_image`, `motiongram_vertical_image`, `motiongram_horizontal_image`, `ssm_figure` |
| `motionvideo()` | `motion_video` |
| `videograms()` | `videogram_vertical_image`, `videogram_horizontal_image` |
| `history()` | `history_video` |
| `blend()`, and its alias `average()` | `blend_image` |
| `motionhistory()` | `mhi_image` |
| `heatmap()` | `heatmap_image` |
| `stroboscope()` | `stroboscope_image` |
| `spacetime_volume()` | `spacetime_volume_figure` |
| `silhouette_waterfall()` | `silhouette_waterfall_figure` |
| `pixelarray()` | `frameaverage_image` |
| `pixelarray_cv2()` | `frameaverage_cv2_image` |
| `ssm()` | `ssm_figure`, `ssm_combined_image` |
| `pose()` | `pose_video`, `pose_average_image`, `pose_trajectories_image` |
| `pose_waterfall()`, `pose_segments()`, `pose_center()`, `pose_distance()` | `pose_waterfall_figure`, `pose_segments_figure`, `pose_centered_figure`, `pose_distance_figure` |
| `subtract()` | `subtract_video` |
| `blur_faces()` | `blur_faces_video` |
| `eulerian()` | `eulerian_video` |
| `motionvectors()` | `motionvectors_video` |
| `sonomotiongram()` | `sonomotiongram_audio` |
| `motiondescriptors()` | `motiondescriptors_figure` |
| `beat_statistics()` | `movement_beat_statistics_figure` |
| `tempo_similarity()` | `tempo_similarity_figure` |
| `phase_synchrony()`, `structure_comparison()`, `body_audio_coupling()`, `dynamics_coupling()` | `phase_synchrony_figure`, `structure_comparison_figure`, `body_audio_coupling_figure`, `dynamics_coupling_figure` |
| `warp_audiovisual_beats()` | `warp_video` |

### Why the grams are named for what they show

`motiongram_vertical_image` is the gram you get by collapsing the **x** axis, and
`motiongram_horizontal_image` collapses the **y** axis. The older names for these
were `motiongram_x` and `motiongram_y`, which recorded the axis that was
collapsed rather than the picture that came out, and reliably read backwards.
`show()` has long carried `mgh` and `mgv` keys to work around exactly that; the
attributes now say it themselves.

### Renamed attributes

Older names still work and are removed in 2.0. If a script uses one, the value
it reads is the same object the new name holds.

| old | new |
|---|---|
| `motion_plot` | `motion_plot_image` |
| `motiongram_x` | `motiongram_vertical_image` |
| `motiongram_y` | `motiongram_horizontal_image` |
| `videogram_x` | `videogram_vertical_image` |
| `videogram_y` | `videogram_horizontal_image` |
| `ssm_fig` | `ssm_figure` |
| `ssm_combined` | `ssm_combined_image` |
| `movement_beat_statistics` | `movement_beat_statistics_figure` |
| `pose_average` | `pose_average_image` |
| `pose_trajectories` | `pose_trajectories_image` |

!!! warning "`pixelarray` is the one exception, and it was a bug"

    `pixelarray()` is the method that computes the frame average, and its result
    used to be stored as `pixelarray` as well. The result then hid the method, so
    calling `mv.pixelarray()` a second time raised
    `TypeError: 'MgImage' object is not callable`. The result is called
    `frameaverage_image` now, the method keeps its name, and there is
    deliberately no old-name alias for this one, since an alias would bring the
    collision back. Read `mv.frameaverage_image`; the cv2 variant stores
    `frameaverage_cv2_image`.

---

## Method chaining

Every analysis method returns its result object, so calls can be chained:

```python
mv.motion().show()
mv.motionvideo().history().show()
mv.motionvideo().blend(component_mode='average').show()
```

The result of each call is an `MgVideo`, `MgImage`, or `MgFigure`, so the chain can continue as long as the types are compatible.

One-liners work too:

```python
mg.MgVideo('/path/to/video.avi', skip=4, crop='auto').motion().history().average().show()
```

This loads the video with preprocessing, renders a motion video, builds a motion history, computes the average of that history, and displays the result, in a single expression.

---

## Next steps

- [Video Analysis](video-analysis.md)—full list of video analysis methods
- [Audio Analysis](audio-analysis.md)—full list of audio analysis methods
- [API Reference](../musicalgestures/_utils.md)—MgFigure and MgImage signatures
- [MgList Reference](../musicalgestures/_mglist.md)—MgList method signatures

# Working with Results

Analysis methods return one of three result types: `MgFigure`, `MgImage`, or `MgList`. All three implement `show()`, can be combined into stacked, time-aligned figures, and are also stored as named attributes on the video they came from. This page is the task reference; the walk-through of the three types is [chapter 6 of the wiki](https://github.com/fourMs/MGT-python/wiki/6-%E2%80%90-Figures,-Images,-Lists).

## Showing results

```python
spectrogram = mv.audio.spectrogram()
spectrogram.show()
mv.show(key='plot')     # look up a stored result by key
```

Result objects do not auto-render as the last expression of a notebook cell; call `show()`. An HTML snippet is still available programmatically via `to_html()` on `MgImage`/`MgFigure`. `show(key=...)` finds a stored result only after the method that produces it has run.

## Saving and locating output files

```python
img = mv.average()      # MgImage
img.filename            # path of the saved PNG
img.of, img.fex         # path without extension, and '.png'
spectrogram.image       # MgImage pointing to the figure's saved PNG
```

Analyses save their files next to the source video as they run, so there is nothing extra to save. `MgImage` wraps the saved file, and an `MgFigure` carries its rendered PNG as `.image`.

## Composing an MgList

```python
my_list = mg.MgList(spectrogram, mv.audio.tempogram())
my_list += mv.audio.descriptors()       # append one item
everything = mv.videograms() + my_list  # concatenate into one flat MgList
everything.as_figure(title='My Video Analysis').show()
```

`MgList` supports indexing, `len()`, `show()`, `+=`, and `+`. `as_figure()` stacks the contents into one time-aligned `MgFigure`, first element at the top. Most figure-producing methods also take a `title` argument of their own.

## Accessing data and figure objects

```python
print(spectrogram)             # MgFigure(figure_type='audio.spectrogram')
print(spectrogram.data.keys()) # dict_keys(['hop_size', 'sr', 'of', 'S', 'length'])
```

`figure_type` identifies the kind of figure, `data` holds the raw arrays used to draw it, and `layers` holds child figures when the `MgFigure` is a composition. Reading `data` is how you get at the numbers without rerunning the analysis.

## Matplotlib interop

```python
fig = spectrogram.figure       # the underlying matplotlib.pyplot.Figure
fig.set_size_inches(12, 6)
fig.savefig('spectrogram_hires.png', dpi=300)
```

`MgFigure.figure` is a live Matplotlib figure, so anything Matplotlib can do—resizing, restyling, re-saving at another resolution—works on it directly.

## Results stored on the object

Every analysis method returns its result and also stores it on the video it was called on. The stored name says what the result is: `_video` for an `MgVideo`, `_image` for an `MgImage`, `_figure` for an `MgFigure`, `_audio` for an `MgAudio`. The attributes are declared on the class, so an editor completes them and a type checker follows them; they come into existence when the method that produces them runs.

| method | stores |
|---|---|
| `motion()`, `motiongrams()` | `motion_video`, `motion_plot_image`, `motiongram_x_image`, `motiongram_y_image`, `ssm_figure` |
| `motionvideo()` | `motion_video` |
| `videograms()` | `videogram_x_image`, `videogram_y_image` |
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

The gram attributes are named for the position axis each keeps: `motiongram_x_image` keeps horizontal position and is the tall picture with time downward, `motiongram_y_image` keeps vertical position and is the wide picture with time rightward. The picture-named attributes (`motiongram_vertical_image`, `motiongram_horizontal_image`, and the videogram pair) still resolve with a deprecation warning until 2.0.

### Renamed attributes

Older names still work and are removed in 2.0. If a script uses one, the value it reads is the same object the new name holds.

| old | new |
|---|---|
| `motion_plot` | `motion_plot_image` |
| `motiongram_x` | `motiongram_x_image` |
| `motiongram_y` | `motiongram_y_image` |
| `videogram_x` | `videogram_x_image` |
| `videogram_y` | `videogram_y_image` |
| `ssm_fig` | `ssm_figure` |
| `ssm_combined` | `ssm_combined_image` |
| `movement_beat_statistics` | `movement_beat_statistics_figure` |
| `pose_average` | `pose_average_image` |
| `pose_trajectories` | `pose_trajectories_image` |

!!! note "`pixelarray` is the one name without an alias"

    `pixelarray()` is the method that computes the frame average, and its result is
    stored as `frameaverage_image`; the cv2 variant stores `frameaverage_cv2_image`.
    There is deliberately no `pixelarray` result alias, since a result under the
    method's own name would shadow the method and make a second call fail.

## Method chaining

```python
mv.motionvideo().history().average().show()
```

Every analysis method returns its result object, so calls chain as long as the types are compatible. See [chapter 7 of the wiki](https://github.com/fourMs/MGT-python/wiki/7-%E2%80%90-Chaining) for the pattern.

## Further

- [Chapter 6 of the wiki](https://github.com/fourMs/MGT-python/wiki/6-%E2%80%90-Figures,-Images,-Lists)—the course chapter on figures, images, and lists
- [Video Analysis](video-analysis.md)—full list of video analysis methods
- [Audio Analysis](audio-analysis.md)—full list of audio analysis methods
- [API Reference](../musicalgestures/_utils.md)—MgFigure and MgImage signatures
- [MgList Reference](../musicalgestures/_mglist.md)—MgList method signatures
- [Show Reference](../musicalgestures/_show.md)—`show()` and its `key` values

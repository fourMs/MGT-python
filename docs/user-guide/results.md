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
motiongrams[0].show()   # horizontal motiongram
motiongrams[1].show()   # vertical motiongram
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

# Videograms

> Auto-generated documentation for [\_videograms](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videograms.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Videograms
  - [videograms_ffmpeg](#videograms_ffmpeg)

## videograms_ffmpeg

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_videograms.py#L10)

```python
def videograms_ffmpeg(self):
```

Renders horizontal and vertical videograms of the source video using ffmpeg. Averages videoframes by axes, and creates two images of the horizontal-axis and vertical-axis stacks. In these stacks, a single row or column corresponds to a frame from the source video, and the index of the row or column corresponds to the index of the source frame.

#### Outputs

- `self.filename`\_vgx.png
- `self.filename`\_vgy.png

#### Returns

- `MgList(MgImage, MgImage)` - An MgList with the MgImage objects referring to the horizontal and vertical videograms respectively.

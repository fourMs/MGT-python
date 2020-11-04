# Average

> Auto-generated documentation for [\_average](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_average.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Average
  - [mg_average_image](#mg_average_image)

## mg_average_image

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_average.py#L7)

```python
def mg_average_image(self, filename='', normalize=True):
```

Finds and saves an average image of an input video file.

#### Arguments

- `filename` _str, optional_ - Path to the input video file. If not specified the video file pointed to by the MgObject is used. Defaults to ''.
- `normalize` _bool, optional_ - If True, normalizes pixel values in the output image. Defaults to True.

#### Outputs

- `filename`\_average.png

#### Returns

- `MgImage` - A new MgImage pointing to the output '\_average' image file.

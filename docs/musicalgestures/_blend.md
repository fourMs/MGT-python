# Blend

> Auto-generated documentation for [musicalgestures._blend](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_blend.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Blend
    - [mg_blend_image](#mg_blend_image)

## mg_blend_image

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_blend.py#L7)

```python
def mg_blend_image(
    self,
    filename=None,
    mode='all_mode',
    component_mode='average',
    target_name=None,
    overwrite=False,
):
```

Finds and saves a blended image of an input video file using FFmpeg.
The FFmpeg tblend (time blend) filter takes two consecutive frames from one single stream, and outputs the result obtained by blending the new frame on top of the old frame.

#### Arguments

- `filename` *str, optional* - Path to the input video file. If None, the video file of the MgObject is used. Defaults to None.
- `mode` *str, optional* - Set blend mode for specific pixel component or all pixel components. Accepted options are 'c0_mode', 'c1_mode', c2_mode', 'c3_mode' and 'all_mode'. Defaults to 'all_mode'.
- `component_mode` *str, optional* - Component mode of the FFmpeg tblend. Available values for component modes can be accessed here: https://ffmpeg.org/ffmpeg-filters.html#blend-1. Defaults to 'average'.
- `target_name` *str, optional* - The name of the output video. Defaults to None (which assumes that the input filename with the component mode suffix should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgImage` - A new MgImage pointing to the output image file.

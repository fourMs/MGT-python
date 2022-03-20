# Blurfaces

> Auto-generated documentation for [_blurfaces](https://github.com/fourMs/MGT-python/blob/main/_blurfaces.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Blurfaces
    - [mg_blurfaces](#mg_blurfaces)
    - [scaling_mask](#scaling_mask)

## mg_blurfaces

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_blurfaces.py#L32)

```python
def mg_blurfaces(
    self,
    mask='blur',
    mask_image=None,
    mask_scale=1.0,
    ellipse=True,
    draw_scores=False,
    coordinates=False,
    color=(0, 0, 0),
    target_name=None,
    overwrite=False,
):
```

Automatic anonymization of faces in videos.
This function works by first detecting all human faces in each video frame and then applying an anonymization filter
(blurring, black rectangles or images) on each detected face region.

Credits: `centerface.onnx` (original) and `centerface.py` are based on https://github.com/Star-Clouds/centerface (revision 8c39a49), released under [MIT license](https://github.com/Star-Clouds/CenterFace/blob/36afed/LICENSE).

#### Arguments

- `mask` *str, optional* - Mask filter mode for face regions. 'blur' applies a strong gaussian blurring, 'rectangle' draws a solid black box, 'image' replaces the face with a custom image and 'none' does leaves the input unchanged. Defaults to 'blur'.
- `mask_image` *str, optional* - Anonymization image path which can be used for masking face regions. This can be activated by specifying 'image' in the mask parameter. Defaults to None.
- `mask_scale` *float, optional* - Scale factor for face masks, to make sure that the masks cover the complete face. Defaults to 1.0.
- `ellipse` *bool, optional* - Mask faces with blurred ellipses. Defaults to True.
- `draw_scores` *bool, optional* - Draw detection faceness scores onto outputs (a score between 0 and 1 that roughly corresponds to the detector's confidence that something is a face). Defaults to False.
- `coordinates` *bool, optional* - A list of intergers corresponding to the scaled coordinates of the face masks (x1, y1, x2, y2) for each frame. When set to True the function returns two variables: the coordinates list and the MgVideo object. Defaults to False.
- `color` *tuple, optional* - Customized color of the rectangle boxes. Defaults to black (0, 0, 0).
- `target_name` *str, optional* - Target output name for the directogram. Defaults to None (which assumes that the input filename with the suffix "_blurred" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgVideo` - A MgVideo as blur_faces for parent MgVideo

## scaling_mask

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_blurfaces.py#L10)

```python
def scaling_mask(x1, y1, x2, y2, mask_scale=1.0):
```

Scale factor for face masks, to make sure that the masks cover the complete face.

#### Arguments

- `x1` *int* - X start coordinate value
- `y1` *int* - Y start coordinate value
- `x2` *int* - X end coordinate value
- `y2` *int* - Y end coordinate value
- `mask_scale` *float, optional* - Scale factor for adjusting the size of the face masks. Defaults to 1.0.

#### Returns

[x1, y1, x2, y2]: A list of intergers corresponding to the scaled coordinates of the face masks.

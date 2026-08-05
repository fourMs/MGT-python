# Ssm

> Auto-generated documentation for [musicalgestures._ssm](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_ssm.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Ssm
    - [mg_ssm](#mg_ssm)
    - [slow_dot](#slow_dot)
    - [smooth_downsample_feature_sequence](#smooth_downsample_feature_sequence)

## mg_ssm

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_ssm.py#L68)

```python
def mg_ssm(
    self,
    features: str = 'motiongrams',
    filtertype: str = 'Regular',
    threshold: float = 0.05,
    blur: str = 'None',
    norm: int | float = np.inf,
    norm_threshold: float = 0.001,
    cmap: str = 'gray_r',
    use_median: bool = False,
    kernel_size: int = 5,
    invert_yaxis: bool = True,
    combine: bool = False,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'MgList | MgImage':
```

Compute Self-Similarity Matrix (SSM) by converting the input signal into a suitable feature sequence and comparing each element of the feature sequence with all other elements of the sequence.
SSMs can be computed over different input features such as 'motiongrams', 'spectrogram', 'chromagram' and 'tempogram'.

#### Arguments

- `features` *str, optional* - Defines the type of features on which to compute SSM. Possible to compute SSM on 'motiongrams', 'videograms', 'spectrogram', 'chromagram' and 'tempogram'. Defaults to 'motiongrams'.
- `filtertype` *str, optional* - 'Regular' turns all values below `threshold` to 0. 'Binary' turns all values below `threshold` to 0, above `threshold` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `threshold` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `norm` *int, optional* - Normalize the columns of the feature sequence. Possible to compute Manhattan norm (1), Euclidean norm (2), Minimum norm (-np.inf), Maximum norm (np.inf), etc. Defaults to np.inf.
- `norm_threshold` *float, optional* - Only the columns with norm at least `norm_threshold` are normalized. Defaults to 0.001.
- `combine` *bool, optional* - For 'motiongrams', compute a single SSM from the concatenated
    horizontal + vertical motiongram features (both axes of motion in one display) and
    return a single MgImage instead of an MgList of two. Defaults to False.
- `cmap` *str, optional* - A Colormap instance or registered colormap name. The colormap maps the C values to colors. Defaults to 'gray_r'.
- `use_median` *bool, optional* - If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
- `kernel_size` *int, optional* - Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
- `invert_yaxis` *bool, optional* - Whether to invert the y axis of the SSM. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *[type], optional* - Target output name for the SSM. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

# if features='motiongrams':
- `MgList` - An MgList pointing to the output SSM images (as MgImages).
# else:
- `MgImage` - An MgImage to the output SSM.

## slow_dot

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_ssm.py#L49)

```python
def slow_dot(X: np.ndarray, Y: np.ndarray, length: int):
```

Low-memory implementation of dot product

## smooth_downsample_feature_sequence

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_ssm.py#L19)

```python
def smooth_downsample_feature_sequence(
    X: np.ndarray,
    sr: int,
    filt_len: int = 41,
    down_sampling: int = 10,
    w_type: str = 'boxcar',
):
```

Smoothes and downsamples a feature sequence. Smoothing is achieved by convolution with a filter kernel

#### Arguments

- `X` *np.ndarray* - Feature sequence.
- `sr` *int* - Sampling rate.
- `filt_len` *int, optional* - Length of smoothing filter. Defaults to 41.
- `down_sampling` *int, optional* - Downsampling factor. Defaults to 10.
- `w_type` *str, optional* - Window type of smoothing filter. Defaults to 'boxcar'.

#### Returns

- `X_smooth` *np.ndarray* - Smoothed and downsampled feature sequence.
- `sr_feature` *scalar* - Sampling rate of `X_smooth`.

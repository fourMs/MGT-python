# Ssm

> Auto-generated documentation for [musicalgestures._ssm](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_ssm.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Ssm
    - [mg_ssm](#mg_ssm)
    - [smooth_downsample_feature_sequence](#smooth_downsample_feature_sequence)

## mg_ssm

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_ssm.py#L47)

```python
def mg_ssm(
    self,
    features='motiongrams',
    filtertype='Regular',
    thresh=0.05,
    blur='None',
    norm=np.inf,
    threshold=0.001,
    cmap='gray_r',
    use_median=False,
    kernel_size=5,
    target_name=None,
    overwrite=False,
):
```

Compute Self-Similarity Matrix (SSM) by converting the input signal into a suitable feature sequence and comparing each element of the feature sequence with all other elements of the sequence.
SSMs can be computed over different input features such as 'motiongrams', 'spectrogram', 'chromagram' and 'tempogram'.

#### Arguments

- `features` *str, optional* - Defines the type of features on which to compute SSM. Possible to compute SSM on 'motiongrams', 'spectrogram', 'chromagram' and 'tempogram'. Defaults to 'motiongrams'.
- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `norm` *int, optional* - Normalize the columns of the feature sequence. Possible to compute Manhattan norm (1), Euclidean norm (2), Minimum norm (-np.inf), Maximum norm (np.inf), etc. Defaults to np.inf.
- `threshold` *float, optional* - Only the columns with norm at least the amount of `threshold` indicated are normalized. Defaults to 0.001.
- `cmap` *str, optional* - A Colormap instance or registered colormap name. The colormap maps the C values to colors. Defaults to 'gray_r'.
- `use_median` *bool, optional* - If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
- `kernel_size` *int, optional* - Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
- `target_name` *[type], optional* - Target output name for the SSM. Defaults to None.
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

# if features='motiongrams':
- `MgList` - An MgList pointing to the output SSM images (as MgImages).
# else:
- `MgImage` - An MgImage to the output SSM.

## smooth_downsample_feature_sequence

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_ssm.py#L17)

```python
def smooth_downsample_feature_sequence(
    X,
    sr,
    filt_len=41,
    down_sampling=10,
    w_type='boxcar',
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

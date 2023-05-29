# Audio

> Auto-generated documentation for [musicalgestures._audio](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Audio
    - [MgAudio](#mgaudio)
        - [MgAudio().descriptors](#mgaudiodescriptors)
        - [MgAudio().format_time](#mgaudioformat_time)
        - [MgAudio().hpss](#mgaudiohpss)
        - [MgAudio().spectrogram](#mgaudiospectrogram)
        - [MgAudio().tempogram](#mgaudiotempogram)
        - [MgAudio().waveform](#mgaudiowaveform)

## MgAudio

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L18)

```python
class MgAudio():
    def __init__(filename, sr=22050, n_fft=2048, hop_length=512):
```

Class container for audio analysis processes.

### MgAudio().descriptors

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L484)

```python
def descriptors(
    n_mels=128,
    fmin=0.0,
    fmax=None,
    power=2,
    dpi=300,
    autoshow=True,
    original_time=False,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure of plots showing spectral/loudness descriptors, including RMS energy, spectral flatness, centroid, bandwidth, rolloff of the video/audio file.

#### Arguments

- `n_mels` *int, optional* - The number of mel filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 128.
- `fmin` *float, optional* - Lowest frequency (in Hz). Defaults to 0.0.
- `fmax` *float, optional* - Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0
- `power` *float, optional* - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `original_time` *bool, optional* - Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_descriptors.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

### MgAudio().format_time

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L46)

```python
def format_time(ax):
```

Format time for audio plotting of video file. This is useful if one wants to plot the original time of the video when frames have been skipped beforehand.

#### Arguments

- `ax` *str, optional* - Axis of the figure.

### MgAudio().hpss

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L375)

```python
def hpss(
    n_mels=128,
    fmin=0.0,
    fmax=None,
    kernel_size=31,
    margin=(1.0, 5.0),
    power=2.0,
    mask=False,
    residual=False,
    dpi=300,
    autoshow=True,
    original_time=False,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure with a plots of harmonic and percussive components of the audio file.

#### Arguments

- `n_mels` *int, optional* - Number of Mel bands to generate. Defaults to 128.
- `fmin` *float, optional* - Lowest frequency (in Hz). Defaults to 0.0.
- `fmax` *float, optional* - Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0.
kernel_size (int or tuple, optional): Kernel size(s) for the median filters. If tuple, the first value specifies the width of the harmonic filter, and the second value specifies the width of the percussive filter. Defaults to 31.
margin (float or tuple, optional): Margin size(s) for the masks (as described in this [paper](https://archives.ismir.net/ismir2014/paper/000127.pdf)). If tuple, the first value specifies the margin of the harmonic mask, and the second value specifies the margin of the percussive mask. Defaults to (1.0,5.0).
- `power` *float, optional* - Exponent for the Wiener filter when constructing soft mask matrices. Defaults to 2.0.
- `mask` *bool, optional* - Return the masking matrices instead of components. Defaults to False.
- `residual` *bool, optional* - Whether to return residual components of the audio file or not. Defaults to False.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `original_time` *bool, optional* - Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempogram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

### MgAudio().spectrogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L160)

```python
def spectrogram(
    fmin=0.0,
    fmax=None,
    n_mels=128,
    power=2,
    dpi=300,
    autoshow=True,
    raw=False,
    original_time=False,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure showing the mel-scaled spectrogram of the video/audio file.

#### Arguments

- `n_mels` *int, optional* - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 128.
- `fmin` *float, optional* - Lowest frequency (in Hz). Defaults to 0.0.
- `fmax` *float, optional* - Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0.
- `power` *float, optional* - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `raw` *bool, optional* - Whether to show labels and ticks on the plot. Defaults to False.
- `original_time` *bool, optional* - Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_spectrogram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

### MgAudio().tempogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L274)

```python
def tempogram(
    dpi=300,
    autoshow=True,
    raw=False,
    original_time=False,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure with a plots of onset strength and tempogram of the video/audio file.

#### Arguments

- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `raw` *bool, optional* - Whether to show labels and ticks on the plot. Defaults to False.
- `original_time` *bool, optional* - Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempogram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

### MgAudio().waveform

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L80)

```python
def waveform(
    dpi=300,
    autoshow=True,
    raw=False,
    original_time=True,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure showing the waveform of the video/audio file.

#### Arguments

- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `sr` *int, optional* - Sampling rate of the audio file. Defaults to 22050.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `raw` *bool, optional* - Whether to show labels and ticks on the plot. Defaults to False.
- `original_time` *bool, optional* - Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_waveform.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

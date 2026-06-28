# Audio

> Auto-generated documentation for [musicalgestures._audio](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Audio
    - [MgAudio](#mgaudio)
        - [MgAudio().beat_statistics](#mgaudiobeat_statistics)
        - [MgAudio().chromagram](#mgaudiochromagram)
        - [MgAudio().descriptors](#mgaudiodescriptors)
        - [MgAudio().duration](#mgaudioduration)
        - [MgAudio().format_time](#mgaudioformat_time)
        - [MgAudio().hpss](#mgaudiohpss)
        - [MgAudio().mfcc](#mgaudiomfcc)
        - [MgAudio().numpy](#mgaudionumpy)
        - [MgAudio().spectrogram](#mgaudiospectrogram)
        - [MgAudio().tempo](#mgaudiotempo)
        - [MgAudio().tempogram](#mgaudiotempogram)
        - [MgAudio().waveform](#mgaudiowaveform)

## MgAudio

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L22)

```python
class MgAudio():
    def __init__(
        filename: str,
        sr: int = None,
        n_fft: int = 2048,
        hop_length: int = 512,
    ):
```

Class container for audio analysis processes.

### MgAudio().beat_statistics

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L1047)

```python
def beat_statistics(
    n_bins: int = 32,
    cmap: str = 'YlOrRd',
    dpi: int = 300,
    autoshow: bool = True,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> MgFigure:
```

Renders circular statistics of beat-timing consistency.

Fits an ideal isochronous beat grid to the detected beats and visualises how
each beat deviates from it: a polar histogram of beat phases (with the mean
resultant vector) and a time series of millisecond deviations. This reveals
whether a performer rushes, drags, or keeps steady time.

#### Arguments

- `n_bins` *int, optional* - Number of bins in the polar phase histogram. Defaults to 32.
- `cmap` *str, optional* - Matplotlib colormap for the polar histogram. Defaults to 'YlOrRd'.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Use 'filename' to set the filename as title. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_beatstats.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object whose ``.data`` mirrors the beat statistics from tempo(),
    or None if fewer than four beats are detected.

#### See also

- [MgFigure](_utils.md#mgfigure)

### MgAudio().chromagram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L750)

```python
def chromagram(
    n_chroma: int = 12,
    norm: float | None = np.inf,
    chroma_type: str = 'cqt',
    cmap: str = 'coolwarm',
    dpi: int = 300,
    autoshow: bool = True,
    raw: bool = False,
    original_time: bool = False,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> MgFigure:
```

Renders a figure showing the chromagram of the video/audio file.

A chromagram maps audio energy onto the 12 pitch classes (C, C#, D, …, B) over time,
making it useful for analysing harmony and chord progressions.

#### Arguments

- `n_chroma` *int, optional* - Number of chroma bins (pitch classes). Defaults to 12.
norm (float or None, optional): Column-wise normalisation. np.inf gives maximum-norm,
    1 gives L1-norm, 2 gives L2-norm, None disables normalisation. Defaults to np.inf.
- `chroma_type` *str, optional* - Algorithm used to compute the chroma features.
    'cqt'  — Constant-Q transform (best for music, handles low frequencies well).
    'stft' — Short-time Fourier transform (faster, slightly lower pitch resolution).
    'cens' — Chroma Energy Normalised Statistics (robust to dynamics and timbre).
    Defaults to 'cqt'.
- `cmap` *str, optional* - Matplotlib colormap for the chromagram display. Defaults to 'coolwarm'.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `raw` *bool, optional* - Whether to show labels and ticks on the plot. Defaults to False.
- `original_time` *bool, optional* - Whether to plot original time or not. Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Use 'filename' to set the filename as title. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_chromagram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

#### See also

- [MgFigure](_utils.md#mgfigure)

### MgAudio().descriptors

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L598)

```python
def descriptors(
    n_mels: int = 128,
    fmin: float = 0.0,
    fmax: float | None = None,
    power: int = 2,
    dpi: int = 300,
    autoshow: bool = True,
    original_time: bool = False,
    title: str | None = None,
    target_name: str | None = None,
    save_data: bool = False,
    data_format: str | list = 'csv',
    target_name_data: str | None = None,
    overwrite: bool = True,
) -> MgFigure:
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
- `save_data` *bool, optional* - Whether to also save the per-frame descriptor time series (time, RMS, centroid, bandwidth, rolloff, rolloff_min, flatness) to a data file. Defaults to False.
- `data_format` *str/list, optional* - Format of the saved descriptor data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple formats, use a list, e.g. ['csv', 'txt']. Defaults to 'csv'.
- `target_name_data` *str, optional* - The name of the output data file. Defaults to None (which uses the input filename with the suffix "_descriptors").
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

#### See also

- [MgFigure](_utils.md#mgfigure)

### MgAudio().duration

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L60)

```python
@property
def duration() -> float:
```

Audio duration in **seconds** (for an MgAudio this equals ``self.length``).

### MgAudio().format_time

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L93)

```python
def format_time(ax, original_time: bool = True, original_duration=None):
```

Format time for audio plotting of video file. This is useful if one wants to plot the original time of the video when frames have been skipped beforehand.

#### Arguments

- `ax` *str, optional* - Axis of the figure.
- `original_time` *bool, optional* - Whether to get the original time for audio plotting or not. Defaults to True.
- `original_duration` *bool, optional* - Whether to add the original duration of the file to be formatted manually. Defaults to None.

### MgAudio().hpss

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L452)

```python
def hpss(
    dim: int = 2,
    n_mels: int = 128,
    fmin: float = 0.0,
    fmax: float | None = None,
    kernel_size: int | tuple = 31,
    margin: float | tuple = (1.0, 5.0),
    power: float = 2.0,
    top_db: float = 80.0,
    mask: bool = False,
    residual: bool = False,
    dpi: int = 300,
    autoshow: bool = True,
    original_time: bool = False,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> MgFigure:
```

Renders a figure with a plots of harmonic and percussive components of the audio file.

#### Arguments

- `dim` *str, optional* - Whether to plot hpss in one (i.e. waveform) or two (i.e. spectrogram) dimensions. Defaults to 2.
- `n_mels` *int, optional* - Number of Mel bands to generate. Defaults to 128.
- `fmin` *float, optional* - Lowest frequency (in Hz). Defaults to 0.0.
- `fmax` *float, optional* - Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0.
kernel_size (int or tuple, optional): Kernel size(s) for the median filters. If tuple, the first value specifies the width of the harmonic filter, and the second value specifies the width of the percussive filter. Defaults to 31.
margin (float or tuple, optional): Margin size(s) for the masks (as described in this [paper](https://archives.ismir.net/ismir2014/paper/000127.pdf)). If tuple, the first value specifies the margin of the harmonic mask, and the second value specifies the margin of the percussive mask. Defaults to (1.0,5.0).
- `power` *float, optional* - Exponent for the Wiener filter when constructing soft mask matrices. Defaults to 2.0.
- `top_db` *float, optional* - threshold the output at top_db below the peak: max(20 * log10(S/ref)) - top_db. Defaults to 80.0.
- `mask` *bool, optional* - Return the masking matrices instead of components. Defaults to False.
- `residual` *bool, optional* - Whether to return residual components of the audio file or not. Defaults to False.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `original_time` *bool, optional* - Whether to plot original time or not. This parameter can be useful if the video file has been shortened beforehand (e.g. skip). Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_hpss.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

#### See also

- [MgFigure](_utils.md#mgfigure)

### MgAudio().mfcc

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L851)

```python
def mfcc(
    n_mfcc: int = 13,
    cmap: str = 'RdBu_r',
    dpi: int = 300,
    autoshow: bool = True,
    raw: bool = False,
    original_time: bool = False,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> MgFigure:
```

Renders a figure showing the Mel-frequency cepstral coefficients (MFCCs) of the video/audio file.

MFCCs compactly describe the spectral envelope (timbre) of a sound over time and are
widely used as features for audio classification and similarity.

#### Arguments

- `n_mfcc` *int, optional* - Number of MFCCs to compute. Defaults to 13.
- `cmap` *str, optional* - Matplotlib colormap for the display. Defaults to 'RdBu_r'.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `raw` *bool, optional* - Whether to show labels and ticks on the plot. Defaults to False.
- `original_time` *bool, optional* - Whether to plot original time or not. Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Use 'filename' to set the filename as title. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_mfcc.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

#### See also

- [MgFigure](_utils.md#mgfigure)

### MgAudio().numpy

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L87)

```python
def numpy():
```

Read the original file of the MgAudio object as a numpy array using librosa.

### MgAudio().spectrogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L238)

```python
def spectrogram(
    fmin: float = 0.0,
    fmax: float | None = None,
    n_mels: int = 128,
    power: float = 2.0,
    top_db: float = 80.0,
    dpi: int = 300,
    autoshow: bool = True,
    raw: bool = False,
    original_time: bool = False,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> MgFigure:
```

Renders a figure showing the mel-scaled spectrogram of the video/audio file.

#### Arguments

- `n_mels` *int, optional* - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 128.
- `fmin` *float, optional* - Lowest frequency (in Hz). Defaults to 0.0.
- `fmax` *float, optional* - Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0.
- `power` *float, optional* - The steepness of the curve for the color mapping. Defaults to 2.
- `top_db` *float, optional* - threshold the output at top_db below the peak: max(20 * log10(S/ref)) - top_db. Defaults to 80.0.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `raw` *bool, optional* - Whether to show labels and ticks on the plot. Defaults to False.
- `original_time` *bool, optional* - Whether to plot original time or not. This parameter can be useful if the video file has been shortened beforehand (e.g. skip). Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_spectrogram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

#### See also

- [MgFigure](_utils.md#mgfigure)

### MgAudio().tempo

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L931)

```python
def tempo(
    dpi: int = 300,
    autoshow: bool = True,
    raw: bool = False,
    original_time: bool = False,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> MgFigure:
```

Estimates tempo and beat positions, and renders the waveform with beat markers.

Uses librosa's beat tracker. In addition to the figure, the returned object's
``.data`` dictionary contains the estimated tempo, beat times, inter-beat
intervals, a beat-regularity measure, and circular beat statistics (phase
deviation of each beat from a fitted ideal grid, plus a Rayleigh test of
timing consistency).

#### Arguments

- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `raw` *bool, optional* - Whether to show labels and ticks on the plot. Defaults to False.
- `original_time` *bool, optional* - Whether to plot original time or not. Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Use 'filename' to set the filename as title. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempo.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object. Access numeric results via ``.data``:
    'tempo', 'beat_times', 'ibi', 'beat_regularity', 'beat_phases',
    'deviations_s', 'R_beat', 'mu_beat', 'T_fit', 't0_fit', 'p_rayleigh'.

#### See also

- [MgFigure](_utils.md#mgfigure)

### MgAudio().tempogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L347)

```python
def tempogram(
    dpi: int = 300,
    autoshow: bool = True,
    raw: bool = False,
    onset_strength: bool = True,
    original_time: bool = False,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> MgFigure:
```

Renders a figure with a plots of onset strength and tempogram of the video/audio file.

#### Arguments

- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `raw` *bool, optional* - Whether to show labels and ticks on the plot. Defaults to False.
- `onset_strength` *bool, optional* - Whether to include the onset-strength panel above the
    tempogram. Set to False for just the tempogram in a single-panel figure (the same
    size as spectrogram/chromagram). Defaults to True.
- `original_time` *bool, optional* - Whether to plot original time or not. This parameter can be useful if the video file has been shortened beforehand (e.g. skip). Defaults to False.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempogram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

#### See also

- [MgFigure](_utils.md#mgfigure)

### MgAudio().waveform

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L131)

```python
def waveform(
    dpi: int = 300,
    autoshow: bool = True,
    raw: bool = False,
    colored: bool = False,
    image_width: int = 2500,
    image_height: int = 500,
    fmin: int = 500,
    fmax: int | None = None,
    cmap: str = 'freesound',
    original_time: bool = True,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
) -> MgFigure:
```

Renders a figure showing the waveform of the video/audio file.

#### Arguments

- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `raw` *bool, optional* - Whether to show labels and ticks on the plot. Defaults to False.
- `colored` *bool, optional* - Whether to create a colored waveform image (freesound-style) from an audio input file. Defauts to False.
- `image_width` *int, optional* - Number of pixels for the colored waveform image width. Defaults to 2500.
- `image_height` *int, optional* - Number of pixels for the colored waveform image height. Defaults to 500.
- `fmin` *int, optional* - Minimum frequency for computing spectral centroid for the colored waveform image. Defaults to 500.
- `fmax` *int, optional* - Maximum frequency for computing spectral centroid for the colored waveform image. Defaults to None (i.e. Nyquist frequency).
- `cmap` *str, optional* - Colormap used for coloring the waveform, all colormaps included with matplotlib can be used. Defaults to 'freesound'.
- `original_time` *bool, optional* - Whether to plot original time or not. This parameter can be useful if the video file has been shortened beforehand (e.g. skip). Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_waveform.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

#### See also

- [MgFigure](_utils.md#mgfigure)

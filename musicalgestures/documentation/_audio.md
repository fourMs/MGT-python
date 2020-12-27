# Audio

> Auto-generated documentation for [\_audio](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Audio
  - [Audio](#audio)
    - [Audio().descriptors](#audiodescriptors)
    - [Audio().spectrogram](#audiospectrogram)
    - [Audio().tempogram](#audiotempogram)
  - [mg_audio_descriptors](#mg_audio_descriptors)
  - [mg_audio_spectrogram](#mg_audio_spectrogram)
  - [mg_audio_tempogram](#mg_audio_tempogram)

## Audio

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L11)

```python
class Audio():
    def __init__(filename):
```

Class container for audio analysis processes.

### Audio().descriptors

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L112)

```python
def descriptors(
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None
):
```

Renders a figure of plots showing spectral/loudness descriptors, including RMS energy, spectral flatness, centroid, bandwidth, rolloff of the video/audio file.

#### Arguments

- `window_size` _int, optional_ - The size of the FFT frame. Defaults to 4096.
- `overlap` _int, optional_ - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` _int, optional_ - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` _float, optional_ - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` _int, optional_ - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` _bool, optional_ - Whether to show the resulting figure automatically. Defaults to True.
- `title` _str, optional_ - Optionally add title to the figure. Defaults to None, which uses the file name as a title.

#### Outputs

- `self.filename`\_descriptors.png

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

### Audio().spectrogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L26)

```python
def spectrogram(
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None
):
```

Renders a figure showing the mel-scaled spectrogram of the video/audio file.

#### Arguments

- `window_size` _int, optional_ - The size of the FFT frame. Defaults to 4096.
- `overlap` _int, optional_ - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` _int, optional_ - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` _float, optional_ - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` _int, optional_ - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` _bool, optional_ - Whether to show the resulting figure automatically. Defaults to True.
- `title` _str, optional_ - Optionally add title to the figure. Defaults to None, which uses the file name as a title.

#### Outputs

- `self.filename`\_spectrogram.png

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

### Audio().tempogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L233)

```python
def tempogram(
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None
):
```

Renders a figure with a plots of onset strength and tempogram of the video/audio file.

#### Arguments

- `window_size` _int, optional_ - The size of the FFT frame. Defaults to 4096.
- `overlap` _int, optional_ - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` _int, optional_ - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` _float, optional_ - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` _int, optional_ - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` _bool, optional_ - Whether to show the resulting figure automatically. Defaults to True.
- `title` _str, optional_ - Optionally add title to the figure. Defaults to None, which uses the file name as a title.

#### Outputs

- `self.filename`\_tempogram.png

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

## mg_audio_descriptors

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L403)

```python
def mg_audio_descriptors(
    filename=None,
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None
):
```

Renders a figure of plots showing spectral/loudness descriptors, including RMS energy, spectral flatness, centroid, bandwidth, rolloff of the video/audio file.

#### Arguments

- `filename` _str, optional_ - Path to the audio/video file to be processed. Defaults to None.
- `window_size` _int, optional_ - The size of the FFT frame. Defaults to 4096.
- `overlap` _int, optional_ - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` _int, optional_ - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` _float, optional_ - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` _int, optional_ - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` _bool, optional_ - Whether to show the resulting figure automatically. Defaults to True.
- `title` _str, optional_ - Optionally add title to the figure. Defaults to None, which uses the file name as a title.

#### Outputs

- `filename`\_descriptors.png

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

## mg_audio_spectrogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L309)

```python
def mg_audio_spectrogram(
    filename=None,
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None
):
```

Renders a figure showing the mel-scaled spectrogram of the video/audio file.

#### Arguments

- `filename` _str, optional_ - Path to the audio/video file to be processed. Defaults to None.
- `window_size` _int, optional_ - The size of the FFT frame. Defaults to 4096.
- `overlap` _int, optional_ - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` _int, optional_ - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` _float, optional_ - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` _int, optional_ - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` _bool, optional_ - Whether to show the resulting figure automatically. Defaults to True.
- `title` _str, optional_ - Optionally add title to the figure. Defaults to None, which uses the file name as a title.

#### Outputs

- `filename`\_spectrogram.png

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

## mg_audio_tempogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audio.py#L530)

```python
def mg_audio_tempogram(
    filename=None,
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None
):
```

Renders a figure with a plots of onset strength and tempogram of the video/audio file.

#### Arguments

- `filename` _str, optional_ - Path to the audio/video file to be processed. Defaults to None.
- `window_size` _int, optional_ - The size of the FFT frame. Defaults to 4096.
- `overlap` _int, optional_ - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` _int, optional_ - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` _float, optional_ - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` _int, optional_ - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` _bool, optional_ - Whether to show the resulting figure automatically. Defaults to True.
- `title` _str, optional_ - Optionally add title to the figure. Defaults to None, which uses the file name as a title.

#### Outputs

- `filename`\_tempogram.png

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

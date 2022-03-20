# Audio

> Auto-generated documentation for [_audio](https://github.com/fourMs/MGT-python/blob/main/_audio.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Audio
    - [Audio](#audio)
        - [Audio().descriptors](#audiodescriptors)
        - [Audio().spectrogram](#audiospectrogram)
        - [Audio().tempogram](#audiotempogram)
        - [Audio().waveform](#audiowaveform)
    - [mg_audio_descriptors](#mg_audio_descriptors)
    - [mg_audio_spectrogram](#mg_audio_spectrogram)
    - [mg_audio_tempogram](#mg_audio_tempogram)
    - [mg_audio_waveform](#mg_audio_waveform)

## Audio

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_audio.py#L22)

```python
class Audio():
    def __init__(filename):
```

Class container for audio analysis processes.

### Audio().descriptors

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_audio.py#L210)

```python
def descriptors(
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure of plots showing spectral/loudness descriptors, including RMS energy, spectral flatness, centroid, bandwidth, rolloff of the video/audio file.

#### Arguments

- `window_size` *int, optional* - The size of the FFT frame. Defaults to 4096.
- `overlap` *int, optional* - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` *int, optional* - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` *float, optional* - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses the file name as a title.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_descriptors.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

### Audio().spectrogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_audio.py#L107)

```python
def spectrogram(
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure showing the mel-scaled spectrogram of the video/audio file.

#### Arguments

- `window_size` *int, optional* - The size of the FFT frame. Defaults to 4096.
- `overlap` *int, optional* - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` *int, optional* - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` *float, optional* - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses the file name as a title.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_spectrogram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

### Audio().tempogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_audio.py#L348)

```python
def tempogram(
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure with a plots of onset strength and tempogram of the video/audio file.

#### Arguments

- `window_size` *int, optional* - The size of the FFT frame. Defaults to 4096.
- `overlap` *int, optional* - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` *int, optional* - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` *float, optional* - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses the file name as a title.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempogram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

### Audio().waveform

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_audio.py#L38)

```python
def waveform(
    mono=False,
    dpi=300,
    autoshow=True,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure showing the waveform of the video/audio file.

#### Arguments

- `mono` *bool, optional* - Convert the signal to mono. Defaults to False.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses the file name as a title. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_waveform.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

## mg_audio_descriptors

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_audio.py#L629)

```python
def mg_audio_descriptors(
    filename=None,
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure of plots showing spectral/loudness descriptors, including RMS energy, spectral flatness, centroid, bandwidth, rolloff of the video/audio file.

#### Arguments

- `filename` *str, optional* - Path to the audio/video file to be processed. Defaults to None.
- `window_size` *int, optional* - The size of the FFT frame. Defaults to 4096.
- `overlap` *int, optional* - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` *int, optional* - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` *float, optional* - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses the file name as a title.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_descriptors.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

## mg_audio_spectrogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_audio.py#L518)

```python
def mg_audio_spectrogram(
    filename=None,
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure showing the mel-scaled spectrogram of the video/audio file.

#### Arguments

- `filename` *str, optional* - Path to the audio/video file to be processed. Defaults to None.
- `window_size` *int, optional* - The size of the FFT frame. Defaults to 4096.
- `overlap` *int, optional* - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` *int, optional* - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` *float, optional* - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses the file name as a title.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_spectrogram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

## mg_audio_tempogram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_audio.py#L773)

```python
def mg_audio_tempogram(
    filename=None,
    window_size=4096,
    overlap=8,
    mel_filters=512,
    power=2,
    dpi=300,
    autoshow=True,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure with a plots of onset strength and tempogram of the video/audio file.

#### Arguments

- `filename` *str, optional* - Path to the audio/video file to be processed. Defaults to None.
- `window_size` *int, optional* - The size of the FFT frame. Defaults to 4096.
- `overlap` *int, optional* - The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
- `mel_filters` *int, optional* - The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
- `power` *float, optional* - The steepness of the curve for the color mapping. Defaults to 2.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses the file name as a title.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempogram.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

## mg_audio_waveform

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_audio.py#L441)

```python
def mg_audio_waveform(
    filename=None,
    mono=False,
    dpi=300,
    autoshow=True,
    title=None,
    target_name=None,
    overwrite=False,
):
```

Renders a figure showing the waveform of the video/audio file.

#### Arguments

- `filename` *str, optional* - Path to the audio/video file to be processed. Defaults to None.
- `mono` *bool, optional* - Convert the signal to mono. Defaults to False.
- `dpi` *int, optional* - Image quality of the rendered figure in DPI. Defaults to 300.
- `autoshow` *bool, optional* - Whether to show the resulting figure automatically. Defaults to True.
- `title` *str, optional* - Optionally add title to the figure. Defaults to None, which uses the file name as a title. Defaults to None.
- `target_name` *str, optional* - The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_waveform.png" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgFigure` - An MgFigure object referring to the internal figure and its data.

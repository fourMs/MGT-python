# Colored

> Auto-generated documentation for [musicalgestures._colored](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_colored.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Colored
    - [MgAudioProcessor](#mgaudioprocessor)
        - [MgAudioProcessor().peaks](#mgaudioprocessorpeaks)
        - [MgAudioProcessor().read_samples](#mgaudioprocessorread_samples)
        - [MgAudioProcessor().spectral_centroid](#mgaudioprocessorspectral_centroid)
    - [MgWaveformImage](#mgwaveformimage)
        - [MgWaveformImage().draw_peaks](#mgwaveformimagedraw_peaks)
        - [MgWaveformImage().interpolate_colors](#mgwaveformimageinterpolate_colors)
    - [min_max_level](#min_max_level)

## MgAudioProcessor

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_colored.py#L25)

```python
class MgAudioProcessor(object):
    def __init__(
        filename,
        n_fft,
        fmin,
        fmax=None,
        window_function=np.hanning,
    ):
```

### MgAudioProcessor().peaks

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_colored.py#L134)

```python
def peaks(start_seek, end_seek, block_size=1024):
```

Read all samples between start_seek and end_seek, then find the minimum and maximum peak
in that range. Returns that pair in the order they were found. So if min was found first,
it returns (min, max) else the other way around.

### MgAudioProcessor().read_samples

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_colored.py#L70)

```python
def read_samples(start, size, resize_if_less=False):
```

Read size samples starting at start, if resize_if_less is True and less than size
samples are read, resize the array to size and fill with zeros

### MgAudioProcessor().spectral_centroid

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_colored.py#L118)

```python
def spectral_centroid(seek_point):
```

Starting at seek_point to read n_fft samples and calculate the spectral centroid

## MgWaveformImage

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_colored.py#L168)

```python
class MgWaveformImage(object):
    def __init__(image_width=2500, image_height=500, cmap='freesound'):
```

### MgWaveformImage().draw_peaks

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_colored.py#L194)

```python
def draw_peaks(x, peaks, spectral_centroid):
```

Draw 2 peaks at x using the spectral_centroid for color

### MgWaveformImage().interpolate_colors

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_colored.py#L205)

```python
def interpolate_colors(colors, flat=False, num_colors=256):
```

Given a list of colors, create a larger list of colors linearly interpolating
the first one. If flatten is True a list of numbers will be returned. If
False, a list of (r,g,b) tuples. num_colors is the number of colors wanted
in the final list

## min_max_level

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_colored.py#L11)

```python
def min_max_level(filename):
```

# Sonification

> Auto-generated documentation for [musicalgestures._sonification](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_sonification.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Sonification
    - [mg_sonomotiongram](#mg_sonomotiongram)

## mg_sonomotiongram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_sonification.py#L8)

```python
def mg_sonomotiongram(
    self,
    sonogram='vertical',
    n_fft=2048,
    sr=22050,
    n_iter=32,
    flip=True,
    normalize=True,
    target_name=None,
    overwrite=True,
):
```

Creates a *sonomotiongram*: a sonification of the video's motiongram.

The motiongram (a time–space image of where motion happens) is treated as a magnitude
spectrogram—spatial position maps to frequency, motion intensity to amplitude—and
converted back to audio with an inverse STFT (Griffin–Lim phase estimation). The result
lets you *hear* the motion. Based on Jensenius, "Some video abstraction techniques for
displaying body movement in analysis and performance" / sonomotiongrams (SMC 2013).

#### Arguments

- `sonogram` *str, optional* - Which motiongram to sonify: 'vertical' (motion across the
    vertical axis) or 'horizontal'. Defaults to 'vertical'.
- `n_fft` *int, optional* - FFT size; sets the number of frequency bins (n_fft//2+1) the
    motiongram rows are mapped onto. Defaults to 2048.
- `sr` *int, optional* - Sample rate of the rendered audio. Defaults to 22050.
- `n_iter` *int, optional* - Griffin–Lim iterations for phase estimation (higher = cleaner,
    slower). Defaults to 32.
- `flip` *bool, optional* - If True, map the top of the image to high frequencies (usually
    more intuitive). Defaults to True.
- `normalize` *bool, optional* - Normalise the rendered audio to peak 1.0. Defaults to True.
- `target_name` *str, optional* - Output audio filename. Defaults to None (input filename
    with the suffix "_sono_<sonogram>.wav").
- `overwrite` *bool, optional* - Whether to allow overwriting or auto-increment the filename.
    Defaults to True.

#### Returns

- `MgAudio` - An MgAudio pointing to the rendered sonification (WAV).

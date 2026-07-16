# Audiofeatures

> Auto-generated documentation for [musicalgestures._audiofeatures](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audiofeatures.py) module.

Scipy-only audio feature extraction for sound--motion analysis.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Audiofeatures
    - [attack_spectral_centroid](#attack_spectral_centroid)
    - [energy_onsets](#energy_onsets)
    - [rms_envelope](#rms_envelope)
    - [spectral_flux](#spectral_flux)
    - [spectral_flux_onsets](#spectral_flux_onsets)
    - [t60_backward_decay](#t60_backward_decay)

RMS envelopes, spectral-flux and energy-based onset detection, T60-style
backward-decay reverberation time, and attack spectral centroid.

These functions are independent of the MgAudio class and operate on plain
numpy waveforms (`y`, `sr`), so they can be used on any mono audio array.
They complement the librosa-based, figure-producing methods of `MgAudio`
with lightweight numeric outputs. All onset detectors use the canonical
peak-picker (`musicalgestures.pick_peaks`).

Sources: cymbal-comparison study and Westney-comparisons study (Jensenius).

## attack_spectral_centroid

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audiofeatures.py#L207)

```python
def attack_spectral_centroid(
    y,
    sr,
    attack=0.12,
    nperseg=2048,
    hop=512,
    window=0.02,
):
```

Attack spectral centroid: the energy-weighted mean STFT spectral
centroid over the first `attack` seconds after the RMS-envelope peak.
Discriminates, e.g., strike placement and damping on a cymbal.

The constants (120 ms attack, 2048-sample Hann window, 512 hop) are
PROVISIONAL defaults reimplemented from the cymbal-comparison paper's
method description.

Source: cymbal-comparison study (Jensenius).

#### Arguments

- `y` *np.ndarray* - Mono waveform.
- `sr` *int* - Sampling rate (Hz).
- `attack` *float, optional* - Analysis span after the envelope peak (s).
    Defaults to 0.12.
- `nperseg` *int, optional* - STFT window length in samples. Defaults to 2048.
- `hop` *int, optional* - STFT hop in samples. Defaults to 512.
- `window` *float, optional* - RMS window length (s) used to locate the
    envelope peak. Defaults to 0.02.

#### Returns

- `float` - The attack spectral centroid in Hz (NaN if the attack segment
    is too short to analyse).

## energy_onsets

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audiofeatures.py#L107)

```python
def energy_onsets(y, sr, window=0.02, rel_threshold=0.15, min_interval=0.06):
```

Energy-based onset times: the RMS envelope's half-wave-rectified first
difference is peak-picked (canonical peak-picker) at a threshold
relative to the per-file peak, with a minimum inter-onset interval.

Reliable for discrete strokes; over-fragments sustained rolls/tremolo
and can trigger on near-noise material. The default constants
(0.15 x peak, 0.06 s) are PROVISIONAL defaults reimplemented from the
cymbal-comparison paper's method description.

Source: cymbal-comparison study (Jensenius).

#### Arguments

- `y` *np.ndarray* - Mono waveform.
- `sr` *int* - Sampling rate (Hz).
- `window` *float, optional* - RMS window length (s). Defaults to 0.02.
- `rel_threshold` *float, optional* - Threshold as a fraction of the
    onset-function's peak. Defaults to 0.15.
- `min_interval` *float, optional* - Minimum inter-onset interval (s).
    Defaults to 0.06.

#### Returns

- `np.ndarray` - Onset times in seconds.

## rms_envelope

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audiofeatures.py#L21)

```python
def rms_envelope(y, sr, window=0.02):
```

RMS energy envelope over consecutive, non-overlapping windows.

Source: cymbal-comparison study (Jensenius); also the
Westney-comparisons study's high-rate sync envelope.

#### Arguments

- `y` *np.ndarray* - Mono waveform.
- `sr` *int* - Sampling rate (Hz).
- `window` *float, optional* - Window length in seconds. Defaults to 0.02.

#### Returns

- `tuple` - `(env, rate)` where `env` is the RMS envelope (one value per
    window) and `rate` its sampling rate (1 / `window` Hz).

## spectral_flux

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audiofeatures.py#L44)

```python
def spectral_flux(y, sr, nperseg=2048, noverlap=1536):
```

Spectral-flux onset-detection function: the positive first difference of
the STFT magnitude, summed over frequency and normalized to a maximum of
1. Rises sharply at note/percussion onsets.

Source: Westney-comparisons study (Jensenius).

#### Arguments

- `y` *np.ndarray* - Mono waveform.
- `sr` *int* - Sampling rate (Hz).
- `nperseg` *int, optional* - STFT window length in samples. Defaults to 2048.
- `noverlap` *int, optional* - STFT window overlap in samples. Defaults to 1536.

#### Returns

- `tuple` - `(flux, times)` where `flux` is the onset-detection function and
    `times` are its frame times in seconds (frame rate
    `sr / (nperseg - noverlap)`).

## spectral_flux_onsets

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audiofeatures.py#L72)

```python
def spectral_flux_onsets(
    y,
    sr,
    nperseg=2048,
    noverlap=1536,
    threshold=None,
    min_interval=0.05,
):
```

Onset times from the spectral-flux onset-detection function (see
[spectral_flux](#spectral_flux)), peak-picked with the canonical peak-picker. By default
the threshold adapts to the signal as mean + 1 standard deviation of the
flux, following the source study.

Source: Westney-comparisons study (Jensenius).

#### Arguments

- `y` *np.ndarray* - Mono waveform.
- `sr` *int* - Sampling rate (Hz).
- `nperseg` *int, optional* - STFT window length in samples. Defaults to 2048.
- `noverlap` *int, optional* - STFT window overlap in samples. Defaults to 1536.
- `threshold` *float, optional* - Absolute flux threshold (the flux has
    maximum 1). Defaults to None, which uses mean + std of the flux.
- `min_interval` *float, optional* - Minimum inter-onset interval (s).
    Defaults to 0.05.

#### Returns

- `np.ndarray` - Onset times in seconds.

## t60_backward_decay

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_audiofeatures.py#L139)

```python
def t60_backward_decay(
    y,
    sr,
    window=0.02,
    spans=((-5, -35), (-5, -25)),
    rerise_db=6.0,
):
```

T60-style reverberation time by an ISO-3382-inspired level-span
regression on the RMS envelope (without Schroeder backward
integration): the RMS envelope is converted to dB relative to its peak;
from the peak the decay is followed (stopping if the envelope re-rises
by more than `rerise_db` dB, marking a new onset), and T60 is estimated
by linear regression of the dB curve over the first available level
span -- by default -5 to -35 dB (a T30 measure, extrapolated x2),
falling back to -5 to -25 dB (T20, x3) when the deeper level is not
reached.

The constants (20 ms window, -5/-35 with -5/-25 fallback, 6 dB re-rise
stop) are PROVISIONAL defaults reimplemented from the cymbal-comparison
paper's method description.

Source: cymbal-comparison study (Jensenius) -- instrument decay of
damped vs undamped cymbal strokes.

#### Arguments

- `y` *np.ndarray* - Mono waveform of a decaying event (analysis starts at
    the envelope peak).
- `sr` *int* - Sampling rate (Hz).
- `window` *float, optional* - RMS window length (s). Defaults to 0.02.
- `spans` *tuple, optional* - Level spans (dB re. peak) to try in order,
    each a `(top, bottom)` pair. Defaults to ((-5, -35), (-5, -25)).
- `rerise_db` *float, optional* - Stop following the decay when the envelope
    re-rises this many dB above its running minimum. Defaults to 6.0.

#### Returns

- `tuple` - `(t60, span)` where `t60` is the estimated reverberation time in
    seconds (NaN if no span was usable) and `span` is the `(top, bottom)`
    pair actually used (None if none).

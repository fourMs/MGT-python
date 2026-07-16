# Physio

> Auto-generated documentation for [musicalgestures._physio](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_physio.py) module.

Physiology signal features for standstill / micromotion studies.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Physio
    - [respiration_rate](#respiration_rate)
    - [spectral_band_fractions](#spectral_band_fractions)

Two pure numpy/scipy surfaces ported from the "still standing" study:

* :func:`respiration_rate` -- windowed breathing rate (breaths per minute)
  from a respiration waveform, via band-pass filtering and a Welch spectral
  peak per window.
* :func:`spectral_band_fractions` -- the fraction of a signal's Welch power
  falling in each of a set of caller-supplied named frequency bands. This is
  the generic "cardiorespiratory QoM" spectral-composition diagnostic with
  the heart-rate/respiration bands supplied by the caller, so the function
  carries no dependency on any particular physiological sensor.

Source: still standing study (Jensenius) -- Deichman / Equivital physiology
analyses.

## respiration_rate

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_physio.py#L22)

```python
def respiration_rate(waveform, fs, band=(0.1, 0.6), window_s=30, step_s=30):
```

Windowed respiration rate (breaths per minute) from a breathing waveform.

Each analysis window is band-pass filtered to the respiration band and
its dominant frequency is taken as the Welch spectral peak inside that
band; the rate is that frequency times 60. Windows advance by ``step_s``
seconds. The default band ``(0.1, 0.6)`` Hz corresponds to about
6-36 breaths/min. Each window must contain at least 15 seconds of valid
samples for spectral estimation.

Source: still standing study (Jensenius), Deichman respiration analysis
(``compute_qom_resp``).

#### Arguments

- `waveform` *np.ndarray* - 1-D respiration/breathing waveform.
- `fs` *float* - Sampling rate in Hz.
- `band` *tuple, optional* - ``(low, high)`` respiration band in Hz.
    Defaults to ``(0.1, 0.6)``.
- `window_s` *float, optional* - Window length in seconds. Defaults to 30.
- `step_s` *float, optional* - Hop between windows in seconds. Defaults to
    30.

#### Returns

- `dict` - ``{"rate_bpm", "times_s", "median_bpm"}`` where ``rate_bpm`` is
    the per-window rate (breaths/min, ``nan`` for windows without a
    clear peak), ``times_s`` the window centre times in seconds, and
    ``median_bpm`` the median across valid windows.

## spectral_band_fractions

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_physio.py#L94)

```python
def spectral_band_fractions(
    signal,
    fs,
    bands,
    total_band=(0.1, 8.0),
    nperseg_s=20,
):
```

Fraction of a signal's power in each of a set of named frequency bands.

Estimates the Welch power spectrum and, for each named band in ``bands``,
returns that band's summed power divided by the summed power in
``total_band``. This is the generic spectral-composition diagnostic used
for the "cardiorespiratory QoM artifact" analysis (e.g. how much of a
chest-accelerometer QoM signal sits in a cardiac vs a respiration band),
with the bands supplied by the caller so there is no built-in dependence
on a heart-rate or respiration sensor. Power is bin-summed on the Welch
grid; the study source integrated with trapz, which yields nearly
identical results on the uniform frequency spacing of Welch.

Source: still standing study (Jensenius), Deichman chest-QoM
cardiorespiratory spectral-composition analysis (``deichman_full``).

#### Arguments

- `signal` *np.ndarray* - 1-D input signal.
- `fs` *float* - Sampling rate in Hz.
- `bands` *dict* - Mapping of band name to ``(low, high)`` in Hz, e.g.
    - ```{"cardiac"` - (0.9, 1.3), "resp": (0.12, 0.5)}``.
- `total_band` *tuple, optional* - ``(low, high)`` reference band whose
    power is the denominator. Defaults to ``(0.1, 8.0)``.
- `nperseg_s` *float, optional* - Welch segment length in seconds.
    Defaults to 20.

#### Returns

- `dict` - Mapping of each band name to its power fraction in ``[0, 1]``
    (``nan`` if the total band contains no power).

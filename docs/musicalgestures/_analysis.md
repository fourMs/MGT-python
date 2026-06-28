# Analysis

> Auto-generated documentation for [musicalgestures._analysis](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_analysis.py) module.

General-purpose signal and statistics utilities for analysing rhythmic and
periodic structure in motion and audio signals.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Analysis
    - [bandpass](#bandpass)
    - [circular_stats](#circular_stats)
    - [dominant_frequency](#dominant_frequency)
    - [rayleigh_test](#rayleigh_test)
    - [smooth](#smooth)
    - [synchrony](#synchrony)

These helpers are independent of the MgVideo/MgAudio classes and can be used on
any 1-D numpy signal (e.g. quantity-of-motion curves, body-part speeds, audio
onset envelopes).

## bandpass

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_analysis.py#L28)

```python
def bandpass(signal, lo, hi, fs, order=4):
```

Apply a zero-phase Butterworth band-pass filter to a signal.

#### Arguments

- `signal` *np.ndarray* - Input signal.
- `lo` *float* - Lower cutoff frequency (Hz).
- `hi` *float* - Upper cutoff frequency (Hz).
- `fs` *float* - Sampling rate of the signal (Hz).
- `order` *int, optional* - Filter order. Defaults to 4.

#### Returns

- `np.ndarray` - The filtered signal. Returns the input unchanged if the
    requested band is invalid for the given sampling rate.

## circular_stats

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_analysis.py#L79)

```python
def circular_stats(phases):
```

Compute circular mean direction and resultant vector length of a set of phases.

#### Arguments

- `phases` *np.ndarray* - Phase angles in radians.

#### Returns

- `tuple` - ``(R, mean_angle_deg)`` where ``R`` is the mean resultant length
    in [0, 1] (1 = perfectly concentrated, 0 = uniform) and
    ``mean_angle_deg`` is the mean direction in degrees [0, 360).

## dominant_frequency

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_analysis.py#L53)

```python
def dominant_frequency(signal, fps, fmin=0.5, fmax=8.0):
```

Find the dominant frequency of a signal within a frequency band using the FFT.

Useful for estimating, e.g., the dominant oscillation rate of a body part's
speed signal (steps per second in a dance).

#### Arguments

- `signal` *np.ndarray* - Input signal.
- `fps` *float* - Sampling rate of the signal (Hz, e.g. frames per second).
- `fmin` *float, optional* - Lowest frequency to consider (Hz). Defaults to 0.5.
- `fmax` *float, optional* - Highest frequency to consider (Hz). Defaults to 8.0.

#### Returns

- `float` - The dominant frequency (Hz) within [fmin, fmax], or 0.0 if the
    band contains no frequency bins.

## rayleigh_test

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_analysis.py#L98)

```python
def rayleigh_test(phases):
```

Rayleigh test for non-uniformity of circular data.

Tests the null hypothesis that the phases are uniformly distributed around
the circle. A small p-value indicates significant phase concentration
(i.e. consistent timing).

#### Arguments

- `phases` *np.ndarray* - Phase angles in radians.

#### Returns

- `tuple` - ``(Z, p)`` where ``Z`` is the Rayleigh statistic and ``p`` is the
    approximate p-value.

## smooth

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_analysis.py#L13)

```python
def smooth(x, w=5):
```

Smooth a 1-D signal with a moving average.

#### Arguments

- `x` *np.ndarray* - Input signal.
- `w` *int, optional* - Window size in samples. Defaults to 5.

#### Returns

- `np.ndarray` - Smoothed signal of the same length as the input.

## synchrony

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_analysis.py#L123)

```python
def synchrony(signal_a, signal_b, times_a=None, times_b=None):
```

Pearson correlation between two signals after alignment and normalisation.

If time vectors are supplied, ``signal_b`` is linearly resampled onto the
time base of ``signal_a`` before correlating. Both signals are min-max
normalised to [0, 1]. Useful for quantifying audio–motion synchrony (e.g.
audio onset strength vs. overall motion energy).

#### Arguments

- `signal_a` *np.ndarray* - First signal (reference time base).
- `signal_b` *np.ndarray* - Second signal.
- `times_a` *np.ndarray, optional* - Time stamps for ``signal_a``. Defaults to None.
- `times_b` *np.ndarray, optional* - Time stamps for ``signal_b``. Defaults to None.

#### Returns

- `float` - Pearson correlation coefficient in [-1, 1].

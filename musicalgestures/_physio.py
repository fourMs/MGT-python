"""
Physiology signal features for standstill / micromotion studies.

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
"""

import numpy as np


def respiration_rate(waveform, fs, *, band=(0.1, 0.6), window_s=30,
                     step_s=30):
    """
    Windowed respiration rate (breaths per minute) from a breathing waveform.

    Each analysis window is band-pass filtered to the respiration band and
    its dominant frequency is taken as the Welch spectral peak inside that
    band; the rate is that frequency times 60. Windows advance by ``step_s``
    seconds. The default band ``(0.1, 0.6)`` Hz corresponds to about
    6-36 breaths/min. Each window must contain at least 15 seconds of valid
    samples for spectral estimation.

    Source: still standing study (Jensenius), Deichman respiration analysis
    (``compute_qom_resp``).

    Args:
        waveform (np.ndarray): 1-D respiration/breathing waveform.
        fs (float): Sampling rate in Hz.
        band (tuple, optional): ``(low, high)`` respiration band in Hz.
            Defaults to ``(0.1, 0.6)``.
        window_s (float, optional): Window length in seconds. Defaults to 30.
        step_s (float, optional): Hop between windows in seconds. Defaults to
            30.

    Returns:
        dict: ``{"rate_bpm", "times_s", "median_bpm"}`` where ``rate_bpm`` is
            the per-window rate (breaths/min, ``nan`` for windows without a
            clear peak), ``times_s`` the window centre times in seconds, and
            ``median_bpm`` the median across valid windows.
    """
    from scipy.signal import butter, filtfilt, welch

    x = np.asarray(waveform, dtype=float)
    x = x[np.isfinite(x)]
    lo, hi = band
    nyq = fs / 2.0
    if len(x) < int(fs * window_s):
        # single short window: still attempt one estimate
        window_s = max(1.0, len(x) / fs)

    b, a = butter(2, [lo / nyq, hi / nyq], btype="band")
    xf = filtfilt(b, a, x - x.mean())

    win = int(fs * window_s)
    step = int(fs * step_s)
    win = max(win, 1)
    step = max(step, 1)

    rates = []
    times = []
    for start in range(0, max(len(xf) - win + 1, 1), step):
        seg = xf[start:start + win]
        if len(seg) < int(fs * 15):  # need at least 15 s for spectral estimation
            rates.append(np.nan)
            times.append((start + win / 2) / fs)
            continue
        nperseg = min(len(seg), int(fs * window_s))
        f, P = welch(seg, fs, nperseg=nperseg)
        mask = (f >= lo) & (f <= hi)
        if mask.any() and P[mask].sum() > 0:
            fpk = f[mask][np.argmax(P[mask])]
            rates.append(float(fpk * 60.0))
        else:
            rates.append(np.nan)
        times.append((start + win / 2) / fs)

    rate_bpm = np.array(rates, dtype=float)
    return dict(rate_bpm=rate_bpm, times_s=np.array(times, dtype=float),
                median_bpm=float(np.nanmedian(rate_bpm))
                if np.isfinite(rate_bpm).any() else np.nan)


def spectral_band_fractions(signal, fs, bands, *, total_band=(0.1, 8.0),
                            nperseg_s=20):
    """
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

    Args:
        signal (np.ndarray): 1-D input signal.
        fs (float): Sampling rate in Hz.
        bands (dict): Mapping of band name to ``(low, high)`` in Hz, e.g.
            ``{"cardiac": (0.9, 1.3), "resp": (0.12, 0.5)}``.
        total_band (tuple, optional): ``(low, high)`` reference band whose
            power is the denominator. Defaults to ``(0.1, 8.0)``.
        nperseg_s (float, optional): Welch segment length in seconds.
            Defaults to 20.

    Returns:
        dict: Mapping of each band name to its power fraction in ``[0, 1]``
            (``nan`` if the total band contains no power).
    """
    from scipy.signal import welch

    x = np.asarray(signal, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 8:
        return {name: np.nan for name in bands}
    nperseg = min(len(x), max(8, int(fs * nperseg_s)))
    f, P = welch(x - x.mean(), fs, nperseg=nperseg)
    tlo, thi = total_band
    total = P[(f >= tlo) & (f < thi)].sum()
    if total <= 0:
        return {name: np.nan for name in bands}
    out = {}
    for name, (lo, hi) in bands.items():
        out[name] = float(P[(f >= lo) & (f < hi)].sum() / total)
    return out

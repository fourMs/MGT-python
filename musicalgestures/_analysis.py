"""
General-purpose signal and statistics utilities for analysing rhythmic and
periodic structure in motion and audio signals.

These helpers are independent of the MgVideo/MgAudio classes and can be used on
any 1-D numpy signal (e.g. quantity-of-motion curves, body-part speeds, audio
onset envelopes).
"""

import numpy as np


def smooth(x, w=5):
    """
    Smooth a 1-D signal with a moving average.

    Args:
        x (np.ndarray): Input signal.
        w (int, optional): Window size in samples. Defaults to 5.

    Returns:
        np.ndarray: Smoothed signal of the same length as the input.
    """
    from scipy.ndimage import uniform_filter1d
    return uniform_filter1d(np.asarray(x, dtype=float), size=w)


def bandpass(signal, lo, hi, fs, order=4):
    """
    Apply a zero-phase Butterworth band-pass filter to a signal.

    Args:
        signal (np.ndarray): Input signal.
        lo (float): Lower cutoff frequency (Hz).
        hi (float): Upper cutoff frequency (Hz).
        fs (float): Sampling rate of the signal (Hz).
        order (int, optional): Filter order. Defaults to 4.

    Returns:
        np.ndarray: The filtered signal. Returns the input unchanged if the
            requested band is invalid for the given sampling rate.
    """
    from scipy.signal import butter, filtfilt
    signal = np.asarray(signal, dtype=float)
    nyq = fs / 2
    lo, hi = max(lo, 0.01), min(hi, nyq - 0.01)
    if lo >= hi:
        return signal
    b, a = butter(order, [lo / nyq, hi / nyq], btype="band")
    return filtfilt(b, a, signal)


def dominant_frequency(signal, fps, fmin=0.5, fmax=8.0):
    """
    Find the dominant frequency of a signal within a frequency band using the FFT.

    Useful for estimating, e.g., the dominant oscillation rate of a body part's
    speed signal (steps per second in a dance).

    Args:
        signal (np.ndarray): Input signal.
        fps (float): Sampling rate of the signal (Hz, e.g. frames per second).
        fmin (float, optional): Lowest frequency to consider (Hz). Defaults to 0.5.
        fmax (float, optional): Highest frequency to consider (Hz). Defaults to 8.0.

    Returns:
        float: The dominant frequency (Hz) within [fmin, fmax], or 0.0 if the
            band contains no frequency bins.
    """
    signal = np.asarray(signal, dtype=float)
    freqs = np.fft.rfftfreq(len(signal), d=1.0 / fps)
    fft = np.abs(np.fft.rfft(signal - signal.mean()))
    mask = (freqs >= fmin) & (freqs <= fmax)
    if not mask.any():
        return 0.0
    return float(freqs[mask][np.argmax(fft[mask])])


def circular_stats(phases):
    """
    Compute circular mean direction and resultant vector length of a set of phases.

    Args:
        phases (np.ndarray): Phase angles in radians.

    Returns:
        tuple: ``(R, mean_angle_deg)`` where ``R`` is the mean resultant length
            in [0, 1] (1 = perfectly concentrated, 0 = uniform) and
            ``mean_angle_deg`` is the mean direction in degrees [0, 360).
    """
    phases = np.asarray(phases, dtype=float)
    C, S = np.cos(phases).mean(), np.sin(phases).mean()
    R = float(np.sqrt(C ** 2 + S ** 2))
    mean_angle = float(np.degrees(np.arctan2(S, C)) % 360)
    return R, mean_angle


def rayleigh_test(phases):
    """
    Rayleigh test for non-uniformity of circular data.

    Tests the null hypothesis that the phases are uniformly distributed around
    the circle. A small p-value indicates significant phase concentration
    (i.e. consistent timing).

    Args:
        phases (np.ndarray): Phase angles in radians.

    Returns:
        tuple: ``(Z, p)`` where ``Z`` is the Rayleigh statistic and ``p`` is the
            approximate p-value.
    """
    phases = np.asarray(phases, dtype=float)
    n = len(phases)
    if n == 0:
        return 0.0, 1.0
    R, _ = circular_stats(phases)
    Z = n * R ** 2
    p = float(np.exp(-Z))
    return float(Z), p


def synchrony(signal_a, signal_b, times_a=None, times_b=None):
    """
    Pearson correlation between two signals after alignment and normalisation.

    If time vectors are supplied, ``signal_b`` is linearly resampled onto the
    time base of ``signal_a`` before correlating. Both signals are min-max
    normalised to [0, 1]. Useful for quantifying audio–motion synchrony (e.g.
    audio onset strength vs. overall motion energy).

    Args:
        signal_a (np.ndarray): First signal (reference time base).
        signal_b (np.ndarray): Second signal.
        times_a (np.ndarray, optional): Time stamps for ``signal_a``. Defaults to None.
        times_b (np.ndarray, optional): Time stamps for ``signal_b``. Defaults to None.

    Returns:
        float: Pearson correlation coefficient in [-1, 1].
    """
    a = np.asarray(signal_a, dtype=float)
    b = np.asarray(signal_b, dtype=float)

    if times_a is not None and times_b is not None:
        b = np.interp(times_a, times_b, b)
    elif len(a) != len(b):
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]

    def _norm01(x):
        return (x - x.min()) / (x.max() - x.min() + 1e-9)

    return float(np.corrcoef(_norm01(a), _norm01(b))[0, 1])

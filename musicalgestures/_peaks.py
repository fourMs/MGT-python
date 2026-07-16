"""
Canonical adaptive peak-picking for sound and motion signals.

This module provides the ONE peak-picker shared by the pulse, alignment,
quantity-of-motion and audio-feature modules (`_pulse`, `_alignment`,
`_qom`, `_audiofeatures`), so that every event-detection step in the
toolbox uses the same, well-tested convention: optional moving-average
smoothing, a relative (or absolute) amplitude threshold, a minimum
inter-peak interval, and an optional prominence gate.

The function is independent of the MgVideo/MgAudio classes and operates on
any 1-D numpy signal (audio onset-detection functions, quantity-of-motion
curves, wrist-speed signals, acceleration magnitudes, ...).
"""

import numpy as np


def pick_peaks(x, fs=1.0, smooth=3, rel_threshold=0.5, min_interval=0.3,
               rel_prominence=0.2, threshold=None, prominence=None):
    """
    Adaptive peak-picker: smoothing, relative threshold, minimum inter-peak
    interval, and an optional prominence gate.

    The processing chain is: (1) an optional short moving-average smoothing
    (`smooth` taps); (2) discard candidate maxima below an amplitude
    threshold, expressed as a fraction of the signal's peak
    (`rel_threshold`) or absolutely (`threshold`); (3) enforce a minimum
    inter-peak interval of `min_interval` seconds (stronger peaks win);
    (4) optionally require each peak to exceed its flanking local minima by
    a prominence, again expressed as a fraction of the signal's peak
    (`rel_prominence`) or absolutely (`prominence`).

    The default constants (3-tap smoothing, 0.50 x peak threshold, 0.30 s
    minimum interval, 0.20 x peak prominence) are the "selective" video
    quantity-of-motion settings from the cymbal-comparison study. A 2026
    revalidation on the original dataset (Zenodo 21360429) confirmed these
    prose constants as accurate; the deposited JSON summary's conflicting
    method string (0.25 x peak / 0.10 s) was found to be inconsistent with
    its own archived results. For reference, the same study used
    0.12 x peak / 0.10 s for hand-acceleration impacts, 0.15 x peak /
    0.06 s for audio energy onsets, and 0.40 x peak / 0.20 s for
    wrist-speed peaks. Tune the parameters to your signal at hand.

    Source: cymbal-comparison study (Jensenius), reimplemented from the
    paper's method description; also subsumes the peak-picking conventions
    of the Westney-comparisons and ro studies.

    Args:
        x (np.ndarray): Input 1-D signal.
        fs (float, optional): Sampling rate of the signal (Hz). Defaults to 1.0
            (i.e. `min_interval` is then expressed in samples).
        smooth (int, optional): Length of the moving-average smoothing window in
            samples (taps). None, 0 or 1 disables smoothing. Defaults to 3.
        rel_threshold (float, optional): Amplitude threshold as a fraction of the
            (smoothed) signal's maximum. None disables the threshold. Defaults to 0.5.
        min_interval (float, optional): Minimum inter-peak interval in seconds
            (given `fs`). Defaults to 0.3.
        rel_prominence (float, optional): Required peak prominence as a fraction of
            the (smoothed) signal's maximum. None disables the gate. Defaults to 0.2.
        threshold (float, optional): Absolute amplitude threshold. Overrides
            `rel_threshold` when given. Defaults to None.
        prominence (float, optional): Absolute prominence requirement. Overrides
            `rel_prominence` when given. Defaults to None.

    Returns:
        np.ndarray: Integer sample indices of the detected peaks (divide by `fs`
            for times in seconds).
    """
    from scipy.signal import find_peaks
    from scipy.ndimage import uniform_filter1d

    x = np.asarray(x, dtype=float)
    if len(x) < 3:
        return np.array([], dtype=int)

    if smooth is not None and smooth > 1:
        x = uniform_filter1d(x, size=int(smooth))

    peak = float(np.max(x))
    height = threshold if threshold is not None else (
        rel_threshold * peak if rel_threshold is not None else None)
    prom = prominence if prominence is not None else (
        rel_prominence * peak if rel_prominence is not None else None)
    distance = max(1, int(round(min_interval * fs))) if min_interval else 1

    idx, _ = find_peaks(x, height=height, distance=distance, prominence=prom)
    return idx

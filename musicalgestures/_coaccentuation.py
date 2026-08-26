"""Co-accentuation: do motion accents land on sound accents?

From Serdar and Jensenius, *Mixed Method Audio-Video Analyses of Felt Togetherness in a
Networked Music-Dance Performance*, MOCO '26. Each motion peak is tested for an audio onset
within a tolerance; the fraction that coincide is the **Global Co-Accentuation Index**, and
a curve over short windows shows whether synchrony came in bursts or was sustained.

This is the measure for the question underneath a project like this one: not whether motion
and sound rise together on average, which a correlation answers, but whether the *moments*
line up.

**Why the chance baseline is not optional.** The index is a raw fraction, and fractions of
coincidence rise with density: sprinkle enough onsets over a recording and every motion
peak has one within 150 ms whether or not anything is coordinated. An index of 0.8 means
nothing until you know what 0.8 would have been by accident. The null here is a circular
shift of the onsets, which preserves how many there are and their rhythm, and destroys only
their relationship to the motion. Both the observed index and what the null gives are
returned, and a claim rests on the difference rather than on the index alone.

**The measure is asymmetric, deliberately.** It asks what fraction of MOTION peaks found a
sound, not the reverse. A dancer moving twice to one sound is a different thing from a
musician playing twice to one movement, and a symmetric measure would hide which happened.
Swap the arguments to ask the other question.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["CoAccentuation", "co_accentuation", "co_accentuation_curve"]


@dataclass
class CoAccentuation:
    """The result of a co-accentuation test.

    Attributes:
        gci (float): Global Co-Accentuation Index --- the fraction of motion peaks with an
            onset within the tolerance. NaN when there were no peaks, because "nothing was
            coordinated" and "nothing was asked" are different answers.
        n_peaks (int): How many motion peaks were tested.
        n_matched (int): How many found an onset.
        expected_gci (float): The mean index over the circular-shift null. What this
            recording's density buys by accident.
        z (float): How many null standard deviations the observed index sits above the
            null mean.
        p (float): Fraction of null draws reaching the observed index. This is the number a
            claim rests on.
        tolerance_s (float): The window used, echoed back so a figure can state it.
    """

    gci: float
    n_peaks: int
    n_matched: int
    expected_gci: float
    z: float
    p: float
    tolerance_s: float


def _matched(peaks: np.ndarray, onsets: np.ndarray, tol: float) -> int:
    """How many peaks have an onset within `tol`. Onsets may serve several peaks."""
    if len(peaks) == 0 or len(onsets) == 0:
        return 0
    idx = np.searchsorted(onsets, peaks)
    best = np.full(len(peaks), np.inf)
    left = np.clip(idx - 1, 0, len(onsets) - 1)
    right = np.clip(idx, 0, len(onsets) - 1)
    best = np.minimum(np.abs(peaks - onsets[left]), np.abs(peaks - onsets[right]))
    #: `<=` and not `<`: an onset exactly at the tolerance is inside the window a reader
    #: was told about.
    return int((best <= tol).sum())


def co_accentuation(motion_peaks, audio_onsets, duration_s: float,
                    tolerance_s: float = 0.15, n_null: int = 200,
                    seed: int = 0) -> CoAccentuation:
    """Test whether motion peaks coincide with audio onsets more than by chance.

    Args:
        motion_peaks: Times of motion accents, in seconds.
        audio_onsets: Times of audio onsets, in seconds.
        duration_s (float): Length of the recording, needed to wrap the null's shifts.
        tolerance_s (float): How close counts as coincident. Defaults to 0.15, the value
            used in the paper this comes from.
        n_null (int): Circular-shift draws for the null. Defaults to 200.
        seed (int): For the shifts, so a reported p-value can be reproduced.

    Returns:
        CoAccentuation: The index, the null it is judged against, and the p-value.
    """
    peaks = np.sort(np.asarray(motion_peaks, dtype=float).ravel())
    onsets = np.sort(np.asarray(audio_onsets, dtype=float).ravel())
    n = len(peaks)
    if n == 0:
        return CoAccentuation(float("nan"), 0, 0, float("nan"), float("nan"),
                              float("nan"), tolerance_s)

    matched = _matched(peaks, onsets, tolerance_s)
    gci = matched / n

    if len(onsets) == 0 or duration_s <= 0 or n_null <= 0:
        return CoAccentuation(gci, n, matched, float("nan"), float("nan"),
                              float("nan"), tolerance_s)

    rng = np.random.default_rng(seed)
    null = np.empty(n_null)
    for i in range(n_null):
        shifted = np.sort((onsets + rng.uniform(0, duration_s)) % duration_s)
        null[i] = _matched(peaks, shifted, tolerance_s) / n
    mu, sd = float(null.mean()), float(null.std())
    z = (gci - mu) / sd if sd > 0 else float("nan")
    #: (count + 1) / (n + 1): a permutation p is never 0, because one more draw might
    #: have reached it.
    p = float((np.sum(null >= gci) + 1) / (n_null + 1))
    return CoAccentuation(gci, n, matched, mu, z, p, tolerance_s)


def co_accentuation_curve(motion_peaks, audio_onsets, duration_s: float,
                          window_s: float = 5.0, step_s: float = 1.0,
                          tolerance_s: float = 0.15):
    """The index over sliding windows, to see whether synchrony was sustained or bursty.

    Args:
        motion_peaks: Times of motion accents, in seconds.
        audio_onsets: Times of audio onsets, in seconds.
        duration_s (float): Length of the recording.
        window_s (float): Window length. Defaults to 5.0, as in the paper.
        step_s (float): Step between windows. Defaults to 1.0.
        tolerance_s (float): How close counts as coincident. Defaults to 0.15.

    Returns:
        tuple: Window start times, and the index in each. A window containing no motion
        peaks is **NaN, not zero**: it has no synchrony to report, which is not the same as
        having looked and found none.
    """
    peaks = np.sort(np.asarray(motion_peaks, dtype=float).ravel())
    onsets = np.sort(np.asarray(audio_onsets, dtype=float).ravel())
    starts = np.arange(0.0, max(0.0, duration_s - window_s) + 1e-9, step_s)
    out = np.full(len(starts), np.nan)
    for i, s in enumerate(starts):
        sel = peaks[(peaks >= s) & (peaks < s + window_s)]
        if len(sel) == 0:
            continue
        out[i] = _matched(sel, onsets, tolerance_s) / len(sel)
    return starts, out

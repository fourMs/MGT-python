"""Do the events of one stream fall near the events of another, and which comes first?

`_alignment` and `_correlate` compare envelopes. This compares *events*: stroke onsets against
note onsets, footfalls against beats, looks against cues. The question is the one gesture
research asks of apexes and pitch accents --- how far is each event of one stream from the
nearest event of the other, and on which side --- asked without assuming a beat.

The test is against chance. Two dense streams have small nearest-event distances whatever
they do, so every distance is compared with the same statistic for reference events placed
uniformly at random over the recording, many times. A median distance *below* the surrogate
median means the events attract (they coincide); one *above* it means they avoid each other
(one stream is active in the other's gaps), and both are findings. On the painter--pianist
session this was written for, the free take showed avoidance (strokes in the piano's silences),
the painter-led take chance, and the pianist-led take attraction, which no envelope
correlation had separated.

The signed lag of the nearest reference event says which came first, event by event, and
the cross-correlation of the two event trains, binned, gives the lag at which they co-occur.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["EventAlignment", "event_alignment", "event_xcorr"]


@dataclass
class EventAlignment:
    """What :func:`event_alignment` found.

    Attributes:
        n_events (int): Events tested.
        n_reference (int): Reference events.
        nearest_s (numpy.ndarray): Distance from each event to the nearest reference, seconds.
        signed_lag_s (numpy.ndarray): Nearest reference minus event, seconds; negative means the
            reference came first.
        median_nearest_s (float): Median of `nearest_s`.
        surrogate_median_s (float): Mean over surrogates of the same median.
        p_closer (float): Share of surrogates at least as close: small when events attract.
        p_farther (float): Share of surrogates at least as far: small when events avoid.
        frac_within (float): Share of events within `tolerance_s` of a reference.
        frac_reference_first (float): Share of events whose nearest reference came earlier.
        tolerance_s (float): The tolerance used for `frac_within`.
        features (dict): Free-form extras.
    """
    n_events: int
    n_reference: int
    nearest_s: np.ndarray
    signed_lag_s: np.ndarray
    median_nearest_s: float
    surrogate_median_s: float
    p_closer: float
    p_farther: float
    frac_within: float
    frac_reference_first: float
    tolerance_s: float
    features: dict = field(default_factory=dict)

    @property
    def verdict(self) -> str:
        """``"attract"``, ``"avoid"`` or ``"chance"`` at the 5 per cent level."""
        if self.p_closer < 0.05:
            return "attract"
        if self.p_farther < 0.05:
            return "avoid"
        return "chance"


def _nearest(events: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    idx = np.searchsorted(reference, events)
    lo = np.clip(idx - 1, 0, len(reference) - 1)
    hi = np.clip(idx, 0, len(reference) - 1)
    d_lo = np.abs(events - reference[lo])
    d_hi = np.abs(events - reference[hi])
    pick = np.where(d_hi < d_lo, hi, lo)
    signed = reference[pick] - events
    return np.abs(signed), signed


def event_alignment(events, reference, duration_s: float, tolerance_s: float = 0.25,
                    n_surrogates: int = 300, seed: int = 0) -> EventAlignment:
    """How close the events of one stream fall to the events of another, against chance.

    Args:
        events: Event times in seconds (the stream asked about, e.g. strokes).
        reference: Reference event times in seconds (e.g. note onsets).
        duration_s (float): Length of the recording, over which surrogate references are drawn.
        tolerance_s (float): Window for `frac_within`. Defaults to 0.25 s.
        n_surrogates (int): Random reference sets. Defaults to 300.
        seed (int): For the surrogates.

    Returns:
        EventAlignment: The distances, signed lags and surrogate comparison. With no events or
        no references the arrays are empty and the p-values 1.0 --- nothing to align is not an
        error, but it is not a result either, and the counts say which it was.
    """
    ev = np.sort(np.asarray(events, dtype=float))
    ref = np.sort(np.asarray(reference, dtype=float))
    if len(ev) == 0 or len(ref) == 0:
        return EventAlignment(len(ev), len(ref), np.array([]), np.array([]), float("nan"), float("nan"),
                              1.0, 1.0, float("nan"), float("nan"), tolerance_s)
    d, signed = _nearest(ev, ref)
    med = float(np.median(d))
    rng = np.random.default_rng(seed)
    sur = np.array([np.median(_nearest(ev, np.sort(rng.uniform(0.0, duration_s, len(ref))))[0])
                    for _ in range(n_surrogates)])
    p_closer = float((np.sum(sur <= med) + 1) / (n_surrogates + 1))
    p_farther = float((np.sum(sur >= med) + 1) / (n_surrogates + 1))
    return EventAlignment(
        n_events=len(ev), n_reference=len(ref), nearest_s=d, signed_lag_s=signed, median_nearest_s=med,
        surrogate_median_s=float(sur.mean()), p_closer=p_closer, p_farther=p_farther,
        frac_within=float(np.mean(d <= tolerance_s)), frac_reference_first=float(np.mean(signed < 0)),
        tolerance_s=tolerance_s, features={"surrogate_medians": sur},
    )


def event_xcorr(events, reference, duration_s: float, bin_s: float = 0.1, max_lag_s: float = 3.0):
    """Cross-correlation of two event trains, binned.

    Args:
        events, reference: Event times in seconds.
        duration_s (float): Recording length.
        bin_s (float): Bin width. Defaults to 0.1 s.
        max_lag_s (float): Lag range. Defaults to ±3 s.

    Returns:
        tuple: ``(lags_s, r)``; positive lag means the reference train follows the events.
    """
    n = int(duration_s / bin_s) + 1
    a = np.bincount(np.clip((np.asarray(events, float) / bin_s).astype(int), 0, n - 1), minlength=n).astype(float)
    b = np.bincount(np.clip((np.asarray(reference, float) / bin_s).astype(int), 0, n - 1), minlength=n).astype(float)
    a = (a - a.mean()) / (a.std() + 1e-12)
    b = (b - b.mean()) / (b.std() + 1e-12)
    L = int(max_lag_s / bin_s)
    lags = np.arange(-L, L + 1)
    r = np.empty(len(lags))
    for i, l in enumerate(lags):
        if l >= 0:
            x, y = a[:n - l], b[l:]
        else:
            x, y = a[-l:], b[:n + l]
        r[i] = float(np.mean(x * y)) if len(x) > 10 else np.nan
    return lags * bin_s, r

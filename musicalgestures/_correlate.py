"""Correlation between two series across a range of lags.

**Why this exists.** A zero-lag correlation asks whether two things rise and fall
together at the same instant. That is rarely the question. This project's underlying
question --- when does an action begin relative to the sound it makes --- is entirely
about displacement in time, and a relationship offset by a second is invisible to a
correlation computed where the two series happen to sit.

**The sign convention, stated once.** A positive lag means `y` **follows** `x`. If the
motion comes two seconds after the sound, `best_lag_s` is `+2.0`. Get this backwards and
every conclusion inverts, so it is asserted in both directions in the tests.

**Why the p-value is corrected.** Scanning many lags and reporting the best one is a
multiple comparison. With enough lags, some pair of unrelated series will always show a
healthy-looking r somewhere, and quoting its uncorrected p would be a false positive
dressed as a finding. Both are returned, and the corrected one is what a claim rests on.

The correction is Bonferroni over the number of lags examined, which is **conservative**:
neighbouring lags of a smooth series are far from independent, so the true number of
independent tests is smaller than `n_lags` and the real p lies between the two reported
values. Conservative is the right direction to err when the purpose is checking a claim
rather than making one.

**Why the sample size is discounted too.** Bonferroni handles scanning many lags. It does
nothing about the other inflation, which is larger: consecutive samples of a smooth series
are not independent observations. One-second bins of a motion envelope are mostly a copy
of the bin before, so treating n bins as n observations inflates every t statistic and
turns autocorrelated noise into a finding. `n_effective` discounts the length by how much
each series repeats itself, after Bartlett, and the reported p-values use it. On this
project's corpus that was not academic: one session's best lag moved from p < 0.001 to
p = 1.0 once the effective size was used.

Ported from `xcov()` in https://github.com/finn42/Laughter_Dance by Finn Upham,
accompanying Upham et al., *Frontiers in Psychology* 2026,
doi:10.3389/fpsyg.2026.1754425. The sign convention and the multiple-comparison
correction are additions; the idea of sweeping the lag is theirs.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

__all__ = ["LaggedCorrelation", "lagged_correlation"]


@dataclass
class LaggedCorrelation:
    """The result of sweeping a correlation across lags.

    Attributes:
        lags_s (np.ndarray): The lags examined, in seconds, ascending. Positive means
            `y` follows `x`.
        r (np.ndarray): Pearson correlation at each lag, aligned with `lags_s`.
        best_lag_s (float): The lag of the strongest correlation, by absolute value.
        best_r (float): The correlation there. NaN when either series is constant.
        p_uncorrected (float): Two-sided p for `best_r` alone, ignoring that lags were
            scanned. Reported so the two can be compared, not so it can be quoted.
        p_corrected (float): `p_uncorrected` after Bonferroni over `n_lags`. This is the
            one a claim rests on.
        n_lags (int): How many lags were examined.
        n_overlap (int): Samples overlapping at `best_lag_s`, which is fewer than the
            series length whenever the lag is not zero.
        n_effective (float): `n_overlap` discounted for autocorrelation, and the sample
            size both p-values are actually computed from. Equals `n_overlap` for white
            noise and falls well below it for anything smooth.
    """

    lags_s: np.ndarray
    r: np.ndarray
    best_lag_s: float
    best_r: float
    p_uncorrected: float
    p_corrected: float
    n_lags: int
    n_overlap: int
    n_effective: float


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r, or NaN where it is undefined rather than a number that looks fine."""
    if len(a) < 3:
        return float("nan")
    sa, sb = a.std(), b.std()
    if sa == 0 or sb == 0:
        return float("nan")
    return float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))


def _ar1(v: np.ndarray) -> float:
    """Lag-one autocorrelation, the single number Bartlett's discount needs."""
    d = v - v.mean()
    denom = float((d * d).sum())
    if denom == 0:
        return 0.0
    return float((d[:-1] * d[1:]).sum() / denom)


def _effective_n(a: np.ndarray, b: np.ndarray) -> float:
    """How many independent observations two autocorrelated series are worth.

    Bartlett's first-order approximation: n * (1 - p1*p2) / (1 + p1*p2), where p1 and p2
    are the lag-one autocorrelations. Two series that each repeat themselves strongly
    carry far less information than their length suggests. Clamped to the length above
    and to 3 below, since a t test needs at least that.
    """
    p1, p2 = _ar1(a), _ar1(b)
    prod = max(-0.99, min(0.99, p1 * p2))
    return float(min(len(a), max(3.0, len(a) * (1 - prod) / (1 + prod))))


def lagged_correlation(x, y, fs: float, max_lag_s: float) -> LaggedCorrelation:
    """Correlate `x` against `y` at every lag out to `max_lag_s`.

    Args:
        x: First series, one dimension.
        y: Second series, same length as `x`.
        fs (float): Sampling rate of both series, in samples per second.
        max_lag_s (float): Largest lag to examine, in seconds, in both directions.

    Returns:
        LaggedCorrelation: The sweep, its peak, and both p-values.

    Raises:
        ValueError: If the series differ in length, or `fs` is not positive.
    """
    a = np.asarray(x, dtype=float).ravel()
    b = np.asarray(y, dtype=float).ravel()
    if len(a) != len(b):
        raise ValueError(f"series must be the same length, got {len(a)} and {len(b)}")
    if fs <= 0:
        raise ValueError(f"fs must be positive, got {fs}")

    n = len(a)
    max_k = min(int(round(max_lag_s * fs)), n - 1)
    ks = np.arange(-max_k, max_k + 1)

    rs = np.empty(len(ks), dtype=float)
    overlaps = np.empty(len(ks), dtype=int)
    for i, k in enumerate(ks):
        #: r[k] compares x[t] with y[t + k], so a positive k tests whether y, read
        #: later, matches x read now --- that is, whether y follows x.
        if k >= 0:
            u, v = a[:n - k], b[k:]
        else:
            u, v = a[-k:], b[:n + k]
        overlaps[i] = len(u)
        rs[i] = _pearson(u, v)

    if np.all(np.isnan(rs)):
        return LaggedCorrelation(lags_s=ks / fs, r=rs, best_lag_s=float("nan"),
                                 best_r=float("nan"), p_uncorrected=float("nan"),
                                 p_corrected=float("nan"), n_lags=len(ks), n_overlap=0,
                                 n_effective=0.0)

    best = int(np.nanargmax(np.abs(rs)))
    best_r = float(rs[best])
    n_ov = int(overlaps[best])
    k_best = int(ks[best])

    #: Two-sided t test on r, with the EFFECTIVE size rather than the raw one. An |r| of
    #: exactly 1 gives an infinite t and a p of 0, which is correct and needs no case.
    if k_best >= 0:
        u_b, v_b = a[:n - k_best], b[k_best:]
    else:
        u_b, v_b = a[-k_best:], b[:n + k_best]
    n_eff = _effective_n(u_b, v_b)
    if n_eff > 2 and abs(best_r) < 1.0:
        t = best_r * np.sqrt((n_eff - 2) / (1 - best_r ** 2))
        p_unc = float(2 * stats.t.sf(abs(t), df=n_eff - 2))
    elif abs(best_r) >= 1.0:
        p_unc = 0.0
    else:
        p_unc = float("nan")

    p_cor = min(1.0, p_unc * len(ks)) if np.isfinite(p_unc) else float("nan")

    return LaggedCorrelation(lags_s=ks / fs, r=rs, best_lag_s=float(ks[best] / fs),
                             best_r=best_r, p_uncorrected=p_unc, p_corrected=p_cor,
                             n_lags=len(ks), n_overlap=n_ov, n_effective=n_eff)

"""
Audio--motion (and stream-to-stream) alignment tools.

Lead/lag estimation by cross-correlation, per-cycle motion-onset deltas,
anchor-and-match relative event alignment with offset statistics,
sliding-window coupling, and N-source envelope agreement.

These functions are independent of the MgVideo/MgAudio classes and operate
on plain numpy arrays (envelopes, onset/event time lists).

Sources: ro study, cymbal-comparison study and Westney-comparisons study
(Jensenius).
"""

import numpy as np

from musicalgestures._qom import envelope


def xcorr_lag(x, y, fs, max_lag=1.5):
    """
    Canonical lead/lag estimate between two signals by vectorized
    cross-correlation: the lag of `y` relative to `x` that maximizes their
    correlation, searched within +/- `max_lag` seconds. Positive lag means
    `y` happens after `x`.

    Both signals are mean-removed and the correlation is normalized to a
    Pearson-like coefficient over the full window. Among near-tied maxima
    (common for periodic envelopes, where peaks recur at +/- one period),
    the smallest-magnitude lag is returned rather than an arbitrary aliased
    one.

    Source: Westney-comparisons study (Jensenius) -- camera/audio residual
    sync by onset-envelope cross-correlation; unified with the ro study's
    `envelope_lag`.

    Args:
        x (np.ndarray): Reference 1-D signal.
        y (np.ndarray): Comparison 1-D signal (same sampling rate).
        fs (float): Sampling rate of both signals (Hz).
        max_lag (float, optional): Maximum absolute lag to search (s). Defaults to 1.5.

    Returns:
        tuple: `(lag, r)` where `lag` is the lag of `y` relative to `x` in
            seconds (positive = `y` later) and `r` is the normalized correlation
            at that lag.
    """
    from scipy.signal import correlate, correlation_lags
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = min(len(x), len(y))
    x, y = x[:n] - x[:n].mean(), y[:n] - y[:n].mean()
    cc = correlate(y, x, mode="full")
    lags = correlation_lags(n, n, mode="full")
    m = np.abs(lags) <= max(1, int(round(max_lag * fs)))
    cc, lags = cc[m], lags[m]
    cc = cc / (n * x.std() * y.std() + 1e-12)
    # Near-exact ties are floating-point noise; prefer the smallest |lag|.
    cand = np.flatnonzero(cc >= cc.max() - 1e-9)
    best = cand[np.argmin(np.abs(lags[cand]))]
    return lags[best] / fs, float(cc[best])


def envelope_lag(x, y, rate, max_lag_s=1.5):
    """
    Lag (s) of `y` relative to `x` maximizing their correlation. Positive
    lag = `y` happens after `x`. Thin wrapper around `xcorr_lag`, kept as
    the ro study's interface for envelope-to-envelope lags (e.g. voice
    envelope vs motion envelope).

    Source: ro study (Jensenius).

    Args:
        x (np.ndarray): Reference envelope.
        y (np.ndarray): Comparison envelope (same sampling rate).
        rate (float): Sampling rate of both envelopes (Hz).
        max_lag_s (float, optional): Maximum absolute lag to search (s). Defaults to 1.5.

    Returns:
        tuple: `(lag, r)` as in `xcorr_lag`.
    """
    return xcorr_lag(x, y, rate, max_lag=max_lag_s)


def per_cycle_motion_delta(cycle_starts, motion_times, lookback=0.3):
    """
    For each cycle, the time of its assigned motion onset minus the
    cycle start (NaN if none). Each cycle's natural window is
    [start-lookback, next_start): the lookback lets a motion onset that
    anticipates this cycle's stroke be credited to it, while the
    unshifted upper bound at next_start lets genuine post-onset motion
    (motion after the cycle's own stroke) be credited too.

    Because windows overlap by up to `lookback`, a single motion onset
    can fall in two consecutive cycles' windows. To avoid double-
    counting (and to stop a slow cycle from "stealing" a fast cycle's
    only motion onset when IOI < lookback), cycles are processed in
    DESCENDING time order and each claims the unclaimed motion onset
    still inside its window that is NEAREST to its own cycle start
    (ties broken toward the earlier onset), marking it claimed.
    A cyclic gesture can plausibly produce two motion peaks per slow
    cycle: a forward-stroke peak close to the sound onset and a later
    return-stroke peak near the tail of the cycle's window. The
    forward-stroke response to the sound is the one of interest, so
    nearest-to-start assignment credits that one to the cycle instead
    of the return-stroke peak that a latest-wins rule would grab.
    Processing cycles in descending order still ensures a fast climax
    cycle can secure its own motion onset before an earlier, slower
    cycle's wider (lookback-only) window claims it instead.

    Source: ro study (Jensenius) -- rowing-gesture onsets vs drum cycles.

    Args:
        cycle_starts (np.ndarray): Cycle start times (s), ascending.
        motion_times (np.ndarray): Motion onset times (s), any order.
        lookback (float, optional): How far before its start a cycle may claim
            a motion onset (s). Defaults to 0.3.

    Returns:
        np.ndarray: One delta (s) per cycle: assigned motion onset time minus
            cycle start, NaN where no onset was assigned.
    """
    cycle_starts = np.asarray(cycle_starts, float)
    motion_times = np.sort(np.asarray(motion_times, float))
    ends = np.append(cycle_starts[1:], np.inf)
    claimed = np.zeros(len(motion_times), dtype=bool)
    out = np.full(len(cycle_starts), np.nan)
    for i in range(len(cycle_starts) - 1, -1, -1):
        s, e = cycle_starts[i], ends[i]
        in_window = (motion_times >= s - lookback) & (motion_times < e) & ~claimed
        idx = np.flatnonzero(in_window)
        if len(idx):
            j = idx[np.argmin(np.abs(motion_times[idx] - s))]
            claimed[j] = True
            out[i] = motion_times[j] - s
    return out


def anchor_and_match(times_a, times_b, anchor_a=None, anchor_b=None,
                     weights_a=None, weights_b=None, window=0.15):
    """
    Per-take relative event alignment between two streams with independent
    clocks: both streams are shifted so that their anchor events -- by
    default the strongest event of each stream, physically the same moment
    (e.g. the hardest strike) -- sit at t = 0; then every non-anchor event
    of stream `a` is matched to the nearest event of stream `b` within
    +/- `window` seconds, and the signed offset (`b` minus `a`; positive =
    `b` later) is recorded. The anchor pair contributes an offset of 0 by
    construction and is excluded. No absolute cross-stream synchronisation
    is claimed: the result measures whether the two streams agree on the
    RELATIVE timing of the remaining events.

    The default matching window of 0.15 s is a PROVISIONAL default,
    reimplemented from the cymbal-comparison paper's method description.

    Source: cymbal-comparison study (Jensenius) -- audio-onset vs kinematic-
    impact (and video/pose) timing agreement without a common clock.

    Args:
        times_a (np.ndarray): Event times (s) of stream a (e.g. kinematic impacts).
        times_b (np.ndarray): Event times (s) of stream b (e.g. audio onsets).
        anchor_a (float, optional): Anchor time in stream a. Defaults to None.
        anchor_b (float, optional): Anchor time in stream b. Defaults to None.
        weights_a (np.ndarray, optional): Event strengths for stream a, used to
            pick the anchor (argmax) when `anchor_a` is None. Defaults to None.
        weights_b (np.ndarray, optional): Event strengths for stream b, used to
            pick the anchor (argmax) when `anchor_b` is None. Defaults to None.
        window (float, optional): Maximum absolute offset (s) for a match.
            Defaults to 0.15.

    Returns:
        np.ndarray: Signed offsets (s), one per matched non-anchor event of
            stream a (`b` minus `a`).

    Raises:
        ValueError: If an anchor can be determined for neither stream (no
            anchor time and no weights given).
    """
    times_a = np.asarray(times_a, float)
    times_b = np.asarray(times_b, float)

    def pick_anchor(times, anchor, weights, name):
        if anchor is not None:
            return float(anchor)
        if weights is not None:
            return float(times[int(np.argmax(weights))])
        raise ValueError(
            f"anchor_and_match: provide anchor_{name} or weights_{name} "
            f"to determine the anchor event of stream {name}")

    a0 = pick_anchor(times_a, anchor_a, weights_a, "a")
    b0 = pick_anchor(times_b, anchor_b, weights_b, "b")
    a = times_a - a0
    b = times_b - b0
    a = a[np.abs(a) > 1e-12]        # exclude the anchor itself
    if len(a) == 0 or len(b) == 0:
        return np.array([])
    offsets = []
    for t in a:
        j = int(np.argmin(np.abs(b - t)))
        if abs(b[j] - t) <= window:
            offsets.append(b[j] - t)
    return np.asarray(offsets, float)


def offset_stats(offsets):
    """
    Summary statistics of a signed-offset distribution (s), as reported for
    anchor-and-match timing agreement.

    Source: cymbal-comparison study (Jensenius).

    Args:
        offsets (np.ndarray): Signed offsets (s), e.g. from `anchor_and_match`.

    Returns:
        dict: `n`, `median`, `mean`, `std`, `iqr` (interquartile range),
            `abs_median` (median absolute offset), `min` and `max`; statistics
            are NaN when `n` is 0.
    """
    offsets = np.asarray(offsets, float)
    offsets = offsets[np.isfinite(offsets)]
    if len(offsets) == 0:
        nan = float("nan")
        return dict(n=0, median=nan, mean=nan, std=nan, iqr=nan,
                    abs_median=nan, min=nan, max=nan)
    q1, q3 = np.percentile(offsets, [25, 75])
    return dict(
        n=int(len(offsets)),
        median=float(np.median(offsets)),
        mean=float(np.mean(offsets)),
        std=float(np.std(offsets)),
        iqr=float(q3 - q1),
        abs_median=float(np.median(np.abs(offsets))),
        min=float(np.min(offsets)),
        max=float(np.max(offsets)),
    )


def sliding_correlation(x, y, fs, window=10.0, step=2.0, min_std=1e-6):
    """
    Local (windowed) Pearson correlation profile between two signals:
    correlation within sliding windows of `window` seconds, hopped by
    `step` seconds. Windows where either signal is (near-)constant yield
    NaN. Useful for testing whether two streams that are uncorrelated
    globally couple locally (e.g. motion effort vs loudness).

    Source: Westney-comparisons study (Jensenius) -- local motion-loudness
    coupling in 10 s windows.

    Args:
        x (np.ndarray): First 1-D signal.
        y (np.ndarray): Second 1-D signal (same sampling rate).
        fs (float): Sampling rate of both signals (Hz).
        window (float, optional): Window length (s). Defaults to 10.0.
        step (float, optional): Hop between windows (s). Defaults to 2.0.
        min_std (float, optional): Minimum in-window standard deviation for a
            valid correlation. Defaults to 1e-6.

    Returns:
        tuple: `(times, r)` where `times` are the window centres (s) and `r`
            the windowed correlations (NaN where undefined).
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = min(len(x), len(y))
    W = max(2, int(round(window * fs)))
    S = max(1, int(round(step * fs)))
    times, r = [], []
    for s0 in range(0, n - W + 1, S):
        a, b = x[s0:s0 + W], y[s0:s0 + W]
        times.append((s0 + W / 2) / fs)
        if a.std() > min_std and b.std() > min_std:
            r.append(float(np.corrcoef(a, b)[0, 1]))
        else:
            r.append(np.nan)
    return np.asarray(times), np.asarray(r)


def envelope_agreement(signals, fs, smooth=1.0):
    """
    Agreement among N parallel envelopes (e.g. per-camera-angle quantity-of-
    motion curves of the same performance): the signals are truncated to
    their common length, smoothed and z-scored (see
    `musicalgestures.envelope`), and their Pearson correlation matrix is
    computed. The mean off-diagonal correlation summarises how well the
    sources agree.

    Source: Westney-comparisons study (Jensenius) -- cross-view agreement of
    five camera angles' motion envelopes.

    Args:
        signals (sequence): Sequence of N 1-D arrays (possibly of different
            lengths), or a 2-D array of shape (N, T).
        fs (float): Sampling rate of the signals (Hz).
        smooth (float, optional): Envelope smoothing window (s); None or 0
            disables smoothing. Defaults to 1.0.

    Returns:
        tuple: `(C, mean_r)` where `C` is the (N, N) correlation matrix and
            `mean_r` is the mean of its upper off-diagonal entries (NaN for
            fewer than two signals).
    """
    signals = [np.asarray(s, float) for s in signals]
    if len(signals) == 0:
        return np.zeros((0, 0)), float("nan")
    L = min(len(s) for s in signals)
    M = np.array([envelope(s[:L], fs, smooth=smooth, normalize=True)
                  for s in signals])
    C = np.corrcoef(M) if len(signals) > 1 else np.ones((1, 1))
    iu = np.triu_indices(len(signals), k=1)
    mean_r = float(np.mean(C[iu])) if len(iu[0]) else float("nan")
    return C, mean_r

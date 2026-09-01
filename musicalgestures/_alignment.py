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
from scipy.signal import fftconvolve

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

    Since 1.11.3 this delegates to `micromotion.xcorr_lag`, which owns lag
    estimation for the toolbox family, so the two packages cannot return
    different numbers for one pair of signals. The convention here is the one
    that was kept: micromotion returned the opposite sign until its 1.13.0,
    against its own documentation, and this function's agreement with its
    docstring is what exposed that. `micromotion` also gained the tie-breaking
    rule described above, which originated here.

    `difference=False` is passed, preserving this function's behaviour.
    micromotion differences by default, which guards against the spurious
    correlation of two drifting series; for envelopes, which do not drift, the
    undifferenced correlation is the more sensitive of the two. Call
    `micromotion.xcorr_lag` directly if the inputs may drift.

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
    from micromotion import xcorr_lag as _xcorr_lag
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = min(len(x), len(y))
    r = _xcorr_lag(x[:n], y[:n], fs=fs, max_lag_s=max_lag, difference=False)
    return float(r["lag_s"]), float(r["r"])


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
    (e.g. the hardest strike) -- sit at t = 0; then non-anchor events of
    stream `a` are matched to non-anchor events of stream `b` within
    +/- `window` seconds, and the signed offset (`b` minus `a`; positive =
    `b` later) is recorded. The anchor pair contributes an offset of 0 by
    construction and is excluded from BOTH streams -- `b`'s anchor is
    dropped from the match pool symmetrically with `a`'s, so a non-anchor
    `a` event near t = 0 cannot spuriously match `b`'s anchor. Matching is
    one-to-one: every candidate pair within the window is considered in
    order of increasing |offset| and greedily claimed, each `a` and `b`
    event usable in at most one match (consistent with
    `per_cycle_motion_delta`'s claim semantics), so a single `b` event
    cannot be double-counted against multiple `a` events. No absolute
    cross-stream synchronisation is claimed: the result measures whether
    the two streams agree on the RELATIVE timing of the remaining events.

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
    a = a[np.abs(a) > 1e-12]        # exclude a's anchor
    b = b[np.abs(b) > 1e-12]        # exclude b's anchor, symmetrically
    if len(a) == 0 or len(b) == 0:
        return np.array([])

    # All candidate pairs within the window, greedily claimed nearest-first
    # so the match is one-to-one (an a event and a b event are each used
    # in at most one pair), mirroring per_cycle_motion_delta's claiming.
    ai, bi = np.meshgrid(np.arange(len(a)), np.arange(len(b)), indexing="ij")
    diffs = b[bi] - a[ai]
    within = np.abs(diffs) <= window
    ai, bi, diffs = ai[within], bi[within], diffs[within]
    order = np.argsort(np.abs(diffs))

    claimed_a = np.zeros(len(a), dtype=bool)
    claimed_b = np.zeros(len(b), dtype=bool)
    offsets = []
    for k in order:
        i, j = ai[k], bi[k]
        if claimed_a[i] or claimed_b[j]:
            continue
        claimed_a[i] = True
        claimed_b[j] = True
        offsets.append(diffs[k])
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
    globally correlate locally (e.g. a motion envelope vs an audio level
    envelope).

    Source: Westney-comparisons study (Jensenius) -- local motion-loudness
    correlation in 10 s windows.

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


# ---------------------------------------------------------------------------
# Locating one recording inside another
#
# `xcorr_lag` above answers "how far apart are these two signals", for signals
# that already cover the same stretch of time. These answer a different
# question: WHERE inside a long recording does this short one sit. Two
# recordings of one event share content even when they share nothing else --- a
# second camera in another room hearing the far end through a speaker, or a cut
# and re-encoded copy of the same session.
#
# Three faults these must not have, all met on real data:
#
#   - probes, not one whole-file correlation. A file named `Cut` may be one
#     contiguous excerpt or several pieces spliced together, and a single
#     correlation cannot tell you which. Several short windows located
#     independently can, and where they disagree the disagreement IS the edit
#     list;
#   - the summary is the offset that RECURS, not the median. Matching a
#     recording made with clip microphones against one made with a room
#     microphone, most probes match nothing and land anywhere, and the middle of
#     a list containing nonsense is nonsense;
#   - a probe that matches nothing must say so. Every cross-correlation has a
#     maximum; the maximum of noise is still a maximum, and reporting it as an
#     offset is how an annotation lands silently on the wrong timeline.
#
# RELATION TO micromotion.search_lag, which owns lag estimation for these
# packages. `search_lag` solves the neighbouring problem and is the right tool
# when it fits: it tolerates unequal lengths and sampling, and scores every
# integer offset within `max_lag_s` by Pearson correlation over whatever the two
# series share there. It is a bounded direct search, and that is the difference.
# Locating a 56-minute excerpt anywhere inside a 2 h 38 min recording at 20 Hz
# needs roughly 190,000 candidate offsets against a 68,000-sample probe, which
# direct search cannot do in reasonable time; these are FFT-based, so the whole
# recording is searchable. Use `search_lag` when you know the offset is small and
# the sampling is awkward, and these when you do not know where the piece sits at
# all. Neither should be reimplemented on top of the other without measuring
# first, and if `search_lag` ever grows an FFT path this should delegate to it.
# ---------------------------------------------------------------------------

def envelope_from_audio(samples, sr: float, hop_s: float = 0.05):
    """An amplitude envelope: peak absolute amplitude per hop.

    Peak rather than mean, because a brief transient is exactly what makes two recordings
    of one event recognisable to each other, and a mean removes it.

    Args:
        samples: Audio, one dimension. Stereo is mixed to mono by the caller.
        sr (float): Sample rate of `samples`.
        hop_s (float): Hop length in seconds. Defaults to 0.05, a 20 Hz envelope.

    Returns:
        tuple: The envelope, and its sampling rate in frames per second.
    """
    y = np.asarray(samples, dtype=float).ravel()
    hop = max(1, int(round(hop_s * sr)))
    n = (len(y) // hop) * hop
    if n == 0:
        return np.zeros(0), sr / hop
    return np.abs(y[:n]).reshape(-1, hop).max(axis=1), sr / hop


def locate_probe(probe, reference):
    """Where `probe` best matches inside `reference`, and how well.

    The correlation is normalised over the actual overlap at every position, so a
    position where only a few samples overlap cannot score better than one where they all
    do --- an unnormalised correlation picks exactly such a position and reports a
    perfect match.

    Args:
        probe: The shorter series to locate.
        reference: The longer series to search.

    Returns:
        tuple: Index of the best position and its Pearson r, or ``(None, -1.0)`` when the
        probe has no variance to match with or is longer than the reference.
    """
    p = np.asarray(probe, dtype=float).ravel()
    s = np.asarray(reference, dtype=float).ravel()
    m, n = len(p), len(s)
    if m < 2 or n < m:
        return None, -1.0
    pc = p - p.mean()
    sd_p = pc.std()
    if sd_p == 0:
        return None, -1.0

    ones = np.ones(m)
    s_sum = fftconvolve(s, ones, mode="valid")
    s_sq = fftconvolve(s ** 2, ones, mode="valid")
    mean_s = s_sum / m
    var_s = np.maximum(s_sq / m - mean_s ** 2, 1e-12)
    num = fftconvolve(s, pc[::-1], mode="valid")
    r = num / (m * np.sqrt(var_s) * sd_p)
    best = int(np.argmax(r))
    return best, float(r[best])


def align_by_audio(cut, reference, fs: float, n_probes: int = 12,
                   probe_s: float = 30.0, min_r: float = 0.45,
                   tolerance_s: float = 0.5):
    """The offset at which `cut` sits inside `reference`, from several probes.

    Args:
        cut: Envelope of the shorter recording.
        reference: Envelope of the longer one.
        fs (float): Sampling rate of both envelopes, in frames per second.
        n_probes (int): How many windows to locate independently. Defaults to 12.
        probe_s (float): Length of each window in seconds. Defaults to 30.0.
        min_r (float): Correlation below which a probe is treated as no match rather
            than as a weak one. Defaults to 0.45.
        tolerance_s (float): How close two probe offsets must be to count as the same.
            Defaults to 0.5.

    Returns:
        tuple: ``(offset_s, mean_r, n_agreeing, n_probes)``. `offset_s` is None when no
        cluster of probes agrees, which is the correct answer for two recordings that
        have nothing in common. Add `offset_s` to a time in `cut` to get the time in
        `reference`.
    """
    c = np.asarray(cut, dtype=float).ravel()
    s = np.asarray(reference, dtype=float).ravel()
    m = int(round(probe_s * fs))
    if m < 2 or len(c) < m or len(s) < m:
        return None, 0.0, 0, 0

    starts = np.linspace(0, max(0, len(c) - m), max(1, n_probes)).astype(int)
    found = []
    for st in starts:
        pos, r = locate_probe(c[st:st + m], s)
        if pos is not None and r >= min_r:
            found.append(((pos - st) / fs, r))
    if not found:
        return None, 0.0, 0, len(starts)

    #: Cluster the offsets and take the largest cluster, not the median: probes that
    #: matched nothing are scattered, and they must not drag the answer.
    found.sort(key=lambda t: t[0])
    clusters, cur = [], [found[0]]
    for off, r in found[1:]:
        if off - cur[-1][0] <= tolerance_s:
            cur.append((off, r))
        else:
            clusters.append(cur)
            cur = [(off, r)]
    clusters.append(cur)
    best = max(clusters, key=len)
    offs = [o for o, _ in best]
    rs = [r for _, r in best]
    return float(np.mean(offs)), float(np.mean(rs)), len(best), len(starts)

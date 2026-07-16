"""
Pulse and cycle segmentation for accelerating rhythmic sequences.

Tools for grouping event onsets (e.g. drum strokes) into per-cycle stroke
groups, tabulating per-cycle metrics, fitting an exponential accelerando
model, and detecting motion onsets from a quantity-of-motion signal.

These helpers are independent of the MgVideo/MgAudio classes and operate on
plain numpy arrays of onset times or 1-D motion signals.

Source: ro study (Jensenius) -- analysis of the accelerating ro ritual's
drum-stroke cycles and their coupling to body motion.
"""

from dataclasses import dataclass

import numpy as np

from musicalgestures._peaks import pick_peaks


@dataclass
class Cycle:
    """
    One rhythmic cycle: a group of stroke onsets plus an optional secondary
    event (e.g. a shout) that falls inside the cycle.

    Source: ro study (Jensenius).

    Attributes:
        index (int): Zero-based cycle index.
        strokes (list): Onset times (s) of the strokes in this cycle.
        event (float | None): Time (s) of the cycle's secondary event, or None.
    """
    index: int
    strokes: list
    event: float | None = None

    @property
    def t_start(self):
        """float: Time (s) of the cycle's first stroke."""
        return self.strokes[0]

    @property
    def n_strokes(self):
        """int: Number of strokes in the cycle."""
        return len(self.strokes)

    @property
    def stroke_gap(self):
        """float: Gap (s) between the first two strokes (NaN if fewer than 2)."""
        return self.strokes[1] - self.strokes[0] if len(self.strokes) >= 2 else np.nan


def group_strokes(onset_times, max_strokes=4, gap_lo=0.10, gap_hi=0.60,
                  w_abs=6.0, w_within=4.0, tol_within=0.15,
                  w_order=2.5, w_trend=2.0, tol_trend=0.25,
                  size_costs=(1.0, 0.0, 1.5, 6.0)):
    """
    Segment stroke onsets into per-cycle stroke groups by dynamic
    programming over candidate group boundaries (Viterbi over segmentations),
    with a greedily carried stroke-gap estimate (EMA) that is exact given
    that carried estimate but is not itself part of the DP state key, so
    Bellman optimality does not strictly hold over the full segmentation.

    The cost of a segmentation encodes structural priors for an accelerating
    cyclic pattern (developed for the ro ritual's double drum strokes):

    * size prior -- `size_costs[k-1]` per k-stroke group: with the defaults,
      double strokes are free, singles/triples carry a small penalty, >=4 a
      steep one;
    * within-gap plausibility -- gaps inside a group should fall in
      `[gap_lo, gap_hi]` seconds (`w_abs` x log-excess outside) and stay
      close to a running stroke-gap estimate (EMA, weight 0.5): `w_within`
      x |log-ratio| beyond `tol_within`;
    * ordering prior -- a between-group gap shorter than the current
      stroke-gap estimate costs `w_order` x the log-ratio shortfall;
    * accelerando prior -- successive between-group gaps should not grow:
      an increase beyond `tol_trend` (log) costs `w_trend` x the excess
      (decreases are free, so a climax's shrinking gaps cost nothing).

    Unlike a single running threshold, the trend and ordering terms let the
    decision boundary between stroke gaps and cycle gaps shrink with the
    accelerando, so the climax stays resolved even when the cycle gap drops
    to (or just below) the stroke gap in the final cycles.

    Source: ro study (Jensenius).

    Args:
        onset_times (np.ndarray): Stroke onset times in seconds (any order).
        max_strokes (int, optional): Maximum strokes per group. Defaults to 4.
        gap_lo (float, optional): Lower bound (s) of plausible within-group gaps. Defaults to 0.10.
        gap_hi (float, optional): Upper bound (s) of plausible within-group gaps. Defaults to 0.60.
        w_abs (float, optional): Weight of the absolute within-gap plausibility term.
            Defaults to 6.0.
        w_within (float, optional): Weight of the within-gap-vs-EMA term. Defaults to 4.0.
        tol_within (float, optional): Log-ratio tolerance of the within-gap-vs-EMA term.
            Defaults to 0.15.
        w_order (float, optional): Weight of the ordering prior. Defaults to 2.5.
        w_trend (float, optional): Weight of the accelerando (non-increasing gaps) prior.
            Defaults to 2.0.
        tol_trend (float, optional): Log-ratio tolerance of the accelerando prior. Defaults to 0.25.
        size_costs (tuple, optional): Cost per group of size 1, 2, 3, >=4.
            Defaults to (1.0, 0.0, 1.5, 6.0).

    Returns:
        list: A list of groups, each a list of stroke onset times (floats, seconds).
    """
    t = np.sort(np.asarray(onset_times, float))
    n = len(t)
    if n == 0:
        return []
    if n == 1:
        return [[float(t[0])]]
    log = np.log
    gaps = np.maximum(np.diff(t), 1e-3)

    def size_cost(k):
        return size_costs[min(k, len(size_costs)) - 1]

    def within_cost(w, ema):
        c = w_abs * (max(0.0, log(w / gap_hi)) + max(0.0, log(gap_lo / w)))
        if ema is not None:
            c += w_within * max(0.0, abs(log(w / ema)) - tol_within)
        return c

    # State (i, j): a completed group spans onsets j..i. Value: cost, the
    # between-gap that preceded the group, the stroke-gap EMA, backpointer.
    best = {}

    def push(key, cost, prev_g, ema, back):
        cur = best.get(key)
        if cur is None or cost < cur[0]:
            best[key] = (cost, prev_g, ema, back)

    for i in range(min(n, max_strokes)):        # groups starting at onset 0
        cost, ema = size_cost(i + 1), None
        for k in range(i):
            cost += within_cost(gaps[k], ema)
            ema = gaps[k] if ema is None else 0.5 * ema + 0.5 * gaps[k]
        push((i, 0), cost, None, ema, None)

    for i in range(n - 1):
        for j in range(max(0, i - max_strokes + 1), i + 1):
            state = best.get((i, j))
            if state is None:
                continue
            cost0, prev_g, ema0, _ = state
            g = gaps[i]                          # between-group gap
            cost0 += w_trend * max(0.0, log(g / prev_g) - tol_trend) \
                if prev_g is not None else 0.0
            if ema0 is not None:
                cost0 += w_order * max(0.0, log(ema0 / g))
            for i2 in range(i + 1, min(n, i + 1 + max_strokes)):
                size = i2 - i
                cost, ema = cost0 + size_cost(size), ema0
                for k in range(i + 1, i2):
                    cost += within_cost(gaps[k], ema)
                    ema = gaps[k] if ema is None else 0.5 * ema + 0.5 * gaps[k]
                push((i2, i + 1), cost, g, ema, (i, j))

    key = min((k for k in best if k[0] == n - 1), key=lambda k: best[k][0])
    starts = []
    while key is not None:
        starts.append(key[1])
        key = best[key][3]
    starts.reverse()
    return [list(map(float, t[a:b]))
            for a, b in zip(starts, starts[1:] + [n])]


def segment_cycles(onset_times, event_times=None, **kwargs):
    """
    Segment stroke onsets into `Cycle` objects: one Cycle per stroke group
    (see `group_strokes`); the cycle's secondary event is the first event
    onset in [group start, next group start).

    Source: ro study (Jensenius) -- the secondary events were the ritual's
    shouts.

    Args:
        onset_times (np.ndarray): Stroke onset times in seconds.
        event_times (np.ndarray, optional): Onset times (s) of a secondary event
            stream (e.g. shouts) to assign to cycles. Defaults to None.
        **kwargs: Passed on to `group_strokes`.

    Returns:
        list: A list of `Cycle` objects.
    """
    groups = group_strokes(onset_times, **kwargs)
    event_times = np.sort(np.asarray(
        [] if event_times is None else event_times, float))
    starts = [g[0] for g in groups] + [np.inf]
    out = []
    for i, g in enumerate(groups):
        ev = event_times[(event_times >= starts[i]) & (event_times < starts[i + 1])]
        out.append(Cycle(i, list(g), float(ev[0]) if len(ev) else None))
    return out


def cycle_table(cycles, clip_id="", context=""):
    """
    Tabulate per-cycle metrics from a list of `Cycle` objects.

    Source: ro study (Jensenius).

    Args:
        cycles (list): A list of `Cycle` objects (see `segment_cycles`).
        clip_id (str, optional): Identifier written to the `clip` column. Defaults to "".
        context (str, optional): Label written to the `context` column. Defaults to "".

    Returns:
        pd.DataFrame: One row per cycle with columns `clip`, `context`, `cycle`,
            `t` (cycle start, s), `ioi` (to next cycle start, s), `n_strokes`,
            `stroke_gap` (s), `event` (secondary-event time, s or NaN) and
            `stroke_event_ioi` (event minus cycle start, s or NaN).
    """
    import pandas as pd
    columns = ['clip', 'context', 'cycle', 't', 'ioi', 'n_strokes',
               'stroke_gap', 'event', 'stroke_event_ioi']
    rows = []
    for i, c in enumerate(cycles):
        nxt = cycles[i + 1].t_start if i + 1 < len(cycles) else np.nan
        rows.append(dict(
            clip=clip_id, context=context, cycle=c.index, t=c.t_start,
            ioi=nxt - c.t_start, n_strokes=c.n_strokes,
            stroke_gap=c.stroke_gap, event=c.event,
            stroke_event_ioi=(c.event - c.t_start) if c.event is not None else np.nan,
        ))
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)


def fit_accelerando(times, iois):
    """
    Fit an exponential accelerando model IOI(t) = ioi0 * 2**(-t / t_double)
    via least squares on log2(IOI): `t_double` is the time (s) it takes the
    inter-onset interval to halve (i.e. the tempo to double).

    Source: ro study (Jensenius).

    Args:
        times (np.ndarray): Cycle start times in seconds.
        iois (np.ndarray): Inter-onset intervals (s) at those times. Non-finite
            or non-positive entries are ignored.

    Returns:
        tuple: `(ioi0, t_double, r2)` where `ioi0` is the fitted IOI at t=0 (s),
            `t_double` is the tempo-doubling time (s; `np.inf` if the sequence is
            not accelerating), and `r2` is the fit's coefficient of determination
            on log2(IOI).
    """
    t = np.asarray(times, float)
    ioi = np.asarray(iois, float)
    m = np.isfinite(t) & np.isfinite(ioi) & (ioi > 0)
    t, ioi = t[m], np.log2(ioi[m])
    A = np.vstack([t, np.ones_like(t)]).T
    (slope, intercept), *_ = np.linalg.lstsq(A, ioi, rcond=None)
    pred = A @ [slope, intercept]
    ss_tot = ((ioi - ioi.mean()) ** 2).sum()
    r2 = 1 - ((ioi - pred) ** 2).sum() / ss_tot if ss_tot > 0 else np.nan
    return 2.0 ** intercept, (-1.0 / slope if slope < 0 else np.inf), r2


def motion_onsets(motion, fs, min_interval=0.25, smooth_cutoff=8.0):
    """
    Times of the steepest sustained rises in a motion signal (e.g. a
    quantity-of-motion curve): the signal is low-pass filtered, its positive
    time-derivative is formed, and peaks of that derivative are picked with
    the canonical peak-picker (`musicalgestures.pick_peaks`) using a robust
    prominence gate of 0.25 x (99th percentile - median) of the derivative.

    Source: ro study (Jensenius) -- motion onsets of the rowing gesture,
    related to the drum cycles via `per_cycle_motion_delta`.

    Args:
        motion (np.ndarray): 1-D motion signal (e.g. mean absolute frame difference).
        fs (float): Sampling rate of the signal (Hz, e.g. video frames per second).
        min_interval (float, optional): Minimum interval between onsets (s). Defaults to 0.25.
        smooth_cutoff (float, optional): Low-pass cutoff (Hz) applied before
            differentiation. Defaults to 8.0.

    Returns:
        np.ndarray: Onset times in seconds.
    """
    from scipy.signal import butter, filtfilt
    motion = np.asarray(motion, float)
    cutoff = min(smooth_cutoff, 0.45 * fs)
    b, a = butter(3, cutoff / (fs / 2))
    s = filtfilt(b, a, motion)
    d = np.clip(np.gradient(s) * fs, 0, None)
    prom = (np.percentile(d, 99) - np.median(d)) * 0.25
    idx = pick_peaks(d, fs=fs, smooth=None, rel_threshold=None,
                     min_interval=min_interval, rel_prominence=None,
                     prominence=prom)
    return idx / fs

# Pulse

> Auto-generated documentation for [musicalgestures._pulse](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py) module.

Pulse and cycle segmentation for accelerating rhythmic sequences.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Pulse
    - [Cycle](#cycle)
        - [Cycle().n_strokes](#cyclen_strokes)
        - [Cycle().stroke_gap](#cyclestroke_gap)
        - [Cycle().t_start](#cyclet_start)
    - [cycle_table](#cycle_table)
    - [fit_accelerando](#fit_accelerando)
    - [group_strokes](#group_strokes)
    - [motion_onsets](#motion_onsets)
    - [segment_cycles](#segment_cycles)

Tools for grouping event onsets (e.g. drum strokes) into per-cycle stroke
groups, tabulating per-cycle metrics, fitting an exponential accelerando
model, and detecting motion onsets from a quantity-of-motion signal.

These helpers are independent of the MgVideo/MgAudio classes and operate on
plain numpy arrays of onset times or 1-D motion signals.

Source: ro study (Jensenius) -- analysis of the accelerating ro ritual's
drum-stroke cycles and their coupling to body motion.

## Cycle

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py#L23)

```python
dataclass
class Cycle():
```

One rhythmic cycle: a group of stroke onsets plus an optional secondary
event (e.g. a shout) that falls inside the cycle.

Source: ro study (Jensenius).

#### Attributes

- `index` *int* - Zero-based cycle index.
- `strokes` *list* - Onset times (s) of the strokes in this cycle.
event (float | None): Time (s) of the cycle's secondary event, or None.

### Cycle().n_strokes

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py#L44)

```python
@property
def n_strokes():
```

int: Number of strokes in the cycle.

### Cycle().stroke_gap

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py#L49)

```python
@property
def stroke_gap():
```

float: Gap (s) between the first two strokes (NaN if fewer than 2).

### Cycle().t_start

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py#L39)

```python
@property
def t_start():
```

float: Time (s) of the cycle's first stroke.

## cycle_table

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py#L201)

```python
def cycle_table(cycles, clip_id='', context=''):
```

Tabulate per-cycle metrics from a list of [Cycle](#cycle) objects.

Source: ro study (Jensenius).

#### Arguments

- `cycles` *list* - A list of [Cycle](#cycle) objects (see [segment_cycles](#segment_cycles)).
- `clip_id` *str, optional* - Identifier written to the `clip` column. Defaults to "".
- `context` *str, optional* - Label written to the `context` column. Defaults to "".

#### Returns

- `pd.DataFrame` - One row per cycle with columns `clip`, `context`, `cycle`,
    `t` (cycle start, s), `ioi` (to next cycle start, s), `n_strokes`,
    `stroke_gap` (s), `event` (secondary-event time, s or NaN) and
    `stroke_event_ioi` (event minus cycle start, s or NaN).

## fit_accelerando

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py#L235)

```python
def fit_accelerando(times, iois):
```

Fit an exponential accelerando model IOI(t) = ioi0 * 2**(-t / t_double)
via least squares on log2(IOI): `t_double` is the time (s) it takes the
inter-onset interval to halve (i.e. the tempo to double).

Source: ro study (Jensenius).

#### Arguments

- `times` *np.ndarray* - Cycle start times in seconds.
- `iois` *np.ndarray* - Inter-onset intervals (s) at those times. Non-finite
    or non-positive entries are ignored.

#### Returns

- `tuple` - `(ioi0, t_double, r2)` where `ioi0` is the fitted IOI at t=0 (s),
    `t_double` is the tempo-doubling time (s; `np.inf` if the sequence is
    not accelerating), and `r2` is the fit's coefficient of determination
    on log2(IOI). Degenerate input -- fewer than 3 valid (finite,
    strictly positive) IOI points, too few to constrain the 2-parameter
    - `fit` - returns `(nan, nan, nan)`.

## group_strokes

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py#L55)

```python
def group_strokes(
    onset_times,
    max_strokes=4,
    gap_lo=0.1,
    gap_hi=0.6,
    w_abs=6.0,
    w_within=4.0,
    tol_within=0.15,
    w_order=2.5,
    w_trend=2.0,
    tol_trend=0.25,
    size_costs=(1.0, 0.0, 1.5, 6.0),
):
```

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

#### Arguments

- `onset_times` *np.ndarray* - Stroke onset times in seconds (any order).
- `max_strokes` *int, optional* - Maximum strokes per group. Defaults to 4.
- `gap_lo` *float, optional* - Lower bound (s) of plausible within-group gaps. Defaults to 0.10.
- `gap_hi` *float, optional* - Upper bound (s) of plausible within-group gaps. Defaults to 0.60.
- `w_abs` *float, optional* - Weight of the absolute within-gap plausibility term.
    Defaults to 6.0.
- `w_within` *float, optional* - Weight of the within-gap-vs-EMA term. Defaults to 4.0.
- `tol_within` *float, optional* - Log-ratio tolerance of the within-gap-vs-EMA term.
    Defaults to 0.15.
- `w_order` *float, optional* - Weight of the ordering prior. Defaults to 2.5.
- `w_trend` *float, optional* - Weight of the accelerando (non-increasing gaps) prior.
    Defaults to 2.0.
- `tol_trend` *float, optional* - Log-ratio tolerance of the accelerando prior. Defaults to 0.25.
- `size_costs` *tuple, optional* - Cost per group of size 1, 2, 3, >=4.
    Defaults to (1.0, 0.0, 1.5, 6.0).

#### Returns

- `list` - A list of groups, each a list of stroke onset times (floats, seconds).

## motion_onsets

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py#L271)

```python
def motion_onsets(motion, fs, min_interval=0.25, smooth_cutoff=8.0):
```

Times of the steepest sustained rises in a motion signal (e.g. a
quantity-of-motion curve): the signal is low-pass filtered, its positive
time-derivative is formed, and peaks of that derivative are picked with
the canonical peak-picker (`musicalgestures.pick_peaks`) using a robust
prominence gate of 0.25 x (99th percentile - median) of the derivative.

Source: ro study (Jensenius) -- motion onsets of the rowing gesture,
related to the drum cycles via `per_cycle_motion_delta`.

#### Arguments

- `motion` *np.ndarray* - 1-D motion signal (e.g. mean absolute frame difference).
- `fs` *float* - Sampling rate of the signal (Hz, e.g. video frames per second).
- `min_interval` *float, optional* - Minimum interval between onsets (s). Defaults to 0.25.
- `smooth_cutoff` *float, optional* - Low-pass cutoff (Hz) applied before
    differentiation. Defaults to 8.0.

#### Returns

- `np.ndarray` - Onset times in seconds.

## segment_cycles

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pulse.py#L172)

```python
def segment_cycles(onset_times, event_times=None, **kwargs):
```

Segment stroke onsets into [Cycle](#cycle) objects: one Cycle per stroke group
(see [group_strokes](#group_strokes)); the cycle's secondary event is the first event
onset in [group start, next group start).

Source: ro study (Jensenius) -- the secondary events were the ritual's
shouts.

#### Arguments

- `onset_times` *np.ndarray* - Stroke onset times in seconds.
- `event_times` *np.ndarray, optional* - Onset times (s) of a secondary event
    stream (e.g. shouts) to assign to cycles. Defaults to None.
- `**kwargs` - Passed on to [group_strokes](#group_strokes).

#### Returns

- `list` - A list of [Cycle](#cycle) objects.

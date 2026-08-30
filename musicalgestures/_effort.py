"""The MGT operationalisation of Laban's Effort, in continuous indices.

Laban's Effort is a qualitative observational system with four factors --- Weight,
Time, Space, Flow --- and every computational version of it is somebody's
operationalisation. This is MGT's, named as such, designed in
`plans/2026-08-30-effort-layer-design.md` and validated in `tests/test_effort.py`
before any docstring made a claim. Each function returns a continuous index with a
documented direction, never a category shipped as fact.

Input-agnostic on purpose: the functions take arrays and a sample rate, so mocap
speeds, pose-trajectory speeds and quantity-of-motion tracks all qualify. What the
index then describes is the mover the array describes --- a full-body QoM track
yields ensemble Effort, one wrist yields that wrist's.

The factors differ in evidential standing, and their docstrings say so. Flow rests
on SPARC, which carries the strongest evidence; Weight is the weakest claim ---
"strong" without mass or force plates is a kinetic proxy --- and is labelled as one.
That proxy status has a scholarly frame: dynamics are inferred from kinematics
(the kinematic-specification-of-dynamics hypothesis, Runeson & Frykholm 1983), and
Laban's factors mix the two --- Time is kinematical, Weight and Flow dynamical ---
so a video-based Effort layer necessarily reads dynamics through what it can see
(Haga 2008, ch. 4).

Two further points from Haga (2008) shape how these indices are meant to be read.
Effort elements denote fluctuation, not level --- "gentler and firmer", the way the
qualities change over a phrase --- so the windowed `effort_profile` contours are the
object of analysis, and a single number for a whole recording flattens what the
concept is about. And effort is the qualitative reading on top of a neutral
intensity contour (Stern's activation, which is what a quantity-of-motion track
measures): QoM says how much, Effort says how.
"""
from __future__ import annotations

import numpy as np

__all__ = ["sparc", "effort_time", "effort_weight", "effort_space", "effort_flow",
           "effort_profile", "basic_effort_actions"]


def sparc(speed, fs: float, padlevel: int = 4, fc: float = 10.0,
          amp_th: float = 0.05) -> float:
    """Spectral arc length: movement smoothness from the speed profile's spectrum.

    Implemented from Balasubramanian, Melendez-Calderon, Roby-Brami & Burdet (2015),
    *On the analysis of movement smoothness*: the negative arc length of the
    normalised Fourier magnitude spectrum below an adaptive cutoff. Values are
    negative, and closer to zero is smoother: a single minimum-jerk reach measures
    about -1.45 here, three chained submovements about -2.6, and the test suite
    holds both.

    The adaptive cutoff is the reason to prefer SPARC over jerk from tracked data:
    under 10 per cent added tracker noise SPARC stays within a few per cent of its
    clean value while still separating submovement count, where jerk RMS cannot
    tell that noise from genuinely tripled submovements. Measured in the test
    suite, and the reason MGT reports no jerk-based smoothness from pose data.

    Args:
        speed: One-dimensional speed profile (non-negative magnitudes).
        fs (float): Sample rate of the profile in Hz.
        padlevel (int): Zero-padding exponent for the FFT. Defaults to 4.
        fc (float): Maximum frequency of interest in Hz. Defaults to 10.
        amp_th (float): Amplitude threshold of the adaptive cutoff. Defaults
            to 0.05.

    Returns:
        float: The spectral arc length; negative, closer to zero is smoother.
        NaN for a profile with no movement.
    """
    speed = np.asarray(speed, dtype=float).ravel()
    if speed.size < 4 or not np.isfinite(speed).any() or np.nanmax(speed) <= 0:
        return float("nan")
    speed = np.nan_to_num(speed)

    n = 2 ** (int(np.ceil(np.log2(speed.size))) + padlevel)
    freq = np.arange(n) * fs / n
    mag = np.abs(np.fft.fft(speed, n))
    mag = mag / mag.max()

    below = freq <= fc
    f_sel, m_sel = freq[below], mag[below]
    #: The adaptive cutoff: within fc, keep up to the last point still above the
    #: amplitude threshold, so trailing noise floor does not add arc length.
    above = np.nonzero(m_sel >= amp_th)[0]
    f_sel, m_sel = f_sel[: above[-1] + 1], m_sel[: above[-1] + 1]

    df = np.diff(f_sel / f_sel[-1])
    dm = np.diff(m_sel)
    return float(-np.sum(np.sqrt(df ** 2 + dm ** 2)))


def effort_time(speed, fs: float) -> float:
    """The Time factor: sudden against sustained, as burst concentration.

    The MGT operationalisation of Laban's Time. A sudden mover concentrates their
    movement into brief peaks; a sustained one spreads it evenly. The index is the
    mean speed of the fastest tenth of samples over the mean speed of all of them:
    1.0 for perfectly sustained movement, rising without bound as movement
    concentrates into bursts. `fs` is accepted for interface symmetry; the index is
    rate-invariant.

    Returns:
        float: Burst concentration; higher is more sudden. NaN with no movement.
    """
    speed = np.asarray(speed, dtype=float).ravel()
    speed = speed[np.isfinite(speed)]
    if speed.size < 10 or speed.max() <= 0:
        return float("nan")
    top = np.sort(speed)[-max(1, speed.size // 10):]
    return float(top.mean() / speed.mean())


def effort_weight(speed, fs: float) -> float:
    """The Weight factor: strong against light, as peak acceleration.

    The weakest claim of the four, and labelled as one: without mass or force
    plates, "strong" from video is a kinetic proxy. The index is the 95th
    percentile of the absolute acceleration of the speed profile, in the profile's
    units per second squared --- a strong mover changes speed hard, a light one
    gently. Comparable within one recording and one mover; across recordings it
    inherits every scale difference of the input.

    Returns:
        float: Peak (p95) absolute acceleration; higher is stronger. NaN with
        fewer than 3 samples.
    """
    speed = np.asarray(speed, dtype=float).ravel()
    speed = speed[np.isfinite(speed)]
    if speed.size < 3:
        return float("nan")
    return float(np.percentile(np.abs(np.diff(speed)) * fs, 95))


def effort_space(xy, fs: float, window_s: float = 5.0) -> np.ndarray:
    """The Space factor: direct against indirect, as windowed path directness.

    The MGT operationalisation of Laban's Space, on a substrate with a long
    history: per window, the straight-line displacement over the path length
    actually travelled. A dead-straight path scores 1; a path that wanders scores
    toward 0. Windows with no movement are NaN, not a guess.

    Args:
        xy: Positions of shape (frames, 2).
        fs (float): Sample rate in Hz.
        window_s (float): Window length in seconds. Defaults to 5.

    Returns:
        np.ndarray: Directness in [0, 1] per full window.
    """
    xy = np.asarray(xy, dtype=float)
    win = int(round(window_s * fs))
    out: list[float] = []
    for a in range(0, xy.shape[0] - win + 1, win):
        seg = xy[a:a + win]
        steps = np.linalg.norm(np.diff(seg, axis=0), axis=1)
        path = float(np.nansum(steps))
        chord = float(np.linalg.norm(seg[-1] - seg[0]))
        out.append(chord / path if path > 0 else float("nan"))
    return np.array(out, dtype=np.float64)


def effort_flow(speed, fs: float) -> float:
    """The Flow factor: bound against free, as negated SPARC.

    The MGT operationalisation of Laban's Flow, on smoothness as its substrate: a
    free mover's speed profile is smooth, a bound one's is held and corrected.
    The index is `-sparc(speed, fs)`, so higher is more bound; about 1.45 for a
    single free reach, rising with every correction. SPARC's noise robustness
    carries over, which is what makes this readable from tracked data at all.

    Returns:
        float: Boundness; higher is more bound. NaN with no movement.
    """
    return -sparc(speed, fs)


def effort_profile(xy_or_speed, fs: float, window_s: float = 5.0) -> dict:
    """All four factors, windowed onto one clock.

    Given positions of shape (frames, 2), speed is their frame-to-frame
    displacement rate and Space is computable; given a one-dimensional speed or
    quantity-of-motion track, Space is NaN throughout, since directness needs a
    path. Each factor is computed per full window; a trailing partial window is
    dropped rather than guessed.

    Args:
        xy_or_speed: (frames, 2) positions, or a (frames,) speed track.
        fs (float): Sample rate in Hz.
        window_s (float): Window length in seconds. Defaults to 5.

    Returns:
        dict: ``time`` (window centres, seconds), ``time_index`` (sudden),
        ``weight`` (strong), ``space`` (direct), ``flow`` (bound) --- one value
        per window, NaN where a factor cannot be measured.
    """
    a = np.asarray(xy_or_speed, dtype=float)
    if a.ndim == 2 and a.shape[1] == 2:
        speed = np.concatenate([[0.0], np.linalg.norm(np.diff(a, axis=0), axis=1) * fs])
        space = effort_space(a, fs, window_s)
    else:
        speed = a.ravel()
        space = None

    win = int(round(window_s * fs))
    n = speed.size // win
    centres, t_idx, weight, flow = [], [], [], []
    for k in range(n):
        seg = speed[k * win:(k + 1) * win]
        centres.append((k + 0.5) * window_s)
        t_idx.append(effort_time(seg, fs))
        weight.append(effort_weight(seg, fs))
        flow.append(effort_flow(seg, fs))
    return {"time": np.asarray(centres),
            "time_index": np.asarray(t_idx),
            "weight": np.asarray(weight),
            "space": (space[:n] if space is not None
                      else np.full(n, np.nan)),
            "flow": np.asarray(flow)}


#: Laban's eight basic effort actions as combinations of the Weight, Time and
#: Space poles, after Laban (1971) as tabulated by Haga (2008, Table 20). Keys are
#: (firm, sudden, direct).
_BASIC_ACTIONS = {(True, True, True): "thrusting",
                  (True, True, False): "slashing",
                  (True, False, True): "pressing",
                  (True, False, False): "wringing",
                  (False, True, True): "dabbing",
                  (False, True, False): "flicking",
                  (False, False, True): "gliding",
                  (False, False, False): "floating"}


def basic_effort_actions(profile: dict) -> list:
    """Laban's eight basic effort actions, per window, as proposals.

    Laban condensed the Weight, Time and Space poles into eight named actions ---
    thrusting, slashing, pressing, wringing, dabbing, flicking, gliding, floating
    --- with Flow as a further colouring element outside the combination (Laban
    1971, via Haga 2008, Table 20, whose derivative verbs --- shove, pat, crush,
    beat, strew, pull, flip, smooth --- give the register these labels live in).

    Each pole is read against the mover's own median over the profile, in the
    house style of median-anchored thresholds: "firm" means firmer than this
    mover's typical window, so the labels describe one mover's range and never
    compare two movers. They are proposals for looking with, not classifications
    --- Laban's categories are observational, and a window's label says which
    octant of this mover's own space it falls in.

    Args:
        profile (dict): As from :func:`effort_profile` --- needs ``weight``,
            ``time_index`` and ``space`` arrays of one length.

    Returns:
        list: One of the eight action names per window, or None where any of the
        three indices is NaN.
    """
    w = np.asarray(profile["weight"], dtype=float)
    t = np.asarray(profile["time_index"], dtype=float)
    sp = np.asarray(profile["space"], dtype=float)
    med = [np.nanmedian(a) if np.isfinite(a).any() else float("nan")
           for a in (w, t, sp)]
    out: list[str | None] = []
    for wi, ti, si in zip(w, t, sp):
        if not (np.isfinite(wi) and np.isfinite(ti) and np.isfinite(si)):
            out.append(None)
            continue
        out.append(_BASIC_ACTIONS[(bool(wi > med[0]), bool(ti > med[1]),
                                   bool(si > med[2]))])
    return out

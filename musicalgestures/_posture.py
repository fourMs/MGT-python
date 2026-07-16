"""
Posturography and standstill-sway metrics for centre-of-pressure (CoP) and
head/marker position signals.

This module ports the "still standing" study's posturography stack into
pure numpy/scipy surfaces that operate on plain arrays -- no study-specific
loaders, axis conventions, or marker loops. Three families of measures are
provided:

* **Sway amount / geometry** -- :func:`cop_sway_metrics`,
  :func:`confidence_ellipse_area`, :func:`convex_hull_area`.
* **Control dynamics / complexity** -- :func:`stabilogram_diffusion`
  (Collins-De Luca SDA), :func:`dfa` (detrended fluctuation analysis),
  :func:`sample_entropy`, :func:`spectral_edges`, :func:`sway_texture`,
  :func:`principal_axis_projection`.
* **Direction / extent** -- :func:`sway_orientation`, :func:`axial_rayleigh`,
  :func:`spatial_extent`.

The from-scratch SDA / DFA / sample-entropy implementations are validated in
the test-suite against known-answer synthetic signals (white noise ->
DFA alpha ~= 0.5 and SDA Hurst ~= 0.5; a sine -> low sample entropy relative
to its shuffle).

Source: still standing study (Jensenius) -- posturography and micromotion
analyses of the international "standstill" championships and related datasets.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Sway amount / geometry
# ---------------------------------------------------------------------------
def confidence_ellipse_area(xy, conf=0.95):
    """
    Area of the confidence ellipse of a 2-D point cloud (e.g. a
    centre-of-pressure trace).

    The ellipse is the standard bivariate-Gaussian confidence region
    ``area = pi * chi2_conf,2df * sqrt(det Cov)`` where ``Cov`` is the
    2x2 covariance of the (mean-removed) points. For a CoP sway path this
    is the classic 95% "sway-ellipse area".

    Source: still standing study (Jensenius), HpSp balance analysis.

    Args:
        xy (np.ndarray): Point cloud of shape ``(T, 2)``.
        conf (float, optional): Confidence level in ``(0, 1)``. Defaults to
            0.95.

    Returns:
        float: Ellipse area in squared position units (e.g. mm^2), or
            ``nan`` if fewer than three finite points are available.
    """
    from scipy.stats import chi2

    xy = np.asarray(xy, dtype=float)
    xy = xy[np.isfinite(xy).all(axis=1)]
    if len(xy) < 3:
        return np.nan
    cov = np.cov(xy.T)
    return float(np.pi * chi2.ppf(conf, 2) * np.sqrt(max(np.linalg.det(cov), 0.0)))


def convex_hull_area(xy):
    """
    Area of the 2-D convex hull of a point cloud.

    A non-parametric alternative to :func:`confidence_ellipse_area` for the
    region occupied by a sway path: it makes no Gaussian assumption and is
    driven by the outermost excursions.

    Source: still standing study (Jensenius); complements the confidence
    ellipse used in the balance reports.

    Args:
        xy (np.ndarray): Point cloud of shape ``(T, 2)``.

    Returns:
        float: Convex-hull area in squared position units, or ``nan`` if
            fewer than three non-collinear finite points are available.
    """
    from scipy.spatial import ConvexHull, QhullError

    xy = np.asarray(xy, dtype=float)
    xy = xy[np.isfinite(xy).all(axis=1)]
    if len(xy) < 3:
        return np.nan
    try:
        return float(ConvexHull(xy).volume)  # 2-D "volume" == area
    except QhullError:
        return np.nan


def cop_sway_metrics(xy, t=None, fs=None, *, freq_band=(0.1, 5.0),
                     resample_fs=50.0):
    """
    Standard centre-of-pressure (CoP) sway metrics from a 2-D sway path.

    Computes the classic posturographic descriptors: CoP path length and
    path rate, the 95% confidence-ellipse area, medio-lateral (ML) and
    antero-posterior (AP) ranges and standard deviations, the AP/ML range
    and SD ratios, and the mean sway frequency of each axis (the
    power-weighted mean frequency of a Welch spectrum inside ``freq_band``,
    computed on a uniform grid at ``resample_fs``).

    The first column of ``xy`` is treated as ML and the second as AP,
    matching the study convention. Sampling time may be given either as an
    explicit time vector ``t`` (seconds; may be irregular) or a constant
    rate ``fs`` (Hz); if neither is supplied a rate of 1 Hz is assumed.

    Source: still standing study (Jensenius), HpSp balance analysis
    (``analyze_balance``).

    Args:
        xy (np.ndarray): CoP path of shape ``(T, 2)`` as ``[ML, AP]`` in
            position units (e.g. mm).
        t (np.ndarray, optional): Per-sample timestamps in seconds. May be
            irregular. Defaults to None.
        fs (float, optional): Constant sampling rate in Hz, used when ``t``
            is not given. Defaults to None (interpreted as 1 Hz).
        freq_band (tuple, optional): ``(low, high)`` band in Hz for the mean
            sway frequency. Defaults to ``(0.1, 5.0)``.
        resample_fs (float, optional): Uniform rate in Hz onto which the
            path is interpolated before the spectral estimate. Defaults to
            50.0.

    Returns:
        dict: Metrics with keys ``n``, ``dur``, ``fs_mean``, ``path_len``,
            ``path_rate``, ``area95``, ``ml_range``, ``ap_range``,
            ``ml_sd``, ``ap_sd``, ``ap_ml_range_ratio``,
            ``ap_ml_sd_ratio``, ``mf_ml``, ``mf_ap`` and ``mf_mean``.
    """
    from scipy import signal as _sig

    xy = np.asarray(xy, dtype=float)
    if xy.ndim != 2 or xy.shape[1] != 2:
        raise ValueError("xy must have shape (T, 2)")
    ml = xy[:, 0]
    ap = xy[:, 1]
    n = len(xy)

    if t is not None:
        t = np.asarray(t, dtype=float)
        t = t - t[0]
    elif fs is not None:
        t = np.arange(n) / float(fs)
    else:
        t = np.arange(n, dtype=float)
    dur = float(t[-1]) if n > 1 else 0.0
    fs_mean = (n - 1) / dur if dur > 0 else np.nan

    ml_c = ml - np.nanmean(ml)
    ap_c = ap - np.nanmean(ap)

    dpath = np.sqrt(np.diff(ml) ** 2 + np.diff(ap) ** 2)
    path_len = float(np.nansum(dpath))
    path_rate = path_len / dur if dur > 0 else np.nan

    ml_range = float(np.nanmax(ml) - np.nanmin(ml))
    ap_range = float(np.nanmax(ap) - np.nanmin(ap))
    ml_sd = float(np.nanstd(ml, ddof=1))
    ap_sd = float(np.nanstd(ap, ddof=1))

    area95 = confidence_ellipse_area(np.column_stack([ml_c, ap_c]), conf=0.95)

    lo, hi = freq_band
    tu = np.arange(0, dur, 1.0 / resample_fs) if dur > 0 else np.array([])

    def _mean_freq(x):
        if len(tu) < 4:
            return np.nan
        xu = np.interp(tu, t, x)
        xu = _sig.detrend(xu)
        nperseg = min(len(xu), int(resample_fs * 20))
        if nperseg < 4:
            return np.nan
        f, P = _sig.welch(xu, fs=resample_fs, nperseg=nperseg)
        band = (f >= lo) & (f <= hi)
        if P[band].sum() <= 0:
            return np.nan
        return float(np.sum(f[band] * P[band]) / np.sum(P[band]))

    mf_ml = _mean_freq(ml_c)
    mf_ap = _mean_freq(ap_c)

    return dict(
        n=n, dur=dur, fs_mean=fs_mean,
        path_len=path_len, path_rate=path_rate, area95=area95,
        ml_range=ml_range, ap_range=ap_range, ml_sd=ml_sd, ap_sd=ap_sd,
        ap_ml_range_ratio=ap_range / ml_range if ml_range else np.nan,
        ap_ml_sd_ratio=ap_sd / ml_sd if ml_sd else np.nan,
        mf_ml=mf_ml, mf_ap=mf_ap, mf_mean=float(np.nanmean([mf_ml, mf_ap])),
    )


# ---------------------------------------------------------------------------
# Control dynamics / complexity
# ---------------------------------------------------------------------------
def principal_axis_projection(xy):
    """
    Project a 2-D (or N-D) point cloud onto its principal axis.

    Runs a PCA on the mean-removed points and returns the 1-D coordinate
    along the direction of greatest variance -- the natural 1-D reduction of
    a sway path used by the dynamics/complexity measures. The PCA eigenvector
    sign is arbitrary; the projection may be globally flipped across calls or
    datasets.

    Source: still standing study (Jensenius), sway-dynamics analysis.

    Args:
        xy (np.ndarray): Point cloud of shape ``(T, D)`` (typically
            ``D == 2``).

    Returns:
        np.ndarray: 1-D projection of shape ``(T,)``.
    """
    xy = np.asarray(xy, dtype=float)
    xy = xy - xy.mean(axis=0)
    cov = np.cov(xy.T)
    w, v = np.linalg.eigh(cov)
    return xy @ v[:, -1]  # eigvecs ascending -> last is major axis


def stabilogram_diffusion(xy, fs, *, short_max_s=0.6, long_min_s=1.5,
                          n_lags=40):
    """
    Collins-De Luca stabilogram-diffusion analysis (SDA) of a sway path.

    Fits the mean-square-displacement (MSD) curve
    ``<[r(t+dt) - r(t)]^2>`` versus time-lag ``dt`` in log-log space and
    reports a short-term and a long-term Hurst exponent (each ``slope / 2``)
    plus the critical crossover time where the two regression lines
    intersect. Persistent (open-loop) drift gives a short-term Hurst above
    0.5; anti-persistent (closed-loop correction) gives a long-term Hurst
    below 0.5.

    Source: still standing study (Jensenius), sway-dynamics analysis;
    method of Collins & De Luca (1993).

    Args:
        xy (np.ndarray): Sway path of shape ``(T, D)`` (``D >= 1``). A 1-D
            input of shape ``(T,)`` is accepted and treated as a single
            axis.
        fs (float): Sampling rate in Hz.
        short_max_s (float, optional): Upper bound (s) of the short-term
            fitting window. Defaults to 0.6.
        long_min_s (float, optional): Lower bound (s) of the long-term
            fitting window. Defaults to 1.5.
        n_lags (int, optional): Number of log-spaced lags at which the MSD
            is evaluated. Defaults to 40.

    Returns:
        dict: ``{"H_short", "H_long", "crossover_s"}``. Entries are ``nan``
            when a window contains fewer than three usable lags.
    """
    xy = np.asarray(xy, dtype=float)
    if xy.ndim == 1:
        xy = xy[:, None]
    n = len(xy)
    if n < 8:
        return dict(H_short=np.nan, H_long=np.nan, crossover_s=np.nan)

    lags = np.unique(
        np.round(np.logspace(0, np.log10(max(n // 4, 2)), n_lags)).astype(int))
    lags = lags[lags >= 1]
    msd = np.array([np.mean(np.sum((xy[l:] - xy[:-l]) ** 2, axis=1))
                    for l in lags])
    t = lags / fs
    ok = msd > 0
    t, msd = t[ok], msd[ok]
    short = t < short_max_s
    long = t > long_min_s

    def _slope_intercept(mask):
        if mask.sum() < 3:
            return np.nan, np.nan
        a, b = np.polyfit(np.log(t[mask]), np.log(msd[mask]), 1)
        return a, b

    a_s, b_s = _slope_intercept(short)
    a_l, b_l = _slope_intercept(long)
    H_short = a_s / 2.0 if np.isfinite(a_s) else np.nan
    H_long = a_l / 2.0 if np.isfinite(a_l) else np.nan
    crossover = np.nan
    if np.isfinite(a_s) and np.isfinite(a_l) and abs(a_s - a_l) > 1e-9:
        crossover = float(np.exp((b_l - b_s) / (a_s - a_l)))
    return dict(H_short=float(H_short), H_long=float(H_long),
                crossover_s=crossover)


def dfa(x, *, n_scales=18, min_scale=10):
    """
    Detrended fluctuation analysis (DFA) scaling exponent.

    Integrates the mean-removed signal, then measures the RMS of the
    linearly-detrended integrated profile within non-overlapping windows of
    increasing size; the slope of ``log F(n)`` versus ``log n`` is the DFA
    exponent ``alpha``. White noise gives ``alpha ~= 0.5``; a random walk
    (Brownian) gives ``alpha ~= 1.5``; ``alpha == 1`` is 1/f noise.

    Source: still standing study (Jensenius), sway-complexity analysis;
    method of Peng et al. (1994).

    Args:
        x (np.ndarray): 1-D input signal.
        n_scales (int, optional): Number of log-spaced window sizes.
            Defaults to 18.
        min_scale (int, optional): Smallest window size in samples. Defaults
            to 10.

    Returns:
        float: The DFA exponent ``alpha`` (``nan`` if too short).
    """
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 4 * min_scale:
        return np.nan
    y = np.cumsum(x - x.mean())
    scales = np.unique(
        np.round(np.logspace(np.log10(min_scale),
                             np.log10(n // 4), n_scales)).astype(int))
    F = []
    used = []
    for m in scales:
        k = n // m
        if k < 1:
            continue
        seg = y[:k * m].reshape(k, m)
        tt = np.arange(m)
        rms = [np.sqrt(np.mean((s - np.polyval(np.polyfit(tt, s, 1), tt)) ** 2))
               for s in seg]
        fm = np.mean(rms)
        if fm > 0:
            F.append(fm)
            used.append(m)
    if len(F) < 2:
        return np.nan
    return float(np.polyfit(np.log(used), np.log(F), 1)[0])


def sample_entropy(x, m=2, r=0.2):
    """
    Sample entropy (SampEn) of a 1-D signal.

    Measures regularity/predictability: the negative log conditional
    probability that sequences close (within tolerance ``r``) for ``m``
    samples remain close for ``m + 1`` samples, self-matches excluded.
    Lower values mean more repetitive/predictable signals. The signal is
    z-scored internally so ``r`` is expressed as a fraction of its standard
    deviation. Neighbour counts use a Chebyshev (max-norm) KD-tree.

    Source: still standing study (Jensenius), sway-complexity analysis;
    method of Richman & Moorman (2000).

    Args:
        x (np.ndarray): 1-D input signal.
        m (int, optional): Embedding (template) length. Defaults to 2.
        r (float, optional): Tolerance as a fraction of the signal SD.
            Defaults to 0.2.

    Returns:
        float: Sample entropy (``nan`` if undefined, e.g. no matches).
    """
    from scipy.spatial import cKDTree

    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    N = len(x)
    if N < m + 2:
        return np.nan
    x = (x - x.mean()) / (x.std() + 1e-12)

    def _count(mm):
        emb = np.array([x[i:i + mm] for i in range(N - mm + 1)])
        tree = cKDTree(emb)
        pairs = tree.query_ball_point(emb, r, p=np.inf)
        return sum(len(p) - 1 for p in pairs)  # exclude self-match

    B = _count(m)
    A = _count(m + 1)
    if B == 0 or A == 0:
        return np.nan
    return float(-np.log(A / B))


def spectral_edges(x, fs, *, edges=(0.5, 0.95), nperseg=None):
    """
    Spectral-edge frequencies of a signal.

    Returns the frequencies below which a given cumulative fraction of the
    Welch power spectrum lies. With the default ``edges`` the first value is
    the median frequency (50% edge) and the second the 95% spectral-edge
    frequency, two standard descriptors of sway spectral shape.

    Source: still standing study (Jensenius), sway-dynamics analysis.

    Args:
        x (np.ndarray): 1-D input signal.
        fs (float): Sampling rate in Hz.
        edges (tuple, optional): Cumulative-power fractions in ``(0, 1)``.
            Defaults to ``(0.5, 0.95)``.
        nperseg (int, optional): Welch segment length in samples. Defaults
            to ``min(2048, len(x))``.

    Returns:
        dict: Mapping ``"f<pct>"`` (e.g. ``"f50"``, ``"f95"``) to the edge
            frequency in Hz.
    """
    from scipy import signal as _sig

    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 8:
        return {f"f{int(round(e * 100))}": np.nan for e in edges}
    if nperseg is None:
        nperseg = min(2048, len(x))
    f, P = _sig.welch(x - x.mean(), fs, nperseg=nperseg)
    cP = np.cumsum(P)
    if cP[-1] <= 0:
        return {f"f{int(round(e * 100))}": np.nan for e in edges}
    cP = cP / cP[-1]
    return {f"f{int(round(e * 100))}": float(np.interp(e, cP, f))
            for e in edges}


def sway_texture(speed, fs, *, frozen_threshold=2.0):
    """
    Micro-texture of a sway speed signal: frozen fraction and burst rate.

    Distinguishes a smooth wander from intermittent ballistic corrections.
    The frozen fraction is the share of time the speed is below
    ``frozen_threshold``; the burst rate is the number of upward threshold
    crossings (onset of a velocity burst) per minute.

    Source: still standing study (Jensenius), sway-texture analysis.

    Args:
        speed (np.ndarray): 1-D speed signal (e.g. mm/s).
        fs (float): Sampling rate in Hz.
        frozen_threshold (float, optional): Speed below which the signal is
            considered "frozen", in the units of ``speed``. Defaults to 2.0.

    Returns:
        dict: ``{"frozen_fraction", "burst_rate"}`` where ``burst_rate`` is
            in bursts per minute.
    """
    speed = np.asarray(speed, dtype=float)
    speed = speed[np.isfinite(speed)]
    if len(speed) < 2:
        return dict(frozen_fraction=np.nan, burst_rate=np.nan)
    frozen = float((speed < frozen_threshold).mean())
    above = (speed >= frozen_threshold).astype(int)
    bursts = int(np.sum(np.diff(above) == 1))
    minutes = len(speed) / fs / 60.0
    burst_rate = bursts / minutes if minutes > 0 else np.nan
    return dict(frozen_fraction=frozen, burst_rate=burst_rate)


# ---------------------------------------------------------------------------
# Direction / extent
# ---------------------------------------------------------------------------
def sway_orientation(xy):
    """
    Principal sway-axis orientation and anisotropy of a 2-D point cloud.

    A PCA of the mean-removed horizontal positions gives the orientation of
    the major axis as an axial angle in ``[0, 180)`` degrees (undirected --
    a line, not an arrow) and the anisotropy ``sqrt(lambda_max / lambda_min)``
    of the sway ellipse. Anisotropy 1.0 is isotropic/circular; values above
    ~1.3 indicate clearly directional sway.

    Source: still standing study (Jensenius), sway-direction analysis.

    Args:
        xy (np.ndarray): Point cloud of shape ``(T, 2)``.

    Returns:
        dict: ``{"angle_deg", "anisotropy"}``. Both are ``nan`` if the
            covariance is degenerate or there are too few finite points.
    """
    xy = np.asarray(xy, dtype=float)
    xy = xy[np.isfinite(xy).all(axis=1)]
    if len(xy) < 3:
        return dict(angle_deg=np.nan, anisotropy=np.nan)
    x = xy[:, 0] - xy[:, 0].mean()
    y = xy[:, 1] - xy[:, 1].mean()
    cov = np.cov(x, y)
    w, v = np.linalg.eigh(cov)  # ascending eigenvalues
    if w[0] <= 0:
        return dict(angle_deg=np.nan, anisotropy=np.nan)
    angle = float(np.degrees(np.arctan2(v[1, 1], v[0, 1])) % 180.0)
    anisotropy = float(np.sqrt(w[1] / w[0]))
    return dict(angle_deg=angle, anisotropy=anisotropy)


def axial_rayleigh(angles_deg):
    """
    Axial Rayleigh test for a preferred orientation among axial angles.

    Tests whether a sample of axial (undirected, ``[0, 180)`` deg) angles --
    e.g. per-session principal sway axes -- clusters around a common
    orientation. Angles are doubled to map the axial circle onto the full
    circle before computing the mean resultant length ``R`` and the Rayleigh
    p-value (small ``p`` with large ``R`` means a shared preferred axis).

    Source: still standing study (Jensenius), sway-direction analysis.

    Args:
        angles_deg (np.ndarray): Axial angles in degrees.

    Returns:
        dict: ``{"R", "p", "mean_axis_deg", "n"}``.
    """
    a = 2 * np.radians(np.asarray(angles_deg, dtype=float))
    a = a[np.isfinite(a)]
    n = len(a)
    if n < 2:
        return dict(R=np.nan, p=np.nan, mean_axis_deg=np.nan, n=n)
    C = np.mean(np.cos(a))
    S = np.mean(np.sin(a))
    R = float(np.hypot(C, S))
    Z = n * R * R
    p = float(np.exp(-Z) * (1 + (2 * Z - Z * Z) / (4 * n)))
    mean_axis = float(np.degrees(0.5 * np.arctan2(S, C)) % 180.0)
    return dict(R=R, p=p, mean_axis_deg=mean_axis, n=n)


def spatial_extent(pos, fs, *, ellipse_conf=0.95, window_s=20.0,
                   vertical_axis=None):
    """
    Spatial extent / occupied volume of a 3-D (or 2-D) position trace.

    Complements sway magnitude (QoM) by describing *how large a region* a
    marker occupies. Reports the RMS dispersion radius about the session
    centroid, the Gaussian confidence-ellipsoid volume and its cube-root
    radius, the mean within-window dispersion (which removes slow drift),
    and a drift ratio ``full_dispersion / within_window_dispersion`` (``> 1``
    when slow drift enlarges the occupied region over the session). When a
    ``vertical_axis`` is given the drift is additionally split into
    horizontal and vertical components.

    Source: still standing study (Jensenius), spatial-range analysis
    (``session_metrics``).

    Args:
        pos (np.ndarray): Position trace of shape ``(T, D)`` with ``D`` 2 or
            3, in position units (e.g. mm).
        fs (float): Sampling rate in Hz.
        ellipse_conf (float, optional): Confidence level for the ellipsoid
            volume. Defaults to 0.95.
        window_s (float, optional): Window length in seconds for the
            within-window dispersion. Defaults to 20.0.
        vertical_axis (int, optional): Index of the vertical axis (``0``,
            ``1`` or ``2``); when given, drift is decomposed into horizontal
            and vertical parts. Defaults to None.

    Returns:
        dict: ``dispersion``, ``ellipsoid_volume``, ``ellipsoid_radius``,
            ``within_window_dispersion``, ``drift_ratio`` and (when
            ``vertical_axis`` is set) ``drift_horizontal`` and
            ``drift_vertical``. Returns ``None`` if fewer than one window of
            finite samples is available.
    """
    from scipy.stats import chi2

    pos = np.asarray(pos, dtype=float)
    if pos.ndim != 2:
        raise ValueError("pos must have shape (T, D)")
    D = pos.shape[1]
    mask = np.isfinite(pos).all(axis=1)
    P = pos[mask]
    w = int(fs * window_s)
    if len(P) < max(w, D + 2):
        return None

    centroid = P.mean(axis=0)
    disp_vec = P - centroid
    d = np.sqrt((disp_vec * disp_vec).sum(axis=1))
    dispersion = float(np.sqrt((d * d).mean()))

    cov = np.cov(P.T)
    det = np.linalg.det(cov)
    chi_d = chi2.ppf(ellipse_conf, D)
    # volume of a D-dim Gaussian confidence ellipsoid
    if D == 2:
        vol = np.pi * chi_d * np.sqrt(max(det, 0.0))
    else:  # D == 3
        vol = (4.0 / 3.0) * np.pi * (chi_d ** 1.5) * np.sqrt(max(det, 0.0))
    ellipsoid_volume = float(vol)
    ellipsoid_radius = float(vol ** (1.0 / D))

    def _within_window(Q):
        cols = Q.shape[1] if Q.ndim == 2 else 1
        Q = Q.reshape(len(Q), cols)
        wr = []
        for s in range(0, len(Q) - w + 1, w):
            seg = Q[s:s + w]
            cc = seg.mean(axis=0)
            e = seg - cc
            wr.append(np.sqrt((e * e).sum(axis=1).mean()))
        return np.mean(wr) if wr else np.nan

    def _full_dispersion(Q):
        cols = Q.shape[1] if Q.ndim == 2 else 1
        Q = Q.reshape(len(Q), cols)
        cc = Q.mean(axis=0)
        e = Q - cc
        return np.sqrt((e * e).sum(axis=1).mean())

    win_disp = float(_within_window(P))
    drift_ratio = (dispersion / win_disp
                   if win_disp and win_disp > 0 else np.nan)

    out = dict(dispersion=dispersion, ellipsoid_volume=ellipsoid_volume,
               ellipsoid_radius=ellipsoid_radius,
               within_window_dispersion=win_disp, drift_ratio=drift_ratio)

    if vertical_axis is not None:
        hax = [k for k in range(D) if k != vertical_axis]

        def _comp_drift(cols):
            Q = P[:, cols]
            wm = _within_window(Q)
            full = _full_dispersion(Q)
            return full / wm if wm and wm > 0 else np.nan

        out["drift_horizontal"] = float(_comp_drift(hax))
        out["drift_vertical"] = float(_comp_drift([vertical_axis]))

    return out

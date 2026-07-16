# Posture

> Auto-generated documentation for [musicalgestures._posture](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py) module.

Posturography and standstill-sway metrics for centre-of-pressure (CoP) and
head/marker position signals.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Posture
    - [axial_rayleigh](#axial_rayleigh)
    - [confidence_ellipse_area](#confidence_ellipse_area)
    - [convex_hull_area](#convex_hull_area)
    - [cop_sway_metrics](#cop_sway_metrics)
    - [dfa](#dfa)
    - [principal_axis_projection](#principal_axis_projection)
    - [sample_entropy](#sample_entropy)
    - [spatial_extent](#spatial_extent)
    - [spectral_edges](#spectral_edges)
    - [stabilogram_diffusion](#stabilogram_diffusion)
    - [sway_orientation](#sway_orientation)
    - [sway_texture](#sway_texture)

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

## axial_rayleigh

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L499)

```python
def axial_rayleigh(angles_deg):
```

Axial Rayleigh test for a preferred orientation among axial angles.

Tests whether a sample of axial (undirected, ``[0, 180)`` deg) angles --
e.g. per-session principal sway axes -- clusters around a common
orientation. Angles are doubled to map the axial circle onto the full
circle before computing the mean resultant length ``R`` and the Rayleigh
p-value (small ``p`` with large ``R`` means a shared preferred axis).

Source: still standing study (Jensenius), sway-direction analysis.

#### Arguments

- `angles_deg` *np.ndarray* - Axial angles in degrees.

#### Returns

- `dict` - ``{"R", "p", "mean_axis_deg", "n"}``.

## confidence_ellipse_area

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L34)

```python
def confidence_ellipse_area(xy, conf=0.95):
```

Area of the confidence ellipse of a 2-D point cloud (e.g. a
centre-of-pressure trace).

The ellipse is the standard bivariate-Gaussian confidence region
``area = pi * chi2_conf,2df * sqrt(det Cov)`` where ``Cov`` is the
2x2 covariance of the (mean-removed) points. For a CoP sway path this
is the classic 95% "sway-ellipse area".

Source: still standing study (Jensenius), HpSp balance analysis.

#### Arguments

- `xy` *np.ndarray* - Point cloud of shape ``(T, 2)``.
- `conf` *float, optional* - Confidence level in ``(0, 1)``. Defaults to
    0.95.

#### Returns

- `float` - Ellipse area in squared position units (e.g. mm^2), or
    ``nan`` if fewer than three finite points are available.

## convex_hull_area

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L65)

```python
def convex_hull_area(xy):
```

Area of the 2-D convex hull of a point cloud.

A non-parametric alternative to :func:[confidence_ellipse_area](#confidence_ellipse_area) for the
region occupied by a sway path: it makes no Gaussian assumption and is
driven by the outermost excursions.

Source: still standing study (Jensenius); complements the confidence
ellipse used in the balance reports.

#### Arguments

- `xy` *np.ndarray* - Point cloud of shape ``(T, 2)``.

#### Returns

- `float` - Convex-hull area in squared position units, or ``nan`` if
    fewer than three non-collinear finite points are available.

## cop_sway_metrics

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L95)

```python
def cop_sway_metrics(
    xy,
    t=None,
    fs=None,
    freq_band=(0.1, 5.0),
    resample_fs=50.0,
):
```

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

#### Arguments

- `xy` *np.ndarray* - CoP path of shape ``(T, 2)`` as ``[ML, AP]`` in
    position units (e.g. mm).
- `t` *np.ndarray, optional* - Per-sample timestamps in seconds. May be
    irregular. Defaults to None.
- `fs` *float, optional* - Constant sampling rate in Hz, used when ``t``
    is not given. Defaults to None (interpreted as 1 Hz).
- `freq_band` *tuple, optional* - ``(low, high)`` band in Hz for the mean
    sway frequency. Defaults to ``(0.1, 5.0)``.
- `resample_fs` *float, optional* - Uniform rate in Hz onto which the
    path is interpolated before the spectral estimate. Defaults to
    50.0.

#### Returns

- `dict` - Metrics with keys ``n``, ``dur``, ``fs_mean``, ``path_len``,
    ``path_rate``, ``area95``, ``ml_range``, ``ap_range``,
    ``ml_sd``, ``ap_sd``, ``ap_ml_range_ratio``,
    ``ap_ml_sd_ratio``, ``mf_ml``, ``mf_ap`` and ``mf_mean``.

## dfa

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L293)

```python
def dfa(x, n_scales=18, min_scale=10):
```

Detrended fluctuation analysis (DFA) scaling exponent.

Integrates the mean-removed signal, then measures the RMS of the
linearly-detrended integrated profile within non-overlapping windows of
increasing size; the slope of ``log F(n)`` versus ``log n`` is the DFA
exponent ``alpha``. White noise gives ``alpha ~= 0.5``; a random walk
(Brownian) gives ``alpha ~= 1.5``; ``alpha == 1`` is 1/f noise.

Source: still standing study (Jensenius), sway-complexity analysis;
method of Peng et al. (1994).

#### Arguments

- `x` *np.ndarray* - 1-D input signal.
- `n_scales` *int, optional* - Number of log-spaced window sizes.
    Defaults to 18.
- `min_scale` *int, optional* - Smallest window size in samples. Defaults
    to 10.

#### Returns

- `float` - The DFA exponent ``alpha`` (``nan`` if too short).

## principal_axis_projection

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L200)

```python
def principal_axis_projection(xy):
```

Project a 2-D (or N-D) point cloud onto its principal axis.

Runs a PCA on the mean-removed points and returns the 1-D coordinate
along the direction of greatest variance -- the natural 1-D reduction of
a sway path used by the dynamics/complexity measures. The PCA eigenvector
sign is arbitrary; the projection may be globally flipped across calls or
datasets.

Source: still standing study (Jensenius), sway-dynamics analysis.

#### Arguments

- `xy` *np.ndarray* - Point cloud of shape ``(T, D)`` (typically
    ``D == 2``).

#### Returns

- `np.ndarray` - 1-D projection of shape ``(T,)``.

## sample_entropy

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L344)

```python
def sample_entropy(x, m=2, r=0.2):
```

Sample entropy (SampEn) of a 1-D signal.

Measures regularity/predictability: the negative log conditional
probability that sequences close (within tolerance ``r``) for ``m``
samples remain close for ``m + 1`` samples, self-matches excluded.
Lower values mean more repetitive/predictable signals. The signal is
z-scored internally so ``r`` is expressed as a fraction of its standard
deviation. Neighbour counts use a Chebyshev (max-norm) KD-tree.

Source: still standing study (Jensenius), sway-complexity analysis;
method of Richman & Moorman (2000).

#### Arguments

- `x` *np.ndarray* - 1-D input signal.
- `m` *int, optional* - Embedding (template) length. Defaults to 2.
- `r` *float, optional* - Tolerance as a fraction of the signal SD.
    Defaults to 0.2.

#### Returns

- `float` - Sample entropy (``nan`` if undefined, e.g. no matches).

## spatial_extent

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L531)

```python
def spatial_extent(
    pos,
    fs,
    ellipse_conf=0.95,
    window_s=20.0,
    vertical_axis=None,
):
```

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

#### Arguments

- `pos` *np.ndarray* - Position trace of shape ``(T, D)`` with ``D`` 2 or
    3, in position units (e.g. mm).
- `fs` *float* - Sampling rate in Hz.
- `ellipse_conf` *float, optional* - Confidence level for the ellipsoid
    volume. Defaults to 0.95.
- `window_s` *float, optional* - Window length in seconds for the
    within-window dispersion. Defaults to 20.0.
- `vertical_axis` *int, optional* - Index of the vertical axis (``0``,
    ``1`` or ``2``); when given, drift is decomposed into horizontal
    and vertical parts. Defaults to None.

#### Returns

- `dict` - ``dispersion``, ``ellipsoid_volume``, ``ellipsoid_radius``,
    ``within_window_dispersion``, ``drift_ratio`` and (when
    ``vertical_axis`` is set) ``drift_horizontal`` and
    ``drift_vertical``. Returns ``None`` if fewer than one window of
    finite samples is available.

## spectral_edges

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L389)

```python
def spectral_edges(x, fs, edges=(0.5, 0.95), nperseg=None):
```

Spectral-edge frequencies of a signal.

Returns the frequencies below which a given cumulative fraction of the
Welch power spectrum lies. With the default ``edges`` the first value is
the median frequency (50% edge) and the second the 95% spectral-edge
frequency, two standard descriptors of sway spectral shape.

Source: still standing study (Jensenius), sway-dynamics analysis.

#### Arguments

- `x` *np.ndarray* - 1-D input signal.
- `fs` *float* - Sampling rate in Hz.
- `edges` *tuple, optional* - Cumulative-power fractions in ``(0, 1)``.
    Defaults to ``(0.5, 0.95)``.
- `nperseg` *int, optional* - Welch segment length in samples. Defaults
    to ``min(2048, len(x))``.

#### Returns

- `dict` - Mapping ``"f<pct>"`` (e.g. ``"f50"``, ``"f95"``) to the edge
    frequency in Hz.

## stabilogram_diffusion

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L226)

```python
def stabilogram_diffusion(xy, fs, short_max_s=0.6, long_min_s=1.5, n_lags=40):
```

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

#### Arguments

- `xy` *np.ndarray* - Sway path of shape ``(T, D)`` (``D >= 1``). A 1-D
    input of shape ``(T,)`` is accepted and treated as a single
    axis.
- `fs` *float* - Sampling rate in Hz.
- `short_max_s` *float, optional* - Upper bound (s) of the short-term
    fitting window. Defaults to 0.6.
- `long_min_s` *float, optional* - Lower bound (s) of the long-term
    fitting window. Defaults to 1.5.
- `n_lags` *int, optional* - Number of log-spaced lags at which the MSD
    is evaluated. Defaults to 40.

#### Returns

- `dict` - ``{"H_short", "H_long", "crossover_s"}``. Entries are ``nan``
    when a window contains fewer than three usable lags.

## sway_orientation

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L465)

```python
def sway_orientation(xy):
```

Principal sway-axis orientation and anisotropy of a 2-D point cloud.

A PCA of the mean-removed horizontal positions gives the orientation of
the major axis as an axial angle in ``[0, 180)`` degrees (undirected --
a line, not an arrow) and the anisotropy ``sqrt(lambda_max / lambda_min)``
of the sway ellipse. Anisotropy 1.0 is isotropic/circular; values above
~1.3 indicate clearly directional sway.

Source: still standing study (Jensenius), sway-direction analysis.

#### Arguments

- `xy` *np.ndarray* - Point cloud of shape ``(T, 2)``.

#### Returns

- `dict` - ``{"angle_deg", "anisotropy"}``. Both are ``nan`` if the
    covariance is degenerate or there are too few finite points.

## sway_texture

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posture.py#L429)

```python
def sway_texture(speed, fs, frozen_threshold=2.0):
```

Micro-texture of a sway speed signal: frozen fraction and burst rate.

Distinguishes a smooth wander from intermittent ballistic corrections.
The frozen fraction is the share of time the speed is below
``frozen_threshold``; the burst rate is the number of upward threshold
crossings (onset of a velocity burst) per minute.

Source: still standing study (Jensenius), sway-texture analysis.

#### Arguments

- `speed` *np.ndarray* - 1-D speed signal (e.g. mm/s).
- `fs` *float* - Sampling rate in Hz.
- `frozen_threshold` *float, optional* - Speed below which the signal is
    considered "frozen", in the units of ``speed``. Defaults to 2.0.

#### Returns

- `dict` - ``{"frozen_fraction", "burst_rate"}`` where ``burst_rate`` is
    in bursts per minute.

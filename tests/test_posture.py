"""Tests for musicalgestures._posture (posturography / sway metrics).

All ground truth is synthetic -- no data files. Circular CoP paths give
closed-form path length and ellipse area; anisotropic Gaussian clouds give a
known orientation and anisotropy; drifting vs stationary random walks give a
drift-ratio separation; white noise validates the from-scratch DFA and SDA
implementations (alpha ~= 0.5, H ~= 0.5); a sine validates that sample entropy
is low relative to its shuffle.
"""
import numpy as np
import pytest

from musicalgestures import (
    cop_sway_metrics,
    confidence_ellipse_area,
    convex_hull_area,
    stabilogram_diffusion,
    dfa,
    sample_entropy,
    spectral_edges,
    sway_texture,
    sway_orientation,
    axial_rayleigh,
    spatial_extent,
    principal_axis_projection,
)


class TestCopSwayMetrics:
    def test_circular_path_length_and_ellipse(self):
        # A circle of radius R sampled densely: path length -> 2*pi*R, and
        # the covariance of a uniform circle is (R^2/2) I, so the 95%
        # ellipse area is pi * chi2_.95,2 * R^2/2.
        from scipy.stats import chi2
        R = 10.0
        fs = 100.0
        n = 4000
        theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
        xy = np.column_stack([R * np.cos(theta), R * np.sin(theta)])
        m = cop_sway_metrics(xy, fs=fs)
        assert m["path_len"] == pytest.approx(2 * np.pi * R, rel=1e-3)
        expected_area = np.pi * chi2.ppf(0.95, 2) * (R ** 2 / 2.0)
        assert m["area95"] == pytest.approx(expected_area, rel=0.02)

    def test_path_rate_uses_duration(self):
        R = 5.0
        fs = 50.0
        n = 2000
        theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
        xy = np.column_stack([R * np.cos(theta), R * np.sin(theta)])
        m = cop_sway_metrics(xy, fs=fs)
        dur = (n - 1) / fs
        assert m["path_rate"] == pytest.approx(2 * np.pi * R / dur, rel=1e-2)

    def test_ap_dominant_sway_ratio(self):
        # AP (col 1) has larger amplitude than ML (col 0).
        rng = np.random.default_rng(0)
        fs = 50.0
        n = 5000
        ml = 1.0 * rng.standard_normal(n)
        ap = 3.0 * rng.standard_normal(n)
        m = cop_sway_metrics(np.column_stack([ml, ap]), fs=fs)
        assert m["ap_ml_sd_ratio"] == pytest.approx(3.0, rel=0.1)

    def test_mean_sway_frequency(self):
        # A pure 0.5 Hz oscillation on both axes -> mean freq ~ 0.5 Hz.
        fs = 50.0
        t = np.arange(0, 120, 1 / fs)
        f0 = 0.5
        xy = np.column_stack([np.sin(2 * np.pi * f0 * t),
                              np.cos(2 * np.pi * f0 * t)])
        m = cop_sway_metrics(xy, fs=fs)
        assert m["mf_mean"] == pytest.approx(f0, abs=0.05)

    def test_accepts_time_vector(self):
        R = 4.0
        n = 1000
        t = np.linspace(0, 20, n)
        theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
        xy = np.column_stack([R * np.cos(theta), R * np.sin(theta)])
        m = cop_sway_metrics(xy, t=t)
        assert m["dur"] == pytest.approx(20.0, rel=1e-6)


class TestEllipseAndHull:
    def test_ellipse_area_matches_formula(self):
        from scipy.stats import chi2
        rng = np.random.default_rng(1)
        sx, sy = 2.0, 5.0
        xy = np.column_stack([sx * rng.standard_normal(20000),
                              sy * rng.standard_normal(20000)])
        area = confidence_ellipse_area(xy, conf=0.95)
        expected = np.pi * chi2.ppf(0.95, 2) * sx * sy
        assert area == pytest.approx(expected, rel=0.05)

    def test_convex_hull_of_square(self):
        # Dense fill of a 4x6 rectangle -> hull area ~ 24.
        rng = np.random.default_rng(2)
        xy = np.column_stack([rng.uniform(0, 4, 5000),
                              rng.uniform(0, 6, 5000)])
        assert convex_hull_area(xy) == pytest.approx(24.0, rel=0.05)

    def test_degenerate_inputs(self):
        assert np.isnan(confidence_ellipse_area(np.zeros((2, 2))))
        assert np.isnan(convex_hull_area(np.zeros((2, 2))))


class TestSwayOrientation:
    def test_known_angle_and_anisotropy(self):
        # Anisotropic Gaussian cloud rotated by 30 deg: major axis 5, minor 1.
        rng = np.random.default_rng(3)
        n = 20000
        major = 5.0 * rng.standard_normal(n)
        minor = 1.0 * rng.standard_normal(n)
        phi = np.radians(30.0)
        Rm = np.array([[np.cos(phi), -np.sin(phi)],
                       [np.sin(phi), np.cos(phi)]])
        xy = (Rm @ np.vstack([major, minor])).T
        out = sway_orientation(xy)
        assert out["angle_deg"] == pytest.approx(30.0, abs=2.0)
        assert out["anisotropy"] == pytest.approx(5.0, rel=0.1)

    def test_isotropic_is_low_anisotropy(self):
        rng = np.random.default_rng(4)
        xy = rng.standard_normal((20000, 2))
        assert sway_orientation(xy)["anisotropy"] < 1.1


class TestAxialRayleigh:
    def test_clustered_axes_significant(self):
        rng = np.random.default_rng(5)
        angles = (45.0 + 3.0 * rng.standard_normal(40)) % 180.0
        out = axial_rayleigh(angles)
        assert out["R"] > 0.9
        assert out["p"] < 1e-6
        assert out["mean_axis_deg"] == pytest.approx(45.0, abs=3.0)

    def test_uniform_axes_not_significant(self):
        angles = np.linspace(0, 180, 60, endpoint=False)
        out = axial_rayleigh(angles)
        assert out["R"] < 0.1
        assert out["p"] > 0.2


class TestSpatialExtent:
    def test_drift_ratio_separates_drift_from_stationary(self):
        rng = np.random.default_rng(6)
        fs = 50.0
        n = 30000  # 600 s
        # stationary: white jitter about a fixed point (no slow drift)
        stat = 2.0 * rng.standard_normal((n, 3))
        # drifting: random walk that wanders over the session
        steps = 0.5 * rng.standard_normal((n, 3))
        drift = np.cumsum(steps, axis=0)
        m_stat = spatial_extent(stat, fs, window_s=20.0)
        m_drift = spatial_extent(drift, fs, window_s=20.0)
        assert m_stat["drift_ratio"] == pytest.approx(1.0, abs=0.2)
        assert m_drift["drift_ratio"] > 2.0

    def test_vertical_split(self):
        rng = np.random.default_rng(7)
        fs = 50.0
        n = 20000
        pos = rng.standard_normal((n, 3))
        # add a slow vertical (axis 2) drift only
        pos[:, 2] += np.linspace(0, 200, n)
        m = spatial_extent(pos, fs, window_s=20.0, vertical_axis=2)
        assert m["drift_vertical"] > m["drift_horizontal"]

    def test_too_short_returns_none(self):
        assert spatial_extent(np.zeros((10, 3)), fs=50.0) is None


class TestDynamicsKnownAnswers:
    def test_dfa_white_noise(self):
        rng = np.random.default_rng(10)
        x = rng.standard_normal(20000)
        alpha = dfa(x)
        assert alpha == pytest.approx(0.5, abs=0.1)

    def test_dfa_random_walk(self):
        rng = np.random.default_rng(11)
        x = np.cumsum(rng.standard_normal(20000))
        alpha = dfa(x)
        # Brownian motion -> alpha ~ 1.5
        assert alpha == pytest.approx(1.5, abs=0.15)

    def test_sda_random_walk_hurst(self):
        # Collins-De Luca SDA operates on the CoP *trajectory*, modelled as a
        # diffusion process. A pure random walk (Brownian trajectory) has
        # MSD ~ dt^1, so the Hurst exponent (slope/2) is ~0.5 on all scales.
        rng = np.random.default_rng(12)
        fs = 50.0
        xy = np.cumsum(rng.standard_normal((20000, 2)), axis=0)
        out = stabilogram_diffusion(xy, fs)
        assert out["H_short"] == pytest.approx(0.5, abs=0.15)
        assert out["H_long"] == pytest.approx(0.5, abs=0.2)

    def test_sda_white_noise_positions_flat(self):
        # White-noise *positions* (no diffusion): MSD is flat vs lag, so the
        # short-scale Hurst collapses toward 0 -- a useful sanity contrast to
        # the random-walk case above.
        rng = np.random.default_rng(15)
        fs = 50.0
        xy = rng.standard_normal((20000, 2))
        out = stabilogram_diffusion(xy, fs)
        assert out["H_short"] < 0.15

    def test_sample_entropy_sine_low_vs_shuffled_high(self):
        t = np.linspace(0, 40 * np.pi, 3000)
        sine = np.sin(t)
        rng = np.random.default_rng(13)
        shuffled = sine.copy()
        rng.shuffle(shuffled)
        se_sine = sample_entropy(sine, m=2, r=0.2)
        se_shuf = sample_entropy(shuffled, m=2, r=0.2)
        assert se_sine < se_shuf
        assert se_sine < 0.5

    def test_spectral_edges_of_lowpass_signal(self):
        # A 0.5 Hz sine: essentially all power at 0.5 Hz -> both edges ~0.5.
        fs = 50.0
        t = np.arange(0, 200, 1 / fs)
        x = np.sin(2 * np.pi * 0.5 * t)
        edges = spectral_edges(x, fs)
        assert edges["f50"] == pytest.approx(0.5, abs=0.1)
        assert edges["f95"] == pytest.approx(0.5, abs=0.2)

    def test_sway_texture_frozen_fraction(self):
        # Speed below threshold 80% of the time.
        fs = 50.0
        n = 10000
        speed = np.concatenate([np.full(8000, 0.5), np.full(2000, 10.0)])
        out = sway_texture(speed, fs, frozen_threshold=2.0)
        assert out["frozen_fraction"] == pytest.approx(0.8, abs=0.01)

    def test_principal_axis_projection_recovers_major_axis(self):
        rng = np.random.default_rng(14)
        n = 5000
        major = 10.0 * rng.standard_normal(n)
        minor = 0.5 * rng.standard_normal(n)
        xy = np.column_stack([major, minor])
        proj = principal_axis_projection(xy)
        # projection should be almost perfectly correlated with the major axis
        assert abs(np.corrcoef(proj, major)[0, 1]) > 0.99

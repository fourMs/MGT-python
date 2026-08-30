"""The Effort layer's validation tiers, from the 2026-08-30 design.

Every factor is MGT's own operationalisation of Laban's category, and every claim a
docstring makes is measured here first. SPARC carries the heaviest burden: the
textbook minimum-jerk ordering, the tracker-noise robustness that is its reason to
exist, and a dev-only cross-check against the lab that originated the line.
"""
import numpy as np
import pytest

from musicalgestures._effort import (
    effort_flow, effort_profile, effort_space, effort_time, effort_weight, sparc)

FS = 100.0


def min_jerk_speed(n_sub=1, duration=1.0, fs=FS, gap=0.9):
    """A speed profile of `n_sub` minimum-jerk submovements, the canonical case."""
    t = np.arange(0, duration + (n_sub - 1) * gap + 0.5, 1 / fs)
    v = np.zeros_like(t)
    for k in range(n_sub):
        tau = np.clip((t - k * gap) / duration, 0, 1)
        v += 30 * (tau ** 2 - 2 * tau ** 3 + tau ** 4)
    return v


class TestSparc:
    def test_the_textbook_ordering(self):
        """1, 2 and 3 submovements must order as the survey measured: about
        -1.45, -2.22, -2.59."""
        s1 = sparc(min_jerk_speed(1), FS)
        s2 = sparc(min_jerk_speed(2), FS)
        s3 = sparc(min_jerk_speed(3), FS)
        assert s1 > s2 > s3
        assert abs(s1 - -1.45) < 0.35
        assert abs(s3 - -2.59) < 0.6

    def test_tracker_noise_barely_moves_it(self):
        """Under 10 per cent noise SPARC stays near its clean value while still
        separating submovement count --- the property that is its reason to exist."""
        rng = np.random.default_rng(3)
        clean = min_jerk_speed(1)
        noisy = clean + 0.10 * clean.max() * rng.standard_normal(clean.size)
        s_clean, s_noisy = sparc(clean, FS), sparc(np.abs(noisy), FS)
        s_three = sparc(min_jerk_speed(3), FS)
        assert abs(s_noisy - s_clean) < 0.35
        assert s_noisy > s_three + 0.4

    def test_agrees_with_the_originating_lab(self):
        """Dev-only cross-check against pyeyesweb's SPARC on the canonical profile."""
        pytest.importorskip("pyeyesweb")
        from pyeyesweb.utils.math_utils import compute_sparc
        v = min_jerk_speed(2)
        theirs = float(compute_sparc(v, rate_hz=FS, max_fc=10.0))
        assert abs(sparc(v, FS) - theirs) < 0.12


class TestFactors:
    def test_time_reads_bursts_as_more_sudden_than_a_plateau(self):
        burst = np.zeros(1000)
        burst[100:120] = 5.0
        burst[600:620] = 5.0
        plateau = np.full(1000, 0.2)
        assert effort_time(burst, FS) > effort_time(plateau, FS)

    def test_flow_reads_jitter_as_more_bound_than_a_reach(self):
        rng = np.random.default_rng(5)
        smooth = min_jerk_speed(1)
        jittery = np.abs(smooth + 0.3 * smooth.max() * rng.standard_normal(smooth.size))
        assert effort_flow(jittery, FS) > effort_flow(smooth, FS)

    def test_space_reads_a_line_as_direct_and_a_walk_as_indirect(self):
        t = np.linspace(0, 10, 1000)
        line = np.column_stack([t, 2 * t])
        rng = np.random.default_rng(7)
        walk = np.cumsum(rng.standard_normal((1000, 2)), axis=0)
        d_line = effort_space(line, FS, window_s=2.0)
        d_walk = effort_space(walk, FS, window_s=2.0)
        assert np.nanmean(d_line) > 0.99
        assert np.nanmean(d_walk) < 0.6

    def test_weight_reads_hard_peaks_as_stronger_than_gentle_drift(self):
        t = np.arange(0, 10, 1 / FS)
        gentle = 0.5 + 0.1 * np.sin(t)
        hard = np.abs(3.0 * np.sin(8 * t)) ** 3
        assert effort_weight(hard, FS) > effort_weight(gentle, FS)


class TestProfile:
    def test_every_factor_arrives_windowed_on_one_clock(self):
        rng = np.random.default_rng(11)
        xy = np.cumsum(rng.standard_normal((3000, 2)), axis=0)
        p = effort_profile(xy, FS, window_s=5.0)
        n = len(p["time"])
        assert n == 3000 // int(5.0 * FS)
        for key in ("time_index", "weight", "space", "flow"):
            assert len(p[key]) == n, key

    def test_a_short_window_is_nan_not_a_guess(self):
        xy = np.zeros((40, 2))
        p = effort_profile(xy, FS, window_s=5.0)
        assert len(p["time"]) == 0

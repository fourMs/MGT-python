"""Tests for musicalgestures._alignment (lead/lag, matching, coupling profiles).

All ground truth is synthetic: lagged envelopes with known shifts, event
lists with known offsets, and signals with a built-in coupling change.
"""
import numpy as np
import pytest

from musicalgestures import (
    xcorr_lag,
    envelope_lag,
    per_cycle_motion_delta,
    anchor_and_match,
    offset_stats,
    sliding_correlation,
    envelope_agreement,
)


def noisy_envelope(fs=50.0, dur=30.0, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * fs)) / fs
    x = np.zeros_like(t)
    for a in (1.0, 0.7, 0.4):
        f = rng.uniform(0.2, 2.0)
        x += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    return x + 0.05 * rng.standard_normal(len(t))


class TestXcorrLag:
    def test_recovers_300ms_shift(self):
        fs = 50.0
        x = noisy_envelope(fs)
        shift = int(0.3 * fs)
        y = np.roll(x, shift)  # y happens 0.3 s after x
        lag, r = xcorr_lag(x[shift:-shift], y[shift:-shift], fs, max_lag=1.5)
        assert lag == pytest.approx(0.3, abs=1.5 / fs)
        assert r > 0.9

    def test_negative_lag(self):
        fs = 50.0
        x = noisy_envelope(fs, seed=2)
        shift = int(0.4 * fs)
        y = np.roll(x, -shift)  # y precedes x
        lag, _ = xcorr_lag(x[shift:-shift], y[shift:-shift], fs, max_lag=1.5)
        assert lag == pytest.approx(-0.4, abs=1.5 / fs)

    def test_periodic_prefers_smallest_lag(self):
        # A pure sinusoid has equally good peaks at lag +/- one period;
        # the smallest-|lag| candidate (0) must win.
        fs = 100.0
        t = np.arange(int(20 * fs)) / fs
        x = np.sin(2 * np.pi * 1.0 * t)
        lag, r = xcorr_lag(x, x, fs, max_lag=1.5)
        assert lag == 0.0
        assert r > 0.99

    def test_envelope_lag_wrapper_agrees(self):
        # Ground truth: y is built by rolling x by exactly 0.25 s, so the
        # wrapper must recover that known lag (not merely equal whatever
        # xcorr_lag happens to return).
        fs = 50.0
        x = noisy_envelope(fs, seed=3)
        shift = int(0.25 * fs)
        y = np.roll(x, shift)
        lag, r = envelope_lag(x[shift:-shift], y[shift:-shift], fs)
        assert lag == pytest.approx(0.25, abs=1.5 / fs)
        assert r > 0.9


class TestPerCycleMotionDelta:
    def test_nearest_to_start_and_dedup(self):
        starts = np.array([0.0, 2.0, 4.0, 5.0])
        # one anticipating onset, one late return-stroke peak in cycle 0,
        # one onset shared between cycle 2's window and cycle 3's lookback
        motion = np.array([-0.1, 1.5, 2.05, 4.9])
        out = per_cycle_motion_delta(starts, motion, lookback=0.3)
        assert out[0] == pytest.approx(-0.1)
        assert out[1] == pytest.approx(0.05)
        # 4.9 is in both cycle 2's window [3.7, 5.0) and cycle 3's [4.7, inf);
        # descending order lets cycle 3 claim it first, leaving cycle 2 empty.
        assert np.isnan(out[2])
        assert out[3] == pytest.approx(-0.1)

    def test_no_motion(self):
        out = per_cycle_motion_delta([0.0, 1.0], [])
        assert np.all(np.isnan(out))


class TestAnchorAndMatch:
    def test_recovers_known_offsets(self):
        # Stream b = stream a + per-event offsets, on a shifted clock.
        a = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        true_off = np.array([0.0, 0.05, -0.04, 0.02, 0.10])
        b = a + true_off + 7.3            # independent clock
        wa = np.array([1, 5, 1, 1, 1])    # anchor: a[1] / b[1]
        wb = wa.copy()
        off = anchor_and_match(a, b, weights_a=wa, weights_b=wb, window=0.15)
        # relative to the anchor pair (offset 0.05), excluded by construction
        expected = np.array([0.0, -0.04, 0.02, 0.10]) - 0.05
        assert np.allclose(np.sort(off), np.sort(expected), atol=1e-9)

    def test_window_excludes_far_events(self):
        a = np.array([0.0, 1.0, 2.0])
        b = np.array([0.0, 1.5])          # the 1.0 event has no match within 0.15
        off = anchor_and_match(a, b, anchor_a=0.0, anchor_b=0.0, window=0.15)
        assert len(off) == 0

    def test_requires_anchor_or_weights(self):
        with pytest.raises(ValueError):
            anchor_and_match([0.0, 1.0], [0.0, 1.0])

    def test_a_event_does_not_match_b_anchor(self):
        # a has a non-anchor event within `window` of t = 0 (b's anchor,
        # also at t = 0 after shifting); with no other b event nearby, this
        # must NOT match -- b's anchor has to be excluded from the match
        # pool symmetrically with a's, or this would spuriously match with
        # a near-zero offset.
        a = np.array([0.0, 0.05])         # anchor at 0.0, other event near it
        b = np.array([0.0, 5.0])          # anchor at 0.0, no other nearby event
        off = anchor_and_match(a, b, anchor_a=0.0, anchor_b=0.0, window=0.15)
        assert len(off) == 0

    def test_matching_is_one_to_one(self):
        # Two a events both fall within `window` of the same single b
        # event: only the nearer one may claim it, yielding exactly one
        # match (not two, as many-to-one matching would give).
        a = np.array([0.0, 1.0, 1.08])
        b = np.array([0.0, 1.02])
        off = anchor_and_match(a, b, anchor_a=0.0, anchor_b=0.0, window=0.15)
        assert len(off) == 1
        assert off[0] == pytest.approx(0.02)   # 1.02 - 1.0, the nearer pair

    def test_offset_stats(self):
        off = np.array([-0.02, 0.0, 0.02, 0.04])
        st = offset_stats(off)
        assert st["n"] == 4
        assert st["median"] == pytest.approx(0.01)
        assert st["mean"] == pytest.approx(0.01)
        assert st["min"] == pytest.approx(-0.02)
        assert st["max"] == pytest.approx(0.04)
        assert offset_stats([])["n"] == 0
        assert np.isnan(offset_stats([])["median"])


class TestSlidingCorrelation:
    def test_profiles_coupling_change(self):
        # First half: y coupled to x; second half: y independent.
        fs = 25.0
        dur = 60.0
        rng = np.random.default_rng(4)
        x = noisy_envelope(fs, dur, seed=5)
        y = x.copy()
        half = len(x) // 2
        y[half:] = noisy_envelope(fs, dur, seed=6)[half:]
        times, r = sliding_correlation(x, y, fs, window=10.0, step=2.0)
        first = r[times < dur / 2 - 5]
        second = r[times > dur / 2 + 5]
        assert np.nanmedian(first) > 0.95
        assert np.nanmedian(second) < 0.5

    def test_constant_window_is_nan(self):
        fs = 10.0
        x = np.ones(int(30 * fs))
        y = noisy_envelope(fs, 30.0)
        _, r = sliding_correlation(x, y, fs, window=5.0, step=5.0)
        assert np.all(np.isnan(r))


class TestEnvelopeAgreement:
    def test_agreeing_sources(self):
        fs = 25.0
        base = noisy_envelope(fs, seed=7)
        rng = np.random.default_rng(8)
        views = [base + 0.1 * rng.standard_normal(len(base)) for _ in range(3)]
        C, mean_r = envelope_agreement(views, fs)
        assert C.shape == (3, 3)
        assert np.allclose(np.diag(C), 1.0)
        assert mean_r > 0.9

    def test_disagreeing_source(self):
        fs = 25.0
        a = noisy_envelope(fs, seed=9)
        b = noisy_envelope(fs, seed=10)
        C, mean_r = envelope_agreement([a, b], fs)
        assert abs(mean_r) < 0.5

    def test_unequal_lengths_truncated(self):
        fs = 25.0
        a = noisy_envelope(fs, dur=30.0, seed=11)
        C, _ = envelope_agreement([a, a[: len(a) - 40]], fs)
        assert C.shape == (2, 2)

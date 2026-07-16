"""Tests for musicalgestures._pulse (cycle segmentation, accelerando, motion onsets).

All ground truth is synthetic (see tests/_synth.py, adapted from the ro study).
"""
import numpy as np
import pytest

from musicalgestures import (
    Cycle,
    group_strokes,
    segment_cycles,
    cycle_table,
    fit_accelerando,
    motion_onsets,
)
from _synth import ro_times


class TestGroupStrokes:
    def test_basic_double_strokes(self):
        gt = ro_times(n_cycles=15)
        groups = group_strokes(gt["strokes"])
        assert len(groups) == 15
        assert all(len(g) == 2 for g in groups)
        assert np.allclose([g[0] for g in groups], gt["starts"])

    def test_deep_accelerando_25_cycles(self):
        # Deep-accelerando case: 25 cycles with a shrinking stroke gap; the
        # final cycle gaps approach the stroke gap. At least 95% of the
        # groups must be recovered as double strokes at the right starts.
        gt = ro_times(ioi0=2.0, t_double=10.0, n_cycles=25,
                      stroke_gap=0.25, gap_shrink=0.4)
        groups = group_strokes(gt["strokes"])
        doubles = [g for g in groups if len(g) == 2]
        assert len(groups) == 25
        assert len(doubles) / len(groups) >= 0.95
        recovered = sorted(g[0] for g in groups)
        assert np.allclose(recovered, gt["starts"], atol=1e-9)

    def test_empty_and_single(self):
        assert group_strokes([]) == []
        assert group_strokes([3.0]) == [[3.0]]

    def test_unsorted_input(self):
        gt = ro_times(n_cycles=8)
        shuffled = np.asarray(gt["strokes"])[::-1]
        groups = group_strokes(shuffled)
        assert len(groups) == 8


class TestSegmentCycles:
    def test_assigns_first_event_in_cycle(self):
        gt = ro_times(n_cycles=10)
        cycles = segment_cycles(gt["strokes"], gt["shouts"])
        assert len(cycles) == 10
        assert all(isinstance(c, Cycle) for c in cycles)
        got = [c.event for c in cycles]
        assert np.allclose(got, gt["shouts"])

    def test_no_events(self):
        gt = ro_times(n_cycles=5)
        cycles = segment_cycles(gt["strokes"])
        assert all(c.event is None for c in cycles)

    def test_cycle_properties(self):
        c = Cycle(0, [1.0, 1.25], 1.8)
        assert c.t_start == 1.0
        assert c.n_strokes == 2
        assert c.stroke_gap == pytest.approx(0.25)
        assert np.isnan(Cycle(0, [1.0]).stroke_gap)


class TestCycleTable:
    def test_columns_and_values(self):
        gt = ro_times(n_cycles=6)
        df = cycle_table(segment_cycles(gt["strokes"], gt["shouts"]),
                         clip_id="clip1", context="test")
        assert list(df.columns) == ['clip', 'context', 'cycle', 't', 'ioi',
                                    'n_strokes', 'stroke_gap', 'event',
                                    'stroke_event_ioi']
        assert len(df) == 6
        assert np.allclose(df.t.to_numpy(), gt["starts"])
        assert np.allclose(df.ioi.to_numpy()[:-1], np.diff(gt["starts"]))
        assert np.isnan(df.ioi.to_numpy()[-1])
        assert (df.n_strokes == 2).all()

    def test_empty(self):
        df = cycle_table([])
        assert len(df) == 0
        assert 'ioi' in df.columns


class TestFitAccelerando:
    def test_recovers_known_parameters(self):
        gt = ro_times(ioi0=2.0, t_double=12.0, n_cycles=20)
        t = np.asarray(gt["starts"])
        ioi = np.append(np.diff(t), np.nan)
        ioi0, t_double, r2 = fit_accelerando(t, ioi)
        # ro_times references its exponential to t=1.0 s, so the fitted
        # ioi0 (at t=0) is ioi0 * 2**(1/t_double).
        assert t_double == pytest.approx(12.0, rel=0.05)
        assert ioi0 == pytest.approx(2.0 * 2 ** (1 / 12.0), rel=0.05)
        assert r2 > 0.99

    def test_steady_pulse_gives_inf(self):
        t = np.arange(10, dtype=float)
        ioi = np.ones(10)
        _, t_double, _ = fit_accelerando(t, ioi)
        assert np.isinf(t_double)


class TestMotionOnsets:
    def test_recovers_ramp_onsets(self):
        fs = 50.0
        rng = np.random.default_rng(0)
        t = np.arange(int(20 * fs)) / fs
        truth = np.array([3.0, 8.0, 13.0, 17.0])
        sig = 0.005 * rng.standard_normal(len(t))
        for on in truth:
            sig += 1.0 / (1.0 + np.exp(-(t - on) / 0.1)) * np.exp(-(t - on).clip(0) / 1.5)
        onsets = motion_onsets(sig, fs)
        matched = [np.min(np.abs(onsets - x)) for x in truth]
        assert len(onsets) == len(truth)
        assert max(matched) < 0.25

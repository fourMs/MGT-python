"""Tests for musicalgestures._peaks (canonical adaptive peak-picker)."""
import numpy as np

from musicalgestures import pick_peaks


def bumpy_signal(fs=100.0, peak_times=(1.0, 2.0, 3.5), amps=(1.0, 0.6, 0.9),
                 dur=5.0, width=0.05):
    t = np.arange(int(dur * fs)) / fs
    x = np.zeros_like(t)
    for pt, a in zip(peak_times, amps):
        x += a * np.exp(-0.5 * ((t - pt) / width) ** 2)
    return t, x


class TestPickPeaks:
    def test_recovers_known_peaks(self):
        fs = 100.0
        t, x = bumpy_signal(fs)
        idx = pick_peaks(x, fs=fs, rel_threshold=0.3, min_interval=0.3,
                         rel_prominence=0.2)
        assert len(idx) == 3
        assert np.allclose(idx / fs, [1.0, 2.0, 3.5], atol=0.05)

    def test_relative_threshold_gates_small_peaks(self):
        fs = 100.0
        t, x = bumpy_signal(fs, amps=(1.0, 0.2, 0.9))
        idx = pick_peaks(x, fs=fs, rel_threshold=0.5, min_interval=0.1,
                         rel_prominence=None)
        assert np.allclose(idx / fs, [1.0, 3.5], atol=0.05)

    def test_min_interval_keeps_stronger_peak(self):
        fs = 100.0
        t, x = bumpy_signal(fs, peak_times=(1.0, 1.15), amps=(1.0, 0.8))
        idx = pick_peaks(x, fs=fs, rel_threshold=0.3, min_interval=0.5,
                         rel_prominence=None, smooth=None)
        assert len(idx) == 1
        assert abs(idx[0] / fs - 1.0) < 0.05

    def test_prominence_gate_rejects_shoulder(self):
        fs = 100.0
        t = np.arange(int(5 * fs)) / fs
        # A big slow hump with a tiny ripple riding on it: the ripple's peak
        # is high in absolute terms but has almost no prominence.
        x = np.exp(-0.5 * ((t - 2.5) / 1.0) ** 2)
        x += 0.05 * np.exp(-0.5 * ((t - 3.5) / 0.02) ** 2)
        idx_gated = pick_peaks(x, fs=fs, smooth=None, rel_threshold=0.3,
                               min_interval=0.2, rel_prominence=0.2)
        idx_open = pick_peaks(x, fs=fs, smooth=None, rel_threshold=0.3,
                              min_interval=0.2, rel_prominence=None)
        assert len(idx_gated) == 1
        assert len(idx_open) == 2

    def test_absolute_overrides(self):
        fs = 100.0
        t, x = bumpy_signal(fs, amps=(1.0, 0.6, 0.9))
        idx = pick_peaks(x, fs=fs, rel_threshold=None, threshold=0.7,
                         min_interval=0.1, rel_prominence=None)
        assert np.allclose(idx / fs, [1.0, 3.5], atol=0.05)

    def test_empty_and_short_input(self):
        assert len(pick_peaks(np.array([]))) == 0
        assert len(pick_peaks(np.array([1.0, 2.0]))) == 0

    def test_returns_integer_indices(self):
        fs = 100.0
        t, x = bumpy_signal(fs)
        idx = pick_peaks(x, fs=fs)
        assert idx.dtype.kind == "i"

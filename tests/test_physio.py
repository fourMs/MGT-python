"""Tests for musicalgestures._physio (respiration + spectral band fractions).

Synthetic ground truth: a 0.25 Hz breathing sinusoid must give a respiration
rate of ~15 breaths/min; a two-tone signal must split its Welch power between
two named bands in the expected proportion.
"""
import numpy as np
import pytest

from musicalgestures import respiration_rate, spectral_band_fractions


class TestRespirationRate:
    def test_quarter_hz_breathing_is_15_bpm(self):
        fs = 25.0
        dur = 120.0
        t = np.arange(0, dur, 1 / fs)
        wave = np.sin(2 * np.pi * 0.25 * t)  # 0.25 Hz -> 15 br/min
        out = respiration_rate(wave, fs, band=(0.1, 0.6),
                               window_s=30, step_s=30)
        assert out["median_bpm"] == pytest.approx(15.0, abs=1.0)
        assert np.isfinite(out["rate_bpm"]).all()

    def test_windows_and_times(self):
        fs = 20.0
        dur = 120.0
        t = np.arange(0, dur, 1 / fs)
        wave = np.sin(2 * np.pi * 0.2 * t)  # 12 br/min
        out = respiration_rate(wave, fs, window_s=30, step_s=30)
        assert len(out["rate_bpm"]) == len(out["times_s"])
        assert out["median_bpm"] == pytest.approx(12.0, abs=1.0)

    def test_added_noise_still_recovers_rate(self):
        rng = np.random.default_rng(0)
        fs = 25.0
        t = np.arange(0, 120, 1 / fs)
        wave = np.sin(2 * np.pi * 0.25 * t) + 0.3 * rng.standard_normal(len(t))
        out = respiration_rate(wave, fs)
        assert out["median_bpm"] == pytest.approx(15.0, abs=1.5)


class TestSpectralBandFractions:
    def test_two_tone_split(self):
        # Equal-amplitude tones at 0.3 Hz and 1.2 Hz; each named band should
        # capture close to half the in-band power.
        fs = 50.0
        t = np.arange(0, 200, 1 / fs)
        x = np.sin(2 * np.pi * 0.3 * t) + np.sin(2 * np.pi * 1.2 * t)
        bands = {"low": (0.2, 0.5), "high": (1.0, 1.5)}
        frac = spectral_band_fractions(x, fs, bands, total_band=(0.1, 4.0))
        assert frac["low"] == pytest.approx(0.5, abs=0.1)
        assert frac["high"] == pytest.approx(0.5, abs=0.1)
        assert frac["low"] + frac["high"] == pytest.approx(1.0, abs=0.1)

    def test_dominant_band_gets_most_power(self):
        fs = 50.0
        t = np.arange(0, 200, 1 / fs)
        # a strong 1.2 Hz tone and a weak 0.3 Hz tone
        x = 0.2 * np.sin(2 * np.pi * 0.3 * t) + np.sin(2 * np.pi * 1.2 * t)
        bands = {"low": (0.2, 0.5), "high": (1.0, 1.5)}
        frac = spectral_band_fractions(x, fs, bands)
        assert frac["high"] > frac["low"]

    def test_empty_signal(self):
        frac = spectral_band_fractions(np.array([]), 50.0, {"a": (0.1, 0.5)})
        assert np.isnan(frac["a"])

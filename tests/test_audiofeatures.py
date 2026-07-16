"""Tests for musicalgestures._audiofeatures (onsets, T60, attack centroid).

All ground truth is synthetic (see tests/_synth.py): click trains with known
onset times and tones with an exact exponential decay.
"""
import numpy as np
import pytest

from musicalgestures import (
    rms_envelope,
    spectral_flux,
    spectral_flux_onsets,
    energy_onsets,
    t60_backward_decay,
    attack_spectral_centroid,
)
from _synth import SR, click_train, decaying_tone


class TestRmsEnvelope:
    def test_tracks_amplitude(self):
        sr = SR
        t = np.arange(sr) / sr
        y = np.sin(2 * np.pi * 440 * t)
        y[: sr // 2] *= 0.1
        env, rate = rms_envelope(y, sr, window=0.02)
        assert rate == pytest.approx(50.0)
        assert env[len(env) // 4] == pytest.approx(0.1 / np.sqrt(2), rel=0.05)
        assert env[3 * len(env) // 4] == pytest.approx(1 / np.sqrt(2), rel=0.05)


class TestSpectralFluxOnsets:
    def test_click_train(self):
        truth = np.array([0.5, 1.0, 1.6, 2.3, 3.1])
        y = click_train(truth)
        onsets = spectral_flux_onsets(y, SR)
        assert len(onsets) == len(truth)
        # STFT frame resolution: hop = 512 samples ~ 23 ms
        assert np.max(np.abs(np.sort(onsets) - truth)) < 0.05

    def test_flux_normalized(self):
        y = click_train([0.2, 0.6])
        flux, times = spectral_flux(y, SR)
        assert flux.max() == pytest.approx(1.0)
        assert len(flux) == len(times)

    def test_silence_has_no_onsets(self):
        y = np.zeros(SR)
        assert len(spectral_flux_onsets(y, SR)) == 0


class TestEnergyOnsets:
    def test_click_train(self):
        truth = np.array([0.4, 1.1, 1.9, 2.4])
        y = click_train(truth)
        onsets = energy_onsets(y, SR)
        assert len(onsets) == len(truth)
        assert np.max(np.abs(np.sort(onsets) - truth)) < 0.05

    def test_min_interval_merges_flams(self):
        y = click_train([1.0, 1.03, 2.0])
        onsets = energy_onsets(y, SR, min_interval=0.06)
        assert len(onsets) == 2


class TestT60:
    @pytest.mark.parametrize("true_t60", [0.8, 2.0, 6.0])
    def test_recovers_known_decay(self, true_t60):
        y = decaying_tone(true_t60, dur=0.1 + 0.7 * true_t60)
        t60, span = t60_backward_decay(y, SR)
        assert span == (-5, -35)
        assert t60 == pytest.approx(true_t60, rel=0.1)

    def test_t20_fallback_on_short_decay(self):
        # Truncate before the -35 dB level is reached
        true_t60 = 4.0
        y = decaying_tone(true_t60, dur=0.05 + true_t60 * 30 / 60 * 0.9)
        t60, span = t60_backward_decay(y, SR)
        assert span == (-5, -25)
        assert t60 == pytest.approx(true_t60, rel=0.15)

    def test_no_decay_gives_nan(self):
        y = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)  # steady tone
        t60, span = t60_backward_decay(y, SR)
        assert np.isnan(t60) and span is None


class TestAttackSpectralCentroid:
    def test_orders_bright_vs_dark(self):
        sr = SR
        t = np.arange(int(0.5 * sr)) / sr
        env = np.exp(-t * 8)
        dark = np.sin(2 * np.pi * 300 * t) * env
        bright = np.sin(2 * np.pi * 3000 * t) * env
        c_dark = attack_spectral_centroid(dark, sr)
        c_bright = attack_spectral_centroid(bright, sr)
        assert c_dark == pytest.approx(300, rel=0.2)
        assert c_bright == pytest.approx(3000, rel=0.2)
        assert c_bright > c_dark

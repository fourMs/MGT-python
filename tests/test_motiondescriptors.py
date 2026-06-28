"""Tests for the motion-descriptors module (issue #210).

Covers the scalar movement descriptors derived from the quantity-of-motion signal — motion
energy, SPARC smoothness, Shannon entropy, and the Hann-windowed spectral descriptors — both as
pure functions (fast, with known-answer signals) and end-to-end on a short clip.
"""
from __future__ import annotations

import os

import numpy as np
import pytest

import musicalgestures
from musicalgestures import _motiondescriptors as md


# ---------------------------------------------------------------------------
# Pure-function unit tests (fast, deterministic)
# ---------------------------------------------------------------------------

def test_entropy_bounds_and_extremes():
    # A flat signal puts all mass in one bin -> zero entropy.
    assert md._motion_entropy(np.ones(100)) == 0.0
    # A broad uniform spread approaches the maximum (normalised ~1).
    spread = md._motion_entropy(np.linspace(0, 1, 100000), bins=50)
    assert 0.9 <= spread <= 1.0
    # An all-zero / empty signal is defined as zero.
    assert md._motion_entropy(np.zeros(10)) == 0.0
    assert md._motion_entropy(np.array([])) == 0.0


def test_sparc_smoother_is_less_negative():
    fs = 50.0
    t = np.arange(0, 4, 1 / fs)
    smooth = np.exp(-((t - 2) ** 2) / (2 * 0.3 ** 2))          # single clean bell -> smooth
    jerky = smooth + 0.3 * np.sin(2 * np.pi * 8 * t) ** 2       # high-freq wiggle -> jerky
    s_smooth = md._sparc(smooth, fs)
    s_jerky = md._sparc(jerky, fs)
    assert s_smooth < 0 and s_jerky < 0          # SPARC is negative
    assert s_smooth > s_jerky                     # smoother == less negative
    assert np.isnan(md._sparc(np.zeros(100), fs))  # silent signal -> NaN


def test_spectrum_recovers_known_frequency():
    fs = 50.0
    t = np.arange(0, 8, 1 / fs)
    sig = np.sin(2 * np.pi * 3.0 * t) + 1.0  # 3 Hz tone on a DC offset
    freqs, power = md._qom_spectrum(sig, fs, window='hann')
    assert freqs.shape == power.shape
    dominant = freqs[1 + int(np.argmax(power[1:]))]
    assert abs(dominant - 3.0) < 0.2
    # Hann vs rectangular windows produce different spectra.
    _, power_rect = md._qom_spectrum(sig, fs, window='none')
    assert not np.allclose(power, power_rect)


# ---------------------------------------------------------------------------
# Integration test on a real short clip
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def short_clip(tmp_path_factory):
    target = str(tmp_path_factory.mktemp("motiondesc")).replace("\\", "/") + "/clip.avi"
    return musicalgestures._utils.extract_subclip(musicalgestures.examples.dance, 5, 8, target_name=target)


def test_motiondescriptors_end_to_end(short_clip, tmp_path):
    png = str(tmp_path).replace("\\", "/") + "/desc.png"
    mg = musicalgestures.MgVideo(short_clip)
    res = mg.motiondescriptors(target_name=png)

    assert res is not None
    assert os.path.isfile(png)
    assert os.path.isfile(short_clip[:-4] + "_motiondescriptors.csv")
    assert mg.motiondescriptors_figure is res

    d = res.data
    for key in ("motion_energy", "motion_smoothness", "motion_entropy",
                "dominant_freq", "spectral_centroid"):
        assert key in d and isinstance(d[key], float)
    assert d["motion_energy"] >= 0
    assert 0.0 <= d["motion_entropy"] <= 1.0
    assert d["motion_smoothness"] <= 0  # SPARC is non-positive
    assert d["dominant_freq"] >= 0
    assert d["frequencies"].shape == d["power"].shape

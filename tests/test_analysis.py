"""Tests for musicalgestures._analysis, which had none until 1.11.3.

Six public functions are exported from this module at package top level and no
test file referenced it. Two of them are shared with `micromotion` and had
drifted: `bandpass` differed in argument order and in what it did with an
unusable band, and `dominant_frequency` uses a different band on purpose. The
tests here pin both the delegation and the deliberate difference, so neither
can move without a failure.

Ground truth is synthetic throughout: sinusoids at known frequencies and a
known imposed lag.
"""
import numpy as np
import pytest

from musicalgestures._analysis import bandpass, dominant_frequency, smooth

FS = 100.0


def _signal(freqs_amps, n=2000, fs=FS, seed=0):
    t = np.arange(n) / fs
    x = np.zeros(n)
    for f, a in freqs_amps:
        x += a * np.sin(2 * np.pi * f * t)
    return x + 0.05 * np.random.default_rng(seed).standard_normal(n)


def test_bandpass_delegates_to_micromotion_exactly():
    """One filter, one implementation: the two packages must not merely agree closely."""
    mm = pytest.importorskip("micromotion")
    x = _signal([(1.0, 1.0), (20.0, 1.0)])
    assert np.array_equal(bandpass(x, 0.5, 5.0, FS), mm.bandpass(x, FS, 0.5, 5.0))


def test_bandpass_actually_removes_out_of_band_energy():
    """A delegation test alone would pass even if the owner filtered nothing."""
    x = _signal([(1.0, 1.0), (20.0, 1.0)])
    y = bandpass(x, 0.5, 5.0, FS)
    f = np.fft.rfftfreq(len(y), 1 / FS)
    p = np.abs(np.fft.rfft(y))
    assert p[np.argmin(np.abs(f - 20.0))] < 0.02 * p[np.argmin(np.abs(f - 1.0))]


def test_bandpass_raises_on_an_unusable_band():
    """It returned the signal UNFILTERED until 1.11.3, which is a silent wrong answer.

    Handing back unfiltered data that the caller believes is band-limited is worse
    than a traceback: everything computed downstream is of the wrong band and
    nothing says so.
    """
    with pytest.raises(ValueError):
        bandpass(_signal([(1.0, 1.0)]), 60.0, 80.0, FS)


def test_dominant_frequency_finds_a_known_peak():
    assert dominant_frequency(_signal([(2.0, 1.0)]), FS) == pytest.approx(2.0, abs=0.1)


def test_dominant_frequency_differs_from_micromotions_on_purpose():
    """Same name, different band, different question. Pinned so it cannot drift silently.

    This one covers 0.5-8.0 Hz for locomotion and dance; micromotion's covers
    0.3-4.0 Hz for postural micromotion. A signal whose strongest component sits
    between the two ceilings separates them completely.
    """
    mm = pytest.importorskip("micromotion")
    x = _signal([(0.8, 0.3), (6.0, 1.0)])
    assert dominant_frequency(x, FS) == pytest.approx(6.0, abs=0.1)
    assert mm.dominant_frequency(x, FS) == pytest.approx(0.8, abs=0.1)


def test_xcorr_lag_agrees_with_micromotion_in_value_and_sign():
    """The sign disagreed until micromotion 1.13.0; this is the guard against a repeat."""
    mm = pytest.importorskip("micromotion")
    from musicalgestures._alignment import xcorr_lag

    x = _signal([(1.0, 1.0), (2.7, 0.5)], n=3000)
    lag = 25
    a, b = x[lag:], x[: len(x) - lag]        # b carries every feature `lag` samples later
    ours, r = xcorr_lag(a, b, FS)
    assert ours == pytest.approx(lag / FS, abs=0.02)
    assert r > 0.9
    theirs = mm.xcorr_lag(a, b, fs=FS, max_lag_s=1.5, difference=False)["lag_s"]
    assert ours == pytest.approx(theirs, abs=1e-9)


def test_smooth_preserves_length_and_reduces_variance():
    x = _signal([(1.0, 1.0)])
    y = smooth(x, w=9)
    assert len(y) == len(x)
    assert y.std() < x.std()

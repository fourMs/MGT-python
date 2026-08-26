"""Correlation across a lag range, and why this project needed it.

Every speech-versus-motion number this toolbox has produced on the dance corpus was
computed at zero lag: the two series binned per minute and correlated where they sat.
That assumes the relationship, if there is one, is simultaneous --- which is a strange
assumption for a question about when an action begins RELATIVE TO the sound it makes.
A real association displaced by a second or two is invisible to a zero-lag correlation.

The lag convention is the thing to get right, and it is the thing a reader will get
wrong, so it is stated once here and tested: **a positive lag means `y` follows `x`**.
If the motion happens two seconds after the sound, the peak is at +2.0.

Ported from `xcov()` in https://github.com/finn42/Laughter_Dance (Finn Upham), which
accompanies Upham et al., Frontiers in Psychology 2026, doi:10.3389/fpsyg.2026.1754425.
Two things are added: the sign convention above, and a correction for the fact that
scanning many lags and reporting the best one is a multiple comparison.
"""
import numpy as np
import pytest

from musicalgestures._correlate import lagged_correlation


def test_identical_series_peak_at_zero_lag():
    rng = np.random.default_rng(0)
    x = rng.normal(size=500)
    r = lagged_correlation(x, x, fs=10.0, max_lag_s=5.0)
    assert r.best_lag_s == pytest.approx(0.0)
    assert r.best_r == pytest.approx(1.0)


def test_a_delayed_copy_peaks_at_the_delay():
    """y follows x by 2 s, so the peak belongs at +2.0 and nowhere else."""
    rng = np.random.default_rng(1)
    x = rng.normal(size=1000)
    delay_samples = 20                      # 2.0 s at 10 Hz
    y = np.roll(x, delay_samples)
    r = lagged_correlation(x, y, fs=10.0, max_lag_s=5.0)
    assert r.best_lag_s == pytest.approx(2.0)


def test_an_advanced_copy_peaks_at_a_negative_lag():
    """The other direction, because a sign convention is only proved by both."""
    rng = np.random.default_rng(2)
    x = rng.normal(size=1000)
    y = np.roll(x, -15)                     # y leads x by 1.5 s
    r = lagged_correlation(x, y, fs=10.0, max_lag_s=5.0)
    assert r.best_lag_s == pytest.approx(-1.5)


def test_the_lag_grid_covers_the_requested_range_and_no_more():
    x = np.arange(200, dtype=float)
    r = lagged_correlation(x, x, fs=4.0, max_lag_s=2.0)
    assert r.lags_s[0] == pytest.approx(-2.0)
    assert r.lags_s[-1] == pytest.approx(2.0)


def test_scanning_many_lags_is_corrected_as_a_multiple_comparison():
    """The reason a naive port of xcov would mislead.

    Take the best of many lags and the null distribution is no longer that of a single
    correlation: with enough independent lags, some pair of unrelated series will always
    show a healthy-looking r. The corrected p must therefore be strictly weaker than the
    uncorrected one whenever more than one lag was examined.
    """
    rng = np.random.default_rng(3)
    x = rng.normal(size=300)
    y = rng.normal(size=300)
    r = lagged_correlation(x, y, fs=10.0, max_lag_s=5.0)
    assert r.n_lags > 1
    assert r.p_corrected > r.p_uncorrected


def test_unrelated_noise_is_not_significant_after_correction():
    rng = np.random.default_rng(4)
    x = rng.normal(size=2000)
    y = rng.normal(size=2000)
    r = lagged_correlation(x, y, fs=10.0, max_lag_s=5.0)
    assert r.p_corrected > 0.05


def test_series_of_different_lengths_is_an_error_not_a_guess():
    with pytest.raises(ValueError):
        lagged_correlation(np.zeros(10), np.zeros(11), fs=1.0, max_lag_s=1.0)


def test_a_constant_series_has_no_correlation_to_report():
    """Zero variance makes r undefined. NaN is the honest answer, not 0.0."""
    rng = np.random.default_rng(5)
    r = lagged_correlation(np.ones(100), rng.normal(size=100), fs=10.0, max_lag_s=2.0)
    assert np.isnan(r.best_r)


def _ar1(n, rho, rng):
    """An autocorrelated series: each sample mostly the previous one."""
    v = np.zeros(n)
    for i in range(1, n):
        v[i] = rho * v[i - 1] + rng.normal()
    return v


def test_two_unrelated_but_autocorrelated_series_are_not_significant():
    """The correction that Bonferroni alone does not provide.

    One-second bins of a motion envelope are nothing like independent samples: each is
    mostly the previous one. Treating n bins as n observations inflates every t and
    turns noise into a finding. On this project's corpus the difference was not academic
    --- one session's best lag moved from p < 0.001 to p = 1.0 once the effective sample
    size was used, which is the difference between a result and an artefact.
    """
    rng = np.random.default_rng(11)
    x = _ar1(4000, 0.9, rng)
    y = _ar1(4000, 0.9, rng)          # independent of x by construction
    r = lagged_correlation(x, y, fs=1.0, max_lag_s=30.0)
    assert r.n_effective < r.n_overlap / 2
    assert r.p_corrected > 0.05


def test_effective_size_equals_length_when_samples_are_independent():
    """White noise carries its full information, so nothing should be discounted."""
    rng = np.random.default_rng(12)
    x = rng.normal(size=2000)
    y = rng.normal(size=2000)
    r = lagged_correlation(x, y, fs=1.0, max_lag_s=5.0)
    assert r.n_effective == pytest.approx(r.n_overlap, rel=0.15)

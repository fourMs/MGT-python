"""Co-accentuation: do motion accents land on sound accents?

The measure comes from Serdar and Jensenius, *Mixed Method Audio-Video Analyses of Felt
Togetherness in a Networked Music-Dance Performance*, MOCO '26: each motion peak is tested
for an audio onset within a tolerance, and the fraction that coincide is the Global
Co-Accentuation Index. A time-resolved curve over short windows shows whether synchrony
came in bursts or was sustained.

**Why a chance baseline is not optional here.** The index is a raw fraction, and raw
fractions of coincidence rise with density: sprinkle enough onsets over a recording and
every motion peak has one within 150 ms whether or not anything is coordinated. An index of
0.8 means nothing until you know what 0.8 would have been by accident. The null is a
circular shift of the onsets, which keeps their number and their rhythm and destroys only
their relationship to the motion.

**The measure is asymmetric and that is deliberate.** It asks what fraction of MOTION peaks
found a sound, not the reverse. A dancer moving twice to one sound scores differently from
a musician playing twice to one movement, and collapsing the two would hide which was
happening.
"""
import numpy as np
import pytest

from musicalgestures._coaccentuation import co_accentuation, co_accentuation_curve


def test_every_peak_on_an_onset_scores_one():
    peaks = np.array([1.0, 2.0, 3.0])
    r = co_accentuation(peaks, peaks, duration_s=10.0)
    assert r.gci == pytest.approx(1.0)
    assert r.n_matched == 3


def test_no_onset_anywhere_near_scores_zero():
    r = co_accentuation(np.array([1.0, 2.0]), np.array([50.0]), duration_s=100.0)
    assert r.gci == pytest.approx(0.0)


def test_an_onset_exactly_at_the_tolerance_counts():
    """The boundary, and it has to be reached exactly to be tested.

    Written first as peak 1.0 against onset 1.15, which looks like the boundary and is
    not: 1.15 - 1.0 is 0.1499999999999999 in binary floating point, comfortably inside
    the window. That version passed whether the comparison was `<=` or `<`, so it tested
    nothing. Anchoring the peak at zero makes the difference exact.
    """
    r = co_accentuation(np.array([0.0]), np.array([0.15]), tolerance_s=0.15,
                        duration_s=10.0)
    assert r.n_matched == 1


def test_an_onset_just_beyond_the_tolerance_does_not():
    r = co_accentuation(np.array([0.0]), np.array([0.25]), tolerance_s=0.15,
                        duration_s=10.0)
    assert r.n_matched == 0


def test_the_index_is_a_fraction_of_motion_peaks_not_of_onsets():
    """One movement answered by a hundred sounds is still one coincident movement."""
    r = co_accentuation(np.array([5.0]), np.linspace(4.9, 5.1, 100), duration_s=10.0)
    assert r.gci == pytest.approx(1.0)
    assert r.n_peaks == 1


def test_dense_random_onsets_are_not_reported_as_synchrony():
    """The failure this measure invites: coincidence bought with density.

    Onsets every 200 ms give every motion peak a partner within 150 ms, so the raw index
    is near 1. It is worth nothing, and the null must say so.
    """
    rng = np.random.default_rng(0)
    peaks = np.sort(rng.uniform(0, 300, 60))
    onsets = np.arange(0, 300, 0.2)
    r = co_accentuation(peaks, onsets, duration_s=300.0, n_null=200)
    assert r.gci > 0.9
    assert r.p > 0.05, "dense onsets should not look like coordination"


def test_real_coincidence_beats_its_null():
    rng = np.random.default_rng(1)
    peaks = np.sort(rng.uniform(0, 300, 40))
    onsets = peaks + rng.normal(0, 0.05, len(peaks))     # sound follows movement closely
    r = co_accentuation(peaks, onsets, duration_s=300.0, n_null=200)
    assert r.p < 0.05
    assert r.gci > r.expected_gci


def test_no_peaks_gives_no_index_rather_than_zero():
    """Zero would say "nothing was coordinated". The truth is that nothing was asked."""
    r = co_accentuation(np.array([]), np.array([1.0]), duration_s=10.0)
    assert np.isnan(r.gci)


def test_the_curve_steps_by_the_step_not_the_window():
    times, gci = co_accentuation_curve(np.array([1.0]), np.array([1.0]),
                                       duration_s=20.0, window_s=5.0, step_s=1.0)
    assert times[1] - times[0] == pytest.approx(1.0)
    assert times[0] == pytest.approx(0.0)
    assert times[-1] <= 15.0


def test_a_window_with_no_peaks_is_not_a_zero_in_the_curve():
    """A quiet stretch has no synchrony to report, which is not the same as none found."""
    times, gci = co_accentuation_curve(np.array([1.0, 2.0]), np.array([1.0, 2.0]),
                                       duration_s=30.0, window_s=5.0, step_s=5.0)
    assert gci[0] == pytest.approx(1.0)
    assert np.isnan(gci[2])

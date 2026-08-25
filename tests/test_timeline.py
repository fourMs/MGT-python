"""A decimated strip that does not say so invites a reader to measure timings off it.

Two properties, and both have burned somebody:

1. **min/max, never a mean.** An overview cannot show 475,680 columns. The whole
   purpose of the overview is to find the brief events worth zooming into, and a mean
   removes exactly those.
2. **the reduction factor is on the figure.** A strip drawn at 1 column per 240 frames
   looks like a strip drawn at 1 column per frame. Printing the factor is what stops a
   reader taking a timing off a picture that cannot support one.
"""
import numpy as np
import pytest

from musicalgestures._timeline import decimate_minmax


def test_a_one_sample_spike_survives():
    x = np.zeros(10000)
    x[4321] = 1.0
    mins, maxs, factor = decimate_minmax(x, 100)
    assert maxs.max() == 1.0, "the spike was averaged away"
    assert factor == 100


def test_a_one_sample_trough_survives():
    x = np.ones(10000)
    x[4321] = -1.0
    mins, maxs, factor = decimate_minmax(x, 100)
    assert mins.min() == -1.0


def test_the_spike_lands_in_the_right_column():
    x = np.zeros(10000)
    x[4321] = 1.0
    _, maxs, _ = decimate_minmax(x, 100)
    assert int(np.argmax(maxs)) == 43


def test_no_decimation_when_it_already_fits():
    x = np.arange(50.0)
    mins, maxs, factor = decimate_minmax(x, 100)
    assert factor == 1
    assert np.array_equal(mins, x) and np.array_equal(maxs, x)


def test_a_mean_would_fail_the_spike_test():
    """Guard on the guard, stated so the property cannot be quietly weakened."""
    x = np.zeros(10000)
    x[4321] = 1.0
    naive = x[: 100 * 100].reshape(100, 100).mean(axis=1)
    assert naive.max() < 0.05, "the fixture is wrong; a mean should lose this"


def test_the_tail_is_not_dropped():
    """10000 samples into 3 columns leaves a remainder that must still be drawn."""
    x = np.zeros(10000)
    x[-1] = 5.0
    mins, maxs, factor = decimate_minmax(x, 3)
    assert maxs[-1] == 5.0, "the last partial column was discarded"


def test_padding_does_not_invent_a_trough_at_the_end():
    """Zero-padding a positive signal would draw a dip that is not in the recording."""
    x = np.full(10000, 7.0)
    mins, maxs, factor = decimate_minmax(x, 3)
    assert mins.min() == 7.0, "the padding was drawn as data"


def test_an_empty_signal_is_not_an_error():
    mins, maxs, factor = decimate_minmax(np.zeros(0), 100)
    assert len(mins) == len(maxs) == 0 and factor == 1

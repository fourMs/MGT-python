"""segment_actions thresholds on the envelope's GLOBAL range, which does not survive
a session.

The threshold is a fraction of max minus min. Over 2 h 38 min a handful of outlier
spikes raise `max` so far that the threshold sits below almost everything, and a
setting tuned on a clip silently means something else on a recording. Same shape as
the two long-video faults already fixed: invisible on a clip, wrong on a session, and
it does not raise.
"""
import numpy as np

from musicalgestures._actions import segment_actions


def _session_like(n=6000, fs=50.0):
    """Ten clear bursts on a low floor, plus three brief outlier spikes."""
    rng = np.random.default_rng(0)
    e = rng.uniform(0.0, 0.05, n)
    for k in range(10):
        i = 300 + k * 500
        e[i:i + 100] = 1.0
    #: The spikes: a few frames, forty times the bursts. A camera flash, a person
    #: crossing close to the lens --- the recording is full of them.
    for i in (1234, 3456, 5678):
        e[i:i + 3] = 40.0
    return e, fs


def test_minmax_loses_the_bursts_to_three_spikes():
    """The fault, asserted rather than described."""
    e, fs = _session_like()
    found = segment_actions(e, fs, threshold=0.15, min_duration=0.5)
    assert len(found) < 10, (
        f"expected the spikes to hide the bursts, got {len(found)}; "
        "if this fails the fault is gone and this test should be reconsidered")


def test_robust_finds_all_ten_bursts():
    e, fs = _session_like()
    found = segment_actions(e, fs, threshold=0.15, min_duration=0.5,
                            range_mode="robust")
    assert len(found) == 10, [f"{a.start:.1f}-{a.end:.1f}" for a in found]


def test_minmax_remains_the_default():
    """Nothing already measured may change."""
    e, fs = _session_like()
    assert segment_actions(e, fs, threshold=0.15, min_duration=0.5) == \
           segment_actions(e, fs, threshold=0.15, min_duration=0.5,
                           range_mode="minmax")


def test_robust_and_minmax_agree_when_there_are_no_outliers():
    """Robustness must not move boundaries on well-behaved material."""
    fs = 50.0
    e = np.zeros(2000)
    for k in range(4):
        e[200 + k * 400: 300 + k * 400] = 1.0
    a = segment_actions(e, fs, threshold=0.15, min_duration=0.5)
    b = segment_actions(e, fs, threshold=0.15, min_duration=0.5, range_mode="robust")
    assert [(x.start, x.end) for x in a] == [(x.start, x.end) for x in b]


def test_an_unknown_range_mode_is_refused():
    e, fs = _session_like()
    try:
        segment_actions(e, fs, range_mode="whatever")
    except ValueError:
        return
    raise AssertionError("an unknown range_mode silently did something")

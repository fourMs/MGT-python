"""Laughter detection, split the way the speech detector is split.

`_voice` established the pattern and the reason: the model wrapper has no right answer and
cannot run in CI, so it is kept as thin as it can be, and everything with a right answer
lives in a function that is tested. The same division here.

What has a right answer is which AudioSet classes count as laughter and how a per-class
score becomes one number. That is where a silent error would live --- picking `Laughter`
alone silently discards giggling, chuckling and belly laughs, which on this project's
corpus are most of what the dancers actually do.

Span assembly is NOT reimplemented. `spans_from_probabilities` already turns a probability
track into spans, closing short gaps before dropping short bursts, and a second copy of
that logic would be a second place for the ordering to be got wrong.

Measured against Finn Upham's 79 hand-coded laughter annotations on this corpus: ROC AUC
0.823 against a level baseline's 0.741, and 91 per cent precision in the top 5 per cent
of windows. That is why this ships as proposals rather than as an empty tier.
"""
import numpy as np
import pytest

from musicalgestures._laughter import LAUGHTER_CLASSES, laughter_score


def test_all_six_laughter_classes_are_counted():
    """Laughter, baby laughter, giggle, snicker, belly laugh, chuckle/chortle.

    AudioSet splits laughter six ways. Using only the class called `Laughter` throws
    away the giggling and chuckling that a rehearsal is mostly made of.
    """
    assert len(LAUGHTER_CLASSES) == 6
    assert 16 in LAUGHTER_CLASSES          # Laughter
    assert 21 in LAUGHTER_CLASSES          # Chuckle, chortle


def test_the_score_is_the_strongest_laughter_class_not_their_sum():
    """A sum would let six lukewarm classes outvote one confident one, and the six are
    not independent: a real belly laugh raises `Laughter` and `Belly laugh` together."""
    clip = np.zeros((1, 527))
    clip[0, 16] = 0.8
    clip[0, 18] = 0.3
    assert laughter_score(clip)[0] == pytest.approx(0.8)


def test_a_clip_with_no_laughter_scores_zero():
    clip = np.zeros((2, 527))
    clip[0, 0] = 0.99                      # Speech
    assert laughter_score(clip).max() == pytest.approx(0.0)


def test_one_row_per_clip_is_returned():
    assert laughter_score(np.zeros((5, 527))).shape == (5,)


def test_a_clipwise_output_of_the_wrong_width_is_an_error():
    """AudioSet has 527 classes. Anything else means a different model, and the class
    indices would then point at something other than laughter."""
    with pytest.raises(ValueError):
        laughter_score(np.zeros((2, 128)))

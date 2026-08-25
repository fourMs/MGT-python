"""The speech detector is split so the part with a right answer can be tested.

silero-vad is an optional dependency and a neural network: it cannot be asserted
against exactly and it cannot run in CI. What CAN be tested is everything after it ---
turning a probability track into spans, closing short silences and dropping short
bursts --- and that is where the errors of the kind this project keeps finding live.
So the model is one thin function and the logic is another, and this tests the logic.

Order matters and is the reason this file exists: silences are closed BEFORE short
spans are dropped. A single utterance with a breath in the middle would otherwise be
discarded as two fragments rather than kept as one.
"""
import numpy as np
import pytest

from musicalgestures._voice import spans_from_probabilities


def test_one_clear_utterance_becomes_one_span():
    probs = np.zeros(100)
    probs[20:60] = 0.9
    spans = spans_from_probabilities(probs, hop_s=0.1, min_speech_s=0.2)
    assert len(spans) == 1
    assert spans[0].start == pytest.approx(2.0)
    assert spans[0].end == pytest.approx(6.0)
    assert spans[0].source == "vad"


def test_a_breath_inside_an_utterance_does_not_split_it():
    """The ordering guard: close gaps first, THEN drop short spans.

    Both fragments must be shorter than `min_speech_s` on their own and long enough
    together, or the test passes whichever order the code uses. The first version of
    this used two fragments that each already survived the filter, and it passed
    against the very mutation it was written to catch.

    Here each burst is 0.3 s against a 0.5 s minimum, separated by a 0.2 s breath. Merge
    first and one 0.8 s utterance survives; filter first and the utterance is gone.
    """
    probs = np.zeros(100)
    probs[20:23] = 0.9          # 0.3 s
    probs[25:28] = 0.9          # 0.3 s, after a 0.2 s gap
    spans = spans_from_probabilities(probs, hop_s=0.1, min_speech_s=0.5,
                                     min_silence_s=0.5)
    assert len(spans) == 1, [f"{s.start:.1f}-{s.end:.1f}" for s in spans]
    assert spans[0].start == pytest.approx(2.0)
    assert spans[0].end == pytest.approx(2.8)


def test_a_short_blip_is_dropped():
    probs = np.zeros(100)
    probs[50:51] = 0.9          # 0.1 s
    assert spans_from_probabilities(probs, hop_s=0.1, min_speech_s=0.25) == []


def test_silence_yields_no_spans_rather_than_an_error():
    assert spans_from_probabilities(np.zeros(100), hop_s=0.1) == []


def test_speech_to_the_final_sample_is_not_lost():
    """An interval left open at the end of the track must still close."""
    probs = np.zeros(50)
    probs[30:] = 0.9
    spans = spans_from_probabilities(probs, hop_s=0.1, min_speech_s=0.2)
    assert len(spans) == 1
    assert spans[0].end == pytest.approx(5.0)

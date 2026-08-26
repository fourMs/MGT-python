"""Which annotation layers coincide, and by how much.

A timeline with motion on one line and speech on another lets a reader SEE that the two
coincide. It does not let them count it, filter by it, or answer "show me every gesture
made in silence" --- and that combination question is what a qualitative annotator
actually works in. This module turns coincidence from something visible into something
addressable.

Deliberately not restricted to speech and motion. Any two levels: laughter against
gesture, gesture against a rehearsal segmentation, one annotator's tier against another's.

Two invariants carry most of the weight, and both are tested. Overlapping or unsorted
spans in the reference layer must be counted once, not twice --- a detector that emits
two touching spans would otherwise make a gesture look doubly accompanied. And the four
cells of the co-occurrence table must sum to the recording's duration, because every
instant is in exactly one of them.
"""
import pytest

from musicalgestures._actions import Action
from musicalgestures._cooccurrence import (cooccurrence_table, label_by_overlap,
                                           overlap_seconds)


def a(start, end, source="x"):
    return Action(start=start, end=end, source=source)


def test_a_span_with_no_reference_nearby_overlaps_nothing():
    assert overlap_seconds(a(0, 10), [a(20, 30)]) == pytest.approx(0.0)


def test_partial_overlap_counts_only_the_shared_part():
    assert overlap_seconds(a(0, 10), [a(8, 20)]) == pytest.approx(2.0)


def test_overlapping_reference_spans_are_counted_once():
    """Two touching detections are one region, not two seconds of double credit."""
    assert overlap_seconds(a(0, 10), [a(2, 6), a(4, 8)]) == pytest.approx(6.0)


def test_reference_spans_out_of_order_are_still_correct():
    assert overlap_seconds(a(0, 10), [a(6, 8), a(1, 3)]) == pytest.approx(4.0)


def test_a_gesture_mostly_during_speech_is_labelled_with_speech():
    spans = [a(0, 10)]
    out = label_by_overlap(spans, [a(0, 8)], name="speech", threshold=0.5)
    assert out[0].labels["speech"] == "with"
    assert out[0].features["speech_overlap"] == pytest.approx(0.8)


def test_a_gesture_mostly_in_silence_is_labelled_without():
    out = label_by_overlap([a(0, 10)], [a(0, 2)], name="speech", threshold=0.5)
    assert out[0].labels["speech"] == "without"


def test_labelling_does_not_mutate_the_input():
    """She will label the same gestures against speech AND laughter AND Finn's tiers."""
    spans = [a(0, 10)]
    label_by_overlap(spans, [a(0, 9)], name="speech")
    assert spans[0].labels == {}


def test_the_four_cells_account_for_the_whole_recording():
    """The invariant: every instant is in exactly one cell."""
    t = cooccurrence_table([a(0, 10), a(20, 30)], [a(5, 25)], duration_s=40.0)
    assert t["both"] == pytest.approx(10.0)
    assert t["a_only"] == pytest.approx(10.0)
    assert t["b_only"] == pytest.approx(10.0)
    assert t["neither"] == pytest.approx(10.0)
    assert sum(t[k] for k in ("both", "a_only", "b_only", "neither")) == pytest.approx(40.0)


def test_an_empty_layer_puts_everything_in_the_other_cells():
    t = cooccurrence_table([a(0, 10)], [], duration_s=20.0)
    assert t["both"] == pytest.approx(0.0)
    assert t["a_only"] == pytest.approx(10.0)
    assert t["neither"] == pytest.approx(10.0)


def test_threshold_zero_means_touches_at_all_not_always_true():
    """The edge case a naive comparison gets backwards.

    `threshold=0.0` is the natural way to ask "does this gesture touch speech at all",
    and it is the setting an exploratory annotator reaches for first. Written as
    `frac >= threshold` it is true for everything, including spans with no overlap
    whatsoever, and every gesture in the recording comes back labelled "with speech".
    """
    out = label_by_overlap([a(0, 10)], [a(50, 60)], name="speech", threshold=0.0)
    assert out[0].labels["speech"] == "without"

    touching = label_by_overlap([a(0, 10)], [a(9, 60)], name="speech", threshold=0.0)
    assert touching[0].labels["speech"] == "with"

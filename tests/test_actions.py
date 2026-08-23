"""Actions cut from a motion envelope, and the shape of what was cut.

The signals here are built so the right answer is not a matter of opinion: three separated
bursts are three actions, a decaying spike is impulsive, a plateau is sustained, and a
tremolo is iterative. If the thresholds are ever retuned, these say what must not change.
"""
import numpy as np
import pytest

from musicalgestures._actions import (
    Action,
    action_type,
    describe_actions,
    segment_actions,
)

FS = 100.0


def _silence(seconds):
    return np.zeros(int(seconds * FS))


def _burst(seconds, shape="flat"):
    n = int(seconds * FS)
    if shape == "flat":
        return np.ones(n)
    if shape == "decay":
        return np.exp(-np.linspace(0, 6, n))
    if shape == "tremolo":
        return 0.5 + 0.5 * np.sin(2 * np.pi * 8 * np.linspace(0, seconds, n))
    raise ValueError(shape)


class TestSegmentation:
    def test_three_separated_bursts_are_three_actions(self):
        env = np.concatenate([_silence(1), _burst(0.5), _silence(1),
                              _burst(0.5), _silence(1), _burst(0.5), _silence(1)])
        assert len(segment_actions(env, FS)) == 3

    def test_a_still_recording_has_no_actions(self):
        assert segment_actions(_silence(5), FS) == []

    def test_boundaries_land_where_the_movement_is(self):
        env = np.concatenate([_silence(1), _burst(0.5), _silence(1)])
        a, = segment_actions(env, FS)
        assert a.start == pytest.approx(1.0, abs=0.05)
        assert a.end == pytest.approx(1.5, abs=0.05)

    def test_a_momentary_dip_does_not_split_one_action_in_two(self):
        """A gap shorter than min_gap is closed, and the closing happens before short
        spans are dropped, or the halves would be discarded rather than joined."""
        env = np.concatenate([_silence(1), _burst(0.3), _silence(0.05),
                              _burst(0.3), _silence(1)])
        assert len(segment_actions(env, FS, min_gap=0.2)) == 1

    def test_a_flicker_shorter_than_min_duration_is_not_an_action(self):
        env = np.concatenate([_silence(1), _burst(0.02), _silence(1)])
        assert segment_actions(env, FS, min_duration=0.1) == []

    def test_the_threshold_is_relative_so_scale_does_not_matter(self):
        env = np.concatenate([_silence(1), _burst(0.5), _silence(1)])
        assert len(segment_actions(env, FS)) == len(segment_actions(env * 1000, FS))

    def test_movement_at_the_very_start_and_end_is_not_lost(self):
        env = np.concatenate([_burst(0.5), _silence(1), _burst(0.5)])
        assert len(segment_actions(env, FS)) == 2

    def test_source_is_recorded_so_segmenters_can_be_told_apart(self):
        env = np.concatenate([_silence(1), _burst(0.5), _silence(1)])
        a, = segment_actions(env, FS, source="pose-qom")
        assert a.source == "pose-qom"


class TestActionType:
    def test_a_decaying_spike_is_impulsive(self):
        assert action_type(_burst(0.4, "decay"), FS)["type"] == "impulsive"

    def test_a_plateau_is_sustained(self):
        assert action_type(_burst(1.0, "flat"), FS)["type"] == "sustained"

    def test_a_tremolo_is_iterative(self):
        assert action_type(_burst(1.0, "tremolo"), FS)["type"] == "iterative"

    def test_iterative_wins_over_sustained(self):
        """A repeated movement is also a held one by the sustain measure; the repetition
        is the more specific description, so it is tested first."""
        out = action_type(_burst(1.0, "tremolo"), FS)
        assert out["sustain"] >= 0.35 and out["type"] == "iterative"

    def test_the_evidence_for_the_call_is_returned(self):
        out = action_type(_burst(1.0, "tremolo"), FS)
        assert out["peaks"] >= 3
        assert 0.0 <= out["sustain"] <= 1.0
        assert 0.0 <= out["centroid"] <= 1.0

    def test_an_impulse_is_front_loaded_and_a_plateau_is_centred(self):
        """The measure the impulsive/sustained call rests on."""
        assert action_type(_burst(0.4, "decay"), FS)["centroid"] < 0.42
        assert action_type(_burst(1.0, "flat"), FS)["centroid"] == pytest.approx(0.5, abs=0.02)

    def test_a_perfectly_steady_span_is_sustained(self):
        """Its minimum and its peak are the same number, which an earlier version of this
        measured from and so called the steadiest possible movement impulsive."""
        assert action_type(np.ones(50), FS)["type"] == "sustained"

    @pytest.mark.parametrize("n", [0, 1, 2])
    def test_too_few_samples_gives_a_default_rather_than_raising(self, n):
        assert action_type(np.zeros(n), FS)["type"] == "impulsive"


class TestDescribe:
    def test_each_action_gets_its_own_shape(self):
        env = np.concatenate([_silence(0.5), _burst(0.4, "decay"), _silence(0.5),
                              _burst(1.0, "tremolo"), _silence(0.5)])
        actions = describe_actions(segment_actions(env, FS), env, FS)
        assert [a.features["type"] for a in actions] == ["impulsive", "iterative"]

    def test_describing_fills_features_and_never_labels(self):
        """A shape is measured; a name is claimed. The module does not confuse them."""
        env = np.concatenate([_silence(0.5), _burst(0.5), _silence(0.5)])
        a, = describe_actions(segment_actions(env, FS), env, FS)
        assert a.features and a.labels == {}


class TestActionRecord:
    def test_duration(self):
        assert Action(1.0, 2.5).duration == pytest.approx(1.5)

    def test_overlap_is_symmetric(self):
        a, b = Action(0, 2), Action(1, 3)
        assert a.overlaps(b) and b.overlaps(a)

    def test_touching_actions_do_not_overlap(self):
        assert not Action(0, 1).overlaps(Action(1, 2))

    def test_labels_are_per_recogniser_so_two_may_disagree(self):
        a = Action(0, 1)
        a.labels["pose-gcn"] = "wave"
        a.labels["video-i3d"] = "clapping"
        assert len(a.labels) == 2

"""Postures cut from landmark trajectories, and poses as labels attached to some of them.

The synthetic bodies here are built so the right answer is not a matter of opinion: a shape
held for three seconds is one posture, a walk across the frame in a held shape is still one
posture, and a transition between two shapes is a boundary. If the stability criterion is
ever retuned, these say what must not change.
"""
import numpy as np
import pytest

from musicalgestures._postures import (
    Posture,
    average_posture,
    configuration_distance,
    describe_postures,
    key_postures,
    match_postures,
    posture_shape,
    segment_postures,
)

FS = 25.0


def _skeleton(arms="down"):
    """A 33-landmark body in image pixels: shoulders at y=100, hips at y=200."""
    pts = np.zeros((33, 2))
    pts[:, 0] = np.linspace(-10, 10, 33)     # incidental spread so no landmark is special
    pts[:, 1] = 150.0
    pts[11] = (-25, 100)                     # shoulders
    pts[12] = (25, 100)
    pts[23] = (-15, 200)                     # hips
    pts[24] = (15, 200)
    if arms == "down":
        pts[15] = (-30, 190)                 # wrists
        pts[16] = (30, 190)
    elif arms == "t":
        pts[15] = (-80, 100)
        pts[16] = (80, 100)
    else:
        raise ValueError(arms)
    return pts


def _hold(shape, seconds):
    n = int(seconds * FS)
    return np.repeat(shape[None, :, :], n, axis=0)


def _transition(a, b, seconds):
    n = int(seconds * FS)
    w = np.linspace(0, 1, n)[:, None, None]
    return a[None] * (1 - w) + b[None] * w


def _with_visibility(xy, visible=1.0):
    vis = np.full(xy.shape[:2] + (1,), visible)
    return np.concatenate([xy, vis], axis=2)


DOWN = _skeleton("down")
TPOSE = _skeleton("t")


class TestSegmentation:
    def test_a_held_shape_is_one_posture(self):
        lm = _with_visibility(_hold(DOWN, 3))
        postures = segment_postures(lm, FS)
        assert len(postures) == 1
        assert postures[0].duration == pytest.approx(3.0, abs=0.3)

    def test_two_holds_around_a_transition_are_two_postures(self):
        lm = _with_visibility(np.concatenate([
            _hold(DOWN, 3), _transition(DOWN, TPOSE, 1), _hold(TPOSE, 3)]))
        postures = segment_postures(lm, FS)
        assert len(postures) == 2
        assert postures[0].end <= 3.5
        assert postures[1].start >= 3.5

    def test_walking_in_a_held_shape_is_still_one_posture(self):
        """Position is not posture: translating the whole body changes every coordinate
        and no relationship between them."""
        frames = _hold(TPOSE, 4)
        drift = np.linspace(0, 200, len(frames))[:, None]
        frames = frames + np.stack([drift, np.zeros_like(drift)], axis=2)
        postures = segment_postures(_with_visibility(frames), FS)
        assert len(postures) == 1

    def test_continuous_movement_yields_no_postures(self):
        lm = _with_visibility(np.concatenate([
            _transition(DOWN, TPOSE, 1), _transition(TPOSE, DOWN, 1),
            _transition(DOWN, TPOSE, 1), _transition(TPOSE, DOWN, 1)]))
        assert segment_postures(lm, FS) == []

    def test_a_hold_shorter_than_min_duration_is_not_a_posture(self):
        lm = _with_visibility(np.concatenate([
            _transition(DOWN, TPOSE, 1), _hold(TPOSE, 0.3),
            _transition(TPOSE, DOWN, 1)]))
        assert segment_postures(lm, FS, min_duration=1.0) == []

    def test_a_momentary_wobble_does_not_split_a_hold(self):
        wobble = _hold(DOWN, 0.12).copy()
        wobble[:, 15] += 40                  # one wrist flicks out and back
        lm = _with_visibility(np.concatenate([_hold(DOWN, 2), wobble, _hold(DOWN, 2)]))
        assert len(segment_postures(lm, FS, min_gap=0.5)) == 1

    def test_detection_gaps_are_not_postures(self):
        """A stretch the detector missed is unknown, not held: NaN frames neither extend
        a posture nor form one."""
        held = _hold(DOWN, 2)
        gap = np.full_like(_hold(DOWN, 2), np.nan)
        lm = _with_visibility(np.concatenate([held, gap, held]))
        postures = segment_postures(lm, FS, min_gap=0.1)
        assert len(postures) == 2

    def test_landmark_jitter_does_not_break_a_hold(self):
        rng = np.random.default_rng(0)
        frames = _hold(DOWN, 3) + rng.normal(0, 0.5, _hold(DOWN, 3).shape)
        assert len(segment_postures(_with_visibility(frames), FS)) == 1

    def test_each_posture_carries_its_configuration(self):
        lm = _with_visibility(_hold(TPOSE, 3))
        p, = segment_postures(lm, FS)
        assert p.configuration.shape == (33, 2)
        # normalised units: pelvis at the origin, torso length 1
        pelvis = p.configuration[[23, 24]].mean(axis=0)
        assert np.allclose(pelvis, 0, atol=1e-6)


class TestConfigurationDistance:
    def test_a_shape_is_at_distance_zero_from_itself(self):
        lm = _with_visibility(_hold(DOWN, 2))
        p, = segment_postures(lm, FS)
        assert configuration_distance(p.configuration, p.configuration) == pytest.approx(0.0)

    def test_different_shapes_are_far_apart(self):
        a, = segment_postures(_with_visibility(_hold(DOWN, 2)), FS)
        b, = segment_postures(_with_visibility(_hold(TPOSE, 2)), FS)
        assert configuration_distance(a.configuration, b.configuration) > 0.05


class TestKeyPostures:
    def test_returns_to_the_same_shape_group_together(self):
        lm = _with_visibility(np.concatenate([
            _hold(DOWN, 2), _transition(DOWN, TPOSE, 1), _hold(TPOSE, 2),
            _transition(TPOSE, DOWN, 1), _hold(DOWN, 2)]))
        postures = segment_postures(lm, FS)
        assert len(postures) == 3
        clusters = key_postures(postures)
        assert len(clusters) == 2
        # the recurring shape holds the most total time and comes first
        assert clusters[0]["total_duration"] == pytest.approx(4.0, abs=0.6)
        assert len(clusters[0]["postures"]) == 2


class TestPoseLayer:
    def test_labels_are_empty_by_default(self):
        p, = segment_postures(_with_visibility(_hold(DOWN, 2)), FS)
        assert p.labels == {}

    def test_match_postures_labels_only_what_matches(self):
        lm = _with_visibility(np.concatenate([
            _hold(DOWN, 2), _transition(DOWN, TPOSE, 1), _hold(TPOSE, 2)]))
        postures = segment_postures(lm, FS)
        template, = segment_postures(_with_visibility(_hold(TPOSE, 1)),
                                     FS, min_duration=0.5)
        matched = match_postures(postures, template.configuration, name="t-pose")
        assert [p.labels.get("template") for p in matched] == [None, "t-pose"]


class TestShape:
    def test_a_t_pose_is_wider_spread_than_arms_down(self):
        a, = segment_postures(_with_visibility(_hold(DOWN, 2)), FS)
        b, = segment_postures(_with_visibility(_hold(TPOSE, 2)), FS)
        assert posture_shape(b.configuration)["spread"] > posture_shape(a.configuration)["spread"]

    def test_describe_fills_features_and_never_labels(self):
        postures = segment_postures(_with_visibility(_hold(DOWN, 2)), FS)
        described = describe_postures(postures)
        assert "spread" in described[0].features
        assert described[0].labels == {}


class TestDetectorAgnostic:
    """The higher-level analysis must not care which detector made the landmarks."""

    def _coco_skeleton(self, arms="down"):
        pts = np.zeros((17, 2))
        pts[:, 1] = 150.0
        pts[5] = (-25, 100)                  # shoulders
        pts[6] = (25, 100)
        pts[11] = (-15, 200)                 # hips
        pts[12] = (15, 200)
        pts[9] = (-30, 190) if arms == "down" else (-80, 100)   # wrists
        pts[10] = (30, 190) if arms == "down" else (80, 100)
        return pts

    def test_coco_17_landmarks_segment_like_mediapipe(self):
        down, t = self._coco_skeleton("down"), self._coco_skeleton("t")
        lm = _with_visibility(np.concatenate([
            _hold(down, 3), _transition(down, t, 1), _hold(t, 3)]))
        postures = segment_postures(lm, FS)
        assert len(postures) == 2
        assert postures[0].configuration.shape == (17, 2)

    def test_an_unknown_topology_asks_for_anchors(self):
        with pytest.raises(ValueError, match="anchors"):
            segment_postures(_with_visibility(_hold(DOWN, 2)[:, :20]), FS)


class TestAveragePosture:
    def test_the_average_is_the_shape_mostly_held(self):
        """9 s arms down against 1 s of T-shape: the habitual carriage is arms down,
        and a mean would have dragged the wrists partway up."""
        lm = _with_visibility(np.concatenate([_hold(DOWN, 9), _hold(TPOSE, 1)]))
        avg = average_posture(lm)
        held, = segment_postures(_with_visibility(_hold(DOWN, 2)), FS)
        assert configuration_distance(avg, held.configuration) < 0.02


class TestPosture:
    def test_overlap_and_duration(self):
        a = Posture(start=1.0, end=2.0)
        b = Posture(start=1.5, end=3.0)
        c = Posture(start=2.5, end=3.5)
        assert a.overlaps(b) and not a.overlaps(c)
        assert a.duration == pytest.approx(1.0)

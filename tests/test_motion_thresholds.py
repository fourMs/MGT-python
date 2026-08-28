"""Thresholds that keep human motion and drop what is not, per measure.

`mg_motion`'s `threshold` exists because a frame difference is mostly sensor noise, and
the same is true of every other motion measure --- but each has its own units and its own
floor, so one number cannot serve all of them:

* a **motion vector** is a displacement in pixels, and H.264 codes to quarter-pel, so a
  large share of vectors are fractions of a pixel that the encoder chose for rate reasons
  rather than because anything moved. Measured on this corpus, 46 per cent of vectors are
  exactly zero and the median non-zero one is 0.79 px.
* a **pose landmark** carries the model's own confidence, and 16 per cent of landmarks
  here sit below 0.5 --- MediaPipe estimating a limb it cannot see.

These tests pin the behaviour, not the numbers: a threshold must remove small things,
keep large ones, and never turn a real movement into nothing.
"""
import numpy as np
import pytest

from musicalgestures._posegram import pose_activity


class Test_motion_vector_displacement_gate:
    """H.264 codes motion to quarter-pel, so a large share of vectors are fractions of a
    pixel chosen for rate reasons rather than because anything moved."""

    def test_a_threshold_removes_small_vectors_and_keeps_large_ones(self, tmp_path):
        from _synth import moving_block_video
        from musicalgestures._motionvectors import motion_vector_views
        clip = moving_block_video(tmp_path / "c.mp4", dx=6, frames=80)
        loose = motion_vector_views(clip, deterministic=True)
        tight = motion_vector_views(clip, deterministic=True, threshold=2.0)
        #: the block moves 6 px a frame, so its own vectors survive a 2 px gate
        assert tight.magnitude.sum() > 0
        #: and the small ones the encoder scattered elsewhere do not
        assert tight.magnitude.sum() < loose.magnitude.sum()

    def test_a_gate_above_the_real_motion_removes_everything(self, tmp_path):
        from _synth import moving_block_video
        from musicalgestures._motionvectors import motion_vector_views
        clip = moving_block_video(tmp_path / "c2.mp4", dx=3, frames=60)
        out = motion_vector_views(clip, deterministic=True, threshold=500.0)
        assert out.magnitude.sum() == pytest.approx(0.0, abs=1e-9)

    def test_it_is_off_by_default(self, tmp_path):
        from _synth import moving_block_video
        from musicalgestures._motionvectors import motion_vector_views
        clip = moving_block_video(tmp_path / "c3.mp4", dx=3, frames=60)
        assert motion_vector_views(clip, deterministic=True).magnitude.sum() > 0


class Test_pose_visibility_gate:
    def _landmarks(self, n=100, visibility=1.0):
        a = np.zeros((n, 33, 3))
        a[:, :, 0] = 100.0
        a[:, :, 1] = 100.0
        a[:, :, 2] = visibility
        #: one landmark genuinely moving
        a[:, 15, 0] = np.linspace(50, 250, n)
        return a

    def test_a_confident_landmark_is_kept(self):
        a = self._landmarks(visibility=0.95)
        act = pose_activity(a, min_visibility=0.5)
        assert act[15].sum() > 0

    def test_an_unconfident_landmark_is_dropped(self):
        a = self._landmarks(visibility=0.2)
        act = pose_activity(a, min_visibility=0.5)
        assert act[15].sum() == pytest.approx(0.0, abs=1e-9)

    def test_the_gate_is_off_by_default(self):
        """Existing callers must not silently change their numbers."""
        a = self._landmarks(visibility=0.2)
        assert pose_activity(a)[15].sum() > 0

    def test_a_landmark_that_drops_below_confidence_midway_stops_counting(self):
        a = self._landmarks(visibility=0.95)
        a[50:, 15, 2] = 0.1
        act = pose_activity(a, min_visibility=0.5)
        assert act[15, :45].sum() > 0
        assert act[15, 55:].sum() == pytest.approx(0.0, abs=1e-9)

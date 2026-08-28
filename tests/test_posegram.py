"""A posegram: which part of the body moved, and when.

MGT can already draw where a pose went (`pose_waterfall`, trajectories), how its segments
are angled (`pose_segments`) and how its centre moves (`pose_center`). None of them
answers the question a motiongram answers for pixels --- what was moving at 04:12 --- with
the body rather than the image as the frame of reference.

The rows are the point. MediaPipe's 33 landmarks are indexed in the order the model emits
them, which scatters the body: nose, eyes, ears, mouth, then shoulders, elbows, wrists,
then eight hand points, then hips, knees, ankles, feet. Plotted in that order the image is
unreadable. Ordered head to foot it reads as a body, and a run of bright rows is a limb.
"""
import numpy as np
import pytest

from musicalgestures._posegram import ANATOMICAL_ORDER, pose_activity


def _still(n=200, n_landmarks=33):
    """A pose that does not move, plus a little jitter so nothing is exactly zero."""
    rng = np.random.default_rng(0)
    a = np.zeros((n, n_landmarks, 3))
    a[:, :, :2] = rng.normal(0, 0.01, (n, n_landmarks, 2)) + np.arange(n_landmarks)[:, None]
    a[:, :, 2] = 1.0
    return a


class Test_it_finds_the_part_that_moved:
    def test_a_moving_landmark_stands_out(self):
        a = _still()
        a[:, 15, 0] += np.sin(np.linspace(0, 40, len(a))) * 30      # left wrist
        activity = pose_activity(a)
        assert activity[15].mean() > 10 * np.median(activity.mean(axis=1))

    def test_it_finds_when_as_well_as_where(self):
        a = _still(n=300)
        a[100:150, 15, 0] += np.sin(np.linspace(0, 20, 50)) * 30
        activity = pose_activity(a)
        assert activity[15, 100:150].mean() > 10 * activity[15, :90].mean()

    def test_undetected_frames_do_not_read_as_movement(self):
        """All-NaN rows are how the extractor marks a frame with no pose. Differencing
        across one must not invent a jump."""
        a = _still()
        a[80:90] = np.nan
        activity = pose_activity(a)
        assert np.isfinite(activity).all()
        assert activity[:, 78:92].max() < 1.0


class Test_the_rows_are_a_body:
    def test_every_landmark_appears_exactly_once(self):
        assert len(ANATOMICAL_ORDER) == 33
        assert sorted(ANATOMICAL_ORDER) == list(range(33))

    def test_it_runs_head_to_foot(self):
        """Nose before wrists before ankles: the ordering carries anatomy, so a limb is
        a contiguous band of rows rather than four scattered lines."""
        pos = {lm: i for i, lm in enumerate(ANATOMICAL_ORDER)}
        assert pos[0] < pos[15]        # nose above left wrist
        assert pos[15] < pos[27]       # left wrist above left ankle
        assert abs(pos[15] - pos[16]) <= 2      # the two wrists sit together

    def test_activity_is_returned_in_that_order(self):
        a = _still()
        a[:, 27, 0] += np.sin(np.linspace(0, 40, len(a))) * 30      # left ankle
        activity = pose_activity(a, anatomical=True)
        assert int(np.argmax(activity.mean(axis=1))) == ANATOMICAL_ORDER.index(27)

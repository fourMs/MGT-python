"""A posegram on the image's own axes, so it can be laid beside a motiongram.

The landmark-row posegram answers "which body part moved when". This one answers the
question a motiongram answers --- "what moved, at what height, when" --- but from the
body rather than from the pixels. Same axes as a vertical motiongram: image y down the
page, time across it, brightness for motion at that height.

That makes the two comparable rather than merely analogous: a diagonal in one should be a
diagonal in the other, and where they disagree, one of them is wrong about the body.
"""
import numpy as np
import pytest

from musicalgestures._posegram import pose_spatial_gram


def _pose(n, n_landmarks=33, height=480):
    a = np.zeros((n, n_landmarks, 3))
    a[:, :, 0] = 320.0
    a[:, :, 1] = height / 2
    a[:, :, 2] = 1.0
    return a


class Test_it_uses_image_coordinates:
    def test_shape_is_bins_by_frames(self):
        a = _pose(120)
        g = pose_spatial_gram(a, height=480, width=640, bins=100)
        assert g.shape == (100, 120)

    def test_a_landmark_travelling_down_draws_a_diagonal(self):
        """The property that makes this a motiongram and not a bar chart."""
        n = 200
        a = _pose(n)
        a[:, 15, 1] = np.linspace(20, 460, n)          # left wrist, top to bottom
        a[:, 15, 0] += np.sin(np.linspace(0, 60, n))   # keep it moving, so speed > 0
        g = pose_spatial_gram(a, height=480, width=640, bins=120)
        lit = [int(np.argmax(g[:, i])) for i in range(n) if g[:, i].max() > 0]
        assert len(lit) > n // 2
        assert lit[-1] > lit[0] + 30

    def test_a_landmark_travelling_up_draws_the_other_diagonal(self):
        n = 200
        a = _pose(n)
        a[:, 15, 1] = np.linspace(460, 20, n)
        a[:, 15, 0] += np.sin(np.linspace(0, 60, n))
        g = pose_spatial_gram(a, height=480, width=640, bins=120)
        lit = [int(np.argmax(g[:, i])) for i in range(n) if g[:, i].max() > 0]
        assert lit[-1] < lit[0] - 30


class Test_landmarks_outside_the_frame:
    """MediaPipe estimates landmarks it cannot see, and puts them outside the picture.

    On a real 640x360 extraction the maximum y was 1529 --- four times the frame height ---
    while the body itself lived between 73 and 435. Scaling the plot by the data's maximum
    squeezed every real landmark into the top quarter and left the rest black. The frame
    size has to come from the frame, not from the data.
    """

    def test_one_wild_landmark_does_not_squash_the_plot(self):
        n = 200
        a = _pose(n)
        a[:, 15, 1] = np.linspace(60, 420, n)
        a[:, 15, 0] += np.sin(np.linspace(0, 60, n))
        a[:, 31, 1] = 1529.0                       # an estimate far below the frame
        a[:, 31, 0] += np.sin(np.linspace(0, 60, n))
        g = pose_spatial_gram(a, height=480, width=640, bins=120)
        lit = np.flatnonzero(g.sum(axis=1) > 0)
        # the travelling landmark should sweep a wide band, not sit in a sliver
        assert lit.max() - lit.min() > 60

    def test_it_is_bounded_by_the_frame_it_was_given(self):
        a = _pose(100)
        a[:, 31, 1] = 5000.0
        a[:, 31, 0] += np.sin(np.linspace(0, 30, 100))
        g = pose_spatial_gram(a, height=480, width=640, bins=100)
        assert np.isfinite(g).all()
        assert g.shape[0] == 100


class Test_what_the_brightness_means:
    def test_speed_weighting_ignores_a_body_that_is_present_but_still(self):
        g = pose_spatial_gram(_pose(150), height=480, width=640, bins=80,
                              weight="speed")
        assert g.max() == pytest.approx(0.0, abs=1e-9)

    def test_presence_weighting_shows_it(self):
        g = pose_spatial_gram(_pose(150), height=480, width=640, bins=80,
                              weight="presence")
        assert g.max() > 0

    def test_the_horizontal_axis_uses_x(self):
        n = 200
        a = _pose(n)
        a[:, 15, 0] = np.linspace(20, 620, n)
        a[:, 15, 1] += np.sin(np.linspace(0, 60, n))
        g = pose_spatial_gram(a, height=480, width=640, bins=120, axis="horizontal")
        lit = [int(np.argmax(g[:, i])) for i in range(n) if g[:, i].max() > 0]
        assert lit[-1] > lit[0] + 30

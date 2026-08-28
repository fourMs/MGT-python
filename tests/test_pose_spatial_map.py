"""A 2-D map of where the body was, in the frame's own coordinates.

The other measures' "where" panels are images of the room: accumulate the per-pixel
difference, or the flow magnitude, over the whole recording and you get a picture with a
bright patch where things happened. The pose equivalent has to be the same KIND of object
--- a (height, width) image --- and not a gram with time on one axis, which is what a
spatial *gram* is and which looks, correctly, like a squashed posegram.
"""
import numpy as np
import pytest

from musicalgestures._posegram import pose_spatial_map


def _pose(n, n_landmarks=33):
    a = np.zeros((n, n_landmarks, 3))
    a[:, :, 0] = 320.0
    a[:, :, 1] = 240.0
    a[:, :, 2] = 1.0
    return a


class Test_it_is_an_image_of_the_frame:
    def test_shape_is_height_by_width(self):
        m = pose_spatial_map(_pose(120), width=640, height=480, bins=(90, 120))
        assert m.shape == (90, 120)

    def test_a_landmark_crossing_left_to_right_lights_a_horizontal_band(self):
        n = 300
        a = _pose(n)
        #: Only the travelling landmark is present. With the other 32 parked at one
        #: point they outvote it 32 to 1 and the brightest row is theirs, not its ---
        #: which is what the first version of this test actually measured.
        a[:, :, :] = np.nan
        a[:, 15, 0] = np.linspace(40, 600, n)
        a[:, 15, 1] = 120.0
        a[:, 15, 2] = 1.0
        m = pose_spatial_map(a, width=640, height=480, bins=(96, 128), weight="presence")
        rows = m.sum(axis=1)
        band = int(np.argmax(rows))
        # 120/480 of 96 rows is row 24
        assert abs(band - 24) <= 4
        assert m[band].max() > 0
        lit_cols = np.flatnonzero(m[band] > 0)
        assert lit_cols.max() - lit_cols.min() > 40      # it swept across

    def test_a_landmark_that_stays_put_lights_one_place(self):
        m = pose_spatial_map(_pose(200), width=640, height=480, bins=(96, 128),
                             weight="presence")
        lit = np.argwhere(m > m.max() * 0.5)
        assert np.ptp(lit[:, 0]) < 8 and np.ptp(lit[:, 1]) < 8


class Test_what_it_weights_by:
    def test_speed_ignores_a_body_that_is_present_but_still(self):
        m = pose_spatial_map(_pose(150), width=640, height=480, bins=(60, 80),
                             weight="speed")
        assert m.max() == pytest.approx(0.0, abs=1e-9)

    def test_landmarks_outside_the_frame_are_dropped_not_clamped(self):
        """MediaPipe places unseen landmarks outside the picture. Clamping them would
        pile a lost limb onto the edge and draw a bright rim no body ever made."""
        a = _pose(120)
        a[:, 31, 0] = 5000.0
        a[:, 31, 1] = 5000.0
        m = pose_spatial_map(a, width=640, height=480, bins=(60, 80), weight="presence")
        assert m[-1, -1] == pytest.approx(0.0, abs=1e-9)
        assert np.isfinite(m).all()

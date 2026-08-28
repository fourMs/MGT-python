"""Posegrams follow the motiongram convention: the two views run in different directions.

In MGT a **horizontal** videogram tiles each frame's column left to right, so time runs
across and image *y* runs down. A **vertical** one tiles each frame's row top to bottom, so
time runs down and image *x* runs across. The pair is meant to be laid around the video
frame, which only works if each shares its spatial axis with the picture.

A pose view drawn with time on the x axis in both orientations breaks that, and cannot be
placed beside a motiongram of the same recording.
"""
import numpy as np
import pytest

from musicalgestures._posegram import posegram_arrays


def _pose(n, n_landmarks=33):
    a = np.full((n, n_landmarks, 3), np.nan)
    a[:, 15, 2] = 1.0
    return a


class Test_the_two_views_run_in_different_directions:
    def test_horizontal_has_time_across_and_y_down(self):
        n = 240
        a = _pose(n)
        a[:, 15, 1] = np.linspace(30, 450, n)     # travels down the frame
        a[:, 15, 0] = 320.0
        h, v = posegram_arrays(a, width=640, height=480, bins=120)
        assert h.shape[1] == n                     # a column per frame
        lit = [int(np.argmax(h[:, i])) for i in range(n) if h[:, i].max() > 0]
        assert lit[-1] > lit[0] + 40               # the diagonal runs down as time runs right

    def test_vertical_has_time_down_and_x_across(self):
        n = 240
        a = _pose(n)
        a[:, 15, 0] = np.linspace(30, 600, n)     # travels across the frame
        a[:, 15, 1] = 240.0
        h, v = posegram_arrays(a, width=640, height=480, bins=120)
        assert v.shape[0] == n                     # a ROW per frame
        lit = [int(np.argmax(v[i])) for i in range(n) if v[i].max() > 0]
        assert lit[-1] > lit[0] + 40               # the diagonal runs right as time runs down

    def test_the_spatial_axis_of_each_matches_the_picture(self):
        """Horizontal is as tall as the frame's bins; vertical is as wide."""
        a = _pose(100)
        a[:, 15, 0] = 300.0
        a[:, 15, 1] = 200.0
        h, v = posegram_arrays(a, width=640, height=480, bins=90)
        assert h.shape[0] == 90
        assert v.shape[1] == 90

"""Tests for musicalgestures._motionanalysis.motiongram_data (orientation option)."""
import numpy as np
import pytest

from musicalgestures import motiongram_data


def falling_bar_frames(T=30, H=40, W=60):
    """A bright horizontal bar moving downward one row per frame."""
    frames = np.zeros((T, H, W), dtype=np.float32)
    for i in range(T):
        frames[i, 5 + i, :] = 255.0
    return frames


class TestMotiongramData:
    def test_vertical_traces_falling_bar(self):
        frames = falling_bar_frames()
        gram = motiongram_data(frames, orientation="vertical")
        assert gram.shape == (40, 29)          # (H, T-1), time on axis 1
        # the motion energy at time t sits at rows 5+t / 6+t: the ridge descends
        rows = gram.argmax(axis=0)
        assert np.all(np.diff(rows) >= 0)
        assert rows[0] in (5, 6)
        assert rows[-1] in (33, 34)

    def test_horizontal_of_falling_bar_is_uniform(self):
        frames = falling_bar_frames()
        gram = motiongram_data(frames, orientation="horizontal")
        assert gram.shape == (60, 29)          # (W, T-1)
        # a full-width bar moving vertically spreads evenly over columns
        assert gram.std() / (gram.mean() + 1e-12) < 1e-6

    def test_videogram_mode(self):
        frames = falling_bar_frames()
        gram = motiongram_data(frames, orientation="vertical", frame_diff=False)
        assert gram.shape == (40, 30)          # T columns, no differencing

    def test_normalization(self):
        frames = falling_bar_frames()
        gram = motiongram_data(frames)
        assert gram.max() == pytest.approx(1.0)
        raw = motiongram_data(frames, normalize=False)
        assert raw.max() > 1.0

    def test_bad_input_raises(self):
        with pytest.raises(ValueError):
            motiongram_data(np.zeros((5, 5)))
        with pytest.raises(ValueError):
            motiongram_data(falling_bar_frames(), orientation="diagonal")

"""The space motion happened in, accumulated from the codec's vectors.

`motionhistory()` already renders a Bobick--Davis image from frame differences, and
`heatmap()` already accumulates where pixels changed. What neither can do is say which
*way* things moved, because a frame difference has no sign: a dancer entering a region and
leaving it look alike. A motion vector is a displacement, so accumulating vectors keeps the
direction, and that is what these tests are about.

Ground truth is generated. A block travelling a known path leaves its accumulation on that
path and nowhere else, and travelling the other way reverses the sign --- neither of which
a clip of real dancing could establish.
"""
import numpy as np
import pytest

import musicalgestures
from _synth import moving_block_video, oscillating_block_video

av = pytest.importorskip("av", reason="motion-vector data needs the optional 'av' extra")

from musicalgestures._motionvectors import accumulate_motion_vectors  # noqa: E402


@pytest.fixture(scope="module")
def moving_right(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("mvh") / "right.mp4", dx=4, dy=0,
                              frames=48)


@pytest.fixture(scope="module")
def moving_left(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("mvh") / "left.mp4", dx=-4, dy=0,
                              frames=48)


class Test_where_the_motion_was:
    def test_accumulates_on_the_row_the_block_crossed_and_not_elsewhere(self, moving_right):
        weight, _, _, _ = accumulate_motion_vectors(moving_right)
        rows = weight.sum(axis=1)
        travelled = int(np.argmax(rows))
        far = (np.arange(len(rows)) < travelled - 3) | (np.arange(len(rows)) > travelled + 3)
        assert rows[travelled] > 10 * rows[far].mean()

    def test_the_accumulator_covers_the_frame(self, moving_right):
        weight, vx, vy, _ = accumulate_motion_vectors(moving_right)
        assert weight.shape == vx.shape == vy.shape
        assert weight.ndim == 2
        assert weight.sum() > 0


class Test_which_way_it_went:
    """The reason to accumulate vectors rather than frame differences."""

    def test_rightward_travel_accumulates_a_rightward_direction(self, moving_right):
        weight, vx, vy, _ = accumulate_motion_vectors(moving_right)
        busy = weight > np.percentile(weight[weight > 0], 75)
        assert np.median(vx[busy]) > 1.0
        assert abs(np.median(vy[busy])) < 1.0

    def test_leftward_travel_reverses_the_sign(self, moving_left):
        weight, vx, vy, _ = accumulate_motion_vectors(moving_left)
        busy = weight > np.percentile(weight[weight > 0], 75)
        assert np.median(vx[busy]) < -1.0


class Test_directional_coherence:
    """One-way travel and back-and-forth leave the same motion in the same place, and
    only coherence tells them apart. Without it the history image paints a cell that saw
    a dancer pass all afternoon the same as one that saw only encoder noise."""

    def test_consistent_travel_is_coherent(self, moving_right):
        weight, _, _, coherence = accumulate_motion_vectors(moving_right)
        busy = weight > np.percentile(weight[weight > 0], 90)
        assert np.median(coherence[busy]) > 0.5

    def test_going_back_and_forth_is_not(self, tmp_path):
        """A slow oscillation. P-frames arrive at about a quarter of the frame rate, so
        a reversal faster than a few samples per cycle is under-sampled and reads as
        coherent: at 3 samples per cycle this measures 0.97, at 12 it measures 0.06.
        That is a real limit of the method, recorded in the docstring, and the fixture
        here sits well inside it."""
        path = oscillating_block_video(tmp_path / "osc.mp4", period=50, frames=200)
        weight, _, _, coherence = accumulate_motion_vectors(path)
        busy = weight > np.percentile(weight[weight > 0], 90)
        assert np.median(coherence[busy]) < 0.4


class Test_the_rendered_image:
    def test_writes_an_image_the_size_of_the_video(self, moving_right, tmp_path):
        target = str(tmp_path / "history.png")
        result = musicalgestures.MgVideo(moving_right).motionvectorhistory(
            target_name=target)
        assert isinstance(result, musicalgestures.MgImage)
        import os
        assert os.path.isfile(result.filename)
        from PIL import Image
        assert Image.open(result.filename).size == (320, 240)

    def test_direction_mode_and_magnitude_mode_differ(self, moving_right, tmp_path):
        """Two renderings of the same accumulator; if they were identical the direction
        information would not be reaching the image at all."""
        from PIL import Image
        a = musicalgestures.MgVideo(moving_right).motionvectorhistory(
            mode="direction", target_name=str(tmp_path / "dir.png"))
        b = musicalgestures.MgVideo(moving_right).motionvectorhistory(
            mode="magnitude", target_name=str(tmp_path / "mag.png"))
        ia = np.asarray(Image.open(a.filename).convert("RGB"), dtype=np.int16)
        ib = np.asarray(Image.open(b.filename).convert("RGB"), dtype=np.int16)
        assert np.abs(ia - ib).mean() > 1.0

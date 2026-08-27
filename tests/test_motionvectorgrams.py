"""Motiongrams from the codec's vectors rather than from differenced pixels.

A motiongram collapses one spatial axis per frame and stacks the result over time, so a
horizontal motiongram is position-against-time and a moving body draws a diagonal in it.
That is the property tested here: a block travelling right must leave a ridge whose
position increases with time, and one travelling left must leave the mirror image. An
implementation that lost the time ordering, or that collapsed the wrong axis, would still
produce a plausible-looking image and would fail these.
"""
import numpy as np
import pytest

import musicalgestures
from _synth import moving_block_video

av = pytest.importorskip("av", reason="motion-vector data needs the optional 'av' extra")

from musicalgestures._motionvectors import motion_vector_motiongrams  # noqa: E402


@pytest.fixture(scope="module")
def moving_right(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("mvg") / "right.mp4", dx=4, dy=0,
                              frames=60)


@pytest.fixture(scope="module")
def moving_down(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("mvg") / "down.mp4", dx=0, dy=3,
                              frames=60)


def _ridge(gram, axis_len):
    """Where the motion sits in each column of the motiongram, ignoring empty columns."""
    strong = gram.sum(axis=0) > 0
    return np.array([int(np.argmax(gram[:, i])) for i in range(gram.shape[1]) if strong[i]])


class Test_the_diagonal:
    def test_rightward_travel_draws_a_ridge_that_moves_right_over_time(self, moving_right):
        horizontal, _ = motion_vector_motiongrams(moving_right)
        ridge = _ridge(horizontal, horizontal.shape[0])
        assert len(ridge) > 10
        first, last = ridge[:len(ridge) // 3], ridge[-len(ridge) // 3:]
        assert last.mean() > first.mean() + 2

    def test_downward_travel_draws_the_ridge_in_the_vertical_gram(self, moving_down):
        _, vertical = motion_vector_motiongrams(moving_down)
        ridge = _ridge(vertical, vertical.shape[0])
        assert len(ridge) > 10
        first, last = ridge[:len(ridge) // 3], ridge[-len(ridge) // 3:]
        assert last.mean() > first.mean() + 2

    def test_horizontal_travel_leaves_the_vertical_gram_stationary(self, moving_right):
        """The axis that nothing moved along must not show a drift."""
        _, vertical = motion_vector_motiongrams(moving_right)
        ridge = _ridge(vertical, vertical.shape[0])
        first, last = ridge[:len(ridge) // 3], ridge[-len(ridge) // 3:]
        assert abs(last.mean() - first.mean()) < 2


class Test_shape:
    def test_one_column_per_frame_used(self, moving_right):
        horizontal, vertical = motion_vector_motiongrams(moving_right)
        assert horizontal.shape[1] == vertical.shape[1]
        assert horizontal.shape[1] > 5

    def test_each_gram_spans_its_own_axis(self, moving_right):
        horizontal, vertical = motion_vector_motiongrams(moving_right)
        # 320x240 at a 16-pixel grid
        assert horizontal.shape[0] == 20
        assert vertical.shape[0] == 15


class Test_the_image_stays_openable:
    """One column per P-frame is right for the array and wrong for the picture.

    A 158-minute session has 77,592 P-frames, and stretching that to the video's height
    gives a 149-megapixel PNG --- 309 MB on disk, for something meant to be glanced at.
    The array keeps every column; the image is capped.
    """

    def test_a_long_recording_does_not_produce_an_enormous_image(self, moving_right,
                                                                 tmp_path):
        from PIL import Image
        result = musicalgestures.MgVideo(moving_right).motionvectorgrams(
            max_width=24, target_name=str(tmp_path / "g.png"))
        for image in result:
            assert Image.open(image.filename).size[0] <= 24

    def test_a_short_recording_is_not_stretched_up_to_the_cap(self, moving_right,
                                                             tmp_path):
        from PIL import Image
        result = musicalgestures.MgVideo(moving_right).motionvectorgrams(
            max_width=100000, target_name=str(tmp_path / "g2.png"))
        assert Image.open(result[0].filename).size[0] < 1000


class Test_the_rendered_images:
    def test_writes_two_images(self, moving_right, tmp_path):
        import os
        result = musicalgestures.MgVideo(moving_right).motionvectorgrams(
            target_name=str(tmp_path / "g.png"))
        assert isinstance(result, musicalgestures.MgList)
        assert len(result) == 2
        for image in result:
            assert isinstance(image, musicalgestures.MgImage)
            assert os.path.isfile(image.filename)

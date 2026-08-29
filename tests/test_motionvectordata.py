"""The numeric side of motion vectors: what the codec already knows about displacement.

`motionvectors()` draws the vectors. These tests are for reading them as data, which is
a different promise: a number per frame that can be correlated, thresholded and plotted
rather than looked at.

The ground truth is generated, not borrowed. A clip of somebody dancing cannot say
whether a reported displacement of 4 pixels is right, so every test here uses a block
translating by an exact amount per frame.
"""
import numpy as np
import pytest

import musicalgestures
from _synth import intra_only_video, moving_block_video

av = pytest.importorskip("av", reason="motion-vector data needs the optional 'av' extra")


@pytest.fixture(scope="module")
def moving_right(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("mv") / "right.mp4", dx=4, dy=0)


@pytest.fixture(scope="module")
def moving_left(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("mv") / "left.mp4", dx=-4, dy=0)


@pytest.fixture(scope="module")
def moving_down(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("mv") / "down.mp4", dx=0, dy=3)


class Test_displacement:
    def test_recovers_the_horizontal_displacement_it_was_given(self, moving_right):
        mv = musicalgestures.MgVideo(moving_right).motionvectordata()
        moved = mv.median_dx[mv.n_vectors > 0]
        assert np.median(moved) == pytest.approx(4, abs=1.0)

    def test_recovers_the_vertical_displacement_it_was_given(self, moving_down):
        """3 px a frame, within the spread the multi-reference residual introduces.

        The cadence part of the reference distance is corrected now --- see
        Test_reference_distance --- but a block reaching an OLDER reference through
        multi-reference prediction still over-reports, and which blocks do that is the
        encoder's choice: ffmpeg 6.1.1 emits only distance-1 references here and reads
        exactly 3.00, while CI's newer build mixes references. The tolerance covers
        that residual, not the cadence, which is asserted tightly below.
        """
        mv = musicalgestures.MgVideo(moving_down).motionvectordata()
        moved = mv.median_dy[mv.n_vectors > 0]
        assert np.median(moved) == pytest.approx(3, abs=2.0)

    def test_leftward_motion_reports_the_opposite_sign_to_rightward(self, moving_left):
        """Direction, not just distance. Without this an implementation taking the
        absolute value of every vector passes every other test in this file."""
        mv = musicalgestures.MgVideo(moving_left).motionvectordata()
        moved = mv.median_dx[mv.n_vectors > 0]
        assert np.median(moved) == pytest.approx(-4, abs=1.0)

    def test_horizontal_motion_reports_no_vertical_component(self, moving_right):
        mv = musicalgestures.MgVideo(moving_right).motionvectordata()
        moved = mv.median_dy[mv.n_vectors > 0]
        assert abs(np.median(moved)) < 1.0


class Test_shape:
    def test_one_row_per_decoded_frame(self, moving_right):
        mv = musicalgestures.MgVideo(moving_right).motionvectordata()
        assert len(mv.time) == len(mv.magnitude) == len(mv.picture_type)
        assert len(mv.time) > 1

    def test_time_is_in_seconds_and_increases(self, moving_right):
        mv = musicalgestures.MgVideo(moving_right).motionvectordata()
        assert np.all(np.diff(mv.time) > 0)
        assert mv.time[-1] == pytest.approx(len(mv.time) / 25, abs=0.2)


class Test_picture_type:
    """B-frames cost 0.3 of the correlation with quantity of motion when pooled in.

    Measured on a 100-minute corpus: r = 0.87 on P-frames alone against 0.54 pooled,
    because a B-frame's vectors point both ways over varying temporal distances and are
    not the same quantity. So the picture type is not a diagnostic here, it is what
    makes the rest usable, and it has to be on the result.
    """

    def test_picture_type_is_reported_for_every_frame(self, moving_right):
        mv = musicalgestures.MgVideo(moving_right).motionvectordata()
        assert set(mv.picture_type) <= {"I", "P", "B"}
        assert "P" in set(mv.picture_type)

    def test_intra_frames_carry_no_vectors(self, moving_right):
        mv = musicalgestures.MgVideo(moving_right).motionvectordata()
        intra = mv.picture_type == "I"
        assert intra.any()
        assert not mv.n_vectors[intra].any()


class Test_awkward_input:
    def test_an_intra_only_video_returns_empty_vectors_rather_than_failing(
            self, tmp_path):
        path = intra_only_video(tmp_path / "intra.avi")
        mv = musicalgestures.MgVideo(path).motionvectordata()
        assert len(mv.time) > 0
        assert not mv.n_vectors.any()
        assert mv.magnitude.sum() == 0


class Test_saying_so_when_there_is_nothing_to_read:
    """Silence here is indistinguishable from stillness, which is the dangerous case.

    ffmpeg exports motion vectors for H.264 and MPEG-4 Part 2 and, in this build, for
    nothing else: HEVC and VP9 decode perfectly and return zero vectors. A caller who
    gets an array of zeros back has no way to tell "nobody moved" from "this codec does
    not carry vectors", so the function has to say which it is.
    """

    def test_warns_when_no_frame_carried_a_vector(self, tmp_path):
        path = intra_only_video(tmp_path / "silent.avi")
        with pytest.warns(UserWarning, match="motion vectors"):
            musicalgestures.MgVideo(path).motionvectordata()

    def test_does_not_warn_when_vectors_are_present(self, moving_right):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            musicalgestures.MgVideo(moving_right).motionvectordata()


class Test_it_is_cheap:
    """The whole reason to prefer this over differencing pixels."""

    def test_reports_how_many_frames_carried_vectors(self, moving_right):
        mv = musicalgestures.MgVideo(moving_right).motionvectordata()
        assert 0 < int((mv.n_vectors > 0).sum()) <= len(mv.time)


class Test_reference_distance:
    """The cadence part of the reference distance is corrected, and says so in numbers.

    FFmpeg's `source` carries only the sign of the reference, so a P-frame that follows
    a run of B-frames reports its whole multi-frame displacement as if it were one
    frame's. The distance to the previous REFERENCE frame is recoverable from the
    picture-type cadence while decoding, and that is the correction under test: with a
    forced I B B P cadence and single reference, every P-frame's vectors span exactly
    3 display frames, and a block moving 2 px a frame must read 2, not 6.

    What this cannot correct, and is not tested: blocks reaching an older reference
    through multi-reference prediction (suppressed here with ref=1), and B-frame
    vectors that point at a future reference, which the toolbox excludes by default.
    """

    @pytest.fixture(scope="class")
    def cadenced(self, tmp_path_factory):
        return moving_block_video(tmp_path_factory.mktemp("mv") / "cadence.mp4",
                                  dx=2, dy=0, frames=60,
                                  x264opts="bframes=2:b-adapt=0:ref=1")

    def test_a_p_frame_after_b_frames_reports_per_frame_displacement(self, cadenced):
        mv = musicalgestures.MgVideo(cadenced).motionvectordata()
        p = (mv.picture_type == "P") & (mv.n_vectors > 0) & (mv.median_dx != 0)
        assert p.sum() > 5
        assert np.median(mv.median_dx[p]) == pytest.approx(2, abs=0.75)

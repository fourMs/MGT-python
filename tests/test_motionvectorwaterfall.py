"""A waterfall of the vector profiles: the same cascade, from displacement not silhouette."""
import numpy as np
import pytest

import musicalgestures
from tests._synth import moving_block_video

av = pytest.importorskip("av", reason="motion-vector data needs the optional 'av' extra")

from musicalgestures._motionvectors import motion_vector_profiles  # noqa: E402


@pytest.fixture(scope="module")
def moving_right(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("wf") / "right.mp4", dx=4, dy=0,
                              frames=60)


class Test_profiles:
    def test_returns_one_profile_per_requested_slice(self, moving_right):
        profiles, times = motion_vector_profiles(moving_right, n_samples=12)
        assert profiles.shape[0] == 12
        assert len(times) == 12
        assert np.all(np.diff(times) > 0)

    def test_the_peak_travels_across_the_slices(self, moving_right):
        profiles, _ = motion_vector_profiles(moving_right, n_samples=12, axis="horizontal")
        peaks = np.array([int(np.argmax(p)) for p in profiles if p.sum() > 0])
        assert len(peaks) > 6
        assert peaks[-3:].mean() > peaks[:3].mean() + 2

    def test_vertical_axis_profiles_the_other_dimension(self, moving_right):
        h, _ = motion_vector_profiles(moving_right, n_samples=8, axis="horizontal")
        v, _ = motion_vector_profiles(moving_right, n_samples=8, axis="vertical")
        assert h.shape[1] == 20
        assert v.shape[1] == 15


class Test_the_figure:
    def test_renders_a_figure(self, moving_right, tmp_path):
        import os
        result = musicalgestures.MgVideo(moving_right).motionvectorwaterfall(
            n_samples=10, target_name=str(tmp_path / "wf.png"))
        assert isinstance(result, musicalgestures.MgFigure)
        assert os.path.isfile(result.image)

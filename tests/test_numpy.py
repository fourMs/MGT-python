"""Tests for numpy array read/write and memory-based processing flow (issue #294)."""
import os
import numpy as np
import pytest
import musicalgestures
from musicalgestures._utils import extract_subclip


@pytest.fixture(scope="module")
def testvideo_avi(tmp_path_factory):
    target_name = os.path.join(str(tmp_path_factory.mktemp("data")), "testvideo.avi")
    return extract_subclip(musicalgestures.examples.dance, 5, 6, target_name=target_name)


class Test_MgVideo_numpy:
    """Tests for MgVideo.numpy() – read video frames as numpy array."""

    def test_returns_tuple(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.numpy()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_array_shape(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        array, fps = mg.numpy()
        # shape should be (N_frames, height, width, 3)
        assert array.ndim == 4
        assert array.shape[1] == mg.height
        assert array.shape[2] == mg.width
        assert array.shape[3] == 3

    def test_array_dtype(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        array, fps = mg.numpy()
        assert array.dtype == np.uint8

    def test_fps_matches(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        array, fps = mg.numpy()
        assert fps == mg.fps

    def test_frame_count(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        array, fps = mg.numpy()
        from musicalgestures._utils import get_framecount
        expected_frames = get_framecount(testvideo_avi)
        assert array.shape[0] == expected_frames


class Test_MgAudio_numpy:
    """Tests for MgAudio.numpy() – read audio as numpy array."""

    def test_returns_array(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.audio.numpy()
        assert isinstance(result, np.ndarray)

    def test_array_1d(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.audio.numpy()
        assert result.ndim == 1

    def test_sample_rate_set(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        mg.audio.numpy()
        assert mg.audio.sr > 0

    def test_array_length_matches_duration(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.audio.numpy()
        # Audio duration = n_samples / sr, should be roughly 1 second (we extracted 5-6 s)
        duration = len(result) / mg.audio.sr
        assert 0.5 < duration < 2.0


class Test_MgVideo_from_numpy:
    """Tests for creating MgVideo from a numpy array (via __init__ array parameter)."""

    def test_init_with_array_no_path(self, testvideo_avi, tmp_path):
        mg = musicalgestures.MgVideo(testvideo_avi)
        array, fps = mg.numpy()
        out_file = str(tmp_path / "from_arr.avi")
        new_mg = musicalgestures.MgVideo(
            filename=out_file,
            array=array[:30],
            fps=fps,
        )
        assert os.path.isfile(new_mg.filename)
        assert new_mg.fps == fps
        assert new_mg.width == array.shape[2]
        assert new_mg.height == array.shape[1]

    def test_init_with_array_and_path(self, testvideo_avi, tmp_path):
        mg = musicalgestures.MgVideo(testvideo_avi)
        array, fps = mg.numpy()
        new_mg = musicalgestures.MgVideo(
            filename="arr_output.avi",
            array=array[:30],
            fps=fps,
            path=str(tmp_path),
        )
        expected_path = os.path.join(str(tmp_path), "arr_output.avi")
        assert new_mg.filename == expected_path
        assert os.path.isfile(new_mg.filename)

    def test_from_numpy_direct_call(self, testvideo_avi, tmp_path):
        mg = musicalgestures.MgVideo(testvideo_avi)
        array, fps = mg.numpy()
        target = str(tmp_path / "direct.avi")
        mg.from_numpy(array[:30], fps, target_name=target)
        assert os.path.isfile(target)

    def test_roundtrip_frame_count(self, testvideo_avi, tmp_path):
        """Array written to disk should have the same number of frames."""
        mg = musicalgestures.MgVideo(testvideo_avi)
        array, fps = mg.numpy()
        n_frames = 20
        out_file = str(tmp_path / "roundtrip.avi")
        new_mg = musicalgestures.MgVideo(
            filename=out_file,
            array=array[:n_frames],
            fps=fps,
        )
        from musicalgestures._utils import get_framecount
        assert get_framecount(new_mg.filename) == n_frames


class Test_mg_grid_return_array:
    """Tests for mg_grid() memory-based flow (return_array=True)."""

    def test_return_array_type(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.grid(height=100, rows=2, cols=2, return_array=True)
        assert isinstance(result, np.ndarray)

    def test_return_array_dtype(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.grid(height=100, rows=2, cols=2, return_array=True)
        assert result.dtype == np.uint8

    def test_return_array_shape(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        rows, cols, height = 2, 3, 100
        result = mg.grid(height=height, rows=rows, cols=cols, return_array=True)
        assert result.ndim == 3
        assert result.shape[0] == height * rows
        assert result.shape[2] == 3  # RGB channels

    def test_no_file_written(self, testvideo_avi, tmp_path):
        """return_array=True should not write any file to disk."""
        mg = musicalgestures.MgVideo(testvideo_avi)
        of = os.path.splitext(testvideo_avi)[0]
        expected_file = of + "_grid.png"
        if os.path.exists(expected_file):
            os.remove(expected_file)
        mg.grid(height=100, rows=2, cols=2, return_array=True)
        assert not os.path.exists(expected_file)

    def test_return_mgimage_when_no_array(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.grid(height=100, rows=2, cols=2, return_array=False)
        assert isinstance(result, musicalgestures.MgImage)
        assert os.path.isfile(result.filename)

"""Tests for mg_info (musicalgestures._info)."""
import os
import pandas as pd
import pytest
import musicalgestures
from musicalgestures._utils import extract_subclip, get_framecount, get_length


@pytest.fixture(scope="module")
def testvideo_avi(tmp_path_factory):
    target_name = os.path.join(str(tmp_path_factory.mktemp("data")), "testvideo.avi")
    testvideo_avi = extract_subclip(
        musicalgestures.examples.dance, 5, 6, target_name=target_name)
    return testvideo_avi


class Test_info_summary:
    def test_duration_is_seconds_not_frames(self, testvideo_avi):
        # Regression: the summary used self.length (the frame *count* for an
        # MgVideo) as if it were seconds, reporting e.g. a 1 s clip as 25 s.
        mg = musicalgestures.MgVideo(testvideo_avi)
        info = mg.info("summary")
        assert isinstance(info, dict)
        real_duration = get_length(testvideo_avi)
        assert info["duration"] == pytest.approx(real_duration, abs=0.25)
        assert info["frames"] == get_framecount(testvideo_avi)
        # a ~1 s 25 fps clip: duration must not equal the frame count
        assert info["duration"] < info["frames"]

    def test_summary_fields(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        info = mg.info("summary")
        assert info["width"] == mg.width
        assert info["height"] == mg.height
        assert info["fps"] == mg.fps
        assert info["filename"] == os.path.basename(testvideo_avi)

    def test_default_returns_dataframe(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.info()
        assert isinstance(result, pd.DataFrame)

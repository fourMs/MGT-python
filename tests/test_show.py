"""Tests for MgVideo.show() key-based file resolution (musicalgestures._show).

Windowed display is stubbed out by monkeypatching show_in_new_process, so no
ffplay window is ever opened; the tests only check which file show() resolves.
"""
import os
import pytest
import musicalgestures
import musicalgestures._show
from musicalgestures._utils import extract_subclip


@pytest.fixture(scope="module")
def testvideo_avi(tmp_path_factory):
    target_name = os.path.join(str(tmp_path_factory.mktemp("data")), "testvideo.avi")
    testvideo_avi = extract_subclip(
        musicalgestures.examples.dance, 5, 6, target_name=target_name)
    return testvideo_avi


@pytest.fixture
def shown_files(monkeypatch):
    """Capture the file paths show() would have displayed."""
    captured = []

    def fake_show_in_new_process(cmd):
        # cmd is 'ffplay <file> -window_title <title> -x <w> -y <h>'
        captured.append(cmd.split(" ")[1])

    monkeypatch.setattr(
        musicalgestures._show, "show_in_new_process", fake_show_in_new_process)
    return captured


class Test_show_keys:
    def test_key_blur_resolves_blur_faces_video(self, testvideo_avi, shown_files):
        # Regression: show(key='blur') used to look up a non-existent
        # 'blur_faces' attribute (the video is stored as 'blur_faces_video')
        # and silently did nothing.
        mg = musicalgestures.MgVideo(testvideo_avi)
        mg.blur_faces_video = musicalgestures.MgVideo(testvideo_avi)
        mg.show(key="blur")
        assert len(shown_files) == 1
        assert shown_files[0] == os.path.realpath(testvideo_avi)

    def test_key_blur_without_render_raises(self, testvideo_avi, shown_files):
        mg = musicalgestures.MgVideo(testvideo_avi)
        with pytest.raises(FileNotFoundError):
            mg.show(key="blur")
        assert shown_files == []

    def test_key_subtract_resolves_subtract_video(self, testvideo_avi, shown_files):
        mg = musicalgestures.MgVideo(testvideo_avi)
        mg.subtract_video = musicalgestures.MgVideo(testvideo_avi)
        mg.show(key="subtract")
        assert len(shown_files) == 1
        assert shown_files[0] == os.path.realpath(testvideo_avi)

    def test_key_subtract_without_render_raises(self, testvideo_avi, shown_files):
        mg = musicalgestures.MgVideo(testvideo_avi)
        with pytest.raises(FileNotFoundError):
            mg.show(key="subtract")
        assert shown_files == []

    def test_no_key_shows_source(self, testvideo_avi, shown_files):
        mg = musicalgestures.MgVideo(testvideo_avi)
        mg.show()
        assert shown_files == [os.path.realpath(testvideo_avi)]

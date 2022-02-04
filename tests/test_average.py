import musicalgestures
import os
import pytest


@pytest.fixture(scope="class")
def testvideo_avi(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace(
        "\\", "/") + "/testvideo.avi"
    testvideo_avi = musicalgestures._utils.extract_subclip(
        musicalgestures.examples.dance, 5, 6, target_name=target_name)
    return testvideo_avi


@pytest.fixture(scope="class")
def testvideo_mp4(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace(
        "\\", "/") + "/testvideo.avi"
    testvideo_avi = musicalgestures._utils.extract_subclip(
        musicalgestures.examples.dance, 5, 6, target_name=target_name)
    testvideo_mp4 = musicalgestures._utils.convert_to_mp4(testvideo_avi)
    os.remove(testvideo_avi)
    return testvideo_mp4


class Test_Average:
    def test_normal_case(self):
        mg = musicalgestures.MgVideo(musicalgestures.examples.dance)
        result = mg.average()
        assert type(result) == musicalgestures._utils.MgImage
        assert os.path.isfile(result.filename) == True
        assert os.path.splitext(result.filename)[1] == ".png"

    def test_not_avi(self, testvideo_mp4):
        mg = musicalgestures.MgVideo(testvideo_mp4)
        result = mg.average()
        assert type(result) == musicalgestures._utils.MgImage
        assert os.path.isfile(result.filename) == True
        assert os.path.splitext(result.filename)[1] == ".png"

    def test_no_color(self):
        mg = musicalgestures.MgVideo(
            musicalgestures.examples.dance, color=False)
        result = mg.average()
        assert type(result) == musicalgestures._utils.MgImage
        assert os.path.isfile(result.filename) == True
        assert os.path.splitext(result.filename)[1] == ".png"

    def test_no_normalize(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.average(normalize=False)
        assert type(result) == musicalgestures._utils.MgImage
        assert os.path.isfile(result.filename) == True
        assert os.path.splitext(result.filename)[1] == ".png"

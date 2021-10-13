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


class Test_videograms:
    def test_normal_case(self, testvideo_avi):
        mg = musicalgestures.MgObject(testvideo_avi)
        result = mg.videograms()
        assert type(result) == musicalgestures.MgList
        for videogram in result:
            assert type(videogram) == musicalgestures.MgImage
            assert os.path.isfile(videogram.filename) == True

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
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.videograms()
        assert type(result) == musicalgestures.MgList
        for videogram in result:
            assert type(videogram) == musicalgestures.MgImage
            assert os.path.isfile(videogram.filename) == True

    def test_slit_mode(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        width, height = musicalgestures._utils.get_widthheight(testvideo_avi)
        framecount = musicalgestures._utils.get_framecount(testvideo_avi)
        result = mg.videograms(mode="slit", line_x=0, line_y=0)

        assert os.path.isfile(result[0].filename) == True
        assert os.path.isfile(result[1].filename) == True
        assert result[0].filename.endswith("_vgv_slit.png")
        assert result[1].filename.endswith("_vgh_slit.png")

        x_width, x_height = musicalgestures._utils.get_widthheight(result[0].filename)
        y_width, y_height = musicalgestures._utils.get_widthheight(result[1].filename)
        assert x_width == width
        assert x_height == framecount
        assert y_width == framecount
        assert y_height == height

    def test_slit_mode_validates_inputs(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        width, height = musicalgestures._utils.get_widthheight(testvideo_avi)

        with pytest.raises(ValueError):
            mg.videograms(mode="unknown")
        with pytest.raises(ValueError):
            mg.videograms(mode="slit", line_x=width)
        with pytest.raises(ValueError):
            mg.videograms(mode="slit", line_y=height)

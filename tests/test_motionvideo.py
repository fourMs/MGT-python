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


class Test_motiongrams:
    def test_normal_case(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motiongrams()
        assert type(result) == musicalgestures.MgList
        for motiongram in result:
            assert type(motiongram) == musicalgestures.MgImage
            assert os.path.isfile(motiongram.filename) == True

    def test_overwrite(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motiongrams(overwrite=True)
        assert type(result) == musicalgestures.MgList
        for motiongram in result:
            assert type(motiongram) == musicalgestures.MgImage
            assert os.path.isfile(motiongram.filename) == True


class Test_motiondata:
    def test_normal_case(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motiondata()
        assert type(result) == str
        assert os.path.isfile(result) == True

    def test_overwrite(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motiondata(overwrite=True)
        assert type(result) == str
        assert os.path.isfile(result) == True

    def test_dataformat_is_list(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motiondata(data_format=["csv", "tsv"])
        assert type(result) == list
        for result_file in result:
            assert os.path.isfile(result_file) == True
            assert type(result_file) == str

    def test_dataformat_is_list_overwrite(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motiondata(overwrite=True, data_format=["csv", "tsv"])
        assert type(result) == list
        for result_file in result:
            assert os.path.isfile(result_file) == True
            assert type(result_file) == str


class Test_motionplots:
    def test_normal_case(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motionplots()
        assert type(result) == musicalgestures.MgImage
        assert os.path.isfile(result.filename) == True

    def test_overwrite(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motionplots(overwrite=True)
        assert type(result) == musicalgestures.MgImage
        assert os.path.isfile(result.filename) == True


class Test_motionvideo:
    def test_normal_case(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motionvideo()
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True


class Test_motion:
    def test_normal_case(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion()
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_not_avi(self, testvideo_mp4):
        mg = musicalgestures.MgVideo(testvideo_mp4)
        result = mg.motion()
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_with_target_name_video(self, testvideo_avi):
        target_name_video = os.path.dirname(testvideo_avi) + "/result.avi"
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(target_name_video=target_name_video)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_no_color(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi, color=False)
        result = mg.motion()
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_blur_average(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(blur="average")
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_filtertype_binary(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(filtertype="binary")
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_filtertype_blob(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(filtertype="blob")
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_inverted_motionvideo(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(inverted_motionvideo=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_inverted_motiongram(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(inverted_motiongram=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_nothing(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(save_data=False, save_motiongrams=False,
                           save_plot=False, save_video=False)
        assert type(result) == musicalgestures.MgVideo
        assert result == mg

    def test_unit_samples(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(unit="samples")
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_data_format_tsv(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(data_format="tsv")
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_data_format_txt(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(data_format="txt")
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_data_format_txt_target_name_data(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(data_format="txt", target_name_data=os.path.dirname(
            testvideo_avi)+"/test.txt")
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_data_format_xyz(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(data_format="xyz")
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_data_format_list_xyz(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.motion(data_format=["xyz", "csv", "txt"])
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

import musicalgestures
from musicalgestures._audio import *
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
def testvideo_avi_silent(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace(
        "\\", "/") + "/testvideo.avi"
    target_name_silent = str(tmp_path_factory.mktemp("data")).replace(
        "\\", "/") + "/testvideo_silent.avi"
    testvideo_avi = musicalgestures._utils.extract_subclip(
        musicalgestures.examples.dance, 5, 6, target_name=target_name)
    cmd = ["ffmpeg", "-y", "-i", target_name, "-an", target_name_silent]
    musicalgestures._utils.ffmpeg_cmd(
        cmd, get_length(testvideo_avi), stream=False)
    return target_name_silent


class Test_Audio:
    def test_init(self):
        my_audio = MgAudio("testfile.avi")
        assert my_audio.filename == "testfile.avi"
        assert my_audio.of == "testfile"
        assert my_audio.fex == ".avi"


class Test_Audio_Waveform:
    def test_waveform_no_audio(self, testvideo_avi_silent):
        assert musicalgestures.MgVideo(testvideo_avi_silent).waveform() == None

    def test_target_name_is_none(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).waveform(target_name=None)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.waveform"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = musicalgestures.MgVideo(
            testvideo_avi).audio.waveform(target_name=target_name)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.waveform"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = musicalgestures.MgVideo(
            testvideo_avi).audio.waveform(autoshow=False)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.waveform"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"


class Test_Waveform:
    def test_waveform_no_file(self):
        assert waveform() == None

    def test_waveform_no_audio(self, testvideo_avi_silent):
        assert waveform(filename=testvideo_avi_silent) == None

    def test_target_name_is_none(self, testvideo_avi):
        result = waveform(filename=testvideo_avi, target_name=None)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.waveform"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = waveform(
            filename=testvideo_avi, target_name=target_name)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.waveform"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = waveform(filename=testvideo_avi, autoshow=False)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.waveform"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"


class Test_Audio_Spectrogram:
    def test_spectrogram_no_audio(self, testvideo_avi_silent):
        assert musicalgestures.MgVideo(testvideo_avi_silent).spectrogram() == None

    def test_target_name_is_none(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).spectrogram(target_name=None)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.spectrogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = musicalgestures.MgVideo(testvideo_avi).spectrogram(target_name=target_name)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.spectrogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).spectrogram(autoshow=False)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.spectrogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"


class Test_Spectrogram:
    def test_spectrogram_no_file(self):
        assert spectrogram() == None

    def test_spectrogram_no_audio(self, testvideo_avi_silent):
        assert spectrogram(filename=testvideo_avi_silent) == None

    def test_target_name_is_none(self, testvideo_avi):
        result = spectrogram(filename=testvideo_avi, target_name=None)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.spectrogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = spectrogram(
            filename=testvideo_avi, target_name=target_name)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.spectrogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = spectrogram(filename=testvideo_avi, autoshow=False)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.spectrogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"


class Test_Audio_Descriptors:
    def test_descriptors_no_audio(self, testvideo_avi_silent):
        assert musicalgestures.MgVideo(testvideo_avi_silent).descriptors() is None

    def test_target_name_is_none(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).descriptors(target_name=None)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.descriptors"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = musicalgestures.MgVideo(testvideo_avi).descriptors(target_name=target_name)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.descriptors"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).descriptors(autoshow=False)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.descriptors"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"


class Test_Descriptors:
    def test_descriptors_no_file(self):
        assert descriptors() == None

    def test_descriptors_no_audio(self, testvideo_avi_silent):
        assert descriptors(filename=testvideo_avi_silent) is None

    def test_target_name_is_none(self, testvideo_avi):
        result = descriptors(filename=testvideo_avi, target_name=None)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.descriptors"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = descriptors(
            filename=testvideo_avi, target_name=target_name)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.descriptors"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = descriptors(filename=testvideo_avi, autoshow=False)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.descriptors"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"


class Test_Audio_Tempogram:
    def test_tempogram_no_audio(self, testvideo_avi_silent):
        assert musicalgestures.MgVideo(testvideo_avi_silent).tempogram() == None

    def test_target_name_is_none(self, testvideo_avi):
        result = musicalgestures.MgVideo(
            testvideo_avi).tempogram(target_name=None)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.tempogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = musicalgestures.MgVideo(
            testvideo_avi).tempogram(target_name=target_name)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.tempogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = musicalgestures.MgVideo(
            testvideo_avi).tempogram(autoshow=False)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.tempogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"


class Test_Tempogram:
    def test_tempogram_no_file(self):
        assert tempogram() == None

    def test_tempogram_no_audio(self, testvideo_avi_silent):
        assert tempogram(filename=testvideo_avi_silent) == None

    def test_target_name_is_none(self, testvideo_avi):
        result = tempogram(filename=testvideo_avi, target_name=None)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.tempogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = tempogram(
            filename=testvideo_avi, target_name=target_name)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.tempogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = tempogram(filename=testvideo_avi, autoshow=False)
        assert type(result) == musicalgestures._utils.MgFigure
        assert result.figure_type == "audio.tempogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

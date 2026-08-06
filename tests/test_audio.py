import os
import pytest
import musicalgestures
from musicalgestures._utils import MgFigure, get_length, extract_subclip


@pytest.fixture(scope="class")
def testvideo_avi(tmp_path_factory):
    target_name = os.path.join(str(tmp_path_factory.mktemp("data")), "testvideo.avi")
    print(target_name)
    testvideo_avi = extract_subclip(musicalgestures.examples.dance, 5, 6, target_name=target_name)
    return testvideo_avi

@pytest.fixture(scope="class")
def testvideo_avi_silent(tmp_path_factory):
    target_name = os.path.join(str(tmp_path_factory.mktemp("data")), "testvideo.avi")
    target_name_silent = os.path.join(str(tmp_path_factory.mktemp("data")), "testvideo_silent.avi")
    testvideo_avi = extract_subclip(musicalgestures.examples.dance, 5, 6, target_name=target_name)
    cmd = ["ffmpeg", "-y", "-i", target_name, "-an", target_name_silent]
    musicalgestures._utils.ffmpeg_cmd(cmd, get_length(testvideo_avi), stream=False)
    return target_name_silent


class Test_Audio:
    def test_init(self, testvideo_avi):
        my_audio = musicalgestures.MgAudio(testvideo_avi)
        assert os.path.basename(my_audio.filename) == "testvideo.avi"
        # assert my_audio.of == "testvideo"
        # assert my_audio.fex == ".avi"
    def test_no_audio(self, testvideo_avi_silent):
        assert musicalgestures.MgVideo(testvideo_avi_silent).audio is None

    def test_mgvideo_inherited_audio_method(self, testvideo_avi):
        # Regression: audio methods called directly on an MgVideo (which inherits them
        # but does not set the _y_cache attribute) must still work.
        result = musicalgestures.MgVideo(testvideo_avi).spectrogram(autoshow=False, overwrite=True)
        assert isinstance(result, MgFigure)

class Test_Audio_Waveform:
    def test_target_name_is_none(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).audio.waveform(target_name=None)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.waveform"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = musicalgestures.MgVideo(testvideo_avi).audio.waveform(target_name=target_name)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.waveform"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).audio.waveform(autoshow=False)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.waveform"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

class Test_Audio_Spectrogram:
    def test_target_name_is_none(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).audio.spectrogram(target_name=None)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.spectrogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = musicalgestures.MgVideo(testvideo_avi).audio.spectrogram(target_name=target_name)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.spectrogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).audio.spectrogram(autoshow=False)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.spectrogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

class Test_Audio_Descriptors:
    def test_target_name_is_none(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).audio.descriptors(target_name=None)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.descriptors"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = musicalgestures.MgVideo(testvideo_avi).audio.descriptors(target_name=target_name)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.descriptors"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = musicalgestures.MgVideo(testvideo_avi).audio.descriptors(autoshow=False)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.descriptors"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

class Test_Audio_Tempogram:
    def test_target_name_is_none(self, testvideo_avi):
        result = musicalgestures.MgVideo(
            testvideo_avi).audio.tempogram(target_name=None)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.tempogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

    def test_target_name(self, testvideo_avi):
        tmp_folder = os.path.dirname(testvideo_avi)
        target_name = tmp_folder + "/result.png"
        result = musicalgestures.MgVideo(
            testvideo_avi).audio.tempogram(target_name=target_name)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.tempogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"
        assert target_name == result.image

    def test_target_no_autoshow(self, testvideo_avi):
        result = musicalgestures.MgVideo(
            testvideo_avi).audio.tempogram(autoshow=False)
        assert type(result) == MgFigure
        assert result.figure_type == "audio.tempogram"
        assert os.path.isfile(result.image) == True
        assert os.path.splitext(result.image)[1] == ".png"

class Test_Audio_Autoshow:
    # Regression: the `autoshow` parameter on the MgAudio figure methods used
    # to be accepted but never acted on.

    def test_autoshow_inert_outside_notebook(self, testvideo_avi, monkeypatch):
        calls = []
        monkeypatch.setattr(MgFigure, "show", lambda self, **kw: calls.append(1))
        result = musicalgestures.MgVideo(testvideo_avi).audio.waveform(autoshow=True)
        assert type(result) == MgFigure
        assert calls == []

    def test_autoshow_displays_in_notebook(self, testvideo_avi, monkeypatch):
        calls = []
        monkeypatch.setattr(MgFigure, "show", lambda self, **kw: calls.append(1))
        monkeypatch.setattr(musicalgestures._utils, "in_ipynb", lambda: True)
        audio = musicalgestures.MgVideo(testvideo_avi).audio
        result = audio.waveform(autoshow=True)
        assert type(result) == MgFigure
        assert calls == [1]
        audio.spectrogram(autoshow=True)
        assert calls == [1, 1]
        audio.spectrogram(autoshow=False)
        assert calls == [1, 1]

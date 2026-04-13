import musicalgestures
import os
import pytest


@pytest.fixture(scope="class")
def testvideo_avi(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace("\\", "/") + "/testvideo.avi"
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


class Test_flow_dense:
    def test_normal_case(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.dense()
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_overwrite(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.dense(overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_not_avi(self, testvideo_mp4):
        mg = musicalgestures.MgVideo(testvideo_mp4)
        result = mg.flow.dense()
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_skip_empty(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.dense(skip_empty=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_with_target_name(self, testvideo_avi):
        target_name = os.path.dirname(testvideo_avi) + "/result_dense.avi"
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.dense(target_name=target_name, overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True


class Test_flow_sparse:
    def test_normal_case(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.sparse()
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_overwrite(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.sparse(overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_not_avi(self, testvideo_mp4):
        mg = musicalgestures.MgVideo(testvideo_mp4)
        result = mg.flow.sparse()
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_with_target_name(self, testvideo_avi):
        target_name = os.path.dirname(testvideo_avi) + "/result_sparse.avi"
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.sparse(target_name=target_name, overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

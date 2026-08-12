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

    def test_use_gpu_true(self, testvideo_avi):
        # use_gpu=True should work (falls back to CPU when CUDA is unavailable)
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.dense(use_gpu=True, overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_use_gpu_false(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.dense(use_gpu=False, overwrite=True)
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

    def test_use_gpu_true(self, testvideo_avi):
        # use_gpu=True should work (falls back to CPU when CUDA is unavailable)
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.sparse(use_gpu=True, overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_use_gpu_false(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.flow.sparse(use_gpu=False, overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True


class Test_get_cuda_device_count:
    def test_returns_int(self):
        result = musicalgestures.get_cuda_device_count()
        assert isinstance(result, int)
        assert result >= 0


class Test_blur_faces_gpu:
    def test_use_gpu_false(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.blur_faces(use_gpu=False, overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_use_gpu_true(self, testvideo_avi):
        # use_gpu=True should work (falls back to CPU when CUDA is unavailable)
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.blur_faces(use_gpu=True, overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True


class Test_pose_gpu:
    """Device selection on the OpenPose path.

    Skipped where OpenCV cannot load a Caffe model. Without MediaPipe
    installed `pose()` uses the OpenPose BODY_25 backend, and OpenCV 5.0
    removed the Caffe importer those models need --- so on such a build there
    is no OpenPose device to select and the thing under test does not exist.
    These two failed with a bare `AttributeError` on OpenCV 5 before the guard
    in `_pose` was added, which is what made the incompatibility look like a
    fault in the pose code rather than in the environment.
    """

    @staticmethod
    def _skip_without_openpose():
        from musicalgestures._pose import caffe_supported
        if not caffe_supported():
            pytest.skip("OpenCV has no Caffe importer; the OpenPose backends "
                        "cannot run on this build (OpenCV 5.0 removed it)")

    def test_device_cpu(self, testvideo_avi):
        self._skip_without_openpose()
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.pose(device='cpu', overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

    def test_device_gpu_fallback(self, testvideo_avi):
        # device='gpu' should fall back to CPU when CUDA is unavailable
        self._skip_without_openpose()
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.pose(device='gpu', overwrite=True)
        assert type(result) == musicalgestures.MgVideo
        assert os.path.isfile(result.filename) == True

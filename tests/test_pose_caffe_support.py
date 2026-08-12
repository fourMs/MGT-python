"""The OpenPose backends need a Caffe importer, and OpenCV 5.0 removed it.

`cv2.dnn.readNetFromCaffe` is gone in OpenCV 5, and `readNet` raises on the
format rather than falling back, so BODY_25, COCO and MPI cannot run there at
all. On such a build `pose()` used to fail with

    AttributeError: module 'cv2.dnn' has no attribute 'readNetFromCaffe'

raised from deep inside the run, *after* offering to download 200 MB of
weights the environment could never load. These tests pin the two things that
fix: the failure names its cause and its remedies, and it happens before any
download is attempted.

They run on either OpenCV, patching the capability check rather than the
library, so the OpenCV 4 machines that can load Caffe still exercise the path
the OpenCV 5 machines take.
"""
import cv2
import pytest

from musicalgestures import _pose
from musicalgestures._exceptions import MgDependencyError


def test_capability_matches_the_library():
    """The probe must report what this build can actually do."""
    assert _pose.caffe_supported() == hasattr(cv2.dnn, "readNetFromCaffe")


def test_supported_build_passes_through(monkeypatch):
    monkeypatch.setattr(_pose, "caffe_supported", lambda: True)
    _pose._require_caffe_support()          # must not raise


def test_unsupported_build_names_cause_and_remedies(monkeypatch):
    """A message a user can act on, not a stack trace about an attribute."""
    monkeypatch.setattr(_pose, "caffe_supported", lambda: False)
    with pytest.raises(MgDependencyError) as e:
        _pose._require_caffe_support()
    msg = str(e.value)
    assert "Caffe" in msg
    assert "mediapipe" in msg               # the other backend
    assert "opencv-python<5" in msg         # or keep the skeletons
    for model in ("body_25", "coco", "mpi"):
        assert model in msg
    # The landmark sets differ, so the two backends are not a silent swap.
    assert "not interchangeable" in msg


def test_check_precedes_any_download(monkeypatch, tmp_path):
    """The 200 MB prompt must not be reached on a build that cannot use it.

    `download_model` is replaced with a fuse: if the check were placed after
    the weights lookup, as it was, this would blow rather than the dependency
    error being raised.
    """
    monkeypatch.setattr(_pose, "caffe_supported", lambda: False)

    def fuse(*a, **k):                                        # pragma: no cover
        raise AssertionError("download attempted on an unusable build")

    if hasattr(_pose, "download_model"):
        monkeypatch.setattr(_pose, "download_model", fuse)

    class FakeVideo:
        filename = str(tmp_path / "nothing.mp4")
        color = True

    with pytest.raises(MgDependencyError):
        _pose.pose(FakeVideo(), model="body_25", device="cpu")


def test_missing_mediapipe_does_not_fall_back_into_a_wall(monkeypatch, tmp_path):
    """The fallback assumed OpenCV could always load Caffe. It cannot.

    Asking for the default backend without MediaPipe installed used to print
    "falling back to the OpenPose 'body_25' backend" and then fail on that
    backend, because on OpenCV 5 there is nowhere to fall back to. The message
    must name the one thing that would work instead of advertising a route
    that is closed.
    """
    monkeypatch.setattr(_pose, "caffe_supported", lambda: False)
    monkeypatch.setattr(_pose, "_mediapipe_available", lambda: False)

    class FakeVideo:
        filename = str(tmp_path / "nothing.mp4")
        color = True

    with pytest.raises(MgDependencyError) as e:
        _pose.pose(FakeVideo(), model="mediapipe", device="cpu")
    assert "musicalgestures[pose]" in str(e.value)


def test_mediapipe_still_runs_where_it_is_installed(monkeypatch, tmp_path):
    """A guard one block too early would have taken the working backend too.

    MediaPipe carries its own weights and never touches `cv2.dnn`, so with it
    available the Caffe check must not be reached at all, whatever else then
    goes wrong on a file that is not a video.
    """
    monkeypatch.setattr(_pose, "caffe_supported", lambda: False)
    monkeypatch.setattr(_pose, "_mediapipe_available", lambda: True)

    class FakeVideo:
        filename = str(tmp_path / "nothing.mp4")
        color = True

    try:
        _pose.pose(FakeVideo(), model="mediapipe", device="cpu")
    except Exception as e:                          # unreadable file, fine
        assert "Caffe" not in str(e), f"MediaPipe hit the Caffe guard: {e}"

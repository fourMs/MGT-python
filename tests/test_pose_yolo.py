"""The YOLO twin of extract_pose_landmarks: same contract, 17 COCO keypoints.

The point of the twin (issue #359) is detector agreement: two detectors, one
trajectory-array contract, so the anchor_and_match tooling can compare them on a
shared clock. These tests hold the twin to that contract on the bundled dancer.
"""
import os

import numpy as np
import pytest

import musicalgestures
from musicalgestures._posetools import COCO_KEYPOINT_NAMES, extract_pose_landmarks_yolo

EXAMPLE_VIDEO = os.path.join(
    os.path.dirname(musicalgestures.__file__), "examples", "dancer.avi")


def _yolo_available():
    try:
        import ultralytics  # noqa: F401
        return True
    except ImportError:
        return False


class TestValidation:
    """Argument errors arrive before the optional import, so they cost nothing."""

    def test_negative_t0_is_refused(self):
        with pytest.raises(ValueError, match="t0"):
            extract_pose_landmarks_yolo("nope.mp4", t0=-1.0)

    def test_nonpositive_duration_is_refused(self):
        with pytest.raises(ValueError, match="duration"):
            extract_pose_landmarks_yolo("nope.mp4", duration=0.0)


class TestNames:
    def test_the_coco_topology_is_seventeen_named_points(self):
        assert len(COCO_KEYPOINT_NAMES) == 17
        assert COCO_KEYPOINT_NAMES[0] == "nose"
        assert "left_wrist" in COCO_KEYPOINT_NAMES


@pytest.mark.skipif(not _yolo_available(), reason="ultralytics not installed")
@pytest.mark.skipif(not os.path.exists(EXAMPLE_VIDEO), reason="example video missing")
class TestOnTheDancer:
    """Integration on the bundled dancer: a real human, plainly visible."""

    @pytest.fixture(scope="class")
    def result(self, tmp_path_factory):
        csv_path = str(tmp_path_factory.mktemp("yolo") / "dancer_yolo.csv")
        return extract_pose_landmarks_yolo(
            EXAMPLE_VIDEO, fps=6.0, width=320, max_frames=12,
            target_name=csv_path, verbose=False), csv_path

    def test_the_contract_matches_the_mediapipe_twin(self, result):
        r, _ = result
        f = len(r["time"])
        assert r["landmarks"].shape == (f, 17, 3)
        assert r["detected"].shape == (f,)
        assert r["names"] == list(COCO_KEYPOINT_NAMES)
        assert r["width"] == 320
        assert 0.0 <= r["detection_rate"] <= 1.0

    def test_the_dancer_is_found(self, result):
        r, _ = result
        assert r["detection_rate"] >= 0.5

    def test_timestamps_run_at_the_analysis_rate(self, result):
        r, _ = result
        t = r["time"]
        assert t[0] == 0.0
        assert np.allclose(np.diff(t), 1.0 / 6.0)

    def test_the_csv_lands_with_named_columns(self, result):
        _, csv_path = result
        head = open(csv_path).readline().strip().split(",")
        assert head[0] == "time"
        assert "nose_x" in head and "left_wrist_v" in head

    def test_undetected_frames_are_nan_rows(self, result):
        r, _ = result
        if (~r["detected"]).any():
            assert np.isnan(r["landmarks"][~r["detected"]]).all()
        else:
            first = r["landmarks"][0]
            assert np.isfinite(first[:, :2]).any()

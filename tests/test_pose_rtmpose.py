"""The RTMPose backend: the Apache-licensed second family, same twin contract.

ARJ's flexibility decision keeps both pose families in the toolbox. RTMPose rides
rtmlib (ONNX runtime, no MMPose stack) and emits the same 17-point COCO topology
as the YOLO twin, so the detector-agreement tooling covers all three extractors.
"""
import os

import numpy as np
import pytest

import musicalgestures
from musicalgestures._posetools import (COCO_KEYPOINT_NAMES,
                                        extract_pose_landmarks_rtmpose)

EXAMPLE_VIDEO = os.path.join(
    os.path.dirname(musicalgestures.__file__), "examples", "dancer.avi")


def _rtmlib_available():
    try:
        import rtmlib  # noqa: F401
        return True
    except ImportError:
        return False


class TestValidation:
    def test_negative_t0_is_refused(self):
        with pytest.raises(ValueError, match="t0"):
            extract_pose_landmarks_rtmpose("nope.mp4", t0=-1.0)

    def test_nonpositive_duration_is_refused(self):
        with pytest.raises(ValueError, match="duration"):
            extract_pose_landmarks_rtmpose("nope.mp4", duration=0.0)


@pytest.mark.skipif(not _rtmlib_available(), reason="rtmlib not installed")
@pytest.mark.skipif(not os.path.exists(EXAMPLE_VIDEO), reason="example video missing")
class TestOnTheDancer:
    @pytest.fixture(scope="class")
    def result(self, tmp_path_factory):
        csv_path = str(tmp_path_factory.mktemp("rtm") / "dancer_rtm.csv")
        return extract_pose_landmarks_rtmpose(
            EXAMPLE_VIDEO, fps=6.0, width=320, max_frames=12,
            target_name=csv_path, verbose=False), csv_path

    def test_the_contract_matches_the_twins(self, result):
        r, _ = result
        f = len(r["time"])
        assert r["landmarks"].shape == (f, 17, 3)
        assert r["names"] == list(COCO_KEYPOINT_NAMES)
        assert r["world"] is None
        assert 0.0 <= r["detection_rate"] <= 1.0

    def test_the_dancer_is_found(self, result):
        r, _ = result
        assert r["detection_rate"] >= 0.5

    def test_timestamps_run_at_the_analysis_rate(self, result):
        r, _ = result
        assert r["time"][0] == 0.0
        assert np.allclose(np.diff(r["time"]), 1.0 / 6.0)

    def test_the_csv_lands_with_named_columns(self, result):
        _, csv_path = result
        head = open(csv_path).readline().strip().split(",")
        assert head[0] == "time" and "nose_x" in head

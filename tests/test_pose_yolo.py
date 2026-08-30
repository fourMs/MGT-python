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


@pytest.mark.skipif(not _yolo_available(), reason="ultralytics not installed")
@pytest.mark.skipif(not os.path.exists(EXAMPLE_VIDEO), reason="example video missing")
class TestTracking:
    """Identity persistence: the cure for the top-confidence person flipping.

    Measured on the corpus, per-frame top-confidence selection teleports the
    trajectory whenever two bodies are in frame --- two real dancers, or a dancer
    and their projected partner. Tracking follows one identity instead.
    """

    def test_tracked_extraction_keeps_the_twin_contract(self):
        from musicalgestures._posetools import extract_pose_landmarks_yolo

        r = extract_pose_landmarks_yolo(EXAMPLE_VIDEO, fps=6.0, width=320,
                                        max_frames=12, track=True, verbose=False)
        f = len(r["time"])
        assert r["landmarks"].shape == (f, 17, 3)
        assert r["detection_rate"] >= 0.5
        assert r["names"] == list(COCO_KEYPOINT_NAMES)

    def test_every_identity_is_returned_separately(self):
        from musicalgestures._posetools import extract_pose_tracks_yolo

        tracks = extract_pose_tracks_yolo(EXAMPLE_VIDEO, fps=6.0, width=320,
                                          max_frames=12, verbose=False)
        assert len(tracks["tracks"]) >= 1
        tid, tr = max(tracks["tracks"].items(), key=lambda kv: len(kv[1]["time"]))
        assert tr["landmarks"].shape == (len(tr["time"]), 17, 3)
        #: The dancer is alone in the example, so one identity carries the video.
        assert len(tr["time"]) >= 0.5 * tracks["n_frames"]
        assert tracks["fps"] == 6.0


class TestSkeletonTimeline:
    """A timeline of stick figures: posture at moments, on a real time axis."""

    def test_figures_are_drawn_at_the_asked_moments(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from musicalgestures._posetools import skeleton_timeline

        f = 100
        lm = np.full((f, 17, 3), np.nan)
        #: A standing figure that raises one arm over the sequence.
        base = np.array([[0, 0], [-1, -1], [1, -1], [-2, -1], [2, -1],
                         [-4, 4], [4, 4], [-6, 8], [6, 8], [-7, 12], [7, 12],
                         [-3, 14], [3, 14], [-3, 20], [3, 20], [-3, 26], [3, 26]],
                        dtype=float) * 4 + np.array([160, 60])
        for i in range(f):
            p = base.copy()
            p[9, 1] -= i * 0.5          # left wrist rises
            lm[i, :, :2] = p
            lm[i, :, 2] = 0.9
        lm[40:44] = np.nan              # a dropout is skipped, not drawn
        times = np.arange(f) / 10.0

        fig, ax = plt.subplots()
        n = skeleton_timeline(lm, times, ax=ax, n_figures=8)
        assert n == 8
        assert len(ax.lines) >= 8 * 10   # a skeleton is many bone segments
        plt.close(fig)

    def test_no_detections_draws_nothing(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from musicalgestures._posetools import skeleton_timeline

        lm = np.full((50, 17, 3), np.nan)
        fig, ax = plt.subplots()
        n = skeleton_timeline(lm, np.arange(50) / 10.0, ax=ax, n_figures=6)
        assert n == 0
        plt.close(fig)

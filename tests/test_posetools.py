"""Tests for musicalgestures._posetools (landmark-trajectory pose tools).

The numpy-only helpers (midpoint, limb_speed_from_landmarks, impact_events)
are tested against synthetic trajectories with known ground truth and always
run. extract_pose_landmarks needs MediaPipe (optional dependency) plus a real
human video, so it is an integration test that skips when either is missing.
"""

import os
import subprocess
import sys

import numpy as np
import pytest

import musicalgestures
from musicalgestures._posetools import (
    extract_pose_landmarks,
    midpoint,
    limb_speed_from_landmarks,
    impact_events,
    _pick_relative_peaks,
)


def _gaussian_bump(n, center, sigma, amplitude):
    t = np.arange(n, dtype=float)
    return amplitude * np.exp(-0.5 * ((t - center) / sigma) ** 2)


def _position_from_accel(accel, fps):
    """Double-integrate a 1-D acceleration signal into a position signal."""
    vel = np.cumsum(accel) / fps
    return np.cumsum(vel) / fps


# ---------------------------------------------------------------------------
# midpoint
# ---------------------------------------------------------------------------

class TestMidpoint:
    def test_basic(self):
        a = np.array([[0.0, 0.0], [2.0, 2.0]])
        b = np.array([[2.0, 4.0], [4.0, 6.0]])
        np.testing.assert_allclose(midpoint(a, b), [[1.0, 2.0], [3.0, 4.0]])

    def test_nan_propagates(self):
        a = np.array([[0.0, np.nan], [2.0, 2.0]])
        b = np.array([[2.0, 4.0], [4.0, 6.0]])
        m = midpoint(a, b)
        assert np.isnan(m[0, 1])
        np.testing.assert_allclose(m[1], [3.0, 4.0])

    def test_shoulder_midpoint_from_landmark_array(self):
        # (F, 33, 3) landmark array as returned by extract_pose_landmarks
        lm = np.zeros((4, 33, 3))
        lm[:, 11, :2] = [100.0, 50.0]   # left shoulder
        lm[:, 12, :2] = [200.0, 70.0]   # right shoulder
        m = midpoint(lm[:, 11, :2], lm[:, 12, :2])
        np.testing.assert_allclose(m, np.tile([150.0, 60.0], (4, 1)))


# ---------------------------------------------------------------------------
# limb_speed_from_landmarks
# ---------------------------------------------------------------------------

class TestLimbSpeed:
    def test_constant_velocity_speed(self):
        # One limb moving at (3, 4) px/frame at 50 fps -> speed 5 px/frame = 250 px/s
        fps = 50.0
        t = np.arange(100, dtype=float)
        xy = np.stack([3.0 * t, 4.0 * t], axis=1)
        conf = np.ones(100)
        speed = limb_speed_from_landmarks(xy, conf, fps)
        assert speed.shape == (100,)
        np.testing.assert_allclose(speed, 250.0)

    def test_confidence_gate_masks_frames(self):
        fps = 50.0
        t = np.arange(100, dtype=float)
        xy = np.stack([3.0 * t, 4.0 * t], axis=1)
        conf = np.ones(100)
        conf[40:51] = 0.2  # below the default 0.5 gate
        speed = limb_speed_from_landmarks(xy, conf, fps)
        assert np.isnan(speed[45])
        # away from the gated region (and its central-difference/smoothing
        # neighbourhood) the speed is intact
        np.testing.assert_allclose(speed[5:35], 250.0)
        np.testing.assert_allclose(speed[60:95], 250.0)

    def test_bilateral_max_merge(self):
        # Left limb moves at 5 px/frame in the first half, right limb at
        # 10 px/frame in the second half; merged speed tracks the faster limb.
        fps = 30.0
        n = 120
        left = np.zeros((n, 2))
        right = np.zeros((n, 2))
        left[:60, 0] = 5.0 * np.arange(60)
        left[60:, 0] = left[59, 0]
        right[:60] = 0.0
        right[60:, 1] = 10.0 * np.arange(60)
        xy = np.stack([left, right], axis=1)          # (F, 2, 2)
        conf = np.ones((n, 2))
        merged = limb_speed_from_landmarks(xy, conf, fps, smooth_taps=0)
        per_limb = limb_speed_from_landmarks(xy, conf, fps, merge=None, smooth_taps=0)
        assert per_limb.shape == (n, 2)
        # interior of each half: merged = max of the two limbs
        np.testing.assert_allclose(merged[10:50], 5.0 * fps)
        np.testing.assert_allclose(merged[70:110], 10.0 * fps)
        np.testing.assert_allclose(merged, np.nanmax(per_limb, axis=1))

    def test_speed_peak_location(self):
        # Velocity is a Gaussian bump centred at frame 100: the speed peak
        # must sit at the bump centre.
        fps = 60.0
        n = 200
        vel = _gaussian_bump(n, center=100, sigma=6.0, amplitude=8.0)  # px/frame
        xy = np.stack([np.cumsum(vel), np.zeros(n)], axis=1)
        speed = limb_speed_from_landmarks(xy, np.ones(n), fps)
        assert abs(int(np.nanargmax(speed)) - 100) <= 1
        # peak speed close to the designed maximum (px/frame * fps)
        assert speed[np.nanargmax(speed)] == pytest.approx(8.0 * fps, rel=0.05)

    def test_no_confidence_given(self):
        fps = 25.0
        t = np.arange(50, dtype=float)
        xy = np.stack([2.0 * t, 0.0 * t], axis=1)
        speed = limb_speed_from_landmarks(xy, None, fps)
        np.testing.assert_allclose(speed, 50.0)

    def test_all_limbs_gated_gives_nan(self):
        xy = np.zeros((20, 2, 2))
        conf = np.zeros((20, 2))
        speed = limb_speed_from_landmarks(xy, conf, 30.0)
        assert speed.shape == (20,)
        assert np.isnan(speed).all()

    def test_bad_shapes_raise(self):
        with pytest.raises(ValueError):
            limb_speed_from_landmarks(np.zeros((10, 3)), None, 30.0)
        with pytest.raises(ValueError):
            limb_speed_from_landmarks(np.zeros((10, 2, 2)), np.ones((9, 2)), 30.0)
        with pytest.raises(ValueError):
            limb_speed_from_landmarks(np.zeros((10, 2)), None, 30.0, merge="mean")


# ---------------------------------------------------------------------------
# impact_events
# ---------------------------------------------------------------------------

class TestImpactEvents:
    fps = 120.0

    def _pos_from_bumps(self, n, bumps):
        """1-point 2-D position whose x-acceleration has Gaussian bumps.

        bumps: list of (center_index, amplitude).
        """
        accel = np.zeros(n)
        for c, a in bumps:
            accel += _gaussian_bump(n, c, sigma=2.0, amplitude=a)
        x = _position_from_accel(accel, self.fps)
        return np.stack([x, np.zeros(n)], axis=1)  # (F, 2)

    def test_detects_known_impacts(self):
        pos = self._pos_from_bumps(600, [(100, 10.0), (250, 6.0), (400, 4.0)])
        ev = impact_events(pos, self.fps)
        assert len(ev["index"]) == 3
        for found, expected in zip(ev["index"], (100, 250, 400)):
            assert abs(found - expected) <= 2
        np.testing.assert_allclose(ev["time"], ev["index"] / self.fps)
        assert len(ev["accel"]) == 600
        # strongest impact carries the largest magnitude
        assert np.argmax(ev["magnitude"]) == 0

    def test_bilateral_max_across_points(self):
        # A strike by either hand registers: one bump per point.
        left = self._pos_from_bumps(600, [(150, 8.0)])
        right = self._pos_from_bumps(600, [(350, 8.0)])
        pos = np.stack([left, right], axis=1)  # (F, 2, 2)
        ev = impact_events(pos, self.fps)
        assert len(ev["index"]) == 2
        assert abs(ev["index"][0] - 150) <= 2
        assert abs(ev["index"][1] - 350) <= 2

    def test_relative_threshold_excludes_weak_peaks(self):
        pos = self._pos_from_bumps(600, [(100, 10.0), (300, 0.5)])  # 5% of max
        ev = impact_events(pos, self.fps, rel_thresh=0.12)
        assert len(ev["index"]) == 1
        assert abs(ev["index"][0] - 100) <= 2
        # a permissive threshold keeps the weak one too
        ev2 = impact_events(pos, self.fps, rel_thresh=0.02)
        assert len(ev2["index"]) == 2

    def test_min_interval_keeps_stronger_peak(self):
        # Two impacts 6 samples (50 ms) apart; min_interval 100 ms keeps only
        # the stronger.
        pos = self._pos_from_bumps(600, [(200, 10.0), (206, 6.0)])
        ev = impact_events(pos, self.fps, min_interval_s=0.10)
        close = [i for i in ev["index"] if 190 <= i <= 216]
        assert len(close) == 1
        assert abs(close[0] - 200) <= 2
        # with a permissive interval both survive
        ev2 = impact_events(pos, self.fps, min_interval_s=0.02)
        close2 = [i for i in ev2["index"] if 190 <= i <= 216]
        assert len(close2) == 2

    def test_3d_positions(self):
        n = 600
        accel = _gaussian_bump(n, 300, sigma=2.0, amplitude=9.0)
        x = _position_from_accel(accel, self.fps)
        pos = np.stack([x, x, x], axis=1)[:, None, :]  # (F, 1, 3)
        ev = impact_events(pos, self.fps)
        assert len(ev["index"]) == 1
        assert abs(ev["index"][0] - 300) <= 2

    def test_nan_dropout_region(self):
        pos = self._pos_from_bumps(600, [(100, 10.0), (400, 8.0)])
        pos[200:250] = np.nan
        ev = impact_events(pos, self.fps)
        found = sorted(ev["index"])
        assert any(abs(i - 100) <= 2 for i in found)
        assert any(abs(i - 400) <= 2 for i in found)
        assert not any(200 <= i < 250 for i in found)

    def test_empty_and_flat_signals(self):
        ev = impact_events(np.zeros((2, 2)), self.fps)
        assert len(ev["index"]) == 0
        ev = impact_events(np.ones((100, 2)), self.fps)  # no motion at all
        assert len(ev["index"]) == 0

    def test_bad_shape_raises(self):
        with pytest.raises(ValueError):
            impact_events(np.zeros((10, 2, 2, 2)), self.fps)


class TestPickRelativePeaks:
    def test_plateau_and_order(self):
        s = np.array([0.0, 1.0, 1.0, 0.0, 5.0, 0.0, 2.0, 0.0])
        idx = _pick_relative_peaks(s, rel_thresh=0.1, min_dist=1)
        assert list(idx) == [1, 4, 6]  # plateau picked once, ascending order

    def test_nan_never_a_peak(self):
        s = np.array([0.0, np.nan, 0.0, 3.0, 0.0])
        idx = _pick_relative_peaks(s, rel_thresh=0.1, min_dist=1)
        assert list(idx) == [3]


# ---------------------------------------------------------------------------
# extract_pose_landmarks
# ---------------------------------------------------------------------------

def test_import_safe_without_mediapipe():
    """The package (and the numpy-only helpers) must work without mediapipe,
    and extract_pose_landmarks must raise a clear ImportError naming the
    [pose] extra."""
    code = "\n".join([
        "import sys",
        "sys.modules['mediapipe'] = None  # simulate mediapipe not installed",
        "import numpy as np",
        "import musicalgestures",
        "m = musicalgestures.midpoint(np.array([0.0, 0.0]), np.array([2.0, 4.0]))",
        "assert m.tolist() == [1.0, 2.0]",
        "try:",
        "    musicalgestures.extract_pose_landmarks('does_not_matter.mp4')",
        "except ImportError as exc:",
        "    assert 'musicalgestures[pose]' in str(exc), str(exc)",
        "else:",
        "    raise AssertionError('expected ImportError without mediapipe')",
        "print('IMPORT_SAFE_OK')",
    ])
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "IMPORT_SAFE_OK" in out.stdout


def test_invalid_model_complexity_raises():
    """model_complexity must be 0, 1 or 2; validated up front so both the
    Solutions and Tasks backends behave identically (and mediapipe need not
    be installed for this to raise)."""
    with pytest.raises(ValueError):
        extract_pose_landmarks("does_not_matter.mp4", model_complexity=3)


def _mediapipe_available():
    try:
        import mediapipe  # noqa: F401
        return True
    except Exception:
        return False


EXAMPLE_VIDEO = os.path.join(
    os.path.dirname(musicalgestures.__file__), "examples", "dancer.avi")


@pytest.mark.skipif(not _mediapipe_available(), reason="mediapipe not installed")
@pytest.mark.skipif(not os.path.exists(EXAMPLE_VIDEO), reason="example video missing")
def test_extract_pose_landmarks_integration(tmp_path):
    """Integration test on the bundled dancer example video (real human
    motion). Skips when the MediaPipe model file cannot be obtained."""
    from musicalgestures._exceptions import MgDependencyError

    csv_path = str(tmp_path / "dancer_landmarks.csv")
    try:
        res = extract_pose_landmarks(
            EXAMPLE_VIDEO, fps=5, width=320, world_landmarks=True,
            max_frames=15, target_name=csv_path, verbose=False)
    except MgDependencyError as exc:  # model download failed (offline)
        pytest.skip(f"MediaPipe model unavailable: {exc}")

    n = len(res["time"])
    assert 0 < n <= 15
    assert res["landmarks"].shape == (n, 33, 3)
    assert res["world"].shape == (n, 33, 3)
    assert res["detected"].shape == (n,)
    assert res["width"] == 320
    assert res["fps"] == 5
    assert len(res["names"]) == 33
    # the dancer is plainly visible: expect a solid detection rate
    assert res["detection_rate"] > 0.5
    # detected frames have finite pixel coordinates within the analysis frame,
    # undetected frames are all-NaN
    det = res["detected"]
    assert np.isfinite(res["landmarks"][det][:, :, :2]).all()
    if (~det).any():
        assert np.isnan(res["landmarks"][~det]).all()
    x = res["landmarks"][det][:, :, 0]
    assert (x > -res["width"]).all() and (x < 2 * res["width"]).all()
    # timestamps follow the analysis rate
    np.testing.assert_allclose(np.diff(res["time"]), 1.0 / 5.0)
    # tidy CSV written with one column per landmark coordinate
    assert os.path.exists(csv_path)
    with open(csv_path) as fh:
        header = fh.readline().strip().split(",")
    assert header[0] == "time"
    assert "left_wrist_x" in header and "left_wrist_v" in header
    assert "left_wrist_wz" in header  # world landmarks requested
    assert len(header) == 1 + 33 * 3 + 33 * 3

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


# ---------------------------------------------------------------------------
# extract_pose_landmarks windowing (t0/duration)


def test_t0_duration_validation():
    """Invalid windows are rejected before mediapipe is even imported."""
    with pytest.raises(ValueError):
        extract_pose_landmarks("does_not_matter.mp4", t0=-1.0)
    with pytest.raises(ValueError):
        extract_pose_landmarks("does_not_matter.mp4", duration=0)
    with pytest.raises(ValueError):
        extract_pose_landmarks("does_not_matter.mp4", duration=-2.5)


@pytest.mark.skipif(not _mediapipe_available(), reason="mediapipe not installed")
@pytest.mark.skipif(not os.path.exists(EXAMPLE_VIDEO), reason="example video missing")
def test_extract_pose_landmarks_windowed():
    """t0/duration cut the analysis window and keep source-clock timestamps."""
    from musicalgestures._exceptions import MgDependencyError

    try:
        res = extract_pose_landmarks(
            EXAMPLE_VIDEO, fps=5, width=256, t0=1.0, duration=1.0,
            verbose=False)
    except MgDependencyError as exc:  # model download failed (offline)
        pytest.skip(f"MediaPipe model unavailable: {exc}")

    n = len(res["time"])
    # a 1 s window at 5 fps: about 5 frames
    assert 4 <= n <= 6
    assert res["time"][0] == pytest.approx(1.0)
    assert res["time"][-1] <= 1.0 + 1.0 + 1.0 / 5
    assert res["landmarks"].shape == (n, 33, 3)


# ---------------------------------------------------------------------------
# get_pose_model_path (shared MediaPipe model download/cache)


def test_get_pose_model_path_cache(tmp_path, monkeypatch):
    """The public helper caches the model file and downloads it only once."""
    import urllib.request
    from musicalgestures._pose_estimator import get_pose_model_path

    downloads = []

    def fake_urlretrieve(url, path):
        downloads.append(url)
        with open(path, "wb") as f:
            f.write(b"fake model")

    monkeypatch.setattr(urllib.request, "urlretrieve", fake_urlretrieve)

    path1 = get_pose_model_path(1, models_dir=tmp_path)
    assert path1.name == "pose_landmarker_full.task"
    assert path1.parent == tmp_path
    assert path1.exists()
    assert len(downloads) == 1

    # second call: cached, no new download
    path2 = get_pose_model_path(1, models_dir=tmp_path)
    assert path2 == path1
    assert len(downloads) == 1

    # invalid complexity falls back to 1 (the full model), so it is cached too
    path3 = get_pose_model_path(7, models_dir=tmp_path)
    assert path3 == path1
    assert len(downloads) == 1

    # a different complexity is a different (cached) file
    path4 = get_pose_model_path(0, models_dir=tmp_path)
    assert path4.name == "pose_landmarker_lite.task"
    assert len(downloads) == 2


# ---------------------------------------------------------------------------
# fuse_pose_views
# ---------------------------------------------------------------------------


def _rotation(axis, degrees):
    """Right-handed rotation matrix about a unit axis, for building views."""
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)
    th = np.radians(degrees)
    K = np.array([[0.0, -axis[2], axis[1]],
                  [axis[2], 0.0, -axis[0]],
                  [-axis[1], axis[0], 0.0]])
    return np.eye(3) + np.sin(th) * K + (1.0 - np.cos(th)) * (K @ K)


def _synthetic_skeleton(frames=120, landmarks=33, seed=0):
    """A moving 33-landmark skeleton: a fixed pose plus a slow global sway.

    Landmarks 11/12/23/24 (shoulders and hips) are placed as a genuinely rigid
    torso, because those are the ones the alignment is estimated from.
    """
    rng = np.random.default_rng(seed)
    base = rng.normal(scale=0.30, size=(landmarks, 3))
    base[11] = [-0.20, 0.55, 0.0]      # left shoulder
    base[12] = [0.20, 0.55, 0.0]       # right shoulder
    base[23] = [-0.15, 0.0, 0.0]       # left hip
    base[24] = [0.15, 0.0, 0.0]        # right hip

    t = np.arange(frames) / 25.0
    sway = np.stack([0.05 * np.sin(2 * np.pi * 0.3 * t),
                     0.02 * np.sin(2 * np.pi * 0.2 * t),
                     0.03 * np.cos(2 * np.pi * 0.25 * t)], axis=-1)
    return base[None, :, :] + sway[:, None, :]


def _views_from(truth, transforms):
    """Turn one ground-truth skeleton into per-view (world, visibility) pairs."""
    views = []
    for R, scale in transforms:
        world = np.einsum("ij,fkj->fki", R, truth) * scale
        vis = np.ones(truth.shape[:2])
        views.append((world, vis))
    return views


def test_fuse_pose_views_recovers_a_known_skeleton_from_rotated_views():
    """Three rigidly transformed views of one skeleton fuse back to that skeleton."""
    from musicalgestures._posetools import fuse_pose_views

    truth = _synthetic_skeleton()
    views = _views_from(truth, [
        (np.eye(3), 1.0),                          # the reference view
        (_rotation([0, 1, 0], 35.0), 1.4),         # rotated and larger
        (_rotation([0, 1, 0], -50.0), 0.7),        # rotated the other way, smaller
    ])

    out = fuse_pose_views(views, smooth=None)

    assert out["fused"].shape == truth.shape
    np.testing.assert_allclose(out["fused"], truth, atol=1e-6)
    assert out["residual_mm"] < 1e-3


def test_mean_rotation_never_returns_a_reflection():
    """Averaging rotations can land on a reflection; the fix is to reject it.

    The three 180-degree rotations about x, y and z average to
    diag(-1/3, -1/3, -1/3), whose determinant is negative. Projecting that
    with a bare SVD gives an orthogonal matrix with det -1 -- a mirror, which
    would silently swap the skeleton's left and right.
    """
    from musicalgestures._posetools import _mean_rotation

    rots = [np.diag([1.0, -1.0, -1.0]),
            np.diag([-1.0, 1.0, -1.0]),
            np.diag([-1.0, -1.0, 1.0])]
    assert np.linalg.det(np.mean(rots, axis=0)) < 0     # the trap is real

    R = _mean_rotation(rots)

    assert np.linalg.det(R) == pytest.approx(1.0)
    np.testing.assert_allclose(R @ R.T, np.eye(3), atol=1e-12)


def test_umeyama_returns_a_rotation_for_a_degenerate_torso():
    """Collinear points give a rank-deficient fit; it must still be a rotation."""
    from musicalgestures._posetools import _umeyama

    src = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                    [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
    dst = src[::-1].copy()

    R, scale = _umeyama(src, dst)

    assert np.linalg.det(R) == pytest.approx(1.0, abs=1e-9)
    assert scale > 0


def test_fuse_pose_views_ignores_a_landmark_a_view_cannot_see():
    """A landmark at visibility 0 must not drag the fused position towards it."""
    from musicalgestures._posetools import fuse_pose_views

    truth = _synthetic_skeleton(frames=60)
    good = (truth.copy(), np.ones(truth.shape[:2]))
    blind = truth.copy()
    blind[:, 7, :] += 5.0                      # a wildly wrong landmark ...
    blind_vis = np.ones(truth.shape[:2])
    blind_vis[:, 7] = 0.0                      # ... that this view cannot see
    second = (truth.copy(), np.ones(truth.shape[:2]))

    out = fuse_pose_views([good, (blind, blind_vis), second], smooth=None)

    np.testing.assert_allclose(out["fused"][:, 7, :], truth[:, 7, :], atol=1e-6)


def test_fuse_pose_views_leaves_a_long_dropout_as_nan_when_max_gap_is_set():
    """A repair longer than max_gap must stay NaN rather than pass for a measurement."""
    from musicalgestures._posetools import fuse_pose_views

    truth = _synthetic_skeleton(frames=120)
    views = []
    for _ in range(3):
        world = truth.copy()
        world[40:80, 5, :] = np.nan            # a 40-frame dropout in every view
        world[90:93, 6, :] = np.nan            # a 3-frame one, short enough to fill
        views.append((world, np.ones(truth.shape[:2])))

    out = fuse_pose_views(views, smooth=None, max_gap=10)

    assert np.all(np.isnan(out["fused"][40:80, 5, :]))
    assert np.all(np.isfinite(out["fused"][90:93, 6, :]))


def test_fuse_pose_views_accepts_extract_pose_landmarks_results():
    """The obvious producer's result dict is a valid view, visibility included."""
    from musicalgestures._posetools import fuse_pose_views

    truth = _synthetic_skeleton(frames=60)
    R = _rotation([0, 1, 0], 20.0)

    def as_result(world):
        landmarks = np.zeros((world.shape[0], world.shape[1], 3))
        landmarks[..., 2] = 1.0                # visibility column
        return {"world": world, "landmarks": landmarks}

    out = fuse_pose_views(
        {"side": as_result(truth.copy()),
         "above": as_result(np.einsum("ij,fkj->fki", R, truth) * 1.2)},
        reference="side", smooth=None)

    np.testing.assert_allclose(out["fused"], truth, atol=1e-6)
    assert out["names"] == ["side", "above"]


def test_fuse_pose_views_refuses_a_single_view():
    from musicalgestures._posetools import fuse_pose_views

    truth = _synthetic_skeleton(frames=10)
    with pytest.raises(ValueError, match="at least two views"):
        fuse_pose_views([(truth, np.ones(truth.shape[:2]))])


def test_fuse_pose_views_says_so_when_a_view_has_no_world_landmarks():
    from musicalgestures._posetools import fuse_pose_views

    truth = _synthetic_skeleton(frames=10)
    ok = {"world": truth, "landmarks": np.ones((10, 33, 3))}
    with pytest.raises(ValueError, match="world_landmarks=True"):
        fuse_pose_views([ok, {"landmarks": np.ones((10, 33, 3))}])

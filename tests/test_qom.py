"""Tests for musicalgestures._qom (band-limited QoM, normalisation, grid QoM).

All ground truth is synthetic: sinusoidal trajectories with known band
content and analytically known speeds, a simulated 2x camera zoom, and a
moving spot on a synthetic frame stack.
"""
import numpy as np
import pytest

from musicalgestures import (
    band_limited_qom,
    accel_to_speed,
    group_qom,
    pose_qom,
    body_scale,
    normalized_qom,
    grid_qom,
    envelope,
    bin_series,
)


def circular_motion(fs=100.0, dur=30.0, f=1.0, radius=10.0):
    """Circular trajectory: constant speed 2*pi*f*radius, all energy at f Hz."""
    t = np.arange(int(dur * fs)) / fs
    return np.column_stack([radius * np.cos(2 * np.pi * f * t),
                            radius * np.sin(2 * np.pi * f * t)]), t


class TestBandLimitedQom:
    def test_in_band_speed_close_to_truth(self):
        fs = 100.0
        pos, _ = circular_motion(fs, f=1.0, radius=10.0)
        speed, fs_out = band_limited_qom(pos, fs, lo=0.3, hi=15.0)
        assert fs_out == fs
        true_speed = 2 * np.pi * 1.0 * 10.0
        mid = speed[len(speed) // 4: -len(speed) // 4]
        assert np.median(mid) == pytest.approx(true_speed, rel=0.05)

    def test_out_of_band_motion_rejected(self):
        fs = 100.0
        pos_slow, _ = circular_motion(fs, f=0.05, radius=10.0)   # below lo
        pos_in, _ = circular_motion(fs, f=1.0, radius=10.0)
        s_slow, _ = band_limited_qom(pos_slow, fs, lo=0.3, hi=5.0,
                                     auto_decimate=False)
        s_in, _ = band_limited_qom(pos_in, fs, lo=0.3, hi=5.0)
        assert s_slow.mean() < 0.05 * s_in.mean()

    def test_low_band_uses_decimation(self):
        fs = 100.0
        pos, _ = circular_motion(fs, dur=60.0, f=0.3, radius=10.0)
        speed, fs_out = band_limited_qom(pos, fs, lo=0.1, hi=0.5)
        assert fs_out < fs                      # decimated regime
        true_speed = 2 * np.pi * 0.3 * 10.0
        mid = speed[len(speed) // 4: -len(speed) // 4]
        assert np.median(mid) == pytest.approx(true_speed, rel=0.1)

    def test_nan_interpolation(self):
        fs = 100.0
        pos, _ = circular_motion(fs)
        pos[200:205] = np.nan
        speed, _ = band_limited_qom(pos, fs)
        assert len(speed) == len(pos) - 1
        assert np.isfinite(speed).all()

    def test_too_short_input(self):
        speed, fs_out = band_limited_qom(np.zeros((10, 2)), 100.0)
        assert len(speed) == 0


class TestAccelToSpeed:
    def test_recovers_sinusoidal_speed(self):
        # Position x(t) = A sin(2 pi f t) => acceleration is its second
        # derivative; the integrated speed magnitude should peak near
        # A * 2 pi f.
        fs = 256.0
        f, A = 1.0, 0.05
        t = np.arange(int(60 * fs)) / fs
        w = 2 * np.pi * f
        acc = np.column_stack([-A * w ** 2 * np.sin(w * t),
                               np.zeros_like(t), np.zeros_like(t)])
        speed = accel_to_speed(acc, fs)
        mid = speed[len(speed) // 4: -len(speed) // 4]
        assert np.max(mid) == pytest.approx(A * w, rel=0.1)

    def test_gravity_normalisation(self):
        fs = 256.0
        t = np.arange(int(30 * fs)) / fs
        counts_per_g = 340.0
        w = 2 * np.pi * 1.0
        A = 0.05
        # raw counts: gravity on z plus motion on x
        acc = np.column_stack([
            -A * w ** 2 * np.sin(w * t) / 9.80665 * counts_per_g,
            np.zeros_like(t),
            counts_per_g * np.ones_like(t)])
        speed = accel_to_speed(acc, fs, normalize_gravity=True)
        mid = speed[len(speed) // 4: -len(speed) // 4]
        assert np.max(mid) == pytest.approx(A * w, rel=0.15)


class TestGroupAndPoseQom:
    def test_group_mean_of_identical_markers(self):
        fs = 50.0
        pos, _ = circular_motion(fs, f=0.7)
        points = np.stack([pos, pos, pos], axis=1)
        qom, speed, fs_out = group_qom(points, fs, lo=0.3, hi=5.0)
        single, _ = band_limited_qom(pos, fs, lo=0.3, hi=5.0)
        assert qom == pytest.approx(single.mean(), rel=1e-6)
        assert np.allclose(speed, single[: len(speed)])

    def test_pose_qom_single_landmark(self):
        fs = 25.0
        pos, _ = circular_motion(fs, f=0.7)
        qom, speed, _ = pose_qom(pos, fs)
        assert np.isfinite(qom) and qom > 0


class TestBodyScaleNormalisation:
    def make_person(self, fs=25.0, dur=30.0, scale=1.0, f=0.6):
        """A minimal MediaPipe-indexed skeleton with oscillating wrists."""
        t = np.arange(int(dur * fs)) / fs
        L = 33
        lm = np.zeros((len(t), L, 2))
        lm[:, 11] = [100, 100]
        lm[:, 12] = [140, 100]
        lm[:, 23] = [105, 200]
        lm[:, 24] = [135, 200]
        wrist = 30 * np.sin(2 * np.pi * f * t)
        lm[:, 15, 0] = 80 + wrist
        lm[:, 15, 1] = 150
        lm[:, 16, 0] = 160 - wrist
        lm[:, 16, 1] = 150
        return lm * scale

    def test_body_scale_torso_length(self):
        lm = self.make_person()
        # torso: shoulder-mid (120, 100) to hip-mid (120, 200) => 100 px
        assert body_scale(lm) == pytest.approx(100.0)

    def test_zoom_invariance(self):
        """A simulated 2x camera zoom must not change the normalised QoM."""
        fs = 25.0
        lm1 = self.make_person(fs, scale=1.0)
        lm2 = self.make_person(fs, scale=2.0)
        q1, _, _ = normalized_qom(lm1, fs)
        q2, _, _ = normalized_qom(lm2, fs)
        raw1, _, _ = pose_qom(lm1, fs)
        raw2, _, _ = pose_qom(lm2, fs)
        assert raw2 == pytest.approx(2 * raw1, rel=1e-6)   # raw QoM scales
        assert q2 == pytest.approx(q1, rel=1e-6)           # normalised is invariant


class TestGridQom:
    def test_moving_spot_lights_up_its_cell(self):
        T, H, W = 40, 40, 60
        frames = np.zeros((T, H, W), dtype=np.float32)
        # A flickering spot inside cell (row 0, col 0) region
        frames[::2, 2:8, 2:8] = 200.0
        series, heat = grid_qom(frames, grid=(6, 4), threshold=8.0)
        assert series.shape == (T - 1, 24)
        assert heat.shape == (4, 6)
        assert np.argmax(heat) == 0
        assert heat[0, 0] > 10 * (heat.sum() - heat[0, 0] + 1e-9)

    def test_region_of_interest(self):
        T, H, W = 10, 40, 60
        frames = np.zeros((T, H, W), dtype=np.float32)
        frames[::2, :H // 2, :] = 100.0     # motion only in the top half
        _, heat_bottom = grid_qom(frames, grid=(2, 2), region=(0, 1, 0.5, 1))
        assert heat_bottom.max() == 0


class TestEnvelopeBinSeries:
    def test_envelope_zscored(self):
        fs = 25.0
        x = np.sin(2 * np.pi * 0.2 * np.arange(int(20 * fs)) / fs)
        e = envelope(x, fs)
        assert len(e) == len(x)
        assert abs(e.mean()) < 1e-6
        assert e.std() == pytest.approx(1.0, rel=1e-3)

    def test_bin_series_means(self):
        fs = 10.0
        x = np.repeat([1.0, 2.0, 3.0], int(fs))
        b = bin_series(x, fs, bin_s=1.0)
        assert np.allclose(b, [1.0, 2.0, 3.0])
        assert len(bin_series(np.ones(5), fs)) == 0

"""360 directional analysis: anglegram, AEM overlay, projection detection.

All fixtures are synthetic: a moving white block on an equirectangular
canvas, written with ffmpeg. Ground truth is the block's azimuth, so the
tests prove that the anglegram localises visual motion at the correct
azimuth under both azimuth conventions.
"""
import os
import shutil
import subprocess

import numpy as np
import pytest

import musicalgestures
from musicalgestures import Mg360Video, anglegram_data, load_aem
from musicalgestures._360video import Projection, detect_projection

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None,
                                reason="ffmpeg not on PATH")

W, H, FPS, DUR = 320, 160, 10, 2.0


def block_frames(az_deg_image, T=20, w=W, h=H):
    """Grayscale equirect frames (T, h, w) with a block bobbing vertically
    at a fixed image azimuth (degrees, -180 left edge .. +180 right)."""
    frames = np.zeros((T, h, w), dtype=np.float32)
    col = int((az_deg_image + 180.0) / 360.0 * w)
    for i in range(T):
        r = h // 2 + (8 if i % 2 else -8)
        frames[i, r - 10:r + 10, col - 8:col + 8] = 255.0
    return frames


@pytest.fixture(scope="module")
def equirect_video(tmp_path_factory):
    """A 2:1 mp4 with a block bobbing at image azimuth +90 (right of center),
    written losslessly enough (high bitrate) to keep the block localised."""
    folder = tmp_path_factory.mktemp("data360")
    raw = str(folder / "eq_raw.mp4")
    frames = block_frames(90.0, T=int(FPS * DUR))
    cmd = ["ffmpeg", "-y", "-v", "error", "-s", f"{W}x{H}", "-r", str(FPS),
           "-f", "rawvideo", "-pix_fmt", "gray", "-i", "-",
           "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", raw]
    p = subprocess.run(cmd, input=frames.astype(np.uint8).tobytes())
    assert p.returncode == 0
    return raw


class TestAnglegramData:
    def test_localises_block_ambisonic(self):
        frames = block_frames(90.0)          # image right => ambisonic -90
        gram, az = anglegram_data(frames, n_bins=36)
        assert gram.shape == (36, 19)
        assert az[0] < az[-1]
        peak_az = az[gram.sum(axis=1).argmax()]
        assert abs(peak_az - (-90.0)) <= 10.0

    def test_localises_block_image_convention(self):
        frames = block_frames(90.0)
        gram, az = anglegram_data(frames, n_bins=36,
                                  azimuth_convention="image")
        peak_az = az[gram.sum(axis=1).argmax()]
        assert abs(peak_az - 90.0) <= 10.0

    def test_full_resolution_and_normalization(self):
        frames = block_frames(0.0)
        gram, az = anglegram_data(frames)
        assert gram.shape == (W, 19)
        assert gram.max() == pytest.approx(1.0)

    def test_latitude_weighting_downweights_poles(self):
        # same block at the equator vs at the pole: with weighting on, the
        # polar block contributes less energy
        eq = np.zeros((3, H, W), np.float32)
        po = np.zeros((3, H, W), np.float32)
        eq[1, H // 2 - 5:H // 2 + 5, 150:170] = 255.0
        po[1, 0:10, 150:170] = 255.0
        g_eq, _ = anglegram_data(eq, normalize=False)
        g_po, _ = anglegram_data(po, normalize=False)
        assert g_po.sum() < 0.5 * g_eq.sum()

    def test_bad_input_raises(self):
        with pytest.raises(ValueError):
            anglegram_data(np.zeros((5, 5)))
        with pytest.raises(ValueError):
            anglegram_data(block_frames(0.0), azimuth_convention="compass")


class TestDetectProjection:
    def test_two_to_one_is_equirect(self, equirect_video):
        assert detect_projection(equirect_video) == Projection.equirect

    def test_square_video_is_unknown(self, tmp_path):
        out = str(tmp_path / "sq.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                        "color=red:s=64x64:d=0.5:r=10", "-pix_fmt", "yuv420p",
                        out], check=True)
        assert detect_projection(out) is None
        with pytest.raises(ValueError, match="Could not detect"):
            Mg360Video(out)

    def test_auto_detection_in_constructor(self, equirect_video):
        v = Mg360Video(equirect_video)   # no projection argument
        assert v.projection == Projection.equirect


class TestMgAnglegram:
    def test_figure_and_peak_azimuth(self, equirect_video):
        v = Mg360Video(equirect_video, Projection.equirect)
        mgf = v.anglegram(n_bins=36)
        assert type(mgf) == musicalgestures.MgFigure
        assert mgf.figure_type == 'video.anglegram'
        assert os.path.isfile(mgf.image)
        gram, az = mgf.data['anglegram'], mgf.data['azimuth']
        assert gram.shape[0] == 36
        # image azimuth +90 => ambisonic -90
        peak_az = az[gram.sum(axis=1).argmax()]
        assert abs(peak_az - (-90.0)) <= 10.0

    def test_requires_equirect(self, equirect_video):
        v = Mg360Video(equirect_video, Projection.equirect)
        v.projection = Projection.fisheye
        with pytest.raises(ValueError, match="equirect"):
            v.anglegram()


class TestLoadAem:
    def _write(self, path, text):
        with open(path, "w") as f:
            f.write(text)
        return str(path)

    def test_tsv_with_aliases(self, tmp_path):
        f = self._write(tmp_path / "aem.tsv",
                        "t\taz\tlevel\n0.5\t-90\t1.0\n1.5\t45\t0.25\n")
        aem = load_aem(f)
        assert np.allclose(aem["time"], [0.5, 1.5])
        assert np.allclose(aem["azimuth"], [-90, 45])
        assert np.allclose(aem["energy"], [1.0, 0.25])

    def test_csv_with_db_conversion(self, tmp_path):
        f = self._write(tmp_path / "aem.csv",
                        "Time,Azimuth_deg,level_db\n0,0,-10\n1,90,0\n")
        aem = load_aem(f)
        assert np.allclose(aem["energy"], [0.1, 1.0])

    def test_missing_column_raises(self, tmp_path):
        f = self._write(tmp_path / "bad.csv", "time,foo\n0,1\n")
        with pytest.raises(ValueError, match="azimuth"):
            load_aem(f)


class TestAemOverlay:
    @pytest.fixture()
    def aem_file(self, tmp_path):
        # audio energy at ambisonic azimuth -90 throughout (matching the
        # block at image azimuth +90)
        rows = ["time\tazimuth\tenergy"]
        for t in np.arange(0, DUR, 0.5):
            rows.append(f"{t}\t-90\t1.0")
            rows.append(f"{t}\t100\t0.2")
        f = tmp_path / "aem.tsv"
        f.write_text("\n".join(rows) + "\n")
        return str(f)

    def test_overlay_on_anglegram(self, equirect_video, aem_file):
        v = Mg360Video(equirect_video, Projection.equirect)
        mgf = v.aem_overlay(aem_file, on='anglegram')
        assert type(mgf) == musicalgestures.MgFigure
        assert mgf.figure_type == 'video.anglegram_aem'
        assert os.path.isfile(mgf.image)
        assert mgf.data['aem'].shape[0] == 72

    def test_overlay_on_video(self, equirect_video, aem_file):
        v = Mg360Video(equirect_video, Projection.equirect)
        out = v.aem_overlay(aem_file, on='video', strip_height=0.2)
        assert type(out) == musicalgestures.MgVideo
        assert os.path.isfile(out.filename)
        # the strip region must differ from the source; above it, not much
        import cv2
        src, ov = cv2.VideoCapture(equirect_video), cv2.VideoCapture(out.filename)
        _, fs = src.read()
        _, fo = ov.read()
        src.release(), ov.release()
        strip = slice(int(H * 0.8) + 2, H)
        # the audio hotspot (ambisonic -90 => image +90 => x ~ 3W/4) is
        # painted over the (black) source strip; the quiet side (x = W/4,
        # ambisonic +90, no energy) stays close to the source
        hot_x = slice(3 * W // 4 - 2, 3 * W // 4 + 2)
        cold_x = slice(W // 4 - 2, W // 4 + 2)
        d_hot = np.abs(fs[strip, hot_x].astype(int)
                       - fo[strip, hot_x].astype(int)).mean()
        d_cold = np.abs(fs[strip, cold_x].astype(int)
                        - fo[strip, cold_x].astype(int)).mean()
        assert d_hot > 30
        assert d_hot > 3 * max(d_cold, 1.0)
        assert fo[strip, hot_x].mean() > fo[strip, cold_x].mean()

    def test_bad_on_raises(self, equirect_video, aem_file):
        v = Mg360Video(equirect_video, Projection.equirect)
        with pytest.raises(ValueError, match="on must be"):
            v.aem_overlay(aem_file, on='sphere')


class TestView:
    def test_perspective_crop(self, equirect_video):
        v = Mg360Video(equirect_video, Projection.equirect)
        out = v.view(yaw=90, h_fov=90, v_fov=60, width=64, height=48)
        assert type(out) == musicalgestures.MgVideo
        assert os.path.isfile(out.filename)
        assert (out.width, out.height) == (64, 48)

"""Dual-fisheye stitching: mask, calibration, and a synthetic round trip."""
import os
import subprocess

import numpy as np
import pytest

from musicalgestures._360video import (Mg360Video, Projection,
                                       calibrate_dual_fisheye_fov,
                                       make_seam_mask, stitch_dual_fisheye)

FOV = 195  # ground-truth lens FOV used to synthesize the fisheye pair


def test_make_seam_mask():
    m = make_seam_mask(720, 360, feather_deg=8.0)
    assert m.shape == (360, 720) and m.dtype == np.uint8
    assert m[0, 360] == 0          # front centre (lon 0) -> front lens
    assert m[0, 5] == 255          # lon ~-180 -> back lens
    assert m[0, 715] == 255        # lon ~+180 -> back lens
    seam = m[0, 180]               # lon -90: mid-blend
    assert 100 < seam < 156


@pytest.fixture(scope="module")
def fisheye_pair(tmp_path_factory):
    """A synthetic equirect scene projected into two fisheye lens videos."""
    import cv2

    folder = tmp_path_factory.mktemp("fisheye")
    w, h = 768, 384
    # structured scene: gradient + grid + circles, so seams are measurable
    x, y = np.meshgrid(np.arange(w), np.arange(h))
    img = (128 + 60 * np.sin(x / 17.0) + 50 * np.cos(y / 11.0))
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for cx in range(40, w, 120):
        cv2.circle(img, (cx, h // 2 + (cx % 90) - 45), 24,
                   (40, 200, 240), -1)
    src = str(folder / "equirect_src.png")
    cv2.imwrite(src, img)
    scene = str(folder / "scene.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", src,
                    "-t", "2", "-r", "10", "-c:v", "libx264", "-pix_fmt",
                    "yuv420p", scene], check=True)
    pair = {}
    for name, yaw in (("front", 0), ("back", 180)):
        out = str(folder / f"{name}.mp4")
        vf = (f"v360=input=e:output=fisheye:h_fov={FOV}:v_fov={FOV}"
              f":yaw={yaw}:w=384:h=384")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", scene, "-vf",
                        vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", out],
                       check=True)
        pair[name] = out
    return {"src": src, **pair}


def test_calibrate_recovers_fov(fisheye_pair):
    fov = calibrate_dual_fisheye_fov(fisheye_pair["front"],
                                     fisheye_pair["back"],
                                     time_s=0.5,
                                     candidates=[185, 190, 195, 200])
    assert fov == FOV


def test_stitch_round_trip(fisheye_pair, tmp_path):
    import cv2

    out = stitch_dual_fisheye(fisheye_pair["front"], fisheye_pair["back"],
                              target_name=str(tmp_path / "stitched.mp4"),
                              fov=FOV, width=768, height=384)
    assert os.path.isfile(out)
    frame_png = str(tmp_path / "frame.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.5", "-i", out,
                    "-frames:v", "1", frame_png], check=True)
    got = cv2.imread(frame_png, cv2.IMREAD_GRAYSCALE).astype(float)
    ref = cv2.imread(fisheye_pair["src"], cv2.IMREAD_GRAYSCALE).astype(float)
    assert got.shape == ref.shape
    # compare away from the poles (top/bottom quarter distort most)
    band = slice(ref.shape[0] // 4, 3 * ref.shape[0] // 4)
    corr = np.corrcoef(got[band].ravel(), ref[band].ravel())[0, 1]
    assert corr > 0.9


def test_from_dual_fisheye(fisheye_pair, tmp_path):
    v = Mg360Video.from_dual_fisheye(
        fisheye_pair["front"], fisheye_pair["back"],
        target_name=str(tmp_path / "v.mp4"), fov=FOV,
        width=384, height=192)
    assert v.projection == Projection.equirect
    assert os.path.isfile(v.filename)


def test_default_candidates_cover_garmin_raw(fisheye_pair, tmp_path):
    """Garmin VIRB RAW hemispheres are ~200 deg; defaults must reach 205."""
    import inspect

    from musicalgestures._360video import calibrate_dual_fisheye_fov
    src = inspect.getsource(calibrate_dual_fisheye_fov)
    assert "205" in src and "200" in src

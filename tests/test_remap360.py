"""Legacy-360 remap flattening: GoPro MAX EAC and Ricoh Theta S."""
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from musicalgestures._remap360 import (GOPRO_TEMPLATES, probe_gopro360,
                                       write_remap_pgm)

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None,
                                reason="ffmpeg not on PATH")


def _mux_two_strips(folder, w=512, h=168, name="synthetic.360"):
    """Two color video tracks + stereo AAC + 4ch PCM in one MOV."""
    out = str(folder / name)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"color=red:s={w}x{h}:d=1:r=10",
         "-f", "lavfi", "-i", f"color=blue:s={w}x{h}:d=1:r=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
         "-f", "lavfi", "-i", "anoisesrc=d=1:c=pink",
         "-filter_complex",
         "[3:a]pan=4.0|c0=c0|c1=c0|c2=c0|c3=c0[a4]",
         "-map", "0:v", "-map", "1:v", "-map", "2:a", "-map", "[a4]",
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a:0", "aac", "-c:a:1", "pcm_s32le",
         "-f", "mov", out],
        check=True)
    return out


def test_probe_two_strip_file(tmp_path):
    # 512x168 scales the 4096x1344 template by 1/8: center 172, side 168, blend 4
    f = _mux_two_strips(tmp_path)
    info = probe_gopro360(f)
    assert len(info["video"]) == 2
    assert info["video"][0]["width"] == 512
    assert info["experimental"] is True          # scaled, not exact template
    assert info["centerwidth"] == round(512 * 1376 / 4096)
    assert info["sidewidth"] == round(512 * 1344 / 4096)
    assert any(a["channels"] == 4 for a in info["audio"])


def test_probe_exact_template_not_experimental():
    assert GOPRO_TEMPLATES[(4096, 1344)] == (1376, 1344, 32)
    assert GOPRO_TEMPLATES[(2272, 736)] == (768, 736, 16)


def test_probe_rejects_single_track(tmp_path):
    out = str(tmp_path / "single.360")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "color=red:s=512x168:d=1:r=10", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-f", "mov", out], check=True)
    with pytest.raises(ValueError, match="not a GoPro two-strip"):
        probe_gopro360(out)


def test_write_remap_pgm_roundtrip(tmp_path):
    xmap = np.arange(12, dtype=np.uint16).reshape(3, 4)
    ymap = (xmap * 7).astype(np.uint16)
    xp, yp = write_remap_pgm(xmap, ymap, str(tmp_path))
    raw = open(xp, "rb").read()
    assert raw.startswith(b"P5")
    assert b"65535" in raw.split(b"\n")[2] or b"65535" in raw
    data = raw[raw.rindex(b"65535") + 6:]
    got = np.frombuffer(data, dtype=">u2").reshape(3, 4)
    assert np.array_equal(got, xmap)


from musicalgestures._remap360 import gopro_maps


def _maps_max():
    return gopro_maps(4096, 1344, 1376, 1344, 32, 512, 256)


def test_gopro_maps_front_center():
    xL, yL, xR, yR, alpha = _maps_max()
    # lon=0, lat=0 -> FRONT face centre -> strip 1, x = sidewidth + cw/2
    r, c = 128, 256                      # centre of a 512x256 equirect
    assert alpha[r, c] == 0
    assert abs(xL[r, c] - (1344 + 1376 / 2)) < 3
    assert abs(yL[r, c] - 1344 / 2) < 3


def test_gopro_maps_back_in_second_strip():
    xL, yL, xR, yR, alpha = _maps_max()
    r, c = 128, 0                        # lon=-180 -> BACK -> strip 2
    assert yL[r, c] >= 1344              # vstacked: second strip below first


def test_gopro_maps_poles_in_second_strip():
    xL, yL, xR, yR, alpha = _maps_max()
    assert yL[2, 256] >= 1344            # lat ~ +90 -> TOP -> strip 2
    assert yL[253, 256] >= 1344          # lat ~ -90 -> DOWN -> strip 2


def test_gopro_maps_blend_zone_exists_and_bounded():
    xL, yL, xR, yR, alpha = _maps_max()
    assert 0.0 <= alpha.min() and alpha.max() <= 1.0
    assert (alpha > 0).any()             # some pixels blend
    assert (alpha > 0).mean() < 0.2      # ...but only near the four seams
    # where alpha==0, both maps agree (single-sample region)
    same = alpha == 0
    assert np.allclose(xL[same], xR[same], atol=0.51)


import cv2

from musicalgestures._remap360 import flatten_gopro360


def _eac_fixture(folder, track_w=512, track_h=168):
    """Render a test pattern into two GoPro-EAC strips (inverse mapping,
    written independently of gopro_maps: strip pixel -> direction ->
    pattern), muxed with stereo AAC + 4ch PCM audio."""
    cw = round(track_w * 1376 / 4096)
    sw = round(track_w * 1344 / 4096)
    bw = max(2, round(track_w * 32 / 4096))

    def pattern(lon, lat):
        r = 128 + 100 * np.sin(4 * lon) * np.cos(3 * lat)
        g = 128 + 100 * np.cos(5 * lon + 1.0)
        b = 128 + 100 * np.sin(6 * lat + 0.5)
        return np.clip(np.stack([b, g, r], -1), 0, 255).astype(np.uint8)

    strips = []
    for strip_i in range(2):
        img = np.zeros((track_h, track_w, 3), np.uint8)
        jj, ii = np.meshgrid(np.arange(track_h), np.arange(track_w),
                             indexing="ij")
        for slot, x0, w_f in (("l", 0, sw), ("c", sw, cw),
                              ("r", sw + cw, sw)):
            m = (ii >= x0) & (ii < x0 + w_f)
            u_phys = (ii - x0 + 0.5) / w_f
            v = (jj + 0.5) / track_h
            if slot == "c":
                u = u_phys
            else:                          # invert the seam split
                duv = bw / sw
                u = np.where(u_phys < 0.5,
                             u_phys / (2 * (0.5 - duv)),
                             (u_phys - 0.5 - duv) / (2 * (0.5 - duv)) + 0.5)
                u = np.clip(u, 0, 1)
            face = {("l", 0): "LEFT", ("c", 0): "FRONT", ("r", 0): "RIGHT",
                    ("l", 1): "DOWN", ("c", 1): "BACK", ("r", 1): "TOP"}[
                        (slot, strip_i)]
            uu, vv = u.copy(), v.copy()
            if face in ("DOWN", "BACK", "TOP"):    # invert RotateUV90
                uu, vv = 1 - vv, uu
            t_a = np.tan((2 * uu - 1) * np.pi / 4)  # inverse EAC
            t_b = np.tan((2 * vv - 1) * np.pi / 4)
            if face == "LEFT":
                x, y, z = -np.ones_like(t_a), t_a, t_b
            elif face == "RIGHT":
                x, y, z = np.ones_like(t_a), -t_a, t_b
            elif face == "FRONT":
                x, y, z = t_a, np.ones_like(t_a), t_b
            elif face == "BACK":
                x, y, z = -t_a, -np.ones_like(t_a), t_b
            elif face == "TOP":
                x, y, z = -t_a, t_b, np.ones_like(t_a)
            else:                                   # DOWN
                x, y, z = -t_a, -t_b, -np.ones_like(t_a)
            lon = np.arctan2(x, y)
            lat = np.arctan2(z, np.hypot(x, y))
            img[m] = pattern(lon, lat)[m]
        p = str(folder / f"strip{strip_i}.png")
        cv2.imwrite(p, img)
        strips.append(p)

    out = str(folder / "synthetic.360")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-loop", "1", "-t", "1", "-r", "10", "-i", strips[0],
         "-loop", "1", "-t", "1", "-r", "10", "-i", strips[1],
         "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
         "-f", "lavfi", "-i", "anoisesrc=d=1:c=pink",
         "-filter_complex", "[3:a]pan=4.0|c0=c0|c1=c0|c2=c0|c3=c0[a4]",
         "-map", "0:v", "-map", "1:v", "-map", "2:a", "-map", "[a4]",
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a:0", "aac", "-c:a:1", "pcm_s32le", "-shortest",
         "-f", "mov", out], check=True)
    return out, pattern


def test_flatten_gopro360_round_trip(tmp_path):
    src, pattern = _eac_fixture(tmp_path)
    out = flatten_gopro360(src, target_name=str(tmp_path / "flat.mp4"),
                           width=504, height=252)
    frame_png = str(tmp_path / "flat.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.5", "-i", out,
                    "-frames:v", "1", frame_png], check=True)
    got = cv2.imread(frame_png).astype(float)
    jj, ii = np.meshgrid(np.arange(252), np.arange(504), indexing="ij")
    lon = (ii + 0.5) / 504 * 2 * np.pi - np.pi
    lat = np.pi / 2 - (jj + 0.5) / 252 * np.pi
    ref = pattern(lon, lat).astype(float)
    band = slice(252 // 4, 3 * 252 // 4)          # away from the poles
    corr = np.corrcoef(got[band].ravel(), ref[band].ravel())[0, 1]
    assert corr > 0.9


def test_flatten_gopro360_accepts_mkv(tmp_path):
    src, _ = _eac_fixture(tmp_path)
    mkv = str(tmp_path / "merged.mkv")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src,
                    "-map", "0", "-c", "copy", mkv], check=True)
    out = flatten_gopro360(mkv, target_name=str(tmp_path / "flat2.mp4"),
                           width=504, height=252)
    assert Path(out).is_file()


def test_camera_registry_has_max2():
    from musicalgestures._360video import CAMERA
    assert "gopro max2" in CAMERA

"""Legacy-360 remap flattening: GoPro MAX EAC and Ricoh Theta S."""
import shutil
import subprocess

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

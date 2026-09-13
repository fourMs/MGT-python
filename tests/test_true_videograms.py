"""The videogram tracks are videograms (issue #383): means of the picture, not of the motion frame."""
import json
import subprocess

import numpy as np
import pytest

from musicalgestures._tracks import extract_tracks, read_columns, build_pyramid

cv2 = pytest.importorskip("cv2")


def _static_then_moving(path, size=(160, 120), fps=25):
    """4 s of a bright bar that never moves, then 4 s where a small square moves across it."""
    W, H = size
    out = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    for k in range(8 * fps):
        f = np.zeros((H, W, 3), np.uint8)
        f[40:60, :, :] = 200                         # the bar: rows 40..59 bright in every frame
        if k >= 4 * fps:
            x = (k - 4 * fps) * 3 % (W - 20)
            f[90:110, x:x + 20, :] = 255              # the mover, lower in the frame
        out.write(f)
    out.release()
    return str(path)


def test_videogram_sees_the_static_bar_and_the_motiongram_does_not(tmp_path):
    v = _static_then_moving(tmp_path / "v.mp4")
    meta = extract_tracks(v, out_dir=tmp_path / "out", progress=False)
    d = tmp_path / "out" / "v"
    assert {"motiongram_v", "motiongram_h", "videogram_v", "videogram_h"} <= set(meta)
    n, H = meta["frames"], meta["height"]
    vg = np.memmap(d / meta["videogram_v"], dtype=np.uint8, mode="r", shape=(n, H))
    mg = np.memmap(d / meta["motiongram_v"], dtype=np.uint8, mode="r", shape=(n, H))
    early = slice(5, 3 * 25)                         # static seconds
    assert vg[early, 40:60].mean() > 150             # the bar is in the picture
    assert vg[early, 0:30].mean() < 10               # and the background is dark
    assert mg[early, 40:60].mean() < 5               # nothing moves there, so the motiongram is dark
    late = slice(4 * 25 + 5, n - 2)
    assert mg[late, 90:110].mean() > mg[late, 40:60].mean() + 5   # motion shows where the square moves
    # readers take both names, and the pyramid is per track
    cols, spc = read_columns(d, max_columns=50, which="videogram_v")
    assert cols.shape[1] == H and cols[:, 40:60].max() > 150
    mcols, _ = read_columns(d, max_columns=50, which="motiongram_v")
    assert mcols.shape[1] == H
    pyr = json.loads((d / "tracks.json").read_text())["pyramid"]
    assert "videogram_v" in pyr and "motiongram_v" in pyr


def test_legacy_folder_serves_motion_means_under_the_old_name(tmp_path):
    d = tmp_path / "old"; d.mkdir()
    n, H, W = 300, 8, 6
    np.full((n, H), 7, np.uint8).tofile(d / "videogram_v.u1")
    np.zeros((n, W), np.uint8).tofile(d / "videogram_h.u1")
    np.zeros(n, np.float32).tofile(d / "qom.f4")
    (d / "tracks.json").write_text(json.dumps({"frames": n, "fps": 25.0, "width": W, "height": H, "duration_s": 12.0,
                                               "qom": "qom.f4", "videogram_v": "videogram_v.u1", "videogram_h": "videogram_h.u1"}))
    cols, _ = read_columns(d, max_columns=40, which="motiongram_v")     # the honest name works on old data
    assert cols.max() == 7
    with pytest.raises(FileNotFoundError):
        read_columns(d, max_columns=40, which="videogram_v")            # and the old name is refused with a reason

"""Camera state from synthetic footage: a static scene, a pan, and a cut."""
import subprocess

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from musicalgestures._camera import camera_motion, camera_state_at, still_runs
from musicalgestures._performers import performer_count


def _footage(path, fps=2, size=(320, 180)):
    """8 s static texture, 4 s pan (2 px/frame), a cut to a different texture, 8 s static."""
    rng = np.random.default_rng(1)
    W, H = size
    wide = (rng.random((H, W + 200)) * 255).astype(np.uint8)
    wide = cv2.GaussianBlur(wide, (0, 0), 1.5)
    # the other angle: a different, darker picture, as a second camera on a lit stage is
    other = cv2.GaussianBlur((rng.random((H, W)) * 110).astype(np.uint8), (0, 0), 3)
    out = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    x = 0
    for k in range(8 * fps):
        out.write(cv2.cvtColor(wide[:, x:x + W], cv2.COLOR_GRAY2BGR))
    for k in range(4 * fps):
        x += 4
        out.write(cv2.cvtColor(wide[:, x:x + W], cv2.COLOR_GRAY2BGR))
    for k in range(8 * fps):
        out.write(cv2.cvtColor(other, cv2.COLOR_GRAY2BGR))
    out.release()
    return path


def test_states_cuts_and_framings(tmp_path):
    v = _footage(tmp_path / "cam.mp4")
    cam = camera_motion(v, proxy_path=tmp_path / "proxy.mp4", verbose=False)
    st = np.array(cam["state"])
    t = np.array(cam["t"])
    assert (st[(t > 1) & (t < 7.5)] == "still").mean() > 0.9
    assert (st[(t > 8.5) & (t < 11.5)] == "moving").mean() > 0.8
    assert len(cam["cuts"]) == 1 and abs(cam["cuts"][0] - 12.0) <= 1.0
    assert len(cam["shots"]) == 2
    runs = still_runs(cam, min_s=5.0)
    assert len(runs) == 2 and runs[0][0] < 1.0 and runs[1][0] >= 11.5
    assert list(camera_state_at(cam, [3.0, 10.0])) == ["still", "moving"]


def test_performer_count_per_framing_ignores_the_moving_camera():
    cam = {"hop_s": 0.5, "t": [i * 0.5 for i in range(80)],
           "state": ["still"] * 30 + ["moving"] * 10 + ["still"] * 40}
    frames = []
    for t in range(40):
        n = 1 if t < 15 else (4 if t < 20 else 3)     # close shot, then the camera swings past a crowd, then wide
        frames.append({"t": float(t), "boxes": [[0.1 * k, 0.2, 0.1 * k + 0.08, 0.7, 0.9] for k in range(n)]})
    c = performer_count({"fps": 1.0, "frames": frames}, 0, 40, camera=cam)
    assert c["method"] == "framings" and c["estimate"] == 3 and c["low"] == 1

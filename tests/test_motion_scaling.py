"""Motion extraction must not reallocate its output once per frame.

`mg_motion` grew every output with `np.append` inside the frame loop until
2026-08-24. Each append reallocates the whole array, so cost is O(n^2) in frames,
and the motiongrams --- which grow to height x n x 3 --- reallocate O(n^2) bytes.
The numbers were right, so nothing caught it. Measured on 1080p before the fix:
69 s, 148 s and 366 s for 30 s, 60 s and 120 s of video, an exponent rising from
1.10 to 1.31 as the quadratic term took over, extrapolating to roughly 215 hours
for a 2 h 38 min recording. Invisible on clips, fatal on a session.

**This test counts calls rather than seconds, and that is deliberate.** The
obvious test --- process a long clip and a short one and compare the times --- was
written first and PASSED AGAINST THE UNFIXED CODE, because at a small frame size
the quadratic term is still negligible and the timing is noise. A check that
cannot fail is worth nothing, so this asserts the property directly: the number
of `np.append` calls must not grow with the number of frames.
"""
import subprocess

import numpy as np

import musicalgestures as mg


def _synth(path, seconds, fps=25, size="160x120"):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
         "-i", f"testsrc=size={size}:rate={fps}:duration={seconds}",
         "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True)
    return str(path)


def _appends_during_motion(path, monkeypatch):
    """How many times np.append is called while extracting motion from `path`."""
    calls = {"n": 0}
    real = np.append

    def counting(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(np, "append", counting)
    mg.MgVideo(path).motion(save_video=False, save_plot=False,
                            save_data=True, normalize=False)
    return calls["n"]


def test_motion_does_not_reallocate_per_frame(tmp_path, monkeypatch):
    short = _synth(tmp_path / "short.mp4", 2)     # 50 frames
    long = _synth(tmp_path / "long.mp4", 8)       # 200 frames, four times as many

    n_short = _appends_during_motion(short, monkeypatch)
    n_long = _appends_during_motion(long, monkeypatch)

    assert n_long <= n_short + 2, (
        f"np.append was called {n_short} times for 50 frames and {n_long} times for "
        f"200 frames, so it grows with the frame count. Something is accumulating "
        f"inside the frame loop again; collect into a list and convert once after it."
    )

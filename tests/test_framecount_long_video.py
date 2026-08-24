"""A long video must be openable at all.

`get_framecount` gave ffprobe a flat 10-second timeout, and on timeout escalated to
`-count_frames`, which fully DECODES the file and is far slower --- so that timed out
too and the call raised. The effect was a hard ceiling on video length that had
nothing to do with any analysis: MGT simply could not open the file.

Measured on a 2 h 38 min 1080p recording: counting packets takes 22 s, so `MgVideo()`
raised `FFprobeError: Could not count frames. (Is this a video file?)` on a perfectly
ordinary MP4. The container's own `nb_frames` said 475,680 all along, and the packet
count agreed exactly.

These tests use a simulated timeout rather than a two-hour fixture: the property is
"a timeout falls back instead of escalating", and that does not need a big file to
assert.
"""
import subprocess

import pytest

from musicalgestures import _utils
from musicalgestures._utils import _container_framecount, get_framecount


def _synth(path, seconds=2, fps=25, size="160x120"):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
         "-i", f"testsrc=size={size}:rate={fps}:duration={seconds}",
         "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True)
    return str(path)


def test_container_framecount_reads_nb_frames(tmp_path):
    v = _synth(tmp_path / "v.mp4")
    assert _container_framecount(v) == 50


def test_framecount_agrees_with_the_container(tmp_path):
    v = _synth(tmp_path / "v.mp4")
    assert get_framecount(v) == _container_framecount(v) == 50


def test_a_timeout_falls_back_instead_of_escalating(tmp_path, monkeypatch):
    """The regression. A timeout must not send us to a slower method.

    Escalating from `-count_packets` to `-count_frames` on a timeout is strictly
    worse: the second is the one that decodes. Before this fix a file that was merely
    long could not be opened at all.

    The timeout is shortened to something ffprobe cannot meet, so this exercises the
    real code path against a real ffprobe rather than a mock of one.
    """
    v = _synth(tmp_path / "v.mp4", seconds=3)
    monkeypatch.setattr(_utils, "framecount_timeout", lambda *a, **k: 0.001)
    with pytest.warns(RuntimeWarning, match="timed out"):
        n = get_framecount(v)
    assert n == 75, "should have fallen back to the container's nb_frames"


def test_timeout_scales_with_file_size(tmp_path):
    """A bigger file gets longer, not the same ten seconds.

    Asserted through behaviour rather than by reading a constant. The bug was that a
    2.8 GB file needed 22 s and was given 10; the fix is that the allowance grows with
    the file, and that the floor is well above what any short clip needs.
    """
    small = _synth(tmp_path / "small.mp4", seconds=1)
    t_small = _utils.framecount_timeout(small)
    assert t_small >= 60, "the floor is lower than the 22 s a long file measurably needed"

    #: A file that does not exist stands in for size 0: the point is the scaling rule,
    #: not the bytes on disk.
    import os
    real_getsize = os.path.getsize
    try:
        os.path.getsize = lambda p: 3_000_000_000            # type: ignore[assignment]
        t_big = _utils.framecount_timeout(small)
    finally:
        os.path.getsize = real_getsize                       # type: ignore[assignment]
    assert t_big > t_small, "a 3 GB file gets no more time than a 1-second clip"
    assert t_big >= 300, f"3 GB got only {t_big:.0f}s; it needed 22 s at 2.8 GB"

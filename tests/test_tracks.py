"""The lean extractor must agree with mg_motion, and with itself.

`_tracks.extract_tracks` exists to do in one pass what `mg_motion` does in several,
for recordings too long for the general path. It is only worth having if it produces
the same numbers, so that is what these assert --- against `mg_motion` itself, which
is the known answer.

The bug these were written for: an earlier version appended its own output arguments
before calling `ffmpeg_cmd(pipe="read")`, which appends its OWN. ffmpeg was given two
outputs and wrote both into the same stdout, interleaved. The result was frames that
were wrong and, because interleaving depends on buffering, **different between
identical runs**. Nothing in the suite would have caught it, so these exist.
"""
import csv
import subprocess

import numpy as np
import musicalgestures as mg
from musicalgestures._tracks import extract_tracks, extract_tracks_parallel


def _synth(path, seconds=4, fps=25, size="320x240"):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
         "-i", f"testsrc=size={size}:rate={fps}:duration={seconds}",
         "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True)
    return str(path)


def _qom_from_tracks(meta, d):
    return np.memmap(d / "qom.f4", dtype=np.float32, mode="r").astype(float)


def _qom_from_mg_motion(path):
    mg.MgVideo(path).motion(motion_analysis="qom", save_motiongrams=False,
                            save_video=False, save_plot=False, save_data=True,
                            normalize=False)
    csv_path = str(path).rsplit(".", 1)[0] + "_motion.csv"
    return np.array([float(r["QomRaw"]) for r in csv.DictReader(open(csv_path))])


def test_qom_matches_mg_motion(tmp_path):
    """The whole point: same numbers as the path it replaces."""
    v = _synth(tmp_path / "v.mp4")
    meta = extract_tracks(v, out_dir=tmp_path / "out", progress=False)
    mine = _qom_from_tracks(meta, tmp_path / "out" / "v")
    truth = _qom_from_mg_motion(v)
    n = min(len(mine), len(truth))
    assert n > 50, "clip too short to be a real comparison"
    np.testing.assert_allclose(mine[:n], truth[:n], rtol=0, atol=1e-3)


def test_extraction_is_deterministic(tmp_path):
    """Run it twice and get the same answer.

    This is the test that would have caught the interleaved-output bug on the day it
    was written, and it is cheap. An extractor whose answer depends on buffering is
    not an extractor.
    """
    v = _synth(tmp_path / "v.mp4")
    a = extract_tracks(v, out_dir=tmp_path / "a", progress=False)
    b = extract_tracks(v, out_dir=tmp_path / "b", progress=False)
    qa = _qom_from_tracks(a, tmp_path / "a" / "v")
    qb = _qom_from_tracks(b, tmp_path / "b" / "v")
    assert np.array_equal(qa, qb), "two identical runs disagreed"


def test_parallel_matches_serial(tmp_path):
    """Chunked extraction must equal serial extraction.

    **This passes here and does NOT cover the fault that matters.** On the real
    material --- 1920x1080 at 50 fps, 120 s, eight workers, 15 s chunks --- the
    parallel path repeats one frame at the last chunk seam: `-ss` before `-i` seeks
    to a keyframe, so the number of frames decoded before the target is not always
    the single frame the worker drops. On this small synthetic clip the seek lands
    exactly and the artefact does not appear.

    So this guards the easy case only, and the parallel path should not be used until
    a fixture reproduces the hard one. Written down because a passing test that does
    not exercise the known bug is worse than no test: it reads like cover.
    """
    v = _synth(tmp_path / "v.mp4", seconds=8)
    s = extract_tracks(v, out_dir=tmp_path / "s", progress=False)
    p = extract_tracks_parallel(v, out_dir=tmp_path / "p", workers=4, chunk_s=2)
    qs = _qom_from_tracks(s, tmp_path / "s" / "v")
    qp = _qom_from_tracks(p, tmp_path / "p" / "v")
    n = min(len(qs), len(qp))
    assert np.array_equal(qs[:n], qp[:n])

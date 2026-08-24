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


def _synth_keyframes(path, seconds=10, fps=25, size="320x240", gop=37):
    """A clip whose keyframes deliberately do NOT align with chunk boundaries.

    `gop=37` at 25 fps puts a keyframe every 1.48 s, so a chunk starting on a round
    second lands mid-GOP and `-ss` seeks backwards to the keyframe. How many frames
    then arrive before the target varies --- which is exactly what the old
    drop-exactly-one-frame logic got wrong.
    """
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
         "-i", f"testsrc=size={size}:rate={fps}:duration={seconds}",
         "-g", str(gop), "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True)
    return str(path)


def test_parallel_matches_serial_across_unaligned_keyframes(tmp_path):
    """Chunked extraction must equal serial extraction, seams included.

    The fault this exists for: chunks were seeked with `-ss` and then had exactly one
    frame dropped as the difference filter's lead-in. `-ss` before `-i` lands on a
    keyframe, so the frames arriving before the target are not always one, and a chunk
    could repeat its predecessor's value. On 1080p/50 fps that showed up as a single
    wrong frame in 6,005 --- small enough to dismiss and wrong all the same.

    **THIS TEST DOES NOT REPRODUCE THAT FAULT, and saying so is the point.** It was
    written twice --- once with a default GOP, once with keyframes forced off the chunk
    grid as here --- and BOTH versions pass against the broken drop-exactly-one-frame
    code. The artefact needs the real material to appear: 1920x1080 at 50 fps, 120 s,
    eight workers, 15 s chunks, where it showed up as one wrong frame in 6,005. A
    fixture that heavy does not belong in a unit suite.

    So this guards the easy case and no more. What actually prevents the fault coming
    back is structural rather than tested: the worker no longer counts frames after a
    seek at all --- it seeks a second early and lets `trim` keep the wanted range by
    timestamp, so there is no count to get wrong. If that ever reverts to counting,
    this test will not notice. The comment in `_chunk_worker` says the same thing at
    the place where it would happen.
    """
    v = _synth_keyframes(tmp_path / "v.mp4")
    s = extract_tracks(v, out_dir=tmp_path / "s", progress=False)
    p = extract_tracks_parallel(v, out_dir=tmp_path / "p", workers=4, chunk_s=2)
    qs = _qom_from_tracks(s, tmp_path / "s" / "v")
    qp = _qom_from_tracks(p, tmp_path / "p" / "v")
    n = min(len(qs), len(qp))
    assert n > 200
    bad = np.flatnonzero(qs[:n] != qp[:n])
    assert len(bad) == 0, f"{len(bad)} frames differ at/after chunk seams: {bad[:8]}"

"""Counting performers from person boxes: the stage filter and the span statistic.

The detector itself is an optional extra and needs weights; what is tested here is the
geometry that separates performers from the audience and how the per-frame counts are
summarised over a span with a moving camera.
"""
import numpy as np
import pytest

from musicalgestures._performers import on_stage, people_track, performer_count


def test_on_stage_keeps_high_heads_and_drops_the_audience():
    assert on_stage([0.27, 0.38, 0.44, 0.85, 0.91])          # seated pianist, feet visible
    assert on_stage([0.34, 0.15, 0.49, 0.62, 0.79])          # singer, upper body
    assert not on_stage([0.20, 0.80, 0.32, 1.00, 0.81])      # audience head cut by the bottom edge
    assert not on_stage([0.44, 0.51, 0.57, 0.80, 0.70])      # head in the lower half, seated in the hall
    assert not on_stage([0.34, 0.15, 0.49, 0.62, 0.30])      # weak detection
    assert on_stage([0.08, 0.30, 0.31, 0.99, 0.74])          # standing performer whose feet are cut off


def _frames(counts_per_frame):
    """One on-stage box per counted person, plus two audience heads in every frame."""
    fr = []
    for t, n in enumerate(counts_per_frame):
        boxes = [[0.1 * k, 0.2, 0.1 * k + 0.08, 0.7, 0.9] for k in range(n)]
        boxes += [[0.2, 0.8, 0.3, 1.0, 0.8], [0.5, 0.82, 0.6, 1.0, 0.7]]
        fr.append({"t": float(t), "boxes": boxes})
    return {"fps": 1.0, "frames": fr}


def test_people_track_ignores_the_audience():
    t, n = people_track(_frames([1, 1, 2]))
    np.testing.assert_array_equal(t, [0, 1, 2])
    np.testing.assert_array_equal(n, [1, 1, 2])


def test_performer_count_reads_the_wide_shots():
    # camera mostly on the singer, wide shot of the band now and then
    det = _frames([1, 1, 5, 1, 2, 1, 5, 1, 1, 5])
    c = performer_count(det, 0, 10)
    assert c == {"estimate": 5, "median": 1, "max": 5, "frames": 10}


def test_performer_count_respects_the_span():
    det = _frames([3, 3, 3, 1, 1, 1])
    assert performer_count(det, 3, 6)["estimate"] == 1
    assert performer_count(det, 6, 9)["frames"] == 0 and performer_count(det, 6, 9)["estimate"] is None


def test_detect_people_runs_when_the_extra_is_there(tmp_path):
    pytest.importorskip("ultralytics")
    import subprocess
    from musicalgestures._performers import detect_people
    v = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=10:duration=3",
                    "-pix_fmt", "yuv420p", str(v)], check=True, capture_output=True)
    try:
        det = detect_people(v, fps=1.0, width=320, verbose=False)
    except Exception as e:                      # no weights, no network
        pytest.skip(f"detector unavailable: {e}")
    assert det["fps"] == 1.0 and len(det["frames"]) == 3
    assert all("boxes" in f for f in det["frames"])

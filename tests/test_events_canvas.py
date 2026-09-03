"""Events against events, cross-recurrence, head turns and painting content on synthetic material.

Each test builds the case where the answer is known: events placed on references must attract,
events placed between them must avoid, a delayed copy must recur at its delay, a head that turns
must give one span per turn, and a canvas that gains a red patch must show it in coverage,
warmth and paint centre.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from musicalgestures._canvas import composition, painting_content
from musicalgestures._correlate import cross_recurrence
from musicalgestures._events import event_alignment, event_xcorr
from musicalgestures._pupillabs import head_turns


def test_events_on_references_attract_and_between_them_avoid():
    rng = np.random.default_rng(0)
    ref = np.sort(rng.uniform(0, 600, 300))
    on = ref[::3] + rng.normal(0, 0.03, len(ref[::3]))
    a = event_alignment(on, ref, 600.0)
    assert a.verdict == "attract" and a.median_nearest_s < 0.1 and a.frac_within > 0.9
    mid = (ref[:-1] + ref[1:]) / 2
    gaps = np.diff(ref)
    between = mid[gaps > 3.0]
    b = event_alignment(between, ref, 600.0)
    assert b.verdict == "avoid" and b.median_nearest_s > b.surrogate_median_s
    assert 0.25 < b.frac_reference_first < 0.75


def test_event_alignment_handles_empty():
    a = event_alignment([], [1.0, 2.0], 10.0)
    assert a.n_events == 0 and a.p_closer == 1.0 and a.verdict == "chance"


def test_event_xcorr_peaks_at_the_delay():
    ev = np.arange(5, 500, 4.0)
    lags, r = event_xcorr(ev, ev + 0.7, 520.0, bin_s=0.1, max_lag_s=3.0)
    assert abs(lags[np.argmax(r)] - 0.7) < 0.11


def test_cross_recurrence_finds_delayed_copy():
    rng = np.random.default_rng(1)
    x = np.convolve(rng.standard_normal(700), np.ones(8) / 8, "same")
    y = np.roll(x, 4) + 0.1 * rng.standard_normal(700)
    out = cross_recurrence(x, y, 1.0, n_surrogates=40, max_lag_s=10)
    assert out["profile_peak_lag_s"] == 4.0
    assert out["determinism"] > out["det_surrogate_mean"] and out["p_determinism"] < 0.1
    assert abs(out["recurrence_rate"] - 0.2) < 0.03 and out["matrix"].shape == (698, 698)


def test_head_turns_one_span_per_turn():
    fps = 30.0
    t = np.arange(0, 120, 1 / fps)
    yaw = np.zeros(len(t))
    for a, b, deg in ((20, 23, 40), (60, 62, -35), (90, 90.2, 50)):  # the last is too short
        yaw[(t >= a) & (t < b)] = deg
    frames = pd.DataFrame({"frame": np.arange(len(t)), "time": t, "head_yaw": yaw})
    spans = head_turns(frames, fps, baseline_s=30, threshold_deg=25, min_duration_s=0.5)
    assert len(spans) == 2
    assert spans.direction.tolist() == ["left", "right"]
    assert abs(spans.start.iloc[0] - 20) < 0.1 and abs(spans.duration.iloc[0] - 3) < 0.2
    assert "head_turned" in frames and frames.head_turned.sum() == pytest.approx((3 + 2) * fps, rel=0.05)


def _canvas_video(path, seconds=12, fps=10):
    import cv2
    w, h = 160, 120
    out = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i in range(seconds * fps):
        fr = np.full((h, w, 3), 235, np.uint8)
        s = i / fps
        if s >= 6:  # a red patch appears at the top left after 6 s
            fr[10:50, 10:70] = (30, 30, 200)
        if i % 3 == 0:  # a dark "hand" flickers across the canvas
            fr[60:100, 80:140] = (40, 40, 40)
        out.write(fr)
    out.release()


def test_painting_content_sees_the_red_patch(tmp_path):
    p = tmp_path / "canvas.mp4"
    _canvas_video(p)
    c = painting_content(p, reference_s=3)
    assert len(c["t"]) == 12
    assert c["coverage"][:5].max() < 0.02 and c["painted"][-3:].min() > 0.08
    assert c["warm"][-3:].mean() > c["warm"][:5].mean() + 0.05
    assert c["composition"]["mass_y"][-1] < 0.5 and c["composition"]["mass_x"][-1] < 0.5
    assert c["hue_hist"].shape[0] == 36 and len(c["palette"]) == 1
    # the flickering hand is removed by the temporal median: brightness barely moves
    assert np.ptp(c["brightness"][:5]) < 0.02


def test_composition_symmetry():
    import cv2  # noqa: F401
    fr = np.full((100, 100, 3), 240, np.uint8)
    fr[20:80, 10:40] = (200, 40, 40)
    fr[20:80, 60:90] = (200, 40, 40)
    c = composition(fr)
    assert c["symmetry_lr"] > 0.9 and abs(c["mass_x"] - 0.5) < 0.02
    fr2 = fr.copy(); fr2[20:80, 60:90] = 240
    assert composition(fr2)["symmetry_lr"] < 0.2

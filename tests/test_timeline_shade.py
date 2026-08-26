"""Shaded regions on a sheet, because a boundary line does not show an extent.

Drawing only the start of each span tells a reader where the warm-up began and lets them
assume it ran until the next line. On this corpus that is wrong by 21 minutes: the
warm-up ends and nothing happens for a third of an hour before the rehearsal starts.
A reader orienting themselves from the overview would misread the whole session.

The idiom is `annat_shade()` from https://github.com/finn42/Laughter_Dance by Finn Upham.
"""
import json

import pytest

from musicalgestures._actions import Action
from musicalgestures._timeline import render_timeline


def test_shaded_spans_are_recorded_in_the_sidecar(tmp_path, monkeypatch):
    """The sidecar is the figure's audit trail, so what was shaded belongs in it."""
    from musicalgestures import _timeline
    d = tmp_path / "analysis"
    d.mkdir()
    import numpy as np
    n, fps = 1000, 10.0
    (d / "qom.f4").write_bytes(np.arange(n, dtype=np.float32).tobytes())
    (d / "tracks.json").write_text(json.dumps(
        {"fps": fps, "frames": n, "duration_s": n / fps, "qom": "qom.f4"}))
    out = render_timeline(d, panels=("qom",), levels=(), hierarchy=None,
                          shade=[Action(start=10.0, end=30.0, source="s",
                                        labels={"shade": "warm-up"})],
                          out=tmp_path / "s.png")
    side = json.loads((out.with_suffix(".json")).read_text())
    assert "shaded" in side
    assert side["shaded"][0]["start"] == pytest.approx(10.0)
    assert side["shaded"][0]["end"] == pytest.approx(30.0)
    assert side["shaded"][0]["label"] == "warm-up"


def test_no_shading_leaves_the_sidecar_as_it_was(tmp_path):
    """A figure that shades nothing must not claim it shaded something."""
    import numpy as np
    d = tmp_path / "analysis"
    d.mkdir()
    n, fps = 1000, 10.0
    (d / "qom.f4").write_bytes(np.arange(n, dtype=np.float32).tobytes())
    (d / "tracks.json").write_text(json.dumps(
        {"fps": fps, "frames": n, "duration_s": n / fps, "qom": "qom.f4"}))
    out = render_timeline(d, panels=("qom",), levels=(), hierarchy=None,
                          out=tmp_path / "n.png")
    side = json.loads((out.with_suffix(".json")).read_text())
    assert side.get("shaded", []) == []

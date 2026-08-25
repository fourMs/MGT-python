"""The sheet must record what it is showing, or a reader will measure off it.

These are structural assertions on a figure, which is as much as a figure can be
tested for: that it was written, that it carries its reduction factor and its time
range as text, and that a boundary the segmenter is unsure about is drawn differently
from one it is sure about. The last is the important one --- it is the difference
between a picture that reports a hypothesis and one that asserts a result.
"""
import json

import numpy as np
import pytest

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy
from musicalgestures._timeline import render_timeline


@pytest.fixture
def analysis(tmp_path):
    """A small but complete analysis directory."""
    d = tmp_path / "analysis"
    d.mkdir()
    n, H, W, fps = 3000, 16, 24, 50.0
    rng = np.random.default_rng(0)
    qom = (rng.uniform(0, 0.1, n)).astype(np.float32)
    qom[500:1000] = 1.0
    qom[2000:2500] = 1.0
    qom.tofile(d / "qom.f4")
    np.full((n, H), 40, dtype=np.uint8).tofile(d / "videogram_v.u1")
    np.full((n, W), 40, dtype=np.uint8).tofile(d / "videogram_h.u1")
    (d / "tracks.json").write_text(json.dumps({
        "frames": n, "fps": fps, "width": W, "height": H, "duration_s": n / fps,
        "qom": "qom.f4", "videogram_v": "videogram_v.u1",
        "videogram_h": "videogram_h.u1"}))
    return d


@pytest.fixture
def hierarchy():
    return Hierarchy(levels={"part": [
        Action(start=0.0, end=20.0, source="part", labels={"part": "improvisation"},
               features={"agreement": "both"}),
        Action(start=20.0, end=40.0, source="part", labels={"part": "talk"},
               features={"agreement": "motion_only"}),
        Action(start=40.0, end=60.0, source="part", labels={"part": "improvisation"},
               features={"agreement": "both"})]})


def test_a_sheet_is_written(analysis, hierarchy):
    out = render_timeline(analysis, hierarchy=hierarchy, levels=("part",))
    assert out.exists() and out.stat().st_size > 0


def test_the_reduction_factor_is_on_the_figure(analysis, hierarchy):
    """A decimated strip that does not say so is a trap."""
    out = render_timeline(analysis, hierarchy=hierarchy, levels=("part",))
    meta = json.loads(out.with_suffix(".json").read_text())
    assert meta["decimation_factor"] >= 1
    assert meta["printed_on_figure"] is True


def test_the_time_range_is_recorded(analysis, hierarchy):
    out = render_timeline(analysis, start_s=10.0, end_s=30.0, hierarchy=hierarchy)
    meta = json.loads(out.with_suffix(".json").read_text())
    assert meta["start_s"] == 10.0 and meta["end_s"] == 30.0


def test_uncertain_boundaries_are_drawn_differently(analysis, hierarchy):
    """The falsifiable claim, made visible."""
    out = render_timeline(analysis, hierarchy=hierarchy, levels=("part",))
    meta = json.loads(out.with_suffix(".json").read_text())
    styles = {b["agreement"]: b["linestyle"] for b in meta["boundaries"]}
    assert styles["both"] == "solid"
    assert styles["motion_only"] == "dashed"
    assert styles["both"] != styles["motion_only"]


def test_a_span_shorter_than_one_column_still_renders(analysis, hierarchy):
    out = render_timeline(analysis, start_s=0.0, end_s=0.2, hierarchy=hierarchy)
    assert out.exists()


def test_no_hierarchy_is_not_an_error(analysis):
    """An overview drawn before any segmentation exists is a normal thing to want."""
    out = render_timeline(analysis, hierarchy=None)
    meta = json.loads(out.with_suffix(".json").read_text())
    assert meta["boundaries"] == []


def test_the_sidecar_names_the_image_it_belongs_to(analysis, hierarchy):
    out = render_timeline(analysis, hierarchy=hierarchy)
    meta = json.loads(out.with_suffix(".json").read_text())
    assert meta["image"] == out.name

"""A self-contained zoomable page: the one thing the original goal asked for and never got.

The stated aim for this corpus included "the ability to zoom from the whole session down to
a single action". What existed was three printed scales over a thirteen-level pyramid that
could support any scale. This closes that.

Self-contained matters: the page has to work from a folder somebody was sent, with no
server and no network, or it is not a deliverable. So the data is embedded, and the amount
embedded is a decision with a right answer --- enough to zoom usefully, not so much that the
file will not open. That decision is what is tested here.
"""
import numpy as np
import pytest

from musicalgestures._zoomview import decimate_minmax_pairs, embed_budget


def test_decimation_keeps_both_extremes_of_each_bucket():
    """A brief spike is exactly what zooming out must not lose; a mean would remove it."""
    x = np.zeros(100)
    x[7] = 5.0
    x[8] = -3.0
    lo, hi = decimate_minmax_pairs(x, 10)
    assert hi[0] == pytest.approx(5.0)
    assert lo[0] == pytest.approx(-3.0)


def test_decimation_returns_the_requested_number_of_buckets():
    lo, hi = decimate_minmax_pairs(np.arange(1000, dtype=float), 250)
    assert len(lo) == len(hi) == 250


def test_a_series_shorter_than_the_bucket_count_is_returned_whole():
    """Asking for more detail than exists must not invent any."""
    lo, hi = decimate_minmax_pairs(np.array([1.0, 2.0, 3.0]), 100)
    assert len(lo) == 3
    assert list(hi) == [1.0, 2.0, 3.0]


def test_an_empty_series_gives_empty_output_rather_than_an_error():
    lo, hi = decimate_minmax_pairs(np.array([]), 10)
    assert len(lo) == 0


def test_the_budget_gives_finer_resolution_for_a_shorter_recording():
    coarse = embed_budget(duration_s=9000.0, max_points=8000)
    fine = embed_budget(duration_s=600.0, max_points=8000)
    assert fine["seconds_per_point"] < coarse["seconds_per_point"]


def test_the_budget_never_promises_more_points_than_asked_for():
    b = embed_budget(duration_s=9000.0, max_points=4000)
    assert b["n_points"] <= 4000


def test_the_budget_reports_the_finest_resolution_the_page_can_show():
    """A page that cannot resolve a one-second gesture should say so, not imply it can."""
    b = embed_budget(duration_s=9513.6, max_points=8000)
    assert b["seconds_per_point"] == pytest.approx(9513.6 / 8000, rel=1e-6)
    assert "seconds_per_point" in b and b["seconds_per_point"] > 0

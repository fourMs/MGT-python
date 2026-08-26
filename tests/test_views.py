"""Views that know about annotations, which is what none of MGT's other figures do.

The toolbox already has a rich battery --- motiongrams, videograms, self-similarity,
tempograms, contact sheets, heatmaps --- and every one of them is about the signal. The
Hierarchy and the ELAN exporter exist on the other side. Almost nothing joins them, and for
somebody annotating two and a half hours that join is the tool.

Split the way `_voice` is split: the parts with a right answer --- which frames to sample,
how a grid is shaped, how much of a tier is filled, where a time falls in a matrix --- are
functions that need no video and are tested here. Rendering is a thin layer over them.
"""
import numpy as np
import pytest

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy
from musicalgestures._views import (grid_shape, sample_times, tier_density,
                                    time_to_index)


def test_sampled_times_span_the_range_without_touching_its_edges():
    """A frame at exactly the end of a clip may not exist; a frame just inside always does."""
    t = sample_times(0.0, 100.0, 5)
    assert len(t) == 5
    assert t[0] > 0.0
    assert t[-1] < 100.0
    assert np.all(np.diff(t) > 0)


def test_one_frame_is_taken_from_the_middle():
    assert sample_times(10.0, 20.0, 1) == pytest.approx([15.0])


def test_asking_for_no_frames_gives_none():
    assert sample_times(0.0, 10.0, 0) == []


def test_a_zero_length_span_still_yields_a_frame():
    """Spans arrive from detectors, and a detector can emit a degenerate one."""
    t = sample_times(5.0, 5.0, 3)
    assert len(t) == 3
    assert all(x == pytest.approx(5.0) for x in t)


def test_the_grid_is_as_square_as_it_can_be():
    assert grid_shape(9, None) == (3, 3)
    assert grid_shape(10, None) == (3, 4)      # rows x cols, wider than tall
    assert grid_shape(1, None) == (1, 1)


def test_an_explicit_column_count_is_obeyed():
    assert grid_shape(10, 5) == (2, 5)
    assert grid_shape(11, 5) == (3, 5)         # a partial last row, not a dropped item


def test_tier_density_is_the_fraction_of_each_bin_that_is_covered():
    spans = [Action(start=0.0, end=5.0, source="x")]
    d = tier_density(spans, duration_s=20.0, n_bins=4)
    assert d[0] == pytest.approx(1.0)
    assert d[1] == pytest.approx(0.0)


def test_a_span_crossing_a_bin_boundary_is_split_between_them():
    """Bins are 5 s wide here. A span of 2.5 to 7.5 covers the second half of the first
    bin and the first half of the second, so both read 0.5. Written first asserting 1.0
    for the second bin, which would have been a span twice as long as the one given."""
    spans = [Action(start=2.5, end=7.5, source="x")]
    d = tier_density(spans, duration_s=20.0, n_bins=4)
    assert d[0] == pytest.approx(0.5)
    assert d[1] == pytest.approx(0.5)
    assert d[2] == pytest.approx(0.0)


def test_overlapping_spans_do_not_make_a_bin_more_than_full():
    """Detectors emit touching and overlapping spans, and a density above 1 is nonsense."""
    spans = [Action(start=0.0, end=5.0, source="x"), Action(start=1.0, end=4.0, source="x")]
    d = tier_density(spans, duration_s=20.0, n_bins=4)
    assert d[0] == pytest.approx(1.0)


def test_an_empty_tier_gives_zeros_rather_than_nothing():
    """An empty tier must still be drawn: she needs to see which ones she has not filled."""
    d = tier_density([], duration_s=20.0, n_bins=4)
    assert len(d) == 4
    assert np.all(d == 0.0)


def test_a_time_maps_into_a_matrix_by_proportion():
    assert time_to_index(0.0, duration_s=100.0, n=10) == 0
    assert time_to_index(50.0, duration_s=100.0, n=10) == 5
    assert time_to_index(100.0, duration_s=100.0, n=10) == 9   # clamped inside


def test_a_time_beyond_the_recording_is_clamped_not_wrapped():
    """Annotations shifted from another clock can land outside; wrapping would put a
    boundary at the beginning of the session and look entirely plausible."""
    assert time_to_index(500.0, duration_s=100.0, n=10) == 9
    assert time_to_index(-5.0, duration_s=100.0, n=10) == 0

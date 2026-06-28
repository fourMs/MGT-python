"""Tests for the space-time module and its shared frame-decode caching (issue #347).

The space-time analyses (stroboscope, silhouette_waterfall, spacetime_volume) all need the
same average background frame. Computing it decodes the whole video, so it is cached per
MgVideo (keyed by filename) and reused across chained calls instead of being recomputed.
"""
from __future__ import annotations

import numpy as np
import pytest

import musicalgestures
from musicalgestures import _spacetime


@pytest.fixture(scope="module")
def short_clip(tmp_path_factory):
    target = str(tmp_path_factory.mktemp("spacetime")).replace("\\", "/") + "/clip.avi"
    return musicalgestures._utils.extract_subclip(
        musicalgestures.examples.dance, 5, 6, target_name=target)


def test_average_frame_shape_and_dtype(short_clip):
    mg = musicalgestures.MgVideo(short_clip)
    avg = _spacetime._average_frame(mg)
    assert avg.shape == (mg.height, mg.width, 3)
    assert avg.dtype == np.uint8


def test_average_frame_is_cached(short_clip):
    """The second call must reuse the cache rather than re-decoding the video."""
    mg = musicalgestures.MgVideo(short_clip)
    first = _spacetime._average_frame(mg)
    assert getattr(mg, "_avg_frame_cache", None) is not None
    assert mg._avg_frame_cache[0] == mg.filename

    # If the cache is honoured, decoding never happens again — make that fatal to prove it.
    def _boom(self):
        raise AssertionError("video was re-decoded despite a valid average-frame cache")

    original = _spacetime._iter_frames
    _spacetime._iter_frames = _boom
    try:
        second = _spacetime._average_frame(mg)
    finally:
        _spacetime._iter_frames = original

    np.testing.assert_array_equal(first, second)


def test_average_frame_cache_invalidated_on_filename_change(short_clip):
    mg = musicalgestures.MgVideo(short_clip)
    _spacetime._average_frame(mg)
    mg._avg_frame_cache = ("/some/other/file.avi", np.zeros((mg.height, mg.width, 3), np.uint8))
    # Stale key → recompute (and refresh the cache to the real filename).
    avg = _spacetime._average_frame(mg)
    assert mg._avg_frame_cache[0] == mg.filename
    assert avg.dtype == np.uint8

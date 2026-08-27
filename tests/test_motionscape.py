"""A Sapp-style scape: the same curve summarised at every timescale at once.

In a keyscape each row is a window length and each cell the best-matching key for that
window, so structure that only exists at one scale becomes visible as a shape. The same
construction over quantity of motion answers "is this recording one long even stretch, or
a few busy patches, and at what scale does that impression change".

The tests pin the geometry (a row per scale, the top row summarising everything) and the
one property that makes it a scape rather than a picture: a burst confined to part of the
recording must stay confined at fine scales and spread as the windows lengthen.
"""
import numpy as np
import pytest

from musicalgestures._motionvectors import motion_scape


class Test_geometry:
    def test_one_row_per_scale_and_full_width(self):
        q = np.random.default_rng(0).random(500)
        scape = motion_scape(q, n_scales=20)
        assert scape.shape == (20, 500)

    def test_the_coarsest_row_is_one_value_for_the_whole_recording(self):
        q = np.concatenate([np.ones(250), np.zeros(250)])
        scape = motion_scape(q, n_scales=16)
        defined = scape[0][~np.isnan(scape[0])]
        assert len(defined) >= 1
        assert np.allclose(defined, q.mean(), atol=0.02)

    def test_it_is_a_triangle_not_a_rectangle(self):
        """Each row is only as wide as the number of places its window can sit."""
        q = np.random.default_rng(1).random(800)
        scape = motion_scape(q, n_scales=24)
        widths = [int((~np.isnan(row)).sum()) for row in scape]
        assert widths[0] < widths[-1]
        assert widths == sorted(widths)

    def test_the_finest_row_follows_the_signal(self):
        q = np.concatenate([np.ones(250), np.zeros(250)])
        scape = motion_scape(q, n_scales=16)
        assert scape[-1][:200].mean() > scape[-1][-200:].mean() + 0.5


class Test_it_shows_scale:
    def test_a_short_burst_stays_local_at_fine_scales_and_spreads_at_coarse(self):
        q = np.zeros(1000)
        q[480:520] = 1.0
        scape = motion_scape(q, n_scales=24)
        fine, coarse = scape[-1], scape[2]

        def width(row):
            lit = row > np.nanmax(row) / 2
            return int(np.nansum(lit))

        assert width(fine) < width(coarse)

    def test_an_even_signal_looks_the_same_at_every_scale(self):
        q = np.full(600, 0.4)
        scape = motion_scape(q, n_scales=12)
        assert np.nanstd(scape) < 1e-6

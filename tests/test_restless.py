"""Which pixels change all the time, whether or not anybody is there.

A screen showing a video call, a window onto a street, a flickering lamp: all of them put
motion into a recording that has nothing to do with the person being studied. Quantity of
motion counts them, and on this project's corpus a screen showing the far room raised one
recording's motion floor enough to compress its dynamic range and defeat its segmentation.

The distinction that makes this work: **a screen changes in nearly every frame, a dancer
occupies a given pixel occasionally.** So the median absolute deviation over sampled frames
separates them where the maximum cannot --- a pixel a dancer crossed twice has a large
maximum and a small median, and a pixel showing a screen has both.
"""
import numpy as np
import pytest

from musicalgestures._plate import restless_map, restless_regions


def test_a_pixel_that_never_changes_is_not_restless():
    stack = np.full((20, 4, 4), 100.0)
    assert restless_map(stack).max() == pytest.approx(0.0)


def test_a_pixel_changing_in_every_frame_is_restless():
    stack = np.full((20, 4, 4), 100.0)
    stack[:, 1, 1] = np.linspace(0, 200, 20)
    m = restless_map(stack)
    assert m[1, 1] > 10.0
    assert m[0, 0] == pytest.approx(0.0)


def test_a_pixel_crossed_occasionally_is_not_restless():
    """The distinction the whole thing rests on: a dancer is occasional, a screen is not.

    A maximum-based measure calls both of these restless, which would mask the dancer
    along with the screen --- and masking the thing you are studying is worse than not
    masking anything.
    """
    stack = np.full((20, 4, 4), 100.0)
    stack[3, 2, 2] = 250.0          # crossed once
    stack[11, 2, 2] = 250.0         # and once more
    m = restless_map(stack)
    assert m[2, 2] == pytest.approx(0.0)


def test_regions_are_returned_as_a_boolean_mask_of_the_frame():
    stack = np.full((20, 8, 8), 100.0)
    stack[:, 1:3, 1:3] = np.linspace(0, 200, 20)[:, None, None]
    mask = restless_regions(stack, quantile=0.9)
    assert mask.shape == (8, 8)
    assert mask.dtype == bool
    assert mask[1, 1] and not mask[6, 6]


def test_sensor_noise_alone_yields_no_restless_region():
    """The absolute floor, and the case that exercises it.

    A quantile on its own always marks its top slice, however small the numbers under it.
    A room with nobody in it still has sensor noise, so without a floor every still
    recording comes back with two per cent of itself masked. Written first against a
    perfectly flat stack, where the map is all zeros and the quantile is zero too --- which
    passes whether or not the floor exists, and therefore tested nothing.
    """
    rng = np.random.default_rng(3)
    stack = np.full((30, 8, 8), 50.0) + rng.normal(0, 0.3, (30, 8, 8))
    assert restless_regions(stack, quantile=0.9, min_value=2.0).sum() == 0
    assert restless_regions(stack, quantile=0.9, min_value=0.0).sum() > 0


def test_the_quietest_pixel_is_never_masked():
    """Even on a frame where everything moves. The cut is at least the map's own minimum,
    so masking can never take the whole frame and leave no signal behind."""
    rng = np.random.default_rng(0)
    stack = rng.normal(100, 40, (25, 8, 8))
    for q in (0.0, 0.5, 0.98):
        mask = restless_regions(stack, quantile=q, min_value=0.0)
        assert mask.sum() < mask.size

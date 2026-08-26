"""Which of ambiscape's features cross into MGT, and in what shape.

The adapter surfaced one number --- level --- out of twenty-five available, so a room could
be described as loud or quiet and nothing else. A soundscape vocabulary needs level, the
shape of the spectrum, how tonal or noisy it is, and where the energy sits by band.

The crossing is a dict-to-dict transformation with a right answer, so it is a function of
its own and is tested here without ambiscape present. Everything must come out on the same
1 Hz grid, because the point of this adapter is that motion and sound series join.
"""
import numpy as np
import pytest

from musicalgestures._soundscape import features_from_ambiscape


def fake(n=5, n_bands=10):
    return {
        "t": np.arange(n, dtype=float),
        "rms_w": np.full(n, 0.1),
        "centroid": np.full(n, 1200.0),
        "flatness": np.full(n, 0.3),
        "oct_pow": np.tile(np.arange(1, n_bands + 1, dtype=float), (n, 1)),
    }


def test_level_is_decibels_not_amplitude():
    out = features_from_ambiscape(fake())
    assert out["aud_level_db"][0] == pytest.approx(20 * np.log10(0.1), abs=1e-6)


def test_a_silent_block_does_not_become_negative_infinity():
    """log10(0) is -inf, which poisons every mean and plot downstream."""
    f = fake()
    f["rms_w"] = np.zeros(5)
    out = features_from_ambiscape(f)
    assert np.all(np.isfinite(out["aud_level_db"]))


def test_each_octave_band_becomes_its_own_named_series():
    out = features_from_ambiscape(fake())
    bands = [k for k in out if k.startswith("aud_oct")]
    assert len(bands) == 10
    assert all(len(out[b]) == 5 for b in bands)


def test_every_series_is_on_the_same_grid():
    """The whole point of the adapter is that these join a motion series."""
    out = features_from_ambiscape(fake(n=7))
    assert {len(v) for v in out.values()} == {7}


def test_centroid_and_flatness_cross_unchanged():
    out = features_from_ambiscape(fake())
    assert out["aud_centroid"][0] == pytest.approx(1200.0)
    assert out["aud_flatness"][0] == pytest.approx(0.3)


def test_a_missing_optional_feature_is_skipped_not_faked():
    """ambiscape's set depends on the recording's channel layout. A mono file has no
    directional features, and inventing zeros for them would read as 'measured, front'."""
    f = fake()
    del f["centroid"]
    out = features_from_ambiscape(f)
    assert "aud_centroid" not in out
    assert "aud_level_db" in out


def test_the_only_required_feature_is_level():
    with pytest.raises(KeyError):
        features_from_ambiscape({"t": np.arange(3.0)})

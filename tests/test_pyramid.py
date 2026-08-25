"""build_pyramid and read_columns shipped in 1.14.2 with no tests and have never
produced output.

The property that matters is CONTAINMENT OF THE EXTREME. A pyramid exists so that a
movement lasting a few frames is still visible when the whole session is on one
screen, and a decimation that averages is exactly what makes such a movement vanish.
A plausibility check passes either way; these do not.
"""
import json

import numpy as np
import pytest

from musicalgestures._tracks import build_pyramid, read_columns


def _base(tmp_path, n=1024, span=8, spike_at=37, spike_val=255):
    """A videogram base that is flat except for one bright column.

    `n` must exceed `MIN_LEVEL_COLUMNS` (64) or no level is written at all and every
    assertion here is vacuous --- the first version of this fixture used exactly 64
    and produced an empty pyramid that looked like a bug in `build_pyramid`.
    """
    d = tmp_path / "analysis"
    d.mkdir()
    arr = np.full((n, span), 10, dtype=np.uint8)
    arr[spike_at, :] = spike_val
    arr.tofile(d / "videogram_v.u1")
    (d / "tracks.json").write_text(json.dumps({
        "frames": n, "fps": 10.0, "width": span, "height": span,
        "duration_s": n / 10.0,
        "qom": "qom.f4", "videogram_v": "videogram_v.u1",
        "videogram_h": "videogram_h.u1"}))
    return d


def test_the_spike_survives_every_level(tmp_path):
    """This is the whole point of the pyramid, so it is the first assertion."""
    d = _base(tmp_path)
    levels = build_pyramid(d, which="videogram_v")
    assert levels, "no levels written"
    for p in levels:
        arr = np.fromfile(p, dtype=np.uint8)
        assert arr.max() == 255, f"the spike was lost at {p.name}"


def test_decimation_invents_no_value_that_was_not_there(tmp_path):
    """Guard on the guard, and it must be a property averaging actually violates.

    The first version asserted the background stayed at 10, which is true under a
    mean as well --- it passed against the mutation it was written to catch. Taking
    the max of a set returns a MEMBER of that set, so every value at every level must
    be one that existed in the base. A mean manufactures a value that was never in the
    data, which is the whole objection to it: the column reads 25 where nothing was
    ever 25.
    """
    d = _base(tmp_path)
    levels = build_pyramid(d, which="videogram_v")
    for p in levels:
        values = set(np.unique(np.fromfile(p, dtype=np.uint8)).tolist())
        assert values <= {10, 255}, f"{p.name} invented {sorted(values - {10, 255})}"


def test_each_level_halves_the_columns(tmp_path):
    d = _base(tmp_path, n=1024, span=8)
    levels = build_pyramid(d, which="videogram_v")
    counts = [np.fromfile(p, dtype=np.uint8).size // 8 for p in levels]
    assert counts == [512, 256, 128, 64], counts


def test_pyramid_is_recorded_in_tracks_json(tmp_path):
    d = _base(tmp_path)
    build_pyramid(d, which="videogram_v")
    meta = json.loads((d / "tracks.json").read_text())
    assert meta["pyramid"]["videogram_v"], "a level a reader cannot find is not written"


def test_read_columns_returns_the_slice_asked_for(tmp_path):
    d = _base(tmp_path, n=1024, span=8, spike_at=37)
    build_pyramid(d, which="videogram_v")
    #: max_columns high enough to force level 0, so the answer is exact.
    cols, spc = read_columns(d, start_s=3.0, end_s=4.0, max_columns=10000)
    assert cols.shape == (10, 8), cols.shape
    assert spc == pytest.approx(0.1)
    #: frame 37 is at t=3.7 s, i.e. index 7 of this slice.
    assert cols[7].max() == 255


def test_read_columns_coarsens_when_the_display_is_narrow(tmp_path):
    d = _base(tmp_path, n=1024, span=8)
    build_pyramid(d, which="videogram_v")
    cols, spc = read_columns(d, start_s=0.0, end_s=6.4, max_columns=8)
    assert cols.shape[0] <= 16, cols.shape
    assert spc > 0.1, "no coarsening happened; the pyramid was not used"
    assert cols.max() == 255, "the spike vanished on the way to the screen"

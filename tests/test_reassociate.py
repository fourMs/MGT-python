"""Fragment re-association's validation tiers, from the 2026-08-30 design.

The associator may use position and time only, so its honesty hinges on one
behaviour: a crossing at a fragment boundary yields a recorded break, never a
guess. The synthetic walkers make that exact assertion testable.
"""
import numpy as np
import pytest

from musicalgestures._posetools import associate_fragments

FPS = 25.0


def walker_tracks(cuts_a=(), cuts_b=(), seconds=20.0, cross=True):
    """Two walkers, fragmented at the asked times.

    Walker A runs left-to-right and back; B the mirror. With `cross` they meet
    at the centre twice per period; fragments are cut wherever `cuts_*` say.
    """
    t = np.arange(0, seconds, 1 / FPS)
    xa = 320 + 200 * np.sin(2 * np.pi * t / 20.0)
    xb = 320 - 200 * np.sin(2 * np.pi * t / 20.0) if cross else xa - 250
    tracks, tid = {}, 1

    def add(x, cuts):
        nonlocal tid
        edges = [0] + [int(c * FPS) for c in cuts] + [len(t)]
        for a, b in zip(edges[:-1], edges[1:]):
            lm = np.zeros((b - a, 17, 3))
            lm[:, :, 0] = x[a:b, None] + np.linspace(-20, 20, 17)
            lm[:, :, 1] = 180 + np.linspace(-60, 60, 17)
            lm[:, :, 2] = 0.9
            tracks[tid] = {"time": t[a:b], "frame": np.arange(a, b),
                           "landmarks": lm}
            tid += 1
        return

    add(xa, cuts_a)
    add(xb, cuts_b)
    return {"tracks": tracks, "n_frames": len(t), "fps": FPS,
            "width": 640, "height": 360,
            "names": ["p"] * 17}


class TestChaining:
    def test_cuts_away_from_crossings_rechain_perfectly(self):
        """The walkers cross at t=10; cuts at 4 and 16 are unambiguous."""
        r = associate_fragments(walker_tracks(cuts_a=(4.0,), cuts_b=(16.0,)))
        assert len(r["breaks"]) == 0
        assert len(r["segments"]) == 1
        movers = r["segments"][0]["movers"]
        assert len(movers) == 2
        #: Each mover's trajectory must be one walker, not a mixture: walker A
        #: starts at the centre heading right, so its x at t=5 is near 320+200.
        for m in movers.values():
            x5 = m["landmarks"][np.argmin(np.abs(m["time"] - 5.0)), 8, 0]
            x15 = m["landmarks"][np.argmin(np.abs(m["time"] - 15.0)), 8, 0]
            #: A pure walker is on OPPOSITE sides at t=5 and t=15; a mixed
            #: chain would sit on the same side twice.
            assert (x5 - 320) * (x15 - 320) < 0

    def test_a_cut_at_a_simultaneous_crossing_is_a_break_not_a_guess(self):
        """Both walkers cut exactly where they meet: position cannot say which
        continuation is which, and the design demands a recorded break."""
        r = associate_fragments(walker_tracks(cuts_a=(10.0,), cuts_b=(10.0,)))
        assert len(r["breaks"]) >= 1
        assert any(b["reason"] == "ambiguous" for b in r["breaks"])

    def test_overlapping_fragments_are_different_movers(self):
        r = associate_fragments(walker_tracks())
        movers = r["segments"][0]["movers"]
        assert len(movers) == 2
        t0 = {m: (v["time"][0], v["time"][-1]) for m, v in movers.items()}
        a, b = t0.values()
        assert a[0] < b[1] and b[0] < a[1]   # they overlap in time

    def test_a_gap_too_long_breaks_the_chain(self):
        """A walker who vanishes for longer than max_gap_s cannot be silently
        resumed."""
        tracks = walker_tracks(cuts_a=(8.0, 12.0))
        del tracks["tracks"][2]              # remove A's middle fragment: 4 s hole
        r = associate_fragments(tracks, max_gap_s=2.0)
        assert len(r["breaks"]) >= 1

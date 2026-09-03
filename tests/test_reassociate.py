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


class TestAppearance:
    """The v2 rules: appearance bridges what position cannot, and refusal stays.

    Embeddings are supplied directly here; their extraction from video has its
    own test. Walker A wears embedding [1,0], walker B [0,1] --- fully separable
    --- and the identical-appearance cases assert that nothing links on
    appearance that appearance cannot actually tell apart.
    """

    @staticmethod
    def _embeddings(tracks, a_ids, vec_a=(1.0, 0.0), vec_b=(0.0, 1.0)):
        return {k: np.array(vec_a if k in a_ids else vec_b)
                for k in tracks["tracks"]}

    def test_appearance_links_the_crossing_cut(self):
        """The v1 refusal case: both walkers cut at their crossing. With
        separable appearances the continuation is decidable, and must link."""
        tr = walker_tracks(cuts_a=(10.0,), cuts_b=(10.0,))
        emb = self._embeddings(tr, a_ids={1, 2})
        r = associate_fragments(tr, embeddings=emb)
        assert len(r["breaks"]) == 0
        assert len(r["segments"]) == 1

    def test_identical_appearance_still_breaks_at_the_crossing(self):
        tr = walker_tracks(cuts_a=(10.0,), cuts_b=(10.0,))
        emb = self._embeddings(tr, a_ids=set(tr["tracks"]))   # everyone alike
        r = associate_fragments(tr, embeddings=emb)
        assert any(b["reason"] == "ambiguous" for b in r["breaks"])

    def test_appearance_bridges_a_gap_position_refused(self):
        tr = walker_tracks(cuts_a=(8.0, 12.0))
        del tr["tracks"][2]                    # 4 s hole in walker A
        emb = self._embeddings(tr, a_ids={1, 3})
        r = associate_fragments(tr, embeddings=emb, max_gap_s=2.0)
        assert len(r["breaks"]) == 0


class TestChains:
    """v2.1: appearance links mover-chains ACROSS breaks, or refuses to."""

    @staticmethod
    def _held_apart(appearance_gap=1.0):
        """Both walkers vanish for 5 s: a break no rule at fragment level can
        bridge (position: gap > max_gap_s; appearance: gap > appearance_max_gap_s),
        so the associator must produce two segments."""
        tr = walker_tracks(cuts_a=(8.0, 13.0), cuts_b=(8.0, 13.0))
        del tr["tracks"][2]
        del tr["tracks"][5]
        return tr

    def test_distinct_appearance_links_chains_across_the_break(self):
        tr = self._held_apart()
        emb = TestAppearance._embeddings(tr, a_ids={1, 3})
        r = associate_fragments(tr, embeddings=emb, max_gap_s=2.0,
                                appearance_max_gap_s=1.0)
        assert len(r["segments"]) == 2
        assert len(r["chains"]) == 2
        for chain in r["chains"].values():
            segs = {m[0] for m in chain["members"]}
            assert segs == {0, 1}
            assert chain["coverage_s"] == pytest.approx(15.0, abs=0.5)

    def test_identical_appearance_starts_new_chains_at_the_break(self):
        tr = self._held_apart()
        emb = TestAppearance._embeddings(tr, a_ids=set(tr["tracks"]))
        r = associate_fragments(tr, embeddings=emb, max_gap_s=2.0,
                                appearance_max_gap_s=1.0)
        assert len(r["segments"]) == 2
        assert len(r["chains"]) == 4          # nothing linked, nothing guessed

    def test_chain_ids_are_exclusive_within_a_segment(self):
        tr = self._held_apart()
        emb = TestAppearance._embeddings(tr, a_ids={1, 3})
        r = associate_fragments(tr, embeddings=emb, max_gap_s=2.0,
                                appearance_max_gap_s=1.0)
        for seg in r["segments"]:
            ids = [m["chain"] for m in seg["movers"].values()]
            assert len(ids) == len(set(ids))

    def test_no_embeddings_means_no_chains_key(self):
        tr = walker_tracks(cuts_a=(10.0,))
        r = associate_fragments(tr)
        assert "chains" not in r
        assert all("chain" not in m for seg in r["segments"]
                   for m in seg["movers"].values())


class TestFragmentEmbeddings:
    def test_two_coloured_bodies_get_separable_embeddings(self, tmp_path):
        """A red body and a blue body, two fragments each: same-colour fragments
        must embed closer than cross-colour ones."""
        import subprocess

        import cv2

        from musicalgestures._posetools import fragment_embeddings

        path = str(tmp_path / "two.mp4")
        w, h, n = 320, 240, 40
        raw = tmp_path / "raw.rgb"
        with open(raw, "wb") as fh:
            for i in range(n):
                img = np.full((h, w, 3), 40, np.uint8)
                img[80:200, 40+i:100+i] = (200, 30, 30)      # red walker
                img[80:200, 220-i:280-i] = (30, 30, 200)     # blue walker
                fh.write(img.tobytes())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", "10",
                        "-i", str(raw), "-pix_fmt", "yuv420p", path], check=True)

        def frag(tid, frames, x_of):
            lm = np.zeros((len(frames), 17, 3))
            for j, fi in enumerate(frames):
                cx = x_of(fi)
                lm[j, :, 0] = cx
                lm[j, [5, 6], 0] = (cx - 20, cx + 20)
                lm[j, [11, 12], 0] = (cx - 15, cx + 15)
                lm[j, [5, 6], 1] = 100
                lm[j, [11, 12], 1] = 170
                lm[j, :, 1] = np.clip(lm[j, :, 1], 90, 190)
                lm[j, :, 2] = 0.9
            return {"time": np.asarray(frames) / 10.0,
                    "frame": np.asarray(frames), "landmarks": lm}

        tracks = {"tracks": {
            1: frag(1, range(0, 18), lambda i: 70 + i),
            2: frag(2, range(22, 40), lambda i: 70 + i),
            3: frag(3, range(0, 18), lambda i: 250 - i),
            4: frag(4, range(22, 40), lambda i: 250 - i)},
            "n_frames": n, "fps": 10.0, "width": w, "height": h, "names": []}

        emb = fragment_embeddings(path, tracks)
        assert set(emb) == {1, 2, 3, 4}
        d_same = np.linalg.norm(emb[1] - emb[2]) + np.linalg.norm(emb[3] - emb[4])
        d_cross = np.linalg.norm(emb[1] - emb[3]) + np.linalg.norm(emb[2] - emb[4])
        assert d_same < 0.5 * d_cross

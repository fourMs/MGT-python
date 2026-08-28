"""Many moments of one recording in a single frame.

A chronophotograph: the room recovered as a plate, bodies cut out of frames spread
through the recording, and all of them laid back onto it. One picture then carries where
somebody was, how they were shaped and how far apart the moments were, which no gram
shows.

**Frames are chosen for separation, not at regular intervals.** Evenly spaced frames put
bodies on top of each other as often as not, and overlapping silhouettes read as one
smear rather than as two moments. That is the part worth testing: the compositing is
arithmetic, the choosing is the design.
"""
import numpy as np
import pytest

from musicalgestures._multishot import choose_spaced, multishot


def test_the_choice_spreads_over_the_frame_rather_than_taking_neighbours():
    """Five candidates, three of them in one corner. Two of those must not both win."""
    candidates = [{"centroid": (10.0, 10.0), "area": 0.05, "index": 0},
                  {"centroid": (12.0, 11.0), "area": 0.05, "index": 1},
                  {"centroid": (11.0, 12.0), "area": 0.05, "index": 2},
                  {"centroid": (300.0, 200.0), "area": 0.05, "index": 3},
                  {"centroid": (150.0, 100.0), "area": 0.05, "index": 4}]
    chosen = choose_spaced(candidates, 3)
    assert len(chosen) == 3
    corner = [c for c in chosen if c["centroid"][0] < 50]
    assert len(corner) == 1, "two bodies came from the same corner"


def test_asking_for_more_bodies_than_there_are_candidates_gives_what_there_is():
    candidates = [{"centroid": (10.0, 10.0), "area": 0.05, "index": 0},
                  {"centroid": (99.0, 99.0), "area": 0.05, "index": 1}]
    assert len(choose_spaced(candidates, 8)) == 2


def test_the_chosen_frames_come_back_in_time_order():
    """A composite lays later bodies over earlier ones, so the order is not cosmetic."""
    candidates = [{"centroid": (300.0, 200.0), "area": 0.05, "index": 90},
                  {"centroid": (10.0, 10.0), "area": 0.05, "index": 10},
                  {"centroid": (150.0, 100.0), "area": 0.05, "index": 50}]
    chosen = choose_spaced(candidates, 3)
    assert [c["index"] for c in chosen] == sorted(c["index"] for c in chosen)


def _walker(path, positions, size=(320, 240), body=(40, 70), frames=40):
    """A coherent solid body crossing a textured room, and why not `moving_block_video`.

    That helper's block is randomly TEXTURED, so its mean brightness matches the
    background it crosses. A frame difference against the plate then comes out as
    speckle, and the morphological open that removes sensor noise erodes it to nothing:
    the mask is empty and every frame is rejected. It is the right fixture for motion
    vectors, which care about displacement, and the wrong one for figure-ground
    separation, which cares about a body being distinguishable from a room.
    """
    import subprocess

    W, H = size
    bw, bh = body
    rng = np.random.default_rng(11)
    background = rng.integers(60, 140, size=(H, W), dtype=np.uint8)
    raw = bytearray()
    for i in range(frames):
        frame = background.copy()
        x = positions[i * len(positions) // frames]
        y = H // 2 - bh // 2
        frame[y:y + bh, x:x + bw] = 240          # solid, so it survives the open
        raw += frame.tobytes()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
                    "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", "25", "-i", "pipe:0",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "5", str(path)],
                   input=bytes(raw), check=True)
    return str(path)


@pytest.fixture(scope="module")
def travelling(tmp_path_factory):
    """A body at four well-separated stations, so a count is checkable."""
    stations = [40, 120, 200, 260]
    return _walker(tmp_path_factory.mktemp("ms") / "walk.mp4",
                   [s for s in stations for _ in range(10)])


def test_the_body_count_is_what_was_asked_for(travelling):
    """Two bodies and four bodies, counted in the picture rather than trusted.

    The body stands at four stations 80 px apart and is 40 wide, so all four fit without
    touching. Counting connected components is what distinguishes a composite that placed
    three from one that placed three on top of each other.
    """
    import cv2

    for wanted in (2, 3):
        picture, plate = multishot(travelling, n_bodies=wanted, width=320)
        changed = (np.abs(picture.astype(np.int16)
                          - plate.astype(np.int16)).max(axis=2) > 20).astype(np.uint8)
        n, _, stats, _ = cv2.connectedComponentsWithStats(changed, 8)
        big = sum(1 for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > 300)
        assert big == wanted, f"asked for {wanted}, the picture holds {big}"


def test_more_bodies_covers_more_of_the_frame(travelling):
    two, plate = multishot(travelling, n_bodies=2, width=320)
    four, _ = multishot(travelling, n_bodies=3, width=320)

    def covered(p):
        return float((np.abs(p.astype(np.int16) - plate.astype(np.int16)).max(axis=2)
                      > 20).mean())

    assert covered(four) > covered(two) * 1.2


def test_a_recording_with_nobody_in_it_returns_nothing_to_composite(tmp_path):
    """Not an empty picture of the room, which would look like a result."""
    import subprocess

    W, H = 160, 120
    rng = np.random.default_rng(7)
    background = rng.integers(48, 160, size=(H, W), dtype=np.uint8)
    raw = b"".join(background.tobytes() for _ in range(40))
    path = str(tmp_path / "empty.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
                    "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", "25", "-i", "pipe:0",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", path],
                   input=raw, check=True)
    picture, _ = multishot(path, n_bodies=4, width=W)
    assert picture is None


def test_the_body_size_bounds_can_be_moved_for_a_different_framing(travelling):
    """Generalisable across videos, tuned for humans at studio distance.

    The defaults describe a whole person filling 0.4 to 6 per cent of the frame. A closer
    camera, a wider room or a seated subject breaks that, and the failure is silent --- no
    candidate matches, and an empty result looks like an empty room rather than like a
    bound that matched nothing. So the bounds are arguments.
    """
    impossible, _ = multishot(travelling, n_bodies=2, width=320,
                              min_area=0.30, max_area=0.40)
    assert impossible is None, "a bound matching nothing should return nothing"

    generous, _ = multishot(travelling, n_bodies=2, width=320,
                            min_area=0.0005, max_area=0.9)
    assert generous is not None


def test_it_is_reachable_as_a_method_like_every_other_view(travelling):
    """`room_plate` and `multishot` were the only views that were not methods.

    Everything a student reaches for is `mgv.motiongrams()`, `mgv.stroboscope()`. A view
    that is a module-level function taking a path does not compose with the rest and is
    invisible to anyone browsing the object API --- which is how `stroboscope` came to be
    overlooked while a second chronophotography function was written.
    """
    import os

    import musicalgestures

    image = musicalgestures.MgVideo(travelling).multishot(n_bodies=3, width=320)
    assert isinstance(image, musicalgestures.MgImage)
    assert os.path.exists(image.filename)


def test_the_room_is_reachable_as_a_method_too(travelling):
    import os

    import musicalgestures

    image = musicalgestures.MgVideo(travelling).plate(width=320)
    assert isinstance(image, musicalgestures.MgImage)
    assert os.path.exists(image.filename)


def test_the_method_passes_the_body_count_through(travelling):
    import cv2

    import musicalgestures

    plate = cv2.imread(musicalgestures.MgVideo(travelling).plate(width=320).filename)
    counts = []
    for wanted in (2, 3):
        picture = cv2.imread(musicalgestures.MgVideo(travelling)
                             .multishot(n_bodies=wanted, width=320).filename)
        changed = (np.abs(picture.astype(np.int16) - plate.astype(np.int16)).max(axis=2)
                   > 20).astype(np.uint8)
        n, _, stats, _ = cv2.connectedComponentsWithStats(changed, 8)
        counts.append(sum(1 for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > 300))
    assert counts == [2, 3]

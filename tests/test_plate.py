"""The empty room, and where the people are relative to it.

A long recording of a room contains the room. Recovering it gives you two things: a
background to subtract, and an occupancy signal saying where in the frame anybody was and
how much of it they filled --- which is a different question from quantity of motion, and
answers things motion cannot. A dancer standing still has no motion and plenty of occupancy.

**Median, not mean.** A mean over frames keeps a faint ghost of the dancers everywhere they
went, and subtracting a ghost leaves holes shaped like people. The median throws away
anything present in fewer than half the samples, which is exactly what a person crossing a
room is.

**Then refine once.** A median over a blind sample is contaminated wherever somebody stood
still for most of the recording. Re-taking it over the frames that least resemble the first
plate --- the emptiest ones --- removes that.
"""
import numpy as np
import pytest

from musicalgestures._plate import (occupancy_from_plate, plate_from_stack,
                                    refine_indices, sample_frame_indices)


def test_sampled_indices_cover_the_whole_recording():
    idx = sample_frame_indices(10000, 50)
    assert len(idx) == 50
    assert idx[0] < 500 and idx[-1] > 9500
    assert list(idx) == sorted(idx)


def test_asking_for_more_samples_than_frames_gives_every_frame_once():
    idx = sample_frame_indices(10, 500)
    assert list(idx) == list(range(10))


def test_the_plate_is_the_median_not_the_mean():
    """Three frames where a bright object sits in one. A mean keeps a third of it."""
    stack = np.zeros((3, 4, 4), dtype=float)
    stack[1, 1, 1] = 300.0
    plate = plate_from_stack(stack)
    assert plate[1, 1] == pytest.approx(0.0)


def test_something_present_in_most_frames_stays_in_the_plate():
    """A chair is part of the room. Only what is usually absent should go."""
    stack = np.zeros((5, 4, 4), dtype=float)
    stack[:, 2, 2] = 200.0
    stack[0, 2, 2] = 0.0
    plate = plate_from_stack(stack)
    assert plate[2, 2] == pytest.approx(200.0)


def test_occupancy_is_the_fraction_of_the_frame_that_differs():
    plate = np.zeros((10, 10))
    frame = np.zeros((10, 10))
    frame[:5, :] = 100.0
    assert occupancy_from_plate(frame, plate, threshold=10.0) == pytest.approx(0.5)


def test_an_empty_room_has_no_occupancy():
    plate = np.full((8, 8), 42.0)
    assert occupancy_from_plate(plate.copy(), plate, threshold=10.0) == pytest.approx(0.0)


def test_noise_below_the_threshold_is_not_occupancy():
    """Sensor noise is everywhere; without a threshold every frame is fully occupied."""
    rng = np.random.default_rng(0)
    plate = np.full((32, 32), 100.0)
    frame = plate + rng.normal(0, 2.0, plate.shape)
    assert occupancy_from_plate(frame, plate, threshold=10.0) < 0.01


def test_refinement_keeps_the_emptiest_frames():
    diffs = np.array([0.9, 0.1, 0.8, 0.05, 0.5])
    keep = refine_indices(diffs, keep_fraction=0.4)
    assert set(keep) == {1, 3}


def test_refinement_always_keeps_at_least_two_frames():
    """A median of one frame is that frame, which is not a plate."""
    keep = refine_indices(np.array([0.5, 0.2, 0.9]), keep_fraction=0.01)
    assert len(keep) >= 2


def test_refinement_spreads_across_the_recording_instead_of_taking_one_stretch():
    """The emptiest frames cluster in whatever stretch nobody was working.

    On a real recording a stepladder stood still through a ten-minute break in a
    two-hour session. Those frames were the emptiest by a wide margin, the refinement
    took all of them, and the ladder became part of "the room" for every occupancy
    figure afterwards. Spreading the choice is what stops one stretch deciding the plate.
    """
    from musicalgestures._plate import refine_indices

    diffs = np.full(100, 0.5)
    diffs[70:80] = 0.01                      # one very empty stretch
    kept = refine_indices(diffs, keep_fraction=0.10, stratify=True)
    assert not all(70 <= i < 80 for i in kept), "every frame came from the one stretch"
    assert max(kept) - min(kept) > 50, "the chosen frames do not span the recording"


def test_the_unstratified_choice_is_still_available_and_still_takes_the_emptiest():
    from musicalgestures._plate import refine_indices

    diffs = np.full(100, 0.5)
    diffs[70:80] = 0.01
    kept = refine_indices(diffs, keep_fraction=0.10, stratify=False)
    assert all(70 <= i < 80 for i in kept)


def test_plate_spread_tells_a_clustered_choice_from_a_spread_one():
    from musicalgestures._plate import plate_spread

    assert plate_spread(np.arange(70, 80), 100) < 0.2
    assert plate_spread(np.arange(0, 100, 10), 100) > 0.8


def test_a_prop_standing_through_a_quiet_stretch_stays_out_of_the_room(tmp_path):
    """The stepladder, in miniature, and the test asserts BOTH directions.

    An object present only while nothing else moves. The old unstratified choice draws
    every frame from that one stretch and takes the prop into the room with it; the
    stratified one spreads across the recording and leaves it out. Asserting only the
    second would pass whether or not the fix did anything --- three earlier versions of
    this fixture did exactly that, because the moving block crossed the prop's location,
    or was wide enough to enter the first-pass plate itself.

    **The gap between the two stretches has to be enormous, not merely present.** A
    fourth version used a block of 2000 px against a 625 px prop and passed on Linux and
    Windows and failed on macOS, where a different x264 build's ringing was enough to
    change which frames came out emptiest. At 19 per cent against 0.8 the ordering is a
    property of the scene rather than of the encoder.

    **And the block has to CLEAR each column.** A fifth version made it big by making it
    wide, in a frame narrow enough that it covered the middle columns in nearly every
    busy frame -- so the block entered the first-pass plate itself, and the busy frames
    then read as the empty ones. Big and transient, which needs a wider frame.
    """
    import subprocess
    import warnings

    W, H, frames = 320, 240, 90
    rng = np.random.default_rng(3)
    background = rng.integers(48, 160, size=(H, W), dtype=np.uint8)
    raw = bytearray()
    for i in range(frames):
        frame = background.copy()
        if i >= 60:                          # the quiet stretch: a prop, and nothing else
            frame[200:225, 260:285] = 250    # 625 px, 0.8 per cent, clear of the block
        else:                                # the busy stretch: a big, TRANSIENT block
            x = int(i * 4)                   # 14400 px, 19 per cent, and it clears any
            frame[0:180, x:x + 80] = 250     # column in 20 frames of 60
        raw += frame.tobytes()
    path = str(tmp_path / "prop.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
                    "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", "25", "-i", "pipe:0",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "5", path],
                   input=bytes(raw), check=True)

    from musicalgestures._plate import room_plate

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        clustered, used = room_plate(path, n_samples=60, width=W, stratify=False)
    assert clustered[203:222, 263:282].mean() > 200, "the fixture does not reproduce the bug"
    #: The claim is that every chosen frame comes from the quiet stretch, which begins at
    #: frame 60 -- not that they span fewer than N frames. A span bound is a PROXY for
    #: clustering and a bad one: the quiet stretch is 30 frames long, so a perfectly
    #: clustered choice can span 29. macOS picked 60 to 89, which is entirely inside the
    #: stretch and failed a `< 20` bound that Linux passed with 72 to 79.
    assert min(used) >= 60, f"the old choice was supposed to come from the quiet stretch, got {list(used)}"

    spread_plate, used = room_plate(path, n_samples=60, width=W, stratify=True)
    assert spread_plate[203:222, 263:282].mean() < 150, "the prop is still in the room"
    assert min(used) < 60, "the stratified choice never left the quiet stretch"
    assert max(used) - min(used) > 60, "the stratified choice did not span the recording"


def test_a_plate_built_from_one_stretch_says_so(tmp_path):
    """Silence would let a plate describing one moment pass as a plate of the room."""
    import subprocess

    W, H, frames = 320, 240, 90
    rng = np.random.default_rng(4)
    background = rng.integers(48, 160, size=(H, W), dtype=np.uint8)
    raw = bytearray()
    for i in range(frames):
        frame = background.copy()
        if i >= 60:
            frame[200:225, 260:285] = 250
        else:
            x = int(i * 4)
            frame[0:180, x:x + 80] = 250
        raw += frame.tobytes()
    path = str(tmp_path / "prop.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
                    "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", "25", "-i", "pipe:0",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "5", path],
                   input=bytes(raw), check=True)

    from musicalgestures._plate import room_plate

    with pytest.warns(RuntimeWarning, match="per cent of the recording"):
        room_plate(path, n_samples=60, width=W, stratify=False)


class Test_texture_mask:
    """Motion vectors are only evidence where the picture has texture: an encoder's
    search is unconstrained on a flat block, so its vectors there are rate decisions,
    not measurements. The mask says which cells can be trusted."""

    def test_flat_cells_are_masked_and_textured_ones_kept(self):
        import numpy as np

        from musicalgestures._plate import texture_mask

        rng = np.random.default_rng(0)
        image = np.zeros((64, 128), np.uint8)
        image[:, 64:] = rng.integers(0, 255, (64, 64))   # right half textured
        mask = texture_mask(image, grid=16, percentile=40)
        assert mask.shape == (4, 8)
        assert not mask[:, :4].any(), "flat cells must not be trusted"
        assert mask[:, 4:].all(), "textured cells must be kept"

    def test_the_percentile_sets_how_much_survives(self):
        import numpy as np

        from musicalgestures._plate import texture_mask

        rng = np.random.default_rng(1)
        image = (rng.random((64, 64)) * np.linspace(0, 255, 64)).astype(np.uint8)
        strict = texture_mask(image, grid=16, percentile=75)
        lax = texture_mask(image, grid=16, percentile=25)
        assert strict.sum() < lax.sum()

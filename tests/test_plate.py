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

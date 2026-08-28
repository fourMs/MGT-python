"""A gate measured from the recording rather than guessed at.

A fixed threshold cannot serve recordings whose noise differs. Measured on a dance
corpus, one setting lit 0.52 times the area the dancers covered in one recording and 1.90
times it in another --- too tight and too loose at the same number.

The floor is therefore taken from the material: the distribution of motion magnitudes
where there is nothing to move. Everything above a chosen quantile of that is what a gate
should keep, which makes the parameter a **false-positive rate** rather than a magnitude,
and comparable across recordings in a way a magnitude is not.

**And it must be able to refuse.** Otsu will split pure noise and report a threshold with
no sign of distress; on one recording here it proposed an 82-minute "section" from a
microphone that never heard a conversation. A floor estimator that always answers is the
same fault. When the background and the moving parts do not separate --- a camera move, a
light change, a recording with nothing in it --- the honest return is no number at all.
"""
import numpy as np
import pytest

from musicalgestures._noisefloor import noise_floor


def test_the_floor_is_the_chosen_quantile_of_the_background():
    """Nothing subtle: the gate is where the background's tail ends."""
    background = np.arange(0, 1000, dtype=float)      # 0..999
    result = noise_floor(background, quantile=0.99)
    assert result["threshold"] == pytest.approx(np.percentile(background, 99))
    assert result["refused"] is False


def test_a_refusal_carries_no_threshold_to_use_by_accident():
    """The whole point of declining is that there is nothing to fall back on."""
    result = noise_floor(np.zeros(10), min_samples=1000)
    assert result["refused"] is True
    assert result["threshold"] is None
    assert "background" in result["reason"]


def test_it_refuses_when_the_moving_part_does_not_separate_from_the_background():
    """A camera move makes the whole frame differ, and no gate can be honest about it."""
    rng = np.random.default_rng(0)
    background = rng.normal(100, 10, 5000)
    result = noise_floor(background, foreground=rng.normal(100, 10, 5000))
    assert result["refused"] is True
    assert result["threshold"] is None


def test_it_accepts_when_the_moving_part_sits_well_above_the_background():
    rng = np.random.default_rng(0)
    background = rng.normal(1, 0.3, 5000)
    foreground = rng.normal(40, 5, 5000)
    result = noise_floor(background, foreground=foreground)
    assert result["refused"] is False
    assert 1 < result["threshold"] < 40
    assert result["foreground_kept"] > 0.99


def test_it_reports_how_much_of_the_moving_part_the_gate_would_remove():
    """A caller deciding whether to accept the gate needs its cost, not just its value."""
    background = np.zeros(5000)
    foreground = np.concatenate([np.zeros(2500), np.full(2500, 50.0)])
    result = noise_floor(background, foreground=foreground, quantile=0.99)
    assert result["foreground_kept"] == pytest.approx(0.5, abs=0.01)


def test_the_measured_floor_sits_between_the_noise_and_the_real_motion(tmp_path):
    """On footage whose noise and whose displacement are both known.

    A gate is only useful if it lands above what the sensor invents and below what the
    subject does. Both are set here, so both can be checked rather than eyeballed.
    """
    from tests._synth import moving_block_video
    from musicalgestures._noisefloor import frame_difference_floor

    video = moving_block_video(tmp_path / "block.mp4", dx=4, frames=60, noise=6)
    result = frame_difference_floor(video)
    assert result["refused"] is False, result["reason"]
    assert 0 < result["threshold"] < 255
    assert result["foreground_kept"] > 0.10


def test_a_recording_where_nothing_moves_is_refused_rather_than_answered(tmp_path):
    """The Otsu lesson: a detector with no way to decline will invent a threshold."""
    from tests._synth import moving_block_video
    from musicalgestures._noisefloor import frame_difference_floor

    video = moving_block_video(tmp_path / "still.mp4", dx=0, dy=0, frames=60, noise=6)
    result = frame_difference_floor(video)
    assert result["refused"] is True
    assert result["threshold"] is None


def test_the_vector_floor_lands_below_the_displacement_it_must_not_remove(tmp_path):
    """The block moves 2 px a frame, so any gate at or above 2 deletes the subject.

    Longer than the other clips on purpose: the vector lattice is one cell per 16 px, so
    a 320x240 clip has 300 cells and a 48 px block occupies nine of them. Sixty frames of
    that is fewer samples than the estimator will work from, and rightly so.
    """
    from tests._synth import moving_block_video
    from musicalgestures._noisefloor import motion_vector_floor

    video = moving_block_video(tmp_path / "block.mp4", dx=2, frames=240, noise=6,
                               size=(640, 480), block=96)
    result = motion_vector_floor(video)
    assert result["refused"] is False, result["reason"]
    assert result["threshold"] < 2.0


def test_a_file_with_no_motion_vectors_at_all_is_refused(tmp_path):
    """An all-intra file carries none, and has nothing to estimate a floor from."""
    from tests._synth import intra_only_video
    from musicalgestures._noisefloor import motion_vector_floor

    video = intra_only_video(tmp_path / "intra.avi", frames=20)
    result = motion_vector_floor(video)
    assert result["refused"] is True
    assert result["threshold"] is None

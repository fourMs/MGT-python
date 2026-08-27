"""The spatial views must not hold every frame in memory.

A 100-minute 1920x1080 recording is 310,368 frames, and its macroblock grid is 68 by 120.
Stacking one float64 array of that per frame is 20 GB, and the first version of this
module built three of them --- so it worked on every test clip in this suite and would
have taken the machine down on the first real recording. MGT's tests are short by nature,
so the only way to catch that class is to measure how allocation grows with length rather
than whether a clip succeeds.

Four times the frames must not mean four times the peak.
"""
import tracemalloc

import pytest

from _synth import moving_block_video

av = pytest.importorskip("av", reason="motion-vector data needs the optional 'av' extra")

from musicalgestures._motionvectors import (  # noqa: E402
    accumulate_motion_vectors,
    motion_vector_motiongrams,
)


def _peak_mb(fn, path):
    tracemalloc.start()
    try:
        fn(path)
        return tracemalloc.get_traced_memory()[1] / 1e6
    finally:
        tracemalloc.stop()


@pytest.fixture(scope="module")
def short_clip(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("mem") / "short.mp4", dx=2,
                              frames=60, size=(320, 240))


@pytest.fixture(scope="module")
def long_clip(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("mem") / "long.mp4", dx=2,
                              frames=240, size=(320, 240))


class Test_peak_memory_does_not_scale_with_length:
    def test_the_history_accumulator_is_streaming(self, short_clip, long_clip):
        short = _peak_mb(accumulate_motion_vectors, short_clip)
        long = _peak_mb(accumulate_motion_vectors, long_clip)
        assert long < short * 2, (
            f"peak went {short:.1f} MB -> {long:.1f} MB for 4x the frames; "
            "this accumulator is holding the whole recording")

    def test_the_motiongrams_do_not_hold_every_grid(self, short_clip, long_clip):
        """A motiongram is one column per frame, so it must grow --- but with the
        REDUCED column, not with the full grid behind it."""
        short = _peak_mb(motion_vector_motiongrams, short_clip)
        long = _peak_mb(motion_vector_motiongrams, long_clip)
        assert long < short * 2.5, (
            f"peak went {short:.1f} MB -> {long:.1f} MB for 4x the frames")

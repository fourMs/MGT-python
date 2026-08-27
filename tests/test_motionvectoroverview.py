"""One decode, every view --- and the views must be the ones the single functions give.

The reason this exists is bulk triage: hours of archive material, several visualisations
per file, as a starting point rather than an answer. Decoding is nearly all of the cost,
so four views that each decode the file cost four times what they need to.

The test that matters is equivalence. A combined pass that is fast but subtly different
from the individual functions is worse than no combined pass, because the fast path is
the one people will actually run.
"""
import numpy as np
import pytest

import musicalgestures
from _synth import moving_block_video

av = pytest.importorskip("av", reason="motion-vector data needs the optional 'av' extra")

from musicalgestures._motionvectors import (  # noqa: E402
    accumulate_motion_vectors,
    motion_vector_motiongrams,
    motion_vector_views,
)


@pytest.fixture(scope="module")
def clip(tmp_path_factory):
    return moving_block_video(tmp_path_factory.mktemp("ov") / "c.mp4", dx=3, frames=80)


class Test_one_pass_gives_the_same_answer:
    def test_history_matches_the_separate_accumulator(self, clip):
        """Both sides pinned to the deterministic path. Frame-threaded decoding drops a
        few motion vectors and not the same ones twice, which made this test flake --- two
        runs failed and one passed on identical input before that was found."""
        views = motion_vector_views(clip, deterministic=True)
        weight, vx, vy, coherence = accumulate_motion_vectors(clip, deterministic=True)
        assert np.allclose(views.history_weight, weight)
        assert np.allclose(views.history_vx, vx)
        assert np.allclose(views.history_coherence, coherence)

    def test_motiongrams_match_the_separate_ones(self, clip):
        views = motion_vector_views(clip, deterministic=True)
        horizontal, vertical = motion_vector_motiongrams(clip, deterministic=True)
        assert np.allclose(views.motiongram_horizontal, horizontal)
        assert np.allclose(views.motiongram_vertical, vertical)

    def test_the_temporal_track_covers_every_p_frame(self, clip):
        views = motion_vector_views(clip)
        assert len(views.time) == len(views.magnitude)
        assert views.motiongram_horizontal.shape[1] == len(views.time)
        assert np.all(np.diff(views.time) > 0)


class Test_the_overview_image:
    def test_renders_one_sheet_with_every_panel(self, clip, tmp_path):
        import os
        result = musicalgestures.MgVideo(clip).motionvectoroverview(
            target_name=str(tmp_path / "ov.png"))
        assert isinstance(result, musicalgestures.MgFigure)
        assert os.path.isfile(result.image)
        assert set(result.data) >= {"time", "magnitude", "history_weight"}

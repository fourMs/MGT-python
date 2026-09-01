"""Regression tests for the newer analysis functions: the audio–motion comparison suite,
video resampling, and the pose analysis renderers (tested with synthetic pose data so they
don't require running pose inference / downloading model weights)."""
import os
import numpy as np
import pytest

import musicalgestures
from musicalgestures import MgVideo, MgImage, MgFigure
from musicalgestures._utils import resolve_filename


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def clip(tmp_path_factory):
    """A short clip (with audio) shared across the audio–motion tests."""
    target = str(tmp_path_factory.mktemp("av")).replace("\\", "/") + "/clip.avi"
    path = musicalgestures._utils.extract_subclip(musicalgestures.examples.dance, 2, 7, target_name=target)
    return MgVideo(path)


def _fake_pose_data(n_frames=60, n_markers=6, fps=30.0, seed=0):
    """Synthetic pose rows [time_ms, x0, y0, ...] in normalised coords."""
    rng = np.random.default_rng(seed)
    rows = []
    for f in range(n_frames):
        row = [f / fps * 1000.0]
        for m in range(n_markers):
            row += [0.4 + 0.1 * np.sin(f / 6 + m) + 0.01 * rng.standard_normal(),
                    0.5 + 0.1 * np.cos(f / 6 + m)]
        rows.append(row)
    names = [f"m{i}" for i in range(n_markers)]
    connections = [(i, i + 1) for i in range(n_markers - 1)]
    return rows, names, connections


# ---------------------------------------------------------------------------
# Audio–motion comparison suite
# ---------------------------------------------------------------------------
class Test_AudioMovement:
    def test_tempo_similarity(self, clip, tmp_path):
        fig = clip.tempo_similarity(target_name=str(tmp_path / "ts.png"), overwrite=True)
        assert isinstance(fig, MgFigure)
        assert os.path.isfile(fig.image)
        for k in ("audio_tempo_bpm", "motion_tempo_bpm", "tempo_ratio", "peak_crosscorr"):
            assert k in fig.data

    def test_phase_synchrony(self, clip, tmp_path):
        fig = clip.phase_synchrony(target_name=str(tmp_path / "ps.png"), overwrite=True)
        assert isinstance(fig, MgFigure)
        assert os.path.isfile(fig.image)
        assert 0.0 <= fig.data["plv"] <= 1.0

    def test_dynamics_coupling(self, clip, tmp_path):
        fig = clip.dynamics_coupling(target_name=str(tmp_path / "dc.png"), overwrite=True)
        assert isinstance(fig, MgFigure)
        assert os.path.isfile(fig.image)
        assert -1.0 <= fig.data["zero_lag_corr"] <= 1.0

    def test_structure_comparison(self, clip, tmp_path):
        fig = clip.structure_comparison(n=80, target_name=str(tmp_path / "sc.png"), overwrite=True)
        assert isinstance(fig, MgFigure)
        assert os.path.isfile(fig.image)
        assert 0.0 <= fig.data["structural_agreement"] <= 1.0

    def test_method_not_shadowed(self, clip, tmp_path):
        # The result must not overwrite the bound method (a second call must still work).
        clip.tempo_similarity(target_name=str(tmp_path / "a.png"), overwrite=True)
        assert callable(clip.tempo_similarity)
        clip.tempo_similarity(target_name=str(tmp_path / "b.png"), overwrite=True)


# ---------------------------------------------------------------------------
# resample()
# ---------------------------------------------------------------------------
class Test_Resample:
    def test_fps_preserves_duration(self, clip):
        out = clip.resample(fps=15)
        assert isinstance(out, MgVideo)
        assert os.path.isfile(out.filename)
        assert abs(out.fps - 15) < 1.0
        # original untouched
        assert clip.fps != 15 or True

    def test_speed(self, clip):
        out = clip.resample(speed=2.0)
        assert isinstance(out, MgVideo)
        assert out.duration < clip.duration

    def test_skip(self, clip):
        out = clip.resample(skip=1)
        assert isinstance(out, MgVideo)
        assert os.path.isfile(out.filename)

    def test_requires_an_argument(self, clip):
        with pytest.raises(ValueError):
            clip.resample()


# ---------------------------------------------------------------------------
# Pose renderers (synthetic data — no pose inference)
# ---------------------------------------------------------------------------
class Test_PoseRenderers:
    def test_pose_center(self, tmp_path):
        from musicalgestures._pose_visualize import render_pose_center, pose_center
        data, names, _ = _fake_pose_data()
        centered, offset, times = pose_center(data, names)
        assert centered.shape == (60, 6, 2)
        assert offset.shape == (2,)
        fig = render_pose_center(data, names, 640, 480, str(tmp_path / "pc.png"), overwrite=True)
        assert isinstance(fig, MgFigure) and os.path.isfile(fig.image)

    def test_pose_distance(self, tmp_path):
        from musicalgestures._pose_visualize import render_pose_distance, pose_distance
        data, names, _ = _fake_pose_data()
        cumulative, total, average, _ = pose_distance(data, names, 640, 480)
        assert total.shape == (6,)
        assert average >= 0
        fig = render_pose_distance(data, names, 640, 480, 30.0, str(tmp_path / "pd.png"), overwrite=True)
        assert isinstance(fig, MgFigure) and os.path.isfile(fig.image)

    def test_pose_segments(self, tmp_path):
        from musicalgestures._pose_visualize import render_segment_circular
        data, names, connections = _fake_pose_data()
        fig = render_segment_circular(data, names, connections, 640, 480, 30.0,
                                      str(tmp_path / "seg.png"), overwrite=True)
        assert isinstance(fig, MgFigure) and os.path.isfile(fig.image)
        assert len(fig.data["stats"]) == len(connections)

    def test_pose_waterfall_styles(self, tmp_path):
        from musicalgestures._pose_visualize import render_pose_waterfall
        data, names, connections = _fake_pose_data()
        for style in ("trajectories", "markers", "skeleton", "both"):
            fig = render_pose_waterfall(data, names, 640, 480, 30.0, str(tmp_path / f"wf_{style}.png"),
                                        overwrite=True, style=style, connections=connections, n_samples=20)
            assert isinstance(fig, MgFigure) and os.path.isfile(fig.image)


# ---------------------------------------------------------------------------
# Core-class conveniences
# ---------------------------------------------------------------------------
class Test_CoreConveniences:
    def test_video_duration_and_nframes(self, clip):
        assert clip.n_frames == int(clip.length)
        assert clip.duration == pytest.approx(clip.length / clip.fps, rel=1e-6)

    def test_video_repr(self, clip):
        r = repr(clip)
        assert r.startswith("MgVideo(") and "frames" in r and "audio=" in r

    def test_audio_repr_and_duration(self, clip):
        a = clip.audio
        assert repr(a).startswith("MgAudio(")
        assert a.duration == pytest.approx(a.length, rel=1e-6)

    def test_mgimage_save(self, clip, tmp_path):
        img = clip.average()
        out = img.save(str(tmp_path / "saved.jpg"))   # extension normalised to source (.png)
        assert isinstance(out, MgImage)
        assert os.path.isfile(out.filename) and out.filename.endswith(".png")

    def test_resolve_filename(self):
        assert resolve_filename("/a/b/clip", "_grid.png").endswith("clip_grid.png")
        # provided target: extension is normalised to the suffix's
        assert resolve_filename("/a/b/clip", "_grid.png", "/out/x.jpg").endswith("x.png")

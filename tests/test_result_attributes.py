"""MgVideo declares its result attributes, without creating them.

Analysis methods stash results on the parent object. Declaring those
attributes lets a type checker follow them; declaring them as bare
annotations means they still do not exist until a method assigns one, which
is what `show(key=...)` relies on when it looks in `self.__dict__`.
"""
import pytest
import musicalgestures as mg

CONFORMING = [
    "blend_image", "blur_faces_video", "body_audio_coupling_figure",
    "dynamics_coupling_figure", "eulerian_video", "heatmap_image",
    "history_video", "mhi_image", "motion_video", "motiondescriptors_figure",
    "motionvectors_video", "phase_synchrony_figure", "pose_centered_figure",
    "pose_distance_figure", "pose_segments_figure", "pose_video",
    "pose_waterfall_figure", "silhouette_waterfall_figure",
    "sonomotiongram_audio", "spacetime_volume_figure", "ssm_figure",
    "stroboscope_image", "structure_comparison_figure", "subtract_video",
    "tempo_similarity_figure", "warp_video",
]


class TestDeclarations:
    def test_every_conforming_attribute_is_declared(self):
        # __annotations__ does not inherit, and `ssm_figure` is set on MgAudio
        # instances by mg_ssm's audio paths, so both classes are checked.
        declared = {**mg.MgAudio.__annotations__, **mg.MgVideo.__annotations__}
        missing = [n for n in CONFORMING if n not in declared]
        assert not missing, f"undeclared result attributes: {missing}"

    def test_declaring_does_not_create_a_class_attribute(self):
        """A bare annotation must not put the name in the class dictionary."""
        for name in CONFORMING:
            for cls in (mg.MgVideo, mg.MgAudio):
                assert name not in cls.__dict__, (
                    f"{name} was given a value on {cls.__name__}; "
                    "show() and hasattr would both change")

    def test_every_declared_name_ends_in_its_type(self):
        for name in CONFORMING:
            assert name.endswith(("_video", "_image", "_figure", "_audio")), name


RENAMED = [
    ("motion_plot", "motion_plot_image"),
    ("motiongram_x", "motiongram_vertical_image"),
    ("motiongram_y", "motiongram_horizontal_image"),
    ("videogram_x", "videogram_vertical_image"),
    ("videogram_y", "videogram_horizontal_image"),
]


class TestRenames:
    @pytest.mark.parametrize("old,new", RENAMED)
    def test_the_new_name_is_declared(self, old, new):
        assert new in mg.MgVideo.__annotations__

    @pytest.mark.parametrize("old,new", RENAMED)
    def test_the_old_name_still_works_and_warns(self, old, new):
        v = mg.MgVideo.__new__(mg.MgVideo)
        setattr(v, new, "sentinel")
        with pytest.warns(DeprecationWarning, match=f"use {new}"):
            assert getattr(v, old) == "sentinel"

    @pytest.mark.parametrize("old,new", RENAMED)
    def test_writing_the_old_name_lands_under_the_new_one(self, old, new):
        v = mg.MgVideo.__new__(mg.MgVideo)
        with pytest.warns(DeprecationWarning):
            setattr(v, old, "sentinel")
        assert v.__dict__[new] == "sentinel"
        assert old not in v.__dict__


class TestGramOrientation:
    """The x-collapse produces the vertical gram. Pinning it, because the
    inverted-looking mapping is correct and has been mistaken for a bug."""

    @pytest.mark.parametrize("kind", ["motiongram", "videogram"])
    def test_x_maps_to_vertical_and_y_to_horizontal(self, kind):
        v = mg.MgVideo.__new__(mg.MgVideo)
        with pytest.warns(DeprecationWarning):
            setattr(v, f"{kind}_x", "from-x")
        with pytest.warns(DeprecationWarning):
            setattr(v, f"{kind}_y", "from-y")
        assert getattr(v, f"{kind}_vertical_image") == "from-x"
        assert getattr(v, f"{kind}_horizontal_image") == "from-y"

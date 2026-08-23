"""MgVideo declares its result attributes, without creating them.

Analysis methods stash results on the parent object. Declaring those
attributes lets a type checker follow them; declaring them as bare
annotations means they still do not exist until a method assigns one, which
is what `show(key=...)` relies on when it looks in `self.__dict__`.
"""
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

"""Postures and trajectories over time, in one flat picture.

The data half is tested without video on purpose: a synthetic articulated figure whose
joint angles are set by hand has a known answer, where a clip of somebody dancing has
only a plausible one.
"""
import numpy as np
import pytest

from musicalgestures._posetimeline import (detection_gaps, normalise_poses,
                                           region_angles)

PELVIS, SHOULDERS = (23, 24), (11, 12)


def _figure(n_frames=10, arm_angle_deg=0.0, scale=1.0, offset=(0.0, 0.0), visibility=1.0):
    """A stick figure with a known arm angle, at a known size and place.

    Landmark indices are MediaPipe's, so the same code under test can read it.
    """
    #: Landmarks this figure does not define are left INVISIBLE, not at the origin. A
    #: landmark sitting at (0, 0) with full confidence is a body part the detector claims
    #: to have found in the corner of the frame, and it drags every mean that touches it:
    #: with the wrists left that way the "arm held down" angle read 83 degrees.
    lm = np.zeros((n_frames, 33, 3), dtype=float)
    for f in range(n_frames):
        a = np.deg2rad(arm_angle_deg if np.isscalar(arm_angle_deg) else arm_angle_deg[f])
        lm[f, 23] = [-0.1 * scale + offset[0], 0.6 * scale + offset[1], visibility]
        lm[f, 24] = [0.1 * scale + offset[0], 0.6 * scale + offset[1], visibility]
        lm[f, 11] = [-0.1 * scale + offset[0], 0.2 * scale + offset[1], visibility]
        lm[f, 12] = [0.1 * scale + offset[0], 0.2 * scale + offset[1], visibility]
        #: Left elbow hangs from the left shoulder at `arm_angle_deg` from vertical.
        lm[f, 13] = [lm[f, 11, 0] - np.sin(a) * 0.2 * scale,
                     lm[f, 11, 1] + np.cos(a) * 0.2 * scale, visibility]
        lm[f, 14] = [lm[f, 12, 0] + np.sin(a) * 0.2 * scale,
                     lm[f, 12, 1] + np.cos(a) * 0.2 * scale, visibility]
        for knee, hip in ((25, 23), (26, 24)):
            lm[f, knee] = [lm[f, hip, 0], lm[f, hip, 1] + 0.25 * scale, visibility]
        #: Wrists continue each forearm, so the arm region has whole bones to measure.
        for wrist, elbow, shoulder in ((15, 13, 11), (16, 14, 12)):
            lm[f, wrist] = [2 * lm[f, elbow, 0] - lm[f, shoulder, 0],
                            2 * lm[f, elbow, 1] - lm[f, shoulder, 1], visibility]
        #: A head, so the head group has something to average. Nose above the shoulders,
        #: ears beside it.
        top_y = lm[f, 11, 1] - 0.12 * scale
        lm[f, 0] = [offset[0], top_y, visibility]
        lm[f, 7] = [offset[0] - 0.05 * scale, top_y, visibility]
        lm[f, 8] = [offset[0] + 0.05 * scale, top_y, visibility]
        for ankle, knee, hip in ((27, 25, 23), (28, 26, 24)):
            lm[f, ankle] = [2 * lm[f, knee, 0] - lm[f, hip, 0],
                            2 * lm[f, knee, 1] - lm[f, hip, 1], visibility]
    return lm


def test_normalising_puts_the_pelvis_at_the_origin():
    lm = normalise_poses(_figure(offset=(0.4, 0.3)), min_visibility=0.5)
    pelvis = lm[:, list(PELVIS), :2].mean(axis=1)
    assert np.allclose(pelvis, 0.0, atol=1e-9)


def test_normalising_makes_two_sizes_of_the_same_posture_identical():
    """Otherwise a dancer stepping towards the camera reads as a change of shape."""
    near = normalise_poses(_figure(scale=2.0, offset=(0.1, 0.0)), min_visibility=0.5)
    far = normalise_poses(_figure(scale=1.0, offset=(-0.3, 0.2)), min_visibility=0.5)
    assert np.allclose(near, far, atol=1e-6, equal_nan=True)


def test_an_arm_held_down_and_an_arm_held_out_do_not_read_the_same():
    """The whole point of carrying configuration rather than speed: both are still."""
    down = region_angles(normalise_poses(_figure(arm_angle_deg=0.0), min_visibility=0.5))["arms"]
    out = region_angles(normalise_poses(_figure(arm_angle_deg=90.0), min_visibility=0.5))["arms"]
    assert np.nanmean(down) < 15 and np.nanmean(out) > 75


def test_a_held_posture_is_a_flat_band_and_a_moving_one_is_not():
    held = region_angles(normalise_poses(_figure(n_frames=20, arm_angle_deg=30.0), min_visibility=0.5))["arms"]
    sweeping = region_angles(normalise_poses(
        _figure(n_frames=20, arm_angle_deg=np.linspace(0, 90, 20)), min_visibility=0.5))["arms"]
    assert np.nanstd(held) < 1.0 < np.nanstd(sweeping)


def test_frames_the_detector_missed_are_gaps_and_are_not_interpolated():
    """Interpolating across them would invent posture."""
    lm = _figure(n_frames=10)
    lm[4:7, :, 2] = 0.1                       # three frames the detector was unsure of
    normalised = normalise_poses(lm, min_visibility=0.5)
    assert np.isnan(normalised[4:7]).all(), "a gap was filled in"
    #: The claim is about the ANCHOR, not about every landmark: undefined landmarks are
    #: NaN in every frame by design, so "no NaN before the gap" was never what this meant.
    assert not np.isnan(normalised[:4, list(PELVIS), 0]).any()
    assert not np.isnan(normalised[7:, list(PELVIS), 0]).any()
    assert detection_gaps(lm, min_visibility=0.5) == [(4, 7)]


def test_a_recording_with_nobody_in_it_is_refused_rather_than_drawn():
    """An empty figure reads as 'nothing happened' rather than 'nobody was found'."""
    from musicalgestures._posetimeline import pose_timeline_data

    lm = _figure(n_frames=10, visibility=0.0)
    with pytest.raises(ValueError, match="no pose"):
        pose_timeline_data(lm, min_visibility=0.5)


def test_a_region_with_nothing_visible_is_nan_and_not_a_warning():
    """A RuntimeWarning on ordinary input is how a real one gets ignored later."""
    import warnings

    lm = _figure(n_frames=5)
    lm[:, 0, 2] = 0.0                      # the nose, which the head region needs
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        angles = region_angles(normalise_poses(lm, min_visibility=0.5))
    assert np.isnan(angles["head"]).all()
    assert not np.isnan(angles["legs"]).all(), "the other regions still measure"


def test_the_trajectory_meets_each_posture_where_that_landmark_really_is():
    """It is drawn over the skeletons, so it has to touch them."""
    from musicalgestures._posetimeline import connecting_trajectory

    lm = _figure(n_frames=30, arm_angle_deg=np.linspace(0, 90, 30))
    normalised = normalise_poses(lm, min_visibility=0.5)
    picks = [0, 15, 29]
    segments = connecting_trajectory(normalised, picks, marker=15, lane=2.6,
                                     space="body")["marker"]
    assert len(segments) == len(picks) - 1, "one segment per gap between postures"
    for i, (x, y) in enumerate(segments):
        anchored = i * 2.6 + normalised[picks[i], 15, 0]
        assert abs(x[0] - anchored) < 1e-9, "the curve starts away from the figure"


def test_a_held_limb_traces_a_flat_line_and_a_sweeping_one_does_not():
    """Otherwise the curve says 'movement' wherever it is drawn."""
    from musicalgestures._posetimeline import connecting_trajectory

    held = normalise_poses(_figure(n_frames=30, arm_angle_deg=45.0), min_visibility=0.5)
    swept = normalise_poses(_figure(n_frames=30, arm_angle_deg=np.linspace(0, 90, 30)),
                            min_visibility=0.5)
    flat = connecting_trajectory(held, [0, 15, 29], marker=15, space="body",
                                 smooth=0)["marker"][0][1]
    moving = connecting_trajectory(swept, [0, 15, 29], marker=15, space="body",
                                   smooth=0)["marker"][0][1]
    assert np.std(flat) < 1e-9 < np.std(moving)


def test_detector_spikes_are_dropped_rather_than_drawn():
    """A frame whose torso came out short divides up into a spike that swamps the plot.

    The first version drew them, and the picture was unreadable."""
    from musicalgestures._posetimeline import connecting_trajectory

    normalised = normalise_poses(_figure(n_frames=30), min_visibility=0.5)
    normalised[7, 15] = [40.0, -60.0]
    x, y = connecting_trajectory(normalised, [0, 15, 29], marker=15, max_reach=4.0,
                                 space="body")["marker"][0]
    assert np.abs(y).max() < 10, "a spike was drawn"


def test_the_strip_accepts_both_kinds_of_trajectory_and_neither():
    from musicalgestures._posetimeline import pose_timeline

    lm = _figure(n_frames=40, arm_angle_deg=np.linspace(0, 90, 40))
    for trajectories in (None, "temporal", "spatial", "path"):
        fig = pose_timeline(lm, view="strip", n_samples=4, min_visibility=0.5,
                            trajectories=trajectories)
        assert fig is not None
    with pytest.raises(ValueError, match="trajectories"):
        pose_timeline(lm, view="strip", n_samples=4, min_visibility=0.5,
                      trajectories="sideways")


def test_the_bands_read_down_the_body():
    """Head, torso, then the limbs that hang from it, then legs.

    Asserted rather than left to the dict's insertion order, because a reordering while
    editing would be invisible and would quietly change what every published figure means.
    """
    from musicalgestures._posetimeline import REGION_BONES

    assert list(REGION_BONES) == ["head", "torso", "arms", "hands", "legs"]


def test_the_only_words_on_the_figure_are_the_ones_that_identify_a_row():
    """A plot carrying its own explanation cannot be put beside another one.

    Titles and captions belong in the caption of whatever the figure goes into. What
    stays is the time axis and its unit: numbers without a unit are as unreadable as no
    numbers, since nothing on the figure says whether 175 is seconds, frames or minutes.
    """
    import matplotlib
    matplotlib.use("Agg")
    from musicalgestures._posetimeline import pose_timeline

    lm = _figure(n_frames=40, arm_angle_deg=np.linspace(0, 90, 40))
    for view in ("strip", "bands"):
        fig = pose_timeline(lm, view=view, n_samples=4, min_visibility=0.5)
        #: Seconds when a time base was given, frames when it was not -- and it says
        #: which, rather than leaving the reader to guess what 175 counts.
        labels = [ax.get_xlabel() for ax in fig.axes if ax.get_xlabel()]
        assert labels == ["time (frames)"], f"{view} labels its axes as {labels}"
        for ax in fig.axes:
            assert ax.get_title() == "", f"{view} still carries a title"
            assert ax.get_ylabel() == "", f"{view} still carries a y label"


def test_smoothing_keeps_the_shape_and_drops_the_jitter():
    """A curve drawn at every frame is unreadable exactly where the most is happening.

    The requirement is narrow: the excursion the limb really made must survive, and the
    frame-to-frame tremor on top of it must not. A filter that flattens both is no use.
    """
    from musicalgestures._posetimeline import smooth_trail

    t = np.linspace(0, 2 * np.pi, 400)
    swing = np.sin(t)                                  # the movement
    rng = np.random.default_rng(2)
    jittery = swing + rng.normal(0, 0.08, t.size)      # and the tremor on it

    smoothed = smooth_trail(jittery, window=15)
    assert np.std(smoothed - swing) < np.std(jittery - swing) / 2, "the jitter survived"
    assert abs(np.ptp(smoothed) - np.ptp(swing)) < 0.25, "the swing was flattened"


def test_smoothing_does_not_bridge_a_gap():
    """A window spanning missing frames would invent the posture in between."""
    from musicalgestures._posetimeline import smooth_trail

    y = np.arange(30.0)
    y[12:18] = np.nan
    smoothed = smooth_trail(y, window=9)
    assert np.isnan(smoothed[12:18]).all(), "a gap was smoothed over"


def test_smoothing_can_be_turned_off(travelling_landmarks):
    from musicalgestures._posetimeline import connecting_trajectory

    picks = [0, 20, 39]
    rough = connecting_trajectory(travelling_landmarks, picks, marker=15, smooth=0,
                                  space="body")["marker"]
    soft = connecting_trajectory(travelling_landmarks, picks, marker=15, smooth=15,
                                 space="body")["marker"]
    assert np.std(np.diff(soft[0][1])) < np.std(np.diff(rough[0][1]))


@pytest.fixture
def travelling_landmarks():
    rng = np.random.default_rng(5)
    lm = _figure(n_frames=40, arm_angle_deg=np.linspace(0, 90, 40))
    lm[:, 15, :2] += rng.normal(0, 0.01, (40, 2))     # tremor on the wrist
    return normalise_poses(lm, min_visibility=0.5)


def test_the_pelvis_is_flat_in_body_space_by_construction():
    """Not a bug to fix but a fact to design around, and it is easy to walk into.

    `normalise_poses` centres every posture on the pelvis, so following the pelvis in
    that space traces a straight line whatever the dancer did.
    """
    from musicalgestures._posetimeline import connecting_trajectory

    normalised = normalise_poses(_figure(n_frames=30, arm_angle_deg=np.linspace(0, 90, 30)),
                                 min_visibility=0.5)
    x, y = connecting_trajectory(normalised, [0, 15, 29], marker=(23, 24),
                                 space="body")["marker"][0]
    assert np.nanstd(y) < 1e-9, "the pelvis moved in a space that centres on it"


def test_in_room_space_the_trunk_carries_where_the_body_actually_went():
    from musicalgestures._posetimeline import connecting_trajectory

    lm = _figure(n_frames=30)
    lm[:, :, 1] += np.linspace(0, 0.4, 30)[:, None]      # the whole body rises
    normalised = normalise_poses(lm, min_visibility=0.5)
    #: `smooth=0`: this is testing the geometry, and the default window is wider than
    #: the whole segment here, which would flatten it to a constant.
    x, y = connecting_trajectory(normalised, [0, 15, 29], marker=(11, 12, 23, 24),
                                 space="room", raw=lm, height=1,
                                 smooth=0)["marker"][0]
    assert np.nanstd(y) > 0.01, "a body that moved read as still"


def test_averaging_several_landmarks_is_steadier_than_following_one():
    from musicalgestures._posetimeline import connecting_trajectory

    rng = np.random.default_rng(9)
    lm = _figure(n_frames=40)
    lm[:, [11, 12, 23, 24], :2] += rng.normal(0, 0.004, (40, 4, 2))
    lm[:, :, 1] += np.linspace(0, 0.3, 40)[:, None]
    normalised = normalise_poses(lm, min_visibility=0.5)
    one = connecting_trajectory(normalised, [0, 39], marker=11, space="room",
                                raw=lm, smooth=0, height=1)["marker"][0][1]
    many = connecting_trajectory(normalised, [0, 39], marker=(11, 12, 23, 24),
                                 space="room", raw=lm, smooth=0, height=1)["marker"][0][1]
    assert np.std(np.diff(many)) < np.std(np.diff(one)), "averaging did not steady it"


def test_three_named_lines_come_back_by_default():
    """Head, pelvis and feet: what a body does vertically, which one point cannot show."""
    from musicalgestures._posetimeline import connecting_trajectory

    lm = _figure(n_frames=30)
    lm[:, :, 1] += np.linspace(0, 0.3, 30)[:, None]
    lines = connecting_trajectory(normalise_poses(lm, min_visibility=0.5), [0, 15, 29],
                                  raw=lm, height=1)
    assert set(lines) == {"head", "pelvis", "feet"}
    assert all(len(segments) == 2 for segments in lines.values())


def test_traces_draw_a_fading_history_behind_each_posture():
    """All landmarks, not one, and fading so the direction of time reads.

    A trace with constant alpha is a tangle: it says a limb was in several places and not
    which it reached last.
    """
    from musicalgestures._posetimeline import posture_traces

    lm = _figure(n_frames=40, arm_angle_deg=np.linspace(0, 90, 40))
    normalised = normalise_poses(lm, min_visibility=0.5)
    ghosts = posture_traces(normalised, picks=[10, 30], n_ghosts=4)
    assert len(ghosts) == 2, "one history per posture"
    frames, alphas = ghosts[0]
    assert len(frames) == len(alphas) <= 4
    assert alphas[0] < alphas[-1], "the oldest ghost must be the faintest"
    assert all(f <= 10 for f in frames), "a history reaches backwards, not forwards"


def test_a_held_posture_leaves_ghosts_on_top_of_itself():
    """Otherwise every figure looks like it was moving."""
    from musicalgestures._posetimeline import posture_traces

    held = normalise_poses(_figure(n_frames=40, arm_angle_deg=45.0), min_visibility=0.5)
    frames, _ = posture_traces(held, picks=[20], n_ghosts=4)[0]
    spread = np.nanmax([np.nanstd(held[frames, 15, 0]), np.nanstd(held[frames, 16, 0])])
    assert spread < 1e-9


def test_lanes_widen_when_a_history_is_drawn_in_them():
    """The fan of ghosts needs room the bare postures do not.

    At the fixed spacing the last figures sat inside the previous one's history, which
    reads as one confused body rather than two moments.
    """
    from musicalgestures._posetimeline import lane_spacing

    assert lane_spacing(trajectories=None) < lane_spacing(trajectories="traces")
    assert lane_spacing(trajectories="connect") == lane_spacing(trajectories=None)




def test_the_axis_says_which_unit_it_is_counting():
    """175 is a different claim in seconds than in frames, and nothing else says which."""
    import matplotlib
    matplotlib.use("Agg")
    from musicalgestures._posetimeline import pose_timeline

    lm = _figure(n_frames=40, arm_angle_deg=np.linspace(0, 90, 40))
    seconds = pose_timeline(lm, view="bands", min_visibility=0.5,
                            times=np.arange(40) / 30.0)
    assert [a.get_xlabel() for a in seconds.axes if a.get_xlabel()] == ["time (s)"]


def test_the_two_kinds_of_trace_can_be_asked_for_together():
    """They answer different questions and are not alternatives.

    Temporal is what this figure did around its own instant; spatial is how one figure
    connects to the next. Wanting both is the ordinary case, not an exotic one.
    """
    import matplotlib
    matplotlib.use("Agg")
    from musicalgestures._posetimeline import pose_timeline

    lm = _figure(n_frames=60, arm_angle_deg=np.linspace(0, 90, 60))
    lm[:, :, 0] += np.linspace(0, 0.5, 60)[:, None]
    for asked in ("temporal", "spatial", ("temporal", "spatial"), ["spatial", "path"]):
        fig = pose_timeline(lm, view="strip", n_samples=4, min_visibility=0.5,
                            trajectories=asked)
        assert fig is not None
    with pytest.raises(ValueError, match="trajectories"):
        pose_timeline(lm, view="strip", n_samples=4, min_visibility=0.5,
                      trajectories=("temporal", "sideways"))


def test_the_strip_is_one_panel_with_the_times_under_the_postures():
    """No second plot: the numbers under the figures are the timeline.

    A separate path plot underneath said where the body was, which is the room view's
    job, and it doubled the figure's height to say it.
    """
    import matplotlib
    matplotlib.use("Agg")
    from musicalgestures._posetimeline import pose_timeline

    lm = _figure(n_frames=60)
    fig = pose_timeline(lm, view="strip", n_samples=5, min_visibility=0.5,
                        times=np.arange(60) / 30.0)
    assert len(fig.axes) == 1, "the strip should be a single panel"
    ax = fig.axes[0]
    assert len(ax.get_xticks()) == 5, "one tick per posture"
    assert ax.get_xlabel() == "time (s)"


def test_a_landmark_group_that_is_wholly_missing_is_nan_and_not_a_warning():
    """The same fault as in region_angles, which was fixed there and missed here."""
    import warnings

    from musicalgestures._posetimeline import connecting_trajectory

    lm = _figure(n_frames=30)
    lm[10:20, [27, 28, 31, 32], 2] = 0.0        # the feet, for a third of the clip
    normalised = normalise_poses(lm, min_visibility=0.5)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        lines = connecting_trajectory(normalised, [0, 15, 29], raw=lm, height=1)
    assert "feet" in lines and "pelvis" in lines


def test_the_spatial_lines_are_smoothed_harder_than_the_traces_by_default():
    """They are showing carriage, not gesture, and the two want different windows.

    A third of a second suits a limb's trace and leaves the head/pelvis/feet lines
    thrashing across a fast passage, where they cross other figures and damage the whole
    strip rather than one cell.
    """
    from musicalgestures._posetimeline import SMOOTH, SMOOTH_SPATIAL

    assert SMOOTH_SPATIAL > SMOOTH


def test_the_spatial_window_can_be_set_and_switched_off():
    from musicalgestures._posetimeline import connecting_trajectory

    rng = np.random.default_rng(3)
    lm = _figure(n_frames=120)
    lm[:, :, 1] += np.sin(np.linspace(0, 12, 120))[:, None] * 0.1
    lm[:, :, 1] += rng.normal(0, 0.01, (120, 1))
    normalised = normalise_poses(lm, min_visibility=0.5)

    def roughness(window):
        y = connecting_trajectory(normalised, [0, 60, 119], raw=lm, height=1,
                                  smooth=window)["pelvis"][0][1]
        return np.std(np.diff(y))

    assert roughness(0) > roughness(9) > roughness(45), "a wider window must be calmer"

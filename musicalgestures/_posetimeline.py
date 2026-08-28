"""Postures and trajectories over time, flat enough to read at a glance.

Three views of one pose pipeline, behind one function:

- ``strip`` --- postures at regular instants, each normalised into its own cell, with the
  body's path drawn underneath. What the body looked like, at times you can point at.
- ``room`` --- skeletons at their true positions in the frame, thin, ramped early to late,
  with the path threading through them. Where the body went.
- ``bands`` --- one row per region of the body carrying its joint angles over time, so an
  hour compresses into a strip. What shape the body held, and when it changed.

**One function and not three.** `stroboscope()` and `multishot()` drew the same kind of
picture two ways, and having both meant a reader had to know which before choosing; they
were merged for that reason. Three skeleton views arriving as three names would recreate
the problem knowingly. They share landmarks, visibility gating and normalisation, and
differ only in what they draw.

**What each adds over what was already here.** `pose_waterfall(style='both')` draws
skeletons and trajectories in 3D, which must be rotated to be read; ``strip`` is flat.
`posegram` carries landmark SPEED, so a held posture reads as nothing at all; ``bands``
carries configuration, so a held shape is a steady band and a change of shape is an edge.
`multishot` composites photographs; ``room`` draws lines, so many more moments fit before
they occlude one another.

**All of it is downstream of the pose detector**, which is better at this than expected:
measured on a dance corpus it finds a body in 99 to 100 per cent of frames, including on the
recording whose dark costume against a black curtain defeats plate differencing. What it
loses is individual LANDMARKS --- the wrists most often --- and a row that needs one is a gap
wherever it is missing.

Frames it missed are left as GAPS rather than interpolated. Filling them would invent
posture, which is worse than admitting there is none, and in the bands view they are the
white columns that show how much of a row is actually measured.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:                              # pragma: no cover - typing only
    import musicalgestures
    from musicalgestures._utils import MgFigure, MgImage

__all__ = ["normalise_poses", "region_angles", "detection_gaps", "connecting_trajectory", "posture_traces", "smooth_trail", "lane_spacing",
           "pose_timeline_data", "pose_timeline", "mg_pose_timeline"]

PELVIS = (23, 24)          #: MediaPipe hip landmarks; their midpoint is the body's anchor
SHOULDERS = (11, 12)       #: and the shoulder midpoint sets the scale

#: Which bones belong to which region, for the bands view. Regions rather than landmarks
#: because a row per landmark is what `posegram` already gives, and thirty-three rows of
#: angle are not readable as posture.
#: **Order is head, torso, then what hangs off the torso, then legs.** The trunk belongs
#: directly under the head because that is how a body is built: arms and hands are
#: suspended from the torso, so reading them above it puts the frame beneath its own
#: limbs. `posegram` was reordered to match on the same day, so the two can be read row
#: for row --- which also means a posegram made before 2026-08-28 has its rows in a
#: different order than one made after.
REGION_BONES: dict[str, list[tuple[int, int]]] = {
    "head": [(11, 0), (12, 0)],
    "torso": [(11, 23), (12, 24)],
    "arms": [(11, 13), (12, 14), (13, 15), (14, 16)],
    "hands": [(15, 19), (16, 20)],
    "legs": [(23, 25), (24, 26), (25, 27), (26, 28)],
}


def normalise_poses(landmarks, min_visibility: float = 0.0):
    """Centre each posture on the pelvis and scale it by torso length.

    Without this a dancer stepping towards the camera reads as a change of shape, because
    every coordinate grows at once.

    Args:
        landmarks: `(frames, 33, 3)` as `extract_pose_landmarks` returns --- x, y and
            visibility.
        min_visibility (float): Landmarks below this are not trusted. A frame whose anchor
            landmarks fail it becomes a gap.

    Returns:
        np.ndarray: `(frames, 33, 2)`, with **NaN for frames the detector missed**. Gaps
        are not interpolated: filling them would invent posture.
    """
    lm = np.asarray(landmarks, dtype=float)
    xy, visible = lm[..., :2].copy(), lm[..., 2]

    anchors = list(PELVIS) + list(SHOULDERS)
    usable = (visible[:, anchors] >= min_visibility).all(axis=1)

    pelvis = xy[:, list(PELVIS)].mean(axis=1)
    shoulder = xy[:, list(SHOULDERS)].mean(axis=1)
    scale = np.linalg.norm(shoulder - pelvis, axis=1)
    usable &= scale > 0

    out = np.full(xy.shape, np.nan)
    if usable.any():
        centred = xy[usable] - pelvis[usable][:, None, :]
        out[usable] = centred / scale[usable][:, None, None]
    #: A landmark the detector was unsure of jitters, and a jittering limb is not a
    #: posture. Dropped individually, so one bad wrist does not cost a whole frame.
    out[visible < min_visibility] = np.nan
    return out


def region_angles(normalised) -> dict[str, np.ndarray]:
    """The mean angle of each region's bones from vertical, per frame, in degrees.

    0 is straight down, 90 is horizontal, 180 straight up. Configuration rather than
    speed: an arm held out stays at 90 for as long as it is held, where a speed measure
    reads a held limb as nothing.

    Args:
        normalised: `(frames, 33, 2)` from `normalise_poses`.

    Returns:
        dict: region name to `(frames,)`, NaN where the region could not be measured.
    """
    xy = np.asarray(normalised, dtype=float)
    out = {}
    for region, bones in REGION_BONES.items():
        angles = np.full((xy.shape[0], len(bones)), np.nan)
        for i, (a, b) in enumerate(bones):
            vector = xy[:, b, :] - xy[:, a, :]
            #: Image y grows downward, so "down the picture" is +y and the angle from
            #: vertical is measured against it.
            angles[:, i] = np.degrees(np.arctan2(np.abs(vector[:, 0]), vector[:, 1]))
        #: A region whose bones are all unseen is NaN, not a warning. `np.nanmean` of an
        #: all-NaN row is correct AND noisy, and a RuntimeWarning that fires on ordinary
        #: input is how a real one gets ignored later. The head region trips it whenever
        #: the nose is below visibility, which is often.
        if angles.size:
            measured = ~np.isnan(angles).all(axis=1)
            row = np.full(angles.shape[0], np.nan)
            if measured.any():
                row[measured] = np.nanmean(angles[measured], axis=1)
            out[region] = row
        else:
            out[region] = angles
    return out


def detection_gaps(landmarks, min_visibility: float = 0.5) -> list[tuple[int, int]]:
    """Half-open frame ranges the detector could not place a body in.

    Reported rather than smoothed over, because the honest answer to "what was the posture
    here" is sometimes that nobody knows.

    Returns:
        list: `(start, end)` pairs, end exclusive.
    """
    normalised = normalise_poses(landmarks, min_visibility)
    missing = np.isnan(normalised[:, list(PELVIS), 0]).any(axis=1)
    gaps, start = [], None
    for i, absent in enumerate(missing):
        if absent and start is None:
            start = i
        elif not absent and start is not None:
            gaps.append((start, i))
            start = None
    if start is not None:
        gaps.append((start, len(missing)))
    return gaps


def pose_timeline_data(landmarks, min_visibility: float = 0.5):
    """Everything the three views share: normalised postures, angles, path and gaps.

    Raises:
        ValueError: when no frame holds a usable pose. An empty figure reads as "nothing
            happened" rather than as "nobody was found", and those are different answers.
    """
    normalised = normalise_poses(landmarks, min_visibility)
    if np.isnan(normalised[:, list(PELVIS), 0]).all():
        raise ValueError(
            "no pose was detected in any frame at "
            f"min_visibility={min_visibility}. The detector finds nothing on a small or "
            "dark figure against a dark background; lower min_visibility, or accept that "
            "this recording has no skeleton to draw.")
    raw = np.asarray(landmarks, dtype=float)
    path = raw[:, list(PELVIS), :2].mean(axis=1)
    path[np.isnan(normalised[:, PELVIS[0], 0])] = np.nan
    return {"normalised": normalised, "angles": region_angles(normalised),
            "path": path, "gaps": detection_gaps(landmarks, min_visibility)}


#: **Three lines, not one, and in ROOM space.** A single wrist is the most expressive
#: landmark and the least readable: over a twenty-second gap it crosses the lane many
#: times and the curve becomes a scribble. Head, pelvis and feet together carry what a
#: body does vertically --- crouching brings the head down towards the pelvis, a jump
#: lifts the feet off their line, travelling moves all three as one.
#:
#: Each is an AVERAGE of several landmarks, which is steadier than any of them alone.
#:
#: In body space this would be flat: `normalise_poses` centres on the pelvis, so the
#: pelvis is the origin in every frame by construction, and the trunk barely moves once
#: the scale is divided out. Stability of that kind lives in room coordinates.
TRAJECTORY_GROUPS = {"head": (0, 7, 8), "pelvis": (23, 24), "feet": (27, 28, 31, 32)}

#: Kept for callers who want the gesture rather than the carriage.
TRAIL_MARKERS = (15, 16)

LANE = 2.6              #: horizontal spacing between postures, in torso lengths
LANE_WITH_TRACES = 3.8  #: and with a history drawn behind each one

#: **The skeletons are black.** A colour ramp across the strip says only "this one came
#: later", which the left-to-right order already says, and it costs contrast: a pale
#: yellow figure at the end is harder to read than a black one, and its ghosts nearly
#: invisible. Time is carried by position here, and colour is left for the views that
#: have no other way to carry it.
SKELETON = "0.1"

#: **The two kinds of line want different windows, because they say different things.**
#: A temporal trace is one limb's gesture and a third of a second keeps its shape. The
#: spatial lines are the body's CARRIAGE --- where head, pelvis and feet ride --- and at
#: the same window they thrash through a fast passage, crossing other figures and
#: damaging the whole strip rather than one cell. Roughly a second and a half at 30 fps.
#:
#: **And that is as far as smoothing takes it.** In floor work the head and pelvis really
#: do swing through large arcs many times, so a filter wide enough to calm the lines there
#: is wide enough to eat the arcs everywhere. The spatial lines are for material with a
#: stable carriage --- standing, walking, slow phrases --- and they become noise where the
#: body has none. `'temporal'` carries the fast passages, and carries them well: its
#: density stays local to each figure instead of crossing the whole strip.
SMOOTH = 9
SMOOTH_SPATIAL = 45


def smooth_trail(y, window: int = 9):
    """A moving median along a trail, leaving gaps as gaps.

    A curve drawn at every frame is unreadable exactly where the most is happening: on a
    30 fps recording the busy half of a section puts thousands of points into a few
    centimetres of paper, and the limb's real excursion disappears inside its own tremor.
    A median rather than a mean, because one badly-placed landmark should not drag the
    curve towards it.

    **It does not bridge gaps.** A window spanning missing frames would invent the posture
    in between, which is the same fault as interpolating them.

    Args:
        y: One coordinate along a trail.
        window (int): Frames in the window. 0 or 1 returns the trail untouched.

    Returns:
        np.ndarray: The smoothed trail, NaN preserved where the input was NaN.
    """
    y = np.asarray(y, dtype=float)
    if window is None or window < 2 or y.size == 0:
        return y
    half = int(window) // 2
    out = np.full(y.shape, np.nan)
    for i in range(y.size):
        if np.isnan(y[i]):
            continue                                   # a gap stays a gap
        piece = y[max(0, i - half):i + half + 1]
        finite = piece[~np.isnan(piece)]
        if finite.size:
            out[i] = np.median(finite)
    return out


def connecting_trajectory(normalised, picks, marker=TRAJECTORY_GROUPS, lane: float = LANE,
                          max_reach: float = 4.0, smooth: int = SMOOTH_SPATIAL,
                          space: str = "room",
                          raw=None, height: int = 1080):
    """The course one or more landmark groups take THROUGH the postures, lane to lane.

    Drawn over the skeletons so it is visible how one posture connects to the next.

    Args:
        normalised: `(frames, 33, 2)` from `normalise_poses`.
        picks: The sampled frame indices, ascending.
        marker: An index, a sequence of indices to average, or a mapping of name to
            indices for several lines at once. Defaults to head / pelvis / feet.
        lane (float): Horizontal spacing between postures.
        max_reach (float): In body space, points beyond this many torso lengths are
            dropped as detector noise.
        smooth (int): Moving-median window along each line. 0 draws every frame.
        space (str): `'room'` follows the group's real position in the frame, which is
            where stability lives; `'body'` follows it in the normalised space the
            skeletons are drawn in, which is where GESTURE lives --- and where the pelvis
            is flat by construction.
        raw: `(frames, 33, 3)` original landmarks, required for `space='room'`.
        height (int): Frame height, to scale room coordinates into the strip.

    Returns:
        dict: name to a list of `(x, y)` arrays, one per gap between postures.
    """
    xy = np.asarray(normalised, dtype=float)
    groups = (marker if isinstance(marker, dict)
              else {"marker": marker if isinstance(marker, (tuple, list)) else (marker,)})
    picks = list(picks)

    if space == "room":
        if raw is None:
            raise ValueError("space='room' needs the raw landmarks, which carry position")
        source = np.asarray(raw, dtype=float)[..., :2].copy()
        #: Room coordinates are pixels; the strip's vertical is about two torso lengths.
        #: Scaled by frame height and centred, so the three lines sit among the figures
        #: rather than off the page.
        source[..., 1] = (source[..., 1] / max(height, 1) - 0.5) * 3.0
        source[np.isnan(xy[..., 0])] = np.nan
    else:
        source = xy

    out: dict[str, list] = {}
    for name, indices in groups.items():
        idx = list(indices) if isinstance(indices, (tuple, list)) else [indices]
        #: The average of a few landmarks is steadier than any one of them, and a group
        #: with one missing member is still measurable from the rest --- but a frame where
        #: ALL of them are missing is NaN, not a warning. This is the same fault as in
        #: `region_angles`, fixed there and missed here: `np.nanmean` of an all-NaN row is
        #: correct and noisy, and a RuntimeWarning on ordinary input is how a real one
        #: gets ignored later.
        group = source[:, idx, :]
        measured = ~np.isnan(group[..., 0]).all(axis=1)
        centre = np.full((group.shape[0], 2), np.nan)
        if measured.any():
            centre[measured] = np.nanmean(group[measured], axis=1)
        segments = []
        for i in range(len(picks) - 1):
            a, b = picks[i], picks[i + 1]
            span = np.arange(a, b + 1)
            if len(span) < 2:
                continue
            y = smooth_trail(centre[span, 1], smooth)
            raw_x = centre[span, 0]
            x_in_lane = smooth_trail(raw_x, smooth)
            keep = np.isfinite(y) & np.isfinite(x_in_lane) & np.isfinite(raw_x)
            if space == "body":
                keep &= np.hypot(x_in_lane, y) <= max_reach
            if keep.sum() < 2:
                continue
            fraction = (span[keep] - a) / max(b - a, 1)
            #: In room space the horizontal is time alone: a pixel x would put the lines
            #: where the body was in the frame, which is the other view's job.
            anchor = 0.0 if space == "room" else raw_x[keep][0]
            anchor_end = 0.0 if space == "room" else raw_x[keep][-1]
            start = i * lane + anchor
            end = (i + 1) * lane + anchor_end
            segments.append((start + fraction * (end - start), y[keep]))
        out[name] = segments
    return out


def lane_spacing(trajectories=None) -> float:
    """How far apart to set the postures.

    A fan of ghosts needs room that bare postures do not: at the fixed spacing the busiest
    figures sat inside the previous one's history, which reads as one confused body rather
    than as two moments.
    """
    return LANE_WITH_TRACES if trajectories == "traces" else LANE


def posture_traces(normalised, picks, n_ghosts: int = 6, reach: float = 0.5):
    """Which earlier frames to draw behind each posture, and how faint each should be.

    Every landmark leaves a trace, not one --- and the traces FADE, so the direction of
    time reads. A history drawn at constant alpha is a tangle: it says a limb was in
    several places without saying which it reached last.

    Args:
        normalised: `(frames, 33, 2)` from `normalise_poses`.
        picks: The sampled frame indices.
        n_ghosts (int): Earlier frames to draw behind each posture.
        reach (float): How far back to reach, as a fraction of the gap to the previous
            sample. Short on purpose: a history covering the whole gap is the scribble
            this replaced.

    Returns:
        list: One `(frames, alphas)` pair per pick, oldest first and faintest first.
    """
    xy = np.asarray(normalised, dtype=float)
    picks = list(picks)
    out: list[tuple[list, list]] = []
    for i, frame in enumerate(picks):
        previous = picks[i - 1] if i else max(0, frame - (picks[1] - picks[0]) if len(picks) > 1 else 0)
        span = max(1, int((frame - previous) * reach))
        candidates = [f for f in range(max(0, frame - span), frame + 1)
                      if not np.isnan(xy[f, PELVIS[0], 0])]
        if not candidates:
            out.append(([], []))
            continue
        chosen = [candidates[int(round(j))] for j in
                  np.linspace(0, len(candidates) - 1, min(n_ghosts, len(candidates)))]
        alphas = np.linspace(0.08, 0.35, len(chosen))
        out.append((chosen, list(alphas)))
    return out


def _usable_frames(normalised) -> np.ndarray:
    return np.flatnonzero(~np.isnan(normalised[:, PELVIS[0], 0]))


def _draw_skeleton(ax, xy, colour, linewidth=1.0, alpha=1.0):
    """One posture, as bones. Silently skips bones with a missing end."""
    from musicalgestures._pose import MEDIAPIPE_POSE_CONNECTIONS
    for a, b in MEDIAPIPE_POSE_CONNECTIONS:
        if a < len(xy) and b < len(xy) and not (np.isnan(xy[a]).any() or np.isnan(xy[b]).any()):
            ax.plot([xy[a, 0], xy[b, 0]], [xy[a, 1], xy[b, 1]],
                    color=colour, linewidth=linewidth, alpha=alpha, solid_capstyle="round")


def render_pose_timeline(data, view: str = "strip", n_samples: int = 12,
                         raw=None, width: int = 1920, height: int = 1080,
                         times=None, cmap: str = "viridis", dpi: int = 200,
                         trajectories=None, markers=TRAJECTORY_GROUPS, smooth: int = SMOOTH,
                         space: str = "room", n_ghosts: int = 6,
                         smooth_spatial: int = SMOOTH_SPATIAL):
    """Draw one of the three views. Returns a matplotlib figure."""
    import matplotlib.pyplot as plt

    normalised, angles, path = data["normalised"], data["angles"], data["path"]
    usable = _usable_frames(normalised)
    colours = plt.get_cmap(cmap)

    if view == "strip":
        #: **Two kinds of trace, and they are not alternatives.** `'temporal'` is what a
        #: figure did around its own instant --- every landmark, fading, so the direction
        #: of time reads. `'spatial'` is how one figure connects to the next. Asking for
        #: both is the ordinary case. `'path'` adds the room route as a schematic.
        asked = ([] if trajectories is None
                 else [trajectories] if isinstance(trajectories, str)
                 else list(trajectories))
        allowed = {"temporal", "spatial", "path"}
        unknown = [a for a in asked if a not in allowed]
        if unknown:
            raise ValueError(
                f"trajectories must be drawn from {sorted(allowed)} --- singly or "
                f"together --- not {unknown[0]!r}")

        picks = usable[np.linspace(0, len(usable) - 1, min(n_samples, len(usable)))
                       .round().astype(int)]
        lane = lane_spacing("temporal" if "temporal" in asked else None)
        #: ONE PANEL. A path plot underneath said where the body was, which is the room
        #: view's job, and doubled the figure's height to say it. The timeline is the
        #: numbers under the postures.
        fig, top = plt.subplots(figsize=(max(6, len(picks) * 1.3), 3.6), dpi=dpi)

        ghosts = (posture_traces(normalised, picks, n_ghosts)
                  if "temporal" in asked else None)
        for cell, frame in enumerate(picks):
            if ghosts is not None:
                for ghost, alpha in zip(*ghosts[cell]):
                    faded = normalised[ghost].copy()
                    faded[:, 0] += cell * lane
                    _draw_skeleton(top, faded, SKELETON, 1.0, alpha=alpha)
            xy = normalised[frame].copy()
            xy[:, 0] += cell * lane
            _draw_skeleton(top, xy, SKELETON, 1.6)

        if "spatial" in asked:
            styles = {"head": (0.25, "-"), "pelvis": (0.35, "-"), "feet": (0.5, "--")}
            lines = connecting_trajectory(normalised, picks, marker=markers, lane=lane,
                                          smooth=smooth_spatial, space=space, raw=raw,
                                          height=height)
            for name, segments in lines.items():
                shade, dash = styles.get(name, (0.3, "-"))
                for x, y in segments:
                    top.plot(x, y, color=str(shade), linewidth=1.0, alpha=0.9,
                             linestyle=dash, zorder=5)

        if "path" in asked:
            finite = ~np.isnan(path[:, 0])
            if finite.any():
                px = path[finite, 0]
                lanes = (px - px.min()) / max(np.ptp(px), 1e-9) * (len(picks) - 1) * lane
                py = path[finite, 1]
                py = (py - py.min()) / max(np.ptp(py), 1e-9) * 0.8 - 2.2
                top.plot(lanes, py, color="0.55", linewidth=0.8, alpha=0.8)

        top.set_aspect("equal")
        top.invert_yaxis()                              # image y grows downward
        #: The timeline: one tick under each posture, at its own instant.
        t = np.arange(len(path)) if times is None else np.asarray(times)
        top.set_xticks([cell * lane for cell in range(len(picks))])
        top.set_xticklabels([f"{t[f]:.0f}" for f in picks], fontsize=8)
        top.set_yticks([])
        for side in ("top", "right", "left"):
            top.spines[side].set_visible(False)
        top.tick_params(axis="x", length=3)
        top.set_xlabel("time (s)" if times is not None else "time (frames)", fontsize=8)

    elif view == "room":
        from musicalgestures._multishot import choose_spaced
        candidates = [{"index": int(f), "area": 1.0,
                       "centroid": (float(path[f, 0]), float(path[f, 1]))}
                      for f in usable]
        chosen = choose_spaced(candidates, n_samples)
        fig, ax = plt.subplots(figsize=(width / 240, height / 240), dpi=dpi)
        for order, c in enumerate(chosen):
            frame = c["index"]
            xy = np.asarray(raw)[frame, :, :2].copy()
            xy[np.isnan(normalised[frame, :, 0])] = np.nan
            #: Black here too. The route and its stops carry the order, and a dozen
            #: differently-tinted skeletons in one room is harder to read, not easier.
            _draw_skeleton(ax, xy, SKELETON, 1.3)
        #: The route drawn OVER the figures, not under them: the point of this view is
        #: seeing how the postures connect, and a path behind a dozen skeletons is
        #: invisible exactly where they cluster.
        finite = ~np.isnan(path[:, 0])
        ax.plot(path[finite, 0], path[finite, 1], color="0.15", linewidth=1.2,
                alpha=0.9, zorder=5)
        #: And a dot where each drawn posture stands, so a figure can be tied to the
        #: moment on the route that produced it.
        stops = np.array([[path[c["index"], 0], path[c["index"], 1]] for c in chosen])
        ax.scatter(stops[:, 0], stops[:, 1], s=18, zorder=6,
                   c=[colours(i / max(len(chosen) - 1, 1)) for i in range(len(chosen))],
                   edgecolors="0.15", linewidths=0.6)
        #: `extract_pose_landmarks` returns PIXELS, not normalised coordinates -- checked
        #: rather than assumed: on a 640x480 recording x runs 215 to 530. The first draft
        #: set these to (0, 1) and drew every skeleton off-canvas.
        ax.set_xlim(0, width)
        ax.set_ylim(height, 0)
        ax.set_aspect("equal")
        ax.axis("off")

    elif view == "bands":
        names = list(REGION_BONES)
        grid = np.vstack([angles[n] for n in names])
        fig, ax = plt.subplots(figsize=(11, 2.6), dpi=dpi)
        span = (0, len(path) if times is None else float(np.asarray(times)[-1]))
        im = ax.imshow(grid, aspect="auto", cmap=cmap, vmin=0, vmax=180,
                       interpolation="nearest", extent=(span[0], span[1], len(names), 0))
        ax.set_yticks(np.arange(len(names)) + 0.5)
        ax.set_yticklabels(names, fontsize=8)
        #: The region names stay: without them the rows are five anonymous stripes and
        #: the figure says nothing. The time axis keeps its unit for the same reason.
        ax.set_xlabel("time (s)" if times is not None else "time (frames)", fontsize=8)
        fig.colorbar(im, ax=ax, pad=0.01)

    else:
        raise ValueError(f"view must be 'strip', 'room' or 'bands', not {view!r}")

    fig.tight_layout()
    return fig


def pose_timeline(landmarks, view: str = "strip", n_samples: int = 12,
                  min_visibility: float = 0.5, times=None, width: int = 1920,
                  height: int = 1080, cmap: str = "viridis", dpi: int = 200,
                  trajectories=None, markers=TRAJECTORY_GROUPS, smooth: int = SMOOTH,
                  space: str = "room", n_ghosts: int = 6,
                  smooth_spatial: int = SMOOTH_SPATIAL):
    """Postures and trajectories over time, as a matplotlib figure.

    Args:
        landmarks: `(frames, 33, 3)` from `extract_pose_landmarks`.
        view (str): `'strip'`, `'room'` or `'bands'`. See the module docstring.
        n_samples (int): Postures to draw, for `strip` and `room`.
        min_visibility (float): Landmarks below this are not trusted.
        times (optional): Seconds per frame, for a real time axis.
        width, height (int): The frame's size, for the `room` view's aspect.
        trajectories (str or sequence, optional): For `strip`, singly or together.
            `'temporal'` gives every landmark a fading history behind its own posture ---
            what that figure did around its instant. `'spatial'` draws head, pelvis and
            feet **through** the postures, anchored on each figure, so it is visible how
            one connects to the next: vertical is real height, horizontal is time across
            the gap. They answer different questions and asking for both is ordinary.
            `'path'` draws the
            body's route through the room across the lanes, which is a **schematic**:
            normalising the postures is what removed their translation, so the route
            cannot be to scale in that space, and it is drawn faintly and labelled.
            Defaults to None.
        markers (tuple or int): Landmark to follow for `'connect'`. Defaults to the
            wrists, of which the first is used --- the hand is where a gesture's shape is
            most legible.
        smooth (int): Moving-median window for the temporal traces, in frames. Defaults
            to 9, about a third of a second at 30 fps; 0 draws every frame.
        smooth_spatial (int): The window for the spatial lines, which want a wider one:
            they carry carriage rather than gesture, and at the traces' window they thrash
            through a fast passage and cross other figures. Defaults to 45, about a second
            and a half at 30 fps. **A window wider than the gap between two postures
            flattens that segment to a constant**, so a short recording sampled many times
            wants it lowered along with `n_samples`.
        cmap (str), dpi (int): Appearance.

    Returns:
        matplotlib.figure.Figure

    Raises:
        ValueError: when no frame holds a usable pose, or `view` is not one of the three.
    """
    data = pose_timeline_data(landmarks, min_visibility)
    return render_pose_timeline(data, view=view, n_samples=n_samples, raw=landmarks,
                                width=width, height=height, times=times, cmap=cmap,
                                dpi=dpi, trajectories=trajectories, markers=markers,
                                smooth=smooth, space=space, n_ghosts=n_ghosts,
                                smooth_spatial=smooth_spatial)


def mg_pose_timeline(self: "musicalgestures.MgVideo", view: str = "strip",
                     n_samples: int = 12, min_visibility: float = 0.5,
                     landmarks=None, times=None, cmap: str = "viridis", dpi: int = 200,
                     trajectories=None, markers=TRAJECTORY_GROUPS, smooth: int = SMOOTH,
                     smooth_spatial: int = SMOOTH_SPATIAL,
                     target_name: str | None = None, overwrite: bool = True,
                     **pose_kwargs) -> "MgFigure":
    """Postures and trajectories over time. See `pose_timeline`.

    Landmarks come from a cached `pose()` result when there is one, exactly as `posegram`
    resolves them, and otherwise from a fresh extraction.
    """
    import matplotlib.pyplot as plt

    from musicalgestures._utils import MgFigure, resolve_filename

    if landmarks is None:
        from musicalgestures._posetools import extract_pose_landmarks
        result = extract_pose_landmarks(self.filename, quiet=True, verbose=False,
                                        **pose_kwargs)
        landmarks = result["landmarks"]
        #: The key is `time`, not `times`. Asking for the wrong one silently gave frame
        #: numbers on an axis labelled seconds, which is a plausible-looking wrong answer.
        times = result.get("time")
        if times is None and result.get("fps"):
            times = np.arange(len(landmarks)) / float(result["fps"])

    target_name = resolve_filename(self.of, f"_posetimeline_{view}.png", target_name,
                                   overwrite)
    figure = pose_timeline(landmarks, view=view, n_samples=n_samples,
                           min_visibility=min_visibility, times=times,
                           width=self.width, height=self.height, cmap=cmap, dpi=dpi,
                           trajectories=trajectories, markers=markers, smooth=smooth,
                           smooth_spatial=smooth_spatial)
    figure.savefig(target_name, dpi=dpi)
    plt.close(figure)
    self.pose_timeline_figure = MgFigure(
        figure=figure, figure_type="video.posetimeline",
        data={"view": view}, layers=None, image=target_name)
    return self.pose_timeline_figure

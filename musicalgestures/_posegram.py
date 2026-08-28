"""The posegram: which part of the body moved, and when.

A motiongram collapses one spatial axis of the image per frame and stacks the result over
time. A posegram does the same thing with the body as the frame of reference instead of
the image: one row per landmark, one column per frame, brightness for how fast that
landmark was moving. Read across for a body part's history; read down for a moment's
posture of activity.

It answers what the other pose views do not. `pose_waterfall` and the trajectory renders
say where the body went, `pose_segments` how its limbs were angled, `pose_center` how its
centre moved --- and none of them says *what was moving at 04:12*, which is the question a
motiongram answers for pixels and the one an annotator usually has.

**The row order is the design.** MediaPipe emits its 33 landmarks in model order, which
scatters the body: nose, eyes, ears, mouth, then shoulders, elbows, wrists, then eight
hand points, then hips, knees, ankles, feet. Plotted that way an arm is four rows in
three places and the image says nothing. Ordered head to foot it reads as a body, and a
moving limb is a contiguous band.
"""
from __future__ import annotations

import os

import musicalgestures
from musicalgestures._utils import resolve_filename

#: MediaPipe Pose landmark indices, head to foot, with left and right adjacent so a
#: symmetric movement reads as one band rather than two. Hands are kept together and
#: placed after the wrists they belong to.
ANATOMICAL_ORDER = [
    0,                                   # nose
    1, 2, 3, 4, 5, 6,                    # eyes: inner, centre, outer, both sides
    7, 8,                                # ears
    9, 10,                               # mouth
    11, 12,                              # shoulders
    13, 14,                              # elbows
    15, 16,                              # wrists
    17, 18,                              # pinkies
    19, 20,                              # index fingers
    21, 22,                              # thumbs
    23, 24,                              # hips
    25, 26,                              # knees
    27, 28,                              # ankles
    29, 30,                              # heels
    31, 32,                              # foot index
]

#: Where to draw a dividing line and what to call the band above it, for a readable axis.
BANDS = [("head", 11), ("arms", 23), ("hands", 23), ("torso", 25), ("legs", 33)]


def pose_activity(landmarks, anatomical: bool = False):
    """Speed of every landmark, per frame.

    Args:
        landmarks (np.ndarray): `(frames, landmarks, 3)` as `extract_pose_landmarks`
            returns it --- x, y and visibility --- with all-NaN rows where no pose was
            found.
        anatomical (bool, optional): Return the rows in `ANATOMICAL_ORDER` rather than in
            MediaPipe's. Defaults to False, so the array keeps model indexing unless the
            caller asks for the readable order.

    Returns:
        np.ndarray: `(landmarks, frames)`, in pixels per frame.

    Notes:
        Frames where no pose was detected arrive as NaN, and differencing across one would
        invent a large displacement on the way in and another on the way out. Those
        differences are dropped rather than filled, so an undetected stretch reads as no
        movement rather than as two spikes around a gap.
    """
    import numpy as np

    a = np.asarray(landmarks, dtype=np.float64)
    step = np.linalg.norm(np.diff(a[:, :, :2], axis=0), axis=2)
    step = np.where(np.isfinite(step), step, 0.0)
    #: One column per input frame: the first frame has no predecessor, so it carries the
    #: second frame's value rather than a zero that would read as a pause at every start.
    activity = np.concatenate([step[:1], step], axis=0).T
    if anatomical:
        activity = activity[ANATOMICAL_ORDER]
    return activity


def mg_posegram(self: "musicalgestures.MgVideo", landmarks=None, times=None,
                colormap: str = "magma", gamma: float = 0.5, max_width: int = 4000,
                dpi: int = 130, target_name: str | None = None,
                overwrite: bool = True) -> "musicalgestures.MgFigure":
    """Draw the posegram: landmarks head to foot down the page, time across it.

    Args:
        landmarks (np.ndarray, optional): `(frames, 33, 3)` from a previous
            `extract_pose_landmarks` call. Defaults to None, which runs pose here ---
            expensive on a long recording, so pass a saved extraction when you have one.
        times (array-like, optional): Seconds per frame, needed whenever the landmarks
            were not sampled at the video's own frame rate. Pose is usually extracted at
            a reduced rate, so this is usually needed.
        colormap (str, optional): Defaults to `'magma'`.
        gamma (float, optional): Applied before colouring so quiet passages stay visible.
            Defaults to 0.5.
        max_width (int, optional): Widest the drawn image may be. One column per frame
            makes a 149-megapixel picture of a long session; columns are pooled by
            maximum above this, so a brief accent still shows. Defaults to 4000.
        dpi (int, optional): Defaults to 130.
        target_name (str, optional): Output path. Defaults to the input name with
            `_posegram`.
        overwrite (bool, optional): Defaults to True.

    Returns:
        MgFigure: the posegram, with the activity array in `.data`.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    from musicalgestures._utils import MgFigure

    of, fex = os.path.splitext(self.filename)
    target_name = resolve_filename(of, '_posegram.png', target_name, overwrite)

    if landmarks is None:
        from musicalgestures._posetools import extract_pose_landmarks
        r = extract_pose_landmarks(self.filename, quiet=True, verbose=False)
        landmarks, times = r["landmarks"], r["time"]
    activity = pose_activity(landmarks, anatomical=True)
    times = (np.asarray(times, dtype=np.float64) if times is not None
             else np.arange(activity.shape[1]) / float(self.fps))

    drawn = activity
    if drawn.shape[1] > max_width:
        edges = np.linspace(0, drawn.shape[1], max_width + 1).astype(int)
        drawn = np.stack([drawn[:, a:max(b, a + 1)].max(axis=1)
                          for a, b in zip(edges[:-1], edges[1:])], axis=1)
    ceiling = np.percentile(drawn[drawn > 0], 99) if (drawn > 0).any() else 1.0
    shown = np.power(np.clip(drawn / max(ceiling, 1e-9), 0, 1), gamma)

    minutes = (times[-1] / 60) if len(times) else 1
    fig, ax = plt.subplots(figsize=(15, 6), dpi=dpi)
    ax.imshow(shown, cmap=colormap, aspect="auto", interpolation="nearest",
              extent=(0, minutes, len(ANATOMICAL_ORDER), 0))
    seen = set()
    for label, upto in BANDS:
        if label in seen:
            continue
        seen.add(label)
        ax.axhline(upto, color="white", linewidth=0.6, alpha=0.35)
    ax.set_yticks([5, 14, 20, 24, 29])
    ax.set_yticklabels(["head", "arms", "hands", "torso", "legs"], fontsize=9)
    ax.set_xlabel("minutes")
    ax.set_title(f"{os.path.basename(self.filename)} --- posegram "
                 f"(landmark speed, head to foot)", fontsize=10)
    fig.tight_layout()
    fig.savefig(target_name)
    plt.close(fig)

    self.posegram_figure = MgFigure(
        figure=None, figure_type="video.posegram",
        data={"activity": activity, "time": times, "order": ANATOMICAL_ORDER},
        layers=None, image=target_name)
    return self.posegram_figure


def pose_spatial_gram(landmarks, height, width, bins: int = 200,
                      axis: str = "vertical", weight: str = "speed", spread: float = 1.0):
    """A posegram on the image's own axes, directly comparable with a motiongram.

    The landmark-row posegram above says which body part moved. This says **at what
    height** something moved, which is what a vertical motiongram says, so the two can be
    laid on top of each other: a body crossing the frame draws the same diagonal in both,
    and where they disagree one of them is wrong about the body.

    Args:
        landmarks (np.ndarray): `(frames, 33, 3)` in pixel coordinates.
        height (int): Frame height, for scaling y onto the bins.
        width (int): Frame width, used when `axis='horizontal'`.
        bins (int, optional): Rows in the output. Defaults to 200.
        axis (str, optional): `'vertical'` bins by y, matching a vertical motiongram;
            `'horizontal'` bins by x. Defaults to `'vertical'`.
        weight (str, optional): `'speed'` brightens a bin by how fast the landmarks in it
            are moving, which is the motiongram's own quantity. `'presence'` brightens it
            by how many landmarks are there at all, which shows posture instead --- a
            dancer standing still has presence and no speed. Defaults to `'speed'`.
        spread (float, optional): Landmarks are points and a motiongram is continuous, so
            each is smeared over this many bins to make a comparable picture. Defaults
            to 1.0.

    Returns:
        np.ndarray: `(bins, frames)`.

    Notes:
        Landmarks outside the frame, and frames with no pose, contribute nothing rather
        than being clamped to an edge --- clamping would pile a lost limb onto row 0 and
        draw a bright line along the top of the plot that no body ever made.
    """
    import numpy as np

    a = np.asarray(landmarks, dtype=np.float64)
    n_frames = a.shape[0]
    coord = a[:, :, 1] if axis == "vertical" else a[:, :, 0]
    span = float(height if axis == "vertical" else width)

    if weight == "speed":
        w = pose_activity(a).T                       # (frames, landmarks)
    elif weight == "presence":
        w = np.where(np.isfinite(coord), 1.0, 0.0)
    else:
        raise ValueError(f"weight must be 'speed' or 'presence', not {weight!r}")

    gram = np.zeros((bins, n_frames), dtype=np.float64)
    row = coord / max(span, 1e-9) * bins
    inside = np.isfinite(row) & (row >= 0) & (row < bins) & np.isfinite(w)
    reach = max(int(round(spread)), 0)
    for offset in range(-reach, reach + 1):
        #: Undetected frames are NaN, and casting NaN to an integer is undefined --- it
        #: warns and yields whatever the platform produces. The mask below discards those
        #: entries anyway, so they are replaced with an out-of-range sentinel before the
        #: cast rather than being cast and then thrown away.
        shifted = np.where(np.isfinite(row), row + offset, -1.0)
        r = np.rint(shifted).astype(np.int64, copy=False)
        ok = inside & (r >= 0) & (r < bins)
        if not ok.any():
            continue
        frames = np.repeat(np.arange(n_frames), a.shape[1]).reshape(n_frames, -1)
        np.add.at(gram, (r[ok], frames[ok]), w[ok])
    return gram


def mg_posegram_spatial(self: "musicalgestures.MgVideo", landmarks=None, times=None,
                        frame_size=None,
                        axis: str = "vertical", weight: str = "speed", bins: int = 200,
                        colormap: str = "magma", gamma: float = 0.5,
                        max_width: int = 4000, dpi: int = 130,
                        target_name: str | None = None,
                        overwrite: bool = True) -> "musicalgestures.MgFigure":
    """The posegram drawn on the image's axes, so it lines up with a motiongram.

    `posegram()` puts one landmark per row, which answers "which body part moved". This
    puts **image position** on the vertical axis instead, which is what a motiongram does,
    so a body crossing the frame draws the same diagonal in both and the two can be laid
    against each other. Where they disagree, the pixels saw something the pose model did
    not, or the other way round.

    Args:
        landmarks (np.ndarray, optional): `(frames, 33, 3)` in pixel coordinates from a
            previous extraction. Defaults to None, which runs pose here.
        times (array-like, optional): Seconds per frame. Pose is usually extracted at a
            reduced rate, so this is usually needed.
        frame_size (tuple, optional): `(width, height)` the landmarks were extracted in.
            **Pass this whenever you pass `landmarks`.** MediaPipe estimates landmarks it
            cannot see and puts them outside the picture --- on a real 640x360 extraction
            the largest y was 1529, four times the frame --- so inferring the frame from
            the data squeezes the whole body into a corner of the plot. Without it a high
            percentile is used, which is robust but still a guess.
        axis (str, optional): `'vertical'` bins by y, to match a vertical motiongram;
            `'horizontal'` bins by x. Defaults to `'vertical'`.
        weight (str, optional): `'speed'` for motion at each height, the motiongram's own
            quantity; `'presence'` for where the body is regardless of movement. Defaults
            to `'speed'`.
        bins (int, optional): Rows. Defaults to 200.
        colormap, gamma, max_width, dpi, target_name, overwrite: as `posegram()`.

    Returns:
        MgFigure: the gram, with the array in `.data`.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    from musicalgestures._utils import MgFigure

    of, fex = os.path.splitext(self.filename)
    target_name = resolve_filename(of, '_posegram_spatial.png', target_name, overwrite)

    if landmarks is None:
        from musicalgestures._posetools import extract_pose_landmarks
        r = extract_pose_landmarks(self.filename, quiet=True, verbose=False)
        landmarks, times = r["landmarks"], r["time"]
        height, width = r["height"], r["width"]
    elif frame_size is not None:
        width, height = float(frame_size[0]), float(frame_size[1])
    else:
        #: No frame given, so it has to be inferred --- and NOT from the maximum, which is
        #: an estimated landmark somewhere outside the picture. A high percentile tracks
        #: the body and ignores the extrapolations.
        a = np.asarray(landmarks, dtype=np.float64)
        if np.isfinite(a).any():
            height = float(np.nanpercentile(a[:, :, 1], 99.5)) * 1.05
            width = float(np.nanpercentile(a[:, :, 0], 99.5)) * 1.05
        else:
            height = width = 1.0

    gram = pose_spatial_gram(landmarks, height=height, width=width, bins=bins,
                             axis=axis, weight=weight)
    times = (np.asarray(times, dtype=np.float64) if times is not None
             else np.arange(gram.shape[1]) / float(self.fps))

    drawn = gram
    if drawn.shape[1] > max_width:
        edges = np.linspace(0, drawn.shape[1], max_width + 1).astype(int)
        drawn = np.stack([drawn[:, a:max(b, a + 1)].max(axis=1)
                          for a, b in zip(edges[:-1], edges[1:])], axis=1)
    ceiling = np.percentile(drawn[drawn > 0], 99) if (drawn > 0).any() else 1.0
    shown = np.power(np.clip(drawn / max(ceiling, 1e-9), 0, 1), gamma)

    minutes = (times[-1] / 60) if len(times) else 1
    fig, ax = plt.subplots(figsize=(15, 5.5), dpi=dpi)
    ax.imshow(shown, cmap=colormap, aspect="auto", interpolation="nearest",
              extent=(0, minutes, bins, 0))
    ax.set_xlabel("minutes")
    ax.set_ylabel("top of frame  →  bottom" if axis == "vertical"
                  else "left of frame  →  right")
    ax.set_yticks([])
    ax.set_title(f"{os.path.basename(self.filename)} --- pose {axis} gram "
                 f"({weight}, on the image's own axis)", fontsize=10)
    fig.tight_layout()
    fig.savefig(target_name)
    plt.close(fig)

    self.posegram_spatial_figure = MgFigure(
        figure=None, figure_type="video.posegram_spatial",
        data={"gram": gram, "time": times, "axis": axis, "weight": weight},
        layers=None, image=target_name)
    return self.posegram_spatial_figure

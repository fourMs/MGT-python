"""Postures: the static row's middle term.

The toolbox describes movement at three levels: motion is continuous displacement, an
action is a segment of motion, and a gesture is an action carrying meaning (`_actions`).
Bodies that are not moving need the same three levels, and the words are position,
posture, and pose (*Sound Actions*, pp. 68--69; the review behind the wording is in
``plans/2026-09-01-position-posture-pose-terminology.md``).

**Position** is the measured level: where a point is in space. A pose-estimation model
returns positions --- landmark coordinates per frame --- and nothing more. The name
"pose estimation" is the computer-vision loanword and is kept in function names such as
``pose()``; in the terms used here, what those functions return are landmark positions.

**A posture** is a configuration: how the parts of the body are placed relative to each
other, with the location in the room taken out. Standing, kneeling and a T-shape are
postures. A posture is to position what an action is to motion: a chunk a person would
name.

**A pose** is a posture with meaning, typically assumed for an observer, and meaning is
not a property of the signal. So this module segments postures from landmark positions,
and then lets labels be *attached* to postures --- to some of them, not all --- exactly
as `_actions` keeps segmentation apart from recognition. Nothing here detects a pose; it
can only propose that a held posture is one.

The stability criterion follows the Movement--Hold model of sign-language phonology
(Liddell & Johnson 1989): a hold is a stretch in which *all* aspects of the configuration
remain stationary. Stationarity is therefore judged on the fastest-moving part of the
body (a high percentile across landmarks), not on the average, since an average would
call a body still while one arm travels.

All configurations are body-normalised (`normalise_poses`: pelvis at the origin, torso
length 1), so distances are in torso lengths and rates in torso lengths per second, and
the same thresholds transfer between recordings, spaces and bodies of different size.

.. note::

   The neighbouring module ``_posture`` (singular) holds posturography re-exports from
   ``micromotion``: balance and sway metrics, which quantify the small movements of
   *maintaining* a posture. That is movement science's sense of the word --- posture as a
   regulated process --- and it lives on the dynamic row. This module owns the static
   sense: a posture as a held configuration.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np

import musicalgestures
from musicalgestures._posetimeline import PELVIS, normalise_poses


@dataclass
class Posture:
    """One held configuration, with somewhere to record what it was.

    Attributes:
        start (float): Start time in seconds.
        end (float): End time in seconds.
        source (str): What produced this span, so that spans from different segmenters
            can be told apart when they are pooled.
        configuration (np.ndarray): The representative body configuration of the span,
            ``(landmarks, 2)`` in body-normalised units: the per-landmark median over the
            span's frames. NaN where a landmark was never seen.
        labels (dict): Names given to this posture by recognisers, keyed by recogniser.
            Empty is the normal state: most postures are never named, and a posture with
            no label is still a posture. This is where a pose would be recorded, if
            anything could establish one.
        features (dict): Numbers describing the span, from :func:`posture_shape` and
            anything else that measures without naming.
    """

    start: float
    end: float
    source: str = "unknown"
    configuration: np.ndarray | None = None
    labels: dict = field(default_factory=dict)
    features: dict = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Length of the posture in seconds."""
        return self.end - self.start

    def overlaps(self, other: "Posture") -> bool:
        """Whether this posture shares any time with `other`."""
        return self.start < other.end and other.start < self.end

    def __repr__(self) -> str:
        named = f" {self.labels}" if self.labels else ""
        return f"<Posture {self.start:.2f}-{self.end:.2f}s ({self.source}){named}>"


def configuration_distance(a, b, percentile: float = 95.0) -> float:
    """How far apart two body configurations are, in torso lengths.

    Judged, like the hold criterion, on the most-displaced parts of the body: the given
    percentile of per-landmark distances, over the landmarks present in both. A mean
    would dilute two moved arms across thirty-one unmoved landmarks until a T-shape and
    arms-at-rest read as nearly the same shape.

    Args:
        a: Configuration ``(landmarks, 2)`` in body-normalised units.
        b: Configuration of the same shape.
        percentile (float): Which per-landmark distance speaks for the whole body.
            Defaults to 95.0, high enough to mean "everything agrees" and robust to one
            stray landmark.

    Returns:
        float: The distance, or NaN if no landmark is present in both.
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = np.linalg.norm(a - b, axis=-1)
    if not np.isfinite(d).any():
        return float("nan")
    return float(np.nanpercentile(d, percentile))


def _configuration_speeds(normalised: np.ndarray, fs: float, window: int) -> np.ndarray:
    """Per-frame rate of configuration change, in torso lengths per second.

    Measured as the displacement of the window-median configuration across `window`
    frames. The median rather than the mean, and a stride rather than a one-frame
    difference, because detector jitter does not accumulate while a real change of
    shape does: measured on this project's dance corpus, a seated person's knee sat
    within 1.2 px at one frame's lag and only 2.7 px after 5 s --- pure jitter --- yet on
    a seated body whose 2D torso spans 43 px that one-frame flutter reads as 0.15 torso
    lengths per second, twice the hold threshold. Displacement of window medians across
    the stride keeps such a body still while any actual transition, which moves
    landmarks by whole torso lengths, remains unmistakable.
    """
    n = len(normalised)
    if n <= window:
        return np.zeros(n)
    smoothed = np.full_like(normalised, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN windows
        view = np.lib.stride_tricks.sliding_window_view(normalised, window, axis=0)
        centre = window // 2
        smoothed[centre:centre + view.shape[0]] = np.nanmedian(view, axis=-1)
    for i in range(centre):
        smoothed[i] = smoothed[centre]
    for i in range(centre + n - window + 1, n):
        smoothed[i] = smoothed[centre + n - window]

    step = np.linalg.norm(smoothed[window:] - smoothed[:-window], axis=-1)
    rate = np.full(len(step), np.nan)
    measurable = np.isfinite(step).any(axis=1)
    if measurable.any():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            rate[measurable] = np.nanpercentile(step[measurable], 95.0, axis=1)
    rate *= fs / window
    # centre each measurement on its span, and let the edges borrow their neighbour:
    # an edge frame has no worse evidence than the nearest measured one
    out = np.empty(n)
    half = window // 2
    out[half:half + len(rate)] = rate
    out[:half] = rate[0]
    out[half + len(rate):] = rate[-1]
    return out


def segment_postures(landmarks, fs: float, stability: float = 0.1,
                     min_duration: float = 1.0, min_gap: float = 0.25,
                     min_visibility: float = 0.0, smooth: float = 0.4,
                     source: str = "landmarks") -> list[Posture]:
    """Cut landmark trajectories into postures, where the configuration holds still.

    A posture begins where the body's configuration stops changing and ends where it
    changes again. The judgement is body-relative on both sides: configurations are
    pelvis-centred and torso-scaled first, so a dancer walking across the frame in a held
    T-shape is one posture, since position is not posture. Stationarity is judged on the
    fastest-moving landmark region (95th percentile), following the Movement--Hold rule
    that a hold is a stretch in which everything remains stationary.

    Frames the detector missed are unknown, not held: they never extend a posture, and a
    wobble is only bridged when every frame in it was actually observed. A recording in
    which the body never stops holds no postures, which is the correct answer for
    continuous movement rather than an error.

    Args:
        landmarks: ``(frames, 33, 3)`` as ``extract_pose_landmarks`` returns --- x, y and
            visibility.
        fs (float): Sampling rate of the landmarks, in frames per second.
        stability (float): Fastest configuration change still counting as held, in torso
            lengths per second. Defaults to 0.1: for an adult torso of roughly half a
            metre this is about 5 cm/s at the fastest-moving landmark, an order above
            postural sway and an order below deliberate movement.
        min_duration (float): Holds shorter than this, in seconds, are not postures.
            Defaults to 1.0. (Ergonomics counts a working posture as static from 4 s,
            ISO 11226; dance holds are briefer, and 1 s keeps both reachable by
            parameter.)
        min_gap (float): Wobbles shorter than this, in seconds, are bridged --- but only
            when every frame in them was observed. Defaults to 0.25.
        min_visibility (float): Passed to `normalise_poses`; landmarks below it are not
            trusted. Defaults to 0.0.
        smooth (float): Width of the median-and-stride window, in seconds, behind the
            rate measurement. Defaults to 0.4, long enough that detector jitter cancels
            even on a small or foreshortened body (measured on a seated dancer whose 2D
            torso spanned 43 px), and short enough not to blur a boundary by more than
            half of `min_duration`. A wobble briefer than this window is invisible by
            design; `min_gap` handles the ones between this width and itself.
        source (str): Recorded on each Posture, to identify what produced it.

    Returns:
        list: The postures found, in time order, each carrying its median configuration.
    """
    lm = np.asarray(landmarks, float)
    if lm.ndim != 3 or len(lm) < 2 or fs <= 0:
        return []

    normalised = normalise_poses(lm, min_visibility)
    # A frame is observed when the body was seen well enough to normalise: the anchor
    # landmarks passed. Individual landmarks the detector was unsure of are already NaN
    # and simply do not testify --- demanding every ear and ankle would throw away
    # nearly all real footage, since detectors are routinely unsure at the extremities.
    observed = np.isfinite(normalised).any(axis=(1, 2))
    if not observed.any():
        return []

    window = max(2, int(round(smooth * fs)))
    rate = _configuration_speeds(normalised, fs, window)
    held = observed & np.isfinite(rate) & (rate < stability)
    if not held.any():
        return []

    edges = np.diff(held.astype(np.int8))
    starts = list(np.flatnonzero(edges == 1) + 1)
    ends = list(np.flatnonzero(edges == -1) + 1)
    if held[0]:
        starts.insert(0, 0)
    if held[-1]:
        ends.append(len(held))

    # bridge short observed wobbles first, exactly as `segment_actions` closes short
    # gaps before dropping short spans; an unobserved gap is never bridged, because
    # claiming a posture across frames nobody saw would invent one
    spans: list[list[int]] = []
    for s, t in zip(starts, ends):
        if (spans and (s - spans[-1][1]) < min_gap * fs
                and observed[spans[-1][1]:s].all()):
            spans[-1][1] = t
        else:
            spans.append([s, t])

    postures = []
    for s, t in spans:
        if (t - s) / fs < min_duration:
            continue
        frames = normalised[s:t][observed[s:t]]
        if len(frames):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)  # never-seen landmarks
                configuration = np.nanmedian(frames, axis=0)
        else:
            configuration = None
        postures.append(Posture(start=s / fs, end=t / fs, source=source,
                                configuration=configuration))
    return postures


def average_posture(landmarks, min_visibility: float = 0.0) -> np.ndarray:
    """The habitual carriage of a recording: the median configuration over every frame.

    This is posture in the dictionary's second sense --- "a characteristic way of bearing
    one's body" --- and it is computed over all observed frames, moving and held alike,
    so it describes how this body tends to be organised rather than any moment of it.
    The median rather than the mean, because a recording is mostly transitions, and a
    mean would let every wave of an arm pull the resting arm position towards it.

    Comparing the average postures of two dancers with :func:`configuration_distance`
    says how differently they carry themselves; comparing a posture's `configuration`
    against its own recording's average says how far from habit that hold is.

    Args:
        landmarks: ``(frames, landmarks, 3)`` trajectories --- x, y and visibility.
        min_visibility (float): Passed to `normalise_poses`. Defaults to 0.0.

    Returns:
        np.ndarray: ``(landmarks, 2)`` in body-normalised units, NaN where a landmark
        was never seen.
    """
    normalised = normalise_poses(np.asarray(landmarks, float), min_visibility)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # never-seen landmarks
        return np.nanmedian(normalised, axis=0)


def posture_shape(configuration) -> dict:
    """Describe one configuration in numbers, without naming it.

    Three measures, all in torso lengths, chosen because they are the ones the
    surrounding literatures already read: `spread` is the RMS distance of landmarks from
    their centroid, which is the open-versus-closed axis psychology calls expansiveness;
    `width` and `height` are the horizontal and vertical extents.

    Args:
        configuration: ``(landmarks, 2)`` in body-normalised units.

    Returns:
        dict: ``spread``, ``width`` and ``height``.
    """
    c = np.asarray(configuration, float)
    finite = np.isfinite(c).all(axis=1)
    out = {"spread": 0.0, "width": 0.0, "height": 0.0}
    if not finite.any():
        return out
    pts = c[finite]
    centroid = pts.mean(axis=0)
    out["spread"] = float(np.sqrt(np.mean(np.sum((pts - centroid) ** 2, axis=1))))
    out["width"] = float(pts[:, 0].max() - pts[:, 0].min())
    out["height"] = float(pts[:, 1].max() - pts[:, 1].min())
    return out


def describe_postures(postures: list[Posture]) -> list[Posture]:
    """Attach :func:`posture_shape` to each posture, in place, and return them.

    Measuring is kept apart from naming on purpose: this fills `features`, never
    `labels`. A shape is something the configuration shows; a name is something a
    recogniser claims.

    Args:
        postures (list): Postures to describe, as returned by :func:`segment_postures`.

    Returns:
        list: The same postures, with `features` filled in.
    """
    for p in postures:
        if p.configuration is not None:
            p.features.update(posture_shape(p.configuration))
    return postures


def key_postures(postures: list[Posture], radius: float = 0.2) -> list[dict]:
    """Group recurring postures, without deciding in advance which postures exist.

    The "key postures" of a recording (*Sound Actions*, ch. 12) are the configurations a
    body keeps returning to. They are found here by grouping, not by a fixed catalogue of
    standing and sitting, because which postures matter is a property of the material:
    a pianist's key postures are hand shapes, a dancer's are whole bodies.

    Greedy grouping by :func:`configuration_distance`: the longest-held posture founds
    the first group, and every posture joins the first group whose exemplar it sits
    within `radius` of.

    Args:
        postures (list): Postures to group, as returned by :func:`segment_postures`.
        radius (float): How far a configuration may sit from a group's exemplar and still
            be the same posture, in torso lengths. Defaults to 0.2.

    Returns:
        list: One dict per group --- ``exemplar``, ``postures`` and ``total_duration`` ---
        sorted by total time held, longest first.
    """
    clusters: list[dict] = []
    for p in sorted((p for p in postures if p.configuration is not None),
                    key=lambda p: -p.duration):
        for cluster in clusters:
            if configuration_distance(p.configuration, cluster["exemplar"]) <= radius:
                cluster["postures"].append(p)
                break
        else:
            clusters.append({"exemplar": p.configuration, "postures": [p]})
    for cluster in clusters:
        cluster["postures"].sort(key=lambda p: p.start)
        cluster["total_duration"] = float(sum(p.duration for p in cluster["postures"]))
    clusters.sort(key=lambda c: -c["total_duration"])
    return clusters


def match_postures(postures: list[Posture], template, name: str,
                   radius: float = 0.2, recogniser: str = "template") -> list[Posture]:
    """Label the postures that match a template configuration --- a pose by example.

    This is the smallest honest recogniser: a pose is defined by showing one, and every
    posture within `radius` of it is proposed as that pose. The label lands in `labels`,
    keyed by `recogniser`, and postures that do not match are left exactly as they were,
    because an unlabelled posture is still a posture.

    Args:
        postures (list): Postures to examine, as returned by :func:`segment_postures`.
        template: The configuration that defines the pose, ``(landmarks, 2)`` in
            body-normalised units --- typically the `configuration` of a posture from a
            recording of the pose being demonstrated.
        name (str): What to call postures that match.
        radius (float): How far a configuration may sit from the template and still count,
            in torso lengths. Defaults to 0.2.
        recogniser (str): The key the label is filed under. Defaults to ``"template"``.

    Returns:
        list: The same postures, some now labelled.
    """
    for p in postures:
        if p.configuration is None:
            continue
        if configuration_distance(p.configuration, template) <= radius:
            p.labels[recogniser] = name
    return postures


def mg_postures(self: "musicalgestures.MgVideo", landmarks=None, fs: float | None = None,
                stability: float = 0.1, min_duration: float = 1.0,
                min_gap: float = 0.25, **pose_kwargs) -> list[Posture]:
    """Segment this video into postures and describe the shape of each.

    With no landmarks given, they are taken from a cached ``pose()`` result when there is
    one, and extracted fresh otherwise. The result is the static counterpart of
    ``actions_from_motion()``: where that cuts the recording where the body moves, this
    cuts it where the body holds.

    Args:
        landmarks: ``(frames, 33, 3)`` landmark trajectories. Defaults to None, meaning
            use the cached pose data or extract them.
        fs (float, optional): Sampling rate of `landmarks`. Defaults to the video's frame
            rate.
        stability (float): Fastest configuration change still counting as held, in torso
            lengths per second. Defaults to 0.1.
        min_duration (float): Shortest hold kept, in seconds. Defaults to 1.0.
        min_gap (float): Longest observed wobble bridged, in seconds. Defaults to 0.25.
        **pose_kwargs: Forwarded to ``pose()`` if landmarks have to be computed.

    Returns:
        list: The postures found, each carrying its configuration and shape. Also stored
        on the video as `postures`.
    """
    rate = float(fs) if fs is not None else float(self.fps)
    if landmarks is None:
        from musicalgestures._pose import _ensure_pose_keypoints, pose_cache_landmarks

        cache = _ensure_pose_keypoints(self, **pose_kwargs)
        landmarks = pose_cache_landmarks(cache)
        if isinstance(cache, dict) and cache.get("fps") and fs is None:
            rate = float(cache["fps"])

    postures = segment_postures(landmarks, rate, stability=stability,
                                min_duration=min_duration, min_gap=min_gap,
                                source="pose-landmarks" if fs is None else "landmarks")
    describe_postures(postures)
    self.postures = postures
    return postures

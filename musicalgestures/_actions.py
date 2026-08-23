"""Actions: the layer between motion and meaning.

Three words, and this module owns the middle one.

**Motion** is continuous displacement in space over time. The toolbox already measures it:
quantity of motion, optical flow, pose landmarks.

**An action** is a segment of that motion, usually with a beginning and an end. Reaching for
a cup is an action; so is a drum stroke; so is a phrase of dance that is going nowhere in
particular. Actions need not be goal-directed, and in music they are often sound-producing.

**A gesture** is an action carrying meaning, and meaning is not a property of the signal. A
recogniser can say a segment looks like someone waving; whether that wave means *hello*,
*stop* or nothing at all is not visible in the pixels. So this module derives actions from
motion, and then lets labels be *attached* to actions --- to some of them, not all --- rather
than pretending that recognition and meaning are one step.

That layering is the design. :class:`Action` is a span with provenance and a place to hang
labels. :func:`segment_actions` produces spans from a motion envelope. :func:`action_type`
describes a span in terms of how the movement is distributed within it. Recognisers, of
which there can be several and which may disagree, add named labels to spans they did not
have to produce.

The point of separating them is that the segmenter and the recogniser fail differently. A
segmenter that misses a boundary loses an action entirely; a recogniser that guesses wrong
leaves the action there to be relabelled. Keeping the record of *what happened when* apart
from *what it was* means the second can be revised without redoing the first.

.. note::

   Everything here works from a **motion envelope** --- a one-dimensional series saying how
   much movement there was at each moment --- and not from pixels directly. That is
   deliberate: issue #373 asks that recognition follow human activity rather than camera
   motion or scene change, and an envelope computed from pose landmarks carries only the
   body. Pass a pixel-derived envelope and the module will work, and a pan of the camera
   will read as an action.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import musicalgestures


@dataclass
class Action:
    """One segment of motion, with somewhere to record what it was.

    Attributes:
        start (float): Start time in seconds.
        end (float): End time in seconds.
        source (str): What produced this span, so that spans from different segmenters
            can be told apart when they are pooled.
        labels (dict): Names given to this action by recognisers, keyed by recogniser.
            Empty is the normal state: most actions are never named, and an action with no
            label is still an action. This is where a gesture would be recorded, if anything
            could establish one.
        features (dict): Numbers describing the span, from :func:`action_type` and anything
            else that measures without naming.
    """

    start: float
    end: float
    source: str = "unknown"
    labels: dict = field(default_factory=dict)
    features: dict = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Length of the action in seconds."""
        return self.end - self.start

    def overlaps(self, other: "Action") -> bool:
        """Whether this action shares any time with `other`."""
        return self.start < other.end and other.start < self.end

    def __repr__(self) -> str:
        named = f" {self.labels}" if self.labels else ""
        return f"<Action {self.start:.2f}-{self.end:.2f}s ({self.source}){named}>"


def _as_envelope(x) -> np.ndarray:
    e = np.asarray(x, float).ravel()
    if not np.isfinite(e).all():
        e = np.interp(np.arange(len(e)),
                      np.flatnonzero(np.isfinite(e)),
                      e[np.isfinite(e)]) if np.isfinite(e).any() else np.zeros_like(e)
    return e


def segment_actions(envelope, fs: float, threshold: float = 0.15,
                    min_duration: float = 0.1, min_gap: float = 0.1,
                    source: str = "envelope") -> list[Action]:
    """Cut a motion envelope into actions, where movement rises above rest.

    An action begins where the envelope crosses `threshold` and ends where it falls back.
    Short gaps are closed before short spans are dropped, in that order, because a single
    action that dips momentarily below the threshold would otherwise be discarded as two
    fragments rather than kept as one.

    The threshold is a fraction of the envelope's range, not an absolute value, so the same
    setting transfers between recordings of different scale. Movement never rising above it
    yields no actions, which is the correct answer for a still recording rather than an
    error.

    Args:
        envelope: Motion per frame, one dimension. Non-finite values are interpolated.
        fs (float): Sampling rate of the envelope, in frames per second.
        threshold (float): Level counting as movement, as a fraction of the envelope's
            range. Defaults to 0.15.
        min_duration (float): Spans shorter than this, in seconds, are discarded as noise.
            Defaults to 0.1.
        min_gap (float): Gaps shorter than this, in seconds, are closed. Defaults to 0.1.
        source (str): Recorded on each Action, to identify what produced it.

    Returns:
        list: The actions found, in time order.
    """
    e = _as_envelope(envelope)
    if len(e) < 2 or fs <= 0:
        return []

    lo, hi = float(np.min(e)), float(np.max(e))
    if hi <= lo:
        return []
    level = lo + threshold * (hi - lo)

    active = e > level
    if not active.any():
        return []

    # run starts and ends, as sample indices
    edges = np.diff(active.astype(np.int8))
    starts = list(np.flatnonzero(edges == 1) + 1)
    ends = list(np.flatnonzero(edges == -1) + 1)
    if active[0]:
        starts.insert(0, 0)
    if active[-1]:
        ends.append(len(e))

    spans = [[s / fs, t / fs] for s, t in zip(starts, ends)]

    # close short gaps first: a dip below the level in the middle of one action is not
    # a boundary, and dropping short spans before merging would delete its halves
    merged: list[list[float]] = []
    for span in spans:
        if merged and span[0] - merged[-1][1] < min_gap:
            merged[-1][1] = span[1]
        else:
            merged.append(span)

    return [Action(start=s, end=t, source=source)
            for s, t in merged if t - s >= min_duration]


def action_type(envelope, fs: float, iterative_min_peaks: int = 3,
                impulsive_centroid: float = 0.42) -> dict:
    """Describe how movement is distributed inside one action.

    Three shapes, following the typology of *Sound Actions*:

    - **impulsive** --- energy arrives at once and decays. A hit, a tap, a clap.
    - **sustained** --- energy is held across the span. A bowed note, a slow reach.
    - **iterative** --- energy repeats within the span. A tremolo, a shake, a scrub.

    Decided on two measures rather than a classifier, so the call can be read and argued
    with. `peaks` counts internal maxima above half the span's peak: several of them mean
    the movement repeated. `centroid` is where the span's energy sits, 0 at its start and 1
    at its end: an impulse is front-loaded, a held movement is centred.

    Iterative is tested first, because a repeated movement is also a centred one, and the
    repetition is the more specific description.

    The discriminator is the centroid rather than time spent above half height, and that is
    a correction rather than a preference. Segmentation cuts an action at a threshold, so a
    decaying impulse arrives here already truncated to its loud third, which raises the
    fraction of it spent above half height until it is indistinguishable from a held
    movement. Measured on the canonical shapes after segmentation: time-above-half reads
    0.385 for a decay against 0.510 for a tremolo and 1.000 for a plateau, while the
    centroid reads 0.332, 0.481 and 0.500. Only the second separates the impulse.

    Args:
        envelope: The motion envelope of ONE action, not of the whole recording.
        fs (float): Sampling rate of the envelope, in frames per second.
        iterative_min_peaks (int): Internal peaks needed to call a span iterative.
            Defaults to 3.
        impulsive_centroid (float): Energy centroid below which a span is called impulsive.
            Defaults to 0.42, midway between a decay and a plateau as measured above.

    Returns:
        dict: ``type`` as one of ``'impulsive'``, ``'sustained'``, ``'iterative'``, with the
            ``peaks``, ``centroid`` and ``sustain`` behind it, so a disputed call can be
            checked rather than merely disagreed with.
    """
    e = _as_envelope(envelope)
    out = {"type": "impulsive", "peaks": 0, "centroid": 0.0, "sustain": 0.0}
    if len(e) < 3 or fs <= 0:
        return out

    # Half of the peak, not half of the span's own range. A motion envelope has a
    # meaningful zero --- no movement --- so "held" means "stayed near its peak", and
    # measuring from the span minimum makes a perfectly steady action read as impulsive,
    # because its minimum and its peak are the same number.
    hi = float(np.max(e))
    if hi <= 0:
        return out
    half = 0.5 * hi

    total = float(np.sum(e))
    t = np.arange(len(e)) / (len(e) - 1)
    centroid = float(np.sum(t * e) / total) if total > 0 else 0.0
    rising = (e[1:-1] > e[:-2]) & (e[1:-1] >= e[2:]) & (e[1:-1] > half)

    peaks = int(np.count_nonzero(rising))
    if peaks >= iterative_min_peaks:
        shape = "iterative"
    elif centroid >= impulsive_centroid:
        shape = "sustained"
    else:
        shape = "impulsive"

    out["type"] = shape
    out["peaks"] = peaks
    out["centroid"] = centroid
    out["sustain"] = float(np.mean(e > half))
    return out


def describe_actions(actions: list[Action], envelope, fs: float) -> list[Action]:
    """Attach :func:`action_type` to each action, in place, and return them.

    Measuring is kept apart from naming on purpose: this fills `features`, never `labels`.
    A shape is something the signal shows; a name is something a recogniser claims.

    Args:
        actions (list): Actions to describe, as returned by :func:`segment_actions`.
        envelope: The motion envelope the actions were cut from.
        fs (float): Sampling rate of the envelope.

    Returns:
        list: The same actions, with `features` filled in.
    """
    e = _as_envelope(envelope)
    for a in actions:
        i, j = int(round(a.start * fs)), int(round(a.end * fs))
        a.features.update(action_type(e[i:j], fs))
    return actions


def mg_actions(self: "musicalgestures.MgVideo", envelope=None, fs: float | None = None,
               threshold: float = 0.15, min_duration: float = 0.1,
               min_gap: float = 0.1) -> list[Action]:
    """Segment this video into actions and describe the shape of each.

    With no envelope given, one is built from the body rather than from the picture: pose
    landmarks are extracted if they are not cached, and their quantity of motion becomes
    the envelope. That is what makes the result follow the person and not the camera --- a
    pan moves every pixel and moves no landmark relative to the others.

    Args:
        envelope: A motion envelope to segment. Defaults to None, meaning build one from
            pose. Pass your own to segment something else, and note that a pixel-derived
            envelope will read camera movement as action.
        fs (float, optional): Sampling rate of `envelope`. Defaults to the video's frame
            rate, which is right for any envelope with one value per frame.
        threshold (float): Level counting as movement, as a fraction of the envelope's
            range. Defaults to 0.15.
        min_duration (float): Shortest span kept, in seconds. Defaults to 0.1.
        min_gap (float): Longest gap closed, in seconds. Defaults to 0.1.

    Returns:
        list: The actions found, each carrying its shape in `features`. Also stored on the
            video as `actions`.
    """
    rate = float(fs) if fs is not None else float(self.fps)
    if envelope is None:
        from musicalgestures._qom import pose_qom

        cache = getattr(self, "_pose_keypoints", None)
        if not cache:
            self.pose()
            cache = getattr(self, "_pose_keypoints", None)
        if not cache:
            raise RuntimeError(
                "no pose landmarks are available, so there is no body to follow. Run "
                "pose() first, or pass an envelope of your own.")
        envelope, rate = pose_qom(cache["data"] if isinstance(cache, dict) else cache, rate)

    actions = segment_actions(envelope, rate, threshold=threshold,
                              min_duration=min_duration, min_gap=min_gap,
                              source="pose-qom" if fs is None else "envelope")
    describe_actions(actions, envelope, rate)
    self.actions = actions
    return actions

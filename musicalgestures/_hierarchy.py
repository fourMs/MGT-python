"""Levels of segmentation over one recording, related by containment.

Three levels, coarse to fine: `part` is talking versus improvising, `phrase` is a run
of related activity, `action` is an individual segment of motion. Each is a list of `Action`,
which already carries `features` for what was measured and `labels` for what is
claimed, and the distinction between those two is the one thing here worth protecting.

**Containment is computed on demand rather than stored as a tree.** A level is a
hypothesis, and every one of them will be recomputed --- a stored tree would make
re-cutting the action level invalidate the phrase level that has nothing to do with
it. Asking which phrase contains an action is cheap; keeping a tree correct is not.

**Nothing here claims the levels are right.** They are a draft for a person to
correct, which is why `_annotate` exists.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from typing import cast

import numpy as np

from musicalgestures._actions import Action

__all__ = ["Hierarchy", "part_level"]


@dataclass
class Hierarchy:
    """Named levels of `Action`, and the containment between them.

    Attributes:
        levels (dict): Level name to the list of Actions at that level, in time order.
    """

    levels: dict = field(default_factory=dict)

    def children(self, action: Action, level: str) -> list[Action]:
        """The Actions at `level` whose midpoint falls inside `action`.

        **Midpoint, not overlap.** A span that merely overlaps two parents would be
        returned by both, and twelve actions under three phrases would count as
        fourteen. The midpoint puts every child under exactly one parent.
        """
        out = []
        for c in self.levels.get(level, []):
            mid = 0.5 * (c.start + c.end)
            if action.start <= mid < action.end:
                out.append(c)
        return out

    def parent(self, action: Action, level: str) -> Action | None:
        """The Action at `level` containing `action`'s midpoint, or None."""
        mid = 0.5 * (action.start + action.end)
        for p in self.levels.get(level, []):
            if p.start <= mid < p.end:
                return cast(Action, p)
        return None

    def to_dict(self) -> dict:
        """A plain structure for JSON, one entry per level."""
        return {name: [{"start": a.start, "end": a.end, "source": a.source,
                        "labels": a.labels, "features": a.features}
                       for a in spans]
                for name, spans in self.levels.items()}


def _speech_track(speech, n: int, fs: float) -> np.ndarray:
    """A boolean per frame: is anyone speaking."""
    track = np.zeros(n, dtype=bool)
    for s in speech or []:
        track[max(0, int(s.start * fs)): min(n, int(s.end * fs))] = True
    return track


def part_level(qom, fs: float, speech, quiet_percentile: float = 25.0,
               min_part_s: float = 60.0, tolerance_s: float = 5.0,
               smooth_s: float = 10.0) -> list[Action]:
    """Cut a session into improvisations and the talking between them.

    **Not from motion alone.** ARJ's observation about this corpus is that the dancers
    talk between improvisations and hardly at all while dancing, so a
    between-improvisation section is where speech is present AND motion is low, and an
    improvisation is the converse. Two weak signals that agree beat one strong one,
    and this keys on what the session does rather than on how an envelope happens to
    bend.

    It also makes the segmentation falsifiable. Every part records in `features` which
    signals supported its start:

    - ``"both"``        --- the motion floor and the detector marked the same transition;
    - ``"motion_only"`` --- motion dropped where nobody spoke;
    - ``"vad_only"``    --- somebody spoke where motion did not drop.

    Only ``"both"`` is an assertion. The other two are guesses and the renderer draws
    them differently, so a reader sees which boundaries to distrust without reading a
    log.

    Args:
        qom: Quantity of motion per frame.
        fs (float): Frames per second of `qom`.
        speech: Speech spans, as returned by `_voice.speech_segments`. May be empty.
        quiet_percentile (float): Motion below this percentile of the session counts
            as low. A percentile rather than a fraction of the range, because a
            session's outlier spikes make the range meaningless.
        min_part_s (float): Parts shorter than this are absorbed into their neighbour.
        tolerance_s (float): How close two transitions must be to count as agreeing.
        smooth_s (float): Window for smoothing the envelope before thresholding.

    Returns:
        list: Parts in time order, each labelled ``"improvisation"`` or ``"talk"``.
    """
    e = np.asarray(qom, float).ravel()
    n = len(e)
    if n == 0 or fs <= 0:
        return []

    #: Smooth before thresholding: the part level is about minutes, and an unsmoothed
    #: envelope crosses any level hundreds of times a minute.
    w = max(1, int(smooth_s * fs))
    kernel = np.ones(w) / w
    smooth = np.convolve(e, kernel, mode="same")

    quiet_level = float(np.percentile(smooth, quiet_percentile))
    moving = smooth > quiet_level
    speaking = _speech_track(speech, n, fs)

    #: Improvising where motion is up and nobody is talking. Speech refines the motion
    #: judgement rather than replacing it, because the dancers are sometimes quiet
    #: between improvisations too.
    improv = moving & ~speaking

    #: Runs of the same state. The comparison against improv[0] makes the first run
    #: start at 0 rather than at the first change.
    changes = np.flatnonzero(np.diff(improv.astype(np.int8))) + 1
    bounds = [0, *changes.tolist(), n]
    spans = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)
             if bounds[i + 1] > bounds[i]]

    #: Absorb runs too short to be a part of a session. A fragment at the very start
    #: has no predecessor to be absorbed into, so it is folded forwards afterwards.
    merged: list[tuple[int, int]] = []
    for a, b in spans:
        if merged and (b - a) < min_part_s * fs:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    if len(merged) > 1 and (merged[0][1] - merged[0][0]) < min_part_s * fs:
        merged[1] = (merged[0][0], merged[1][1])
        merged.pop(0)

    tol = int(tolerance_s * fs)
    motion_edges = set((np.flatnonzero(np.diff(moving.astype(np.int8))) + 1).tolist())
    speech_edges = set((np.flatnonzero(np.diff(speaking.astype(np.int8))) + 1).tolist())

    parts = []
    for a, b in merged:
        near_motion = any(abs(a - m) <= tol for m in motion_edges)
        near_speech = any(abs(a - s) <= tol for s in speech_edges)
        if a == 0:
            agreement = "both"          # the recording's own start, not a guess
        elif near_motion and near_speech:
            agreement = "both"
        elif near_motion:
            agreement = "motion_only"
        else:
            agreement = "vad_only"

        frac_moving = float(moving[a:b].mean()) if b > a else 0.0
        frac_speech = float(speaking[a:b].mean()) if b > a else 0.0
        parts.append(Action(
            start=a / fs, end=b / fs, source="part",
            labels={"part": "improvisation"
                    if frac_moving > 0.5 and frac_speech < 0.5 else "talk"},
            features={"agreement": agreement,
                      "fraction_moving": round(frac_moving, 3),
                      "fraction_speech": round(frac_speech, 3),
                      "quiet_level": quiet_level}))
    return parts

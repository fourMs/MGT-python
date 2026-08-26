"""Choosing which segments a person will look at, and doing it defensibly.

**Stratified and seeded, not ranked.** Ranking segments by how clean they look gives
easier material to annotate and a sample whose distribution is a property of the
ranking rather than of the dancing. Any claim the analysis later makes about the
corpus is a claim about this sample, so the sample is spread across the strata that
matter --- improvisations, sessions, conditions --- and the seed is recorded on every
chosen span so it can be drawn again.

**Salience is measured on everything and used for nothing.** It is stored so a curated
subset can be pulled later, deliberately and visibly, without re-running the pipeline
and without having quietly shaped the annotation corpus first.
"""
from __future__ import annotations

import numpy as np

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy

__all__ = ["salience", "stratified_sample"]


def salience(action: Action, qom, fs: float) -> dict:
    """Three measures of how easy a span is to read. Recorded, never selected on.

    Args:
        action: The span to measure.
        qom: Quantity of motion per frame for the whole recording.
        fs (float): Frames per second of `qom`.

    Returns:
        dict: `onset_clarity` (how sharply motion rises at the start, as a fraction of
        the span's peak), `motion_range` (peak minus floor inside the span) and
        `boundary_separation` (how far the span's edges sit below its own peak).
    """
    e = np.asarray(qom, float).ravel()
    i0, i1 = int(action.start * fs), int(action.end * fs)
    i0, i1 = max(0, i0), min(len(e), i1)
    if i1 - i0 < 2:
        return {"onset_clarity": 0.0, "motion_range": 0.0,
                "boundary_separation": 0.0}

    inside = e[i0:i1]
    peak = float(inside.max())
    floor = float(np.percentile(inside, 10))

    lead = e[max(0, i0 - int(fs)): i0]
    lead_level = float(np.percentile(lead, 90)) if lead.size else floor
    onset = (peak - lead_level) / peak if peak > 0 else 0.0

    edge = float(max(inside[0], inside[-1]))
    separation = (peak - edge) / peak if peak > 0 else 0.0

    return {"onset_clarity": round(float(onset), 4),
            "motion_range": round(peak - floor, 4),
            "boundary_separation": round(float(separation), 4)}


def stratified_sample(hierarchy: Hierarchy, level: str = "phrase", n: int = 20,
                      strata: str = "part", seed: int = 0) -> list[Action]:
    """Draw `n` spans from `level`, spread evenly over the strata above them.

    Every stratum is represented before any stratum is sampled twice, so a short
    improvisation cannot be missed entirely by an unlucky draw, and a stratum with ten
    times as many phrases cannot crowd out a small one.

    Args:
        hierarchy: The levels to sample from.
        level (str): Which level the excerpts come from. Defaults to "phrase",
            because the action level runs to roughly 2,500 spans per session and is
            far too fine to choose from.
        n (int): How many spans are wanted. Asking for more than exist returns them
            all, once each.
        strata (str): The coarser level to spread across. Defaults to "part".
        seed (int): Recorded on every chosen span, so the sample can be drawn again.

    Returns:
        list: The chosen spans, in time order, each carrying `sample_seed` and
        `sample_stratum` in `features`.
    """
    rng = np.random.default_rng(seed)
    spans = list(hierarchy.levels.get(level, []))
    if not spans:
        return []

    buckets: dict = {}
    for s in spans:
        parent = hierarchy.parent(s, strata)
        buckets.setdefault(parent.start if parent else None, []).append(s)

    #: Shuffle inside each bucket once, then deal round-robin. Dealing rather than
    #: allocating a quota per bucket is what makes every stratum appear before any
    #: stratum repeats, whatever the bucket sizes are --- an improvisation with three
    #: phrases is represented alongside one with thirty.
    for key in buckets:
        order = rng.permutation(len(buckets[key]))
        buckets[key] = [buckets[key][i] for i in order]

    chosen: list[Action] = []
    keys = sorted(buckets, key=lambda k: (k is None, k))
    while len(chosen) < n and any(buckets[k] for k in keys):
        for k in keys:
            if buckets[k] and len(chosen) < n:
                s = buckets[k].pop()
                s.features["sample_seed"] = seed
                s.features["sample_stratum"] = k
                chosen.append(s)
    return sorted(chosen, key=lambda a: a.start)

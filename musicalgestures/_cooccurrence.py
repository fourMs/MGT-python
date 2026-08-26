"""Which annotation layers coincide, and by how much.

A timeline showing motion on one line and speech on another lets a reader *see* that the
two coincide. It does not let them count it, filter by it, or ask for every gesture made
in silence --- and combinations are what a qualitative annotator works in. This turns
coincidence from something visible into something addressable: a label on each span, and
a table of how the recording divides.

**Not restricted to speech and motion.** Any two layers: laughter against gesture, gesture
against a rehearsal segmentation, one annotator's tier against another's. The names are
arguments, not assumptions.

**Overlapping reference spans are merged before anything is counted.** Two detections that
touch describe one region. Counting them separately would credit a gesture with twice the
accompaniment it had, and detectors emit touching spans routinely --- so the union is taken
first, every time, rather than trusting the caller to have tidied up.
"""
from __future__ import annotations

from dataclasses import replace

from musicalgestures._actions import Action

__all__ = ["overlap_seconds", "label_by_overlap", "cooccurrence_table", "merge_spans"]


def merge_spans(spans) -> list[tuple[float, float]]:
    """The union of a set of spans, as disjoint (start, end) pairs in time order."""
    pairs = sorted((float(s.start), float(s.end)) for s in spans)
    out: list[list[float]] = []
    for start, end in pairs:
        if end <= start:
            continue
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [(a, b) for a, b in out]


def overlap_seconds(span, others) -> float:
    """How many seconds of `span` are covered by any of `others`.

    Args:
        span: The Action being asked about.
        others: The reference layer. Order and overlap do not matter; the union is taken.

    Returns:
        float: Seconds of overlap, never more than `span`'s own duration.
    """
    total = 0.0
    for start, end in merge_spans(others):
        lo, hi = max(float(span.start), start), min(float(span.end), end)
        if hi > lo:
            total += hi - lo
    return total


def label_by_overlap(spans, others, name: str, threshold: float = 0.5,
                     present: str = "with", absent: str = "without") -> list[Action]:
    """Label each span by whether it coincides with a reference layer.

    Returns new Actions rather than modifying the ones passed in: the same gestures get
    labelled against several layers in turn --- speech, then laughter, then someone else's
    segmentation --- and a function that mutated its input would make the second call
    depend on the first.

    Args:
        spans: The Actions to label.
        others: The reference layer to compare against.
        name (str): What the reference layer is called. Becomes the label key, and
            `f"{name}_overlap"` in features.
        threshold (float): Fraction of a span that must be covered for `present`.
            Defaults to 0.5. Use 0.0 for "touches at all".
        present (str): Label for spans at or above the threshold. Defaults to ``"with"``.
        absent (str): Label for spans below it. Defaults to ``"without"``.

    Returns:
        list: New Actions carrying the label and the exact overlap fraction. The fraction
        is kept because a threshold is a decision and the number underneath it should stay
        visible.
    """
    ref = merge_spans(others)
    out = []
    for s in spans:
        dur = float(s.end) - float(s.start)
        secs = 0.0
        for start, end in ref:
            lo, hi = max(float(s.start), start), min(float(s.end), end)
            if hi > lo:
                secs += hi - lo
        frac = (secs / dur) if dur > 0 else 0.0
        #: A threshold of 0.0 must mean "touches at all", not "always true".
        hit = frac > 0 if threshold <= 0 else frac >= threshold
        out.append(replace(s,
                           labels={**s.labels, name: present if hit else absent},
                           features={**s.features, f"{name}_overlap": round(frac, 4),
                                     f"{name}_overlap_s": round(secs, 3)}))
    return out


def cooccurrence_table(a_spans, b_spans, duration_s: float) -> dict:
    """How a recording divides between two annotation layers, in seconds.

    Four cells, and every instant of the recording is in exactly one of them, so they sum
    to `duration_s`. That invariant is the point: a table whose cells do not add up is
    reporting an overlap that was counted twice or a gap that was lost.

    Args:
        a_spans: The first layer, for example gestures.
        b_spans: The second layer, for example speech.
        duration_s (float): Length of the recording.

    Returns:
        dict: Seconds in ``both``, ``a_only``, ``b_only`` and ``neither``, plus the same
        as percentages of `duration_s` under ``*_pct``.
    """
    A, B = merge_spans(a_spans), merge_spans(b_spans)

    def covered(u):
        return sum(min(e, duration_s) - s for s, e in u if min(e, duration_s) > s)

    both = 0.0
    for s1, e1 in A:
        for s2, e2 in B:
            lo, hi = max(s1, s2), min(e1, e2, duration_s)
            if hi > lo:
                both += hi - lo
    a_tot, b_tot = covered(A), covered(B)
    out = {"both": both, "a_only": a_tot - both, "b_only": b_tot - both,
           "neither": duration_s - a_tot - b_tot + both, "duration_s": duration_s}
    for k in ("both", "a_only", "b_only", "neither"):
        out[f"{k}_pct"] = round(100 * out[k] / duration_s, 2) if duration_s > 0 else 0.0
    return out

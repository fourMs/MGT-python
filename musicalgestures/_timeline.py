"""The composite sheet: videogram, envelope, waveform and segmentation on one axis.

One renderer, three configurations. The overview, the improvisation sheet and the
action strip differ only in the span of time they cover and in which level's
boundaries they draw, so they are one function called three ways rather than three
functions that drift apart.

**Boundaries are drawn across every panel**, so a proposed cut is read against the
motion, the sound and the picture at once rather than against whichever signal
produced it.

**Video and audio decimate independently.** The design's rule is that audio stays on
its own clock and is never binned to the 20 ms video frame grid, because forcing both
onto one grid quantises away the very asymmetry this corpus was recorded to study.
That rule holds at render time too: each panel reduces its own samples to the
available pixel columns.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

__all__ = ["decimate_minmax", "render_timeline"]


def decimate_minmax(x, n_columns: int):
    """Reduce a signal to `n_columns`, keeping the extreme of each column.

    **Never a mean.** An overview exists to show where the brief events are, and a
    mean is precisely what removes them: a single frame of large movement in a
    four-second column is the thing a viewer zoomed out to find.

    The final partial column is kept rather than truncated away, so the end of a
    recording is drawn, and it is padded with the edge value rather than with zeros,
    which would draw a trough that is not in the recording.

    Args:
        x: The signal, one dimension.
        n_columns (int): How many output columns are wanted.

    Returns:
        tuple: (mins, maxs, factor), where `factor` is samples per column and is
        meant to be printed on the figure.
    """
    v = np.asarray(x, float).ravel()
    n = v.size
    if n == 0:
        return np.zeros(0), np.zeros(0), 1
    if n_columns >= n:
        return v.copy(), v.copy(), 1

    factor = int(np.ceil(n / n_columns))
    pad = (-n) % factor
    if pad:
        #: Pad with the edge value, not with zeros: zeros would invent a trough at
        #: the end of every recording whose length is not a multiple of the factor.
        v = np.concatenate([v, np.full(pad, v[-1])])
    block = v.reshape(-1, factor)
    return block.min(axis=1), block.max(axis=1), factor

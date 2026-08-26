"""Figures that know about annotations, which none of the toolbox's others do.

MGT already has a rich battery of ways to look at a long recording --- motiongrams,
videograms, self-similarity, tempograms, contact sheets, heatmaps, stroboscopes --- and
every one of them is about the signal. `Hierarchy` and the ELAN exporter live on the other
side of a gap that almost nothing crosses. For somebody annotating two and a half hours,
that crossing is the tool, and these are the four views that make it.

They correspond to what the three fields that use this material actually do:

- **`filmstrip`** --- keyframes laid along the time axis under the annotation tiers. Human
  movement science reduces the spatial dimension so time becomes visible; this reduces it
  the other way, keeping enough picture to answer "what is happening here" without scrubbing.
- **`concordance`** --- every instance of one category side by side. This is the linguist's
  concordance applied to video, and it is what makes 183 laughter proposals codable
  consistently rather than one at a time, hours apart.
- **`tier_map`** --- every tier as a density band over the whole session. The "where is
  there anything to look at" view, and the one that shows which tiers are still empty.
- **`structure_map`** --- a self-similarity matrix with the annotation boundaries drawn on
  it. Music and movement structure analysis uses SSMs to find repeated material; drawing
  someone's coding on top asks whether their boundaries and the repetition agree.

Split the way `_voice` is split. The parts with a right answer --- which frames to sample,
how a grid is shaped, how full a tier is, where a time falls in a matrix --- are the
functions below and are tested. Rendering is a thin layer over them.
"""
from __future__ import annotations

import numpy as np

__all__ = ["sample_times", "grid_shape", "tier_density", "time_to_index"]


def sample_times(start_s: float, end_s: float, n: int) -> list[float]:
    """`n` times spread across a span, kept strictly inside it.

    Inside, not on the edges: a frame at exactly the end of a clip may not exist, and one
    just inside always does. With `n = 1` the time is the middle, which is the frame a
    person would pick to represent a span.

    Args:
        start_s (float): Start of the span.
        end_s (float): End of the span. May equal `start_s`; a detector can emit a
            degenerate span and asking for frames from it should still work.
        n (int): How many times to return.

    Returns:
        list: The times, ascending. Empty when `n` is not positive.
    """
    if n <= 0:
        return []
    span = float(end_s) - float(start_s)
    if span <= 0:
        return [float(start_s)] * n
    #: Midpoints of n equal slices: evenly spaced, and never on either edge.
    return [float(start_s) + span * (i + 0.5) / n for i in range(n)]


def grid_shape(n_items: int, n_cols: int | None = None) -> tuple[int, int]:
    """Rows and columns for a grid of `n_items`.

    Without a column count, as square as it can be and never taller than wide: a
    concordance is read across, and a tall narrow grid puts the instances a reader is
    comparing far apart on the page.

    Args:
        n_items (int): How many cells are needed.
        n_cols (int): Columns to use, or None to choose.

    Returns:
        tuple: (rows, columns). The last row may be partial; nothing is dropped.
    """
    n = max(0, int(n_items))
    if n == 0:
        return (0, 0)
    if n_cols:
        cols = int(n_cols)
    else:
        cols = int(np.ceil(np.sqrt(n)))
    rows = int(np.ceil(n / cols))
    return (rows, cols)


def tier_density(spans, duration_s: float, n_bins: int) -> np.ndarray:
    """What fraction of each time bin a tier covers.

    Overlapping spans are merged first, so a bin cannot be more than full. Detectors emit
    touching and overlapping spans routinely, and a density above 1 is not a stronger
    signal, it is a broken one.

    An empty tier returns zeros rather than an empty array, because an empty tier still
    has to be drawn: seeing which tiers are not yet filled is half of what this view is for.

    Args:
        spans: Actions, in any order.
        duration_s (float): Length of the recording.
        n_bins (int): How many bins to divide it into.

    Returns:
        np.ndarray: One fraction in [0, 1] per bin.
    """
    n_bins = max(1, int(n_bins))
    out = np.zeros(n_bins)
    if duration_s <= 0:
        return out
    width = duration_s / n_bins

    pairs = sorted((float(s.start), float(s.end)) for s in spans or [])
    merged: list[list[float]] = []
    for a, b in pairs:
        if b <= a:
            continue
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])

    for a, b in merged:
        first = max(0, int(a / width))
        last = min(n_bins - 1, int(np.ceil(b / width)) - 1)
        for i in range(first, last + 1):
            lo, hi = i * width, (i + 1) * width
            out[i] += max(0.0, min(b, hi) - max(a, lo))
    #: No clamp here. After merging, the spans are disjoint and no bin can exceed its
    #: own width, so a clamp would be unreachable --- and worse, it would hide a broken
    #: merge by quietly returning 1.0 instead of the 1.6 that would expose it.
    return out / width


def time_to_index(t: float, duration_s: float, n: int) -> int:
    """Where a time falls in an `n`-element series over `duration_s`.

    **Clamped, never wrapped.** Annotations shifted from another recording's clock can land
    outside this one, and a wrapped index puts a boundary at the start of the session where
    it looks entirely plausible. Clamping puts it at the edge, where it looks wrong.

    Args:
        t (float): The time, in seconds.
        duration_s (float): Length the series covers.
        n (int): Number of elements.

    Returns:
        int: An index in [0, n-1].
    """
    if n <= 0:
        return 0
    if duration_s <= 0:
        return 0
    i = int(float(t) / float(duration_s) * n)
    return max(0, min(n - 1, i))


# ---------------------------------------------------------------------------
# The four figures. Thin over the functions above, which hold everything that
# has a right answer.
# ---------------------------------------------------------------------------

def _grab(video, times, height=180):
    """Frames at the given times, as RGB arrays. One ffmpeg call per frame.

    Accurate seek rather than a keyframe seek: a filmstrip whose pictures are up to two
    seconds from where the axis says they are is worse than no filmstrip, because nothing
    on the figure reveals it.
    """
    import subprocess
    import tempfile
    from pathlib import Path

    import matplotlib.image as mpimg

    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            f = str(Path(tmp) / f"{i:04d}.png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}",
                            "-i", str(video), "-frames:v", "1",
                            "-vf", f"scale=-2:{height}", f],
                           check=False)
            out.append(mpimg.imread(f) if Path(f).exists() else None)
    return out


def _sidecar(out, payload):
    import json
    from pathlib import Path
    Path(out).with_suffix(".json").write_text(json.dumps(payload, indent=1) + "\n")


def filmstrip(video, start_s: float, end_s: float, n: int = 12, hierarchy=None,
              levels=(), out=None, height: int = 180, title=None):
    """Keyframes along the time axis, with the annotation tiers beneath them.

    Answers "what is actually happening here" without scrubbing. The frames are sampled
    strictly inside the span and their exact times go in the sidecar, so a picture can
    always be traced back to a moment in the recording.

    Args:
        video: Path to the video.
        start_s (float), end_s (float): The span to cover.
        n (int): How many frames. Defaults to 12.
        hierarchy: A `Hierarchy` whose levels are drawn as bands beneath, or None.
        levels (tuple): Which levels to draw. Empty means all of them.
        out: Output path.
        height (int): Frame height in pixels. Defaults to 180.
        title: Figure title.

    Returns:
        Path: The image written.
    """
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    from pathlib import Path

    times = sample_times(start_s, end_s, n)
    frames = _grab(video, times, height)
    names = list(levels) if levels else (list(hierarchy.levels) if hierarchy else [])

    fig = plt.figure(figsize=(min(24, 1.6 * max(1, n)), 3.2 + 0.28 * len(names)))
    gs = fig.add_gridspec(2, 1, height_ratios=[3.0, max(0.5, 0.28 * len(names))],
                          hspace=0.08)
    top = fig.add_subplot(gs[0])
    #: The frames must sit exactly above the times they were taken at. Default axes
    #: margins would shift the strip a few per cent against the tier bands below, and a
    #: frame drawn above a span it does not belong to is a silent error --- nothing on the
    #: figure would reveal it.
    top.set_xlim(0.0, 1.0)
    top.set_ylim(0.0, 1.0)
    top.margins(0)
    top.axis("off")
    for i, (t, im) in enumerate(zip(times, frames)):
        ax = top.inset_axes([i / max(1, n), 0.0, 1 / max(1, n), 1.0])
        ax.axis("off")
        if im is not None:
            ax.imshow(im)
        ax.set_title(f"{t:.0f} s", fontsize=7, color="#444444", pad=2)

    bot = fig.add_subplot(gs[1])
    for row, name in enumerate(names):
        for a in hierarchy.levels.get(name, []):
            if a.end <= start_s or a.start >= end_s:
                continue
            bot.barh(row, min(a.end, end_s) - max(a.start, start_s),
                     left=max(a.start, start_s), height=0.7,
                     color="#d95f02", alpha=0.75, linewidth=0)
    bot.set_yticks(range(len(names)))
    bot.set_yticklabels(names, fontsize=8)
    bot.set_xlim(start_s, end_s)
    bot.margins(x=0)
    bot.set_xlabel("time (s), session clock")
    bot.grid(axis="x", alpha=0.15)
    fig.suptitle(title or f"{Path(video).name}  {start_s:.0f}-{end_s:.0f} s", fontsize=10)

    out = Path(out) if out else Path(f"filmstrip_{int(start_s):06d}.png")
    fig.savefig(out, bbox_inches="tight", dpi=130)
    plt.close(fig)
    _sidecar(out, {"image": out.name, "start_s": start_s, "end_s": end_s,
                   "frame_times_s": [round(t, 3) for t in times],
                   "levels": names,
                   "note": "frames are sampled strictly inside the span, at the times listed"})
    return out


def concordance(video, spans, out, n_cols=None, label_key=None, height: int = 150,
                title=None, max_items: int = 60):
    """Every instance of one category, side by side.

    The linguist's concordance applied to video. Coding 183 laughter proposals one at a
    time, hours apart, is how a category drifts; seeing them together is how it does not.

    Args:
        video: Path to the video.
        spans: The Actions to show, in any order; they are sorted by time.
        out: Output path.
        n_cols (int): Columns, or None to choose a near-square layout.
        label_key (str): Which label to print under each frame, or None for the time.
        height (int): Frame height in pixels.
        title: Figure title.
        max_items (int): Cap, so a category with thousands of instances does not silently
            produce an unreadable figure. **What was dropped is stated on the figure and
            in the sidecar**, never silently.

    Returns:
        Path: The image written.
    """
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    from pathlib import Path

    items = sorted(spans, key=lambda a: a.start)
    shown, dropped = items[:max_items], max(0, len(items) - max_items)
    rows, cols = grid_shape(len(shown), n_cols)
    if rows == 0:
        rows, cols = 1, 1

    times = [sample_times(a.start, a.end, 1)[0] for a in shown]
    frames = _grab(video, times, height)

    fig, axes = plt.subplots(rows, cols, figsize=(1.9 * cols, 1.7 * rows))
    axes = np.atleast_1d(axes).ravel()
    for ax in axes:
        ax.axis("off")
    for ax, a, t, im in zip(axes, shown, times, frames):
        if im is not None:
            ax.imshow(im)
        lab = a.labels.get(label_key, "") if label_key else ""
        ax.set_title(f"{t:.0f} s" + (f"  {lab}" if lab else ""), fontsize=7, pad=2)

    note = f"{len(shown)} of {len(items)} instances"
    if dropped:
        note += f"; {dropped} not shown (max_items={max_items})"
    fig.suptitle(title or note, fontsize=10)
    fig.text(0.995, 0.005, note, ha="right", va="bottom", fontsize=7, color="#555555")
    out = Path(out)
    fig.savefig(out, bbox_inches="tight", dpi=130)
    plt.close(fig)
    _sidecar(out, {"image": out.name, "n_total": len(items), "n_shown": len(shown),
                   "n_dropped": dropped, "max_items": max_items,
                   "times_s": [round(t, 3) for t in times]})
    return out


def tier_map(hierarchy, duration_s: float, out, n_bins: int = 600, title=None):
    """Every tier as a density band over the whole recording.

    The "where is there anything to look at" view, and the one that shows which tiers are
    still empty --- an empty tier is drawn as an empty band rather than omitted, because
    noticing what has not been annotated is half of what this is for.

    Args:
        hierarchy: The levels to draw.
        duration_s (float): Length of the recording.
        out: Output path.
        n_bins (int): Horizontal resolution. Defaults to 600.
        title: Figure title.

    Returns:
        Path: The image written.
    """
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    from pathlib import Path

    names = list(hierarchy.levels)
    dens = {n: tier_density(hierarchy.levels[n], duration_s, n_bins) for n in names}

    fig, ax = plt.subplots(figsize=(14, 0.42 * max(1, len(names)) + 1.4))
    for row, name in enumerate(names):
        ax.imshow(dens[name][None, :], aspect="auto", cmap="magma", vmin=0, vmax=1,
                  extent=(0, duration_s, row - 0.42, row + 0.42))
    ax.set_ylim(len(names) - 0.5, -0.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([f"{n}  ({len(hierarchy.levels[n])})" for n in names], fontsize=8)
    ax.set_xlim(0, duration_s)
    ax.set_xlabel("time (s), session clock")
    ax.grid(axis="x", alpha=0.15)
    fig.suptitle(title or "annotation density by tier", fontsize=10)
    fig.text(0.995, 0.005, f"1 column = {duration_s / n_bins:.1f} s; "
                           f"brightness is the fraction of the column covered",
             ha="right", va="bottom", fontsize=7, color="#555555")
    out = Path(out)
    fig.savefig(out, bbox_inches="tight", dpi=130)
    plt.close(fig)
    _sidecar(out, {"image": out.name, "duration_s": duration_s, "n_bins": n_bins,
                   "tiers": {n: len(hierarchy.levels[n]) for n in names},
                   "seconds_per_column": duration_s / n_bins})
    return out


def structure_map(analysis_dir, duration_s: float, out, hierarchy=None, levels=(),
                  max_columns: int = 700, which: str = "videogram_v", title=None):
    """A self-similarity matrix with somebody's annotation boundaries drawn on it.

    Music and movement structure analysis uses self-similarity to find repeated material.
    Drawing a coding on top asks the question that matters for this corpus, where the
    rehearsal categories are *searching for material*, *repeating from the top* and
    *cleaning the material*: do the boundaries somebody marked and the repetition the
    signal shows agree?

    Args:
        analysis_dir: Directory holding the cached pyramid.
        duration_s (float): Length of the recording.
        out: Output path.
        hierarchy: A `Hierarchy` whose boundaries are drawn, or None.
        levels (tuple): Which levels to draw. Empty means all.
        max_columns (int): Resolution of the matrix. Defaults to 700.
        which (str): Which pyramid to read. Defaults to ``"videogram_v"``.
        title: Figure title.

    Returns:
        Path: The image written.
    """
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    from pathlib import Path

    from musicalgestures._tracks import read_columns

    cols, _ = read_columns(analysis_dir, 0.0, duration_s, max_columns=max_columns,
                           which=which)
    X = np.asarray(cols, dtype=float)
    if X.ndim == 1:
        X = X[None, :]
    if X.shape[0] < X.shape[1]:
        X = X.T                                  # rows are time
    #: Cosine similarity on unit-normalised rows. A zero row would divide by zero and is
    #: a real state --- a still moment --- so it is given a norm of one and comes out
    #: dissimilar to everything, which is the honest answer for "nothing happened here".
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    S = (X / norms) @ (X / norms).T

    n = S.shape[0]
    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    ax.imshow(S, cmap="magma", origin="lower", extent=(0, duration_s, 0, duration_s))
    names = list(levels) if levels else (list(hierarchy.levels) if hierarchy else [])
    for name in names:
        for a in hierarchy.levels.get(name, []):
            for t in (a.start, a.end):
                if 0 <= t <= duration_s:
                    ax.axvline(t, color="#66ccff", linewidth=0.6, alpha=0.7)
                    ax.axhline(t, color="#66ccff", linewidth=0.6, alpha=0.7)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("time (s)")
    fig.suptitle(title or f"self-similarity, {which}", fontsize=10)
    fig.text(0.995, 0.005, f"{n} columns, {duration_s / max(1, n):.1f} s each; "
                           f"boundaries drawn from {', '.join(names) or 'nothing'}",
             ha="right", va="bottom", fontsize=7, color="#555555")
    out = Path(out)
    fig.savefig(out, bbox_inches="tight", dpi=130)
    plt.close(fig)
    _sidecar(out, {"image": out.name, "duration_s": duration_s, "n_columns": n,
                   "seconds_per_column": duration_s / max(1, n), "which": which,
                   "levels": names})
    return out


__all__ += ["filmstrip", "concordance", "tier_map", "structure_map"]

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


#: Solid asserts, dashed guesses. The part level records which of its boundaries both
#: the motion floor and the speech detector supported; drawing them the same way would
#: throw that away at exactly the point a reader would use it.
_BOUNDARY_STYLE = {"both": "solid", "motion_only": "dashed",
                   "vad_only": "dashed", None: "dotted"}


def render_timeline(analysis_dir, start_s: float = 0.0, end_s=None,
                    panels=("videogram_v", "qom", "waveform", "speech"),
                    levels=("part",), hierarchy=None, speech=None, audio=None,
                    out=None, dpi: int = 150, title=None):
    """One sheet: videogram, motion, sound and segmentation on a shared time axis.

    The same function makes all three tiers. An overview passes the whole file and
    `levels=("part",)`; an improvisation sheet passes one part's span and
    `levels=("phrase",)`; an action strip passes one phrase and `levels=("action",)`.

    A sidecar `.json` is written beside the image recording the decimation factor, the
    time range and every boundary drawn, so a figure can always be traced back to the
    numbers behind it.

    Args:
        analysis_dir: Directory holding `tracks.json` and the memmaps.
        start_s (float): Where the sheet begins, in seconds.
        end_s: Where it ends. None means the end of the recording.
        panels (tuple): Which panels to stack, top to bottom. A `waveform` panel is
            skipped when no `audio` is given rather than drawn empty.
        levels (tuple): Which hierarchy levels to draw boundaries for.
        hierarchy: A `Hierarchy`, or None to draw no boundaries.
        speech: Speech spans for the `speech` panel, or None.
        audio: Path to a WAV for the `waveform` panel, or None to skip it.
        out: Output path. Defaults to a name built from the time range.
        dpi (int): Figure resolution. Defaults to 150.
        title: Figure title. Defaults to the directory name and time range.

    Returns:
        Path: The image written.
    """
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    d = Path(analysis_dir)
    meta = json.loads((d / "tracks.json").read_text())
    fps = float(meta["fps"])
    n_frames = int(meta["frames"])
    end_s = float(meta["duration_s"]) if end_s is None else float(end_s)
    start_s = max(0.0, float(start_s))

    #: The number of columns the sheet can actually show. Everything decimates to
    #: this, and nothing is drawn at a resolution the page cannot carry.
    fig_w_in = 16.0
    n_columns = int(fig_w_in * dpi)

    drawn = [p for p in panels if p != "waveform" or audio is not None]
    fig, axes = plt.subplots(len(drawn), 1, figsize=(fig_w_in, 2.0 * len(drawn)),
                             sharex=True, dpi=dpi,
                             gridspec_kw={"hspace": 0.12})
    if len(drawn) == 1:
        axes = [axes]

    factor = 1
    i0 = int(start_s * fps)
    i1 = max(min(int(end_s * fps), n_frames), i0 + 1)

    for ax, panel in zip(axes, drawn):
        if panel in ("videogram_v", "videogram_h"):
            from musicalgestures._tracks import read_columns
            cols, spc = read_columns(d, start_s, end_s, max_columns=n_columns,
                                     which=panel)
            if cols.size:
                ax.imshow(cols.T, aspect="auto", origin="lower", cmap="magma",
                          extent=(start_s, end_s, 0, cols.shape[1]))
                factor = max(factor, int(round(spc * fps)))
            ax.set_ylabel(panel.replace("videogram_", "videogram "))
            ax.set_yticks([])

        elif panel == "qom":
            q = np.memmap(d / meta["qom"], dtype=np.float32, mode="r",
                          shape=(n_frames,))[i0:i1]
            mins, maxs, f = decimate_minmax(np.asarray(q, dtype=float), n_columns)
            factor = max(factor, f)
            t = np.linspace(start_s, end_s, len(maxs))
            #: Fill between the extremes rather than plotting a line through a mean:
            #: the band IS the information at this magnification.
            ax.fill_between(t, mins, maxs, linewidth=0, color="#333333")
            ax.set_ylabel("quantity of motion")

        elif panel == "waveform":
            import librosa
            wav, sr = librosa.load(str(audio), sr=None, mono=True,
                                   offset=start_s, duration=max(end_s - start_s, 0.01))
            #: Audio decimates on its OWN clock, to the same pixel columns. It is not
            #: binned to the 20 ms video grid, here or anywhere.
            mins, maxs, _ = decimate_minmax(wav, n_columns)
            t = np.linspace(start_s, end_s, len(maxs))
            ax.fill_between(t, mins, maxs, linewidth=0, color="#1f4e79")
            ax.set_ylabel("audio")

        elif panel == "speech":
            for s in speech or []:
                if s.end > start_s and s.start < end_s:
                    ax.add_patch(Rectangle((s.start, 0.0), s.end - s.start, 1.0,
                                           color="#c44e52", alpha=0.7, linewidth=0))
            ax.set_ylim(0, 1)
            ax.set_ylabel("speech")
            ax.set_yticks([])

        ax.set_xlim(start_s, end_s)
        ax.grid(axis="x", alpha=0.15)

    boundaries = []
    if hierarchy is not None:
        for level in levels:
            for a in hierarchy.levels.get(level, []):
                if a.end <= start_s or a.start >= end_s:
                    continue
                agreement = a.features.get("agreement")
                style = _BOUNDARY_STYLE.get(agreement, "dotted")
                for ax in axes:
                    ax.axvline(a.start, color="#d95f02", linestyle=style,
                               linewidth=1.2, alpha=0.9)
                axes[0].annotate(a.labels.get(level, level),
                                 (a.start, 1.02), xycoords=("data", "axes fraction"),
                                 fontsize=7, rotation=90, va="bottom",
                                 color="#d95f02")
                boundaries.append({"level": level, "start": a.start, "end": a.end,
                                   "agreement": agreement, "linestyle": style,
                                   "label": a.labels.get(level)})

    axes[-1].set_xlabel("time (s), session clock")
    note = (f"1 column = {factor} frames ({factor / fps:.3f} s); "
            f"min/max per column, not mean")
    fig.text(0.995, 0.005, note, ha="right", va="bottom", fontsize=7, color="#555555")
    fig.suptitle(title or f"{d.name}  {start_s:.1f}-{end_s:.1f} s", fontsize=10)

    out = Path(out) if out else d / f"sheet_{int(start_s):06d}_{int(end_s):06d}.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)

    out.with_suffix(".json").write_text(json.dumps(
        {"image": out.name, "start_s": start_s, "end_s": end_s,
         "decimation_factor": factor, "printed_on_figure": True,
         "seconds_per_column": factor / fps, "panels": list(drawn),
         "levels": list(levels), "boundaries": boundaries,
         "note": ("min/max per column, never a mean: a brief movement is what an "
                  "overview exists to find and a mean is what removes it")},
        indent=1) + "\n")
    return out

#!/usr/bin/env python
"""Regenerate the animated GIF illustrations for the sound-movement toolkit docs.

Companion to ``generate_example_media.py`` (which covers the video-producing
``MgVideo`` methods): this script builds the matplotlib-animated GIFs that
illustrate the array-level toolkit — pulse/cycle segmentation, cross-modal
alignment, grid QoM, the motiongram orientation option, posturography, and
pose-landmark extraction. Real toolkit functions do the analysis; synthetic
signals are seeded, so every run reproduces the same GIFs.

Outputs land in ``docs/images/examples/``. Run from the repo root:

    python scripts/generate_toolkit_media.py [--only NAME[,NAME...]]

Names: pulse, alignment, grid, motiongram, posture, pose. ``pose`` and
``grid``/``motiongram`` decode the bundled ``dancer.avi``; ``pose``
additionally needs the optional ``mediapipe`` extra.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "docs", "images", "examples")
WORK = os.path.join(REPO, "_toolkit_media_tmp")

# Shared plot style (matches the docs' light figure look).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
BLUE = "#2a78d6"
AQUA = "#1baf7a"
YELLOW = "#eda100"
RED = "#e34948"

RNG = np.random.default_rng(2026)


def _style(ax, title=None):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.xaxis.label.set_size(8)
    ax.yaxis.label.set_size(8)
    if title:
        ax.set_title(title, color=INK, fontsize=9, loc="left")


def gif_from_pngs(frame_dir: str, dst: str, fps: int) -> None:
    """PNG frame sequence -> palette-optimised looping GIF (same pipeline as
    generate_example_media.py)."""
    palette = os.path.join(WORK, "palette.png")
    src = os.path.join(frame_dir, "frame_%04d.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-i", src,
                    "-vf", "palettegen=max_colors=192", palette], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-i", src,
                    "-i", palette, "-lavfi", "paletteuse=dither=bayer:bayer_scale=3",
                    "-loop", "0", dst], check=True)
    print(f"  -> {os.path.relpath(dst, REPO)} ({os.path.getsize(dst) / 1024:.0f} KB)")


def render(name: str, n_frames: int, fps: int, draw, figsize, dpi=100) -> None:
    """Render ``draw(fig, i)`` for each frame index into PNGs, then a GIF."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frame_dir = os.path.join(WORK, name)
    shutil.rmtree(frame_dir, ignore_errors=True)
    os.makedirs(frame_dir)
    fig = plt.figure(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(SURFACE)
    for i in range(n_frames):
        fig.clf()
        draw(fig, i)
        fig.savefig(os.path.join(frame_dir, f"frame_{i:04d}.png"),
                    facecolor=SURFACE, dpi=dpi)
    plt.close(fig)
    gif_from_pngs(frame_dir, os.path.join(OUT, f"{name}.gif"), fps)


def decode_gray(video: str, fps: float, width: int) -> np.ndarray:
    """Decode a video to (T, H, W) grayscale frames through an ffmpeg pipe."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", video],
        capture_output=True, text=True, check=True)
    w0, h0 = map(int, probe.stdout.strip().split(","))
    h = int(round(h0 * width / w0 / 2) * 2)
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", video, "-vf",
         f"fps={fps},scale={width}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, width)


def decode_rgb(video: str, fps: float, width: int) -> np.ndarray:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", video],
        capture_output=True, text=True, check=True)
    w0, h0 = map(int, probe.stdout.strip().split(","))
    h = int(round(h0 * width / w0 / 2) * 2)
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", video, "-vf",
         f"fps={fps},scale={width}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, width, 3)


def dancer_clip(t0: float, t1: float, name: str) -> str:
    import musicalgestures as mg
    from musicalgestures._utils import extract_subclip
    return extract_subclip(mg.examples.dance, t0, t1,
                           target_name=os.path.join(WORK, name))


# ---------------------------------------------------------------------------
# 1. Pulse / cycle segmentation
# ---------------------------------------------------------------------------
def make_pulse() -> None:
    from musicalgestures import segment_cycles, cycle_table, fit_accelerando

    # Synthetic accelerating double-stroke pulse train (the ro-study pattern).
    ioi0_true, t_double_true = 2.1, 7.5
    onsets, t = [], 0.4
    while True:
        ioi = ioi0_true * 2 ** (-t / t_double_true)
        if ioi < 0.95:
            break
        gap = 0.16 + 0.05 * ioi / ioi0_true
        onsets += [t, t + gap]
        t += ioi
    onsets = np.array(onsets) + RNG.normal(0, 0.008, len(onsets))

    fs, dur = 200.0, float(onsets[-1] + 0.8)
    tt = np.arange(0, dur, 1 / fs)
    env = np.zeros_like(tt)
    for k, o in enumerate(onsets):
        amp = 1.0 if k % 2 == 0 else 0.72
        env += amp * np.exp(-np.maximum(tt - o, 0) / 0.055) * (tt >= o)
    env += 0.015 * np.abs(RNG.normal(0, 1, len(tt)))

    cycles = segment_cycles(onsets)
    table = cycle_table(cycles, clip_id="synthetic")
    valid = table["ioi"].notna()
    ioi0, t_double, r2 = fit_accelerando(table.loc[valid, "t"], table.loc[valid, "ioi"])

    n_frames, fps = 96, 12

    def draw(fig, i):
        ax1, ax2 = fig.subplots(2, 1, height_ratios=[1.15, 1.0])
        fig.subplots_adjust(hspace=0.55, left=0.09, right=0.97, top=0.93, bottom=0.11)
        _style(ax1, "segment_cycles() — accelerating stroke onsets")
        _style(ax2)
        ax1.set_xlim(0, dur)
        ax1.set_ylim(0, 1.35)
        ax1.set_xlabel("time (s)")
        ax1.set_ylabel("envelope")

        # Phase A (0-34): detection cursor sweeps, onset markers appear.
        sweep = min(1.0, i / 34) * dur
        ax1.plot(tt, env, color=BLUE, lw=1.0)
        seen = onsets[onsets <= sweep]
        ax1.plot(seen, np.full(len(seen), 1.12), marker=7, ls="none",
                 color=RED, ms=5, clip_on=False)
        if i <= 34:
            ax1.axvline(sweep, color=MUTED, lw=0.8, ls=":")
            ax1.text(0.99, 0.95, "onsets", transform=ax1.transAxes, ha="right",
                     color=RED, fontsize=8)

        # Phase B (35-58): cycle groups + boundaries + numbers appear.
        n_show = int(np.clip((i - 34) / 24 * len(cycles), 0, len(cycles)))
        for c in cycles[:n_show]:
            x0, x1 = c.strokes[0] - 0.06, c.strokes[-1] + 0.14
            ax1.axvspan(x0, x1, color=BLUE, alpha=0.13, lw=0)
            ax1.axvline(x0, color=MUTED, lw=0.8, ls="--")
            ax1.text((x0 + x1) / 2, 1.27, str(c.index + 1), ha="center",
                     color=INK, fontsize=8)
        if 34 < i and n_show:
            ax1.text(0.99, 0.95, "cycles", transform=ax1.transAxes, ha="right",
                     color=INK, fontsize=8)

        # Phase C (>=58): IOI panel — points, then the fitted accelerando.
        _style(ax2, "fit_accelerando() — IOI per cycle")
        ax2.set_xlim(0, dur)
        ax2.set_ylim(0, ioi0_true * 1.25)
        ax2.set_xlabel("cycle start t (s)")
        ax2.set_ylabel("IOI (s)")
        ax2.grid(color=GRID, lw=0.6)
        tv = table.loc[valid, "t"].to_numpy()
        iv = table.loc[valid, "ioi"].to_numpy()
        n_pts = int(np.clip((i - 58) / 14 * len(tv), 0, len(tv)))
        ax2.plot(tv[:n_pts], iv[:n_pts], "o", color=BLUE, ms=5)
        if i >= 74:
            frac = min(1.0, (i - 74) / 12)
            tf = np.linspace(0, dur * frac, 120)
            ax2.plot(tf, ioi0 * 2 ** (-tf / t_double), color=RED, lw=1.6)
        if i >= 86:
            ax2.text(0.98, 0.86, f"tempo doubles every {t_double:.1f} s  "
                     f"(R² = {r2:.2f})", transform=ax2.transAxes,
                     ha="right", color=RED, fontsize=8.5)

    render("pulse_segmentation", n_frames, fps, draw, figsize=(6.4, 4.2))


# ---------------------------------------------------------------------------
# 2. Audio-motion alignment (xcorr_lag)
# ---------------------------------------------------------------------------
def make_alignment() -> None:
    from scipy.ndimage import gaussian_filter1d
    from scipy.signal import correlate, correlation_lags
    from musicalgestures import xcorr_lag

    fs, dur, true_lag = 50.0, 10.0, 0.24
    t = np.arange(0, dur, 1 / fs)
    audio = np.zeros_like(t)
    for o in np.cumsum(RNG.uniform(0.6, 1.4, 12)):
        if o < dur - 0.5:
            audio += RNG.uniform(0.6, 1.0) * np.exp(-0.5 * ((t - o) / 0.07) ** 2)
    audio = gaussian_filter1d(audio, 2)
    shift = int(round(true_lag * fs))
    motion = np.roll(audio, shift)
    motion[:shift] = 0
    motion = gaussian_filter1d(motion + 0.08 * np.abs(RNG.normal(0, 1, len(t))), 2)

    lag_best, r_best = xcorr_lag(audio, motion, fs, max_lag=1.5)

    # Full correlation-vs-lag curve (same normalisation as xcorr_lag).
    n = len(t)
    xa, ym = audio - audio.mean(), motion - motion.mean()
    cc = correlate(ym, xa, mode="full")
    lags = correlation_lags(n, n, mode="full")
    m = np.abs(lags) <= int(round(1.5 * fs))
    cc, lags = cc[m] / (n * xa.std() * ym.std() + 1e-12), lags[m] / fs

    n_frames, fps = 90, 12
    n_sweep = 68

    def draw(fig, i):
        ax1, ax2 = fig.subplots(2, 1, height_ratios=[1.1, 1.0])
        fig.subplots_adjust(hspace=0.6, left=0.09, right=0.97, top=0.93, bottom=0.12)
        cur = lags[int(min(i, n_sweep) / n_sweep * (len(lags) - 1))] \
            if i < n_sweep else lag_best
        _style(ax1, "shifting the motion envelope by −lag")
        ax1.set_xlim(0, dur)
        ax1.set_ylim(0, 1.25)
        ax1.set_xlabel("time (s)")
        ax1.plot(t, audio, color=BLUE, lw=1.2, label="audio envelope")
        ax1.plot(t - cur, motion, color=AQUA, lw=1.2, label="motion envelope")
        ax1.legend(loc="upper right", fontsize=7.5, frameon=False,
                   labelcolor=[BLUE, AQUA], handlelength=1.4)

        _style(ax2, "xcorr_lag() — correlation vs lag")
        ax2.set_xlim(-1.5, 1.5)
        ax2.set_ylim(-0.4, 1.05)
        ax2.set_xlabel("lag of motion relative to audio (s)")
        ax2.set_ylabel("r")
        ax2.grid(color=GRID, lw=0.6)
        ax2.axvline(0, color=MUTED, lw=0.7)
        k = int(min(i, n_sweep) / n_sweep * (len(lags) - 1)) + 1
        ax2.plot(lags[:k], cc[:k], color=INK, lw=1.3)
        if i < n_sweep:
            ax2.plot(cur, cc[k - 1], "o", color=MUTED, ms=4)
        else:
            ax2.plot(lags, cc, color=INK, lw=1.3)
            ax2.plot(lag_best, r_best, "o", color=RED, ms=6)
            ax2.annotate(f"lag = +{lag_best:.2f} s,  r = {r_best:.2f}",
                         (lag_best, r_best), xytext=(0.55, 0.55), color=RED,
                         textcoords="axes fraction", fontsize=8.5,
                         arrowprops=dict(arrowstyle="-", color=RED, lw=0.8))
            ax1.set_title("aligned at the correlation peak",
                          color=INK, fontsize=9, loc="left")

    render("alignment_xcorr", n_frames, fps, draw, figsize=(6.4, 4.2))


# ---------------------------------------------------------------------------
# 3. Grid QoM heatmap over dancer.avi
# ---------------------------------------------------------------------------
def make_grid() -> None:
    from musicalgestures import grid_qom

    fps_v = 10.0
    clip = dancer_clip(30, 35.5, "clip_grid.avi")
    gray = decode_gray(clip, fps_v, 384)
    rgb = decode_rgb(clip, fps_v, 384)
    series, heat = grid_qom(gray, grid=(6, 4))
    T = min(len(series), len(rgb) - 1)
    win = 4  # ~0.4 s rolling window for the per-frame heat
    vmax = np.percentile(series, 98.0)

    H, W = gray.shape[1:]

    def draw(fig, i):
        ax = fig.add_axes([0.0, 0.0, 1.0, 0.92])
        ax.set_axis_off()
        fig.suptitle("grid_qom() — per-cell quantity of motion (6×4 grid)",
                     color=INK, fontsize=9, x=0.02, y=0.97, ha="left")
        ax.imshow(rgb[i + 1], extent=(0, W, H, 0))
        h = series[max(0, i - win):i + 1].mean(axis=0).reshape(4, 6)
        ax.imshow(h, extent=(0, W, H, 0), cmap="inferno", vmin=0, vmax=vmax,
                  alpha=0.62 * np.clip(h / vmax, 0, 1) ** 0.6,
                  interpolation="nearest")
        for x in np.linspace(0, W, 7):
            ax.axvline(x, color="w", lw=0.5, alpha=0.5)
        for y in np.linspace(0, H, 5):
            ax.axhline(y, color="w", lw=0.5, alpha=0.5)

    render("grid_qom", T, int(fps_v), draw,
           figsize=(3.84, 3.84 * H / W / 0.92), dpi=100)


# ---------------------------------------------------------------------------
# 4. Motiongram orientation option
# ---------------------------------------------------------------------------
def make_motiongram() -> None:
    from musicalgestures import motiongram_data

    clip = dancer_clip(8, 48, "clip_gram.avi")
    gray = decode_gray(clip, 10.0, 320)
    mg_h = motiongram_data(gray, orientation="horizontal")  # (W, T-1)
    mg_v = motiongram_data(gray, orientation="vertical")    # (H, T-1)
    for gram in (mg_h, mg_v):  # suppress codec noise, lift faint motion
        gram[gram < 0.03] = 0.0
    gamma = 0.5
    T = mg_h.shape[1]
    dur = T / 10.0

    n_frames, fps = 72, 12
    n_h = 40           # horizontal build-up
    n_hold, n_v = 8, 16

    def draw(fig, i):
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.15)
        if i < n_h + n_hold:
            gram, label, ylab = mg_h, "'horizontal'", "image column"
            frac = min(1.0, i / (n_h - 1))
        else:
            gram, label, ylab = mg_v, "'vertical'", "image row"
            frac = min(1.0, (i - n_h - n_hold) / (n_v - 1))
        _style(ax, f"motiongram_data(frames, orientation={label})")
        k = max(2, int(frac * T))
        ax.imshow(gram[:, :k] ** gamma, cmap="inferno", aspect="auto",
                  origin="upper", extent=(0, k / 10.0, gram.shape[0], 0),
                  vmin=0, vmax=1)
        ax.set_xlim(0, dur)
        ax.set_ylim(gram.shape[0], 0)
        ax.set_xlabel("time (s)")
        ax.set_ylabel(ylab)

    render("motiongram_orientation", n_frames, fps, draw, figsize=(5.6, 2.7))


# ---------------------------------------------------------------------------
# 5. Posturography: sway path, 95% ellipse, principal axis, metrics
# ---------------------------------------------------------------------------
def make_posture() -> None:
    from scipy.signal import butter, filtfilt
    from scipy.stats import chi2
    from musicalgestures import cop_sway_metrics, sway_orientation

    fs, dur = 50.0, 40.0
    n, pad = int(fs * dur), int(fs * 10)
    b, a = butter(2, 0.6 / (fs / 2))
    ml = filtfilt(b, a, RNG.normal(0, 1, n + 2 * pad))[pad:pad + n]
    ap = filtfilt(b, a, RNG.normal(0, 1, n + 2 * pad))[pad:pad + n]
    ml = ml / ml.std() * 3.8   # realistic quiet-stance sway SDs (mm)
    ap = ap / ap.std() * 7.0
    th = np.radians(18)
    xy = np.column_stack([ml * np.cos(th) - ap * np.sin(th),
                          ml * np.sin(th) + ap * np.cos(th)])

    metrics = cop_sway_metrics(xy, fs=fs)
    orient = sway_orientation(xy)

    # 95% confidence ellipse from the covariance (as confidence_ellipse_area).
    c = xy - xy.mean(axis=0)
    w, v = np.linalg.eigh(np.cov(c.T))
    r95 = np.sqrt(chi2.ppf(0.95, 2) * w)
    phi = np.linspace(0, 2 * np.pi, 120)
    ell = (v @ np.vstack([r95[1] * np.cos(phi), r95[0] * np.sin(phi)])[::-1]).T \
        + xy.mean(axis=0)
    ang = np.radians(orient["angle_deg"])
    axis_len = r95.max() * 1.15
    ax_line = np.array([xy.mean(axis=0) - axis_len * np.array([np.cos(ang), np.sin(ang)]),
                        xy.mean(axis=0) + axis_len * np.array([np.cos(ang), np.sin(ang)])])

    n_frames, fps = 96, 12
    n_draw = 58

    def draw(fig, i):
        ax = fig.add_axes([0.14, 0.11, 0.55, 0.80])
        _style(ax, "cop_sway_metrics() — centre-of-pressure sway")
        lim = np.abs(xy).max() * 1.15
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xlabel("ML (mm)")
        ax.set_ylabel("AP (mm)")
        ax.grid(color=GRID, lw=0.6)

        k = int(min(1.0, i / n_draw) * (n - 1)) + 1
        ax.plot(xy[:k, 0], xy[:k, 1], color=BLUE, lw=0.7, alpha=0.75)
        ax.plot(*xy[k - 1], "o", color=INK, ms=4)

        prog = np.clip((i - n_draw) / 10, 0, 1)          # ellipse fade-in
        if prog > 0:
            ax.plot(ell[:, 0], ell[:, 1], color=RED, lw=1.6, alpha=prog)
        if i >= n_draw + 14:                              # principal axis
            ax.plot(ax_line[:, 0], ax_line[:, 1], color=YELLOW, lw=1.6, ls="--")
            ax.text(0.03, 0.03, f"principal axis {orient['angle_deg']:.0f}°",
                    transform=ax.transAxes, color="#8a5d00", fontsize=7.5)
        if prog > 0:
            ax.text(0.03, 0.95, "95% confidence ellipse", transform=ax.transAxes,
                    color=RED, fontsize=7.5, alpha=prog)

        # Metrics ticking in on the right.
        tick = np.clip((i - n_draw) / 24, 0, 1)
        rows = [("path_len", metrics["path_len"] * tick, "mm"),
                ("path_rate", metrics["path_rate"] * tick, "mm/s"),
                ("area95", metrics["area95"] * tick, "mm²"),
                ("ap_ml_sd_ratio", metrics["ap_ml_sd_ratio"] * tick, ""),
                ("mf_mean", metrics["mf_mean"] * tick, "Hz")]
        y = 0.78
        fig.text(0.72, y + 0.08, "metrics", color=INK, fontsize=8.5,
                 fontweight="bold")
        for name, val, unit in rows:
            fig.text(0.72, y, name, color=MUTED, fontsize=7.5)
            fig.text(0.72, y - 0.045, f"{val:.1f} {unit}", color=INK, fontsize=8.5)
            y -= 0.13

    render("posturography", n_frames, fps, draw, figsize=(5.6, 4.4))


# ---------------------------------------------------------------------------
# 6. Pose-landmark extraction over dancer.avi + wrist speed
# ---------------------------------------------------------------------------
def make_pose() -> None:
    from musicalgestures import extract_pose_landmarks, limb_speed_from_landmarks

    fps_v = 12.5
    clip = dancer_clip(30, 35.5, "clip_pose.avi")
    traj = extract_pose_landmarks(clip, fps=fps_v, width=400, model_complexity=1)
    rgb = decode_rgb(clip, fps_v, 400)
    T = min(len(rgb), len(traj["landmarks"]))
    lm = traj["landmarks"][:T]
    tsec = np.arange(T) / fps_v

    wrists = lm[:, [15, 16], :2]
    conf = lm[:, [15, 16], 2]
    speed = limb_speed_from_landmarks(wrists, conf, fps_v)

    H, W = rgb.shape[1:3]

    def draw(fig, i):
        axv = fig.add_axes([0.0, 0.28, 1.0, 0.66])
        axs = fig.add_axes([0.13, 0.075, 0.84, 0.165])
        axv.set_axis_off()
        fig.suptitle("extract_pose_landmarks() + limb_speed_from_landmarks()",
                     color=INK, fontsize=9, x=0.02, y=0.985, ha="left")
        axv.imshow(rgb[i])
        pts = lm[i]
        ok = pts[:, 2] > 0.5
        axv.plot(pts[ok, 0], pts[ok, 1], "o", color=YELLOW, ms=2.6, mec="none")
        for j, col in ((15, RED), (16, "#ffffff")):
            if pts[j, 2] > 0.5:
                axv.plot(pts[j, 0], pts[j, 1], "o", color=col, ms=5.5,
                         mec=INK, mew=0.5)
        axv.set_xlim(0, W)
        axv.set_ylim(H, 0)

        _style(axs)
        axs.set_xlim(0, tsec[-1])
        axs.set_ylim(0, np.nanmax(speed) * 1.15)
        axs.set_ylabel("wrist speed\n(px/s)", fontsize=7)
        axs.tick_params(labelsize=6.5)
        axs.plot(tsec[:i + 1], speed[:i + 1], color=AQUA, lw=1.2)
        axs.plot(tsec[i], speed[i], "o", color=INK, ms=3.5)

    render("pose_landmarks", T, int(fps_v), draw,
           figsize=(4.0, 4.0 * H / W / 0.66), dpi=100)


# ---------------------------------------------------------------------------
MAKERS = dict(pulse=make_pulse, alignment=make_alignment, grid=make_grid,
              motiongram=make_motiongram, posture=make_posture, pose=make_pose)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", default=None,
                    help=f"comma-separated subset of: {', '.join(MAKERS)}")
    args = ap.parse_args()
    names = list(MAKERS) if not args.only else \
        [n.strip() for n in args.only.split(",")]
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    try:
        for name in names:
            print(f"{name}:")
            try:
                MAKERS[name]()
            except Exception as e:  # keep going so one failure doesn't abort the batch
                print(f"  !! {name} failed: {e}")
    finally:
        shutil.rmtree(WORK, ignore_errors=True)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

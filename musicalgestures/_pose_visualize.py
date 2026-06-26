import os
import numpy as np
import cv2
import matplotlib
import matplotlib.pyplot as plt
from musicalgestures._utils import MgImage, generate_outfilename


def _layout_labels(anchors, box_w, box_h, width, height, iterations=120):
    """
    Greedily spread label positions so their (approximate) boxes don't overlap.

    Starts each label slightly above its anchor, then iteratively pushes overlapping
    label boxes apart and keeps them within the image bounds. Returns an (M, 2) array
    of label-centre positions in image (pixel) coordinates.
    """
    pos = anchors.astype(float).copy()
    pos[:, 1] -= box_h * 0.7 + height * 0.01   # start a bit above the marker
    n = len(pos)
    for _ in range(iterations):
        moved = False
        for i in range(n):
            for j in range(i + 1, n):
                dx = pos[i, 0] - pos[j, 0]
                dy = pos[i, 1] - pos[j, 1]
                ox = (box_w[i] + box_w[j]) / 2 - abs(dx)
                oy = (box_h[i] + box_h[j]) / 2 - abs(dy)
                if ox > 0 and oy > 0:
                    if ox < oy:
                        s = (ox / 2 + 0.5) * (1.0 if dx >= 0 else -1.0)
                        pos[i, 0] += s
                        pos[j, 0] -= s
                    else:
                        s = (oy / 2 + 0.5) * (1.0 if dy >= 0 else -1.0)
                        pos[i, 1] += s
                        pos[j, 1] -= s
                    moved = True
        # keep labels inside the frame
        pos[:, 0] = np.clip(pos[:, 0], box_w / 2, width - box_w / 2)
        pos[:, 1] = np.clip(pos[:, 1], box_h / 2, height - box_h / 2)
        if not moved:
            break
    return pos


def _positions_from_data(data, n_points):
    """Convert collected pose rows [time, x0, y0, ...] into a (T, n_points, 2) array.

    Coordinates are normalised (0–1); exact (0, 0) entries (missing detections) become NaN.
    Returns (coords, times_seconds).
    """
    arr = np.asarray(data, dtype=float)
    times = arr[:, 0] / 1000.0
    coords = arr[:, 1:1 + 2 * n_points].reshape(len(arr), n_points, 2)
    missing = (coords[:, :, 0] == 0) & (coords[:, :, 1] == 0)
    coords = coords.copy()
    coords[missing] = np.nan
    return coords, times


def _per_marker_stats(coords, fps, diag, fmin=0.2, fmax=8.0):
    """Per-marker average quantity of motion (px/frame) and dominant frequency (Hz)."""
    from musicalgestures._analysis import dominant_frequency

    T, n, _ = coords.shape
    qom = np.zeros(n)
    freq = np.zeros(n)
    for i in range(n):
        xy = coords[:, i, :]
        d = np.diff(xy, axis=0)
        speed = np.sqrt((d ** 2).sum(axis=1)) * diag   # px/frame
        valid = speed[~np.isnan(speed)]
        if len(valid) > 1:
            qom[i] = float(np.mean(valid))
            freq[i] = dominant_frequency(np.nan_to_num(speed), fps, fmin=fmin, fmax=fmax)
    return qom, freq


def render_average_pose(data, names, connections, width, height, fps, avg_frame,
                        target_name, overwrite=False, fmin=0.2, fmax=8.0):
    """
    Render the average pose of the whole video, with per-marker quantity of motion
    (colour + label) and dominant frequency (label) annotated.

    Returns an MgImage, or None if there are too few frames.
    """
    n_points = len(names)
    coords, _ = _positions_from_data(data, n_points)
    if coords.shape[0] < 2:
        return None

    diag = float(np.sqrt(width ** 2 + height ** 2))
    qom, freq = _per_marker_stats(coords, fps, diag, fmin=fmin, fmax=fmax)

    mean_pos = np.nanmean(coords, axis=0)          # (n, 2) normalised
    mean_px = mean_pos * np.array([width, height])  # to pixels

    if target_name is None:
        target_name = '_pose_average.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    # Colour markers by QoM
    qmax = qom.max() if qom.max() > 0 else 1.0
    cmap = matplotlib.colormaps['plasma']

    aspect = width / height
    fig_h = 9
    fig, ax = plt.subplots(figsize=(fig_h * aspect, fig_h), dpi=150)
    fig.patch.set_facecolor('white')

    # Background: dimmed average frame for spatial context
    if avg_frame is not None:
        gray = cv2.cvtColor(avg_frame, cv2.COLOR_BGR2GRAY)
        bg = np.stack([gray] * 3, axis=-1).astype(np.float64) * 0.5
        ax.imshow(bg.astype(np.uint8))
    else:
        ax.set_facecolor('#f0f0f0')

    # Skeleton connections
    for a, b in connections:
        if a < n_points and b < n_points and not (np.isnan(mean_px[a]).any() or np.isnan(mean_px[b]).any()):
            ax.plot([mean_px[a, 0], mean_px[b, 0]], [mean_px[a, 1], mean_px[b, 1]],
                    color='#888888', lw=2, alpha=0.8, zorder=2, solid_capstyle='round')

    # Markers
    vis_idx = [i for i in range(n_points) if not np.isnan(mean_px[i]).any()]
    for i in vis_idx:
        ax.scatter(mean_px[i, 0], mean_px[i, 1], s=120, color=cmap(qom[i] / qmax),
                   edgecolors='white', linewidths=1.0, zorder=3)

    # Labels (name, QoM, frequency), laid out to avoid overlapping each other
    if vis_idx:
        texts = [f"{names[i]}\n{qom[i]:.1f}px | {freq[i]:.1f}Hz" for i in vis_idx]
        anchors = np.array([mean_px[i] for i in vis_idx], dtype=float)
        char_w = width * 0.0072
        line_h = height * 0.032
        box_w = np.array([max(len(n), len(f"{q:.1f}px | {f:.1f}Hz")) for n, q, f
                          in zip([names[i] for i in vis_idx],
                                 [qom[i] for i in vis_idx],
                                 [freq[i] for i in vis_idx])]) * char_w
        box_h = np.full(len(vis_idx), 2 * line_h)
        label_pos = _layout_labels(anchors, box_w, box_h, width, height)

        for k, i in enumerate(vis_idx):
            ax.annotate(texts[k],
                        xy=(anchors[k, 0], anchors[k, 1]),
                        xytext=(label_pos[k, 0], label_pos[k, 1]), textcoords='data',
                        fontsize=6, color='#101010', zorder=4,
                        ha='center', va='center',
                        arrowprops=dict(arrowstyle='-', color='#555555', lw=0.4, alpha=0.7),
                        bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                                  edgecolor='none', alpha=0.75))

    sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=matplotlib.colors.Normalize(vmin=0, vmax=qmax))
    cb = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.01)
    cb.set_label('Average quantity of motion (px/frame)', fontsize=8)
    cb.ax.tick_params(labelsize=7)

    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.set_title('Average pose — marker colour = QoM, labels = QoM | dominant frequency', fontsize=10)
    ax.axis('off')
    fig.tight_layout()
    fig.savefig(target_name, facecolor='white', bbox_inches='tight')
    plt.close(fig)

    # Also save a CSV of the per-marker statistics
    try:
        import pandas as pd
        stats_path = os.path.splitext(target_name)[0] + '_stats.csv'
        pd.DataFrame({'Marker': names,
                      'AvgQoM_px_per_frame': qom,
                      'DominantFrequency_Hz': freq}).to_csv(stats_path, index=False)
    except Exception:
        pass

    return MgImage(target_name)


def render_trajectories(data, names, width, height, fps, target_name, overwrite=False, transparent=False):
    """
    Render every marker's spatial trajectory across the whole video.

    When ``transparent`` is True the background is left transparent (and labels are
    drawn for contrast on either light or dark footage), so the PNG can be overlaid
    on the original video later. Returns an MgImage, or None if there are too few frames.
    """
    n_points = len(names)
    coords, times = _positions_from_data(data, n_points)
    if coords.shape[0] < 2:
        return None

    px = coords * np.array([width, height])  # (T, n, 2) in pixels

    if target_name is None:
        target_name = '_pose_trajectories.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    cmap = matplotlib.colormaps['hsv']
    aspect = width / height
    fig_h = 9
    fig, ax = plt.subplots(figsize=(fig_h * aspect, fig_h), dpi=150)
    if transparent:
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
    else:
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#0f0f0f')

    for i in range(n_points):
        path = px[:, i, :]
        if np.all(np.isnan(path)):
            continue
        color = cmap(i / max(n_points - 1, 1))
        ax.plot(path[:, 0], path[:, 1], color=color, lw=0.8, alpha=0.9 if transparent else 0.7, zorder=2)
        mean_xy = np.nanmean(path, axis=0)
        if not np.isnan(mean_xy).any():
            # On a transparent background, don't paint an opaque label box over the (future) video
            label_bg = 'none' if transparent else 'black'
            ax.text(mean_xy[0], mean_xy[1], names[i], color=color, fontsize=6,
                    ha='center', va='center', zorder=3,
                    bbox=dict(boxstyle='round,pad=0.12', facecolor=label_bg, edgecolor=color, alpha=0.7))

    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.set_aspect('equal')
    if not transparent:
        ax.set_title('Marker trajectories over the whole video', fontsize=10)
    ax.axis('off')
    fig.tight_layout()
    fig.savefig(target_name, transparent=transparent,
                facecolor=(None if transparent else 'white'), bbox_inches='tight')
    plt.close(fig)

    return MgImage(target_name)

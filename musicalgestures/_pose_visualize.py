import os
import numpy as np
import cv2
import matplotlib
import matplotlib.pyplot as plt
from musicalgestures._utils import MgImage, generate_outfilename


def _layout_labels(anchors, box_w, box_h, width, height, iterations=400, gap=None):
    """
    Greedily spread label positions so their (approximate) boxes don't overlap.

    Starts each label slightly above its anchor, then iteratively pushes overlapping
    label boxes apart (keeping a small gap) and keeps them within the image bounds.
    Returns an (M, 2) array of label-centre positions in image (pixel) coordinates.
    """
    pos = anchors.astype(float).copy()
    pos[:, 1] -= box_h * 0.7 + height * 0.01   # start a bit above the marker
    n = len(pos)
    if gap is None:
        gap = height * 0.006   # keep a small breathing space between boxes
    for _ in range(iterations):
        moved = False
        for i in range(n):
            for j in range(i + 1, n):
                dx = pos[i, 0] - pos[j, 0]
                dy = pos[i, 1] - pos[j, 1]
                ox = (box_w[i] + box_w[j]) / 2 + gap - abs(dx)
                oy = (box_h[i] + box_h[j]) / 2 + gap - abs(dy)
                if ox > 0 and oy > 0:
                    # push apart along the axis of least overlap
                    if ox < oy:
                        sign = 1.0 if dx >= 0 else -1.0
                        s = (ox / 2 + 0.5) * sign
                        pos[i, 0] += s
                        pos[j, 0] -= s
                    else:
                        sign = 1.0 if dy >= 0 else -1.0
                        s = (oy / 2 + 0.5) * sign
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


def _per_marker_stats(coords, fps, fmin=0.2, fmax=8.0):
    """
    Per-marker average quantity of motion and dominant frequency (Hz).

    QoM is the mean frame-to-frame displacement in **normalised** image coordinates,
    then scaled to [0, 1] across markers (the most-moving marker = 1.0).
    """
    from musicalgestures._analysis import dominant_frequency

    T, n, _ = coords.shape
    qom = np.zeros(n)
    freq = np.zeros(n)
    for i in range(n):
        xy = coords[:, i, :]
        d = np.diff(xy, axis=0)
        speed = np.sqrt((d ** 2).sum(axis=1))   # normalised units
        valid = speed[~np.isnan(speed)]
        if len(valid) > 1:
            qom[i] = float(np.mean(valid))
            freq[i] = dominant_frequency(np.nan_to_num(speed), fps, fmin=fmin, fmax=fmax)
    # Normalise QoM to [0, 1] across markers
    if qom.max() > 0:
        qom = qom / qom.max()
    return qom, freq


def render_average_pose(data, names, connections, width, height, fps, avg_frame,
                        target_name, overwrite=True, fmin=0.2, fmax=8.0, style='both'):
    """
    Render the average pose of the whole video, with per-marker quantity of motion
    (colour + label) and dominant frequency (label) annotated.

    ``style`` matches the video: 'both' draws markers + skeleton lines, 'markers' draws
    only the markers, 'skeleton' draws only the connecting joint lines. Per-marker labels
    are shown in all cases.

    Returns an MgImage, or None if there are too few frames.
    """
    n_points = len(names)
    coords, _ = _positions_from_data(data, n_points)
    if coords.shape[0] < 2:
        return None

    qom, freq = _per_marker_stats(coords, fps, fmin=fmin, fmax=fmax)  # qom already 0–1

    mean_pos = np.nanmean(coords, axis=0)          # (n, 2) normalised
    mean_px = mean_pos * np.array([width, height])  # to pixels

    if target_name is None:
        target_name = '_pose_average.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    # Colour markers by normalised QoM (0–1)
    qmax = 1.0
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

    # Skeleton connections (joint lines)
    if style in ('both', 'skeleton'):
        for a, b in connections:
            if a < n_points and b < n_points and not (np.isnan(mean_px[a]).any() or np.isnan(mean_px[b]).any()):
                ax.plot([mean_px[a, 0], mean_px[b, 0]], [mean_px[a, 1], mean_px[b, 1]],
                        color='#888888', lw=2, alpha=0.8, zorder=2, solid_capstyle='round')

    # Markers (keypoints)
    vis_idx = [i for i in range(n_points) if not np.isnan(mean_px[i]).any()]
    if style in ('both', 'markers'):
        for i in vis_idx:
            ax.scatter(mean_px[i, 0], mean_px[i, 1], s=120, color=cmap(qom[i] / qmax),
                       edgecolors='white', linewidths=1.0, zorder=3)

    # Labels: only the numbers (normalised QoM | dominant frequency), no marker name,
    # laid out to avoid overlapping each other.
    if vis_idx:
        texts = [f"{qom[i]:.2f} | {freq[i]:.1f}Hz" for i in vis_idx]
        anchors = np.array([mean_px[i] for i in vis_idx], dtype=float)
        char_w = width * 0.0080
        line_h = height * 0.034
        # Single-line boxes (no name) sized to the text, with a little extra margin
        box_w = np.array([len(t) for t in texts]) * char_w + width * 0.01
        box_h = np.full(len(vis_idx), line_h * 1.3)
        label_pos = _layout_labels(anchors, box_w, box_h, width, height)

        for k in range(len(vis_idx)):
            ax.annotate(texts[k],
                        xy=(anchors[k, 0], anchors[k, 1]),
                        xytext=(label_pos[k, 0], label_pos[k, 1]), textcoords='data',
                        fontsize=6, color='#101010', zorder=4,
                        ha='center', va='center',
                        arrowprops=dict(arrowstyle='-', color='#555555', lw=0.4, alpha=0.7),
                        bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                                  edgecolor='none', alpha=0.8))

    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis('off')
    # Make the axes fill the whole figure and save with no padding so there is no white frame.
    ax.set_position([0, 0, 1, 1])
    fig.savefig(target_name, dpi=150, pad_inches=0)
    plt.close(fig)

    # Also save a CSV of the per-marker statistics
    try:
        import pandas as pd
        stats_path = os.path.splitext(target_name)[0] + '_stats.csv'
        pd.DataFrame({'Marker': names,
                      'AvgQoM_normalized': qom,
                      'DominantFrequency_Hz': freq}).to_csv(stats_path, index=False)
    except Exception:
        pass

    return MgImage(target_name)


def render_trajectories(data, names, width, height, fps, target_name, overwrite=True,
                        background='black', labels=False):
    """
    Render every marker's spatial trajectory across the whole video.

    ``background`` chooses the PNG background: ``'black'`` (default), ``'white'``, or
    ``'transparent'`` (so the PNG can be overlaid on the original video later). Set
    ``labels=True`` to annotate each trajectory with its marker name (off by default).
    Returns an MgImage, or None if there are too few frames.
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

    bg = str(background).lower()
    if bg not in ('black', 'white', 'transparent'):
        bg = 'black'
    transparent = bg == 'transparent'

    cmap = matplotlib.colormaps['hsv']
    aspect = width / height
    fig_h = 9
    fig, ax = plt.subplots(figsize=(fig_h * aspect, fig_h), dpi=150)
    if transparent:
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
    else:
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)

    for i in range(n_points):
        path = px[:, i, :]
        if np.all(np.isnan(path)):
            continue
        color = cmap(i / max(n_points - 1, 1))
        ax.plot(path[:, 0], path[:, 1], color=color, lw=0.8, alpha=0.9 if transparent else 0.7, zorder=2)
        if labels:
            mean_xy = np.nanmean(path, axis=0)
            if not np.isnan(mean_xy).any():
                # On a transparent background, don't paint an opaque label box over the (future) video
                label_bg = 'none' if transparent else bg
                ax.text(mean_xy[0], mean_xy[1], names[i], color=color, fontsize=6,
                        ha='center', va='center', zorder=3,
                        bbox=dict(boxstyle='round,pad=0.12', facecolor=label_bg, edgecolor=color, alpha=0.7))

    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.tight_layout()
    fig.savefig(target_name, transparent=transparent,
                facecolor=(None if transparent else bg), bbox_inches='tight')
    plt.close(fig)

    return MgImage(target_name)


def render_pose_waterfall(data, names, width, height, fps, target_name, overwrite=True,
                          style='trajectories', connections=None, n_samples=40,
                          markers=None, color_by=None, cmap='hsv', dpi=200,
                          elev=20, azim=-60, lw=1.0, axes=True):
    """
    Render a 3D spatio-temporal waterfall of the pose, cascading along the time (depth) axis —
    a pose-based counterpart to ``silhouette_waterfall()``.

    ``style`` selects what is drawn:

    * ``'trajectories'`` (default): each marker's path is a continuous line through (x, time, y).
    * ``'markers'``: the markers themselves are scattered at ``n_samples`` time slices.
    * ``'skeleton'``: the skeleton joint lines are drawn at ``n_samples`` time slices.
    * ``'both'``: markers + skeleton at each time slice.

    Args:
        data (list): Collected pose rows ``[time_ms, x0, y0, x1, y1, ...]`` (normalised coords).
        names (list): Marker names (length n_points).
        width, height (int): Frame size in pixels (used to scale normalised coords).
        fps (float): Frames per second (for the time axis).
        target_name (str): Output PNG path.
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.
        style (str, optional): ``'trajectories'`` (default), ``'markers'``, ``'skeleton'``, or
            ``'both'``.
        connections (list, optional): Skeleton connection pairs (indices); required for the
            ``'skeleton'``/``'both'`` styles.
        n_samples (int, optional): Number of time slices for the marker/skeleton styles.
            Defaults to 40.
        markers (list, optional): Subset of marker names or indices to draw. Defaults to all.
        color_by (str, optional): ``'marker'`` (one colour per marker) or ``'time'`` (colour by
            time). Defaults to None ("auto"): 'marker' for trajectories, 'time' for the slice styles.
        cmap (str, optional): Matplotlib colormap. Defaults to 'hsv'.
        dpi (int, optional): Output DPI. Defaults to 200.
        elev (float, optional): 3D elevation angle. Defaults to 20.
        azim (float, optional): 3D azimuth angle. Defaults to -60.
        lw (float, optional): Line width. Defaults to 1.0.
        axes (bool, optional): Draw the axes and tick labels. Set to False for a clean render
            with all axes and text removed. Defaults to True.

    Returns:
        MgFigure: the 3D waterfall figure, or None if there are too few frames.
    """
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers 3d projection)
    from mpl_toolkits.mplot3d.art3d import Line3DCollection
    from musicalgestures._utils import MgFigure

    style = str(style).lower()
    if style not in ('trajectories', 'markers', 'skeleton', 'both'):
        style = 'trajectories'
    if color_by is None:
        color_by = 'marker' if style == 'trajectories' else 'time'

    n_points = len(names)
    coords, times = _positions_from_data(data, n_points)
    if coords.shape[0] < 2:
        return None

    px = coords * np.array([width, height])   # (T, n, 2) in pixels

    # Resolve which markers to draw
    if markers is None:
        idx = list(range(n_points))
    else:
        idx = []
        for m in markers:
            if isinstance(m, str):
                if m in names:
                    idx.append(names.index(m))
            elif 0 <= int(m) < n_points:
                idx.append(int(m))
    idx_set = set(idx)

    if target_name is None:
        target_name = '_pose_waterfall.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    cmap_obj = matplotlib.colormaps[cmap]
    fig = plt.figure(figsize=(10, 8), dpi=dpi)
    ax = fig.add_subplot(111, projection='3d')
    fig.patch.set_facecolor('white')

    tmin, tmax = float(times.min()), float(times.max())

    def _tcolor(t):
        return cmap_obj((t - tmin) / max(tmax - tmin, 1e-9))

    if style == 'trajectories':
        for k, i in enumerate(idx):
            path = px[:, i, :]
            valid = ~np.isnan(path).any(axis=1)
            if valid.sum() < 2:
                continue
            x = path[valid, 0]
            z = height - path[valid, 1]      # invert so up is up
            t = times[valid]
            if color_by == 'time':
                # Per-segment colouring along the path by time
                pts = np.column_stack([x, t, z]).reshape(-1, 1, 3)
                segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
                norm = (t[:-1] - tmin) / max(tmax - tmin, 1e-9)
                lc = Line3DCollection(segs, colors=cmap_obj(norm), linewidths=lw, alpha=0.8)
                ax.add_collection3d(lc)
            else:
                color = cmap_obj(k / max(len(idx) - 1, 1))
                ax.plot(x, t, z, color=color, lw=lw, alpha=0.8)
    else:
        # Marker/skeleton styles: draw the pose at n_samples time slices, stacked along time.
        T = coords.shape[0]
        sample_idx = np.unique(np.linspace(0, T - 1, min(int(n_samples), T)).astype(int))
        draw_markers = style in ('markers', 'both')
        draw_skeleton = style in ('skeleton', 'both') and connections is not None
        for ti in sample_idx:
            t = times[ti]
            color = _tcolor(t)
            if draw_skeleton:
                for a, b in connections:
                    if a in idx_set and b in idx_set and a < n_points and b < n_points:
                        pa, pb = px[ti, a], px[ti, b]
                        if not (np.isnan(pa).any() or np.isnan(pb).any()):
                            ax.plot([pa[0], pb[0]], [t, t],
                                    [height - pa[1], height - pb[1]],
                                    color=color, lw=lw, alpha=0.8)
            if draw_markers:
                pts = px[ti, idx, :]
                vis = ~np.isnan(pts).any(axis=1)
                if vis.any():
                    ax.scatter(pts[vis, 0], np.full(vis.sum(), t), height - pts[vis, 1],
                               color=color, s=6, alpha=0.8, depthshade=True)

    ax.set_xlim(0, width)
    ax.set_ylim(tmin, tmax)
    ax.set_zlim(0, height)
    if axes:
        ax.set_xlabel('Horizontal position (px)')
        ax.set_ylabel('Time (s)')
        ax.set_zlabel('Vertical position (px)')
    else:
        ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)
    fig.tight_layout()
    fig.savefig(target_name, facecolor='white')
    plt.close(fig)

    fig_data = {'coords': coords, 'times': times, 'names': names, 'markers': idx,
                'style': style, 'fps': fps}
    return MgFigure(figure=fig, figure_type='video.pose_waterfall', data=fig_data,
                    layers=None, image=target_name)

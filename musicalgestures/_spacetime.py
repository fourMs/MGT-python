"""
Space-time visualisations of a person in a video: stroboscope (chronophotography),
silhouette waterfall, motion history image (MHI), and a 3D space-time silhouette volume.

Silhouettes are extracted with MediaPipe selfie segmentation when available, falling back
to background subtraction against the average frame (good for static-camera recordings).
"""

import os
import numpy as np
import cv2
import musicalgestures
from musicalgestures._utils import MgImage, MgFigure, MgProgressbar, generate_outfilename, resolve_filename, ffmpeg_cmd


# ---------------------------------------------------------------------------
# Frame reading and silhouette extraction
# ---------------------------------------------------------------------------

def _iter_frames(self):
    """Yield successive BGR frames of the video via the FFmpeg pipe."""
    cmd = ['ffmpeg', '-y', '-i', self.filename]
    process = ffmpeg_cmd(cmd, total_time=self.length / self.fps if self.fps else 0, pipe='read')
    frame_bytes = self.width * self.height * 3
    try:
        while True:
            buf = process.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            yield np.frombuffer(buf, dtype=np.uint8).reshape(self.height, self.width, 3)
    finally:
        try:
            process.terminate()
        except Exception:
            pass


def _make_segmenter(method):
    """
    Return a callable ``rgb_frame -> float mask in [0,1]`` for person segmentation,
    or None to use background subtraction.

    method: 'auto' (MediaPipe if available, else None), 'mediapipe', or 'bgsub'.
    """
    if method == 'bgsub':
        return None
    try:
        import mediapipe as mp
        seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
        return lambda rgb: seg.process(rgb).segmentation_mask
    except Exception:
        if method == 'mediapipe':
            print("MediaPipe selfie segmentation unavailable; falling back to background subtraction.")
        return None


def _silhouette(frame, seg_fn, bg_gray, threshold, kernel_size=5, keep_largest=False):
    """
    Return a boolean person/foreground mask for a BGR frame.

    Args:
        seg_fn: MediaPipe segmentation callable, or None for background subtraction.
        bg_gray: grayscale background (average frame) for subtraction.
        threshold: foreground threshold in [0, 1] (fraction of 255 for bg-subtraction;
            segmentation-confidence cutoff for MediaPipe).
        kernel_size: morphological kernel for open/close cleanup (0 disables).
        keep_largest: keep only the largest connected component — a clean single-person blob.
    """
    if seg_fn is not None:
        seg = seg_fn(frame[..., ::-1])  # expects RGB
        if seg is not None:
            mask = (seg > max(threshold, 0.1)).astype(np.uint8)
        else:
            mask = None
    else:
        mask = None
    if mask is None:
        # Background subtraction fallback (ideal for a static background)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        diff = np.abs(gray - bg_gray)
        mask = (diff > threshold * 255).astype(np.uint8)

    # Clean up speckle and fill holes
    if kernel_size and kernel_size > 0:
        kernel = np.ones((int(kernel_size), int(kernel_size)), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Keep only the largest blob (the person) — removes stray foreground patches
    if keep_largest and mask.any():
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if n > 1:
            largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            mask = (labels == largest).astype(np.uint8)

    return mask.astype(bool)


def _average_frame(self):
    """Accumulate the average BGR frame (a clean background for static cameras)."""
    acc = np.zeros((self.height, self.width, 3), dtype=np.float64)
    n = 0
    pb = MgProgressbar(total=self.length, prefix='Computing background:')
    for frame in _iter_frames(self):
        acc += frame
        n += 1
        pb.progress(n)
    pb.progress(self.length)
    if n == 0:
        raise RuntimeError(f"Could not read frames from {self.filename}.")
    return (acc / n).astype(np.uint8)


# ---------------------------------------------------------------------------
# 1. Stroboscope (chronophotography)
# ---------------------------------------------------------------------------

def mg_stroboscope(self, n_samples=12, method='auto', threshold=0.1, kernel_size=5,
                   keep_largest=False, colorize=True, background='average',
                   target_name=None, overwrite=True):
    """
    Renders a stroboscope / chronophotography image: the person's silhouette at evenly
    sampled times composited onto a single frame, showing the body moving through space
    over time (Muybridge-style).

    For a clean result with a single person on a static background, raise ``threshold`` and
    set ``keep_largest=True`` so only the person's blob is composited (avoids the image
    "blowing up" from background noise).

    Args:
        n_samples (int, optional): Number of time samples (silhouettes) to composite. Defaults to 12.
        method (str, optional): Silhouette extraction: 'auto', 'mediapipe', or 'bgsub'. Defaults to 'auto'.
        threshold (float, optional): Foreground threshold (0–1). Higher rejects more background. Defaults to 0.1.
        kernel_size (int, optional): Morphological cleanup kernel for the silhouette (0 disables). Defaults to 5.
        keep_largest (bool, optional): Keep only the largest blob (the person). Defaults to False.
        colorize (bool, optional): Tint each silhouette by time (early→late) for a temporal cue. Defaults to True.
        background (str, optional): 'average' (clean plate), 'first' (first frame), 'black' or 'white'. Defaults to 'average'.
        target_name (str, optional): Output name. Defaults to None ("_stroboscope.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.

    Returns:
        MgImage: the stroboscope image.
    """
    target_name = resolve_filename(self.of, '_stroboscope.png', target_name, overwrite)

    avg = _average_frame(self)
    bg_gray = cv2.cvtColor(avg, cv2.COLOR_BGR2GRAY).astype(np.float32)
    seg_fn = _make_segmenter(method)

    total = int(self.length)
    sample_idx = set(np.linspace(0, total - 1, min(n_samples, total)).astype(int).tolist())

    if background == 'average':
        canvas = avg.copy()
    elif background == 'white':
        canvas = np.full((self.height, self.width, 3), 255, np.uint8)
    elif background == 'black':
        canvas = np.zeros((self.height, self.width, 3), np.uint8)
    else:
        canvas = None  # 'first' → set on first read

    import matplotlib
    cmap = matplotlib.colormaps['viridis']

    pb = MgProgressbar(total=self.length, prefix='Rendering stroboscope:')
    i = 0
    order = 0
    n_order = max(len(sample_idx) - 1, 1)
    for frame in _iter_frames(self):
        if canvas is None:
            canvas = frame.copy()
        if i in sample_idx:
            mask = _silhouette(frame, seg_fn, bg_gray, threshold, kernel_size, keep_largest)
            if colorize:
                tint = (np.array(cmap(order / n_order)[:3]) * 255)[::-1]  # RGB→BGR
                tinted = (frame.astype(np.float32) * 0.5 + tint * 0.5).astype(np.uint8)
                canvas[mask] = tinted[mask]
            else:
                canvas[mask] = frame[mask]
            order += 1
        i += 1
        pb.progress(i)
    pb.progress(self.length)

    cv2.imwrite(target_name, canvas)
    self.stroboscope_image = MgImage(target_name)
    return self.stroboscope_image


# ---------------------------------------------------------------------------
# 2. Silhouette waterfall
# ---------------------------------------------------------------------------

def mg_silhouette_waterfall(self, n_samples=40, method='auto', threshold=0.1, kernel_size=5,
                            keep_largest=False, axis='horizontal', cmap='viridis', dpi=200,
                            elev=35, azim=-60, axes=True, crop=False, target_name=None, overwrite=True):
    """
    Renders a 3D silhouette waterfall: the per-frame silhouette projected onto one spatial
    axis and stacked as cascading curves along a time (depth) axis, so the body's occupancy
    profile "flows" through time — like a 3D spectrogram waterfall.

    For a single person on a static background, raise ``threshold`` and/or set
    ``keep_largest=True`` for a cleaner profile.

    Args:
        n_samples (int, optional): Number of time slices (profiles) to stack. Defaults to 40.
        method (str, optional): Silhouette extraction: 'auto', 'mediapipe', or 'bgsub'. Defaults to 'auto'.
        threshold (float, optional): Foreground threshold (0–1). Higher rejects more background. Defaults to 0.1.
        kernel_size (int, optional): Morphological cleanup kernel (0 disables). Defaults to 5.
        keep_largest (bool, optional): Keep only the largest blob (the person). Defaults to False.
        axis (str, optional): 'horizontal' profiles over x (collapse y); 'vertical' profiles over y. Defaults to 'horizontal'.
        cmap (str, optional): Matplotlib colormap (by time). Defaults to 'viridis'.
        dpi (int, optional): Output DPI. Defaults to 200.
        elev (float, optional): 3D elevation angle. Defaults to 35.
        azim (float, optional): 3D azimuth angle. Defaults to -60.
        axes (bool, optional): Draw the axes, tick labels, and title. Set to False for a clean
            render with all axes and text removed. Defaults to True.
        crop (bool, optional): Tighten the spatial axis to the occupied (nonzero) extent and trim
            the surrounding whitespace, so the figure shows mostly the data. Defaults to False.
        target_name (str, optional): Output name. Defaults to None ("_silhouette_waterfall.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.

    Returns:
        MgFigure: the 3D waterfall figure (the stacked profiles are in ``.data``).
    """
    import matplotlib
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers 3d projection)

    target_name = resolve_filename(self.of, '_silhouette_waterfall.png', target_name, overwrite)

    avg = _average_frame(self)
    bg_gray = cv2.cvtColor(avg, cv2.COLOR_BGR2GRAY).astype(np.float32)
    seg_fn = _make_segmenter(method)

    total = int(self.length)
    sample_idx = sorted(set(np.linspace(0, total - 1, min(n_samples, total)).astype(int).tolist()))
    sample_set = set(sample_idx)

    profiles = []
    times = []
    pb = MgProgressbar(total=self.length, prefix='Rendering silhouette waterfall:')
    i = 0
    for frame in _iter_frames(self):
        if i in sample_set:
            mask = _silhouette(frame, seg_fn, bg_gray, threshold, kernel_size, keep_largest)
            if axis == 'horizontal':
                profiles.append(mask.sum(axis=0).astype(np.float32))   # over x (length W)
            else:
                profiles.append(mask.sum(axis=1).astype(np.float32))   # over y (length H)
            times.append(i / max(self.fps, 1))
        i += 1
        pb.progress(i)
    pb.progress(self.length)

    arr = np.array(profiles, dtype=np.float32)  # (n_slices, axis_len)
    if arr.size and arr.max() > 0:
        arr = arr / arr.max()

    cmap_obj = matplotlib.colormaps[cmap]
    fig = plt.figure(figsize=(11, 8), dpi=dpi)
    ax = fig.add_subplot(111, projection='3d')
    fig.patch.set_facecolor('white')

    pos = np.arange(arr.shape[1]) if arr.size else np.array([])
    n_slices = max(len(profiles) - 1, 1)
    for k, (prof, t) in enumerate(zip(arr, times)):
        ax.plot(pos, np.full_like(pos, t, dtype=float), prof,
                color=cmap_obj(k / n_slices), lw=0.9, alpha=0.9)

    if crop and arr.size:
        # Tighten the spatial axis to the occupied (nonzero) profile extent.
        occupied = np.where(arr.max(axis=0) > 0)[0]
        if occupied.size:
            pad = max(int((occupied[-1] - occupied[0]) * 0.05), 1)
            ax.set_xlim(max(occupied[0] - pad, 0), min(occupied[-1] + pad, arr.shape[1] - 1))

    if axes:
        ax.set_xlabel('Horizontal position (px)' if axis == 'horizontal' else 'Vertical position (px)')
        ax.set_ylabel('Time (s)')
        ax.set_zlabel('Silhouette extent')
        ax.set_title('Silhouette waterfall')
    else:
        ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)
    if crop:
        ax.set_position([0, 0, 1, 1])
        try:
            ax.set_box_aspect(None, zoom=1.5)
        except TypeError:
            pass
        save_kwargs = {'bbox_inches': 'tight', 'pad_inches': 0}
    else:
        fig.tight_layout()
        save_kwargs = {}
    fig.savefig(target_name, facecolor='white', **save_kwargs)
    plt.close(fig)

    data = {'profiles': arr, 'times': np.array(times), 'axis': axis}
    mgf = MgFigure(figure=fig, figure_type='video.silhouette_waterfall', data=data, layers=None, image=target_name)
    self.silhouette_waterfall_figure = mgf
    return mgf


# ---------------------------------------------------------------------------
# 3. Motion History Image (MHI)
# ---------------------------------------------------------------------------

def mg_motionhistory(self, threshold=0.05, decay=0.3, normalize=False, blur=0,
                     cmap='hot', dpi=300, target_name=None, overwrite=True):
    """
    Renders a Motion History Image (Bobick & Davis): a single image where intensity encodes
    how recently motion occurred at each pixel (recent motion bright, older motion fades out).

    A motion mark is set to full intensity where motion occurs and then **decays** linearly to
    zero over a window set by ``decay``, so old motion disappears instead of accumulating and
    washing out the image. Raise ``threshold`` to ignore background noise, and lower ``decay``
    for shorter (less crowded) trails.

    Args:
        threshold (float, optional): Motion threshold (0–1) on frame differences. Higher rejects
            more background noise. Defaults to 0.05.
        decay (float, optional): Fade window as a fraction of the clip length (0–1): a motion
            mark fully fades after this fraction of the video. Smaller = shorter trails, less
            blow-out. Defaults to 0.3.
        normalize (bool, optional): Stretch the result to the full intensity range. Defaults to False.
            The MHI is already built in [0, 1], so normalization is rarely needed; when the final
            frames are static it amplifies faint residual trails and over-brightens ("blows up") the
            image, so it is guarded to skip when the peak intensity is very low.
        blur (int, optional): Optional Gaussian smoothing radius for the difference mask (0 = off).
            Helps suppress speckle noise. Defaults to 0.
        cmap (str, optional): Matplotlib colormap. Defaults to 'hot'.
        dpi (int, optional): Output DPI. Defaults to 300.
        target_name (str, optional): Output name. Defaults to None ("_mhi.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.

    Returns:
        MgImage: the motion history image.
    """
    import matplotlib
    import matplotlib.pyplot as plt

    target_name = resolve_filename(self.of, '_mhi.png', target_name, overwrite)

    total = max(int(self.length), 1)
    decay_frames = max(1, int(decay * total))
    step = 1.0 / decay_frames

    mhi = np.zeros((self.height, self.width), dtype=np.float32)
    prev_gray = None
    pb = MgProgressbar(total=self.length, prefix='Rendering motion history image:')
    i = 0
    for frame in _iter_frames(self):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev_gray is not None:
            diff = np.abs(gray - prev_gray)
            if blur and blur > 0:
                k = int(blur) * 2 + 1
                diff = cv2.GaussianBlur(diff, (k, k), 0)
            motion = diff > (threshold * 255)
            # Decay everything, then re-stamp current motion to full intensity
            mhi -= step
            np.clip(mhi, 0.0, 1.0, out=mhi)
            mhi[motion] = 1.0
        prev_gray = gray
        i += 1
        pb.progress(i)
    pb.progress(self.length)

    # Only normalize when there is substantial motion intensity; otherwise dividing by a tiny
    # peak amplifies faint residual trails into a washed-out ("blown up") image.
    if normalize and mhi.max() > 0.2:
        mhi = mhi / mhi.max()

    fig, ax = plt.subplots(figsize=(12, 12 * self.height / self.width), dpi=dpi)
    fig.patch.set_facecolor('white')
    ax.imshow(mhi, cmap=cmap, vmin=0.0, vmax=1.0)
    ax.set_title('Motion History Image (bright = recent motion)')
    ax.axis('off')
    fig.tight_layout()
    fig.savefig(target_name, facecolor='white', bbox_inches='tight')
    plt.close(fig)

    self.mhi_image = MgImage(target_name)
    return self.mhi_image


# ---------------------------------------------------------------------------
# 4. 3D space-time silhouette volume
# ---------------------------------------------------------------------------

def mg_spacetime_volume(self, n_samples=50, downsample=8, method='auto', threshold=0.1,
                        kernel_size=5, keep_largest=False, cmap='viridis', dpi=200,
                        elev=20, azim=-60, target_name=None, overwrite=True):
    """
    Renders a 3D space-time scatter of the person's silhouette: points (x, y, t) where the
    silhouette is present, with time on the depth axis and colour, showing how the body
    occupies space through time.

    Args:
        n_samples (int, optional): Number of time samples (depth slices). Defaults to 50.
        downsample (int, optional): Spatial downsampling factor for the silhouette points. Defaults to 8.
        method (str, optional): Silhouette extraction: 'auto', 'mediapipe', or 'bgsub'. Defaults to 'auto'.
        threshold (float, optional): Foreground threshold (0–1). Higher rejects more background. Defaults to 0.1.
        kernel_size (int, optional): Morphological cleanup kernel for the silhouette (0 disables). Defaults to 5.
        keep_largest (bool, optional): Keep only the largest blob (the person). Defaults to False.
        cmap (str, optional): Matplotlib colormap for time. Defaults to 'viridis'.
        dpi (int, optional): Output DPI. Defaults to 200.
        elev (float, optional): 3D elevation angle. Defaults to 20.
        azim (float, optional): 3D azimuth angle. Defaults to -60.
        target_name (str, optional): Output name. Defaults to None ("_spacetime_volume.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.

    Returns:
        MgFigure: the 3D space-time figure (data holds the point cloud).
    """
    import matplotlib
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers 3d projection)

    target_name = resolve_filename(self.of, '_spacetime_volume.png', target_name, overwrite)

    avg = _average_frame(self)
    bg_gray = cv2.cvtColor(avg, cv2.COLOR_BGR2GRAY).astype(np.float32)
    seg_fn = _make_segmenter(method)

    total = int(self.length)
    sample_idx = set(np.linspace(0, total - 1, min(n_samples, total)).astype(int).tolist())

    xs, ys, ts = [], [], []
    pb = MgProgressbar(total=self.length, prefix='Building space-time volume:')
    i = 0
    for frame in _iter_frames(self):
        if i in sample_idx:
            mask = _silhouette(frame, seg_fn, bg_gray, threshold, kernel_size, keep_largest)
            sub = mask[::downsample, ::downsample]
            yy, xx = np.nonzero(sub)
            xs.append(xx * downsample)
            ys.append(yy * downsample)
            ts.append(np.full(len(xx), i / max(self.fps, 1)))  # seconds
        i += 1
        pb.progress(i)
    pb.progress(self.length)

    xs = np.concatenate(xs) if xs else np.array([])
    ys = np.concatenate(ys) if ys else np.array([])
    ts = np.concatenate(ts) if ts else np.array([])

    fig = plt.figure(figsize=(10, 8), dpi=dpi)
    ax = fig.add_subplot(111, projection='3d')
    fig.patch.set_facecolor('white')
    if len(xs):
        ax.scatter(xs, ts, self.height - ys, c=ts, cmap=cmap, s=2, alpha=0.5, depthshade=True)
    ax.set_xlabel('x (px)')
    ax.set_ylabel('time (s)')
    ax.set_zlabel('y (px)')
    ax.set_title('Space-time silhouette volume')
    ax.view_init(elev=elev, azim=azim)
    fig.tight_layout()
    fig.savefig(target_name, facecolor='white')
    plt.close(fig)

    data = {'x': xs, 'y': ys, 't': ts, 'fps': self.fps}
    mgf = MgFigure(figure=fig, figure_type='video.spacetime_volume', data=data, layers=None, image=target_name)
    self.spacetime_volume_figure = mgf
    return mgf

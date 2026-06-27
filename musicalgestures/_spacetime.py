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
from musicalgestures._utils import MgImage, MgFigure, MgProgressbar, generate_outfilename, ffmpeg_cmd


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


def _silhouette(frame, seg_fn, bg_gray, threshold):
    """Return a boolean person/foreground mask for a BGR frame."""
    if seg_fn is not None:
        mask = seg_fn(frame[..., ::-1])  # expects RGB
        if mask is not None:
            return mask > 0.5
    # Background subtraction fallback
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    diff = np.abs(gray - bg_gray)
    mask = (diff > threshold * 255).astype(np.uint8)
    # Clean up speckle and fill holes
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
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

def mg_stroboscope(self, n_samples=12, method='auto', threshold=0.1, colorize=True,
                   background='average', target_name=None, overwrite=False):
    """
    Renders a stroboscope / chronophotography image: the person's silhouette at evenly
    sampled times composited onto a single frame, showing the body moving through space
    over time (Muybridge-style).

    Args:
        n_samples (int, optional): Number of time samples (silhouettes) to composite. Defaults to 12.
        method (str, optional): Silhouette extraction: 'auto', 'mediapipe', or 'bgsub'. Defaults to 'auto'.
        threshold (float, optional): Foreground threshold (0–1) for background subtraction. Defaults to 0.1.
        colorize (bool, optional): Tint each silhouette by time (early→late) for a temporal cue. Defaults to True.
        background (str, optional): 'average' (clean plate), 'first' (first frame), 'black' or 'white'. Defaults to 'average'.
        target_name (str, optional): Output name. Defaults to None ("_stroboscope.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to False.

    Returns:
        MgImage: the stroboscope image.
    """
    if target_name is None:
        target_name = self.of + '_stroboscope.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

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
            mask = _silhouette(frame, seg_fn, bg_gray, threshold)
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

def mg_silhouette_waterfall(self, method='auto', threshold=0.1, axis='horizontal',
                            cmap='magma', dpi=300, target_name=None, overwrite=False):
    """
    Renders a silhouette waterfall: the per-frame silhouette projected onto one spatial
    axis and stacked over time, so the body's occupancy flows through the image.

    Args:
        method (str, optional): Silhouette extraction: 'auto', 'mediapipe', or 'bgsub'. Defaults to 'auto'.
        threshold (float, optional): Foreground threshold (0–1) for background subtraction. Defaults to 0.1.
        axis (str, optional): 'horizontal' collapses the vertical axis (image = time × x);
            'vertical' collapses the horizontal axis (image = y × time). Defaults to 'horizontal'.
        cmap (str, optional): Matplotlib colormap. Defaults to 'magma'.
        dpi (int, optional): Output DPI. Defaults to 300.
        target_name (str, optional): Output name. Defaults to None ("_silhouette_waterfall.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to False.

    Returns:
        MgImage: the waterfall image.
    """
    import matplotlib
    import matplotlib.pyplot as plt

    if target_name is None:
        target_name = self.of + '_silhouette_waterfall.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    avg = _average_frame(self)
    bg_gray = cv2.cvtColor(avg, cv2.COLOR_BGR2GRAY).astype(np.float32)
    seg_fn = _make_segmenter(method)

    profiles = []
    pb = MgProgressbar(total=self.length, prefix='Rendering silhouette waterfall:')
    i = 0
    for frame in _iter_frames(self):
        mask = _silhouette(frame, seg_fn, bg_gray, threshold)
        if axis == 'horizontal':
            profiles.append(mask.sum(axis=0))   # collapse y → length W
        else:
            profiles.append(mask.sum(axis=1))   # collapse x → length H
        i += 1
        pb.progress(i)
    pb.progress(self.length)

    arr = np.array(profiles, dtype=np.float32)  # (T, axis_len)
    if arr.max() > 0:
        arr = arr / arr.max()

    fig, ax = plt.subplots(figsize=(12, 6), dpi=dpi)
    fig.patch.set_facecolor('white')
    if axis == 'horizontal':
        # time flows downward, x across
        ax.imshow(arr, aspect='auto', cmap=cmap, origin='upper')
        ax.set_xlabel('Horizontal position (px)')
        ax.set_ylabel('Time (frames)')
    else:
        # y down, time across
        ax.imshow(arr.T, aspect='auto', cmap=cmap, origin='upper')
        ax.set_xlabel('Time (frames)')
        ax.set_ylabel('Vertical position (px)')
    ax.set_title('Silhouette waterfall')
    fig.tight_layout()
    fig.savefig(target_name, facecolor='white')
    plt.close(fig)

    self.silhouette_waterfall_image = MgImage(target_name)
    return self.silhouette_waterfall_image


# ---------------------------------------------------------------------------
# 3. Motion History Image (MHI)
# ---------------------------------------------------------------------------

def mg_motionhistory(self, threshold=0.05, cmap='hot', dpi=300, target_name=None, overwrite=False):
    """
    Renders a Motion History Image (Bobick & Davis): a single image where intensity encodes
    how recently motion occurred at each pixel (recent motion bright, older motion fades).

    Args:
        threshold (float, optional): Motion threshold (0–1) on frame differences. Defaults to 0.05.
        cmap (str, optional): Matplotlib colormap. Defaults to 'hot'.
        dpi (int, optional): Output DPI. Defaults to 300.
        target_name (str, optional): Output name. Defaults to None ("_mhi.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to False.

    Returns:
        MgImage: the motion history image.
    """
    import matplotlib
    import matplotlib.pyplot as plt

    if target_name is None:
        target_name = self.of + '_mhi.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    total = max(int(self.length), 1)
    mhi = np.zeros((self.height, self.width), dtype=np.float32)
    prev_gray = None
    decay = 1.0 / total
    t = 0.0
    pb = MgProgressbar(total=self.length, prefix='Rendering motion history image:')
    i = 0
    for frame in _iter_frames(self):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev_gray is not None:
            motion = np.abs(gray - prev_gray) > (threshold * 255)
            t += decay
            mhi[motion] = t                 # stamp current time where motion happens
        prev_gray = gray
        i += 1
        pb.progress(i)
    pb.progress(self.length)

    # Normalise so the most recent motion is brightest
    if mhi.max() > 0:
        mhi = mhi / mhi.max()

    fig, ax = plt.subplots(figsize=(12, 12 * self.height / self.width), dpi=dpi)
    fig.patch.set_facecolor('white')
    ax.imshow(mhi, cmap=cmap)
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
                        cmap='viridis', dpi=200, elev=20, azim=-60, target_name=None, overwrite=False):
    """
    Renders a 3D space-time scatter of the person's silhouette: points (x, y, t) where the
    silhouette is present, with time on the depth axis and colour, showing how the body
    occupies space through time.

    Args:
        n_samples (int, optional): Number of time samples (depth slices). Defaults to 50.
        downsample (int, optional): Spatial downsampling factor for the silhouette points. Defaults to 8.
        method (str, optional): Silhouette extraction: 'auto', 'mediapipe', or 'bgsub'. Defaults to 'auto'.
        threshold (float, optional): Foreground threshold (0–1) for background subtraction. Defaults to 0.1.
        cmap (str, optional): Matplotlib colormap for time. Defaults to 'viridis'.
        dpi (int, optional): Output DPI. Defaults to 200.
        elev (float, optional): 3D elevation angle. Defaults to 20.
        azim (float, optional): 3D azimuth angle. Defaults to -60.
        target_name (str, optional): Output name. Defaults to None ("_spacetime_volume.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to False.

    Returns:
        MgFigure: the 3D space-time figure (data holds the point cloud).
    """
    import matplotlib
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers 3d projection)

    if target_name is None:
        target_name = self.of + '_spacetime_volume.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

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
            mask = _silhouette(frame, seg_fn, bg_gray, threshold)
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

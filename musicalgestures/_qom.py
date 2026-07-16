"""
Quantity-of-motion (QoM) signal cores for position, pose and accelerometer
data.

Band-limited QoM (with an automatic decimate+SOS regime for very low
frequency bands), accelerometer-to-speed integration, per-landmark-group
pose QoM, body-scale normalisation for framing-invariant comparisons,
spatial grid QoM, and small envelope/binning helpers.

These functions are independent of the MgVideo/MgAudio classes and operate
on plain numpy arrays (marker/landmark trajectories, accelerometer data,
grayscale frame stacks, 1-D signals).

Sources: stillstanding study and Westney-comparisons study (Jensenius).
"""

import numpy as np


def _interp_nans(x):
    """Linearly interpolate non-finite entries of a 1-D array (returns a copy)."""
    x = np.asarray(x, float).copy()
    m = np.isfinite(x)
    if m.sum() > 2 and not m.all():
        x = np.interp(np.arange(len(x)), np.flatnonzero(m), x[m])
    return x


def envelope(x, fs, smooth=1.0, normalize=True):
    """
    Smooth, optionally z-scored envelope of a signal: Savitzky-Golay
    smoothing (order 2, window `smooth` seconds) followed by
    standardisation. Used to compare motion/audio envelopes across sources
    on a common, amplitude-free scale.

    Source: Westney-comparisons study (Jensenius).

    Args:
        x (np.ndarray): Input 1-D signal.
        fs (float): Sampling rate of the signal (Hz).
        smooth (float, optional): Smoothing window in seconds. None or 0 disables
            smoothing. Defaults to 1.0.
        normalize (bool, optional): If True, z-score the result. Defaults to True.

    Returns:
        np.ndarray: The smoothed (and optionally z-scored) envelope, same length
            as the input.
    """
    from scipy.signal import savgol_filter
    x = np.asarray(x, float)
    if smooth:
        w = max(3, int(smooth * fs) | 1)
        if len(x) > w:
            x = savgol_filter(x, w, 2)
    if normalize:
        x = (x - x.mean()) / (x.std() + 1e-9)
    return x


def bin_series(x, fs, bin_s=1.0):
    """
    Mean of consecutive, non-overlapping bins of a signal (e.g. a per-second
    quantity-of-motion envelope from a per-frame speed series). Trailing
    samples that do not fill a whole bin are dropped.

    Source: stillstanding study (Jensenius); also used in the
    Westney-comparisons study as a per-second envelope.

    Args:
        x (np.ndarray): Input 1-D signal.
        fs (float): Sampling rate of the signal (Hz).
        bin_s (float, optional): Bin length in seconds. Defaults to 1.0.

    Returns:
        np.ndarray: One mean value per bin (empty if the signal is shorter than
            two bins).
    """
    x = np.asarray(x, float)
    step = max(1, int(round(fs * bin_s)))
    n = len(x) // step
    if n < 2:
        return np.array([])
    return x[:n * step].reshape(n, step).mean(axis=1)


def band_limited_qom(pos, fs, lo=0.3, hi=15.0, order=4, auto_decimate=True):
    """
    Band-limited quantity of motion from a position trajectory: the position
    is band-pass filtered (zero phase) to `[lo, hi]` Hz and the QoM is the
    per-frame speed, i.e. the Euclidean norm of the first difference times
    the sampling rate (units of the input per second).

    For very low bands relative to the sampling rate (band edge below about
    fs/40), a direct high-order band-pass is numerically fragile; in that
    regime the trajectory is first decimated (zero phase) so the band sits
    comfortably in the new Nyquist range, then filtered with a second-order
    section (SOS) band-pass. This is the "slow sway" regime (e.g. 0.1-0.5 Hz
    postural sway from 100 Hz mocap). Set `auto_decimate=False` to force the
    direct filter.

    Source: stillstanding study and Westney-comparisons study (Jensenius) --
    this unifies the band-limited QoM cores used on mocap markers (mm),
    MediaPipe landmarks (px) and slow postural sway across both studies.

    Args:
        pos (np.ndarray): Position trajectory of shape (N,) or (N, D) (e.g. D=2
            image coordinates or D=3 mocap coordinates). Non-finite samples are
            linearly interpolated per dimension.
        fs (float): Sampling rate of the trajectory (Hz).
        lo (float, optional): Lower band edge (Hz). Defaults to 0.3.
        hi (float, optional): Upper band edge (Hz), clipped to 0.9 x Nyquist.
            Defaults to 15.0.
        order (int, optional): Butterworth order of the direct band-pass.
            Defaults to 4.
        auto_decimate (bool, optional): Enable the decimate+SOS low-band regime.
            Defaults to True.

    Returns:
        tuple: `(speed, fs_out)` where `speed` is the per-frame speed series
            (length N-1, or shorter when decimated) and `fs_out` is its
            sampling rate (equal to `fs` unless decimated). `speed` is empty
            (and `fs_out` equals the input `fs`) when the input has fewer
            than `int(fs) + 5` samples, or when it still contains non-finite
            samples after per-dimension interpolation (i.e. a dimension had
            fewer than 3 finite samples to interpolate from). In the
            auto-decimate regime, `speed` is also empty (with `fs_out` the
            decimated rate) when decimation leaves fewer than ~30 samples --
            too few for a stable SOS band-pass.

    Raises:
        ValueError: If the band is invalid, i.e. does not satisfy
            `0 < lo < hi <= 0.45*fs` (after `hi` is clipped to 0.9 x Nyquist).
    """
    from scipy import signal
    pos = np.asarray(pos, float)
    if pos.ndim == 1:
        pos = pos[:, None]
    pos = np.column_stack([_interp_nans(pos[:, i]) for i in range(pos.shape[1])])

    hi_eff = min(hi, 0.9 * fs / 2)
    if not (0 < lo < hi_eff <= 0.45 * fs + 1e-9):
        raise ValueError("band must satisfy 0 < lo < hi <= 0.45*fs")

    if len(pos) < int(fs) + 5 or not np.isfinite(pos).all():
        return np.array([]), fs

    if auto_decimate and fs / hi_eff >= 40:
        q = int(min(13, fs // (20 * hi_eff)))
        pos = signal.decimate(pos, q, axis=0, zero_phase=True)
        fs_out = fs / q
        if len(pos) < 30:
            return np.array([]), fs_out
        sos = signal.butter(2, [lo / (fs_out / 2), hi_eff / (fs_out / 2)],
                            btype="band", output="sos")
        filtered = signal.sosfiltfilt(sos, pos, axis=0)
    else:
        fs_out = fs
        b, a = signal.butter(order, [lo / (fs / 2), hi_eff / (fs / 2)], btype="band")
        filtered = signal.filtfilt(b, a, pos, axis=0)
    speed = np.linalg.norm(np.diff(filtered, axis=0), axis=1) * fs_out
    return speed, fs_out


def accel_to_speed(acc, fs, highpass=0.3, order=2, normalize_gravity=False):
    """
    Integrated speed from a 3-axis accelerometer: each axis is high-pass
    filtered (removing gravity and DC), integrated to velocity, high-pass
    filtered again (killing integration drift), and the speed is the
    Euclidean norm of the velocity (m/s for input in m/s^2).

    Source: stillstanding study (Jensenius) -- the "corpus method" for
    integrated quantity of motion from chest-worn accelerometers.

    Args:
        acc (np.ndarray): Acceleration of shape (N, 3) in m/s^2 (or raw counts
            with `normalize_gravity=True`).
        fs (float): Sampling rate (Hz).
        highpass (float, optional): High-pass cutoff (Hz) used both before and
            after integration. Defaults to 0.3.
        order (int, optional): Butterworth order of the high-pass filters.
            Defaults to 2.
        normalize_gravity (bool, optional): If True, rescale the raw input so
            that the median vector magnitude equals 1 g (9.80665 m/s^2) before
            filtering -- useful for uncalibrated sensors whose resting output
            should be gravity. Defaults to False.

    Returns:
        np.ndarray: Speed series of length N (m/s).
    """
    from scipy.signal import butter, filtfilt
    G = 9.80665
    acc = np.asarray(acc, float)
    if normalize_gravity:
        norm = np.linalg.norm(acc, axis=1)
        acc = acc / np.median(norm) * G
    b, a = butter(order, highpass / (fs / 2), btype="high")
    acc = filtfilt(b, a, acc, axis=0)
    vel = np.cumsum(acc, axis=0) / fs
    vel = filtfilt(b, a, vel, axis=0)
    return np.linalg.norm(vel, axis=1)


def group_qom(points, fs, lo=0.3, hi=15.0, **kwargs):
    """
    Mean band-limited quantity of motion over a group of markers/landmarks,
    plus the group's mean speed envelope: each trajectory is passed through
    `band_limited_qom` and the per-trajectory speeds are averaged.

    Source: stillstanding study and Westney-comparisons study (Jensenius) --
    per-body-part QoM (head, shoulders, arms, wrists) from mocap markers and
    pose landmarks.

    Args:
        points (np.ndarray): Trajectories of shape (N, M, D): N frames, M
            markers/landmarks, D spatial dimensions.
        fs (float): Sampling rate (Hz).
        lo (float, optional): Lower band edge (Hz). Defaults to 0.3.
        hi (float, optional): Upper band edge (Hz). Defaults to 15.0.
        **kwargs: Passed on to `band_limited_qom`.

    Returns:
        tuple: `(qom, speed, fs_out)` where `qom` is the mean speed across
            markers and time (NaN if no marker yields a valid series), `speed`
            is the group's mean per-frame speed series, and `fs_out` its
            sampling rate.
    """
    points = np.asarray(points, float)
    speeds, fs_out = [], fs
    for m in range(points.shape[1]):
        sp, fs_out = band_limited_qom(points[:, m, :], fs, lo=lo, hi=hi, **kwargs)
        if len(sp):
            speeds.append(sp)
    if not speeds:
        return np.nan, np.array([]), fs_out
    L = min(len(s) for s in speeds)
    mean_speed = np.mean([s[:L] for s in speeds], axis=0)
    return float(np.mean([s.mean() for s in speeds])), mean_speed, fs_out


def pose_qom(landmarks, fs, lo=0.3, hi=5.0, **kwargs):
    """
    Band-limited quantity of motion of 2-D pose landmarks (px/s): a thin
    wrapper around `group_qom` with the band used for image-space pose
    trajectories (0.3-5 Hz), where higher bands are dominated by landmark
    jitter rather than motion.

    Source: Westney-comparisons study (Jensenius).

    Args:
        landmarks (np.ndarray): Landmark trajectories of shape (N, L, 2) in
            pixels (a single landmark of shape (N, 2) is also accepted).
        fs (float): Sampling rate (Hz, e.g. video frame rate).
        lo (float, optional): Lower band edge (Hz). Defaults to 0.3.
        hi (float, optional): Upper band edge (Hz). Defaults to 5.0.
        **kwargs: Passed on to `band_limited_qom`.

    Returns:
        tuple: `(qom, speed, fs_out)` as in `group_qom`.
    """
    landmarks = np.asarray(landmarks, float)
    if landmarks.ndim == 2:
        landmarks = landmarks[:, None, :]
    return group_qom(landmarks, fs, lo=lo, hi=hi, **kwargs)


def body_scale(landmarks, upper=(11, 12), lower=(23, 24)):
    """
    Body-size scale (in the landmarks' own units, e.g. pixels) as the median
    torso length: the distance from the midpoint of the `upper` landmarks
    (shoulders) to the midpoint of the `lower` landmarks (hips). The torso
    length is preferred over shoulder width because it stays robust in a
    profile view, where the shoulder width collapses.

    The default indices are MediaPipe Pose landmarks (11/12 shoulders,
    23/24 hips).

    Source: Westney-comparisons study (Jensenius).

    Args:
        landmarks (np.ndarray): Landmark trajectories of shape (N, L, C) with
            C >= 2; only the first two coordinates are used.
        upper (tuple, optional): Indices of the two shoulder landmarks.
            Defaults to (11, 12).
        lower (tuple, optional): Indices of the two hip landmarks.
            Defaults to (23, 24).

    Returns:
        float: Median torso length (NaN if no finite frames).
    """
    landmarks = np.asarray(landmarks, float)
    um = (landmarks[:, upper[0], :2] + landmarks[:, upper[1], :2]) / 2
    lm = (landmarks[:, lower[0], :2] + landmarks[:, lower[1], :2]) / 2
    d = np.linalg.norm(um - lm, axis=1)
    d = d[np.isfinite(d)]
    return float(np.median(d)) if len(d) else np.nan


def normalized_qom(landmarks, fs, scale=None, lo=0.3, hi=5.0,
                   upper=(11, 12), lower=(23, 24), **kwargs):
    """
    Body-scale-normalised quantity of motion (body-lengths per second):
    the pose QoM divided by the performer's own body scale (median torso
    length, see `body_scale`). Being dimensionless, this is invariant to
    camera framing/zoom and comparable across recordings.

    Source: Westney-comparisons study (Jensenius) -- framing-invariant
    with/without-audience comparison of a pianist's motion.

    Args:
        landmarks (np.ndarray): Landmark trajectories of shape (N, L, 2).
        fs (float): Sampling rate (Hz).
        scale (float, optional): Precomputed body scale. Defaults to None (which
            computes `body_scale(landmarks, upper, lower)`).
        lo (float, optional): Lower band edge (Hz). Defaults to 0.3.
        hi (float, optional): Upper band edge (Hz). Defaults to 5.0.
        upper (tuple, optional): Shoulder landmark indices for `body_scale`. Defaults to (11, 12).
        lower (tuple, optional): Hip landmark indices for `body_scale`. Defaults to (23, 24).
        **kwargs: Passed on to `band_limited_qom`.

    Returns:
        tuple: `(qom, speed, fs_out)` as in `group_qom`, with both `qom` and
            `speed` divided by the body scale. When `scale` is non-finite
            (e.g. `body_scale` found no finite torso-length sample) or not
            strictly positive (degenerate, coincident upper/lower landmarks),
            division would otherwise silently propagate NaN/inf through
            `qom` and `speed`; instead both are explicitly returned as NaN
            (`qom` as a NaN scalar, `speed` as an all-NaN array of the same
            shape) so the invalid-scale case is unambiguous rather than
            merely inferred from the arithmetic.
    """
    landmarks = np.asarray(landmarks, float)
    if scale is None:
        scale = body_scale(landmarks, upper=upper, lower=lower)
    qom, speed, fs_out = pose_qom(landmarks, fs, lo=lo, hi=hi, **kwargs)
    if not np.isfinite(scale) or scale <= 0:
        return float("nan"), np.full_like(speed, np.nan), fs_out
    return qom / scale, speed / scale, fs_out


def grid_qom(frames, grid=(6, 4), region=(0.0, 1.0, 0.0, 1.0), threshold=8.0):
    """
    Spatial grid quantity of motion from a stack of grayscale frames: the
    absolute inter-frame difference is thresholded (small differences set to
    zero to suppress sensor noise) and averaged within each cell of a
    `grid[0]` x `grid[1]` grid laid over `region`, yielding one motion time
    series per cell plus a per-cell mean-motion heatmap.

    Source: Westney-comparisons study (Jensenius) -- audience-region motion
    mapping in a concert hall.

    Args:
        frames (np.ndarray): Grayscale frames of shape (T, H, W).
        grid (tuple, optional): Grid size (columns, rows). Defaults to (6, 4).
        region (tuple, optional): Region of interest as fractions
            (x0, x1, y0, y1) of the frame. Defaults to the full frame.
        threshold (float, optional): Absolute-difference threshold below which
            pixel changes are zeroed (0-255 scale). Defaults to 8.0.

    Returns:
        tuple: `(series, heat)` where `series` has shape (T-1, rows*cols)
            (cells in row-major order) and `heat` has shape (rows, cols) with
            each cell's time-mean motion.

    Raises:
        ValueError: If `frames` is not 3-D (T, H, W), as in
            `_motionanalysis.motiongram_data`.
    """
    frames = np.asarray(frames, dtype=np.float32)
    if frames.ndim != 3:
        raise ValueError("grid_qom expects frames of shape (T, H, W)")
    T, H, W = frames.shape
    gx, gy = grid
    x0, x1, y0, y1 = region
    xs = np.linspace(int(x0 * W), int(x1 * W), gx + 1).astype(int)
    ys = np.linspace(int(y0 * H), int(y1 * H), gy + 1).astype(int)
    d = np.abs(np.diff(frames, axis=0))
    d[d < threshold] = 0.0
    series = np.empty((T - 1, gy * gx), dtype=np.float32)
    for r in range(gy):
        for c in range(gx):
            cell = d[:, ys[r]:ys[r + 1], xs[c]:xs[c + 1]]
            series[:, r * gx + c] = cell.mean(axis=(1, 2))
    heat = series.mean(axis=0).reshape(gy, gx)
    return series, heat

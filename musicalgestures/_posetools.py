"""
Landmark-trajectory pose tools.

This module implements the *array-level* pose workflow used in several of the
fourMs sound--motion studies: video file -> tidy per-landmark trajectory
arrays (and optionally CSV) -> derived motion signals (limb speed, impact
events).

It complements — and does not replace — the rendering-oriented
``MgVideo.pose()`` pipeline in :mod:`musicalgestures._pose` (overlaid skeleton
video, average-pose image, trajectory image, keypoint CSV) and the per-frame
:class:`musicalgestures._pose_estimator.PoseEstimator` interface. Use this
module when you want plain numpy trajectories for downstream signal analysis
(quantity of motion, cross-modal alignment, event detection) rather than
rendered output.

Only :func:`extract_pose_landmarks` needs MediaPipe (an optional dependency,
imported lazily). The derived-signal helpers (:func:`midpoint`,
:func:`limb_speed_from_landmarks`, :func:`impact_events`) are numpy-only and
also work on landmark/point trajectories from any other source (OpenPose,
YOLO-pose, motion capture).

Landmark indices follow the 33-landmark MediaPipe Pose (BlazePose GHUM)
topology used by the mediapipe 0.10.x wheels (e.g. 0 = nose, 11/12 =
left/right shoulder, 13/14 = elbows, 15/16 = wrists); see
:data:`musicalgestures._pose_estimator.MEDIAPIPE_LANDMARK_NAMES` for the full
index -> name mapping.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import os
import subprocess
import threading
import warnings

import numpy as np
from scipy import signal

from musicalgestures._utils import get_widthheight, get_fps

# Landmark names are defined next to the per-frame estimator so both pose
# workflows agree on the index -> name mapping. _pose_estimator imports
# mediapipe lazily, so this import is safe without mediapipe installed.
from musicalgestures._pose_estimator import MEDIAPIPE_LANDMARK_NAMES


def extract_pose_landmarks(
        filename: str,
        fps: float | None = None,
        width: int | None = None,
        t0: float = 0.0,
        duration: float | None = None,
        model_complexity: int = 1,
        world_landmarks: bool = False,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        max_frames: int | None = None,
        target_name: str | None = None,
        quiet: bool = True,
        verbose: bool = True) -> dict:
    """
    Run MediaPipe Pose over a whole video and return tidy per-landmark trajectories.

    The video is decoded through an FFmpeg raw-video pipe (optionally resampled
    to a lower frame rate and resized), each frame is passed to MediaPipe Pose,
    and the 33 landmarks are collected into plain numpy arrays: pixel
    coordinates in the analysis frame plus the per-landmark ``visibility``
    score, with all-NaN rows on frames where no pose was detected, and a
    detection-rate summary. This is the consolidated version of several
    near-identical study extractors; downstream method choices (filtering, QoM,
    alignment) are deliberately *not* baked in here.

    MediaPipe is an optional dependency (``pip install musicalgestures[pose]``)
    and is imported lazily, so importing this module works without it. Both
    mediapipe API families are supported: the legacy Solutions API
    (``mp.solutions.pose.Pose``, wheels up to ~0.10.14) and the Tasks API
    (``PoseLandmarker`` in VIDEO running mode, newer 0.10.x wheels where the
    Solutions API was removed). With the Tasks API the model file is
    auto-downloaded and cached in ``musicalgestures/models/`` on first use
    (shared with ``MgVideo.pose()``).

    Args:
        filename (str): Path to the input video file.
        fps (float, optional): Analysis frame rate. Frames are resampled to this
            rate by FFmpeg before pose estimation (e.g. 12.5 to halve a 25 fps
            video). Defaults to None (native frame rate).
        width (int, optional): Resize the analysis frames to this width in
            pixels, keeping the aspect ratio. Smaller frames are much faster and
            are usually sufficient for trajectory-level analysis (the studies
            used 256-640 px). Defaults to None (native resolution).
        t0 (float, optional): Start time of the analysis window in seconds.
            The window is cut by FFmpeg (input-side seek), so the rest of the
            file is never decoded. Returned timestamps stay on the source
            clock, i.e. ``time[0] == t0``. Defaults to 0.0 (start of file).
        duration (float, optional): Length of the analysis window in seconds
            (from ``t0``). Defaults to None (until the end of the file).
        model_complexity (int, optional): MediaPipe model variant: 0 (lite),
            1 (full) or 2 (heavy). Defaults to 1.
        world_landmarks (bool, optional): Whether to also collect MediaPipe's 3D
            world landmarks (metres, hip-centred). Defaults to False.
        min_detection_confidence (float, optional): MediaPipe person-detection
            confidence threshold (also used as the presence threshold with the
            Tasks API). Defaults to 0.5.
        min_tracking_confidence (float, optional): MediaPipe landmark-tracking
            confidence threshold. Defaults to 0.5.
        max_frames (int, optional): Stop after this many analysed frames (handy
            for quick tests). Defaults to None (whole video).
        target_name (str, optional): If given, also write the trajectories to
            this path as a tidy CSV with columns ``time`` and, per landmark
            name, ``<name>_x``, ``<name>_y``, ``<name>_v`` (and ``<name>_wx``,
            ``<name>_wy``, ``<name>_wz`` when ``world_landmarks=True``).
            Defaults to None (no file written).
        quiet (bool, optional): Suppress MediaPipe's native C++/GL console logs
            during inference. Defaults to True.
        verbose (bool, optional): Print a one-line detection-rate summary per
            video. Defaults to True.

    Returns:
        dict: A dictionary with keys:

            - ``time`` (np.ndarray, shape (F,)): Frame timestamps in seconds.
            - ``landmarks`` (np.ndarray, shape (F, 33, 3)): Per frame and
              landmark ``(x_px, y_px, visibility)`` in analysis-frame pixels;
              all-NaN rows where no pose was detected.
            - ``world`` (np.ndarray, shape (F, 33, 3) or None): 3D world
              landmarks ``(x, y, z)`` in metres (hip-centred) when
              ``world_landmarks=True``, else None.
            - ``detected`` (np.ndarray of bool, shape (F,)): Per-frame
              detection flags.
            - ``detection_rate`` (float): Fraction of frames with a detected
              pose.
            - ``fps`` (float): Analysis frame rate of the returned arrays.
            - ``width``, ``height`` (int): Analysis frame size in pixels.
            - ``names`` (list of str): The 33 landmark names (row order of the
              landmark axis).

    Source:
        Consolidated from the author's study extractors: stillstanding
        (mp_extract_westney.py, pose_motion.py) and Westney-comparisons
        (concert_mediapipe.py, reh_pose.py, a1_labstage.py) (Jensenius).
    """
    if model_complexity not in (0, 1, 2):
        raise ValueError(
            f"model_complexity must be 0, 1 or 2, got {model_complexity!r}")
    if t0 < 0:
        raise ValueError(f"t0 must be >= 0, got {t0!r}")
    if duration is not None and duration <= 0:
        raise ValueError(f"duration must be > 0, got {duration!r}")

    try:
        import mediapipe as mp
    except ImportError as exc:
        raise ImportError(
            "MediaPipe is required for extract_pose_landmarks() but is not installed. "
            "Install the optional pose dependencies with: pip install musicalgestures[pose]"
        ) from exc

    # fd-level stderr silencer shared with MgVideo.pose() (MediaPipe's C++/GL
    # logs bypass Python logging).
    from musicalgestures._pose import _suppress_native_stderr

    n_landmarks = len(MEDIAPIPE_LANDMARK_NAMES)

    # --- probe the source and build the FFmpeg decode pipe -------------------
    w0, h0 = get_widthheight(filename)
    native_fps = get_fps(filename)
    sample_fps = float(fps) if fps else float(native_fps)
    if width:
        w = int(width)
        h = int(round(h0 * w / w0))
    else:
        w, h = int(w0), int(h0)

    vf = []
    if fps:
        vf.append(f"fps={sample_fps}")
    if width:
        vf.append(f"scale={w}:{h}")
    cmd = ["ffmpeg", "-v", "error"]
    if t0:
        # Input-side seek (-ss before -i): FFmpeg jumps to the nearest
        # keyframe before t0 and decodes from there, so windowing a long
        # file never decodes the whole file.
        cmd += ["-ss", str(t0)]
    cmd += ["-i", filename]
    if duration is not None:
        cmd += ["-t", str(duration)]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-pix_fmt", "rgb24", "-f", "rawvideo", "-"]

    # --- backend: legacy Solutions API or Tasks API ---------------------------
    # The study scripts were written against the legacy Solutions API
    # (mediapipe 0.10.14); newer 0.10.x wheels (e.g. 0.10.35, as used in the
    # cymbal study) removed it in favour of the Tasks API. Support both.
    #
    # `use_solutions` prefers the Solutions API whenever it is present: this
    # is purely for fidelity to the original study pipeline (the papers'
    # numbers were produced with Solutions, not Tasks), not because Solutions
    # is otherwise preferable.
    #
    # IMPORTANT: the Solutions branch below (`if use_solutions:`) is a
    # faithful port of the study scripts' mediapipe<=0.10.14 Solutions code,
    # but it is UNTESTABLE on modern wheels — mediapipe>=0.10.26 removed
    # `mp.solutions` entirely, so no environment this project can currently
    # install exercises this branch (it is only reachable with an old, pinned
    # mediapipe wheel). Keep it faithful to the source scripts rather than
    # "improving" it blind.
    # TODO: once the legacy Solutions-API mediapipe family (<=0.10.14) is
    # fully retired (no supported environment can install it any more), drop
    # this preference and the Solutions branch, and always use the Tasks API.
    use_solutions = hasattr(mp, "solutions")

    def _read_result(lms, wlms):
        """Convert one frame's MediaPipe landmark lists to (33, 3) arrays."""
        a = np.array([[l.x * w, l.y * h, l.visibility] for l in lms], dtype=np.float64)
        if world_landmarks:
            b = (np.array([[l.x, l.y, l.z] for l in wlms], dtype=np.float64)
                 if wlms is not None else np.full((n_landmarks, 3), np.nan))
        else:
            b = None
        return a, b

    times, lm2d, lm3d, detected = [], [], [], []
    frame_bytes = w * h * 3
    stopped_early = False
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # stdout=PIPE guarantees a stream; the annotation is Optional for the general case
    assert proc.stdout is not None, "ffmpeg was started without a readable output stream"
    assert proc.stderr is not None, "ffmpeg was started without a readable error stream"
    # Drain FFmpeg's stderr on a background thread as it is produced, rather
    # than only reading it in the `finally` block below: the stdout-reading
    # loop can run far longer than the OS pipe buffer takes to fill (a few
    # dozen KB), and if FFmpeg blocks on a full stderr pipe while we are only
    # consuming stdout, decoding stalls. The drained chunks are joined at the
    # end to preserve the existing error-reporting behaviour.
    stderr_chunks: list[bytes] = []

    def _drain_stderr():
        for chunk in iter(lambda: proc.stderr.read(4096), b""):
            stderr_chunks.append(chunk)

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()
    try:
        with _suppress_native_stderr(quiet):
            if use_solutions:
                pose_ctx = mp.solutions.pose.Pose(
                    static_image_mode=False,
                    model_complexity=model_complexity,
                    min_detection_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence)
                close_backend = pose_ctx.close

                def _process(frame_rgb, t):
                    res = pose_ctx.process(frame_rgb)
                    if res.pose_landmarks:
                        return _read_result(
                            res.pose_landmarks.landmark,
                            res.pose_world_landmarks.landmark
                            if getattr(res, "pose_world_landmarks", None) else None)
                    return None, None
            else:
                # Tasks API: reuse the shared model download/cache so both
                # pose workflows use one model file in musicalgestures/models/.
                from musicalgestures._pose_estimator import get_pose_model_path
                model_path = get_pose_model_path(model_complexity)
                BaseOptions = mp.tasks.BaseOptions
                options = mp.tasks.vision.PoseLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=str(model_path)),
                    running_mode=mp.tasks.vision.RunningMode.VIDEO,
                    min_pose_detection_confidence=min_detection_confidence,
                    min_pose_presence_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence)
                landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)
                close_backend = landmarker.close

                def _process(frame_rgb, t):
                    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                    res = landmarker.detect_for_video(img, int(round(t * 1000)))
                    if res.pose_landmarks:
                        return _read_result(
                            res.pose_landmarks[0],
                            res.pose_world_landmarks[0]
                            if res.pose_world_landmarks else None)
                    return None, None

            try:
                fi = 0
                while True:
                    if max_frames is not None and fi >= max_frames:
                        stopped_early = True
                        proc.terminate()
                        break
                    buf = proc.stdout.read(frame_bytes)
                    if buf is None or len(buf) < frame_bytes:
                        break
                    frame = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
                    # Timestamps on the source clock: with a t0 window the
                    # first analysed frame is at (approximately) t0.
                    t = t0 + fi / sample_fps
                    a, b = _process(frame, t)
                    if a is None:
                        a = np.full((n_landmarks, 3), np.nan)
                        b = np.full((n_landmarks, 3), np.nan) if world_landmarks else None
                        detected.append(False)
                    else:
                        detected.append(True)
                    times.append(t)
                    lm2d.append(a)
                    if world_landmarks:
                        lm3d.append(b)
                    fi += 1
            finally:
                close_backend()
    finally:
        proc.stdout.close()
        proc.wait()
        stderr_thread.join()
        proc.stderr.close()
        err = b"".join(stderr_chunks).decode(errors="replace").strip()
        # Stopping at max_frames breaks FFmpeg's output pipe on purpose, so
        # suppress its resulting broken-pipe complaints.
        if err and not stopped_early:
            print(f"FFmpeg warnings while decoding {filename}:\n{err}")

    n_frames = len(times)
    result = {
        "time": np.asarray(times, dtype=np.float64),
        "landmarks": (np.asarray(lm2d, dtype=np.float64)
                      if n_frames else np.empty((0, n_landmarks, 3))),
        "world": ((np.asarray(lm3d, dtype=np.float64)
                   if n_frames else np.empty((0, n_landmarks, 3)))
                  if world_landmarks else None),
        "detected": np.asarray(detected, dtype=bool),
        "detection_rate": float(np.mean(detected)) if n_frames else 0.0,
        "fps": sample_fps,
        "width": w,
        "height": h,
        "names": list(MEDIAPIPE_LANDMARK_NAMES),
    }

    if verbose:
        print(f"{os.path.basename(filename)}: {n_frames} frames at "
              f"{sample_fps:g} fps ({w}x{h}), pose detected in "
              f"{100.0 * result['detection_rate']:.0f}% of frames.")

    if target_name is not None:
        _write_landmarks_csv(target_name, result)

    return result


def _write_landmarks_csv(path: str, result: dict) -> None:
    """Write an extract_pose_landmarks() result dict as a tidy CSV file."""
    names = result["names"]
    cols = [result["time"][:, None]]
    header = ["time"]
    lm = result["landmarks"]
    for j, name in enumerate(names):
        cols.append(lm[:, j, :])
        header += [f"{name}_x", f"{name}_y", f"{name}_v"]
    if result["world"] is not None:
        wl = result["world"]
        for j, name in enumerate(names):
            cols.append(wl[:, j, :])
            header += [f"{name}_wx", f"{name}_wy", f"{name}_wz"]
    data = np.hstack(cols) if len(result["time"]) else np.empty((0, len(header)))
    np.savetxt(path, data, delimiter=",", header=",".join(header), comments="")


def midpoint(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Element-wise midpoint of two landmark trajectories.

    Typical use is the shoulder midpoint (MediaPipe landmarks 11 and 12) as an
    upper-torso proxy point, e.g. ``midpoint(lm[:, 11, :2], lm[:, 12, :2])``.
    NaNs (detection dropouts) propagate: the midpoint is NaN wherever either
    input is NaN.

    Args:
        a (np.ndarray): First trajectory, any shape (e.g. (F, 2)).
        b (np.ndarray): Second trajectory, broadcast-compatible with ``a``.

    Returns:
        np.ndarray: ``(a + b) / 2``.

    Source:
        Stillstanding study, pose_motion.py (shoulder-midpoint torso
        micromotion) (Jensenius).
    """
    return (np.asarray(a, dtype=np.float64) + np.asarray(b, dtype=np.float64)) / 2.0


def limb_speed_from_landmarks(
        xy: np.ndarray,
        confidence: np.ndarray | None,
        fps: float,
        conf_gate: float = 0.5,
        merge: str | None = "max_lr",
        smooth_taps: int = 3) -> np.ndarray:
    """
    Confidence-gated image-plane speed of one or more candidate limbs.

    For each candidate limb (e.g. the left and right wrist), frames whose
    landmark confidence/visibility falls below ``conf_gate`` are masked out
    (NaN), and the limb speed is formed as the central-difference magnitude of
    the pixel path (px/s). Candidate limbs are then merged by element-wise
    maximum — so that motion of *either* limb registers, mirroring the
    bilateral merge used for inertial hand data — and lightly smoothed with a
    short NaN-aware moving average. Peaks of the resulting signal mark, e.g.,
    strike downstrokes of the striking wrist.

    Caveats (from the cymbal study): these are 2D apparent kinematics from a
    single camera — motion toward/away from the lens is foreshortened and pixel
    speed is not metric speed. Moreover, a limb-speed peak marks *maximum
    downstroke speed*, which systematically precedes the contact/arrest that an
    audio onset or an acceleration peak registers; account for this bias when
    comparing event times across modalities.

    Peak-picking on the returned signal is left to the caller (a general
    adaptive peak-picker, ``pick_peaks``, is provided by the sibling
    core-signal-methods PR in ``musicalgestures._peaks``; the cymbal study used
    a relative threshold of 0.4 x the take's peak with a 0.2 s minimum
    interval).

    Args:
        xy (np.ndarray): Pixel positions, shape (F, L, 2) for L candidate limbs
            or (F, 2) for a single limb.
        confidence (np.ndarray, optional): Per-frame landmark confidence
            (MediaPipe ``visibility``), shape (F, L) or (F,). Pass None to skip
            confidence gating.
        fps (float): Frame rate of the trajectory (Hz).
        conf_gate (float, optional): Frames with confidence below this value
            are masked (NaN) before differentiation. Defaults to 0.5.
        merge (str, optional): ``"max_lr"`` (or ``"max"``) merges the candidate
            limbs by element-wise (NaN-aware) maximum; None returns per-limb
            speeds. Defaults to "max_lr".
        smooth_taps (int, optional): Length of the NaN-aware moving-average
            smoother applied after merging. Use 0 or 1 to disable. Defaults
            to 3. With ``smooth_taps > 1``, samples right at the edge of a
            confidence-gated (NaN) region can be partially reconstructed:
            the NaN-aware average only requires *some* finite values inside
            its window, so an edge sample whose window straddles both valid
            and gated frames is averaged from the valid ones rather than
            staying NaN.

    Returns:
        np.ndarray: Speed in px/s: shape (F,) when merged, else (F, L). NaN
            where the position (or a central-difference neighbour) is masked
            or missing.

    Source:
        Cymbal-comparison study, markerless striking-wrist speed
        (reimplemented from the paper's method description; defaults are the
        paper's provisional values) (Jensenius).
    """
    xy = np.asarray(xy, dtype=np.float64)
    single = xy.ndim == 2
    if single:
        xy = xy[:, None, :]
    if xy.ndim != 3 or xy.shape[-1] != 2:
        raise ValueError(f"xy must have shape (F, L, 2) or (F, 2), got {xy.shape}")
    xy = xy.copy()

    if confidence is not None:
        conf = np.asarray(confidence, dtype=np.float64)
        if conf.ndim == 1:
            conf = conf[:, None]
        if conf.shape != xy.shape[:2]:
            raise ValueError(
                f"confidence shape {conf.shape} does not match xy frames/limbs {xy.shape[:2]}")
        with np.errstate(invalid="ignore"):
            xy[~(conf >= conf_gate)] = np.nan

    if len(xy) < 2:
        speed = np.full(xy.shape[:2], np.nan)
    else:
        # Central differences (one-sided at the ends); NaN wherever a needed
        # neighbour is masked/missing.
        d = np.gradient(xy, axis=0)
        speed = np.hypot(d[..., 0], d[..., 1]) * float(fps)

    if merge is not None:
        if merge not in ("max_lr", "max"):
            raise ValueError(f"merge must be 'max_lr', 'max' or None, got {merge!r}")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)  # all-NaN frames
            speed = np.nanmax(speed, axis=1)
    elif single:
        speed = speed[:, 0]

    if smooth_taps and smooth_taps > 1:
        speed = _nan_moving_average(speed, int(smooth_taps))
    return speed


def impact_events(
        pos_by_point: np.ndarray,
        fps: float,
        rel_thresh: float = 0.12,
        min_interval_s: float = 0.10) -> dict:
    """
    Detect candidate impact events from point trajectories via acceleration peaks.

    Each candidate point's position (2D or 3D; e.g. the two hand points of a
    mocap model, or the two wrist landmarks) is differentiated twice with
    central differences to obtain its acceleration vector, the vector magnitude
    is taken, and the points are merged by element-wise maximum so that a
    strike by *either* hand registers (bilateral max). Impacts are then
    peak-picked on the merged acceleration magnitude with a relative threshold
    of ``rel_thresh`` x the signal's maximum and a minimum inter-impact
    interval of ``min_interval_s``.

    The threshold parameters are taken directly (the small relative-threshold
    peak picker is implemented inline here); a general adaptive peak-picker,
    ``pick_peaks``, is provided by the sibling core-signal-methods PR in
    ``musicalgestures._peaks``. The defaults (0.12 x peak, 100 ms) are
    validated against the original cymbal dataset (Zenodo 21360429, 2026
    revalidation) for 120 Hz mocap hand data and should be tuned per dataset.
    Note the study's caveat: double-differentiating (model-reconstructed)
    positions is noisy and also responds to the backswing, not only the
    collision — treat the detected peaks as *candidate* impacts and validate
    against another modality (e.g. audio onsets) where possible. For
    whole-image visual impact detection from video (no landmarks), see
    ``MgVideo.impacts()`` instead.

    Args:
        pos_by_point (np.ndarray): Point positions, shape (F, P, D) for P
            candidate points in D spatial dimensions (2 or 3), or (F, D) for a
            single point. Units are the caller's (m or px); NaNs (dropouts)
            propagate into the acceleration and are never picked as peaks.
        fps (float): Sampling rate of the trajectories (Hz).
        rel_thresh (float, optional): Relative peak threshold as a fraction of
            the merged acceleration magnitude's maximum. Defaults to 0.12.
        min_interval_s (float, optional): Minimum interval between detected
            impacts in seconds (stronger peaks win). Defaults to 0.10.

    Returns:
        dict: A dictionary with keys:

            - ``index`` (np.ndarray of int): Sample indices of the detected
              impacts, ascending.
            - ``time`` (np.ndarray): Impact times in seconds (``index / fps``).
            - ``magnitude`` (np.ndarray): Merged acceleration magnitude at each
              impact (position-units/s^2).
            - ``accel`` (np.ndarray, shape (F,)): The full merged acceleration-
              magnitude signal (for plotting/inspection).

    Source:
        Cymbal-comparison study, kinematic impact detection from Xsens hand
        points (reimplemented from the paper's method description; defaults
        are the paper's provisional values) (Jensenius).
    """
    pos = np.asarray(pos_by_point, dtype=np.float64)
    if pos.ndim == 2:
        pos = pos[:, None, :]
    if pos.ndim != 3:
        raise ValueError(
            f"pos_by_point must have shape (F, P, D) or (F, D), got {pos.shape}")

    n = len(pos)
    if n < 3:
        accel = np.full(n, np.nan)
    else:
        vel = np.gradient(pos, axis=0) * float(fps)
        acc = np.gradient(vel, axis=0) * float(fps)
        mag = np.linalg.norm(acc, axis=2)          # (F, P)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)  # all-NaN frames
            accel = np.nanmax(mag, axis=1)         # bilateral max across points

    min_dist = max(1, int(round(min_interval_s * float(fps))))
    idx = _pick_relative_peaks(accel, rel_thresh, min_dist)
    return {
        "index": idx,
        "time": idx / float(fps),
        "magnitude": accel[idx] if len(idx) else np.array([], dtype=np.float64),
        "accel": accel,
    }


def _nan_moving_average(x: np.ndarray, taps: int) -> np.ndarray:
    """NaN-aware centred moving average along the first axis.

    Averages the finite values inside each window; a sample is NaN only when
    its whole window is NaN. ``taps`` should be odd (an even value is widened
    by one to stay centred).
    """
    x = np.asarray(x, dtype=np.float64)
    if taps % 2 == 0:
        taps += 1
    half = taps // 2
    stack = np.full((taps,) + x.shape, np.nan)
    for k in range(-half, half + 1):
        src = slice(max(0, -k), x.shape[0] - max(0, k))
        dst = slice(max(0, k), x.shape[0] - max(0, -k))
        stack[k + half][dst] = x[src]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)  # all-NaN windows
        return np.nanmean(stack, axis=0)


def _pick_relative_peaks(signal: np.ndarray, rel_thresh: float, min_dist: int) -> np.ndarray:
    """Pick local maxima above ``rel_thresh`` x max, at least ``min_dist`` samples apart.

    Minimal inline relative-threshold picker (stronger peaks win ties within
    ``min_dist``); NaN samples are never candidates. Kept private — the
    general, feature-complete picker lives in ``musicalgestures._peaks``
    (sibling PR).
    """
    s = np.asarray(signal, dtype=np.float64)
    if len(s) < 3 or not np.isfinite(s).any():
        return np.array([], dtype=np.intp)
    peak = np.nanmax(s)
    if not peak > 0:
        return np.array([], dtype=np.intp)
    thr = rel_thresh * peak
    interior = np.arange(1, len(s) - 1)
    mid, prev, nxt = s[1:-1], s[:-2], s[2:]
    cand = interior[(mid >= thr) & (mid > prev) & (mid >= nxt)]
    if len(cand) == 0:
        return cand.astype(np.intp)
    kept: list[int] = []
    for i in cand[np.argsort(s[cand], kind="stable")[::-1]]:
        if all(abs(int(i) - j) >= min_dist for j in kept):
            kept.append(int(i))
    return np.array(sorted(kept), dtype=np.intp)


def _unpack_views(views) -> tuple[list, list[np.ndarray], list[np.ndarray]]:
    """Normalise the accepted view forms into names, world arrays, visibilities.

    A view is either an :func:`extract_pose_landmarks` result dict (its
    ``world`` array, with visibility read from ``landmarks[..., 2]``) or a
    plain ``(world, visibility)`` pair.
    """
    if isinstance(views, dict):
        items = list(views.items())
    else:
        items = list(enumerate(views))
    if len(items) < 2:
        raise ValueError(
            "fuse_pose_views needs at least two views; got "
            f"{len(items)}. Fusing one view has nothing to fuse it with.")

    names: list = []
    worlds: list[np.ndarray] = []
    vis: list[np.ndarray] = []
    for name, view in items:
        names.append(name)
        if isinstance(view, dict):
            world = view.get("world")
            if world is None:
                raise ValueError(
                    f"view {name!r} has no 'world' array. Call "
                    "extract_pose_landmarks(..., world_landmarks=True): the "
                    "fusion is defined on metric 3D landmarks, not pixels.")
            world = np.asarray(world, dtype=float)
            lm = view.get("landmarks")
            v = (np.asarray(lm, dtype=float)[..., 2] if lm is not None
                 else np.ones(world.shape[:2]))
        else:
            world, v = view
            world = np.asarray(world, dtype=float)
            v = np.asarray(v, dtype=float)
        if world.ndim != 3 or world.shape[-1] != 3:
            raise ValueError(
                f"view {name!r} world array has shape {world.shape}; "
                "expected (frames, landmarks, 3).")
        worlds.append(world)
        vis.append(v)

    widths = {w.shape[1] for w in worlds}
    if len(widths) != 1:
        raise ValueError(
            f"views disagree on the number of landmarks: {sorted(widths)}. "
            "All views must come from the same landmark topology.")
    return names, worlds, vis


def _interp_nan(a: np.ndarray, max_gap: int | None = None) -> np.ndarray:
    """Fill NaN gaps per coordinate by linear interpolation.

    With ``max_gap=None`` every gap is filled, of any length, and the ends are
    held flat -- which is what the study scripts this came from did. Pass an
    integer to leave longer dropouts as NaN, so a repair cannot pass for a
    measurement.
    """
    frames = a.shape[0]
    idx = np.arange(frames)
    for j in range(a.shape[1]):
        for c in range(3):
            x = a[:, j, c]
            m = np.isfinite(x)
            if m.sum() < 2:
                continue
            filled = np.interp(idx, np.flatnonzero(m), x[m])
            if max_gap is not None:
                filled = np.where(_gap_lengths(m) > max_gap, np.nan, filled)
            a[:, j, c] = filled
    return a


def _gap_lengths(mask: np.ndarray) -> np.ndarray:
    """Length of the NaN run each sample belongs to; 0 where the sample is finite."""
    out = np.zeros(mask.shape, dtype=int)
    start = None
    for i, ok in enumerate(mask):
        if not ok and start is None:
            start = i
        elif ok and start is not None:
            out[start:i] = i - start
            start = None
    if start is not None:
        out[start:] = len(mask) - start
    return out


def _umeyama(src: np.ndarray, dst: np.ndarray) -> tuple[np.ndarray, float]:
    """Similarity transform (rotation, scale) taking ``src`` onto ``dst``.

    Both arrays are (N, 3). Translation is deliberately not returned: the
    caller re-centres on the torso centroid instead, which is more stable
    than a fitted offset when a view drops landmarks.
    """
    mu_s = src.mean(0)
    mu_d = dst.mean(0)
    S = src - mu_s
    D = dst - mu_d
    C = D.T @ S / len(src)
    U, d, Vt = np.linalg.svd(C)
    # Kabsch sign correction: without it a degenerate fit can return a
    # reflection, which mirrors the skeleton rather than rotating it.
    flip = np.array([1.0, 1.0, np.sign(np.linalg.det(U @ Vt))])
    R = U @ np.diag(flip) @ Vt
    var = (S ** 2).sum() / len(src)
    scale = float((d * flip).sum() / (var + 1e-12))
    return R, scale


def _mean_rotation(rotations: list[np.ndarray]) -> np.ndarray:
    """Project the arithmetic mean of rotation matrices back onto SO(3)."""
    U, _, Vt = np.linalg.svd(np.mean(rotations, axis=0))
    R = U @ Vt
    if np.linalg.det(R) < 0:
        # The mean fell closer to a reflection than to a rotation. Flipping
        # the least-significant singular direction is the nearest true
        # rotation to it; without this the fused skeleton comes out mirrored.
        U[:, -1] *= -1
        R = U @ Vt
    return R


def fuse_pose_views(
        views: Sequence | Mapping,
        reference: int | str = 0,
        torso: Sequence[int] = (11, 12, 23, 24),
        smooth: tuple[int, int] | None = (7, 2),
        max_gap: int | None = None) -> dict:
    """
    Fuse MediaPipe *world* landmarks from two or more uncalibrated camera views.

    This is **not** calibrated triangulation: there is no camera calibration and
    no motion-capture ground truth. Each view gives a monocular metric 3D pose
    in its own gravity-aligned, hip-centred frame. The views are brought into a
    common frame by a single Umeyama (rotation + scale) similarity estimated
    from the rigid torso landmarks, then fused per landmark by a
    visibility-weighted average. The result is a consensus skeleton more robust
    than any single monocular view, plus a cross-view residual in millimetres as
    a quality measure.

    One transform is estimated per view for the whole take, not one per frame:
    the per-frame fits are averaged (rotation through the nearest rotation to
    their arithmetic mean, scale through the median), which is what makes the
    alignment a property of the camera placement rather than of the pose. The
    translation term of each fit is deliberately discarded -- views are
    re-centred on the torso centroid instead, which stays stable when a view
    drops landmarks.

    The residual is a *consistency* measure, not an accuracy one. Views that
    agree closely can still agree on a wrong pose, so a low residual says the
    cameras saw the same thing, not that the thing was right.

    Args:
        views: Two or more views of the same take, either a sequence or a
            mapping of name -> view. Each view is one of:

            - a result dict from :func:`extract_pose_landmarks` called with
              ``world_landmarks=True``, whose visibility is read from its
              ``landmarks[..., 2]`` column;
            - a plain ``(world, visibility)`` pair of arrays, shaped
              ``(F, L, 3)`` and ``(F, L)``, from any other source.

            Views may differ in length; the shortest one sets the number of
            fused frames. They must agree on the number of landmarks.
        reference (int or str, optional): Which view defines the common frame,
            by key when ``views`` is a mapping and by position otherwise. The
            fused skeleton comes out in this view's frame and at its scale.
            Defaults to 0 (the first view).
        torso (sequence of int, optional): Landmark indices used to estimate
            the alignment. Defaults to (11, 12, 23, 24) -- MediaPipe's
            shoulders and hips, the most rigid and best-detected group.
        smooth (tuple, optional): ``(window, polyorder)`` for a Savitzky-Golay
            filter applied along time after fusion, or None for no smoothing.
            Skipped when the take is shorter than the window. Note that
            smoothing spreads any NaN across its window. Defaults to (7, 2).
        max_gap (int, optional): Longest run of missing frames that may be
            filled by interpolation before alignment. Longer dropouts are left
            as NaN, so a repair cannot pass for a measurement. Defaults to None,
            which fills every gap of any length and holds the ends flat -- the
            behaviour of the study scripts this is consolidated from, kept as
            the default so their results reproduce.

    Returns:
        dict: A dictionary with keys:

            - ``fused`` (np.ndarray, shape (F, L, 3)): The consensus skeleton in
              the reference view's frame, in metres.
            - ``residual_mm`` (float): Mean distance between each aligned view
              and the fused skeleton, in millimetres.
            - ``residual_per_landmark_mm`` (np.ndarray, shape (L,)): The same
              measure per landmark, which is where a badly-placed camera shows.
            - ``rotations`` (dict): Per view, the (3, 3) rotation onto the
              reference frame. The reference view's own is the identity.
            - ``scales`` (dict): Per view, the scalar scale onto the reference
              frame.
            - ``names`` (list): The view names, in the order given.
            - ``n_frames`` (int): Number of fused frames, i.e. the length of
              the shortest view.

    Raises:
        ValueError: If fewer than two views are given, if a view dict has no
            ``world`` array, if a world array is not shaped (F, L, 3), or if
            the views disagree on the number of landmarks.

    Examples:
        >>> side = mg.extract_pose_landmarks("side.mp4", world_landmarks=True)
        >>> above = mg.extract_pose_landmarks("above.mp4", world_landmarks=True)
        >>> fused = mg.fuse_pose_views({"side": side, "above": above},
        ...                            reference="side")
        >>> fused["residual_mm"]

    Source:
        Consolidated from the author's Westney-comparisons study scripts
        concert_fuse3d.py and reh_fuse3d.py, which were byte-identical but for
        a hardcoded list of pieces (Jensenius). Reproduces their published
        fusion on all four concert excerpts to within float32 storage precision.
    """
    names, worlds, vis = _unpack_views(views)
    n = min(w.shape[0] for w in worlds)
    worlds = [_interp_nan(w[:n].copy(), max_gap) for w in worlds]
    vis = [np.clip(v[:n], 0.0, 1.0) for v in vis]

    ref_index = names.index(reference) if reference in names else int(reference)
    ref = worlds[ref_index]
    torso = list(torso)

    aligned: list[np.ndarray] = []
    rotations: dict = {}
    scales: dict = {}
    for i, world in enumerate(worlds):
        if i == ref_index:
            aligned.append(world)
            rotations[names[i]] = np.eye(3)
            scales[names[i]] = 1.0
            continue
        per_frame_R = []
        per_frame_s = []
        for f in range(n):
            s_pts = world[f, torso]
            d_pts = ref[f, torso]
            if np.all(np.isfinite(s_pts)) and np.all(np.isfinite(d_pts)):
                R_f, s_f = _umeyama(s_pts, d_pts)
                per_frame_R.append(R_f)
                per_frame_s.append(s_f)
        if not per_frame_R:
            aligned.append(world)
            rotations[names[i]] = np.eye(3)
            scales[names[i]] = 1.0
            continue
        R = _mean_rotation(per_frame_R)
        scale = float(np.median(per_frame_s))
        al = scale * np.einsum("ij,fkj->fki", R, world)
        al = al - np.nanmean(al[:, torso], axis=1, keepdims=True) \
            + np.nanmean(ref[:, torso], axis=1, keepdims=True)
        aligned.append(al)
        rotations[names[i]] = R
        scales[names[i]] = scale

    num = np.zeros((n, worlds[0].shape[1], 3))
    den = np.zeros((n, worlds[0].shape[1], 1))
    for a, v in zip(aligned, vis):
        w = v[:, :, None]
        good = np.isfinite(a).all(-1, keepdims=True)
        num += np.where(good, a * w, 0.0)
        den += np.where(good, w, 0.0)
    fused = num / np.clip(den, 1e-6, None)
    fused = np.where(den > 0, fused, np.nan)

    if smooth is not None:
        window, order = smooth
        if n >= window:
            fused = signal.savgol_filter(fused, window, order, axis=0)

    per_landmark = np.nanmean(
        [np.linalg.norm(a - fused, axis=-1) for a in aligned], axis=(0, 1)) * 1000.0

    return {
        "fused": fused,
        "residual_mm": float(np.nanmean(per_landmark)),
        "residual_per_landmark_mm": per_landmark,
        "rotations": rotations,
        "scales": scales,
        "names": names,
        "n_frames": n,
    }

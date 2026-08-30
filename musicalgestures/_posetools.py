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

#: The 17-point COCO keypoint topology every YOLO pose model emits, in model
#: order. Shared here so downstream detector-agreement workflows agree on the
#: index -> name mapping, as MEDIAPIPE_LANDMARK_NAMES does for the 33-point set.
COCO_KEYPOINT_NAMES = (
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle")


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


def extract_pose_tracks_yolo(
        filename: str,
        fps: float | None = None,
        width: int | None = None,
        t0: float = 0.0,
        duration: float | None = None,
        model: str = "yolo11s-pose.pt",
        conf: float = 0.25,
        max_frames: int | None = None,
        tracker: str = "bytetrack.yaml",
        verbose: bool = True) -> dict:
    """Every person's trajectory separately, with identities held across frames.

    The single-person extractors follow the highest-confidence detection per
    frame, and with two bodies in frame that selection flips between them ---
    measured on a dance corpus, where it teleported the trajectory between two
    real dancers, and between a dancer and their life-size projected partner on a
    screen. This runs the same YOLO pose models through Ultralytics' tracker, so
    each body keeps an identity, and returns one trajectory per identity.

    Args:
        filename (str): Path to the input video file.
        fps (float, optional): Analysis frame rate. Defaults to None (native).
        width (int, optional): Analysis width in pixels. Defaults to None.
        t0 (float, optional): Start of the analysis window in seconds.
        duration (float, optional): Length of the window in seconds.
        model (str, optional): An Ultralytics pose model. Defaults to
            "yolo11s-pose.pt".
        conf (float, optional): Detection confidence threshold. Defaults to 0.25.
        max_frames (int, optional): Stop after this many analysed frames.
        tracker (str, optional): Ultralytics tracker configuration. Defaults to
            "bytetrack.yaml".
        verbose (bool, optional): Print a one-line summary. Defaults to True.

    Returns:
        dict: ``tracks`` (identity -> dict with ``time``, ``frame`` and
        ``landmarks`` of shape (n, 17, 3), confidence in the third channel and
        zero-confidence keypoints as NaN), plus ``n_frames``, ``fps``,
        ``width``, ``height`` and ``names``.
    """
    if t0 < 0:
        raise ValueError(f"t0 must be >= 0, got {t0!r}")
    if duration is not None and duration <= 0:
        raise ValueError(f"duration must be > 0, got {duration!r}")

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise ImportError(
            "Ultralytics is required for extract_pose_tracks_yolo() but is not "
            "installed. Install the optional dependencies with: "
            "pip install musicalgestures[yolo]") from exc

    from pathlib import Path

    model_path = Path(model)
    if not model_path.exists() and model_path.name == str(model):
        from ultralytics.utils.downloads import attempt_download_asset
        models_dir = Path(__file__).parent / "models"
        models_dir.mkdir(exist_ok=True)
        model_path = Path(attempt_download_asset(str(models_dir / model)))
    yolo = YOLO(str(model_path))

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
        cmd += ["-ss", str(t0)]
    cmd += ["-i", filename]
    if duration is not None:
        cmd += ["-t", str(duration)]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-pix_fmt", "rgb24", "-f", "rawvideo", "-"]

    tracks: dict = {}
    frame_bytes = w * h * 3
    stopped_early = False
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None and proc.stderr is not None
    stderr_chunks: list[bytes] = []

    def _drain_stderr():
        for chunk in iter(lambda: proc.stderr.read(4096), b""):
            stderr_chunks.append(chunk)

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()
    fi = 0
    try:
        while True:
            if max_frames is not None and fi >= max_frames:
                stopped_early = True
                proc.terminate()
                break
            buf = proc.stdout.read(frame_bytes)
            if buf is None or len(buf) < frame_bytes:
                break
            frame = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
            t = t0 + fi / sample_fps
            res = yolo.track(frame, persist=True, conf=conf, tracker=tracker,
                             verbose=False)[0]
            kp = res.keypoints
            ids = (res.boxes.id if res.boxes is not None else None)
            if (kp is not None and kp.xy is not None and kp.conf is not None
                    and ids is not None):
                for person, tid in enumerate(ids.int().tolist()):
                    xy = kp.xy[person].cpu().numpy().astype(np.float64)
                    c = kp.conf[person].cpu().numpy().astype(np.float64)
                    xy[c <= 0.0] = np.nan
                    tr = tracks.setdefault(int(tid),
                                           {"time": [], "frame": [],
                                            "landmarks": []})
                    tr["time"].append(t)
                    tr["frame"].append(fi)
                    tr["landmarks"].append(np.column_stack([xy, c]))
            fi += 1
    finally:
        proc.stdout.close()
        proc.wait()
        stderr_thread.join()
        proc.stderr.close()
        err = b"".join(stderr_chunks).decode(errors="replace").strip()
        if err and not stopped_early:
            print(f"FFmpeg warnings while decoding {filename}:\n{err}")

    for tr in tracks.values():
        tr["time"] = np.asarray(tr["time"], dtype=np.float64)
        tr["frame"] = np.asarray(tr["frame"], dtype=np.int64)
        tr["landmarks"] = np.asarray(tr["landmarks"], dtype=np.float64)
    if verbose:
        spans = ", ".join(f"id {k}: {len(v['time'])}"
                          for k, v in sorted(tracks.items()))
        print(f"{os.path.basename(filename)}: {fi} frames, "
              f"{len(tracks)} identities ({spans})")
    return {"tracks": tracks, "n_frames": fi, "fps": sample_fps,
            "width": w, "height": h, "names": list(COCO_KEYPOINT_NAMES)}


def extract_pose_landmarks_yolo(
        filename: str,
        fps: float | None = None,
        width: int | None = None,
        t0: float = 0.0,
        duration: float | None = None,
        model: str = "yolo11n-pose.pt",
        conf: float = 0.25,
        max_frames: int | None = None,
        target_name: str | None = None,
        track: bool = False,
        tracker: str = "bytetrack.yaml",
        verbose: bool = True) -> dict:
    """
    Run a YOLO pose model over a whole video: the Ultralytics twin of
    :func:`extract_pose_landmarks`, on the same trajectory-array contract.

    Same decode pipe, same result dictionary, so the two detectors can be
    compared on a shared clock with the anchor-and-match tooling --- the point
    of having a twin. The differences are the topology and the third channel:
    YOLO emits the 17-point COCO set (``COCO_KEYPOINT_NAMES``), and the third
    value per keypoint is the model's keypoint confidence rather than
    MediaPipe's visibility. A keypoint the model marks with zero confidence has
    no measured position (the raw output pins it to the image origin), so its
    coordinates are returned as NaN rather than as a fabricated point. When
    several people are in frame, the highest-confidence detection is followed;
    multi-person trajectories are out of scope for the twin contract.

    Ultralytics is an optional dependency (``pip install musicalgestures[yolo]``)
    and is imported lazily. The model file is downloaded on first use into
    ``musicalgestures/models/`` and reused after that.

    Args:
        filename (str): Path to the input video file.
        fps (float, optional): Analysis frame rate, resampled by FFmpeg.
            Defaults to None (native frame rate).
        width (int, optional): Resize the analysis frames to this width,
            keeping the aspect ratio. Defaults to None (native resolution).
        t0 (float, optional): Start of the analysis window in seconds
            (input-side seek; returned timestamps stay on the source clock).
            Defaults to 0.0.
        duration (float, optional): Length of the analysis window in seconds.
            Defaults to None (until the end of the file).
        model (str, optional): An Ultralytics pose model: a bare released name
            (downloaded and cached in ``musicalgestures/models/``) or a path to
            a ``.pt`` file. Defaults to "yolo11n-pose.pt", the smallest.
        conf (float, optional): Detection confidence threshold. Defaults
            to 0.25, the Ultralytics default.
        max_frames (int, optional): Stop after this many analysed frames.
            Defaults to None (whole video).
        target_name (str, optional): If given, also write the trajectories as a
            tidy CSV with columns ``time`` and ``<name>_x``, ``<name>_y``,
            ``<name>_v`` per keypoint. Defaults to None.
        track (bool, optional): Follow one stable identity through Ultralytics'
            tracker instead of the highest-confidence detection per frame. With
            two bodies in frame the per-frame selection flips between them ---
            two dancers, or a dancer and their projection on a screen --- and
            tracking is the cure: the identity present in the most frames (ties
            to higher confidence) is followed throughout. For every identity
            separately, use :func:`extract_pose_tracks_yolo`. Defaults to False.
        tracker (str, optional): Ultralytics tracker configuration, used when
            ``track=True``. Defaults to "bytetrack.yaml".
        verbose (bool, optional): Print a one-line detection-rate summary.
            Defaults to True.

    Returns:
        dict: As :func:`extract_pose_landmarks`, with ``landmarks`` of shape
        (F, 17, 3), ``names`` the COCO keypoint names, and ``world`` always
        None (YOLO pose has no world-coordinate output).
    """
    if t0 < 0:
        raise ValueError(f"t0 must be >= 0, got {t0!r}")
    if duration is not None and duration <= 0:
        raise ValueError(f"duration must be > 0, got {duration!r}")

    if track:
        data = extract_pose_tracks_yolo(
            filename, fps=fps, width=width, t0=t0, duration=duration,
            model=model, conf=conf, max_frames=max_frames, tracker=tracker,
            verbose=False)
        n_points = len(COCO_KEYPOINT_NAMES)
        n = data["n_frames"]
        lm = np.full((n, n_points, 3), np.nan)
        det = np.zeros(n, dtype=bool)
        if data["tracks"]:
            def _rank(tr):
                c = tr["landmarks"][:, :, 2]
                return (len(tr["time"]),
                        float(np.nanmean(c)) if c.size else 0.0)
            primary = max(data["tracks"].values(), key=_rank)
            lm[primary["frame"]] = primary["landmarks"]
            det[primary["frame"]] = True
        result = {"time": t0 + np.arange(n) / data["fps"], "landmarks": lm,
                  "world": None, "detected": det,
                  "detection_rate": float(det.mean()) if n else 0.0,
                  "fps": data["fps"], "width": data["width"],
                  "height": data["height"], "names": list(COCO_KEYPOINT_NAMES)}
        if verbose:
            print(f"{os.path.basename(filename)}: {n} frames at "
                  f"{data['fps']:g} fps, primary identity present in "
                  f"{100.0 * result['detection_rate']:.0f}% of frames.")
        if target_name is not None:
            _write_landmarks_csv(target_name, result)
        return result

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise ImportError(
            "Ultralytics is required for extract_pose_landmarks_yolo() but is not "
            "installed. Install the optional dependencies with: "
            "pip install musicalgestures[yolo]") from exc

    from pathlib import Path

    model_path = Path(model)
    if not model_path.exists() and model_path.name == str(model):
        # A bare released name: cache beside the MediaPipe models.
        from ultralytics.utils.downloads import attempt_download_asset
        models_dir = Path(__file__).parent / "models"
        models_dir.mkdir(exist_ok=True)
        model_path = Path(attempt_download_asset(str(models_dir / model)))
    yolo = YOLO(str(model_path))

    n_points = len(COCO_KEYPOINT_NAMES)
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
        cmd += ["-ss", str(t0)]
    cmd += ["-i", filename]
    if duration is not None:
        cmd += ["-t", str(duration)]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-pix_fmt", "rgb24", "-f", "rawvideo", "-"]

    times, lm2d, detected = [], [], []
    frame_bytes = w * h * 3
    stopped_early = False
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None and proc.stderr is not None
    stderr_chunks: list[bytes] = []

    def _drain_stderr():
        for chunk in iter(lambda: proc.stderr.read(4096), b""):
            stderr_chunks.append(chunk)

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()
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
            t = t0 + fi / sample_fps
            res = yolo.predict(frame, conf=conf, verbose=False)[0]
            kp = res.keypoints
            if kp is None or kp.xy is None or len(kp.xy) == 0 or kp.conf is None:
                lm2d.append(np.full((n_points, 3), np.nan))
                detected.append(False)
            else:
                person = int(res.boxes.conf.argmax()) if res.boxes is not None else 0
                xy = kp.xy[person].cpu().numpy().astype(np.float64)
                c = kp.conf[person].cpu().numpy().astype(np.float64)
                #: Zero confidence means the model did not see the point; its
                #: raw coordinates are the image origin, which is not a
                #: measurement.
                xy[c <= 0.0] = np.nan
                lm2d.append(np.column_stack([xy, c]))
                detected.append(True)
            times.append(t)
            fi += 1
    finally:
        proc.stdout.close()
        proc.wait()
        stderr_thread.join()
        proc.stderr.close()
        err = b"".join(stderr_chunks).decode(errors="replace").strip()
        if err and not stopped_early:
            print(f"FFmpeg warnings while decoding {filename}:\n{err}")

    n_frames = len(times)
    result = {
        "time": np.asarray(times, dtype=np.float64),
        "landmarks": (np.asarray(lm2d, dtype=np.float64)
                      if n_frames else np.empty((0, n_points, 3))),
        "world": None,
        "detected": np.asarray(detected, dtype=bool),
        "detection_rate": float(np.mean(detected)) if n_frames else 0.0,
        "fps": sample_fps,
        "width": w,
        "height": h,
        "names": list(COCO_KEYPOINT_NAMES),
    }

    if verbose:
        print(f"{os.path.basename(filename)}: {n_frames} frames at "
              f"{sample_fps:g} fps ({w}x{h}), pose detected in "
              f"{100.0 * result['detection_rate']:.0f}% of frames.")

    if target_name is not None:
        _write_landmarks_csv(target_name, result)

    return result


def fragment_embeddings(filename, tracks_data: dict,
                        bins: int = 12, verbose: bool = True) -> dict:
    """One appearance vector per track fragment, from a single sequential pass.

    The v2 half of fragment re-association
    (`plans/2026-08-30-reid-v2-design.md`): appearance is what survives an
    occlusion, and this collects it the way this project's drives prefer --- one
    sequential decode rather than thousands of seeks. For every stored detection
    row, the torso region (the box the shoulder and hip keypoints span, padded)
    is cut from the frame and summarised as a hue--saturation histogram; a
    fragment's embedding is the median over its rows, so a few bad crops do not
    speak for the fragment.

    A colour histogram is deliberately the first tool: the problem is closed
    over one session --- same people, same clothes, one camera --- and the
    within-fragment consistency check in the test suite is the gate for whether
    it suffices before anything heavier is considered.

    Args:
        filename: The video the fragments were tracked in.
        tracks_data (dict): As returned by :func:`extract_pose_tracks_yolo`;
            its `fps`, `width` and `n_frames` reproduce the extraction's exact
            frame grid.
        bins (int): Histogram bins per channel. Defaults to 12.
        verbose (bool): Print a one-line summary. Defaults to True.

    Returns:
        dict: Fragment id to a normalised embedding vector.
    """
    import cv2

    fps = float(tracks_data["fps"])
    w = int(tracks_data["width"])
    h = int(tracks_data["height"])

    #: frame index -> list of (fragment id, row landmarks)
    per_frame: dict = {}
    for k, tr in tracks_data["tracks"].items():
        lm = np.asarray(tr["landmarks"], dtype=float)
        for fi, row in zip(np.asarray(tr["frame"], dtype=int), lm):
            per_frame.setdefault(int(fi), []).append((k, row))
    if not per_frame:
        return {}
    last = max(per_frame)

    cmd = ["ffmpeg", "-v", "error", "-i", str(filename),
           "-vf", f"fps={fps},scale={w}:{h}",
           "-pix_fmt", "bgr24", "-f", "rawvideo", "-"]
    votes: dict = {}
    frame_bytes = w * h * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)
    assert proc.stdout is not None
    try:
        fi = 0
        while fi <= last:
            buf = proc.stdout.read(frame_bytes)
            if buf is None or len(buf) < frame_bytes:
                break
            if fi in per_frame:
                frame = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
                for k, row in per_frame[fi]:
                    pts = row[:, :2].copy()
                    pts[row[:, 2] < 0.3] = np.nan
                    core = pts[[5, 6, 11, 12]]
                    if not np.isfinite(core).all():
                        continue
                    x0, y0 = np.nanmin(core, axis=0)
                    x1, y1 = np.nanmax(core, axis=0)
                    px = 0.25 * max(x1 - x0, y1 - y0) + 2
                    a, b = int(max(0, x0 - px)), int(min(w, x1 + px))
                    c, d_ = int(max(0, y0 - px)), int(min(h, y1 + px))
                    if b - a < 4 or d_ - c < 4:
                        continue
                    crop = frame[c:d_, a:b]
                    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                    hist = cv2.calcHist([hsv], [0, 1], None, [bins, bins],
                                        [0, 180, 0, 256]).ravel()
                    total = hist.sum()
                    if total > 0:
                        votes.setdefault(k, []).append(hist / total)
            fi += 1
    finally:
        proc.stdout.close()
        proc.terminate()
        proc.wait()

    out = {k: np.median(np.asarray(v), axis=0) for k, v in votes.items() if v}
    if verbose:
        print(f"{os.path.basename(str(filename))}: embeddings for {len(out)} "
              f"of {len(tracks_data['tracks'])} fragments")
    return out


def associate_fragments(tracks_data: dict, n_movers: int = 2,
                        max_gap_s: float = 2.0,
                        max_speed: float | None = None,
                        embeddings: dict | None = None,
                        appearance_max_gap_s: float = 120.0,
                        min_separation: float | None = None) -> dict:
    """Chain track fragments into persistent movers, refusing where honesty demands.

    Identity tracking over a long session yields fragments --- trustworthy within
    themselves, unlinked between themselves. This chains them into `n_movers`
    persistent movers using position and time only, under three rules from the
    design (`plans/2026-08-30-fragment-reassociation-design.md`):

    - **Exclusivity**: fragments overlapping in time are different movers.
    - **Plausibility**: a fragment continues a mover only when the time gap is at
      most `max_gap_s` and the bridging speed of the shoulder midpoint is below
      `max_speed` --- whose default is measured from the material itself (three
      times the 95th percentile of within-fragment speeds), never guessed.
    - **Refusal**: when more than one mover could accept a fragment, or none can,
      that moment becomes a recorded break, never a guess. Chains restart after a
      break, and nothing claims continuity across one. Position alone cannot
      disambiguate two movers who cross exactly at a fragment boundary; the break
      list is where an analyst resolves those moments by watching the video.

    Args:
        tracks_data (dict): As returned by :func:`extract_pose_tracks_yolo`.
        n_movers (int): Persistent movers to chain. Defaults to 2.
        max_gap_s (float): Longest silence a chain may bridge. Defaults to 2.
        max_speed (float, optional): Fastest plausible bridge, in the landmarks'
            units per second. Defaults to None: measured from the fragments.
        embeddings (dict, optional): Appearance vector per fragment id, as from
            :func:`fragment_embeddings`. When given, the v2 rules apply: an
            ambiguous positional choice is decided by appearance when one
            candidate matches clearly better than the rest, and a fragment no
            mover can positionally accept may be appearance-bridged across up
            to `appearance_max_gap_s`. A choice appearance cannot clearly make
            stays a break --- refusal remains output.
        appearance_max_gap_s (float): Longest silence an appearance link may
            bridge. Defaults to 120.
        min_separation (float, optional): How much closer the best appearance
            match must be than the second best. Defaults to None: measured as
            the 95th percentile of within-fragment embedding spread, so the
            bar comes from the material's own appearance stability.

    Returns:
        dict: ``segments`` --- one per stretch between breaks, each with
        ``start_s``, ``end_s`` and ``movers`` mapping a mover index to its
        concatenated ``time``, ``frame`` and ``landmarks``; ``breaks`` with
        ``time_s``, ``reason`` ("ambiguous", "no plausible mover") and the
        candidate movers; and ``coverage_s`` per mover across all segments.
    """
    frags = []
    for k, tr in tracks_data["tracks"].items():
        lm = np.asarray(tr["landmarks"], dtype=float)
        if lm.shape[0] == 0:
            continue
        mid = np.nanmean(lm[:, [5, 6], :2], axis=1)
        frags.append({"id": k, "time": np.asarray(tr["time"], dtype=float),
                      "frame": np.asarray(tr["frame"]), "landmarks": lm,
                      "mid": mid})
    frags.sort(key=lambda f: f["time"][0])

    if max_speed is None:
        v = []
        for f in frags:
            dt = np.diff(f["time"])
            ok = dt > 0
            if ok.any():
                v.append(np.linalg.norm(np.diff(f["mid"], axis=0), axis=1)[ok]
                         / dt[ok])
        allv = np.concatenate(v) if v else np.zeros(1)
        finite = allv[np.isfinite(allv)]
        max_speed = 3.0 * float(np.percentile(finite, 95)) if finite.size else np.inf

    if embeddings is not None and min_separation is None:
        #: Within-fragment spread: how far one body's own appearance wanders.
        #: With single-vector embeddings per fragment this needs pairs, so the
        #: proxy is the spread among ALL fragments' vectors' nearest neighbours;
        #: fragment_embeddings supplies a measured value where it can.
        vecs = np.asarray([embeddings[f["id"]] for f in frags
                           if f["id"] in embeddings], dtype=float)
        if len(vecs) >= 3:
            d = np.linalg.norm(vecs[:, None, :] - vecs[None, :, :], axis=2)
            np.fill_diagonal(d, np.inf)
            min_separation = float(np.percentile(d.min(axis=1), 95))
        else:
            min_separation = 0.0

    def looks_like(f, mover):
        """Distance from a fragment's appearance to a mover's chain mean."""
        if embeddings is None or f["id"] not in embeddings:
            return np.inf
        chain = [embeddings[g["id"]] for g in mover["frags"]
                 if g["id"] in embeddings]
        if not chain:
            return np.inf
        return float(np.linalg.norm(np.asarray(embeddings[f["id"]], dtype=float)
                                    - np.mean(np.asarray(chain, dtype=float),
                                              axis=0)))

    segments: list = []
    breaks: list = []
    coverage: dict = {m: 0.0 for m in range(n_movers)}

    def new_state():
        return [{"frags": [], "end_t": None, "end_pos": None}
                for _ in range(n_movers)]

    def flush(state):
        used = [m for m in state if m["frags"]]
        if not used:
            return
        movers = {}
        for i, m in enumerate(used):
            movers[i] = {
                "time": np.concatenate([f["time"] for f in m["frags"]]),
                "frame": np.concatenate([f["frame"] for f in m["frags"]]),
                "landmarks": np.concatenate([f["landmarks"] for f in m["frags"]]),
            }
            coverage[i] += float(sum(f["time"][-1] - f["time"][0]
                                     for f in m["frags"]))
        segments.append({"start_s": float(min(v["time"][0]
                                              for v in movers.values())),
                         "end_s": float(max(v["time"][-1]
                                            for v in movers.values())),
                         "movers": movers})

    state = new_state()
    for f in frags:
        start, s_pos = f["time"][0], f["mid"][0]
        candidates = []
        empty = None
        for mi, m in enumerate(state):
            if m["end_t"] is None:
                if empty is None:
                    empty = mi
                continue
            if m["end_t"] > start:
                continue                       # busy: overlaps this fragment
            gap = start - m["end_t"]
            if gap > max_gap_s:
                continue
            bridge = float(np.linalg.norm(s_pos - m["end_pos"])) / max(gap, 1e-6)
            if np.isfinite(bridge) and bridge <= max_speed:
                candidates.append(mi)
        def by_appearance(pool):
            """The one member of `pool` appearance clearly prefers, or None."""
            if embeddings is None or not pool:
                return None
            dists = sorted((looks_like(f, state[m]), m) for m in pool)
            if not np.isfinite(dists[0][0]):
                return None
            #: STRICTLY more separated than the within-appearance spread: with
            #: perfectly stable appearances the spread is 0 and any positive
            #: margin decides, while identical-everyone gives margins of exactly
            #: 0, which strictness correctly refuses.
            if len(dists) == 1 or (dists[1][0] - dists[0][0]) > min_separation:
                return dists[0][1]
            return None

        if len(candidates) == 1:
            mi = candidates[0]
        elif len(candidates) > 1:
            mi = by_appearance(candidates)
            if mi is None:
                breaks.append({"time_s": float(start), "reason": "ambiguous",
                               "candidates": candidates})
                flush(state)
                state = new_state()
                mi = 0
        elif empty is not None:
            mi = empty
        else:
            #: Position refused everyone; appearance may bridge a longer gap.
            reachable = [m for m, st in enumerate(state)
                         if st["end_t"] is not None and st["end_t"] <= start
                         and start - st["end_t"] <= appearance_max_gap_s]
            mi = by_appearance(reachable)
            if mi is None:
                breaks.append({"time_s": float(start),
                               "reason": "no plausible mover",
                               "candidates": []})
                flush(state)
                state = new_state()
                mi = 0
        state[mi]["frags"].append(f)
        state[mi]["end_t"] = float(f["time"][-1])
        state[mi]["end_pos"] = f["mid"][-1]
    flush(state)

    return {"segments": segments, "breaks": breaks,
            "n_fragments": len(frags), "coverage_s": coverage}


def extract_pose_landmarks_rtmpose(
        filename: str,
        fps: float | None = None,
        width: int | None = None,
        t0: float = 0.0,
        duration: float | None = None,
        mode: str = "balanced",
        max_frames: int | None = None,
        target_name: str | None = None,
        device: str | None = None,
        verbose: bool = True) -> dict:
    """RTMPose over a whole video: the Apache-licensed twin, same contract.

    The third member of the extractor family, riding `rtmlib` (RTMPose through
    ONNX runtime --- no MMPose stack) and emitting the same 17-point COCO
    topology as the YOLO twin, so all three extractors feed the same
    detector-agreement tooling. Benchmarked on a dark dance stage, RTMPose's
    separate person detector held 100 per cent detection where small single-stage
    models flickered; it is also the family under an Apache licence.

    rtmlib is an optional dependency (``pip install musicalgestures[rtmpose]``)
    and is imported lazily. Model files download to rtmlib's own cache on first
    use. When several people are in frame, the highest-scoring detection is
    followed, exactly as the YOLO twin does; identity tracking stays the YOLO
    path's feature for now.

    Args:
        filename (str): Path to the input video file.
        fps (float, optional): Analysis frame rate, resampled by FFmpeg.
        width (int, optional): Analysis width in pixels, aspect preserved.
        t0 (float, optional): Start of the analysis window in seconds.
        duration (float, optional): Length of the window in seconds.
        mode (str, optional): rtmlib's size: "lightweight", "balanced" or
            "performance". Defaults to "balanced".
        max_frames (int, optional): Stop after this many analysed frames.
        target_name (str, optional): Also write a tidy CSV, as the twins do.
        device (str, optional): "cuda" or "cpu". Defaults to None: cuda when
            onnxruntime reports a CUDA execution provider, else cpu --- and the
            choice is recorded in the result's ``device``.
        verbose (bool, optional): Print a one-line summary. Defaults to True.

    Returns:
        dict: As :func:`extract_pose_landmarks_yolo`, plus ``device``.
    """
    if t0 < 0:
        raise ValueError(f"t0 must be >= 0, got {t0!r}")
    if duration is not None and duration <= 0:
        raise ValueError(f"duration must be > 0, got {duration!r}")

    try:
        import onnxruntime as ort
        from rtmlib import Body
    except ImportError as exc:
        raise ImportError(
            "rtmlib is required for extract_pose_landmarks_rtmpose() but is not "
            "installed. Install the optional dependencies with: "
            "pip install musicalgestures[rtmpose]") from exc

    if device is None:
        device = ("cuda" if "CUDAExecutionProvider" in ort.get_available_providers()
                  else "cpu")
    body = Body(mode=mode, backend="onnxruntime", device=device)

    n_points = len(COCO_KEYPOINT_NAMES)
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
        cmd += ["-ss", str(t0)]
    cmd += ["-i", filename]
    if duration is not None:
        cmd += ["-t", str(duration)]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    #: BGR straight from FFmpeg: rtmlib expects OpenCV-style images.
    cmd += ["-pix_fmt", "bgr24", "-f", "rawvideo", "-"]

    times, lm2d, detected = [], [], []
    frame_bytes = w * h * 3
    stopped_early = False
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None and proc.stderr is not None
    stderr_chunks: list[bytes] = []

    def _drain_stderr():
        for chunk in iter(lambda: proc.stderr.read(4096), b""):
            stderr_chunks.append(chunk)

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()
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
            t = t0 + fi / sample_fps
            kps, scores = body(frame)
            if len(kps):
                person = int(np.argmax(np.asarray(scores).mean(axis=1)))
                xy = np.asarray(kps[person], dtype=np.float64)
                c = np.asarray(scores[person], dtype=np.float64)
                xy[c <= 0.0] = np.nan
                lm2d.append(np.column_stack([xy, c]))
                detected.append(True)
            else:
                lm2d.append(np.full((n_points, 3), np.nan))
                detected.append(False)
            times.append(t)
            fi += 1
    finally:
        proc.stdout.close()
        proc.wait()
        stderr_thread.join()
        proc.stderr.close()
        err = b"".join(stderr_chunks).decode(errors="replace").strip()
        if err and not stopped_early:
            print(f"FFmpeg warnings while decoding {filename}:\n{err}")

    n_frames = len(times)
    result = {
        "time": np.asarray(times, dtype=np.float64),
        "landmarks": (np.asarray(lm2d, dtype=np.float64)
                      if n_frames else np.empty((0, n_points, 3))),
        "world": None,
        "detected": np.asarray(detected, dtype=bool),
        "detection_rate": float(np.mean(detected)) if n_frames else 0.0,
        "fps": sample_fps,
        "width": w,
        "height": h,
        "names": list(COCO_KEYPOINT_NAMES),
        "device": device,
    }
    if verbose:
        print(f"{os.path.basename(filename)}: {n_frames} frames at "
              f"{sample_fps:g} fps ({w}x{h}, {device}), pose detected in "
              f"{100.0 * result['detection_rate']:.0f}% of frames.")
    if target_name is not None:
        _write_landmarks_csv(target_name, result)
    return result


#: The bones of the 17-point COCO topology, as index pairs into
#: COCO_KEYPOINT_NAMES: head, shoulder girdle, arms, trunk, legs.
COCO_SKELETON = ((0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9),
                 (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13),
                 (13, 15), (12, 14), (14, 16))


def skeleton_timeline(landmarks, times, ax=None, n_figures: int = 24,
                      min_conf: float = 0.3, height: float = 1.0,
                      color="#7a3b8f", lw: float = 1.2) -> int:
    """A timeline of stick figures: posture at sampled moments, drawn on time.

    The keyframe display's skeletal descendant: `n_figures` moments spread evenly
    over the material, each drawn as a stick figure at its place on the time axis,
    so a raised arm or a deep bend is visible AS posture where a motiongram shows
    only that something moved. Each figure is normalised by its own torso length
    and centred in its slot, so the timeline reads posture and not position ---
    where the body was in the room is the spatial maps' job.

    A moment with no usable detection --- fewer than half its keypoints above
    `min_conf` at the nearest detected frame --- is skipped rather than guessed,
    so gaps in the timeline are honest gaps in the tracking.

    Args:
        landmarks: (frames, 17, 3) trajectories in the COCO topology, confidence
            in the third channel, as the YOLO extractors return.
        times: (frames,) timestamps in seconds.
        ax: A matplotlib axes to draw on. Created when None.
        n_figures (int): Moments to draw. Defaults to 24.
        min_conf (float): Keypoint confidence below which a point does not
            exist. Defaults to 0.3.
        height (float): Figure height in axis y-units. Defaults to 1.
        color: Line colour.
        lw (float): Line width.

    Returns:
        int: The number of figures actually drawn.
    """
    import matplotlib.pyplot as plt

    landmarks = np.asarray(landmarks, dtype=float)
    times = np.asarray(times, dtype=float)
    if ax is None:
        _, ax = plt.subplots(figsize=(14, 2.4))
    if landmarks.shape[0] == 0:
        return 0

    ok = np.zeros(landmarks.shape[0], dtype=bool)
    conf = landmarks[:, :, 2]
    with np.errstate(invalid="ignore"):
        ok = (np.nan_to_num(conf) >= min_conf).sum(axis=1) >= 9

    targets = np.linspace(times[0], times[-1], n_figures)
    slot = (times[-1] - times[0]) / max(n_figures, 1)
    #: The x-axis is time and the y-axis is body height, so a figure drawn with
    #: one scale for both would compress to a stroke. Correct x by the axes'
    #: data-per-inch ratio, so the drawn body keeps human proportions whatever
    #: the timeline's length.
    pos = ax.get_position()
    fw, fh = ax.figure.get_size_inches()
    x_per_in = (times[-1] - times[0]) / max(fw * pos.width, 1e-9)
    y_per_in = (1.2 * height) / max(fh * pos.height, 1e-9)
    xaspect = x_per_in / y_per_in if y_per_in > 0 else 1.0
    drawn = 0
    used: set = set()
    for tt in targets:
        cand = np.nonzero(ok)[0]
        if cand.size == 0:
            break
        fi = int(cand[np.argmin(np.abs(times[cand] - tt))])
        #: The nearest usable frame must belong to this slot, or the gap is real.
        if abs(times[fi] - tt) > slot or fi in used:
            continue
        used.add(fi)
        pts = landmarks[fi, :, :2].copy()
        pts[conf[fi] < min_conf] = np.nan
        mid_sh = np.nanmean(pts[[5, 6]], axis=0)
        mid_hip = np.nanmean(pts[[11, 12]], axis=0)
        torso = float(np.linalg.norm(mid_sh - mid_hip))
        if not np.isfinite(torso) or torso <= 0:
            continue
        #: Normalise by the torso so every figure has one scale; flip y so up is up.
        scale = height / (3.2 * torso)
        centre = np.nanmean(pts, axis=0)
        x = (pts[:, 0] - centre[0]) * scale * 0.9 * xaspect
        #: A figure never leaves its slot: wide poses compress sideways rather
        #: than tangling with their neighbours.
        half = np.nanmax(np.abs(x)) if np.isfinite(x).any() else 0.0
        if half > 0.42 * slot:
            x = x * (0.42 * slot / half)
        y = -(pts[:, 1] - centre[1]) * scale
        #: And never taller than its lane: a mis-scaled figure (a tiny estimated
        #: torso) compresses instead of striping the whole plot.
        tall = np.nanmax(np.abs(y)) if np.isfinite(y).any() else 0.0
        if tall > 0.55 * height:
            y = y * (0.55 * height / tall)
        for a, b in COCO_SKELETON:
            if np.isfinite(x[a]) and np.isfinite(x[b]):
                ax.plot([tt + x[a], tt + x[b]], [y[a] + height / 2,
                                                 y[b] + height / 2],
                        color=color, lw=lw, solid_capstyle="round")
        drawn += 1
    ax.set_ylim(-0.1 * height, 1.1 * height)
    ax.set_yticks([])
    return drawn


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

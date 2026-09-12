"""Camera cuts and pan/tilt/zoom, so that camera motion is not read as performer motion.

An operated camera pans, tilts and zooms, and a multi-camera edit cuts between angles. Both
inflate frame-difference measures (quantity of motion, motiongrams) and change who is in the
picture. This module labels each sample of a video as ``still``, ``moving`` or ``cut`` from the
global geometry between consecutive frames: ORB features matched across the pair and a
partial-affine (translation + scale) RANSAC fit. Consistent geometry with a shift or a scale
change is a camera move; no consistent geometry together with a large change of the picture
is a cut; the rest is still. Shots are the spans between cuts; *framings* are the still runs
between moves and cuts, which is the unit that matters when counting people or comparing
motion, because the framing is constant inside one.

The analysis runs on a small, low-rate proxy (2 fps, 180 px high by default), made once with
ffmpeg and reused, so a 90-minute recording takes about a minute.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import cast

import numpy as np

__all__ = ["camera_motion", "camera_state_at", "still_runs", "make_proxy"]


def make_proxy(filename: "str | Path", proxy_path: "str | Path", fps: float = 2.0, height: int = 180) -> Path:
    """A low-rate, low-resolution copy of the video (ffmpeg), cached at `proxy_path`."""
    out: Path = Path(proxy_path)
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(filename), "-vf", f"fps={fps},scale=-2:{height}",
                        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(out)],
                       check=True, capture_output=True)
    return out


def camera_motion(filename: "str | Path", proxy_path: "str | Path | None" = None, fps: float = 2.0, height: int = 180, move_px: float = 1.0,
                  zoom: float = 0.005, min_inliers: int = 15, cache=None, verbose: bool = True) -> dict:
    """Per-sample camera state for a video.

    Returns a dict with ``hop_s``, ``t`` (sample times), ``state`` (``still`` / ``moving`` / ``cut``),
    ``tx``, ``ty`` (pixels at proxy scale), ``scale``, ``inliers``, ``cuts`` (times), ``shots``
    (``{"start", "end"}`` between cuts) and ``summary`` (share of time in each state). `move_px` and
    `zoom` are the per-sample translation and scale change that count as a move; both were set on an
    operated concert camera and are conservative for a tripod. Pass `cache` (a JSON path) to reuse.
    """
    import cv2
    if cache and Path(cache).exists():
        cached: dict = json.loads(Path(cache).read_text())
        return cached
    proxy = make_proxy(filename, proxy_path or Path(str(filename)).with_suffix(".camera_proxy.mp4"), fps, height)
    cap = cv2.VideoCapture(str(proxy))
    real_fps = cap.get(cv2.CAP_PROP_FPS) or fps
    orb = cv2.ORB_create(nfeatures=400)  # type: ignore[attr-defined]
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    prev: tuple | None = None
    t: list[float] = []; state: list[str] = []; tx: list[float] = []; ty: list[float] = []
    sc: list[float] = []; inl: list[int] = []
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp, des = orb.detectAndCompute(g, None)
        hist = cv2.calcHist([g], [0], None, [32], [0, 256]); cv2.normalize(hist, hist)
        if prev is not None:
            pg, pkp, pdes, phist = prev
            n_in, dx, dy, s = 0, 0.0, 0.0, 1.0
            if des is not None and pdes is not None and len(kp) >= 8 and len(pkp) >= 8:
                m = bf.match(pdes, des)
                if len(m) >= 8:
                    src = np.float32([pkp[x.queryIdx].pt for x in m]); dst = np.float32([kp[x.trainIdx].pt for x in m])
                    A, mask = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=3.0)
                    if A is not None:
                        n_in = int(mask.sum()); dx, dy = float(A[0, 2]), float(A[1, 2])
                        s = float(np.hypot(A[0, 0], A[0, 1]))
            corr = float(cv2.compareHist(phist, hist, cv2.HISTCMP_CORREL))
            diff = float(np.abs(g.astype(np.int16) - pg.astype(np.int16)).mean())
            if n_in < min_inliers and (corr < 0.6 or diff > 30):
                st = "cut"
            elif n_in >= min_inliers and (abs(dx) > move_px or abs(dy) > move_px or abs(s - 1) > zoom):
                st = "moving"
            else:
                st = "still"
            t.append(round(i / real_fps, 3)); state.append(st); tx.append(round(dx, 2)); ty.append(round(dy, 2))
            sc.append(round(s, 4)); inl.append(n_in)
        prev = (g, kp, des, hist)
        i += 1
        if verbose and i % 2000 == 0:
            print(f"camera_motion: {i} frames")
    cap.release()
    cuts = [t[k] for k in range(len(t)) if state[k] == "cut" and (k == 0 or state[k - 1] != "cut")]
    edges = [0.0] + cuts + [round(i / real_fps, 3)]
    out = {"hop_s": round(1 / real_fps, 4), "proxy": str(proxy), "t": t, "state": state, "tx": tx, "ty": ty,
           "scale": sc, "inliers": inl, "cuts": cuts,
           "shots": [{"start": a, "end": b} for a, b in zip(edges, edges[1:]) if b - a > 0],
           "summary": {k: round(state.count(k) / max(1, len(state)), 3) for k in ("still", "moving", "cut")}}
    if cache:
        Path(cache).write_text(json.dumps(out))
    return out


def camera_state_at(cam: dict, times) -> np.ndarray:
    """The camera state at each time (``still`` when the analysis has nothing there)."""
    times = np.atleast_1d(np.asarray(times, float))
    states: list[str] = ["still"] * len(times)
    if cam and cam.get("t"):
        tt = np.asarray(cam["t"], float)
        labels: list[str] = list(cam["state"])
        idx = np.clip(np.searchsorted(tt, times, side="right") - 1, 0, len(tt) - 1)
        states = [labels[int(i)] for i in idx]
    return cast("np.ndarray", np.array(states, dtype=object))


def still_runs(cam: dict, start_s: float = 0.0, end_s: float | None = None, min_s: float = 10.0) -> list[tuple[float, float]]:
    """Framings: spans inside ``[start_s, end_s)`` where the camera held still for at least `min_s`."""
    tt = np.asarray(cam["t"]); st = np.asarray(cam["state"], dtype=object)
    end_s = float(tt[-1] + cam["hop_s"]) if end_s is None else end_s
    runs: list[tuple[float, float]] = []
    a: float | None = None
    for t, k in zip(tt, st):
        if t < start_s or t >= end_s:
            continue
        if k == "still" and a is None:
            a = float(t)
        elif k != "still" and a is not None:
            if t - a >= min_s:
                runs.append((a, float(t)))
            a = None
    if a is not None and end_s - a >= min_s:
        runs.append((a, float(end_s)))
    return runs

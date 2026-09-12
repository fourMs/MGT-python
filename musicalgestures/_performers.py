"""How many people are performing, read off the video.

A person detector run on a concert video finds everyone in the frame, and in a hall
that is mostly the audience: heads and shoulders in the lower part of the picture,
cut off by the bottom edge. Performers stand (or sit) on a raised stage, so their
heads are in the upper half. That one geometric fact separates the two well enough
to count a soloist, a duo and a five-piece band correctly from an operated camera;
a choir is under-counted, because singers occlude each other in the wide shot.

The camera moves, so no single frame shows everyone. `performer_count` therefore
takes a high percentile of the per-frame counts over a span (the wide shots), and
reports the median and maximum with it so a reader can see how much the shot
framing varied.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from musicalgestures._utils import get_widthheight

__all__ = ["detect_people", "on_stage", "people_track", "performer_count"]


def detect_people(filename, fps: float = 1.0, width: int = 640, model: str = "yolo11n.pt",
                  conf: float = 0.25, device=None, batch: int = 32, verbose: bool = True) -> dict:
    """Person boxes at `fps` samples per second, from a YOLO detector (``ultralytics`` extra).

    Frames are decoded by ffmpeg at `width` pixels (16:9 assumed for the pipe; boxes are
    normalised, so the aspect does not matter downstream). Returns a dict with ``fps``,
    ``model`` and ``frames``: one ``{"t": seconds, "boxes": [[x1, y1, x2, y2, conf], ...]}``
    per sample, coordinates normalised to 0..1.
    """
    from ultralytics import YOLO
    W, H0 = get_widthheight(str(filename))
    height = max(2, int(round(width * H0 / W / 2)) * 2)
    yolo = YOLO(model)
    cmd = ["ffmpeg", "-v", "error", "-i", str(filename), "-vf", f"fps={fps},scale={width}:{height}",
           "-pix_fmt", "bgr24", "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 8)
    if device is None:
        try:
            import torch
            device = 0 if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"
    frames, pending, i = [], [], 0
    nbytes = width * height * 3

    def flush():
        nonlocal pending
        if not pending:
            return
        res = yolo.predict(pending, classes=[0], conf=conf, imgsz=width, device=device, verbose=False)
        for k, r in enumerate(res):
            b = r.boxes
            frames.append({"t": (i - len(pending) + k) / fps,
                           "boxes": [[round(float(v), 4) for v in xyxy] + [round(float(c), 3)]
                                     for xyxy, c in zip(b.xyxyn.tolist(), b.conf.tolist())]})
        pending = []

    while True:
        raw = proc.stdout.read(nbytes)
        if len(raw) < nbytes:
            break
        pending.append(np.frombuffer(raw, np.uint8).reshape(height, width, 3).copy())
        i += 1
        if len(pending) == batch:
            flush()
        if verbose and i % 600 == 0:
            print(f"detect_people: {i} frames")
    flush()
    proc.stdout.close(); proc.wait()
    return {"fps": fps, "width": width, "height": height, "model": str(model), "conf": conf, "frames": frames}


def on_stage(box, min_conf: float = 0.4, head_below: float = 0.5, cut_head_below: float = 0.4) -> bool:
    """Whether one normalised ``[x1, y1, x2, y2, conf]`` box looks like a performer.

    Rejects weak detections, anyone whose head (`y1`) is in the lower part of the frame,
    and anyone cut off by the bottom edge whose head is not clearly high. The defaults
    were set on frames with known counts from an operated concert camera.
    """
    x1, y1, x2, y2, c = box[:5]
    if c < min_conf:
        return False
    if y1 > head_below:
        return False
    if y2 >= 0.97 and y1 > cut_head_below:
        return False
    return True


def people_track(detections: dict, **filter_kw) -> tuple[np.ndarray, np.ndarray]:
    """(times, count of people on stage) per sampled frame."""
    frames = detections["frames"]
    t = np.array([f["t"] for f in frames], float)
    n = np.array([sum(1 for b in f["boxes"] if on_stage(b, **filter_kw)) for f in frames], int)
    return t, n


def performer_count(detections: dict, start_s: float = 0.0, end_s: float | None = None,
                    percentile: float = 90.0, **filter_kw) -> dict:
    """How many performers a span shows: ``estimate`` (the `percentile` of per-frame counts,
    i.e. the wide shots), ``median``, ``max`` and the number of ``frames`` it rests on."""
    t, n = people_track(detections, **filter_kw)
    sel = (t >= start_s) & ((t < end_s) if end_s is not None else True)
    if not sel.any():
        return {"estimate": None, "median": None, "max": None, "frames": 0}
    c = n[sel]
    return {"estimate": int(round(float(np.percentile(c, percentile)))), "median": int(np.median(c)),
            "max": int(c.max()), "frames": int(c.size)}

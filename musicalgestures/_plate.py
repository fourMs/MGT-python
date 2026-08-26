"""The empty room, and where the people are relative to it.

A long recording of a room contains the room. Recovering it gives two things: a background
to subtract, and an **occupancy** signal saying how much of the frame anybody filled --- a
different question from quantity of motion, and one motion cannot answer. A dancer standing
still has no motion and plenty of occupancy.

**Median over frames, never a mean.** A mean keeps a faint ghost of the dancers everywhere
they went, and subtracting a ghost leaves holes shaped like people. The median discards
whatever is present in fewer than half the samples, which is exactly what somebody crossing
a room is, and keeps whatever is usually there, which is exactly what a chair is.

**Then refine once.** A median over a blind sample is still contaminated wherever somebody
stood in one place for much of the recording. Taking it again over the frames that least
resemble the first plate --- the emptiest ones --- removes that, and one pass is enough:
the second plate is what the third would be built from anyway.

Occupancy tolerates downsampling that segmentation does not. Nothing here needs full
resolution, and a few hundred pixels wide is plenty.
"""
from __future__ import annotations

import numpy as np

__all__ = ["sample_frame_indices", "plate_from_stack", "occupancy_from_plate",
           "refine_indices", "room_plate", "occupancy_track"]


def sample_frame_indices(n_frames: int, n_samples: int) -> np.ndarray:
    """Evenly spread sample positions across a recording.

    Evenly rather than randomly: a random sample of a session where the dancers work in
    one half leaves the other half under-represented by luck, and the plate is then a
    picture of the busy half.

    Args:
        n_frames (int): How many frames the recording has.
        n_samples (int): How many to sample.

    Returns:
        np.ndarray: Ascending indices. Every frame once when `n_samples` exceeds
        `n_frames`, since sampling the same frame twice buys nothing.
    """
    n_frames = max(0, int(n_frames))
    n_samples = max(1, int(n_samples))
    if n_frames == 0:
        return np.zeros(0, dtype=int)
    if n_samples >= n_frames:
        return np.arange(n_frames, dtype=int)
    return np.unique(np.linspace(0, n_frames - 1, n_samples).astype(int))


def plate_from_stack(stack) -> np.ndarray:
    """The room, as the per-pixel median over a stack of frames.

    Args:
        stack: Frames, shape (n, h, w) or (n, h, w, c).

    Returns:
        np.ndarray: One frame, the median.
    """
    a = np.asarray(stack, dtype=float)
    return np.median(a, axis=0)


def occupancy_from_plate(frame, plate, threshold: float = 12.0) -> float:
    """What fraction of the frame differs from the room by more than `threshold`.

    Args:
        frame: One frame.
        plate: The room, same shape.
        threshold (float): Difference counting as "something is there", in the units of
            the image. Defaults to 12.0 on an 8-bit scale. **Without a threshold every
            frame is fully occupied**, because sensor noise puts a small difference
            everywhere.

    Returns:
        float: A fraction in [0, 1].
    """
    f = np.asarray(frame, dtype=float)
    p = np.asarray(plate, dtype=float)
    d = np.abs(f - p)
    if d.ndim == 3:
        d = d.max(axis=2)          #: any channel differing is enough
    return float((d > float(threshold)).mean())


def refine_indices(diffs, keep_fraction: float = 0.10) -> np.ndarray:
    """Which sampled frames to rebuild the plate from: the ones least like it already.

    Args:
        diffs: One number per sampled frame, how much it differs from the first plate.
        keep_fraction (float): Fraction to keep. Defaults to 0.10.

    Returns:
        np.ndarray: Indices into `diffs`, ascending. **At least two**, because a median
        over one frame is that frame and not a plate.
    """
    d = np.asarray(diffs, dtype=float).ravel()
    if len(d) == 0:
        return np.zeros(0, dtype=int)
    k = max(2, min(len(d), int(round(len(d) * float(keep_fraction)))))
    return np.sort(np.argsort(d)[:k])


def _read_frames(video, indices, width):
    """Frames at the given indices, greyscale, scaled to `width`."""
    import cv2

    cap = cv2.VideoCapture(str(video))
    out = []
    for i in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, frame = cap.read()
        if not ok:
            continue
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h = max(1, int(g.shape[0] * width / g.shape[1]))
        out.append(cv2.resize(g, (width, h)).astype(float))
    cap.release()
    return np.array(out) if out else np.zeros((0, 1, 1))


def room_plate(video, n_samples: int = 400, width: int = 320,
               keep_fraction: float = 0.10, refine: bool = True):
    """The empty room, from a two-pass median over sampled frames.

    Args:
        video: Path to the video.
        n_samples (int): Frames to sample. Defaults to 400.
        width (int): Working width in pixels. Defaults to 320; occupancy tolerates
            downsampling that segmentation does not.
        keep_fraction (float): Fraction of samples the second pass keeps.
        refine (bool): Take the second pass. Defaults to True.

    Returns:
        tuple: (plate, indices_used).
    """
    import cv2

    cap = cv2.VideoCapture(str(video))
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    idx = sample_frame_indices(n_frames, n_samples)
    stack = _read_frames(video, idx, width)
    if len(stack) == 0:
        raise ValueError(f"{video}: no frames could be read")
    plate = plate_from_stack(stack)
    if not refine or len(stack) < 4:
        return plate, idx
    diffs = np.array([occupancy_from_plate(f, plate) for f in stack])
    keep = refine_indices(diffs, keep_fraction)
    return plate_from_stack(stack[keep]), idx[keep]


def occupancy_track(video, plate, every_n: int = 25, width: int = 320,
                    threshold: float = 12.0):
    """How much of the frame is occupied, sampled through the recording.

    Args:
        video: Path to the video.
        plate: The room, from `room_plate`.
        every_n (int): Sample one frame in this many. Defaults to 25.
        width (int): Working width, which must match the plate's.
        threshold (float): Difference counting as occupied.

    Returns:
        tuple: (frame_indices, occupancy) — a fraction per sampled frame.
    """
    import cv2

    cap = cv2.VideoCapture(str(video))
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    idx = np.arange(0, n_frames, max(1, int(every_n)))
    frames = _read_frames(video, idx, width)
    occ = np.array([occupancy_from_plate(f, plate, threshold) for f in frames])
    return idx[:len(occ)], occ

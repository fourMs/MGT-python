"""A motion gate measured from the recording instead of guessed at.

Every motion measure has a floor. Frame differencing sees sensor noise everywhere the
picture is bright enough; motion vectors carry the encoder's rate decisions, 46 per cent
of them exactly zero and the median non-zero one 0.79 px of quarter-pel noise; optical
flow sits at 0.009 px per pixel per frame across most of the picture. A threshold is what
keeps that out of a result, and a threshold in absolute units cannot serve two recordings
whose floors differ.

Measured on a dance corpus of six recordings, one fixed setting lit **0.52** times the
area the dancers covered in one recording and **1.90** times it in another --- too tight
and too loose at the same number.

So the floor is taken from the material: the distribution of motion magnitudes where
there is nothing to move, which the room plate can point at directly. The gate is a
quantile of that, which makes the parameter a **false-positive rate** rather than a
magnitude.

**What this does and does not buy.** Equalising the false-positive rate makes spatial maps
comparable across recordings. It does **not** make magnitudes comparable: each recording
ends at its own operating point, so a quantity of motion gated this way is harder to
compare across sessions than one gated at a fixed number, not easier. Both are therefore
kept. Use a fixed threshold when magnitudes must be compared, and a measured one when
pictures must be.

**And it can refuse.** Otsu will split pure noise and report a threshold with no sign of
distress. An estimator that always answers has the same fault, so when the background and
the moving parts do not separate --- a camera move, a light change, an empty recording ---
this returns no number at all rather than a plausible one.
"""
from __future__ import annotations

import numpy as np

__all__ = ["noise_floor", "frame_difference_floor", "motion_vector_floor",
           "BoundedSample"]


class BoundedSample:
    """A uniform sample of a stream, bounded in memory whatever the stream's length.

    The floor of a long recording implies hundreds of millions of magnitudes, and
    keeping them all once cost 8 GB and took a measurement service with it. This
    keeps at most about twice `cap` values: every arriving batch is kept with the
    current probability, and when the store exceeds twice the cap it is uniformly
    halved and the probability halves with it. Every value ever offered thus has the
    same chance of being in the final sample, so a quantile of the sample estimates
    the stream's --- which is all `noise_floor` asks of it.
    """

    def __init__(self, cap: int = 2_000_000, seed: int = 0):
        self.cap = int(cap)
        self._rng = np.random.default_rng(seed)
        self._p = 1.0
        self._chunks: list[np.ndarray] = []
        self._held = 0

    def add(self, values):
        values = np.asarray(values).ravel()
        if self._p < 1.0:
            values = values[self._rng.random(values.size) < self._p]
        self._chunks.append(values)
        self._held += values.size
        if self._held > 2 * self.cap:
            pool = np.concatenate(self._chunks)
            keep = self._rng.random(pool.size) < 0.5
            self._chunks = [pool[keep]]
            self._held = int(self._chunks[0].size)
            self._p /= 2.0

    def values(self):
        return (np.concatenate(self._chunks) if self._chunks
                else np.zeros(0, dtype=float))


def noise_floor(background, foreground=None, quantile: float = 0.99,
                min_samples: int = 1000, min_foreground_kept: float = 0.10) -> dict:
    """The gate implied by a sample of magnitudes taken where nothing moves.

    Args:
        background: Motion magnitudes from places nothing should be moving --- pixel
            differences where the plate says nobody is, or vector lengths in unoccupied
            cells. One dimension; shape is not otherwise used.
        foreground (optional): Magnitudes from places something does move. Only used to
            report, and refuse on, what the gate would cost. Without it the gate is
            returned unchecked.
        quantile (float): Where in the background's tail the gate sits. Defaults to 0.99,
            meaning one background sample in a hundred survives the gate.
        min_samples (int): Below this many background samples the estimate is refused.
            Defaults to 1000.
        min_foreground_kept (float): If the gate would keep less than this fraction of
            `foreground`, the two do not separate and the estimate is refused. Defaults
            to 0.10.

    Returns:
        dict: `threshold` (None when refused), `refused`, `reason` (None unless refused),
        `quantile`, `background_samples`, and `foreground_kept` (None without a
        foreground sample).
    """
    background = np.asarray(background, dtype=float).ravel()
    background = background[np.isfinite(background)]

    def refuse(reason: str) -> dict:
        return {"threshold": None, "refused": True, "reason": reason,
                "quantile": quantile, "background_samples": int(background.size),
                "foreground_kept": None}

    if background.size < min_samples:
        return refuse(f"only {background.size} background samples, "
                      f"fewer than the {min_samples} required to estimate a floor")

    threshold = float(np.percentile(background, quantile * 100))

    kept = None
    if foreground is not None:
        fg = np.asarray(foreground, dtype=float).ravel()
        fg = fg[np.isfinite(fg)]
        if fg.size < min_samples:
            return refuse(f"only {fg.size} foreground samples, fewer than the "
                          f"{min_samples} required to check that the gate separates")
        kept = float((fg > threshold).mean())
        if kept < min_foreground_kept:
            return refuse(
                f"a gate at {threshold:.4g} would keep {kept * 100:.1f} per cent of the "
                f"moving sample, below the {min_foreground_kept * 100:.0f} per cent "
                f"required: the background and the moving parts do not separate")

    return {"threshold": threshold, "refused": False, "reason": None,
            "quantile": quantile, "background_samples": int(background.size),
            "foreground_kept": kept}


def _sampled_frames(video, n_samples, width):
    """Consecutive pairs, sampled through the recording, greyscale at `width`.

    Pairs and not singles: a frame difference needs a predecessor, and seeking to
    scattered indices costs more than decoding past them on the drives this runs on.
    """
    import av
    import cv2

    container = av.open(str(video))
    stream = container.streams.video[0]
    stream.thread_type = "AUTO"
    total = stream.frames or 0
    every = max(1, total // max(1, n_samples)) if total else 1
    out, previous = [], None
    try:
        for i, frame in enumerate(container.decode(stream)):
            g = frame.to_ndarray(format="gray")
            h = max(1, int(g.shape[0] * width / g.shape[1]))
            g = cv2.resize(g, (width, h)).astype(np.float32)
            if previous is not None and i % every == 0:
                out.append((previous, g))
            previous = g
    finally:
        container.close()
    return out


def frame_difference_floor(video, plate=None, quantile: float = 0.99,
                           n_samples: int = 200, width: int = 320,
                           tolerance: float = 12.0, **kwargs) -> dict:
    """The frame-differencing gate this recording implies, in grey levels.

    The room plate says which pixels have nobody in front of them. Their frame-to-frame
    differences are the floor by construction --- whatever they show, nothing there
    moved.

    Args:
        video: Path to the video.
        plate (optional): The room, from `room_plate`. Measured here when not given.
        quantile (float): Where in the background's tail the gate sits.
        n_samples (int): Frame pairs to sample.
        width (int): Working width, which the plate must match.
        tolerance (float): Difference from the plate counting as occupied.
        **kwargs: Passed to `noise_floor` --- `min_samples`, `min_foreground_kept`.

    Returns:
        dict: As `noise_floor`, with `threshold` in grey levels on an 8-bit scale. Divide
        by 255 for the `threshold` argument of `mg_motion` and its relatives.
    """
    from musicalgestures._plate import room_plate

    if plate is None:
        plate, _ = room_plate(video, width=width)
    plate = np.asarray(plate, dtype=np.float32)
    pairs = _sampled_frames(video, n_samples, width)
    if not pairs:
        return noise_floor(np.zeros(0), **kwargs)

    background, foreground = [], []
    for previous, current in pairs:
        difference = np.abs(current - previous)
        occupied = np.abs(current - plate) > tolerance
        background.append(difference[~occupied])
        foreground.append(difference[occupied])
    return noise_floor(np.concatenate(background) if background else np.zeros(0),
                       np.concatenate(foreground) if foreground else np.zeros(0),
                       quantile=quantile, **kwargs)


def _grey_stream(video, width):
    """Greyscale frames at `width`, in decode order, one at a time."""
    import av
    import cv2

    container = av.open(str(video))
    stream = container.streams.video[0]
    stream.thread_type = "AUTO"
    try:
        for frame in container.decode(stream):
            g = frame.to_ndarray(format="gray")
            h = max(1, int(g.shape[0] * width / g.shape[1]))
            yield cv2.resize(g, (width, h)).astype(np.float32)
    finally:
        container.close()


def motion_vector_floor(video, plate=None, quantile: float = 0.99,
                        width: int = 320, tolerance: float = 12.0,
                        deterministic: bool = False, **kwargs) -> dict:
    """The motion-vector gate this encode implies, in pixels of displacement.

    The same principle in the units a displacement has. Vectors landing in cells with
    nobody in front of them are the encoder spending bits on rate rather than on
    movement.

    Note that H.264 codes to quarter-pel, so a gate at or below 0.25 px cannot remove
    anything: 0.25 is the smallest non-zero displacement the format can express.

    **Two decodes, walked in step.** Occupancy has to be read frame by frame, and the
    vector reader skips the IDCT --- which is what makes it fast and its picture
    unusable. Averaging occupancy over the recording instead was tried and is wrong for
    the same reason a swept map is not an instantaneous one: it marks the dancer's whole
    path occupied at every moment, so most of the "foreground" is cells the dancer is not
    in, and the estimate refuses footage it should accept. Neither stream is held in
    memory beyond the frame in hand.

    Args:
        video: Path to the video.
        plate (optional): The room, from `room_plate`. Measured here when not given.
        quantile (float): Where in the background's tail the gate sits.
        width (int): Working width for the plate.
        tolerance (float): Difference from the plate counting as occupied.
        deterministic (bool): Decode single-threaded, so the answer repeats exactly.
        **kwargs: Passed to `noise_floor`.

    Returns:
        dict: As `noise_floor`, with `threshold` in pixels of displacement.
    """
    import cv2

    from musicalgestures._motionvectors import motion_vector_grid
    from musicalgestures._plate import room_plate

    if plate is None:
        plate, _ = room_plate(video, width=width)
    plate = np.asarray(plate, dtype=np.float32)

    #: Bounded, not exhaustive: a 2-hour recording offers hundreds of millions of
    #: magnitudes and keeping them all is 8 GB; a uniform 2-million sample of each
    #: side estimates a 0.99 quantile to well under a percent.
    background, foreground = BoundedSample(seed=1), BoundedSample(seed=2)
    seen = False
    pictures = _grey_stream(video, width)
    for (vx, vy, _, _, is_p), picture in zip(
            motion_vector_grid(str(video), deterministic=deterministic), pictures):
        if not is_p:
            continue
        seen = True
        length = np.hypot(vx, vy)
        occupied = cv2.resize((np.abs(picture - plate) > tolerance).astype(np.uint8),
                              (length.shape[1], length.shape[0]),
                              interpolation=cv2.INTER_AREA) > 0
        background.add(length[~occupied])
        foreground.add(length[occupied])
    if not seen:
        return noise_floor(np.zeros(0), **kwargs)
    return noise_floor(background.values(), foreground.values(),
                       quantile=quantile, **kwargs)

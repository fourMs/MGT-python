"""The empty room, and where the people are relative to it.

A long recording of a room contains the room. Recovering it gives two things: a background
to subtract, and an **occupancy** signal saying how much of the frame anybody filled --- a
different question from quantity of motion, and one motion cannot answer. A dancer standing
still has no motion and plenty of occupancy.

**Median over frames, never a mean.** A mean keeps a faint ghost of the dancers everywhere
they went, and subtracting a ghost leaves holes shaped like people. The median discards
whatever is present in fewer than half the samples, which is exactly what somebody crossing
a room is, and keeps whatever is usually there, which is exactly what a chair is.

**Then refine once, and check the refinement did not make things worse.** The second pass
re-takes the median over the emptiest tenth of the samples --- the frames most like the
first plate --- which tightens the plate where passing traffic left residue. What it cannot
do is remove somebody who stood in one place for most of the recording: no selection of
frames recovers a room that no frame shows. Worse, on material where the subject rarely
leaves --- standstill recordings --- the look-alike frames are exactly the ones with the
subject in place, and re-taking the median over them makes the subject solid where the
full sample had washed them out. That failure is detectable at the output: under a median
first pass the kept frames are the ones that AGREE with the plate, so a refinement that
changes the room materially is concentrating, not cleaning. `room_plate` measures that
change and hands back the unrefined plate with a warning when it is material.

Occupancy tolerates downsampling that segmentation does not. Nothing here needs full
resolution, and a few hundred pixels wide is plenty.
"""
from __future__ import annotations

import numpy as np

__all__ = ["sample_frame_indices", "plate_from_stack", "occupancy_from_plate",
           "refine_indices", "room_plate", "occupancy_track",
           "restless_map", "restless_regions"]


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
    idx: np.ndarray = np.unique(np.linspace(0, n_frames - 1, n_samples).astype(int))
    return idx


def plate_from_stack(stack) -> np.ndarray:
    """The room, as the per-pixel median over a stack of frames.

    Args:
        stack: Frames, shape (n, h, w) or (n, h, w, c).

    Returns:
        np.ndarray: One frame, the median.
    """
    a = np.asarray(stack, dtype=float)
    plate: np.ndarray = np.median(a, axis=0)
    return plate


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


def refine_indices(diffs, keep_fraction: float = 0.10,
                   stratify: bool = True) -> np.ndarray:
    """Which sampled frames to rebuild the plate from: the emptiest, spread over time.

    The smallest differences are the emptiest frames, the ones with least in front of
    the room --- a reading that holds only while the first plate is mostly empty. Where
    the subject stood in place through most of the recording, the frames most like the
    plate are the ones with the subject in them, and this selection inverts; that is
    caught downstream, where `room_plate` checks what the refinement did to the plate
    rather than trusting the selection.

    **But the emptiest frames cluster.** They fall in whatever stretch nobody was
    working --- a break, a setup, a pack-down --- and anything standing in the room then
    goes into the plate as though it were furniture. On one recording a stepladder stood
    still for ten minutes of a two-hour session, those frames were the emptiest by a
    wide margin, and the ladder became part of "the room" for every occupancy figure
    afterwards, reading as a body 18.6 per cent of the time where it was not.

    So the default takes **the emptiest frame from each of `k` equal stretches of the
    recording** rather than the emptiest `k` overall. The choice is still made on
    emptiness; it simply cannot all come from one place. `stratify=False` restores the
    older behaviour.

    Args:
        diffs: One number per sampled frame, how much it differs from the first plate.
        keep_fraction (float): Fraction to keep. Defaults to 0.10.
        stratify (bool): Spread the choice over the recording. Defaults to True.

    Returns:
        np.ndarray: Indices into `diffs`, ascending. **At least two**, because a median
        over one frame is that frame and not a plate.
    """
    d = np.asarray(diffs, dtype=float).ravel()
    if len(d) == 0:
        return np.zeros(0, dtype=int)
    k = max(2, min(len(d), int(round(len(d) * float(keep_fraction)))))
    if not stratify:
        keep: np.ndarray = np.sort(np.argsort(d)[:k])
        return keep
    #: One winner per stretch. `array_split` handles a frame count that does not divide
    #: by k, which is the ordinary case.
    chosen = [int(block[np.argmin(d[block])])
              for block in np.array_split(np.arange(len(d)), k) if len(block)]
    return np.array(sorted(set(chosen)), dtype=int)


def plate_spread(indices, n_frames: int) -> float:
    """How much of the recording the plate's frames were drawn from, 0 to 1.

    A plate built from one stretch describes the room during that stretch. This is what
    `room_plate` checks itself against before handing one back.

    Args:
        indices: The frame indices the plate was built from.
        n_frames (int): Frames in the recording.

    Returns:
        float: The span the chosen frames cover, as a fraction of the recording. 0 when
        fewer than two frames were used.
    """
    idx = np.asarray(indices, dtype=float).ravel()
    if idx.size < 2 or n_frames <= 0:
        return 0.0
    return float((idx.max() - idx.min()) / float(n_frames))


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
    frames: np.ndarray = np.array(out) if out else np.zeros((0, 1, 1))
    return frames


def room_plate(video, n_samples: int = 400, width: int = 320,
               keep_fraction: float = 0.10, refine: bool = True,
               stratify: bool = True, min_spread: float = 0.5,
               max_refine_change: float = 0.02):
    """The empty room, from a two-pass median over sampled frames.

    Args:
        video: Path to the video.
        n_samples (int): Frames to sample. Defaults to 400.
        width (int): Working width in pixels. Defaults to 320; occupancy tolerates
            downsampling that segmentation does not.
        keep_fraction (float): Fraction of samples the second pass keeps.
        refine (bool): Take the second pass. Defaults to True.
        stratify (bool): Spread the second pass over the recording rather than taking
            the globally emptiest frames, which cluster in breaks and setups and carry
            whatever was standing in the room then into the plate. Defaults to True.
        min_spread (float): Warn when the frames used span less than this fraction of
            the recording, since such a plate describes one stretch rather than the
            room. Defaults to 0.5.
        max_refine_change (float): Fall back to the unrefined plate, with a warning,
            when refinement changed more than this fraction of it. The kept frames are
            the ones that agree with the first plate, so a large change means they
            agree on something the full sample rejected --- on standstill material,
            the subject, made solid. Defaults to 0.02, above a body's residue and
            below a body.

    Returns:
        tuple: (plate, indices_used). Check `plate_spread(indices_used, n_frames)` when
        the plate matters: a low value means the room it describes is one moment's.
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
    keep = refine_indices(diffs, keep_fraction, stratify=stratify)
    used = idx[keep]
    refined = plate_from_stack(stack[keep])
    changed = occupancy_from_plate(refined, plate)
    if changed > max_refine_change:
        import warnings
        warnings.warn(
            f"refinement changed {changed * 100:.1f} per cent of the plate, which under "
            f"a median first pass means concentrating something the full sample had "
            f"washed out rather than cleaning; returning the unrefined plate. On "
            f"material where the subject rarely leaves the frame, pass refine=False",
            RuntimeWarning, stacklevel=2)
        return plate, idx
    spread = plate_spread(used, n_frames)
    if spread < min_spread:
        import warnings
        warnings.warn(
            f"the plate was built from frames spanning {spread * 100:.0f} per cent of "
            f"the recording, so it describes that stretch rather than the room; "
            f"anything standing there will be treated as furniture",
            RuntimeWarning, stacklevel=2)
    return refined, used


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


def restless_map(stack) -> np.ndarray:
    """How much each pixel changes across the sampled frames, robustly.

    **Median absolute deviation, not range.** A screen showing a video call changes in
    nearly every frame; a dancer occupies a given pixel occasionally. Both have a large
    range, so a range-based measure marks them alike --- and masking the dancer along with
    the screen is worse than masking nothing. The median deviation separates them: it is
    large only where change is the pixel's normal state.

    Args:
        stack: Frames, shape (n, h, w).

    Returns:
        np.ndarray: One value per pixel, in the image's own units.
    """
    a = np.asarray(stack, dtype=float)
    if a.ndim == 4:
        a = a.mean(axis=3)
    med = np.median(a, axis=0)
    mad: np.ndarray = np.median(np.abs(a - med), axis=0)
    return mad


def restless_regions(stack, quantile: float = 0.98, min_value: float = 2.0) -> np.ndarray:
    """A mask of the pixels that change constantly, whatever is or is not in front of them.

    Args:
        stack: Frames, shape (n, h, w).
        quantile (float): How far up the deviation distribution the cut sits. Defaults to
            0.98, roughly the brightest two per cent of the frame.
        min_value (float): An absolute floor, in the image's units. **Without it a
            quantile of a flat map marks the top slice of nothing**, so a perfectly still
            recording would come back with two per cent of itself masked.

    Returns:
        np.ndarray: A boolean mask the shape of one frame. It cannot cover the whole
        frame: the cut is at least the map's own minimum, so the quietest pixel is always
        outside it. That is a property of the arithmetic rather than a guard --- an
        explicit check for it was written, found unreachable by mutation, and removed,
        because defensive code no test can reach hides the fault it pretends to catch.
    """
    m = restless_map(stack)
    if m.size == 0:
        empty: np.ndarray = np.zeros_like(m, dtype=bool)
        return empty
    cut = max(float(np.quantile(m, float(quantile))), float(min_value))
    mask: np.ndarray = m > cut
    return mask


def texture_mask(image, grid: int = 16, percentile: float = 40.0):
    """Which cells of a picture carry enough texture to trust motion vectors on.

    An encoder's motion search is unconstrained where nothing textures the block:
    every candidate vector predicts a flat region equally well, so the vectors there
    are rate decisions that propagate from wherever real motion is, not measurements.
    Measured on a corpus whose one room hangs a dark curtain near the lens, the
    plate's local texture predicted the accumulated vector motion at Spearman -0.6,
    and masking the low-texture cells removed a negative motion-to-dwell correlation
    that had made the maps unreadable, while leaving well-textured rooms untouched.

    The threshold is a percentile of this picture's own cell textures, never an
    absolute number, so the mask adapts to any room and any exposure.

    Args:
        image: A greyscale picture, typically the room plate the maps are built
            against, as (rows, cols).
        grid (int): Cell size in pixels; 16 matches the macroblock lattice the
            vector maps accumulate on. Defaults to 16.
        percentile (float): Cells whose standard deviation falls below this
            percentile of all cells' are masked. Defaults to 40.

    Returns:
        np.ndarray: Boolean (rows, cols) cell grid, True where vectors are evidence.
    """
    import numpy as np

    a = np.asarray(image, dtype=np.float64)
    rows, cols = a.shape[0] // grid, a.shape[1] // grid
    stds = np.array([[a[i * grid:(i + 1) * grid, j * grid:(j + 1) * grid].std()
                      for j in range(cols)] for i in range(rows)])
    threshold = np.percentile(stds, percentile)
    #: Strictly above, so that a picture whose low percentile is exactly zero --- half
    #: the frame perfectly flat --- still masks the flat cells. A picture where nothing
    #: exceeds the threshold keeps everything, since uniformly textured is not the
    #: fault this mask exists for.
    mask = stds > threshold
    return mask if mask.any() else stds >= threshold

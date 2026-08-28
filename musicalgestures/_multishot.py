"""Many moments of one recording in a single picture: a chronophotograph.

The room is recovered as a plate --- what was there before anybody came in --- bodies are
cut out of frames spread through the recording, and all of them are laid back onto it.
One image then carries where somebody was, how they were shaped, and how far apart the
moments were. It answers nothing a motiongram answers and shows something no gram shows.

**Related to `stroboscope()`, and different in two ways that matter.** That method
composites silhouettes at EVENLY SAMPLED times onto a MEAN average frame, and tints each
by time. This one chooses moments for spatial separation and composites onto the median
`room_plate`. Even sampling is what puts bodies on top of each other, and a mean average
keeps a faint ghost of everyone who crossed. Use `stroboscope()` when the time order
matters and MediaPipe segmentation is wanted; use this when the bodies must not overlap.

**Frames are chosen for separation, not at regular intervals.** Evenly spaced frames put
bodies on top of each other as often as not, and two overlapping silhouettes read as one
smear rather than as two moments. Candidates are therefore scored by how far each sits
from every body already placed, and the greediest spacing wins. That is a picture-making
decision rather than a measurement, and it is made explicitly here rather than by luck.

**More bodies is not simply better.** A room is finite, so each body after the first takes
the emptiest remaining spot and the spots run out. Past a dozen or so they overlap whatever
the selection does. Eight suits a studio; a long section with a lot of travel takes more.

**It assumes a subject that MOVES THROUGH SPACE, and it should.** Separation is spatial, so
a subject who stays put gives it nothing to separate: run on a seated pianist it returns
heads and hands stacked in one place, because a static torso is in the plate and only the
moving parts survive the mask. That is not a fault to tune away --- the picture is
reflecting what the recording contains. For travelling subjects it is a chronophotograph;
for a seated one it becomes an overlay of moving limbs, which is a different object and
worth knowing you are looking at.

**The mask is the weak point and is treated as such.** A body is whatever differs from the
plate by more than the tolerance --- which is also true of their shadow, of a screen
showing a video call, and of anything the plate got wrong. Shadows are rejected on the
RATIO of brightness rather than its difference, since a shadow keeps the colour of the
floor it falls on and only darkens it; fragments too small to be a person are dropped; and
the edge is feathered so a cut-out does not read as a sticker.

**It inherits the plate's faults exactly.** Build the plate with `stratify=True`, which is
the default, and heed the warning it raises when the frames it used cluster in time: a prop
that stood in the room through a break will otherwise appear here as a hole or a ghost.

**And it composites whoever is in shot.** Somebody sitting at a laptop differs from the
room like anybody else. Where that matters, mask the region or restrict the span.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:                              # pragma: no cover - typing only
    import musicalgestures
    from musicalgestures._utils import MgImage

__all__ = ["multishot", "choose_spaced", "body_mask", "mg_multishot", "mg_plate"]

TOLERANCE = 26.0        #: difference from the plate counting as somebody, 8-bit
SHADOW_RATIO = 0.55     #: darker than this share of the plate's brightness is a shadow
#: What a PERSON looks like in a frame, which is what this is optimised for. These are
#: defaults and not laws: they assume a whole body at studio distance, and a closer
#: camera, a wider room or a seated subject wants them moved. They are parameters of
#: `multishot` for that reason rather than constants, because a bound that silently
#: matches nothing returns an empty result rather than an error, which reads as "nothing
#: happened here".
MIN_AREA = 0.004        #: a body covers at least this much of the frame
MAX_AREA = 0.06         #: and at most this much, above which it is somebody at the lens
MAX_BORDER = 0.12       #: reject a body with more than this share of it against an edge
FEATHER = 9             #: edge softening, in pixels


def body_mask(frame, plate, tolerance: float = TOLERANCE,
              shadow_ratio: float = SHADOW_RATIO, min_area: float = MIN_AREA):
    """Where somebody is, with shadow and speckle taken out.

    Args:
        frame: One frame, colour, as read.
        plate: The room, same shape, from `room_plate`.
        tolerance (float): Difference counting as somebody, on an 8-bit scale.
        shadow_ratio (float): Brightness ratio below which a difference is read as shadow.
        min_area (float): Sets the size below which a connected piece is not a person and
            is dropped. Scaled from the same human-body assumption as `multishot`'s.

    Returns:
        tuple: `(mask, area)` --- the mask as uint8, and the fraction of the frame it
        covers, so a caller can reject a frame without paying for the rest of the work.
    """
    import cv2

    difference = np.abs(frame.astype(np.int16) - plate.astype(np.int16)).max(axis=2)
    mask = (difference > tolerance).astype(np.uint8)

    #: A shadow differs from the plate as much as a body does. What separates them is that
    #: a shadow keeps the floor's colour and only scales its brightness, so the RATIO to
    #: the plate is near-constant and well below one, where a body's is not.
    luma = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    base = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY).astype(np.float32)
    ratio = luma / np.maximum(base, 1.0)
    mask[(ratio > shadow_ratio) & (ratio < 1.0) & (difference < tolerance * 2.2)] = 0

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))

    #: Only pieces big enough to be a person. Rate noise and a flickering screen both
    #: survive everything above, and both are small.
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    keep = np.zeros_like(mask)
    smallest = min_area * mask.size * 0.25
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= smallest:
            keep[labels == i] = 1
    return keep, float(keep.mean())


def _border_share(mask) -> float:
    """How much of a body lies against the frame edge.

    A silhouette touching an edge is somebody leaving the shot, and compositing one puts
    half a body in the picture. Cheaper to reject than to matte.
    """
    edge = np.zeros_like(mask)
    edge[:6, :] = edge[-6:, :] = edge[:, :6] = edge[:, -6:] = 1
    total = mask.sum()
    return float((mask & edge).sum()) / total if total else 1.0


def choose_spaced(candidates, n_bodies: int):
    """Which moments to composite: each as far as possible from those already placed.

    Args:
        candidates: Dicts carrying at least `centroid` (x, y), `area` and `index`.
        n_bodies (int): How many to place. Fewer are returned if there are fewer.

    Returns:
        list: The chosen candidates, **in time order**, since a composite lays later
        bodies over earlier ones and that order is not cosmetic.
    """
    if not candidates:
        return []
    #: Tracked by POSITION, not by dict equality. `c not in chosen` compares dicts, and
    #: these carry numpy arrays: CPython short-circuits on the first unequal value, so it
    #: works only while every candidate has a distinct `index` -- and `linspace` over
    #: more candidates than the video has frames produces duplicates. Two candidates
    #: sharing an index then reach the array comparison and raise "truth value of an
    #: array is ambiguous", on short videos only.
    taken = {int(np.argmax([c["area"] for c in candidates]))}
    while len(taken) < n_bodies and len(taken) < len(candidates):
        best, best_distance = None, -1.0
        for i, c in enumerate(candidates):
            if i in taken:
                continue
            distance = min((c["centroid"][0] - candidates[j]["centroid"][0]) ** 2
                           + (c["centroid"][1] - candidates[j]["centroid"][1]) ** 2
                           for j in taken)
            if distance > best_distance:
                best, best_distance = i, distance
        if best is None:
            break
        taken.add(best)
    return sorted((candidates[i] for i in taken), key=lambda c: c["index"])


def multishot(video, n_bodies: int = 8, n_candidates: int = 120, start=None, end=None,
              plate=None, width: int = 960, tolerance: float = TOLERANCE,
              feather: int = FEATHER, min_area: float = MIN_AREA,
              max_area: float = MAX_AREA, max_border: float = MAX_BORDER,
              shadow_ratio: float = SHADOW_RATIO):
    """A chronophotograph of one recording, or of one span of it.

    Args:
        video: Path to the video.
        n_bodies (int): Moments to place. Defaults to 8. Past a dozen or so they overlap
            whatever the selection does, because a room is finite.
        n_candidates (int): Frames examined before choosing. Defaults to 120.
        start, end (float, optional): Seconds. Restrict to one section --- **worth doing**,
            since a whole recording is usually mostly setup and the picture fills with
            people standing about rather than with the work.
        plate (optional): The room, from `room_plate`, in colour at `width`. Measured here
            when not given.
        width (int): Working width. Defaults to 960.
        tolerance (float): Difference from the plate counting as somebody.
        feather (int): Edge softening in pixels, so a cut-out does not read as a sticker.
        min_area, max_area (float): How much of the frame a body may cover, as a
            fraction. The defaults --- 0.4 to 6 per cent --- describe a whole person at
            studio distance, which is what this is tuned for. **Move them when the
            framing differs**: a closer camera or a larger subject needs `max_area`
            raised, a wide room or a distant subject needs `min_area` lowered. Too
            narrow a range yields no candidates and returns None, which looks like an
            empty room rather than a setting that matched nothing.
        max_border (float): Reject a body with more than this share of it against a frame
            edge, since compositing one puts half a body in the picture.
        shadow_ratio (float): Brightness ratio below which a difference reads as shadow.

    Returns:
        tuple: `(picture, plate)`, both BGR. **`picture` is None** when no frame held a
        body of a plausible size --- an empty room is not a result and is not returned as
        one.
    """
    import cv2

    from musicalgestures._plate import room_plate

    capture = cv2.VideoCapture(str(video))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0

    if plate is None:
        grey, used = room_plate(video, n_samples=min(300, max(8, total)), width=width)
        #: The plate is greyscale and compositing needs colour, so it is rebuilt in colour
        #: from THE VERY FRAMES the grey one used --- not from a fresh draw, which would
        #: be a different room.
        stack = []
        for i in used:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(i))
            ok, f = capture.read()
            if ok:
                h = max(1, int(f.shape[0] * width / f.shape[1]))
                stack.append(cv2.resize(f, (width, h)))
        plate = np.median(np.asarray(stack, dtype=np.float32), axis=0).astype(np.uint8)

    first = int((start or 0) * fps)
    last = int(end * fps) if end else total

    candidates = []
    for index in np.linspace(first, max(first + 1, last - 1),
                             n_candidates).astype(int):
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
        ok, frame = capture.read()
        if not ok:
            continue
        h = max(1, int(frame.shape[0] * width / frame.shape[1]))
        frame = cv2.resize(frame, (width, h))
        mask, area = body_mask(frame, plate, tolerance, shadow_ratio)
        if not (min_area <= area <= max_area) or _border_share(mask) > max_border:
            continue
        ys, xs = np.nonzero(mask)
        candidates.append({"index": int(index), "frame": frame, "mask": mask,
                           "area": area, "centroid": (float(xs.mean()),
                                                      float(ys.mean()))})
    capture.release()
    if not candidates:
        return None, plate

    canvas = plate.astype(np.float32).copy()
    for c in choose_spaced(candidates, n_bodies):
        alpha = cv2.GaussianBlur(c["mask"].astype(np.float32),
                                 (feather * 2 + 1, feather * 2 + 1), 0)[..., None]
        canvas = c["frame"].astype(np.float32) * alpha + canvas * (1 - alpha)
    return np.clip(canvas, 0, 255).astype(np.uint8), plate


def mg_multishot(self: "musicalgestures.MgVideo", n_bodies: int = 8,
                 n_candidates: int = 120, start=None, end=None, width: int = 960,
                 tolerance: float = TOLERANCE, feather: int = FEATHER,
                 min_area: float = MIN_AREA, max_area: float = MAX_AREA,
                 max_border: float = MAX_BORDER, shadow_ratio: float = SHADOW_RATIO,
                 target_name: str | None = None, overwrite: bool = True) -> "MgImage":
    """Many moments of this recording in one picture, as an `MgImage`.

    The method form of `multishot`, so it composes with the rest of the object API. See
    that function for what the arguments mean and for how this differs from
    `stroboscope()`.

    Args:
        target_name (str, optional): Output name. Defaults to "_multishot.png".
        overwrite (bool, optional): Overwrite or auto-increment. Defaults to True.

    Returns:
        MgImage: the composite.

    Raises:
        ValueError: when no frame held a body of a plausible size. An empty room is not
            a result, and returning one silently would look like the recording was empty
            rather than like the size bounds matched nothing.
    """
    import cv2

    from musicalgestures._utils import MgImage, resolve_filename

    target_name = resolve_filename(self.of, "_multishot.png", target_name, overwrite)
    picture, _ = multishot(self.filename, n_bodies=n_bodies, n_candidates=n_candidates,
                           start=start, end=end, width=width, tolerance=tolerance,
                           feather=feather, min_area=min_area, max_area=max_area,
                           max_border=max_border, shadow_ratio=shadow_ratio)
    if picture is None:
        raise ValueError(
            f"no frame of {self.filename} held a body covering between "
            f"{min_area * 100:.1f} and {max_area * 100:.1f} per cent of the frame. "
            f"Move `min_area`/`max_area` if the framing differs from a whole person at "
            f"studio distance.")
    cv2.imwrite(target_name, picture)
    self.multishot_image = MgImage(target_name)
    return self.multishot_image


def mg_plate(self: "musicalgestures.MgVideo", width: int = 960, n_samples: int = 300,
             stratify: bool = True, target_name: str | None = None,
             overwrite: bool = True) -> "MgImage":
    """The empty room this recording was made in, as an `MgImage`.

    The method form of `room_plate`: a per-pixel median over sampled frames, twice, with
    the second pass spread over the recording so that anything standing there through a
    break does not become furniture.

    **In colour, from the frames the grey pass chose** --- not a fresh draw, which would
    be a different room.

    Args:
        width (int): Working width. Defaults to 960; pass the video's own width for a
            full-resolution room.
        n_samples (int): Frames to sample. Defaults to 300.
        stratify (bool): Spread the second pass over the recording. Defaults to True.
        target_name (str, optional): Output name. Defaults to "_plate.png".
        overwrite (bool, optional): Overwrite or auto-increment. Defaults to True.

    Returns:
        MgImage: the room.
    """
    import cv2

    from musicalgestures._plate import room_plate
    from musicalgestures._utils import MgImage, resolve_filename

    target_name = resolve_filename(self.of, "_plate.png", target_name, overwrite)
    _, used = room_plate(self.filename, n_samples=n_samples, width=width,
                         stratify=stratify)
    capture = cv2.VideoCapture(self.filename)
    stack = []
    for i in used:
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, frame = capture.read()
        if ok:
            h = max(1, int(frame.shape[0] * width / frame.shape[1]))
            stack.append(cv2.resize(frame, (width, h)))
    capture.release()
    if not stack:
        raise ValueError(f"no frames could be read from {self.filename}")
    plate = np.median(np.asarray(stack, dtype=np.float32), axis=0).astype(np.uint8)
    cv2.imwrite(target_name, plate)
    self.plate_image = MgImage(target_name)
    return self.plate_image

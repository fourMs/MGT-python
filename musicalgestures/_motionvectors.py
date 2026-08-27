import os
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING

import musicalgestures
from musicalgestures._utils import generate_outfilename, resolve_filename, get_length, ffmpeg_cmd

if TYPE_CHECKING:
    import numpy as np

    from musicalgestures._mglist import MgList
    from musicalgestures._utils import MgFigure, MgImage

#: PyAV hands back the AVPictureType as an int rather than a name.
_PICTURE_TYPES = {1: "I", 2: "P", 3: "B"}

#: The lattice the spatial views are built on. Codecs subdivide below this --- H.264 goes
#: to 4x4 --- but a common grid is what makes frames stackable, and 16 is the macroblock
#: size every inter-frame codec here agrees on.
_GRID = 16


def mg_motionvectors(self: "musicalgestures.MgVideo", target_name=None, overwrite=True) -> "musicalgestures.MgVideo":
    """
    Renders a video visualising the motion vectors encoded in the input video.

    Inter-frame codecs (MPEG-1/2/4, H.264, H.265, …) store motion vectors that describe
    how macroblocks move between frames. This method uses FFmpeg's ``codecview`` filter
    (with ``-flags2 +export_mvs``) to draw those vectors as arrows on top of the video,
    giving a quick, decoder-level view of motion without any re-computation.

    NB: Only codecs that actually carry motion vectors will show arrows. Intra-only
    formats (e.g. MJPEG, common in ``.avi`` files) have none — convert to an inter-frame
    codec first (e.g. via ``show(mode='notebook')`` which makes an mp4, or any mp4/h264
    source) to see motion vectors.

    Args:
        target_name (str, optional): Target output name for the video. Defaults to None
            (which uses the input filename with the suffix "_motionvectors").
        overwrite (bool, optional): Whether to allow overwriting existing files or to
            automatically increment the target filename. Defaults to True.

    Returns:
        MgVideo: An MgVideo pointing to the rendered motion-vector video.
    """
    of, fex = os.path.splitext(self.filename)

    target_name = resolve_filename(of, '_motionvectors' + fex, target_name, overwrite)

    # -flags2 +export_mvs must precede -i so the decoder exports motion vectors;
    # codecview then draws them (pf=P-frame forward, bf/bb=B-frame forward/backward).
    cmd = [
        'ffmpeg', '-y', '-flags2', '+export_mvs', '-i', self.filename,
        '-vf', 'codecview=mv=pf+bf+bb', '-q:v', '3', target_name,
    ]
    ffmpeg_cmd(cmd, get_length(self.filename), pb_prefix='Rendering motion vectors:')

    self.motionvectors_video = musicalgestures.MgVideo(
        target_name, color=self.color, returned_by_process=True)
    return self.motionvectors_video


@dataclass
class MgMotionVectorData:
    """One row per decoded frame, as arrays.

    `picture_type` is here because it decides whether the rest is usable. Measured on a
    100-minute corpus against exact frame-differenced quantity of motion, the magnitude
    below correlates at r = 0.87 on P-frames alone and r = 0.54 once B-frames are pooled
    in, so a caller who ignores this field gets a much worse signal than the codec is
    offering. Filtering to `picture_type == 'P'` costs three quarters of the frames and
    is usually the right trade.
    """
    time: "np.ndarray"
    picture_type: "np.ndarray"
    n_vectors: "np.ndarray"
    magnitude: "np.ndarray"
    median_dx: "np.ndarray"
    median_dy: "np.ndarray"


def mg_motionvectordata(self: "musicalgestures.MgVideo") -> "MgMotionVectorData":
    """Read the motion vectors the codec already computed, as numbers rather than arrows.

    `motionvectors()` renders these as a video to look at. This returns them as data, and
    the difference in cost is the point: an inter-frame codec has already searched for the
    displacement of every macroblock, so reading its answer is close to free, while
    differencing pixels does the same search again in Python. On a 103-minute recording,
    decoding took 2.2 s and decoding with the vectors took 2.7 s, against 27 minutes for
    the frame-differenced quantity of motion.

    **What it is not.** The vectors are the encoder's decisions, not a measurement of the
    scene: an encoder is entitled to any vector that predicts the block cheaply, and on
    flat or still regions it will pick one that has nothing to do with movement. The
    result tracks quantity of motion well where there is motion to track and poorly where
    there is not --- on that same corpus, median r = 0.86 in windows with movement and
    0.57 in windows without. Re-encoded proxies carry their proxy encoder's vectors, not
    the camera's.

    **Vectors are normalised to point forward in time.** A B-frame may predict a block
    from a later frame, which reverses the sign; dividing by the vector's `source`
    corrects that, so a block moving right reads as positive whichever way it was
    predicted. Without it a B-frame's vectors point backwards half the time and averaging
    them gives roughly nothing.

    **What that normalisation cannot fix is the reference distance.** `source` records
    only the direction, plus or minus one, never how many frames away the reference was.
    An encoder with multiple reference frames will predict some blocks from two or four
    frames back, and those read as two or four times the per-frame displacement. Measured
    on a block moving 4 pixels per frame, 53 per cent of vectors came back as 4 and the
    rest as 8 or 16, with `source` at plus or minus one throughout. So `median_dx` and
    `median_dy` are medians for a reason and are robust to it; `magnitude` is a sum and is
    not, and inherits the over-count. Treat `magnitude` as a quantity to correlate against
    itself over time, which is what it was validated for, rather than as pixels per
    second.

    Returns:
        MgMotionVectorData: `time` in seconds, `picture_type` as 'I'/'P'/'B',
        `n_vectors`, `magnitude` (the area-weighted sum of displacement, which is the
        quantity to compare against quantity of motion), and `median_dx` / `median_dy`
        (the typical displacement in pixels **of the blocks that moved** --- taken over
        every block instead, these would report the still background's zero however fast
        the one moving thing was going). Frames with no vectors, which includes every
        intra frame, read as zero throughout.

    Raises:
        ImportError: if PyAV is not installed. ffprobe reports that the side data exists
            but will not print the vectors themselves, and ffmpeg has no numeric dump, so
            there is no route to these numbers through the command line.
    """
    try:
        import av
    except ImportError as exc:                       # pragma: no cover - trivial branch
        raise ImportError(
            "Reading motion vectors as data needs PyAV. Install it with "
            "`pip install musicalgestures[motionvectors]`, or `pip install av`. "
            "The rendering version, MgVideo.motionvectors(), needs only ffmpeg."
        ) from exc
    import numpy as np

    container = av.open(self.filename)
    stream = container.streams.video[0]
    stream.thread_type = "AUTO"
    #: AV_CODEC_FLAG2_EXPORT_MVS. PyAV exposes flags2 as a plain int and does not
    #: re-export the constant, so it is written out rather than imported.
    stream.codec_context.flags2 |= 1 << 28

    time: list[float] = []
    kinds: list[str] = []
    counts: list[int] = []
    magnitude: list[float] = []
    med_dx: list[float] = []
    med_dy: list[float] = []
    for frame in container.decode(stream):
        time.append(float(frame.pts * stream.time_base) if frame.pts is not None
                    else (time[-1] if time else 0.0))
        kinds.append(_PICTURE_TYPES.get(int(frame.pict_type), "?"))
        vectors = frame.side_data.get("MOTION_VECTORS")
        table = vectors.to_ndarray() if vectors is not None else None
        if table is None or len(table) == 0:
            counts.append(0)
            magnitude.append(0.0)
            med_dx.append(0.0)
            med_dy.append(0.0)
            continue
        scale = np.maximum(table["motion_scale"].astype(np.float64), 1)
        #: Two corrections in one division, and both are needed to get a number that
        #: means "which way did this move, per frame".
        #:
        #: ffmpeg defines the vector as `src = dst + motion / motion_scale`, so it
        #: points from where the block is now back to where it came from: content
        #: travelling right carries a NEGATIVE motion_x. And `source` is negative when
        #: the reference is an earlier frame, positive when it is a later one, with its
        #: magnitude the distance in frames. Dividing by `source` undoes both --- the
        #: backwards sense of the vector and the backwards sense of a future reference
        #: cancel --- and scales a multi-frame prediction down to one frame.
        source = table["source"].astype(np.float64)
        source[source == 0] = -1
        dx = table["motion_x"].astype(np.float64) / scale / source
        dy = table["motion_y"].astype(np.float64) / scale / source
        area = table["w"].astype(np.float64) * table["h"]
        counts.append(len(table))
        magnitude.append(float((np.hypot(dx, dy) * area).sum()))
        #: Over the blocks that moved, not over every block. Most of a frame is
        #: usually still, so a median over all blocks is the background's zero however
        #: fast the one moving thing is going, which is not a useful answer to "which
        #: way did it move". Threshold-free: a block counts as moving if the encoder
        #: gave it a displacement at all.
        moving = (dx != 0) | (dy != 0)
        med_dx.append(float(np.median(dx[moving])) if moving.any() else 0.0)
        med_dy.append(float(np.median(dy[moving])) if moving.any() else 0.0)
    codec = stream.codec_context.name
    container.close()

    if counts and not any(counts):
        #: An array of zeros means "nobody moved" and "this codec carries no vectors"
        #: equally well, and the caller cannot tell them apart. ffmpeg exports vectors
        #: for H.264 and MPEG-4 Part 2; HEVC and VP9 decode fine and return none.
        warnings.warn(
            f"No motion vectors in this file: the {codec} stream decoded but carried "
            f"none, so every value below is zero. ffmpeg exports motion vectors for "
            f"H.264 and MPEG-4 Part 2, and not for HEVC, VP9 or any intra-only format. "
            f"Re-encode to H.264 to read them.",
            UserWarning, stacklevel=2)

    return MgMotionVectorData(
        time=np.asarray(time, dtype=np.float64),
        picture_type=np.asarray(kinds),
        n_vectors=np.asarray(counts, dtype=np.int64),
        magnitude=np.asarray(magnitude, dtype=np.float64),
        median_dx=np.asarray(med_dx, dtype=np.float64),
        median_dy=np.asarray(med_dy, dtype=np.float64),
    )


def motion_vector_grid(filename, deterministic=False):
    """Per-frame displacement fields at macroblock resolution, **yielded one at a time**.

    Everything spatial in this module is built on this: the history image sums it over
    time, the motiongrams reduce it along one axis per frame, the waterfall bins those.
    Decoding is the expensive part, so it happens once per view rather than once per
    frame of interest.

    **A generator, and that is not a style choice.** The first version returned the
    frames stacked into arrays of shape (frames, rows, cols). On a 100-minute 1920x1080
    recording that is 310,368 frames over a 68 by 120 grid --- 20 GB per array, and it
    built three. It ran on every clip in the test suite and would have exhausted memory
    on the first real recording. Consumers now accumulate as they go, and nothing holds
    more than one frame's grid.

    The grid is the codec's own macroblock lattice --- typically 16 pixels, sometimes 8
    or 4 within the same frame when the encoder subdivides. Vectors are painted into the
    cells their block covers, so a 16x16 block contributes to all of its cells and the
    result does not favour finely-subdivided regions for having more vectors.

    Yields:
        tuple: `(vx, vy, weight, time, is_p)` per frame, each of `vx`/`vy`/`weight`
        shaped (rows, cols). `vx`/`vy` are mean displacement per cell in pixels,
        `weight` the moved area, `time` in seconds, `is_p` whether it is a P-frame.
    """
    try:
        import av
    except ImportError as exc:                       # pragma: no cover - trivial branch
        raise ImportError(
            "Reading motion vectors as data needs PyAV. Install it with "
            "`pip install musicalgestures[motionvectors]`, or `pip install av`."
        ) from exc
    import numpy as np

    container = av.open(filename)
    stream = container.streams.video[0]
    #: FRAME-THREADED DECODING DROPS MOTION VECTORS, AND NOT THE SAME ONES TWICE.
    #: Measured on a synthetic clip, three identical runs returned 28,702, 29,649 and
    #: 29,975 vectors with threading on, and 29,975 every time with it off. On a real
    #: 1920x1080 recording the loss is 222 vectors in 25.7 million --- 0.0009 per cent,
    #: far below anything that changes a result --- but it is still not reproducible,
    #: and threading is 4.5x faster (5 minutes a session against 23). So the fast,
    #: slightly lossy path is the default for looking at material, and `deterministic`
    #: is there for anything that has to give the same answer twice.
    stream.thread_type = "NONE" if deterministic else "AUTO"
    stream.codec_context.flags2 |= 1 << 28
    #: The reconstructed picture is never looked at here --- only the side data is --- so
    #: the two most expensive reconstruction stages can be skipped. Measured at
    #: 1,279 fps against 861 on 1920x1080, with the vector count unchanged.
    try:
        stream.codec_context.options = {"skip_loop_filter": "all", "skip_idct": "all"}
    except Exception:                                # pragma: no cover - older PyAV
        pass
    width = stream.codec_context.width
    height = stream.codec_context.height
    cols = max(1, -(-width // _GRID))
    rows = max(1, -(-height // _GRID))

    previous_time = 0.0
    try:
        for frame in container.decode(stream):
            vx = np.zeros((rows, cols), np.float64)
            vy = np.zeros((rows, cols), np.float64)
            w = np.zeros((rows, cols), np.float64)
            t = (float(frame.pts * stream.time_base)
                 if frame.pts is not None else previous_time)
            previous_time = t
            is_p = _PICTURE_TYPES.get(int(frame.pict_type), "?") == "P"
            mvs = frame.side_data.get("MOTION_VECTORS")
            table = mvs.to_ndarray() if mvs is not None else None
            if table is not None and len(table):
                scale = np.maximum(table["motion_scale"].astype(np.float64), 1)
                source = table["source"].astype(np.float64)
                source[source == 0] = -1
                dx = table["motion_x"].astype(np.float64) / scale / source
                dy = table["motion_y"].astype(np.float64) / scale / source
                area = (table["w"].astype(np.float64) * table["h"])
                #: One cell per vector, by integer division, with no loop and no
                #: painting across cells.
                #:
                #: That is exact rather than approximate, because of how these codecs
                #: partition: every H.264 partition --- 16x16 down to 4x4 --- lies
                #: INSIDE a single macroblock, and MPEG-4 Part 2 uses 16x16 and 8x8. So
                #: a block never straddles a 16-pixel cell boundary, checked on a real
                #: encode: 0 of 12,130 vectors crossed one. `dst` is the block centre,
                #: so `dst // 16` is its macroblock.
                #:
                #: The loop this replaces ran once per vector. At 1920x1080 that is
                #: 8,160 macroblocks a frame, and 2.5 billion iterations over a
                #: 100-minute recording --- it worked on a 60-frame test clip and would
                #: never have finished on a session.
                r = np.clip(table["dst_y"].astype(np.int64) // _GRID, 0, rows - 1)
                c = np.clip(table["dst_x"].astype(np.int64) // _GRID, 0, cols - 1)
                flat = r * cols + c
                size = rows * cols
                w += np.bincount(flat, weights=area, minlength=size).reshape(rows, cols)
                vx += np.bincount(flat, weights=dx * area,
                                  minlength=size).reshape(rows, cols)
                vy += np.bincount(flat, weights=dy * area,
                                  minlength=size).reshape(rows, cols)
            busy = w > 0
            vx[busy] /= w[busy]
            vy[busy] /= w[busy]
            yield vx, vy, w * np.hypot(vx, vy), t, is_p
    finally:
        container.close()


def accumulate_motion_vectors(filename, p_frames_only=True, deterministic=False):
    """The whole space motion happened in, summed over the recording.

    Returns `(weight, vx, vy, coherence)`: how much movement each cell saw, the
    direction it saw on average, and how consistently that direction held.

    P-frames only by default. A B-frame's vectors are referenced over varying temporal
    distances, and pooling them into a spatial average blurs the direction that is the
    reason for accumulating vectors rather than frame differences.
    """
    import numpy as np

    total = sum_x = sum_y = sum_speed = None
    for vx, vy, weight, _, is_p in motion_vector_grid(filename, deterministic):
        if p_frames_only and not is_p:
            continue
        if total is None:
            total = np.zeros_like(weight)
            sum_x = np.zeros_like(weight)
            sum_y = np.zeros_like(weight)
            sum_speed = np.zeros_like(weight)
        total += weight
        sum_x += vx * weight
        sum_y += vy * weight
        sum_speed += np.hypot(vx, vy) * weight
    if total is None:
        z = np.zeros((1, 1))
        return z, z.copy(), z.copy(), z.copy()
    busy = total > 0
    mean_x = np.zeros_like(total)
    mean_y = np.zeros_like(total)
    coherence = np.zeros_like(total)
    mean_x[busy] = sum_x[busy] / total[busy]
    mean_y[busy] = sum_y[busy] / total[busy]
    #: How consistently this cell moved ONE way. The length of the mean vector over the
    #: mean length: 1 where every crossing went the same direction, near 0 where they
    #: cancelled. Without it a cell that saw a dancer pass back and forth all afternoon
    #: is indistinguishable from one that saw nothing but encoder noise, since both have
    #: a near-zero mean vector and an arbitrary direction.
    #:
    #: LIMIT. P-frames arrive at roughly a quarter of the frame rate, so a movement that
    #: reverses faster than a few samples per cycle is under-sampled and reads as
    #: coherent when it is not: measured on a block oscillating at 3 samples per cycle
    #: this returns 0.97, and at 12 samples per cycle it returns 0.06. On 50 fps footage
    #: that puts the honest ceiling around 1.5 Hz --- fine for a dancer crossing a room,
    #: wrong for a shaking hand.
    mean_speed = np.zeros_like(total)
    mean_speed[busy] = sum_speed[busy] / total[busy]
    moving = mean_speed > 0
    coherence[moving] = (np.hypot(mean_x, mean_y)[moving] / mean_speed[moving])
    return total, mean_x, mean_y, np.clip(coherence, 0, 1)


def mg_motionvectorhistory(self: "musicalgestures.MgVideo", mode: str = "direction",
                           colormap: str = "inferno", gamma: float = 0.5,
                           target_name: str | None = None,
                           overwrite: bool = True) -> "MgImage":
    """The whole space the motion happened in, accumulated from the codec's vectors.

    `motionhistory()` renders the Bobick--Davis image from frame differences and encodes
    *recency*; `heatmap()` accumulates where pixels changed. Neither can say which way
    anything went, because a frame difference has no sign --- somebody entering a region
    and leaving it look identical. A motion vector is a displacement, so this can, and
    that is the reason for it to exist.

    Args:
        mode (str, optional): `'direction'` colours each cell by the direction motion
            took there, hue running around the compass, with brightness for how much
            motion the cell saw. `'magnitude'` drops the direction and applies `colormap`
            to the amount alone, which is the comparable view when direction is a
            distraction. Defaults to `'direction'`.
        colormap (str, optional): Matplotlib colormap, used by `'magnitude'`. Defaults to
            `'inferno'`.
        gamma (float, optional): Applied to the accumulated amount before colouring, so
            that a few violent moments do not leave everything else black. Defaults to
            0.5.
        target_name (str, optional): Output path. Defaults to the input name with
            `_motionvectorhistory`.
        overwrite (bool, optional): Defaults to True.

    Returns:
        MgImage: the rendered image, at the video's own dimensions.

    Notes:
        Built from P-frames only, for the reason given on `motionvectordata`. And the
        vectors are the encoder's decisions: over a region with no detail every candidate
        predicts equally well, so the encoder copies whatever its neighbours used and the
        field there is inherited rather than observed. Expect that wherever the picture is
        flat.
    """
    import cv2
    import matplotlib
    import numpy as np

    from musicalgestures._utils import MgImage

    of, fex = os.path.splitext(self.filename)
    target_name = resolve_filename(of, '_motionvectorhistory.png', target_name, overwrite)

    weight, vx, vy, coherence = accumulate_motion_vectors(self.filename)
    #: Normalised against a high percentile, not the maximum. Over a long recording the
    #: distribution is heavy-tailed and dividing by the maximum leaves the typical cell
    #: close to it, so the whole frame comes out uniformly bright and shows nothing.
    ceiling = np.percentile(weight[weight > 0], 99) if (weight > 0).any() else 1.0
    amount = np.clip(weight / max(ceiling, 1e-9), 0, 1)
    if gamma and gamma != 1.0:
        amount = np.power(amount, gamma)

    if mode == "direction":
        #: Hue is the compass bearing, so opposite directions are opposite colours.
        #: Value is how much motion there was, and **saturation is how consistently it
        #: went that way**. Pinning saturation at full was the first version's mistake:
        #: it painted every cell a vivid colour whether or not the direction meant
        #: anything, and since every cell accumulates something over a hundred minutes,
        #: the result was a uniform wash. Grey now reads as "moved, but not any one
        #: way", which is the honest thing to say about most of a room.
        hue = (np.arctan2(vy, vx) + np.pi) / (2 * np.pi) * 179
        hsv = np.stack([hue.astype(np.uint8),
                        np.clip(coherence * 255, 0, 255).astype(np.uint8),
                        np.clip(amount * 255, 0, 255).astype(np.uint8)], axis=-1)
        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    elif mode == "magnitude":
        cmap = matplotlib.colormaps[colormap]
        rgb = (cmap(amount)[..., :3] * 255).astype(np.uint8)
    elif mode == "coherence":
        cmap = matplotlib.colormaps[colormap]
        rgb = (cmap(coherence)[..., :3] * 255).astype(np.uint8)
    else:
        raise ValueError(
            f"mode must be 'direction', 'magnitude' or 'coherence', not {mode!r}")

    width, height = self.width, self.height
    full = cv2.resize(rgb, (width, height), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(target_name, full[..., ::-1])

    self.motionvectorhistory_image = MgImage(target_name)
    return self.motionvectorhistory_image


def motion_vector_motiongrams(filename, p_frames_only=True, deterministic=False):
    """Position against time, one column per frame, from the vectors.

    The horizontal motiongram collapses each frame's grid down its rows, leaving motion
    by horizontal position; the vertical one collapses across columns. Stacked over time
    they are the classic motiongram, and a body crossing the room draws a diagonal.

    Returns:
        tuple: `(horizontal, vertical)`, shaped (cols, frames) and (rows, frames).
    """
    import numpy as np

    #: Only the REDUCED column is kept per frame, never the grid it came from. A
    #: motiongram must grow with the recording; the full field behind it must not.
    across, down = [], []
    for _, _, weight, _, is_p in motion_vector_grid(filename, deterministic):
        if p_frames_only and not is_p:
            continue
        across.append(weight.sum(axis=0))
        down.append(weight.sum(axis=1))
    if not across:
        return np.zeros((0, 0)), np.zeros((0, 0))
    #: Transposed so that time runs along the image's x axis, which is what makes a
    #: motiongram readable as a score rather than as a picture of the room.
    return np.array(across).T, np.array(down).T


def mg_motionvectorgrams(self: "musicalgestures.MgVideo", colormap: str = "inferno",
                         gamma: float = 0.5, max_width: int = 4000,
                         target_name: str | None = None,
                         overwrite: bool = True) -> "MgList":
    """Motiongrams built from the codec's motion vectors.

    The same view `motiongrams()` gives, at a fraction of the cost, because the
    displacement has already been computed by the encoder. The trade is resolution: this
    is drawn on the macroblock lattice, sixteen pixels, and on P-frames only, so on 50 fps
    footage it carries about 12.6 columns per second rather than 50.

    Args:
        colormap (str, optional): Matplotlib colormap. Defaults to `'inferno'`.
        gamma (float, optional): Applied before colouring so quiet passages stay visible.
            Defaults to 0.5.
        max_width (int, optional): Widest the saved image may be, in pixels. One column
            per P-frame is right for the array and wrong for the picture: a 158-minute
            session has 77,592 of them, and stretching that to the video's height gave a
            149-megapixel PNG of 309 MB for something meant to be glanced at. Columns are
            pooled by taking the maximum, not the mean, so a brief accent still shows in
            a column standing for several seconds. Defaults to 4000.
        target_name (str, optional): Output path; the two images take `_mvgram_h` and
            `_mvgram_v` from it. Defaults to the input name.
        overwrite (bool, optional): Defaults to True.

    Returns:
        MgList: the horizontal and vertical motiongrams, in that order.
    """
    import cv2
    import matplotlib
    import numpy as np

    from musicalgestures._mglist import MgList
    from musicalgestures._utils import MgImage

    of, fex = os.path.splitext(self.filename)
    base = resolve_filename(of, '_mvgram.png', target_name, overwrite)
    stem, _ = os.path.splitext(base)

    horizontal, vertical = motion_vector_motiongrams(self.filename)
    cmap = matplotlib.colormaps[colormap]
    images = []
    for gram, suffix, span in ((horizontal, "_h", self.width),
                               (vertical, "_v", self.height)):
        if gram.size and gram.shape[1] > max_width:
            #: Pool by maximum rather than mean. A column here stands for several seconds
            #: once a long recording is squeezed to a readable width, and averaging would
            #: bury a one-second accent under the quiet around it --- which is exactly
            #: what a motiongram is read for.
            edges = np.linspace(0, gram.shape[1], max_width + 1).astype(int)
            gram = np.stack([gram[:, a:max(b, a + 1)].max(axis=1)
                             for a, b in zip(edges[:-1], edges[1:])], axis=1)
        scaled = gram / gram.max() if gram.size and gram.max() > 0 else gram
        if gamma and gamma != 1.0:
            scaled = np.power(scaled, gamma)
        rgb = (cmap(scaled)[..., :3] * 255).astype(np.uint8)
        #: Stretched back to the frame's own dimension on the spatial axis so the two
        #: grams line up with the video and with each other; nearest, because smoothing a
        #: macroblock lattice invents detail the vectors never had.
        out = cv2.resize(rgb, (rgb.shape[1], span), interpolation=cv2.INTER_NEAREST)
        path = f"{stem}{suffix}.png"
        cv2.imwrite(path, out[..., ::-1])
        images.append(MgImage(path))

    self.motionvectorgrams_images = MgList(images)
    return self.motionvectorgrams_images


def motion_vector_profiles(filename, n_samples=40, axis="horizontal",
                           p_frames_only=True, deterministic=False):
    """Motion profiles at `n_samples` moments, for stacking as a waterfall.

    Each profile is one spatial axis of the vector grid, summed over the other, pooled
    over the frames nearest that moment rather than taken from a single frame --- a
    single P-frame's vectors are sparse, and a waterfall of sparse profiles reads as
    noise where the pooled version reads as a body moving.

    Returns:
        tuple: `(profiles, times)`, profiles shaped (n_samples, cells).
    """
    import numpy as np

    per_frame, times = [], []
    for _, _, weight, t, is_p in motion_vector_grid(filename, deterministic):
        if p_frames_only and not is_p:
            continue
        per_frame.append(weight.sum(axis=0) if axis == "horizontal"
                         else weight.sum(axis=1))
        times.append(t)
    if not per_frame:
        return np.zeros((0, 0)), np.zeros(0)
    per_frame = np.array(per_frame)
    times = np.array(times)
    edges = np.linspace(0, len(per_frame), n_samples + 1).astype(int)
    profiles, moments = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        b = max(b, a + 1)
        profiles.append(per_frame[a:b].sum(axis=0))
        moments.append(float(times[a:b].mean()))
    return np.array(profiles), np.array(moments)


def mg_motionvectorwaterfall(self: "musicalgestures.MgVideo", n_samples: int = 40,
                             axis: str = "horizontal", cmap: str = "viridis",
                             dpi: int = 200, elev: float = 35, azim: float = -60,
                             target_name: str | None = None,
                             overwrite: bool = True) -> "MgFigure":
    """A waterfall of motion profiles, cascading through time.

    The same cascade `silhouette_waterfall()` draws, but from displacement rather than
    from a silhouette, so it needs no background subtraction and no pose model --- and it
    shows where movement was, not where a body was. A dancer standing still has a
    silhouette and no vectors.

    Args:
        n_samples (int, optional): How many profiles to stack. Defaults to 40.
        axis (str, optional): `'horizontal'` profiles over x, `'vertical'` over y.
            Defaults to `'horizontal'`.
        cmap (str, optional): Matplotlib colormap, applied over time. Defaults to
            `'viridis'`.
        dpi (int, optional): Defaults to 200.
        elev, azim (float, optional): 3D view angles. Default to 35 and -60.
        target_name (str, optional): Output path. Defaults to the input name with
            `_motionvectorwaterfall`.
        overwrite (bool, optional): Defaults to True.

    Returns:
        MgFigure: the rendered waterfall.
    """
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np

    from musicalgestures._utils import MgFigure

    of, fex = os.path.splitext(self.filename)
    target_name = resolve_filename(of, '_motionvectorwaterfall.png', target_name,
                                   overwrite)

    profiles, times = motion_vector_profiles(self.filename, n_samples=n_samples,
                                             axis=axis)
    fig = plt.figure(figsize=(10, 6), dpi=dpi)
    ax = fig.add_subplot(111, projection="3d")
    colours = matplotlib.colormaps[cmap](np.linspace(0, 1, max(len(profiles), 1)))
    x = np.arange(profiles.shape[1]) if profiles.size else np.arange(0)
    for i, profile in enumerate(profiles):
        ax.plot(x, np.full_like(x, times[i], dtype=float), profile,
                color=colours[i], linewidth=0.9)
    ax.set_xlabel("x" if axis == "horizontal" else "y")
    ax.set_ylabel("time (s)")
    ax.set_zlabel("motion")
    ax.view_init(elev=elev, azim=azim)
    fig.tight_layout()
    fig.savefig(target_name)
    plt.close(fig)

    self.motionvectorwaterfall_figure = MgFigure(
        figure=None, figure_type="video.motionvectorwaterfall",
        data={"profiles": profiles, "times": times}, layers=None,
        image=target_name)
    return self.motionvectorwaterfall_figure


@dataclass
class MgMotionVectorViews:
    """Every motion-vector view of one recording, from a single decode.

    Three kinds of representation, which is what a first pass over unfamiliar material
    wants: **spatial** (where motion happened, and which way), **temporal** (how much,
    over time), and **spatio-temporal** (the motiongrams, position against time).
    """
    history_weight: "np.ndarray"
    history_vx: "np.ndarray"
    history_vy: "np.ndarray"
    history_coherence: "np.ndarray"
    time: "np.ndarray"
    magnitude: "np.ndarray"
    motiongram_horizontal: "np.ndarray"
    motiongram_vertical: "np.ndarray"


def motion_vector_views(filename, p_frames_only=True, deterministic=False):
    """Every view at once, in one decode.

    The individual functions each decode the file, which is nearly all of the cost, so
    asking for four views costs four times what it needs to. This walks the vectors once
    and accumulates all of them. On a 100-minute 1920x1080 recording that is about four
    minutes rather than twenty-four.

    The result is checked against the individual functions in the test suite rather than
    assumed equal to them, because a fast path that quietly disagrees with the slow one
    is worse than no fast path.
    """
    import numpy as np

    total = sum_x = sum_y = sum_speed = None
    times, magnitude, across, down = [], [], [], []
    for vx, vy, weight, t, is_p in motion_vector_grid(filename, deterministic):
        if p_frames_only and not is_p:
            continue
        if total is None:
            total = np.zeros_like(weight)
            sum_x = np.zeros_like(weight)
            sum_y = np.zeros_like(weight)
            sum_speed = np.zeros_like(weight)
        total += weight
        sum_x += vx * weight
        sum_y += vy * weight
        sum_speed += np.hypot(vx, vy) * weight
        times.append(t)
        magnitude.append(float(weight.sum()))
        across.append(weight.sum(axis=0))
        down.append(weight.sum(axis=1))

    if total is None:
        z = np.zeros((1, 1))
        return MgMotionVectorViews(z, z.copy(), z.copy(), z.copy(), np.zeros(0),
                                   np.zeros(0), np.zeros((0, 0)), np.zeros((0, 0)))

    busy = total > 0
    mean_x = np.zeros_like(total)
    mean_y = np.zeros_like(total)
    mean_speed = np.zeros_like(total)
    coherence = np.zeros_like(total)
    mean_x[busy] = sum_x[busy] / total[busy]
    mean_y[busy] = sum_y[busy] / total[busy]
    mean_speed[busy] = sum_speed[busy] / total[busy]
    moving = mean_speed > 0
    coherence[moving] = np.hypot(mean_x, mean_y)[moving] / mean_speed[moving]
    return MgMotionVectorViews(
        history_weight=total, history_vx=mean_x, history_vy=mean_y,
        history_coherence=np.clip(coherence, 0, 1),
        time=np.array(times), magnitude=np.array(magnitude),
        motiongram_horizontal=np.array(across).T,
        motiongram_vertical=np.array(down).T)


def mg_motionvectoroverview(self: "musicalgestures.MgVideo", colormap: str = "inferno",
                            gamma: float = 0.5, target_name: str | None = None,
                            overwrite: bool = True) -> "MgFigure":
    """One sheet per recording, from one decode: where, how much, and when.

    Built for a first look at unfamiliar material rather than for measurement. Hours of
    archive video, several representations per file, as the starting point for
    qualitative annotation --- so it favours covering the whole recording cheaply over
    resolving any part of it finely.

    Five panels, of the three kinds a first pass wants:

    * **spatial** --- the area motion covered, coloured by direction, and the same
      accumulation as plain amount;
    * **temporal** --- motion over the whole recording, the curve to scrub against;
    * **spatio-temporal** --- horizontal and vertical motiongrams, position against time,
      where a body crossing the room draws a diagonal.

    Everything comes from the codec's own motion vectors, so the cost is close to the
    cost of reading the file: about five minutes for a 100-minute 1920x1080 recording,
    against roughly twenty-four for the same views computed one at a time, and far less
    than differencing the pixels.

    Args:
        colormap (str, optional): Matplotlib colormap for the amount panels. Defaults to
            `'inferno'`.
        gamma (float, optional): Applied before colouring so quiet passages stay visible.
            Defaults to 0.5.
        target_name (str, optional): Output path. Defaults to the input name with
            `_motionvectoroverview`.
        overwrite (bool, optional): Defaults to True.

    Returns:
        MgFigure: the sheet, with every underlying array in `.data` so the same pass can
        feed further analysis without decoding again.
    """
    import cv2
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np

    from musicalgestures._utils import MgFigure

    of, fex = os.path.splitext(self.filename)
    target_name = resolve_filename(of, '_motionvectoroverview.png', target_name,
                                   overwrite)
    v = motion_vector_views(self.filename)

    def shade(a):
        ceiling = np.percentile(a[a > 0], 99) if (a > 0).any() else 1.0
        return np.power(np.clip(a / max(ceiling, 1e-9), 0, 1), gamma)

    hue = (np.arctan2(v.history_vy, v.history_vx) + np.pi) / (2 * np.pi) * 179
    direction = cv2.cvtColor(np.stack([
        hue.astype(np.uint8),
        np.clip(v.history_coherence * 255, 0, 255).astype(np.uint8),
        np.clip(shade(v.history_weight) * 255, 0, 255).astype(np.uint8)], axis=-1),
        cv2.COLOR_HSV2RGB)

    cmap = matplotlib.colormaps[colormap]
    fig = plt.figure(figsize=(16, 11), dpi=110)
    grid = fig.add_gridspec(3, 2, height_ratios=[3, 1, 2], hspace=0.28, wspace=0.12)

    ax = fig.add_subplot(grid[0, 0])
    ax.imshow(direction, aspect="auto", interpolation="nearest")
    ax.set_title("where, and which way (hue = direction, saturation = consistency)")
    ax.set_xticks([]); ax.set_yticks([])

    ax = fig.add_subplot(grid[0, 1])
    ax.imshow(shade(v.history_weight), cmap=colormap, aspect="auto",
              interpolation="nearest")
    ax.set_title("where, as amount")
    ax.set_xticks([]); ax.set_yticks([])

    ax = fig.add_subplot(grid[1, :])
    if len(v.time):
        ax.plot(v.time / 60, v.magnitude, linewidth=0.4, color="#c1440e")
        ax.set_xlim(v.time[0] / 60, v.time[-1] / 60)
    ax.set_title("how much, over the recording")
    ax.set_xlabel("minutes")
    ax.set_yticks([])

    minutes = (v.time[-1] / 60) if len(v.time) else 1
    for column, (gram, label) in enumerate((
            (v.motiongram_horizontal, "horizontal motiongram (x against time)"),
            (v.motiongram_vertical, "vertical motiongram (y against time)"))):
        ax = fig.add_subplot(grid[2, column])
        if gram.size:
            ax.imshow(shade(gram), cmap=colormap, aspect="auto",
                      interpolation="nearest", extent=(0, minutes, gram.shape[0], 0))
        ax.set_title(label)
        ax.set_xlabel("minutes")
        ax.set_yticks([])

    fig.suptitle(os.path.basename(self.filename), fontsize=11)
    fig.savefig(target_name, bbox_inches="tight")
    plt.close(fig)

    self.motionvectoroverview_figure = MgFigure(
        figure=None, figure_type="video.motionvectoroverview",
        data={"time": v.time, "magnitude": v.magnitude,
              "history_weight": v.history_weight, "history_vx": v.history_vx,
              "history_vy": v.history_vy, "history_coherence": v.history_coherence,
              "motiongram_horizontal": v.motiongram_horizontal,
              "motiongram_vertical": v.motiongram_vertical},
        layers=None, image=target_name)
    return self.motionvectoroverview_figure


def motion_scape(track, n_scales=64):
    """A Sapp-style scape of any per-frame track: every timescale at once.

    In Craig Sapp's keyscape each row is a window length and each cell the key that best
    fits that window, so the plot answers "at what scale does this look like one thing"
    rather than "what is happening now". The same construction over quantity of motion
    reads the same way: a recording that is one long even stretch looks flat at every
    scale, and a few busy patches separated by quiet stay separate at the bottom and merge
    into one bright mass as the windows grow.

    Rows run coarse to fine --- the top row is a single window covering the whole
    recording, the bottom row is the track itself --- which puts the apex at the top, as
    a keyscape has it.

    Computed from a cumulative sum, so the cost does not depend on how wide the windows
    get: the whole plot is O(n_scales x n) whatever the recording's length.

    Args:
        track (np.ndarray): One value per frame. Quantity of motion from either source
            works; nothing here assumes it came from motion vectors.
        n_scales (int, optional): How many window lengths to stack. Defaults to 64.

    Returns:
        np.ndarray: shape (n_scales, len(track)), coarsest row first. Each cell is the
        mean of the track over a window of that row's length centred on that position,
        and NaN where a window that long does not fit --- which is what gives the plot
        its triangular shape, apex at the top.
    """
    import numpy as np

    q = np.asarray(track, dtype=np.float64).ravel()
    n = len(q)
    if n == 0:
        return np.zeros((n_scales, 0))
    #: One prepended zero so that `cumulative[b] - cumulative[a]` is the sum over [a, b).
    cumulative = np.concatenate([[0.0], np.cumsum(q)])
    positions = np.arange(n)
    #: Geometric, because the interesting structure is spread over orders of magnitude:
    #: linear scales would spend most of the plot on windows that all look alike.
    #: Geometric spacing rounds to duplicate integers at the short end --- for 20 scales
    #: over 500 frames it yields 18 distinct lengths --- so the shortfall is topped up
    #: from the unused lengths rather than by nudging the largest, which was an infinite
    #: loop: the nudged value already existed, so the set never grew.
    chosen = sorted({int(x) for x in np.geomspace(1, n, n_scales)})
    if len(chosen) < n_scales:
        spare = [x for x in range(1, n + 1) if x not in set(chosen)]
        chosen = sorted(chosen + spare[:n_scales - len(chosen)])
    while len(chosen) < n_scales:                 # fewer frames than scales asked for
        chosen.append(chosen[-1])
    lengths = np.array(chosen[:n_scales])

    scape = np.full((len(lengths), n), np.nan, dtype=np.float64)
    for row, length in enumerate(sorted(lengths, reverse=True)):
        half = length // 2
        lo = positions - half
        hi = lo + length
        #: Only where the whole window fits. Truncating at the edges instead would fill
        #: the corners with partial windows and square the plot off --- and the triangle
        #: IS the information: a row is only as wide as the number of places a window
        #: that long can sit, so the apex is the single window covering everything.
        fits = (lo >= 0) & (hi <= n)
        scape[row, fits] = ((cumulative[hi[fits]] - cumulative[lo[fits]])
                            / max(length, 1))
    return scape


def mg_motionscape(self: "musicalgestures.MgVideo", track=None,
                   n_scales: int = 96, colormap: str = "magma",
                   gamma: float = 0.5, target_name: str | None = None,
                   overwrite: bool = True) -> "MgFigure":
    """A scape of the recording's motion: every timescale in one triangle.

    After Craig Sapp's keyscape, where each row is a window length and the apex is a
    single window covering the whole piece. Here each cell is the mean quantity of motion
    over that window, so the plot answers a question the flat curve cannot: **at what
    scale does this recording stop looking like one thing?** A session of even, continuous
    improvisation is flat all the way up. A session of separated bursts stays separated at
    the base and merges into one mass near the apex, and the height at which it merges is
    the length of the structure.

    Args:
        track (array-like, optional): One value per frame to build the scape from. Pass
            a frame-differenced quantity of motion here --- `mg_motion`'s `QomRaw`, or a
            `qom.f4` read off disk --- to scape that instead. Nothing about the
            construction assumes where the numbers came from. Defaults to None, which
            reads the codec's motion vectors, cheap enough to run over an archive.
        n_scales (int, optional): Rows in the triangle. Defaults to 96.
        colormap (str, optional): Defaults to `'magma'`.
        gamma (float, optional): Applied before colouring. Defaults to 0.5.
        target_name (str, optional): Output path. Defaults to the input name with
            `_motionscape`.
        overwrite (bool, optional): Defaults to True.

    Returns:
        MgFigure: the scape, with the track and the triangle in `.data`.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    from musicalgestures._utils import MgFigure

    of, fex = os.path.splitext(self.filename)
    target_name = resolve_filename(of, '_motionscape.png', target_name, overwrite)

    if track is not None:
        track = np.asarray(track, dtype=np.float64).ravel()
        times = np.arange(len(track)) / float(self.fps)
        used = "supplied track"
    else:
        views = motion_vector_views(self.filename)
        track, times, used = views.magnitude, views.time, "motion vectors"

    scape = motion_scape(track, n_scales=n_scales)
    shown = scape / np.nanpercentile(scape, 99) if np.isfinite(scape).any() else scape
    shown = np.power(np.clip(shown, 0, 1), gamma)

    minutes = (times[-1] / 60) if len(times) else 1
    fig, ax = plt.subplots(figsize=(14, 7), dpi=120)
    ax.imshow(shown, cmap=colormap, aspect="auto", interpolation="nearest",
              extent=(0, minutes, 0, n_scales))
    ax.set_xlabel("minutes")
    ax.set_ylabel("window length: short at the base, whole recording at the apex")
    ax.set_yticks([])
    ax.set_title(f"{os.path.basename(self.filename)} --- motion scape ({used})")
    fig.tight_layout()
    fig.savefig(target_name)
    plt.close(fig)

    self.motionscape_figure = MgFigure(
        figure=None, figure_type="video.motionscape",
        data={"track": track, "time": times, "scape": scape, "source": used},
        layers=None, image=target_name)
    return self.motionscape_figure

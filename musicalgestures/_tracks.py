"""One pass over a long recording, and everything a timeline needs afterwards.

`mg_motion` is built for a clip and for a person looking at the result: it can write
a motion video, plots, motiongrams and a data file, and it computes centroid and area
whether or not you asked for them. That generosity is the right default for interactive
use and the wrong one for a two-hour session, where the cost decomposes like this on
120 s of 1080p video:

    motion_analysis='all',  motiongrams on   245 s
    motion_analysis='qom',  motiongrams on   215 s
    motion_analysis='qom',  motiongrams off   62 s

The motiongrams are 71 per cent of it and the area of motion another 12. This module
does the one pass those numbers argue for: **convert each motion frame to greyscale
once, and take everything from that** --- the quantity of motion, and both videogram
columns. `centroid()` converts to greyscale internally and then throws the conversion
away; doing it once and reusing it is most of the saving, and working on one channel
rather than three is the rest.

**Nothing is appended to a growing array.** The frame count is known before the pass
starts, so the columns go into a preallocated memory-mapped file. That is not a
micro-optimisation: growing these by `np.append` is what made a session take an
extrapolated 215 hours before 2026-08-24.

**The videogram is stored as a pyramid, the way an audio editor stores peaks.** A
column per frame is finer than any page can show --- 50 columns per second on an A4
width is one column per 20 pixels even when zoomed to a single action --- but the
whole session at that rate is 475,680 columns and cannot be drawn at all. So each
level halves the one below it by taking the extremes rather than the mean, because a
brief movement must survive being zoomed out of; averaging is what makes a spike
disappear at low magnification. Levels are built once, after the pass, from the base
that is already on disk, and cost a geometric series: less than the base again.

Reading is then a slice: pick the level whose width is nearest the pixels available
and take the columns for the time range wanted.
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np

import musicalgestures
from musicalgestures._filter import filter_frame_ffmpeg
from musicalgestures._utils import MgProgressbar, ffmpeg_cmd

#: Coarser levels stop here: below this a level is too narrow to be worth a file.
MIN_LEVEL_COLUMNS = 64


def _analysis_dir(video, out_dir=None) -> Path:
    """`analysis/<stem>/` beside the video unless told otherwise."""
    video = Path(video)
    root = Path(out_dir) if out_dir else video.parent / "analysis"
    d: Path = root / video.stem
    d.mkdir(parents=True, exist_ok=True)
    return d


def _frame_count(video, fps, duration) -> int:
    """Frames to expect, from the container's own duration.

    Deliberately an estimate with room in it: the memmaps are opened at this size and
    trimmed to what actually arrived, because a container that misreports its duration
    should cost a truncated file rather than a crash halfway through a two-hour pass.
    """
    return int(round(float(duration) * float(fps))) + 8




def _read_exact(stream, n: int) -> bytes | None:
    """Read exactly n bytes, or None at end of stream.

    **A pipe read can return short.** `stdout.read(n)` on a pipe is not obliged to
    give n bytes, and treating a short read as a whole frame slides every later frame
    across the boundary --- which shows up as output that changes between identical
    runs rather than as an error. Loop until the frame is complete.
    """
    buf = bytearray()
    while len(buf) < n:
        part = stream.read(n - len(buf))
        if not part:
            return None
        buf.extend(part)
    return bytes(buf)


def _chunk_worker(args) -> int:
    """Extract one time range into its slice of the memmaps. Runs in its own process.

    **Each chunk starts one frame early and throws that frame away.** The motion frame
    is a difference against the preceding frame, so the first frame after a seek has no
    predecessor and is not a motion frame at all. Overlapping by one and discarding it
    makes a chunked pass identical to a serial one instead of merely close.
    """
    (video, d, i0, n_frames, t0, fps, W, H, n_total,
     filtertype, threshold, blur, use_median, kernel_size, plate_every, is_last) = args
    import cv2 as _cv2
    import numpy as _np
    import musicalgestures as _mg
    from musicalgestures._filter import filter_frame_ffmpeg as _ffilter
    from musicalgestures._utils import ffmpeg_cmd as _ffcmd

    d = Path(d)
    #: SEEK EARLY AND TRIM BY TIME, rather than seeking close and dropping a frame.
    #: `-ss` before `-i` lands on a keyframe, so how many frames arrive before the
    #: target is not fixed --- dropping exactly one left a repeated frame at a seam.
    #: A whole second of lead-in guarantees the difference filter has a predecessor,
    #: and `trim` then keeps precisely the wanted range by timestamp.
    lead = 1.0 if t0 > 0 else 0.0
    seek = max(0.0, t0 - lead)
    dur = lead + n_frames / fps

    #: -ss goes before the input it seeks; -t must come AFTER -filter_complex so it
    #: is an OUTPUT option. filter_frame_ffmpeg appends further inputs (infinite
    #: `color=` sources for the threshold filter), so a -t placed between the video
    #: and them binds to one of THOSE inputs instead, changing which frames the
    #: filter sees. That produced an envelope differing from the serial one on almost
    #: every frame while looking like a chunking bug.
    cmd = ["ffmpeg", "-y", "-ss", f"{seek:.6f}", "-i", str(video)]
    cmd, chain = _ffilter(str(video), cmd, True, blur, filtertype,
                          threshold, kernel_size, use_median)
    #: STOP AT -filter_complex. ffmpeg_cmd(pipe="read") appends its OWN output
    #: arguments --- `-f image2pipe -pix_fmt bgr24 -vcodec rawvideo -` --- so adding
    #: an output spec here gives ffmpeg two outputs and it writes BOTH into the same
    #: stdout, interleaved. That produced frames that were wrong and, because the
    #: interleaving depends on buffering, different between identical runs. The pixel
    #: format is therefore bgr24, which is what COLOR_BGR2GRAY below expects.
    trim = ""
    if lead:
        #: Relative to the seek point, keep from `lead` onwards. setpts restarts the
        #: clock so downstream sees a normal stream.
        trim = f",trim=start={lead:.6f},setpts=PTS-STARTPTS"
    cmd += ["-filter_complex", chain[:-1] + trim]
    #: The last chunk runs to end of file; earlier ones are bounded so a worker does
    #: not decode the rest of a two-hour recording it will discard.
    if not is_last:
        cmd += ["-t", f"{dur:.6f}"]

    qom = _np.memmap(d / "qom.f4", dtype=_np.float32, mode="r+", shape=(n_total,))
    vg = _np.memmap(d / "videogram_v.u1", dtype=_np.uint8, mode="r+", shape=(n_total, H))
    hg = _np.memmap(d / "videogram_h.u1", dtype=_np.uint8, mode="r+", shape=(n_total, W))

    #: total_time drives the progress bar's arithmetic, so it must be a number
    #: even when no bar is wanted --- None makes it subtract from nothing.
    proc = _ffcmd(cmd, total_time=dur, pipe="read", stream=False)
    nbytes = W * H * 3
    written = 0
    plates = []
    while written < n_frames:
        buf = _read_exact(proc.stdout, nbytes)
        if buf is None:
            break
        frame = _np.frombuffer(buf, dtype=_np.uint8).reshape(H, W, 3)
        grey = _cv2.cvtColor(frame, _cv2.COLOR_BGR2GRAY)
        j = i0 + written
        qom[j] = float(_cv2.sumElems(grey)[0])
        vg[j] = grey.mean(axis=1).round().astype(_np.uint8)
        hg[j] = grey.mean(axis=0).round().astype(_np.uint8)
        if plate_every and j % plate_every == 0:
            plates.append(frame.copy())
        written += 1
    proc.terminate()
    qom.flush(); vg.flush(); hg.flush()
    if plates:
        _np.save(d / f".plate_{i0}.npy", _np.stack(plates))
    (d / f".done_{i0}").write_text(str(written))
    return written


def extract_tracks(video, out_dir=None, filtertype="Regular", threshold=0.05,
                   blur="None", use_median=False, kernel_size=5,
                   plate_every=None, progress=True) -> dict:
    """Quantity of motion and both videogram bases, in one pass over the video.

    Args:
        video: path to the recording.
        out_dir: where `analysis/<stem>/` goes. Defaults to beside the video.
        filtertype, threshold, blur, use_median, kernel_size: passed to the same
            ffmpeg filter chain `mg_motion` uses, so the motion frames are identical.
        plate_every: keep one raw frame in this many for the room plate, or None to
            keep none. The frames are sampled across the whole recording, so a plate
            built from them describes the whole room rather than one stretch.
        progress: show a progress bar.

    Returns:
        dict: paths written, and the parameters that made them.
    """
    video = Path(video)
    mgv = musicalgestures.MgVideo(str(video))
    W, H, fps = mgv.width, mgv.height, float(mgv.fps)
    n_max = _frame_count(video, fps, mgv.length / fps if mgv.length else 0) \
        if mgv.length else 10 ** 7
    if mgv.length:
        n_max = int(mgv.length) + 8

    d = _analysis_dir(video, out_dir)
    qom_path = d / "qom.f4"
    vgram_path = d / "videogram_v.u1"      # one column per frame, height H
    hgram_path = d / "videogram_h.u1"      # one row per frame, width W

    qom = np.memmap(qom_path, dtype=np.float32, mode="w+", shape=(n_max,))
    vg = np.memmap(vgram_path, dtype=np.uint8, mode="w+", shape=(n_max, H))
    hg = np.memmap(hgram_path, dtype=np.uint8, mode="w+", shape=(n_max, W))

    cmd = ["ffmpeg", "-y", "-i", str(video)]
    cmd, chain = filter_frame_ffmpeg(str(video), cmd, True, blur, filtertype,
                                     threshold, kernel_size, use_median)
    #: STOP AT -filter_complex. ffmpeg_cmd(pipe="read") appends its OWN output
    #: arguments --- `-f image2pipe -pix_fmt bgr24 -vcodec rawvideo -` --- so adding
    #: an output spec here gives ffmpeg two outputs and it writes BOTH into the same
    #: stdout, interleaved. That produced frames that were wrong and, because the
    #: interleaving depends on buffering, different between identical runs. The pixel
    #: format is therefore bgr24, which is what COLOR_BGR2GRAY below expects.
    cmd += ["-filter_complex", chain[:-1]]

    plates: list = []
    pb = MgProgressbar(total=n_max, prefix="Tracks:") if progress else None
    process = ffmpeg_cmd(cmd, total_time=mgv.length, pipe="read")

    i = 0
    nbytes = W * H * 3
    while i < n_max:
        buf = _read_exact(process.stdout, nbytes)
        if buf is None:
            break
        frame = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3)
        #: ONE conversion, three uses. centroid() does this conversion internally and
        #: discards it; the videogram columns then redo the work on three channels.
        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        qom[i] = float(cv2.sumElems(grey)[0])
        vg[i] = grey.mean(axis=1).round().astype(np.uint8)
        hg[i] = grey.mean(axis=0).round().astype(np.uint8)
        if plate_every and i % plate_every == 0:
            plates.append(frame.copy())
        if pb:
            pb.progress(i)
        i += 1
    process.terminate()
    if pb:
        pb.progress(n_max)

    n = i
    qom.flush(); vg.flush(); hg.flush()
    del qom, vg, hg
    _truncate(qom_path, n * 4)
    _truncate(vgram_path, n * H)
    _truncate(hgram_path, n * W)

    meta = {
        "video": str(video), "frames": n, "fps": fps, "width": W, "height": H,
        "duration_s": n / fps,
        "filtertype": filtertype, "threshold": threshold, "blur": blur,
        "use_median": use_median, "kernel_size": kernel_size,
        "qom": qom_path.name, "videogram_v": vgram_path.name,
        "videogram_h": hgram_path.name,
        "note": ("qom is the sum of the greyscale motion frame, the same quantity "
                 "mg_motion writes as QomRaw. The videogram bases hold one column "
                 "per frame; read them through pyramid levels rather than whole."),
    }
    if plates:
        plate = np.median(np.stack(plates), axis=0).astype(np.uint8)
        cv2.imwrite(str(d / "room_plate.png"), plate)
        meta["room_plate"] = "room_plate.png"
        meta["plate_frames"] = len(plates)
        meta["plate_note"] = ("MEDIAN, not mean. A mean over frames with performers in "
                              "different places keeps a faint ghost of each of them "
                              "everywhere they stood; a median removes them, because at "
                              "any pixel they are a minority of the samples.")
    (d / "tracks.json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


def _truncate(path: Path, nbytes: int) -> None:
    """Cut a memmap file back to the rows that were actually written."""
    with open(path, "r+b") as fh:
        fh.truncate(nbytes)


def build_pyramid(analysis_dir, which="videogram_v") -> list[Path]:
    """Halve a videogram base repeatedly, keeping extremes rather than means.

    Level 0 is the base, one column per frame. Level k is 2^k frames per column, and
    each column holds the greatest value of the columns beneath it. **Extremes, not
    means**: a movement lasting a few frames is exactly what a viewer zooms out to
    find, and averaging is what makes it vanish at low magnification.

    Returns the paths written, coarsest last.
    """
    d = Path(analysis_dir)
    meta = json.loads((d / "tracks.json").read_text())
    n, H, W = meta["frames"], meta["height"], meta["width"]
    span = H if which == "videogram_v" else W
    base = np.memmap(d / meta[which], dtype=np.uint8, mode="r", shape=(n, span))

    out, level, cur = [], 0, np.asarray(base)
    while cur.shape[0] > MIN_LEVEL_COLUMNS:
        level += 1
        m = cur.shape[0] // 2
        pair = cur[: m * 2].reshape(m, 2, span)
        cur = pair.max(axis=1)
        p = d / f"{which}.L{level}.u1"
        np.asarray(cur, dtype=np.uint8).tofile(p)
        out.append(p)
    meta.setdefault("pyramid", {})[which] = [p.name for p in out]
    (d / "tracks.json").write_text(json.dumps(meta, indent=1) + "\n")
    return out


def read_columns(analysis_dir, start_s=0.0, end_s=None, max_columns=2000,
                 which="videogram_v") -> tuple[np.ndarray, float]:
    """The videogram for a time range, at the coarsest level that still fills the width.

    This is how an audio editor draws a waveform: choose the level whose resolution
    the display can use and read a slice of it, rather than reading everything and
    throwing most of it away.

    Returns (columns, seconds_per_column).
    """
    d = Path(analysis_dir)
    meta = json.loads((d / "tracks.json").read_text())
    n, fps = meta["frames"], meta["fps"]
    span = meta["height"] if which == "videogram_v" else meta["width"]
    end_s = meta["duration_s"] if end_s is None else end_s
    want = max(1, int((end_s - start_s) * fps))

    #: Choose the level whose column count for this range is nearest below the
    #: pixels available. Reading a finer level and decimating in the reader would
    #: undo the point of having levels at all.
    level, stride = 0, 1
    while want // (stride * 2) >= max_columns and stride * 2 <= n:
        stride *= 2
        level += 1
    if level == 0:
        arr = np.memmap(d / meta[which], dtype=np.uint8, mode="r", shape=(n, span))
    else:
        name = f"{which}.L{level}.u1"
        rows = n // stride
        arr = np.memmap(d / name, dtype=np.uint8, mode="r", shape=(rows, span))

    lo = int(start_s * fps) // stride
    hi = int(end_s * fps) // stride
    return np.asarray(arr[lo:hi]), stride / fps


def extract_tracks_parallel(video, out_dir=None, workers=None, chunk_s=120.0,
                            filtertype="Regular", threshold=0.05, blur="None",
                            use_median=False, kernel_size=5, plate_every=None,
                            resume=True) -> dict:
    """The same pass, split over processes by time. Resumable.

    The work is embarrassingly parallel because each frame's motion depends only on
    its predecessor, so a chunk needs one frame of lead-in and nothing else. Workers
    write into disjoint slices of the same memory-mapped files, which is why no
    merging step is needed and why a crashed worker costs one chunk rather than the run.

    `resume=True` skips chunks that already left a marker, so restarting after a
    failure at hour five does not redo hours one to four --- the lesson the SINS
    producers learned by truncating a completed table.
    """
    video = Path(video)
    mgv = musicalgestures.MgVideo(str(video))
    W, H, fps = mgv.width, mgv.height, float(mgv.fps)
    n_total = int(mgv.length) + 8
    d = _analysis_dir(video, out_dir)

    for name, dt, shape in (("qom.f4", np.float32, (n_total,)),
                            ("videogram_v.u1", np.uint8, (n_total, H)),
                            ("videogram_h.u1", np.uint8, (n_total, W))):
        if not (d / name).exists() or not resume:
            m = np.memmap(d / name, dtype=dt, mode="w+", shape=shape)
            m.flush(); del m

    per = max(1, int(round(chunk_s * fps)))
    jobs = []
    for i0 in range(0, n_total, per):
        n_frames = min(per, n_total - i0)
        if resume and (d / f".done_{i0}").exists():
            continue
        jobs.append((str(video), str(d), i0, n_frames, i0 / fps, fps, W, H, n_total,
                     filtertype, threshold, blur, use_median, kernel_size, plate_every,
                     i0 + n_frames >= n_total))

    workers = workers or max(1, min(os.cpu_count() or 2, 8))
    if jobs:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            list(pool.map(_chunk_worker, jobs))

    #: The true frame count is where the last chunk stopped, not the estimate.
    written = 0
    for f in sorted(d.glob(".done_*"), key=lambda q: int(q.name.split("_")[1])):
        i0 = int(f.name.split("_")[1])
        written = max(written, i0 + int(f.read_text() or 0))
    n = written or n_total

    _truncate(d / "qom.f4", n * 4)
    _truncate(d / "videogram_v.u1", n * H)
    _truncate(d / "videogram_h.u1", n * W)

    meta = {"video": str(video), "frames": n, "fps": fps, "width": W, "height": H,
            "duration_s": n / fps, "filtertype": filtertype, "threshold": threshold,
            "blur": blur, "use_median": use_median, "kernel_size": kernel_size,
            "workers": workers, "chunk_s": chunk_s,
            "qom": "qom.f4", "videogram_v": "videogram_v.u1",
            "videogram_h": "videogram_h.u1",
            "note": ("qom is the sum of the greyscale motion frame, the quantity "
                     "mg_motion writes as QomRaw. Chunks overlap by one frame and "
                     "discard it, because the first frame after a seek has no "
                     "predecessor to differ from.")}

    plate_files = sorted(d.glob(".plate_*.npy"))
    if plate_files:
        stack = np.concatenate([np.load(f) for f in plate_files])
        cv2.imwrite(str(d / "room_plate.png"),
                    np.median(stack, axis=0).astype(np.uint8))
        meta["room_plate"] = "room_plate.png"
        meta["plate_frames"] = int(stack.shape[0])
        meta["plate_note"] = ("MEDIAN, not mean: a mean keeps a faint ghost of each "
                              "performer everywhere they stood.")
        for f in plate_files:
            f.unlink()
    (d / "tracks.json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


def check_tracks(analysis_dir) -> dict:
    """What an extraction actually produced, read from the data rather than the file.

    `extract_tracks_parallel` preallocates its memmaps to an estimated frame count, so
    the files reach full size in the first second of a run and every cheap check ---
    size, existence, `ls -la`, the last row of the array --- reports a finished
    extraction over a file that may be mostly zeros.

    Three numbers are returned **separately and unreconciled**, because on a run killed
    at 08:28 on 2026-08-25 they disagreed by 42,000 and 211,000 frames and each was
    right about something different:

    - `preallocated` is the estimate the file was sized to, and was never a measurement;
    - `last_nonzero` is where data stops, because workers write continuously and only
      drop a marker when a whole chunk closes;
    - `highest_marker` is the last chunk that closed, and is what `resume=True` trusts.

    `complete` is true only when `tracks_run.json` exists, since that file is written
    last and by the runner alone.

    Args:
        analysis_dir: The directory holding `qom.f4` and the chunk markers.

    Returns:
        dict: `preallocated`, `last_nonzero`, `highest_marker`, `n_markers`,
        `marker_gaps` and `complete`.
    """
    d = Path(analysis_dir)
    qom_path = d / "qom.f4"
    if not qom_path.exists():
        raise FileNotFoundError(f"no qom.f4 in {d}")

    prealloc = qom_path.stat().st_size // 4
    q = np.memmap(qom_path, dtype=np.float32, mode="r", shape=(prealloc,))
    #: SCAN BACKWARDS IN BLOCKS, and copy each block before testing it.
    #: `np.flatnonzero` over the whole memmap raises "number of non-zero array
    #: elements changed during function execution" when workers are still writing ---
    #: which is exactly when this function is most useful, since a run in progress is
    #: the thing you most want to ask about. Copying a block detaches it from the
    #: live mapping, and going backwards finds the answer in one block for the normal
    #: case of data at the front and zeros at the tail.
    last_nonzero = -1
    block = 1 << 20
    for hi in range(prealloc, 0, -block):
        lo = max(0, hi - block)
        chunk = np.array(q[lo:hi])
        nz = np.flatnonzero(chunk)
        if len(nz):
            last_nonzero = int(lo + nz[-1])
            break
    del q

    markers = sorted(int(p.name.split("_")[1]) for p in d.glob(".done_*"))
    step = markers[1] - markers[0] if len(markers) > 1 else 0
    gaps = []
    if step:
        expected = set(range(markers[0], markers[-1] + 1, step))
        gaps = sorted(expected - set(markers))

    return {"preallocated": prealloc,
            "last_nonzero": last_nonzero,
            "highest_marker": markers[-1] if markers else -1,
            "n_markers": len(markers),
            "marker_gaps": gaps,
            "complete": (d / "tracks_run.json").exists()}

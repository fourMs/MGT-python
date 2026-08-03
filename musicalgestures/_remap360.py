"""Remap-table flattening for legacy 360 formats.

GoPro MAX/MAX2 .360 files store the sphere as two strips of a custom
equi-angular cubemap (EAC) that stock ffmpeg cannot unwrap; legacy Ricoh
Theta S files store two 90-degree-rotated fisheye circles in one 16:9
frame. Both become plain equirectangular through the same machinery:
numpy-generated remap tables (16-bit PGM) driving ffmpeg's `remap` filter,
with a feathered `maskedmerge` blend across the unstitched seams — the
same two-pass pattern as `stitch_dual_fisheye` in `_360video`.

The GoPro mapping is a port of Paul Bourke's max2sphere reference
(paulbourke.net/panorama/gopromax2sphere/). MAX2-resolution files are
handled by proportional template scaling and are experimental until
validated against a real recording.
"""
import contextlib
import json
import os
import shutil
import subprocess
import tempfile

import cv2
import numpy as np

# (track_w, track_h) -> (centerwidth, sidewidth, blendwidth); the last 32
# (resp. 16) columns of each strip are unused padding in the real files
GOPRO_TEMPLATES = {
    (4096, 1344): (1376, 1344, 32),
    (2272, 736): (768, 736, 16),
}


def probe_gopro360(path):
    """Stream inventory + strip geometry of a GoPro two-strip container.

    Works on original .360 files and on chunk-merged .mkv copies. Returns
    {"video": [{index,width,height} x2], "audio": [{index,codec,channels}],
    "centerwidth", "sidewidth", "blendwidth", "experimental"}. Raises
    ValueError naming what was found when the file does not match the
    two-strip pattern.
    """
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=index,codec_type,codec_name,width,height,channels",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True)
    streams = json.loads(out.stdout).get("streams", [])
    video = [{"index": s["index"], "width": s.get("width"),
              "height": s.get("height")}
             for s in streams if s.get("codec_type") == "video"]
    audio = [{"index": s["index"], "codec": s.get("codec_name", "none"),
              "channels": s.get("channels", 0)}
             for s in streams if s.get("codec_type") == "audio"]
    inventory = (f"{len(video)} video "
                 f"{[(v['width'], v['height']) for v in video]}, "
                 f"{len(audio)} audio "
                 f"{[(a['codec'], a['channels']) for a in audio]}")
    if len(video) != 2 or video[0]["width"] != video[1]["width"] \
            or video[0]["height"] != video[1]["height"]:
        raise ValueError(f"not a GoPro two-strip .360: found {inventory}")
    w, h = video[0]["width"], video[0]["height"]
    if 3 * h > w:
        raise ValueError(f"not a GoPro two-strip .360: found {inventory} "
                         f"(strip narrower than three faces)")
    if (w, h) in GOPRO_TEMPLATES:
        cw, sw, bw = GOPRO_TEMPLATES[(w, h)]
        experimental = False
    else:                       # MAX2 & friends: scale the 5.6K template
        cw = round(w * 1376 / 4096)
        sw = round(w * 1344 / 4096)
        bw = max(2, round(w * 32 / 4096))
        experimental = True
    return {"video": video, "audio": audio, "centerwidth": cw,
            "sidewidth": sw, "blendwidth": bw, "experimental": experimental}


def write_remap_pgm(xmap, ymap, tmpdir):
    """Write x/y remap tables as 16-bit binary PGMs for ffmpeg's remap.

    Values are integer source-pixel coordinates; 16-bit PGM payloads are
    big-endian per the Netpbm spec.
    """
    paths = []
    for name, arr in (("xmap", xmap), ("ymap", ymap)):
        a = np.ascontiguousarray(arr.astype(">u2"))
        p = os.path.join(tmpdir, f"{name}.pgm")
        with open(p, "wb") as f:
            f.write(f"P5\n{a.shape[1]} {a.shape[0]}\n65535\n".encode())
            f.write(a.tobytes())
        paths.append(p)
    return tuple(paths)


_LEFT, _RIGHT, _FRONT, _BACK, _TOP, _DOWN = range(6)


def gopro_maps(track_w, track_h, centerwidth, sidewidth, blendwidth,
               out_w, out_h):
    """Equirect -> vstacked GoPro strips: dual sample maps + blend alpha.

    Port of max2sphere's FindFaceUV/GetColour (Paul Bourke). Returns
    (xmapL, ymapL, xmapR, ymapR, alpha): two source-coordinate maps into
    the double-height stacked frame (strip 1 on top) and the weight of the
    R sample (nonzero only in the unstitched seam zones of the four side
    faces).
    """
    # NOTE (port-check deviation, see task-2-report.md): max2sphere.c samples
    # each output pixel at x0 = i / width, y0 = j / height (max2sphere.c
    # lines ~116-124), i.e. the pixel's un-offset grid position, not a
    # centred (i+0.5)/width sample. Matching that here (rather than the
    # brief's +0.5-centred formula) is required for FRONT/BACK/TOP/DOWN
    # face boundaries to land where the test data expects them.
    #
    # Coordinates never exceed a handful of thousand pixels, far below
    # float32's ~7-significant-digit precision floor, so the geometry
    # below runs in float32 throughout; large intermediates are freed as
    # soon as they are no longer needed to keep peak memory down.
    jj, ii = np.meshgrid(np.arange(out_h, dtype=np.float32),
                         np.arange(out_w, dtype=np.float32), indexing="ij")
    lon = ii / out_w * 2 * np.pi - np.pi             # -pi..pi
    lat = np.pi / 2 - jj / out_h * np.pi             # +pi/2..-pi/2
    del jj, ii
    px = np.cos(lat) * np.sin(lon)
    py = np.cos(lat) * np.cos(lon)
    pz = np.sin(lat)
    del lon, lat

    ax, ay, az = np.abs(px), np.abs(py), np.abs(pz)
    face = np.full((out_h, out_w), _FRONT, dtype=np.int8)
    face = np.where((ax >= ay) & (ax >= az) & (px < 0), _LEFT, face)
    face = np.where((ax >= ay) & (ax >= az) & (px >= 0), _RIGHT, face)
    face = np.where((ay > ax) & (ay >= az) & (py >= 0), _FRONT, face)
    face = np.where((ay > ax) & (ay >= az) & (py < 0), _BACK, face)
    face = np.where((az > ax) & (az > ay) & (pz >= 0), _TOP, face)
    face = np.where((az > ax) & (az > ay) & (pz < 0), _DOWN, face)

    fourdivpi = 4.0 / np.pi
    dom = np.select([face == _LEFT, face == _RIGHT, face == _FRONT,
                     face == _BACK, face == _TOP, face == _DOWN],
                    [ax, ax, ay, ay, az, az])
    dom = np.maximum(dom, 1e-12)
    del ax, ay, az
    qx = np.arctan(px / dom) * fourdivpi
    qy = np.arctan(py / dom) * fourdivpi
    qz = np.arctan(pz / dom) * fourdivpi
    del px, py, pz, dom

    u = np.select(
        [face == _LEFT, face == _RIGHT, face == _FRONT,
         face == _BACK, face == _TOP, face == _DOWN],
        [(qy + 1), (1 - qy), (qx + 1), (1 - qx), (1 - qx), (1 - qx)]) / 2
    v = np.select(
        [face == _LEFT, face == _RIGHT, face == _FRONT,
         face == _BACK, face == _TOP, face == _DOWN],
        [(qz + 1), (qz + 1), (qz + 1), (qz + 1), (qy + 1), (1 - qy)]) / 2
    u = np.clip(u, 0, 1 - 1e-9)
    v = np.clip(v, 0, 1 - 1e-9)
    del qx, qy, qz

    # RotateUV90 for DOWN, BACK, TOP (port-check Step 0 verified this)
    rot = (face == _DOWN) | (face == _BACK) | (face == _TOP)
    u, v = np.where(rot, v, u), np.where(rot, 1 - u, v)
    # real GoPro MAX files store every face with v inverted in the
    # face-local (post-rotation) frame relative to the max2sphere
    # formulas — validated on 2023-12-18 lab footage, where the
    # un-flipped mapping renders the equatorial band upside-down
    v = np.clip(1.0 - v, 0, 1 - 1e-9)

    second = (face == _BACK) | (face == _DOWN) | (face == _TOP)
    y_off = np.where(second, np.float32(track_h), np.float32(0))
    center = (face == _FRONT) | (face == _BACK)
    left_slot = (face == _LEFT) | (face == _DOWN)
    x0 = np.where(center, np.float32(sidewidth),
                  np.where(left_slot, np.float32(0),
                           np.float32(sidewidth + centerwidth)))

    # side faces: split halves + seam blend (GetColour)
    duv = blendwidth / sidewidth
    uL = 2 * (0.5 - duv) * u
    uR = 2 * (0.5 - duv) * (u - 0.5) + 0.5 + duv
    left_only = uL <= 0.5 - 2 * duv
    right_only = uR >= 0.5 + 2 * duv
    blend = ~(left_only | right_only)
    alpha = np.where(blend & ~center,
                     (uL - 0.5 + 2 * duv) / (2 * duv), 0.0)
    alpha = np.clip(alpha, 0.0, 1.0)

    u_l = np.where(right_only, uR, uL)     # L map: left sample unless right-only
    u_r = np.where(left_only, uL, uR)      # R map: right sample unless left-only
    w_face = np.where(center, np.float32(centerwidth), np.float32(sidewidth))
    xL = x0 + np.where(center, u, u_l) * w_face
    xR = x0 + np.where(center, u, u_r) * w_face
    y = y_off + v * track_h
    return xL, y.copy(), xR, y.copy(), alpha


def _imwrite(path, img):
    """cv2.imwrite, but it raises instead of returning False.

    cv2.imwrite reports failure by return value, and every call in this module ignored it. On a
    full disk that turns "no space left" into a PNG that was never written, and the error surfaces
    later and somewhere else as a file that reads back as None. Two days of a StillStanding365
    build were reported as corrupt recordings on 2026-08-02 for exactly this reason; both sources
    probed clean.
    """
    if not cv2.imwrite(path, img):
        raise OSError(f"cv2.imwrite could not write {path} "
                      f"(disk full, unwritable directory, or unsupported extension)")
    return path


@contextlib.contextmanager
def _gopro_remap_stage(path, info, width, height, fps=None):
    """Inputs and filter graph that turn a two-strip .360 into one equirect frame.

    Shared by `flatten_gopro360` and `gopro360_to_dual_fisheye` so the two cannot drift: the remap
    tables, the seam handling and the blend are defined once, and each caller only decides what to
    do with the `[eq]` label at the end.

    `fps` decimates BEFORE the remap. That placement is the whole point of the parameter: the remap
    and the projection are the expensive stages, so dropping frames after them saves nothing. Put
    the same filter after `[eq]` and an averaging pass runs about fifteen times longer for an
    identical result.

    A CONTEXT MANAGER, and that is the whole reason it is one. The remap tables are written to a
    temporary directory that ffmpeg reads as input files, so it has to outlive this function and
    the caller has to remove it. Three call sites did not, and one of them discarded the path
    outright, so there was no way to. A build over 364 GoPro recordings left 22 GB across 348
    directories and filled the disk, which then surfaced as two unrelated-looking failures: one
    honest `OSError: [Errno 28]`, and one `expected RGBA, got None` that read like a corrupt
    recording and was `cv2.imwrite` silently failing on a full disk. Yielding rather than returning
    means the next call site cannot forget.

    Yields (extra_inputs, graph). The graph ends in `[eq]` and assumes the .360 is input 0.
    """
    w, h = info["video"][0]["width"], info["video"][0]["height"]
    xL, yL, xR, yR, alpha = gopro_maps(
        w, h, info["centerwidth"], info["sidewidth"], info["blendwidth"],
        width, height)
    tmpdir = tempfile.mkdtemp(prefix="mgt_remap360_")
    try:
        xlp, ylp = write_remap_pgm(np.rint(xL), np.rint(yL), tmpdir)
        os.rename(xlp, os.path.join(tmpdir, "xl.pgm"))
        os.rename(ylp, os.path.join(tmpdir, "yl.pgm"))
        xrp, yrp = write_remap_pgm(np.rint(xR), np.rint(yR), tmpdir)
        mask = os.path.join(tmpdir, "alpha.png")
        _imwrite(mask, (alpha * 255).astype(np.uint8))
        xlp, ylp = os.path.join(tmpdir, "xl.pgm"), os.path.join(tmpdir, "yl.pgm")
        rate = f",fps={fps}" if fps else ""
        graph = (f"[0:v:0]setpts=PTS-STARTPTS{rate}[v0];"
                 f"[0:v:1]setpts=PTS-STARTPTS{rate}[v1];"
                 f"[v0][v1]vstack[st];"
                 f"[st]format=gbrp,split[s1][s2];"
                 f"[s1][1:v][2:v]remap[l];"
                 f"[s2][3:v][4:v]remap[r];"
                 f"[5:v]format=gray,scale={width}:{height}[m];"
                 f"[l][r][m]maskedmerge[eq]")
        yield ["-i", xlp, "-i", ylp, "-i", xrp, "-i", yrp, "-i", mask], graph, tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _gopro_audio_args(info):
    """Map and re-encode the best audio stream, or nothing if the file carries none."""
    best_a = max(info["audio"], key=lambda a: a["channels"], default=None)
    if best_a is None:
        return []
    # GoPro tags its spatial PCM track 'ambisonic 1', a channel ORDER the
    # AAC encoder rejects outright; remap to a plain named layout (a no-op
    # for already-plain layouts). Unknown counts downmix to stereo.
    _LAYOUTS = {1: "mono", 2: "stereo", 4: "4.0"}
    out = ["-map", f"0:a:{info['audio'].index(best_a)}"]
    layout = _LAYOUTS.get(int(best_a["channels"]))
    if layout:
        chmap = "|".join(str(i) for i in range(int(best_a["channels"])))
        out += ["-af", f"channelmap={chmap}:{layout}"]
    else:
        out += ["-ac", "2"]
    return out + ["-c:a", "aac", "-b:a", "192k"]


def gopro360_dual_fisheye_average(path, target_name=None, fov=180.0, size=704,
                                  fps=2.0, transparent=True, print_cmd=False):
    """The time-average of a .360 as one dual-fisheye image, without writing a video first.

    For a recording of somebody standing still this is the useful still: whatever held position
    resolves, whatever moved smears, and a single frame cannot show either. Returns the path to a
    PNG, RGBA with the area outside each circle transparent when `transparent` is set.

    `fps` decimates before averaging. The mean of a stationary scene converges long before every
    frame is used -- a few hundred samples is plenty -- and decoding 4K equi-angular cubemap frames
    is the whole cost of this operation, so sampling at 2 Hz rather than 30 does the same job for a
    fifteenth of the work. Pass `fps=None` to average every frame.

    Frames are accumulated in float64 from a raw pipe rather than written out and re-read. An 8-bit
    running mean over a few hundred frames loses roughly a bit of precision at the point where the
    averaging is meant to be revealing motion smaller than a pixel.

    `path` may be several files. GoPro splits a recording into chapters, and averaging each chapter
    separately and combining the means weighted by frame count is arithmetically identical to
    averaging their concatenation -- while skipping the concatenation, which for a full session is
    an 8 GB lossless copy written and read back before any useful work starts.

    See `gopro360_to_dual_fisheye` for what `fov` means and why it has to be recorded.
    """
    from musicalgestures._utils import generate_outfilename

    paths = [str(path)] if isinstance(path, (str, os.PathLike)) else [str(p) for p in path]
    path = paths[0]
    info = probe_gopro360(path)
    h = info["video"][0]["height"]
    eq_w = (3 * h) // 2 * 2
    if target_name is None:
        target_name = os.path.splitext(path)[0] + "_dualfisheye_average.png"
    target_name = generate_outfilename(target_name)

    with _gopro_remap_stage(path, info, eq_w, eq_w // 2, fps=fps) as (extra, graph, _tmp):
        graph += (f";[eq]format=gbrp,split[e1][e2];"
                  f"[e1]v360=input=e:output=fisheye:h_fov={fov}:v_fov={fov}:"
                  f"w={size}:h={size}[front];"
                  f"[e2]v360=input=e:output=fisheye:h_fov={fov}:v_fov={fov}:yaw=180:"
                  f"w={size}:h={size}[back];"
                  f"[front][back]hstack=inputs=2,format=rgb24[out]")
        nbytes = size * 2 * size * 3
        acc = np.zeros((size, size * 2, 3), np.float64)
        n = 0
        err = ""
        for src in paths:
            cmds = (["ffmpeg", "-v", "error", "-i", src] + extra
                    + ["-filter_complex", graph, "-map", "[out]", "-an",
                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
            if print_cmd:
                print(" ".join(cmds))
            proc = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    bufsize=nbytes)
            try:
                while True:
                    buf = proc.stdout.read(nbytes)
                    if len(buf) < nbytes:
                        break
                    acc += np.frombuffer(buf, np.uint8).reshape(size, size * 2, 3)
                    n += 1
            finally:
                proc.stdout.close()
                err = proc.stderr.read().decode(errors="replace")
                proc.wait()
        if n == 0:
            raise RuntimeError(f"no frames decoded from {paths}\n{err.strip()[:500]}")

    img = np.rint(acc / n).astype(np.uint8)[:, :, ::-1]          # RGB -> BGR for cv2
    if transparent:
        yy, xx = np.mgrid[0:size, 0:size]
        r = np.hypot(yy - (size - 1) / 2, xx - (size - 1) / 2)
        disc = (r <= size / 2).astype(np.uint8) * 255
        alpha = np.hstack([disc, disc])
        img = np.dstack([img, alpha])
    _imwrite(target_name, img)
    return target_name


def _circle_mask_png(size, tmpdir):
    """A white disc inscribed in a black square, for masking outside the fisheye circle."""
    m = np.zeros((size, size), np.uint8)
    cv2.circle(m, (size // 2, size // 2), size // 2, 255, -1)
    return _imwrite(os.path.join(tmpdir, "circle.png"), m)


def gopro360_to_dual_fisheye(path, target_name=None, fov=180.0, size=704,
                             circular=True, crf=21, preset="fast",
                             print_cmd=False):
    """Convert a GoPro MAX .360 to side-by-side fisheye circles, front then back.

    The output is `2*size` by `size`: two inscribed circles of `size` pixels, the layout GoPro's
    own LRV proxies use and what most dual-fisheye viewers expect.

    `fov` is the angular width each circle covers, and it is a parameter to set deliberately rather
    than leave at a default. At 180 degrees a circle holds exactly a hemisphere and the two together
    hold the sphere with nothing to spare. Above 180 each holds more than a hemisphere, the pair
    overlap, and a given real-world direction lands closer to the centre of the circle --- at 195
    degrees by a factor of 180/195, about eight per cent at the rim. Two renders at different `fov`
    have identical pixel dimensions and are not comparable as measurements, so anything measuring
    direction or angular size in the result must record which was used.

    Why this is not `v360=input=eac` on the strips. GoPro's `.360` is a custom equi-angular cubemap
    that stock ffmpeg cannot unwrap: pointing `v360` at one 4096x1344 strip, or at the two stacked,
    yields a plausible-looking frame with scrambled corners rather than an error. The sphere is
    recovered here with the same remap tables `flatten_gopro360` uses, and only then projected.

    `circular` masks everything outside the inscribed circle to black, which is the convention for
    dual-fisheye files and what GoPro's own proxies look like. Without it `v360` fills the square
    out to the corners, and those corners hold real image content at an angle wider than `fov` --
    harmless to look at, wrong to measure, and enough to make two otherwise identical renders
    disagree about where the image ends.

    Geometry is validated against synthetic fixtures and the max2sphere reference; strip
    order/orientation against real camera files is still unverified, as for `flatten_gopro360`.
    """
    from musicalgestures._utils import (ffmpeg_cmd, generate_outfilename,
                                        get_length)

    path = str(path)
    info = probe_gopro360(path)
    h = info["video"][0]["height"]
    eq_w = (3 * h) // 2 * 2
    eq_h = eq_w // 2
    if target_name is None:
        target_name = os.path.splitext(path)[0] + "_dualfisheye.mp4"
    target_name = generate_outfilename(target_name)

    with _gopro_remap_stage(path, info, eq_w, eq_h) as (extra, graph, tmpdir):
        # one equirect frame, projected twice: forward, and the same rotated half a turn
        graph += (f";[eq]format=gbrp,split[e1][e2];"
                  f"[e1]v360=input=e:output=fisheye:h_fov={fov}:v_fov={fov}:"
                  f"w={size}:h={size}[front];"
                  f"[e2]v360=input=e:output=fisheye:h_fov={fov}:v_fov={fov}:yaw=180:"
                  f"w={size}:h={size}[back]")
        if circular:
            mask = _circle_mask_png(size, tmpdir)
            n = len(extra) // 2 + 1                     # next free input index
            extra = extra + ["-i", mask]
            graph += (f";[{n}:v]format=gbrp,split[mk1][mk2];"
                      f"[front][mk1]blend=all_mode=multiply[fc];"
                      f"[back][mk2]blend=all_mode=multiply[bc];"
                      f"[fc][bc]hstack=inputs=2,format=yuv420p[out]")
        else:
            graph += ";[front][back]hstack=inputs=2,format=yuv420p[out]"
        cmds = (["ffmpeg", "-y", "-i", path] + extra
                + ["-filter_complex", graph, "-map", "[out]"]
                + _gopro_audio_args(info)
                + ["-shortest", "-c:v", "libx264", "-crf", str(crf),
                   "-preset", preset, target_name])
        ffmpeg_cmd(cmds, get_length(path),
                   pb_prefix=f"GoPro 360 to dual fisheye ({fov:g} deg):",
                   print_cmd=print_cmd)
    return target_name


def flatten_gopro360(path, target_name=None, width=None, height=None,
                     crf=21, preset="fast", print_cmd=False):
    """Flatten a GoPro MAX/MAX2 .360 (or chunk-merged .mkv) to equirect.

    vstacks the two EAC strips, runs two `remap` passes (left/right seam
    samples) and blends the unstitched zones with `maskedmerge`. The best
    audio stream (most channels — the ambisonic PCM track on a MAX) is
    carried over as AAC. Files that are not exact GoPro templates (e.g.
    MAX2) use proportionally scaled geometry and are experimental.

    Geometry is validated against synthetic fixtures and the max2sphere
    reference; strip order/orientation against real camera files is still
    unverified.
    """
    from musicalgestures._utils import (ffmpeg_cmd, generate_outfilename,
                                        get_length)

    path = str(path)
    info = probe_gopro360(path)
    h = info["video"][0]["height"]
    if width is None:
        width = (3 * h) // 2 * 2
    if height is None:
        height = width // 2
    if target_name is None:
        target_name = os.path.splitext(path)[0] + "_equirect.mp4"
    target_name = generate_outfilename(target_name)

    with _gopro_remap_stage(path, info, width, height) as (extra, graph, _tmp):
        graph += ";[eq]format=yuv420p[out]"
        cmds = (["ffmpeg", "-y", "-i", path] + extra
                + ["-filter_complex", graph, "-map", "[out]"]
                + _gopro_audio_args(info)
                + ["-shortest", "-c:v", "libx264", "-crf", str(crf),
                   "-preset", preset, target_name])
        ffmpeg_cmd(cmds, get_length(path),
                   pb_prefix="Flattening GoPro 360:", print_cmd=print_cmd)
    return target_name


def theta_maps(in_w, in_h, out_w, out_h, fov_deg=191.5,
               roll_deg=(90.0, -90.0)):
    """Equirect -> Ricoh Theta S rotated dual-fisheye source coordinates.

    Legacy Theta S videos hold two fisheye circles side by side, each
    rotated 90 degrees in plane, in a 16:9 frame whose bottom band is
    unused. Front lens = left circle (axis +y), back = right (axis -y);
    equidistant fisheye model. Returns dual maps + seam-blend alpha like
    `gopro_maps`. fov_deg and roll_deg are tunable against a real file.
    """
    R = in_w / 4.0
    cy = R
    centers = (in_w / 4.0, 3.0 * in_w / 4.0)
    rolls = tuple(np.radians(r) for r in roll_deg)
    fov = np.radians(fov_deg)

    jj, ii = np.meshgrid(np.arange(out_h), np.arange(out_w), indexing="ij")
    lon = (ii + 0.5) / out_w * 2 * np.pi - np.pi
    # top-down rows: latitude runs south->north (validated against the
    # RICOH THETA app's own equirect export of the same file)
    lat = (jj + 0.5) / out_h * np.pi - np.pi / 2
    sx = np.cos(lat) * np.sin(lon)
    sy = np.cos(lat) * np.cos(lon)
    sz = np.sin(lat)

    maps = []
    for lens in range(2):
        axis = 1 if lens == 0 else -1
        costh = axis * sy
        theta = np.arccos(np.clip(costh, -1, 1))
        phi = np.arctan2(-sz, axis * sx)
        r = np.where(fov > 0, theta / (fov / 2), 0.0)
        x = centers[lens] + r * R * np.cos(phi + rolls[lens])
        y = cy + r * R * np.sin(phi + rolls[lens])
        maps.append((x, y, theta))

    (x0m, y0m, th0), (x1m, y1m, th1) = maps
    use1 = th1 < th0                       # back lens closer to its axis
    xL = np.where(use1, x1m, x0m)
    yL = np.where(use1, y1m, y0m)
    xR = np.where(use1, x0m, x1m)          # the *other* lens
    yR = np.where(use1, y0m, y1m)
    # blend where both lenses see the point (theta near 90 deg on both);
    # ramps 0 -> 0.5 over the last `margin` radians, reaching 0.5 exactly
    # at the geometric seam (theta == pi/2 on both lenses)
    margin = (fov / 2) - np.pi / 2         # half-overlap beyond a hemisphere
    prim = np.minimum(th0, th1)
    alpha = np.where(margin > 0,
                     0.5 * np.clip((prim - (np.pi / 2 - margin)) / margin,
                                   0.0, 1.0), 0.0)
    return xL, yL, xR, yR, alpha


def flatten_theta360(path, target_name=None, width=1920, height=960,
                     fov_deg=191.5, roll_deg=(90.0, -90.0), crf=21,
                     preset="fast", print_cmd=False):
    """Flatten a legacy Ricoh Theta S dual-fisheye MP4 to equirectangular.

    Explicit invocation only: a 16:9 MP4 is not identifiable as a Theta
    file by probing. Audio (mono on the Theta S) is passed through as AAC.

    The 191.5-degree/±90-degree defaults are validated only against
    synthetic fixtures; a real Theta S recording may need fov_deg/roll_deg
    fine-tuning.
    """
    from musicalgestures._utils import (ffmpeg_cmd, generate_outfilename,
                                        get_length, get_widthheight,
                                        has_audio)

    path = str(path)
    in_w, in_h = get_widthheight(path)
    if target_name is None:
        target_name = os.path.splitext(path)[0] + "_equirect.mp4"
    target_name = generate_outfilename(target_name)

    xL, yL, xR, yR, alpha = theta_maps(in_w, in_h, width, height,
                                       fov_deg=fov_deg, roll_deg=roll_deg)
    tmpdir = tempfile.mkdtemp(prefix="mgt_remap360_")
    try:
        xlp, ylp = write_remap_pgm(np.rint(xL), np.rint(yL), tmpdir)
        os.rename(xlp, os.path.join(tmpdir, "xl.pgm"))
        os.rename(ylp, os.path.join(tmpdir, "yl.pgm"))
        xrp, yrp = write_remap_pgm(np.rint(xR), np.rint(yR), tmpdir)
        mask = os.path.join(tmpdir, "alpha.png")
        _imwrite(mask, (alpha * 255).astype(np.uint8))
        xlp, ylp = os.path.join(tmpdir, "xl.pgm"), os.path.join(tmpdir, "yl.pgm")

        graph = (f"[0:v]format=gbrp,split[s1][s2];"
                 f"[s1][1:v][2:v]remap[l];"
                 f"[s2][3:v][4:v]remap[r];"
                 f"[5:v]format=gray,scale={width}:{height}[m];"
                 f"[l][r][m]maskedmerge,format=yuv420p[out]")
        cmds = ["ffmpeg", "-y", "-i", path,
                "-i", xlp, "-i", ylp, "-i", xrp, "-i", yrp, "-i", mask,
                "-filter_complex", graph, "-map", "[out]"]
        if has_audio(path):
            cmds += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "128k"]
        cmds += ["-shortest", "-c:v", "libx264", "-crf", str(crf),
                 "-preset", preset, target_name]
        ffmpeg_cmd(cmds, get_length(path),
                   pb_prefix="Flattening Theta 360:", print_cmd=print_cmd)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return target_name

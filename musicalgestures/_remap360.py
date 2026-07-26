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
import json
import os
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
    w, h = info["video"][0]["width"], info["video"][0]["height"]
    if width is None:
        width = (3 * h) // 2 * 2
    if height is None:
        height = width // 2
    if target_name is None:
        target_name = os.path.splitext(path)[0] + "_equirect.mp4"
    target_name = generate_outfilename(target_name)

    xL, yL, xR, yR, alpha = gopro_maps(
        w, h, info["centerwidth"], info["sidewidth"], info["blendwidth"],
        width, height)
    tmpdir = tempfile.mkdtemp(prefix="mgt_remap360_")
    xlp, ylp = write_remap_pgm(np.rint(xL), np.rint(yL), tmpdir)
    os.rename(xlp, os.path.join(tmpdir, "xl.pgm"))
    os.rename(ylp, os.path.join(tmpdir, "yl.pgm"))
    xrp, yrp = write_remap_pgm(np.rint(xR), np.rint(yR), tmpdir)
    mask = os.path.join(tmpdir, "alpha.png")
    cv2.imwrite(mask, (alpha * 255).astype(np.uint8))
    xlp, ylp = os.path.join(tmpdir, "xl.pgm"), os.path.join(tmpdir, "yl.pgm")

    best_a = max(info["audio"], key=lambda a: a["channels"], default=None)
    # GoPro tags its spatial PCM track 'ambisonic 1', a channel ORDER the
    # AAC encoder rejects outright; remap to a plain named layout (a no-op
    # for already-plain layouts). Unknown counts downmix to stereo.
    _LAYOUTS = {1: "mono", 2: "stereo", 4: "4.0"}
    graph = (f"[0:v:0][0:v:1]vstack[st];"
             f"[st]format=gbrp,split[s1][s2];"
             f"[s1][1:v][2:v]remap[l];"
             f"[s2][3:v][4:v]remap[r];"
             f"[5:v]format=gray,scale={width}:{height}[m];"
             f"[l][r][m]maskedmerge,format=yuv420p[out]")
    cmds = ["ffmpeg", "-y", "-i", path,
            "-i", xlp, "-i", ylp, "-i", xrp, "-i", yrp, "-i", mask,
            "-filter_complex", graph, "-map", "[out]"]
    if best_a is not None:
        astream = info["audio"].index(best_a)
        cmds += ["-map", f"0:a:{astream}"]
        layout = _LAYOUTS.get(int(best_a["channels"]))
        if layout:
            chmap = "|".join(str(i) for i in range(int(best_a["channels"])))
            cmds += ["-af", f"channelmap={chmap}:{layout}"]
        else:
            cmds += ["-ac", "2"]
        cmds += ["-c:a", "aac", "-b:a", "192k"]
    cmds += ["-shortest", "-c:v", "libx264", "-crf", str(crf),
             "-preset", preset, target_name]
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
    xlp, ylp = write_remap_pgm(np.rint(xL), np.rint(yL), tmpdir)
    os.rename(xlp, os.path.join(tmpdir, "xl.pgm"))
    os.rename(ylp, os.path.join(tmpdir, "yl.pgm"))
    xrp, yrp = write_remap_pgm(np.rint(xR), np.rint(yR), tmpdir)
    mask = os.path.join(tmpdir, "alpha.png")
    cv2.imwrite(mask, (alpha * 255).astype(np.uint8))
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
    return target_name

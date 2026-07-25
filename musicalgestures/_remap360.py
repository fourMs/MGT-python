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
from pathlib import Path

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
    jj, ii = np.meshgrid(np.arange(out_h), np.arange(out_w), indexing="ij")
    lon = ii / out_w * 2 * np.pi - np.pi             # -pi..pi
    lat = np.pi / 2 - jj / out_h * np.pi             # +pi/2..-pi/2
    px = np.cos(lat) * np.sin(lon)
    py = np.cos(lat) * np.cos(lon)
    pz = np.sin(lat)

    ax, ay, az = np.abs(px), np.abs(py), np.abs(pz)
    face = np.full(lon.shape, _FRONT, dtype=np.int8)
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
    qx = np.arctan(px / dom) * fourdivpi
    qy = np.arctan(py / dom) * fourdivpi
    qz = np.arctan(pz / dom) * fourdivpi

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

    # RotateUV90 for DOWN, BACK, TOP (port-check Step 0 verified this)
    rot = (face == _DOWN) | (face == _BACK) | (face == _TOP)
    u, v = np.where(rot, v, u), np.where(rot, 1 - u, v)

    second = (face == _BACK) | (face == _DOWN) | (face == _TOP)
    y_off = np.where(second, track_h, 0)
    center = (face == _FRONT) | (face == _BACK)
    left_slot = (face == _LEFT) | (face == _DOWN)
    x0 = np.where(center, sidewidth,
                  np.where(left_slot, 0, sidewidth + centerwidth))

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
    w_face = np.where(center, centerwidth, sidewidth)
    xL = x0 + np.where(center, u, u_l) * w_face
    xR = x0 + np.where(center, u, u_r) * w_face
    y = y_off + v * track_h
    return xL, y.copy(), xR, y.copy(), alpha

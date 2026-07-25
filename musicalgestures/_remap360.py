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

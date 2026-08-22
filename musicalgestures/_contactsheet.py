"""One frame from each of many videos, tiled into a sheet a corpus can be scanned by eye.

`grid()` tiles frames from ONE video. This does the other case: a corpus of recordings, one tile
each, so a year of daily sessions is a handful of pictures rather than a folder nobody opens.

WHY IT IS WORTH HAVING. On a 366-day export of daily standstill recordings, every framing fault
found was found by a person looking at a sheet like this and not by a measurement: a crop pointed
at a colleague rather than the participant, a frame that cut the subject's feet off, a geometry
that ran out of room at the bottom. A day framed differently from its neighbours announces itself
without any threshold having to be chosen, which is exactly what an automatic check cannot do,
because a check has to be told in advance what wrong looks like.

AN UNREADABLE FILE IS LABELLED, not skipped and not silently black. A tile that is simply dark and
a tile whose file could not be read look identical, and on that corpus a day was investigated as a
fault when the truth was that the sheet had been built while the file was still being written. So
a file that will not open gets a tile with UNREADABLE on it.
"""
from __future__ import annotations

import os

import numpy as np

from musicalgestures._utils import MgImage, generate_outfilename


def mg_contact_sheet(
    videos,
    at=None,
    tile_height=300,
    per_sheet=40,
    labels=None,
    background=(14, 13, 18),
    ink=(232, 228, 216),
    target_name=None,
    overwrite=False,
):
    """Tile one frame from each video into one or more contact sheets.

    Args:
        videos (list): paths to the video files, in the order they should appear.
        at (float, optional): seconds into each video to sample. Defaults to the midpoint of
            each file, which is per-file rather than a single number, because a corpus rarely
            shares one duration and the opening seconds usually hold setup rather than content.
        tile_height (int, optional): height of each tile in pixels; width follows the aspect
            ratio. Defaults to 300.
        per_sheet (int, optional): tiles per sheet before starting another. Defaults to 40.
        labels (list, optional): one label per video. Defaults to each file's basename without
            its extension.
        background (tuple, optional): sheet background as RGB. Defaults to a near-black.
        ink (tuple, optional): label colour as RGB.
        target_name (str, optional): path of the first sheet. Later sheets take a numbered
            suffix. Defaults to `contact_sheet.png` beside the first video.
        overwrite (bool, optional): whether to overwrite an existing file. Defaults to False.

    Returns:
        list: the `MgImage` objects written, one per sheet.

    Example:
        >>> import glob, musicalgestures as mg
        >>> sheets = mg.contact_sheet(sorted(glob.glob('exports/*.mp4')))
    """
    import cv2
    from PIL import Image, ImageDraw

    videos = list(videos)
    if not videos:
        raise ValueError("no videos given")
    if labels is None:
        labels = [os.path.splitext(os.path.basename(v))[0] for v in videos]
    if len(labels) != len(videos):
        raise ValueError(f"{len(labels)} labels for {len(videos)} videos")

    tiles = []
    for path, label in zip(videos, labels):
        cap = cv2.VideoCapture(path)
        frame = None
        if cap.isOpened():
            if at is None:
                n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                fps = cap.get(cv2.CAP_PROP_FPS) or 0
                when = (n / fps / 2.0) if (n and fps) else 0.0
            else:
                when = float(at)
            cap.set(cv2.CAP_PROP_POS_MSEC, when * 1000.0)
            ok, f = cap.read()
            if ok:
                frame = f
        cap.release()
        if frame is None:
            tiles.append((label, None))
            continue
        h, w = frame.shape[:2]
        tw = max(1, int(round(tile_height * w / h)))
        small = cv2.resize(frame, (tw, tile_height), interpolation=cv2.INTER_AREA)
        tiles.append((label, Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))))

    tile_w = max((im.width for _, im in tiles if im is not None), default=tile_height)
    label_h, pad = 16, 3

    if target_name is None:
        target_name = os.path.join(os.path.dirname(os.path.abspath(videos[0])),
                                   "contact_sheet.png")
    stem, ext = os.path.splitext(target_name)
    ext = ext or ".png"

    out = []
    for i in range(0, len(tiles), per_sheet):
        chunk = tiles[i:i + per_sheet]
        sheet = Image.new("RGB",
                          (len(chunk) * (tile_w + pad) + pad, tile_height + label_h + 2 * pad),
                          tuple(background))
        draw = ImageDraw.Draw(sheet)
        for j, (label, im) in enumerate(chunk):
            x = pad + j * (tile_w + pad)
            if im is not None:
                sheet.paste(im, (x + (tile_w - im.width) // 2, pad))
            else:
                draw.text((x + 4, pad + tile_height // 2), "UNREAD-\nABLE", fill=(210, 90, 90))
            draw.text((x + 2, pad + tile_height + 2), str(label), fill=tuple(ink))
        name = f"{stem}{ext}" if len(tiles) <= per_sheet else f"{stem}_{i // per_sheet + 1:02d}{ext}"
        if not overwrite:
            name = generate_outfilename(name)
        sheet.save(name)
        out.append(MgImage(name))
    return out

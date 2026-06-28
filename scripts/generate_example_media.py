#!/usr/bin/env python
"""Regenerate the example media used in the documentation.

Produces:
  * the still-image figure for ``motiondescriptors`` (the gallery already has the others), and
  * lightweight, palette-optimised GIFs for every video-producing method, built from a short
    sub-clip of the bundled ``dancer.avi`` so they stay small (<~1.5 MB, 320 px wide, 10 fps).

Outputs land in ``docs/images/examples/``. Run from the repo root:

    python scripts/generate_example_media.py [--figures] [--gifs] [--clip SECONDS]

With no flag both figures and GIFs are (re)generated. Pose is intentionally skipped: it needs the
optional ``mediapipe`` extra (or a slow OpenPose model download) and its figures already exist.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "docs", "images", "examples")
WORK = os.path.join(REPO, "_media_tmp")


def gif_from_video(src: str, dst: str, width: int = 320, fps: int = 10,
                   max_colors: int = 256) -> None:
    """Convert a video to a small, good-looking looping GIF via ffmpeg's palette pipeline."""
    palette = os.path.join(WORK, "palette.png")
    vf = f"fps={fps},scale={width}:-1:flags=lanczos"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf",
                    f"{vf},palettegen=max_colors={max_colors}", palette], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-i", palette,
                    "-lavfi", f"{vf} [x]; [x][1:v] paletteuse", "-loop", "0", dst], check=True)
    size_kb = os.path.getsize(dst) / 1024
    print(f"  -> {os.path.relpath(dst, REPO)} ({size_kb:.0f} KB)")


def make_clip(seconds: float) -> str:
    """Extract a short, motion-rich sub-clip of dancer.avi for the GIFs."""
    import musicalgestures as mg
    from musicalgestures._utils import extract_subclip
    clip = os.path.join(WORK, "clip.avi")
    # 30 s in has clear dancing; keep `seconds` of it.
    return extract_subclip(mg.examples.dance, 30, 30 + seconds, target_name=clip)


def generate_figures() -> None:
    import musicalgestures as mg
    print("Figures:")
    mv = mg.MgVideo(mg.examples.dance)
    mv.motiondescriptors(target_name=os.path.join(OUT, "motiondescriptors.png"))
    print(f"  -> {os.path.relpath(os.path.join(OUT, 'motiondescriptors.png'), REPO)}")


def generate_gifs(clip_seconds: float) -> None:
    import musicalgestures as mg
    print("GIFs:")
    clip = make_clip(clip_seconds)

    def video_gif(name: str, build, **gif_kw) -> None:
        try:
            out = build(mg.MgVideo(clip))
            path = out.filename if hasattr(out, "filename") else out
            gif_from_video(path, os.path.join(OUT, f"{name}.gif"), **gif_kw)
        except Exception as e:  # keep going so one failure doesn't abort the batch
            print(f"  !! {name} failed: {e}")

    # Only methods that actually produce a *video* get a GIF. (grid() returns a PNG and
    # sonomotiongram() returns a sonified WAV — they are figures/audio, not videos.)
    video_gif("motion", lambda v: v.motion())
    video_gif("history", lambda v: v.motionvideo().history(normalize=True))
    video_gif("motionvectors", lambda v: v.motionvectors())
    video_gif("eulerian", lambda v: v.eulerian(), width=260, fps=8, max_colors=128)
    video_gif("flow_dense", lambda v: v.flow.dense())
    video_gif("flow_sparse", lambda v: v.flow.sparse())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--figures", action="store_true", help="only (re)generate figures")
    ap.add_argument("--gifs", action="store_true", help="only (re)generate GIFs")
    ap.add_argument("--clip", type=float, default=3.0, help="GIF source clip length in seconds")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    do_figures = args.figures or not args.gifs
    do_gifs = args.gifs or not args.figures
    try:
        if do_figures:
            generate_figures()
        if do_gifs:
            generate_gifs(args.clip)
    finally:
        shutil.rmtree(WORK, ignore_errors=True)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

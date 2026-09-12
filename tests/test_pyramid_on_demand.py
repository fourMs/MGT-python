"""read_columns must work on a fresh extraction, and callers must be able to find it.

The bug: the extractors write the videogram base only, and `read_columns` mapped
`videogram_v.L<k>.u1` without checking, so the first read of any recording long enough to
need a coarser level raised FileNotFoundError until someone ran `build_pyramid` by hand.
"""
import json
import subprocess

import numpy as np

from musicalgestures._tracks import MIN_LEVEL_COLUMNS, extract_tracks, read_columns


def _synth(path, seconds=12, fps=25, size="160x120"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                    "-i", f"testsrc=size={size}:rate={fps}:duration={seconds}",
                    "-pix_fmt", "yuv420p", str(path)], check=True, capture_output=True)
    return str(path)


def test_read_columns_builds_the_pyramid_it_needs(tmp_path):
    v = _synth(tmp_path / "v.mp4")
    meta = extract_tracks(v, out_dir=tmp_path / "out", progress=False)
    d = tmp_path / "out" / "v"
    assert meta["frames"] > 2 * MIN_LEVEL_COLUMNS, "clip too short to need a level"
    assert not list(d.glob("videogram_v.L*.u1"))            # nothing built yet
    cols, spc = read_columns(d, max_columns=MIN_LEVEL_COLUMNS + 10)
    assert cols.shape[0] < meta["frames"] and cols.shape[1] == meta["height"]
    assert spc > 1.0 / meta["fps"]                          # a coarser level was used
    assert list(d.glob("videogram_v.L*.u1"))                # and it is now on disk
    assert "pyramid" in json.loads((d / "tracks.json").read_text())
    # the level keeps extremes: no coarse column exceeds the base maximum
    base = np.memmap(d / meta["videogram_v"], dtype=np.uint8, mode="r", shape=(meta["frames"], meta["height"]))
    assert cols.max() <= np.asarray(base).max()


def test_meta_says_where_it_lives(tmp_path):
    v = _synth(tmp_path / "v.mp4", seconds=2)
    meta = extract_tracks(v, out_dir=tmp_path / "out", progress=False)
    assert (tmp_path / "out" / "v" / "tracks.json").exists()
    assert meta["analysis_dir"] == str(tmp_path / "out" / "v")
    assert json.loads((tmp_path / "out" / "v" / "tracks.json").read_text())["analysis_dir"] == meta["analysis_dir"]


def test_extract_wav_is_exported():
    import musicalgestures as mg
    assert callable(mg.extract_wav)

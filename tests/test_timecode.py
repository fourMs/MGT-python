"""Absolute-clock helpers shared conceptually with ambiscape."""
import datetime as dt

import numpy as np
import pytest

from musicalgestures._features import MgFeatures
from musicalgestures._timecode import filename_datetime, media_start_datetime


def test_filename_datetime_long_and_short():
    assert filename_datetime("20260724_142731_00_037.insv") == \
        dt.datetime(2026, 7, 24, 14, 27, 31)
    assert filename_datetime("260724_143808 Belfort.m4a") == \
        dt.datetime(2026, 7, 24, 14, 38, 8)
    assert filename_datetime("holiday_video.mp4") is None


def test_media_start_datetime_falls_back_to_mtime(tmp_path):
    f = tmp_path / "clip.mp4"
    f.write_bytes(b"\0")
    got = media_start_datetime(f)
    assert abs((got - dt.datetime.now()).total_seconds()) < 60


def test_absolute_times():
    start = dt.datetime(2026, 7, 24, 14, 27, 31)
    mgf = MgFeatures({"qom": np.arange(4.0)}, times=np.arange(4.0),
                     sr=1.0, metadata={"start_datetime": start})
    t_abs = mgf.absolute_times()
    assert t_abs[0] == start.timestamp()
    assert t_abs[-1] - t_abs[0] == 3.0


def test_absolute_times_requires_start():
    mgf = MgFeatures({"qom": np.arange(4.0)}, times=np.arange(4.0))
    with pytest.raises(ValueError):
        mgf.absolute_times()

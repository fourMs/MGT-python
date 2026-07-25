"""The ambiscape adapter: audio session features as MgFeatures."""
import struct
import wave
from pathlib import Path

import numpy as np
import pytest

ambiscape = pytest.importorskip("ambiscape")

from musicalgestures._soundscape import soundscape_features  # noqa: E402


def _write_bwf(path, seconds, time="12:00:00", date="2026-07-24", fs=8000):
    """Minimal BWF WAV (bext date/time) — mirrors ambiscape's test writer."""
    x = (0.1 * np.random.default_rng(0).standard_normal(
        (int(seconds * fs), 1))).clip(-1, 1)
    pcm = (x * 32767).astype("<i2").tobytes()
    bext = bytearray(602)
    bext[320:330] = date.encode()
    bext[330:338] = time.encode()
    fmt = struct.pack("<HHIIHH", 1, 1, fs, fs * 2, 2, 16)
    chunks = (b"bext" + struct.pack("<I", len(bext)) + bytes(bext)
              + b"fmt " + struct.pack("<I", len(fmt)) + fmt
              + b"data" + struct.pack("<I", len(pcm)) + pcm)
    Path(path).write_bytes(b"RIFF" + struct.pack("<I", 4 + len(chunks))
                           + b"WAVE" + chunks)


def test_soundscape_features_roundtrip(tmp_path):
    _write_bwf(tmp_path / "room.wav", seconds=12.0, time="12:00:00")
    mgf = soundscape_features(tmp_path)
    assert "aud_level_db" in mgf.feature_names
    assert mgf.sr == 1.0
    t_abs = mgf.absolute_times()
    # first sample lands at 12:00:00 on 2026-07-24
    import datetime as dt
    assert abs(t_abs[0]
               - dt.datetime(2026, 7, 24, 12, 0, 0).timestamp()) < 2.0
    assert 5 <= mgf.n_samples <= 13

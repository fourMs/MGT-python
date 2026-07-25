"""Envelope cross-correlation alignment of two devices' recordings."""
import shutil
import subprocess

import numpy as np
import pytest

from musicalgestures._sync import align_recordings

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None,
                                reason="ffmpeg not on PATH")


@pytest.fixture()
def offset_pair(tmp_path):
    """Two WAVs of the same click train, the second starting 1.7 s later."""
    rng = np.random.default_rng(0)
    fs = 8000
    x = np.zeros(20 * fs, dtype=np.float32)
    for t in rng.uniform(0.5, 19.5, 40):        # 40 random clicks
        i = int(t * fs)
        x[i:i + 40] += rng.standard_normal(40).astype(np.float32)
    x = np.clip(0.5 * x, -1, 1)
    import wave

    def write(path, sig):
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(fs)
            w.writeframes((sig * 32767).astype("<i2").tobytes())

    a, b = tmp_path / "a.wav", tmp_path / "b.wav"
    write(a, x)
    write(b, x[int(1.7 * fs):])                 # b starts 1.7 s after a
    return a, b


def test_align_recordings_recovers_offset(offset_pair):
    a, b = offset_pair
    res = align_recordings(a, b)
    assert abs(res["lag_s"] - 1.7) < 0.05
    assert res["peak"] > 0.3

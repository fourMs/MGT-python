"""Align recordings from different devices by their transient envelopes.

One session, many gadgets, every clock slightly wrong: this estimates the
start-time offset between two recordings of the same scene from the
cross-correlation of their band-passed onset envelopes. Use the result to
fill ambiscape's ``calibration.json`` ``clock_offsets_s`` or to trim video
against a separate audio recorder.
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _envelope(path, band, env_fs):
    """Log-compressed, median-detrended transient envelope via ffmpeg."""
    from scipy import signal
    from scipy.io import wavfile

    fs = 16000
    with tempfile.TemporaryDirectory() as tmp:
        wav = str(Path(tmp) / "mono.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(path),
             "-map", "0:a:0", "-ac", "1", "-ar", str(fs), wav],
            check=True)
        _, x = wavfile.read(wav)
    x = x.astype(np.float64) / 32768.0
    hi = min(band[1], 0.45 * fs)
    sos = signal.butter(4, [band[0], hi], btype="band", fs=fs, output="sos")
    x = signal.sosfilt(sos, x)
    hop = fs // env_fs
    n = (len(x) // hop) * hop
    env = np.abs(x[:n]).reshape(-1, hop).mean(axis=1)
    env = np.log1p(1000 * env / (env.max() + 1e-12))
    return env - signal.medfilt(env, 2 * env_fs + 1)


def align_recordings(file_a, file_b, band=(200.0, 4000.0), env_fs=200,
                     max_lag_s=None):
    """Offset between two recordings of the same scene.

    Returns ``{"lag_s": s, "peak": p}`` where ``lag_s`` is positive when
    *file_b starts after file_a*. ``peak`` is the normalized correlation
    peak; below ~0.3 the alignment is unreliable (little shared audio).
    ``max_lag_s`` restricts the search when a rough offset is known.
    """
    from scipy import signal

    ea = _envelope(file_a, band, env_fs)
    eb = _envelope(file_b, band, env_fs)
    a = (ea - ea.mean()) / (ea.std() + 1e-12)
    b = (eb - eb.mean()) / (eb.std() + 1e-12)
    c = signal.correlate(a, b, mode="full")
    lags = signal.correlation_lags(len(a), len(b), mode="full")
    if max_lag_s is not None:
        keep = np.abs(lags) <= max_lag_s * env_fs
        c, lags = c[keep], lags[keep]
    k = int(np.argmax(c))
    return {"lag_s": float(lags[k] / env_fs),
            "peak": float(c[k] / min(len(a), len(b)))}

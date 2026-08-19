# MGT ↔ ambiscape Consolidation (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make MGT-python (video-first) and ambiscape (audio-first) interoperate on one absolute time base, with a single adapter direction, thinned overlaps, and shared device-sync utilities.

**Architecture:** Ownership line at the medium—MGT owns pixels, ambiscape owns samples. ambiscape stays dependency-light; MGT hosts the one cross-toolbox adapter (`musicalgestures[soundscape]` extra depends on ambiscape, never the reverse). Both toolboxes anchor feature series to wall-clock datetimes parsed the same way (identical filename-timestamp regexes), so audio and motion series join with a single time-shift.

**Tech Stack:** Python ≥3.10, numpy/scipy, ffmpeg CLI, pytest. Repos: `~/github/MGT-python` (venv: `.venv/bin/python`) and `~/github/ambiscape` (system `python3`, editable install).

## Global Constraints

- ambiscape core must stay numpy/scipy/soundfile-light: **no** new hard dependencies, and **never** a dependency on musicalgestures (course/CI use requires the light core).
- MGT's dependency on ambiscape lives **only** in the optional extra `soundscape = ["ambiscape>=0.17"]`.
- The filename-timestamp regexes in MGT must be byte-identical to ambiscape's (`io.py:39-40`): `(?<!\d)(\d{4})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})` and `(?<!\d)(\d{2})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})`.
- Cross-toolbox feature keys are namespaced: `mot_` for MGT motion, `vis_` for visual (existing ambiscape convention), `aud_` for audio-derived series exposed inside MGT.
- Tests: ambiscape tests run with `python3 -m pytest` from `~/github/ambiscape`; MGT tests run with `.venv/bin/python -m pytest` from `~/github/MGT-python`. ffmpeg-dependent tests guard with `pytest.importorskip`/`shutil.which("ffmpeg")`.
- Work on branch `consolidation-phase1` in each repo; commit per task; do not push until the user asks.

## Phase map (this plan = Phase 1 only)

Phase 1 (this plan): container ingest, per-take clock offsets, shared time base, sync utility, adapter + extra, summary merge, ownership docs.
Phase 2 (separate future plans, one each): deprecate MGT's duplicate audio descriptors in favour of the adapter; make `ambiscape.vision` delegate to MGT when installed; a joint session-folder spec with one combined `summary.json`; a shared example dataset (the Belfort session) used by both docs sites.

---

### Task 1: ambiscape opens Insta360/GoPro containers directly

**Files:**
- Modify: `~/github/ambiscape/src/ambiscape/io.py:30-33` (`_NEEDS_TRANSCODE`)
- Test: `~/github/ambiscape/tests/test_io_features.py`

**Interfaces:**
- Consumes: existing `_ensure_readable` ffmpeg-decode path (`io.py:174`), `open_session` (`io.py:258`).
- Produces: `.insv`, `.lrv`, `.glv`, `.360` accepted as session takes (first audio stream decoded to cached WAV). No signature changes.

- [ ] **Step 1: Write the failing test**

Append to `~/github/ambiscape/tests/test_io_features.py`:

```python
def test_insv_container_opens_via_transcode(tmp_path):
    """Insta360 .insv (an MP4 in disguise) is decoded on ingest."""
    import shutil
    import subprocess
    import pytest
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not on PATH")
    import ambiscape as asc
    # a 2 s stereo AAC mp4, renamed to the Insta360 extension
    mp4 = tmp_path / "20260724_142731_00_037.insv"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "sine=frequency=440:duration=2",
         "-ac", "2", "-c:a", "aac", "-f", "mp4", str(mp4)],
        check=True)
    sess = asc.open_session(tmp_path)
    assert len(sess.takes) == 1
    tk = sess.takes[0]
    assert tk.clock == "14:27:31"          # from the filename stamp
    assert 1.5 < tk.duration < 2.5
    assert tk.channels == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/ambiscape && python3 -m pytest tests/test_io_features.py::test_insv_container_opens_via_transcode -v`
Expected: FAIL with `FileNotFoundError: no audio files in ...` (suffix not recognized).

- [ ] **Step 3: Add the suffixes**

In `~/github/ambiscape/src/ambiscape/io.py`, change:

```python
_NEEDS_TRANSCODE = {".m4a", ".aac", ".mp4", ".m4b", ".mov", ".3gp", ".wma",
                    ".opus", ".webm"}
```

to:

```python
_NEEDS_TRANSCODE = {".m4a", ".aac", ".mp4", ".m4b", ".mov", ".3gp", ".wma",
                    ".opus", ".webm",
                    # 360-camera containers (Insta360, GoPro): plain MP4s
                    # with the first audio stream where we expect it
                    ".insv", ".lrv", ".glv", ".360"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/ambiscape && python3 -m pytest tests/test_io_features.py::test_insv_container_opens_via_transcode -v`
Expected: PASS

- [ ] **Step 5: Run the whole ambiscape suite**

Run: `cd ~/github/ambiscape && python3 -m pytest tests/ -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
cd ~/github/ambiscape && git checkout -b consolidation-phase1
git add src/ambiscape/io.py tests/test_io_features.py
git commit -m "Accept Insta360/GoPro 360 containers (.insv/.lrv/.glv/.360) on ingest"
```

---

### Task 2: ambiscape per-take clock offsets

**Files:**
- Modify: `~/github/ambiscape/src/ambiscape/io.py` (`open_session`, `io.py:258-289`)
- Test: `~/github/ambiscape/tests/test_io_features.py`

**Interfaces:**
- Consumes: `_make_take(path, day0, clock_offset, mode_override)` (`io.py:240`)—already takes a per-call offset; only `open_session` changes.
- Produces: `calibration.json` may now contain `"clock_offsets_s": {"<filename>": <seconds>}`, applied **in addition to** the global `clock_offset_s`. Real multi-device sessions need this (Belfort 2026-07-24: Insta360 −5 s, voice recorder +2 s, video 0 s).

- [ ] **Step 1: Write the failing test**

Append to `~/github/ambiscape/tests/test_io_features.py` (the file already imports `write_bwf` from `tests.conftest` and `numpy as np`; follow the style of `test_clock_offset_applied` at line 29):

```python
def test_per_take_clock_offsets(tmp_path):
    import json
    import ambiscape as asc
    from tests.conftest import write_bwf
    n = 48000
    write_bwf(tmp_path / "a.wav", np.zeros((n, 4)), time="10:00:00")
    write_bwf(tmp_path / "b.wav", np.zeros((n, 4)), time="10:01:00")
    (tmp_path / "calibration.json").write_text(json.dumps({
        "clock_offset_s": 2.0,
        "clock_offsets_s": {"b.wav": -5.0},
    }))
    sess = asc.open_session(tmp_path)
    takes = {t.path.name: t for t in sess.takes}
    assert takes["a.wav"].start == 2.0            # global only
    assert takes["b.wav"].start == 60.0 + 2.0 - 5.0   # global + per-take
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/ambiscape && python3 -m pytest tests/test_io_features.py::test_per_take_clock_offsets -v`
Expected: FAIL with `assert 62.0 == 57.0` (per-take offset ignored).

- [ ] **Step 3: Apply per-take offsets in `open_session`**

In `io.py`'s `open_session`, extend the calibration block:

```python
    clock_offset = 0.0
    clock_offsets = {}
    mode_override = None
    cal = folder / "calibration.json"
    if cal.exists():
        import json
        c = json.loads(cal.read_text())
        clock_offset = float(c.get("clock_offset_s", 0.0))
        clock_offsets = {str(k): float(v)
                         for k, v in c.get("clock_offsets_s", {}).items()}
        mode_override = c.get("mode")            # e.g. "binaural" for ear signals
```

and where takes are built (the loop below `sess.day0 = ...`), pass the summed offset:

```python
    for p, _ in metas:
        sess.takes.append(_make_take(
            p, sess.day0,
            clock_offset + clock_offsets.get(p.name, 0.0),
            mode_override))
```

(Keep everything else in the loop as it is; only the offset argument changes.)
Also extend the docstring's calibration sentence:

```python
    time — the fix for a recorder whose clock was found to be off (positive
    offset = clock was slow). ``clock_offsets_s`` maps individual filenames
    to additional per-take offsets for multi-device sessions.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/ambiscape && python3 -m pytest tests/test_io_features.py::test_per_take_clock_offsets tests/test_io_features.py::test_clock_offset_applied -v`
Expected: both PASS (the old global-offset behaviour must not regress).

- [ ] **Step 5: Commit**

```bash
cd ~/github/ambiscape
git add src/ambiscape/io.py tests/test_io_features.py
git commit -m "calibration.json: per-take clock_offsets_s for multi-device sessions"
```

---

### Task 3: MGT absolute-clock time base

**Files:**
- Create: `~/github/MGT-python/musicalgestures/_timecode.py`
- Modify: `~/github/MGT-python/musicalgestures/_features.py` (add one method to `MgFeatures`, class starts at line 41)
- Test: `~/github/MGT-python/tests/test_timecode.py`

**Interfaces:**
- Consumes: `MgFeatures(data, times=None, sr=1.0, source=None, metadata=None)` (`_features.py:73-80`).
- Produces:
  - `filename_datetime(path: str | Path) -> datetime | None` — parses `YYYYMMDD_HHMMSS` / `YYMMDD_HHMMSS` stamps, regexes identical to ambiscape `io.py:39-40`.
  - `media_start_datetime(path: str | Path) -> datetime | None` — filename stamp, else file mtime.
  - `MgFeatures.absolute_times() -> np.ndarray` — epoch seconds per sample; requires `metadata["start_datetime"]` (a `datetime` or ISO string); raises `ValueError` otherwise.

- [ ] **Step 1: Write the failing tests**

Create `~/github/MGT-python/tests/test_timecode.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/github/MGT-python && .venv/bin/python -m pytest tests/test_timecode.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'musicalgestures._timecode'`.

- [ ] **Step 3: Create `_timecode.py`**

```python
"""Absolute-clock helpers: parse recording start times from filenames.

The regexes are byte-identical to ambiscape's (``ambiscape/io.py``), so a
folder of phone/recorder/360-camera files resolves to the same wall-clock
timeline in both toolboxes.
"""
import datetime as dt
import os
import re
from pathlib import Path

# leading YYYYMMDD_HHMMSS or YYMMDD_HHMMSS in a filename (phone / recorder)
_TS_LONG = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})")
_TS_SHORT = re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})")


def filename_datetime(path) -> dt.datetime | None:
    """Parse a ``YYYYMMDD_HHMMSS`` / ``YYMMDD_HHMMSS`` filename stamp."""
    name = Path(path).name
    m = _TS_LONG.search(name)
    if m:
        y, mo, d, hh, mm, ss = (int(g) for g in m.groups())
        try:
            return dt.datetime(y, mo, d, hh, mm, ss)
        except ValueError:
            pass
    m = _TS_SHORT.search(name)
    if m:
        yy, mo, d, hh, mm, ss = (int(g) for g in m.groups())
        try:
            return dt.datetime(2000 + yy, mo, d, hh, mm, ss)
        except ValueError:
            pass
    return None


def media_start_datetime(path) -> dt.datetime | None:
    """Start time of a recording: filename stamp, else file mtime."""
    stamped = filename_datetime(path)
    if stamped is not None:
        return stamped
    try:
        return dt.datetime.fromtimestamp(os.path.getmtime(path))
    except OSError:
        return None
```

- [ ] **Step 4: Add `MgFeatures.absolute_times()`**

In `_features.py`, inside `class MgFeatures` (after the existing properties; match the class's docstring style):

```python
    def absolute_times(self) -> np.ndarray:
        """Wall-clock time stamps (epoch seconds) for each sample.

        Requires ``metadata["start_datetime"]`` — a ``datetime`` or ISO
        string, e.g. from ``musicalgestures._timecode.media_start_datetime``.
        """
        import datetime as _dt

        start = (self.metadata or {}).get("start_datetime")
        if start is None:
            raise ValueError(
                "no metadata['start_datetime']; set it (see "
                "musicalgestures._timecode) to place features on the "
                "wall clock")
        if isinstance(start, str):
            start = _dt.datetime.fromisoformat(start)
        return start.timestamp() + np.asarray(self.times, dtype=float)
```

(`self.times` is the existing public property at `_features.py:127-128`.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/github/MGT-python && .venv/bin/python -m pytest tests/test_timecode.py -v`
Expected: 4 PASS.

- [ ] **Step 6: Commit**

```bash
cd ~/github/MGT-python && git checkout -b consolidation-phase1
git add musicalgestures/_timecode.py musicalgestures/_features.py tests/test_timecode.py
git commit -m "Add absolute-clock time base: filename stamps + MgFeatures.absolute_times()"
```

---

### Task 4: MGT device-sync utility

**Files:**
- Create: `~/github/MGT-python/musicalgestures/_sync.py`
- Test: `~/github/MGT-python/tests/test_sync.py`

**Interfaces:**
- Consumes: ffmpeg CLI (already a hard MGT requirement); scipy (available via librosa's dependency tree—if `import scipy` fails in the venv, add `scipy>=1.10` to `[project] dependencies`).
- Produces: `align_recordings(file_a, file_b, band=(200.0, 4000.0), env_fs=200, max_lag_s=None) -> dict` with keys `lag_s` (float; positive = **b starts after a**) and `peak` (float, normalized correlation peak, ~>0.3 is trustworthy). Works on any av file ffmpeg can read.

- [ ] **Step 1: Write the failing test**

Create `~/github/MGT-python/tests/test_sync.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && .venv/bin/python -m pytest tests/test_sync.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'musicalgestures._sync'`.

- [ ] **Step 3: Create `_sync.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && .venv/bin/python -m pytest tests/test_sync.py -v`
Expected: PASS. If scipy is missing in the venv: add `"scipy>=1.10"` to `dependencies` in `pyproject.toml`, `.venv/bin/pip install -e .`, re-run.

- [ ] **Step 5: Commit**

```bash
cd ~/github/MGT-python
git add musicalgestures/_sync.py tests/test_sync.py
git commit -m "Add align_recordings(): envelope cross-correlation device sync"
```

---

### Task 5: MGT `soundscape` extra + ambiscape adapter

**Files:**
- Modify: `~/github/MGT-python/pyproject.toml:38-44` (optional-dependencies)
- Create: `~/github/MGT-python/musicalgestures/_soundscape.py`
- Test: `~/github/MGT-python/tests/test_soundscape.py`

**Interfaces:**
- Consumes: `ambiscape.open_session(folder)`, `ambiscape.features.extract_session(sess, out_dir, verbose)` (`features.py:237`), `ambiscape.features.load_features(npz_paths)` (`features.py:253`) returning a dict with at least `t` (1 Hz time axis, seconds since session day0) and `rms_w`; `Session.day0` (a `datetime.date`). Also Task 3's `MgFeatures.absolute_times()` contract.
- Produces: `soundscape_features(session_folder, features_dir=None) -> MgFeatures` with 1 Hz series named `aud_level_db` (from `rms_w`), `times` in seconds since session day0 midnight, `sr=1.0`, and `metadata={"start_datetime": <day0 midnight ISO>, "tool": "ambiscape"}`.

- [ ] **Step 1: Install ambiscape into the MGT venv (dev-time only)**

Run: `cd ~/github/MGT-python && .venv/bin/pip install -e ~/github/ambiscape`
Expected: installs; `.venv/bin/python -c "import ambiscape"` succeeds.

- [ ] **Step 2: Write the failing test**

Create `~/github/MGT-python/tests/test_soundscape.py`:

```python
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd ~/github/MGT-python && .venv/bin/python -m pytest tests/test_soundscape.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'musicalgestures._soundscape'`.

- [ ] **Step 4: Create `_soundscape.py` and the extra**

`musicalgestures/_soundscape.py`:

```python
"""Bridge to ambiscape: soundscape features on the MGT time base.

MGT owns pixels, ambiscape owns samples; this adapter is the one crossing
point. It runs (or reuses) ambiscape's cached feature extraction for a
session folder and returns the 1 Hz series as an MgFeatures container whose
metadata carries the absolute start time, so motion and audio series join
on the wall clock. Requires ``pip install "musicalgestures[soundscape]"``.
"""
import datetime as dt
from pathlib import Path

import numpy as np

from musicalgestures._features import MgFeatures


def soundscape_features(session_folder, features_dir=None) -> MgFeatures:
    """ambiscape session features as an MgFeatures (1 Hz, wall-clocked).

    Args:
        session_folder: an ambiscape session folder (WAVs on one clock).
        features_dir: cache directory for ambiscape's .npz features
            (default: ``<session_folder>/analysis/features``).
    """
    try:
        import ambiscape as asc
        from ambiscape import features as afeat
    except ImportError as e:
        raise ImportError(
            "ambiscape is required: pip install "
            "'musicalgestures[soundscape]'") from e

    session_folder = Path(session_folder)
    sess = asc.open_session(session_folder)
    out = Path(features_dir) if features_dir else \
        session_folder / "analysis" / "features"
    npz = sorted(out.glob("*.npz")) or \
        afeat.extract_session(sess, out, verbose=False)
    F = afeat.load_features(sorted(Path(p) for p in npz))

    level_db = 20 * np.log10(np.asarray(F["rms_w"], float) + 1e-12)
    day0_midnight = dt.datetime.combine(sess.day0, dt.time())
    return MgFeatures(
        {"aud_level_db": level_db},
        times=np.asarray(F["t"], float),
        sr=1.0,
        source=str(session_folder),
        metadata={"start_datetime": day0_midnight.isoformat(),
                  "tool": "ambiscape"},
    )
```

In `pyproject.toml`, add to `[project.optional-dependencies]` (before `full`):

```toml
soundscape = ["ambiscape>=0.17"]
```

and extend `full`:

```toml
full = ["musicalgestures[pose,ml,cli,c3d,soundscape]"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd ~/github/MGT-python && .venv/bin/python -m pytest tests/test_soundscape.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd ~/github/MGT-python
git add musicalgestures/_soundscape.py tests/test_soundscape.py pyproject.toml
git commit -m "Add musicalgestures[soundscape]: ambiscape session features as MgFeatures"
```

---

### Task 6: MGT summary merge with `mot_` prefix

**Files:**
- Modify: `~/github/MGT-python/musicalgestures/_soundscape.py`
- Test: `~/github/MGT-python/tests/test_soundscape.py`

**Interfaces:**
- Consumes: `MgFeatures.feature_names` and item access `mgf[name]` (`__getitem__`, `_features.py:140`).
- Produces: `merge_into_summary(features: MgFeatures, summary_json, prefix="mot_") -> Path` — adds `<prefix><name>_median` and `<prefix><name>_iqr` keys (rounded to 4 decimals) into an existing JSON file (ambiscape's `analysis/summary.json` convention, mirroring ambiscape's own `vis_` merge). Creates the file if absent.

- [ ] **Step 1: Write the failing test**

Append to `~/github/MGT-python/tests/test_soundscape.py`:

```python
def test_merge_into_summary(tmp_path):
    import json
    from musicalgestures._features import MgFeatures
    from musicalgestures._soundscape import merge_into_summary

    summary = tmp_path / "summary.json"
    summary.write_text(json.dumps({"leq_dbfs": -25.0}))
    mgf = MgFeatures({"qom": np.array([0.0, 1.0, 2.0, 3.0])},
                     times=np.arange(4.0), sr=1.0)
    merge_into_summary(mgf, summary)
    doc = json.loads(summary.read_text())
    assert doc["leq_dbfs"] == -25.0            # existing keys preserved
    assert doc["mot_qom_median"] == 1.5
    assert doc["mot_qom_iqr"] == 1.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && .venv/bin/python -m pytest tests/test_soundscape.py::test_merge_into_summary -v`
Expected: FAIL with `ImportError: cannot import name 'merge_into_summary'`.

- [ ] **Step 3: Implement `merge_into_summary`**

Append to `musicalgestures/_soundscape.py`:

```python
def merge_into_summary(features: MgFeatures, summary_json,
                       prefix: str = "mot_"):
    """Fold feature medians/IQRs into an analysis summary.json.

    The mirror of ambiscape's ``vision --merge`` (which uses ``vis_``):
    each feature contributes ``<prefix><name>_median`` and
    ``<prefix><name>_iqr`` so one summary file describes the whole
    audio-visual session. Existing keys are preserved.
    """
    import json

    summary_json = Path(summary_json)
    doc = json.loads(summary_json.read_text()) \
        if summary_json.exists() else {}
    for name in features.feature_names:
        x = np.asarray(features[name], dtype=float)
        q25, q50, q75 = np.nanpercentile(x, [25, 50, 75])
        doc[f"{prefix}{name}_median"] = round(float(q50), 4)
        doc[f"{prefix}{name}_iqr"] = round(float(q75 - q25), 4)
    summary_json.write_text(json.dumps(doc, indent=2))
    return summary_json
```

(`mgf[name]` is the container's existing item access, `_features.py:140`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && .venv/bin/python -m pytest tests/test_soundscape.py -v`
Expected: all PASS.

- [ ] **Step 5: Run the full MGT suite**

Run: `cd ~/github/MGT-python && .venv/bin/python -m pytest tests/ -q -x --timeout=600` (drop `--timeout` if pytest-timeout is not installed)
Expected: all pass (pre-existing failures unrelated to these files may be noted and skipped).

- [ ] **Step 6: Commit**

```bash
cd ~/github/MGT-python
git add musicalgestures/_soundscape.py tests/test_soundscape.py
git commit -m "Add merge_into_summary(): mot_-prefixed keys into a shared summary.json"
```

---

### Task 7: Ownership statement in both READMEs

**Files:**
- Modify: `~/github/MGT-python/README.md` (add section after the introduction)
- Modify: `~/github/ambiscape/README.md` (add section after the introduction)
- Modify: `~/github/ambiscape/src/ambiscape/vision.py` (docstring note only)

**Interfaces:**
- Consumes: nothing.
- Produces: a written division of labour both projects link to; no code changes.

- [ ] **Step 1: Add to MGT README (after the opening paragraph):**

```markdown
## Scope: MGT and ambiscape

MGT-python and [ambiscape](https://github.com/fourMs/ambiscape) are sister
toolboxes: **MGT owns the pixels** (motion analysis, pose, 360° handling,
video visualization), **ambiscape owns the samples** (soundscape levels,
spatial audio, sound-event taxonomies). MGT's audio functions cover quick
looks; for serious soundscape work, install the bridge—`pip
 install "musicalgestures[soundscape]"` — and pull ambiscape's
session features straight into `MgFeatures` on a shared wall-clock time
base (see `musicalgestures._soundscape` and `musicalgestures._timecode`).
```

- [ ] **Step 2: Add to ambiscape README (after the opening paragraph):**

```markdown
## Scope: ambiscape and MGT

ambiscape and [MGT-python](https://github.com/fourMs/MGT-python) are sister
toolboxes: **ambiscape owns the samples**, **MGT owns the pixels**. The
built-in `vision` module extracts only lightweight per-frame features as a
multimodal companion to the audio; for real video analysis (motion, pose,
360° stitching) use MGT, which can ingest ambiscape sessions directly via
`pip install "musicalgestures[soundscape]"`. ambiscape itself stays
dependency-light and never imports MGT.
```

- [ ] **Step 3: Extend the `vision.py` module docstring** with one closing line:

```python
For full video analysis (motion, pose, 360° handling) use MGT-python
(https://github.com/fourMs/MGT-python); this module deliberately stays a
lightweight, dependency-free companion.
```

- [ ] **Step 4: Commit both repos**

```bash
cd ~/github/MGT-python && git add README.md && \
  git commit -m "Document the MGT/ambiscape division of labour"
cd ~/github/ambiscape && git add README.md src/ambiscape/vision.py && \
  git commit -m "Document the ambiscape/MGT division of labour"
```

---

## Self-review notes

- Spec coverage: divide ownership (Task 7), thin overlaps (Task 7 now, Phase 2 for deprecations), shared time base (Task 3, consumed by 5), adapter (Task 5, extra + one direction only), sync utilities (Task 4), plus the two concrete ambiscape fixes surfaced by the Belfort session (Tasks 1–2). ✔
- `MgFeatures` accessors verified against `_features.py`: `.times` property (line 127) and `mgf[name]` item access (line 140)—used consistently in Tasks 3/5/6.
- Key namespaces consistent throughout: `aud_` (Task 5), `mot_` (Task 6), `vis_` (existing).
```

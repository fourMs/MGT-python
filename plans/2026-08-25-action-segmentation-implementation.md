# Action Segmentation and Three-Level Videogram — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce, for six long dance-improvisation recordings, a three-tier set of videogram+waveform sheets with talk/improvise segmentation, plus ELAN/TextGrid/TSV exports a student can annotate gestures in.

**Architecture:** One cached per-frame feature table per recording (`_tracks.py`, already shipped) feeds a hierarchy of three segment levels (`_hierarchy.py`), which feeds one composite renderer used at three time spans (`_timeline.py`) and three exporters (`_annotate.py`). Speech comes from `_voice.py` and is what makes the top level falsifiable rather than merely plausible.

**Tech Stack:** Python 3.12, numpy, matplotlib (Agg), OpenCV, ffmpeg, pytest, silero-vad (optional dependency, via torch.hub).

**Spec:** `plans/2026-08-25-action-segmentation-pipeline-design.md`

## Global Constraints

- **Branch:** all work on `action-segmentation`. Do not push. Do not create a release.
- **Native resolution.** Segmentation runs at 1920x1080. Downsampling is permitted for occupancy only, never for anything that produces a boundary.
- **Corpus facts:** six files, 1920x1080, 50 fps, AAC stereo 48 kHz, 2,202,696 frames total. Read frame counts from `HANDOVER.md`, never from a file size.
- **`tracks_run.json` is written by the runner alone, last.** Its absence is the signal a run did not finish. No other code may create it.
- **`tracks.json` is written by `extract_tracks_parallel` when it returns.** `build_pyramid` and `read_columns` both require it.
- **Never trust a file length in `analysis/`.** The memmaps are preallocated; read where data stops.
- **Every guard is verified by removing it and watching the test fail.** A test that passes the first time has told you nothing yet. Record in the commit message that you did this.
- **Tests live in `tests/`,** use `pytest`, and follow `tests/test_tracks.py`: synthetic material built with `ffmpeg -f lavfi`, known answers, and a module docstring naming the bug the test exists for.
- **Matplotlib is Agg** via `tests/conftest.py`. Never call `plt.show()`.
- **Do not modify the source video files** under `ProcessedData/Video/PanasonicDownsized/`.

---

## File Structure

| file | responsibility |
|---|---|
| `musicalgestures/_tracks.py` (modify) | add `check_tracks`; extraction otherwise unchanged |
| `musicalgestures/_actions.py` (modify) | add `range_mode` to `segment_actions` |
| `musicalgestures/_voice.py` (create) | speech spans; model wrapper + pure segment assembly |
| `musicalgestures/_hierarchy.py` (create) | `Hierarchy` container and `build_hierarchy` |
| `musicalgestures/_timeline.py` (create) | `decimate_minmax` and `render_timeline` |
| `musicalgestures/_annotate.py` (create) | `.eaf`, `.TextGrid`, `.tsv` writers and an `.eaf` reader |
| `musicalgestures/_select.py` (create) | stratified excerpt selection and salience measures |
| `tests/test_tracks_completeness.py` (create) | `check_tracks` against a truncated memmap |
| `tests/test_pyramid.py` (create) | `build_pyramid`, `read_columns` known answers |
| `tests/test_actions_range.py` (create) | the session-scale threshold fault |
| `tests/test_voice.py` (create) | probability-to-span assembly |
| `tests/test_hierarchy.py` (create) | planted hierarchy, containment, agreement labels |
| `tests/test_timeline.py` (create) | decimation keeps extremes; figure records its factor |
| `tests/test_annotate.py` (create) | round trip through `.eaf` and `.TextGrid` |
| `tests/test_select.py` (create) | stratification and seed reproducibility |

---

## Task 1: `check_tracks` — completeness that reads the data, not the file

**Files:**
- Modify: `musicalgestures/_tracks.py`
- Test: `tests/test_tracks_completeness.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `check_tracks(analysis_dir) -> dict` with keys `preallocated` (int), `last_nonzero` (int), `highest_marker` (int), `marker_gaps` (list[int]), `complete` (bool).

- [ ] **Step 1: Write the failing test**

Create `tests/test_tracks_completeness.py`:

```python
"""A preallocated memmap reports a finished extraction over a file of zeros.

The bug this exists for, measured on the 27 Nov dance session on 2026-08-25: an
extraction was killed at 08:28 with 44 per cent of the frames missing, and file size,
existence, `ls -la` and reading the last row ALL reported success. Three numbers
disagreed --- 475,688 preallocated, 264,008 written, 222,000 markers --- and each was
right about something different, so `check_tracks` reports all three and reconciles
none of them.
"""
import json

import numpy as np
import pytest

from musicalgestures._tracks import check_tracks


def _stalled(tmp_path, prealloc=1000, written=610, markers=(0, 100, 200, 300, 400, 500)):
    """An analysis dir shaped exactly like a killed run."""
    d = tmp_path / "analysis"
    d.mkdir()
    q = np.memmap(d / "qom.f4", dtype=np.float32, mode="w+", shape=(prealloc,))
    #: Nonzero up to `written`, zeros after, which is what a killed worker leaves.
    q[:written] = np.arange(1, written + 1, dtype=np.float32)
    q.flush()
    del q
    for m in markers:
        (d / f".done_{m}").write_text("100")
    return d


def test_reports_three_numbers_separately(tmp_path):
    d = _stalled(tmp_path)
    r = check_tracks(d)
    assert r["preallocated"] == 1000
    assert r["last_nonzero"] == 609        # index of the last written frame
    assert r["highest_marker"] == 500
    assert r["complete"] is False


def test_complete_only_when_run_json_exists(tmp_path):
    d = _stalled(tmp_path, written=1000)
    assert check_tracks(d)["complete"] is False
    (d / "tracks_run.json").write_text(json.dumps({"finished": "yes"}))
    assert check_tracks(d)["complete"] is True


def test_marker_gaps_are_named_not_counted(tmp_path):
    """A count cannot tell a contiguous run from one missing chunk 200."""
    d = _stalled(tmp_path, markers=(0, 100, 300, 400))
    assert check_tracks(d)["marker_gaps"] == [200]


def test_contiguous_markers_report_no_gaps(tmp_path):
    d = _stalled(tmp_path)
    assert check_tracks(d)["marker_gaps"] == []


def test_all_zero_file_is_not_mistaken_for_one_written_frame(tmp_path):
    """An extraction that wrote nothing must report -1, not 0."""
    d = tmp_path / "analysis"
    d.mkdir()
    m = np.memmap(d / "qom.f4", dtype=np.float32, mode="w+", shape=(500,))
    m.flush()
    del m
    assert check_tracks(d)["last_nonzero"] == -1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_tracks_completeness.py -v`
Expected: FAIL with `ImportError: cannot import name 'check_tracks'`.

- [ ] **Step 3: Write minimal implementation**

Append to `musicalgestures/_tracks.py`:

```python
def check_tracks(analysis_dir) -> dict:
    """What an extraction actually produced, read from the data rather than the file.

    `extract_tracks_parallel` preallocates its memmaps to an estimated frame count, so
    the files reach full size in the first second of a run and every cheap check ---
    size, existence, `ls -la`, the last row of the array --- reports a finished
    extraction over a file that may be mostly zeros.

    Three numbers are returned **separately and unreconciled**, because on a run killed
    at 08:28 on 2026-08-25 they disagreed by 42,000 and 211,000 frames and each was
    right about something different:

    - `preallocated` is the estimate the file was sized to, and was never a measurement;
    - `last_nonzero` is where data stops, because workers write continuously and only
      drop a marker when a whole chunk closes;
    - `highest_marker` is the last chunk that closed, and is what `resume=True` trusts.

    `complete` is true only when `tracks_run.json` exists, since that file is written
    last and by the runner alone.
    """
    d = Path(analysis_dir)
    qom_path = d / "qom.f4"
    if not qom_path.exists():
        raise FileNotFoundError(f"no qom.f4 in {d}")

    prealloc = qom_path.stat().st_size // 4
    q = np.memmap(qom_path, dtype=np.float32, mode="r", shape=(prealloc,))
    nz = np.flatnonzero(q)
    #: -1 rather than 0 for an empty file: frame 0 written and nothing written at all
    #: are different situations, and 0 would report the second as the first.
    last_nonzero = int(nz[-1]) if len(nz) else -1
    del q

    markers = sorted(int(p.name.split("_")[1]) for p in d.glob(".done_*"))
    step = markers[1] - markers[0] if len(markers) > 1 else 0
    gaps = []
    if step:
        expected = set(range(markers[0], markers[-1] + 1, step))
        gaps = sorted(expected - set(markers))

    return {"preallocated": prealloc,
            "last_nonzero": last_nonzero,
            "highest_marker": markers[-1] if markers else -1,
            "n_markers": len(markers),
            "marker_gaps": gaps,
            "complete": (d / "tracks_run.json").exists()}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_tracks_completeness.py -v`
Expected: 5 passed.

- [ ] **Step 5: Verify each guard by removing it**

Do all three, confirm each named test fails, then restore:

1. Change `last_nonzero = int(nz[-1]) if len(nz) else -1` to `... else 0`.
   Expected: `test_all_zero_file_is_not_mistaken_for_one_written_frame` FAILS.
2. Change `prealloc` to use `meta["frames"]` from `tracks.json` instead of the file size.
   Expected: `test_reports_three_numbers_separately` FAILS (no `tracks.json` exists).
3. Replace the gap computation with `gaps = []`.
   Expected: `test_marker_gaps_are_named_not_counted` FAILS.

- [ ] **Step 6: Run it against the real stalled directory**

Run:
```bash
cd ~/github/MGT-python && python -c "
from musicalgestures._tracks import check_tracks
d='/media/alexanje/Seagate Hub/aktiv/HybridDanceImprov/ProcessedData/Video/PanasonicDownsized/analysis/27CoLocated.Panasonic.A003C505_231127_DJ0B'
print(check_tracks(d))"
```
Expected: a dict whose `preallocated` is 475688 and whose other numbers are consistent with however far the running extraction has reached. If `complete` is True and `last_nonzero` is 475687, the run finished.

- [ ] **Step 7: Commit**

```bash
git add musicalgestures/_tracks.py tests/test_tracks_completeness.py
git commit -m "A preallocated memmap reports success over a file of zeros

check_tracks reads where the data stops, not where the file does, and reports
the preallocated length, the last non-zero frame and the highest chunk marker as
three separate numbers because on the killed 27 Nov run they disagreed by 42,000
and 211,000 frames and each was right about something different.

Each guard verified by removing it and watching the named test fail."
```

---

## Task 2: `build_pyramid` — a known answer, not a plausible one

**Files:**
- Test: `tests/test_pyramid.py`
- Modify: `musicalgestures/_tracks.py` only if the test finds a fault.

**Interfaces:**
- Consumes: `check_tracks` from Task 1 (not required, but available).
- Produces: no new API. Establishes that `build_pyramid(analysis_dir, which) -> list[Path]` is correct.

- [ ] **Step 1: Write the failing test**

Create `tests/test_pyramid.py`:

```python
"""build_pyramid and read_columns shipped in 1.14.2 with no tests and have never
produced output.

The property that matters is CONTAINMENT OF THE EXTREME. A pyramid exists so that a
movement lasting a few frames is still visible when the whole session is on one
screen, and a decimation that averages is exactly what makes such a movement vanish.
A plausibility check passes either way; these do not.
"""
import json

import numpy as np
import pytest

from musicalgestures._tracks import build_pyramid, read_columns


def _base(tmp_path, n=64, span=8, spike_at=37, spike_val=255):
    """A videogram base that is flat except for one bright column."""
    d = tmp_path / "analysis"
    d.mkdir()
    arr = np.full((n, span), 10, dtype=np.uint8)
    arr[spike_at, :] = spike_val
    arr.tofile(d / "videogram_v.u1")
    (d / "tracks.json").write_text(json.dumps({
        "frames": n, "fps": 10.0, "width": span, "height": span,
        "duration_s": n / 10.0,
        "qom": "qom.f4", "videogram_v": "videogram_v.u1",
        "videogram_h": "videogram_h.u1"}))
    return d


def test_the_spike_survives_every_level(tmp_path):
    """This is the whole point of the pyramid, so it is the first assertion."""
    d = _base(tmp_path)
    levels = build_pyramid(d, which="videogram_v")
    assert levels, "no levels written"
    for p in levels:
        arr = np.fromfile(p, dtype=np.uint8)
        assert arr.max() == 255, f"the spike was lost at {p.name}"


def test_a_mean_would_fail_this(tmp_path):
    """Guard on the guard: the flat background must NOT rise toward the spike."""
    d = _base(tmp_path)
    levels = build_pyramid(d, which="videogram_v")
    coarsest = np.fromfile(levels[-1], dtype=np.uint8)
    assert coarsest.min() == 10, "background changed; this is averaging, not max"


def test_each_level_halves_the_columns(tmp_path):
    d = _base(tmp_path, n=64, span=8)
    levels = build_pyramid(d, which="videogram_v")
    counts = [np.fromfile(p, dtype=np.uint8).size // 8 for p in levels]
    assert counts == [32, 16, 8, 4], counts


def test_pyramid_is_recorded_in_tracks_json(tmp_path):
    d = _base(tmp_path)
    build_pyramid(d, which="videogram_v")
    meta = json.loads((d / "tracks.json").read_text())
    assert meta["pyramid"]["videogram_v"], "a level a reader cannot find is not written"


def test_read_columns_returns_the_slice_asked_for(tmp_path):
    d = _base(tmp_path, n=64, span=8, spike_at=37)
    build_pyramid(d, which="videogram_v")
    #: max_columns high enough to force level 0, so the answer is exact.
    cols, spc = read_columns(d, start_s=3.0, end_s=4.0, max_columns=10000)
    assert cols.shape == (10, 8), cols.shape
    assert spc == pytest.approx(0.1)
    #: frame 37 is at t=3.7 s, i.e. index 7 of this slice.
    assert cols[7].max() == 255


def test_read_columns_coarsens_when_the_display_is_narrow(tmp_path):
    d = _base(tmp_path, n=64, span=8)
    build_pyramid(d, which="videogram_v")
    cols, spc = read_columns(d, start_s=0.0, end_s=6.4, max_columns=8)
    assert cols.shape[0] <= 16, cols.shape
    assert spc > 0.1, "no coarsening happened; the pyramid was not used"
    assert cols.max() == 255, "the spike vanished on the way to the screen"
```

- [ ] **Step 2: Run test to verify it fails or reveals a fault**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_pyramid.py -v`
Expected: these may pass, because the implementation exists. **If they all pass first time, that is the situation this project has been burned by.** Prove they can fail before believing them — do Step 3 regardless.

- [ ] **Step 3: Prove each test can fail**

In `build_pyramid`, change `cur = pair.max(axis=1)` to `cur = pair.mean(axis=1).astype(np.uint8)`.

Run: `cd ~/github/MGT-python && python -m pytest tests/test_pyramid.py -v`
Expected: `test_the_spike_survives_every_level`, `test_a_mean_would_fail_this` and `test_read_columns_coarsens_when_the_display_is_narrow` all FAIL.

Restore `pair.max(axis=1)`.

Then change `while cur.shape[0] > MIN_LEVEL_COLUMNS` to `while False`.
Expected: `test_each_level_halves_the_columns` and `test_pyramid_is_recorded_in_tracks_json` FAIL. Restore.

- [ ] **Step 4: Run the whole file green**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_pyramid.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_pyramid.py
git commit -m "build_pyramid and read_columns get the known answer they shipped without

The property is containment of the extreme: a pyramid exists so a movement of a
few frames is still visible with a whole session on screen, and averaging is what
makes it vanish. Verified by replacing max with mean and watching three tests fail."
```

---

## Task 3: a range that survives a session

**Files:**
- Modify: `musicalgestures/_actions.py`
- Test: `tests/test_actions_range.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `segment_actions(envelope, fs, threshold=0.15, min_duration=0.1, min_gap=0.1, source="envelope", range_mode="minmax", range_percentiles=(1.0, 99.0))`. `range_mode` is `"minmax"` (default, unchanged behaviour) or `"robust"`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_actions_range.py`:

```python
"""segment_actions thresholds on the envelope's GLOBAL range, which does not survive
a session.

The threshold is a fraction of max minus min. Over 2 h 38 min a handful of outlier
spikes raise `max` so far that the threshold sits below almost everything, and a
setting tuned on a clip silently means something else on a recording. Same shape as
the two long-video faults already fixed: invisible on a clip, wrong on a session, and
it does not raise.
"""
import numpy as np

from musicalgestures._actions import segment_actions


def _session_like(n=6000, fs=50.0):
    """Ten clear bursts on a low floor, plus three brief outlier spikes."""
    rng = np.random.default_rng(0)
    e = rng.uniform(0.0, 0.05, n)
    for k in range(10):
        i = 300 + k * 500
        e[i:i + 100] = 1.0
    #: The spikes: a few frames, forty times the bursts. A camera flash, a person
    #: crossing close to the lens --- the recording is full of them.
    for i in (1234, 3456, 5678):
        e[i:i + 3] = 40.0
    return e, fs


def test_minmax_loses_the_bursts_to_three_spikes():
    """The fault, asserted rather than described."""
    e, fs = _session_like()
    found = segment_actions(e, fs, threshold=0.15, min_duration=0.5)
    assert len(found) < 10, (
        f"expected the spikes to hide the bursts, got {len(found)}; "
        "if this fails the fault is gone and this test should be reconsidered")


def test_robust_finds_all_ten_bursts():
    e, fs = _session_like()
    found = segment_actions(e, fs, threshold=0.15, min_duration=0.5,
                            range_mode="robust")
    assert len(found) == 10, [f"{a.start:.1f}-{a.end:.1f}" for a in found]


def test_minmax_remains_the_default():
    """Nothing already measured may change."""
    e, fs = _session_like()
    assert segment_actions(e, fs, threshold=0.15, min_duration=0.5) == \
           segment_actions(e, fs, threshold=0.15, min_duration=0.5,
                           range_mode="minmax")


def test_robust_and_minmax_agree_when_there_are_no_outliers():
    """Robustness must not move boundaries on well-behaved material."""
    fs = 50.0
    e = np.zeros(2000)
    for k in range(4):
        e[200 + k * 400: 300 + k * 400] = 1.0
    a = segment_actions(e, fs, threshold=0.15, min_duration=0.5)
    b = segment_actions(e, fs, threshold=0.15, min_duration=0.5, range_mode="robust")
    assert [(x.start, x.end) for x in a] == [(x.start, x.end) for x in b]


def test_an_unknown_range_mode_is_refused():
    e, fs = _session_like()
    try:
        segment_actions(e, fs, range_mode="whatever")
    except ValueError:
        return
    raise AssertionError("an unknown range_mode silently did something")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_actions_range.py -v`
Expected: `test_robust_finds_all_ten_bursts` and `test_an_unknown_range_mode_is_refused` FAIL with `TypeError: unexpected keyword argument 'range_mode'`.

- [ ] **Step 3: Write minimal implementation**

In `musicalgestures/_actions.py`, change the signature and the two lines computing `level`:

```python
def segment_actions(envelope, fs: float, threshold: float = 0.15,
                    min_duration: float = 0.1, min_gap: float = 0.1,
                    source: str = "envelope", range_mode: str = "minmax",
                    range_percentiles: tuple = (1.0, 99.0)) -> list[Action]:
```

Add to the docstring's Args:

```
        range_mode (str): How the envelope's range is measured before `threshold` is
            taken as a fraction of it. ``"minmax"`` uses the full range and is the
            default, so nothing already measured changes. ``"robust"`` uses
            `range_percentiles` instead, which is what a recording of session length
            needs: a handful of outlier spikes otherwise raise the maximum so far that
            the threshold falls below everything and the real movement is never found.
        range_percentiles (tuple): The percentiles bounding the range when
            `range_mode="robust"`. Defaults to (1.0, 99.0).
```

Replace:

```python
    lo, hi = float(np.min(e)), float(np.max(e))
```

with:

```python
    if range_mode == "minmax":
        lo, hi = float(np.min(e)), float(np.max(e))
    elif range_mode == "robust":
        lo, hi = (float(v) for v in np.percentile(e, range_percentiles))
    else:
        raise ValueError(f"range_mode must be 'minmax' or 'robust', not {range_mode!r}")
```

Leave everything below unchanged, including the `if hi <= lo: return []` guard, which
now also correctly handles an envelope so flat that both percentiles coincide.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_actions_range.py tests/test_actions.py -v`
Expected: all pass, including the pre-existing `tests/test_actions.py` — the default path must be untouched.

- [ ] **Step 5: Verify the guard by removing it**

Change the `else: raise ValueError(...)` to `else: lo, hi = 0.0, 1.0`.
Expected: `test_an_unknown_range_mode_is_refused` FAILS. Restore.

Change `"robust"` to use `np.percentile(e, (0.0, 100.0))`.
Expected: `test_robust_finds_all_ten_bursts` FAILS (that is min/max again). Restore.

- [ ] **Step 6: Commit**

```bash
git add musicalgestures/_actions.py tests/test_actions_range.py
git commit -m "A threshold on the global range does not survive a session

segment_actions takes its threshold as a fraction of max minus min, so three
brief outlier spikes in a 2 h 38 min recording push the level below ten obvious
bursts and none of them is found. range_mode='robust' bounds the range by
percentile instead. minmax stays the default so nothing measured changes.

Both guards verified by removing them."
```

---

## Task 4: `_voice.py` — where speech is

**Files:**
- Create: `musicalgestures/_voice.py`
- Test: `tests/test_voice.py`

**Interfaces:**
- Consumes: `Action` from `musicalgestures._actions`.
- Produces:
  - `spans_from_probabilities(probs, hop_s, threshold=0.5, min_speech_s=0.25, min_silence_s=0.5, source="vad") -> list[Action]` — pure, no model.
  - `speech_segments(audio, sr=16000, **kw) -> list[Action]` — loads silero-vad and calls the above.

- [ ] **Step 1: Write the failing test**

Create `tests/test_voice.py`:

```python
"""The speech detector is split so the part with a right answer can be tested.

silero-vad is an optional dependency and a neural network: it cannot be asserted
against exactly and it cannot run in CI. What CAN be tested is everything after it ---
turning a probability track into spans, closing short silences and dropping short
bursts --- and that is where the errors of the kind this project keeps finding live.
So the model is one thin function and the logic is another, and this tests the logic.

Order matters and is the reason this file exists: silences are closed BEFORE short
spans are dropped. A single utterance with a breath in the middle would otherwise be
discarded as two fragments rather than kept as one.
"""
import numpy as np
import pytest

from musicalgestures._voice import spans_from_probabilities


def test_one_clear_utterance_becomes_one_span():
    probs = np.zeros(100)
    probs[20:60] = 0.9
    spans = spans_from_probabilities(probs, hop_s=0.1, min_speech_s=0.2)
    assert len(spans) == 1
    assert spans[0].start == pytest.approx(2.0)
    assert spans[0].end == pytest.approx(6.0)
    assert spans[0].source == "vad"


def test_a_breath_inside_an_utterance_does_not_split_it():
    """The ordering guard: close gaps first, then drop short spans."""
    probs = np.zeros(100)
    probs[20:40] = 0.9
    probs[43:60] = 0.9          # 0.3 s gap
    spans = spans_from_probabilities(probs, hop_s=0.1, min_speech_s=1.0,
                                     min_silence_s=0.5)
    assert len(spans) == 1, [f"{s.start:.1f}-{s.end:.1f}" for s in spans]
    assert spans[0].end - spans[0].start == pytest.approx(4.0)


def test_a_short_blip_is_dropped():
    probs = np.zeros(100)
    probs[50:51] = 0.9          # 0.1 s
    assert spans_from_probabilities(probs, hop_s=0.1, min_speech_s=0.25) == []


def test_silence_yields_no_spans_rather_than_an_error():
    assert spans_from_probabilities(np.zeros(100), hop_s=0.1) == []


def test_speech_to_the_final_sample_is_not_lost():
    """An interval left open at the end of the track must still close."""
    probs = np.zeros(50)
    probs[30:] = 0.9
    spans = spans_from_probabilities(probs, hop_s=0.1, min_speech_s=0.2)
    assert len(spans) == 1
    assert spans[0].end == pytest.approx(5.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_voice.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'musicalgestures._voice'`.

- [ ] **Step 3: Write minimal implementation**

Create `musicalgestures/_voice.py`:

```python
"""Where speech is in a recording, and nothing else about it.

This module decides WHERE someone is speaking. It does not transcribe, and it does not
identify anyone --- both are separate decisions with separate consequences, and putting
them in one function is how a detector quietly becomes a diariser.

**Why a detector and not a tagger.** A screening probe on this corpus put PANNs and
silero-vad on the same 60 s and they disagreed: the tagger returned `Speech 0.86` for a
minute holding 1.6 s of speech, along with `Snort`, `Gasp`, `Animal` and `Horse` for
dancers breathing. A clip-level tag answers "is there speech in this minute", which is
not the question. So the detector decides where speech is, the tagger decides whether
there is music, and their disagreements are recorded rather than resolved silently.

**Why the assembly is a separate function.** `spans_from_probabilities` has a right
answer and is tested; the model wrapper has neither and is kept as thin as it can be.
"""
from __future__ import annotations

import numpy as np

from musicalgestures._actions import Action

__all__ = ["spans_from_probabilities", "speech_segments"]


def spans_from_probabilities(probs, hop_s: float, threshold: float = 0.5,
                             min_speech_s: float = 0.25,
                             min_silence_s: float = 0.5,
                             source: str = "vad") -> list[Action]:
    """Turn a per-frame speech probability into spans.

    **Silences are closed before short spans are dropped, in that order.** A single
    utterance with a breath in the middle would otherwise be discarded as two
    fragments rather than kept as one --- the same ordering `segment_actions` uses,
    and for the same reason.

    Args:
        probs: Speech probability per frame, one dimension.
        hop_s (float): Seconds per frame of `probs`.
        threshold (float): Probability counting as speech. Defaults to 0.5.
        min_speech_s (float): Spans shorter than this are dropped. Defaults to 0.25.
        min_silence_s (float): Gaps shorter than this are closed. Defaults to 0.5.
        source (str): Recorded on each Action. Defaults to "vad".

    Returns:
        list: The speech spans found, in time order. Empty for silence, which is the
        correct answer for a recording with no speech rather than an error.
    """
    p = np.asarray(probs, float).ravel()
    if p.size == 0 or hop_s <= 0:
        return []

    active = p >= threshold
    #: Pad both ends so a span running to the final sample still closes. Without this
    #: an utterance at the end of a recording is silently lost.
    edges = np.diff(np.concatenate(([0], active.view(np.int8), [0])))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)

    spans = [[float(a) * hop_s, float(b) * hop_s] for a, b in zip(starts, ends)]
    if not spans:
        return []

    merged = [spans[0]]
    for s, e in spans[1:]:
        if s - merged[-1][1] < min_silence_s:
            merged[-1][1] = e
        else:
            merged.append([s, e])

    return [Action(start=s, end=e, source=source)
            for s, e in merged if e - s >= min_speech_s]


def speech_segments(audio, sr: int = 16000, threshold: float = 0.5,
                    min_speech_s: float = 0.25, min_silence_s: float = 0.5,
                    source: str = "vad") -> list[Action]:
    """Speech spans in an audio file or array, via silero-vad.

    silero-vad is an optional dependency. It is loaded here and nowhere else, so a
    machine without it can still import everything that does not detect speech.

    Args:
        audio: Path to an audio file, or a one-dimensional array already at `sr`.
        sr (int): Sample rate. silero-vad wants 16000. Defaults to 16000.

    Returns:
        list: Speech spans, in seconds on the audio's own clock.
    """
    try:
        import torch
    except ImportError as exc:                                   # pragma: no cover
        raise ImportError(
            "speech_segments needs torch and silero-vad. Install with "
            "`pip install torch silero-vad`, or call spans_from_probabilities "
            "directly if you already have a probability track.") from exc

    if isinstance(audio, (str, bytes)) or hasattr(audio, "__fspath__"):
        import librosa
        wav, sr = librosa.load(str(audio), sr=sr, mono=True)
    else:
        wav = np.asarray(audio, dtype=np.float32).ravel()

    model, _ = torch.hub.load("snakers4/silero-vad", "silero_vad", trust_repo=True)
    #: silero-vad consumes fixed windows: 512 samples at 16 kHz. The hop is therefore
    #: known exactly and is not something to infer from the output length.
    win = 512 if sr == 16000 else 256
    n = (len(wav) // win) * win
    probs = []
    with torch.no_grad():
        for i in range(0, n, win):
            probs.append(float(model(torch.from_numpy(wav[i:i + win]), sr).item()))

    return spans_from_probabilities(np.array(probs), hop_s=win / sr,
                                    threshold=threshold, min_speech_s=min_speech_s,
                                    min_silence_s=min_silence_s, source=source)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_voice.py -v`
Expected: 5 passed.

- [ ] **Step 5: Verify each guard by removing it**

1. Remove the `[0]` padding on both ends of the `edges` computation (use
   `np.diff(active.view(np.int8))`).
   Expected: `test_speech_to_the_final_sample_is_not_lost` FAILS. Restore.
2. Swap the order: filter by `min_speech_s` first, then merge.
   Expected: `test_a_breath_inside_an_utterance_does_not_split_it` FAILS. Restore.

- [ ] **Step 6: Commit**

```bash
git add musicalgestures/_voice.py tests/test_voice.py
git commit -m "Where speech is, split from the model that decides it

spans_from_probabilities has a right answer and is tested; the silero-vad wrapper
has neither and is kept thin. Silences close before short spans are dropped, so an
utterance with a breath in it stays one span, and both ends are padded so speech
running to the final sample is not lost. Both guards verified by removing them."
```

---

## Task 5: `_hierarchy.py` — the container, and containment

**Files:**
- Create: `musicalgestures/_hierarchy.py`
- Test: `tests/test_hierarchy.py`

**Interfaces:**
- Consumes: `Action` from `_actions`, `segment_actions` with `range_mode` from Task 3, `spans_from_probabilities` from Task 4.
- Produces:
  - `class Hierarchy` with `.levels: dict[str, list[Action]]`, `.children(action, level) -> list[Action]`, `.parent(action, level) -> Action | None`, `.to_dict() -> dict`.
  - `part_level(qom, fs, speech, quiet_percentile=25.0, min_part_s=60.0, tolerance_s=5.0) -> list[Action]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_hierarchy.py`:

```python
"""Levels are checked for CONTAINMENT, not for plausibility.

A segmenter that returns roughly the right number of roughly the right-looking spans
passes any eyeball check. What it must actually do is nest: every action lies inside a
phrase, every phrase inside a part. So the fixture plants a hierarchy --- three
phrases of four actions --- and the assertions are about containment.

The part level is the one with a claim worth falsifying. ARJ's observation is that the
dancers talk between improvisations and hardly at all while dancing, so an
improvisation is where motion is high and speech is absent, and the gap between them
is the converse. Two weak signals that agree beat one strong one. Where they DISAGREE
the boundary is a guess, and it must be recorded as one rather than smoothed over.
"""
import numpy as np
import pytest

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy, part_level


def _planted():
    """Three phrases of four actions, on a 50 fps grid."""
    actions, phrases = [], []
    for p in range(3):
        p0 = p * 100.0
        phrases.append(Action(start=p0, end=p0 + 80.0, source="phrase"))
        for a in range(4):
            a0 = p0 + a * 20.0
            actions.append(Action(start=a0, end=a0 + 10.0, source="action"))
    parts = [Action(start=0.0, end=300.0, source="part")]
    return Hierarchy(levels={"part": parts, "phrase": phrases, "action": actions})


def test_every_action_has_exactly_one_phrase_parent():
    h = _planted()
    for a in h.levels["action"]:
        assert h.parent(a, "phrase") is not None, f"{a} is an orphan"


def test_each_phrase_has_its_four_actions():
    h = _planted()
    for ph in h.levels["phrase"]:
        assert len(h.children(ph, "action")) == 4


def test_children_are_not_shared_between_phrases():
    """Containment by time must not double-count a span on a boundary."""
    h = _planted()
    seen = [id(c) for ph in h.levels["phrase"] for c in h.children(ph, "action")]
    assert len(seen) == len(set(seen)) == 12


def test_a_level_can_be_recomputed_without_touching_the_others():
    """The reason containment is computed on demand rather than stored as a tree."""
    h = _planted()
    h.levels["action"] = h.levels["action"][:4]
    assert len(h.children(h.levels["phrase"][0], "action")) == 4
    assert len(h.children(h.levels["phrase"][1], "action")) == 0


def _session(fs=50.0):
    """Two improvisations with a talking gap between them.

    Motion high 0-100 s and 200-300 s; speech only in 100-200 s. This is the shape
    ARJ described, made into a fixture.
    """
    n = int(300 * fs)
    qom = np.full(n, 0.02)
    qom[: int(100 * fs)] = 1.0
    qom[int(200 * fs):] = 1.0
    speech = [Action(start=110.0, end=190.0, source="vad")]
    return qom, fs, speech


def test_two_improvisations_are_found():
    qom, fs, speech = _session()
    parts = part_level(qom, fs, speech, min_part_s=30.0)
    improv = [p for p in parts if p.labels.get("part") == "improvisation"]
    assert len(improv) == 2, [(p.start, p.end, p.labels) for p in parts]


def test_the_talking_section_is_labelled_talk():
    qom, fs, speech = _session()
    parts = part_level(qom, fs, speech, min_part_s=30.0)
    talk = [p for p in parts if p.labels.get("part") == "talk"]
    assert len(talk) == 1
    assert talk[0].start == pytest.approx(100.0, abs=5.0)


def test_agreement_is_recorded_on_every_part():
    """The falsifiable claim: which boundaries both signals support."""
    qom, fs, speech = _session()
    for p in part_level(qom, fs, speech, min_part_s=30.0):
        assert p.features["agreement"] in {"both", "motion_only", "vad_only"}


def test_a_boundary_only_one_signal_supports_is_marked_as_such():
    """Motion drops but nobody speaks: the boundary is a guess and must say so."""
    qom, fs, _ = _session()
    parts = part_level(qom, fs, speech=[], min_part_s=30.0)
    assert any(p.features["agreement"] == "motion_only" for p in parts), \
        [p.features for p in parts]


def test_no_speech_and_no_motion_change_yields_one_part():
    fs = 50.0
    parts = part_level(np.full(int(300 * fs), 1.0), fs, speech=[], min_part_s=30.0)
    assert len(parts) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_hierarchy.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'musicalgestures._hierarchy'`.

- [ ] **Step 3: Write minimal implementation**

Create `musicalgestures/_hierarchy.py`:

```python
"""Levels of segmentation over one recording, related by containment.

Three levels, coarse to fine: `part` is talking versus improvising, `phrase` is a run
of related activity, `action` is an individual movement. Each is a list of `Action`,
which already carries `features` for what was measured and `labels` for what is
claimed, and the distinction between those two is the one thing here worth protecting.

**Containment is computed on demand rather than stored as a tree.** A level is a
hypothesis, and every one of them will be recomputed --- a stored tree would make
re-cutting the action level invalidate the phrase level that has nothing to do with
it. Asking which phrase contains an action is cheap; keeping a tree correct is not.

**Nothing here claims the levels are right.** They are a draft for a person to
correct, which is why `_annotate` exists.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from musicalgestures._actions import Action, segment_actions

__all__ = ["Hierarchy", "part_level"]


@dataclass
class Hierarchy:
    """Named levels of `Action`, and the containment between them.

    Attributes:
        levels (dict): Level name to the list of Actions at that level, in time order.
    """

    levels: dict = field(default_factory=dict)

    def children(self, action: Action, level: str) -> list[Action]:
        """The Actions at `level` whose midpoint falls inside `action`.

        **Midpoint, not overlap.** A span that merely overlaps two parents would be
        returned by both, and twelve actions under three phrases would count as
        fourteen. The midpoint puts every child under exactly one parent.
        """
        out = []
        for c in self.levels.get(level, []):
            mid = 0.5 * (c.start + c.end)
            if action.start <= mid < action.end:
                out.append(c)
        return out

    def parent(self, action: Action, level: str) -> Action | None:
        """The Action at `level` containing `action`'s midpoint, or None."""
        mid = 0.5 * (action.start + action.end)
        for p in self.levels.get(level, []):
            if p.start <= mid < p.end:
                return p
        return None

    def to_dict(self) -> dict:
        """A plain structure for JSON, one entry per level."""
        return {name: [{"start": a.start, "end": a.end, "source": a.source,
                        "labels": a.labels, "features": a.features}
                       for a in spans]
                for name, spans in self.levels.items()}


def _speech_track(speech, n: int, fs: float) -> np.ndarray:
    """A boolean per frame: is anyone speaking."""
    track = np.zeros(n, dtype=bool)
    for s in speech or []:
        track[max(0, int(s.start * fs)): min(n, int(s.end * fs))] = True
    return track


def part_level(qom, fs: float, speech, quiet_percentile: float = 25.0,
               min_part_s: float = 60.0, tolerance_s: float = 5.0,
               smooth_s: float = 10.0) -> list[Action]:
    """Cut a session into improvisations and the talking between them.

    **Not from motion alone.** ARJ's observation about this corpus is that the dancers
    talk between improvisations and hardly at all while dancing, so a
    between-improvisation section is where speech is present AND motion is low, and an
    improvisation is the converse. Two weak signals that agree beat one strong one,
    and this keys on what the session does rather than on how an envelope happens to
    bend.

    It also makes the segmentation falsifiable. Every part records in `features` which
    signals supported its start:

    - ``"both"``   --- the motion floor and the detector marked the same transition;
    - ``"motion_only"`` --- motion dropped where nobody spoke;
    - ``"vad_only"``    --- somebody spoke where motion did not drop.

    Only ``"both"`` is an assertion. The other two are guesses and the renderer draws
    them differently, so a reader sees which boundaries to distrust without reading a
    log.

    Args:
        qom: Quantity of motion per frame.
        fs (float): Frames per second of `qom`.
        speech: Speech spans, as returned by `_voice.speech_segments`. May be empty.
        quiet_percentile (float): Motion below this percentile of the session counts
            as low. A percentile rather than a fraction of the range, because a
            session's outlier spikes make the range meaningless.
        min_part_s (float): Parts shorter than this are absorbed into their neighbour.
        tolerance_s (float): How close two transitions must be to count as agreeing.
        smooth_s (float): Window for smoothing the envelope before thresholding.

    Returns:
        list: Parts in time order, each labelled ``"improvisation"`` or ``"talk"``.
    """
    e = np.asarray(qom, float).ravel()
    n = len(e)
    if n == 0 or fs <= 0:
        return []

    #: Smooth before thresholding: the part level is about minutes, and an unsmoothed
    #: envelope crosses any level hundreds of times a minute.
    w = max(1, int(smooth_s * fs))
    kernel = np.ones(w) / w
    smooth = np.convolve(e, kernel, mode="same")

    quiet_level = float(np.percentile(smooth, quiet_percentile))
    moving = smooth > quiet_level
    speaking = _speech_track(speech, n, fs)

    #: Improvising where motion is up; talking where it is not. Speech refines this
    #: rather than deciding it, because the dancers are sometimes quiet between
    #: improvisations too.
    improv = moving & ~speaking

    #: Runs of the same state, padded so a run reaching the end still closes.
    changes = np.flatnonzero(np.diff(np.concatenate(([~improv[0]], improv))))
    bounds = [0, *changes.tolist(), n]
    spans = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)
             if bounds[i + 1] > bounds[i]]

    #: Absorb runs too short to be a part of a session, smallest first, so a single
    #: pass cannot leave a fragment behind.
    merged = []
    for a, b in spans:
        if merged and (b - a) < min_part_s * fs:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    if len(merged) > 1 and (merged[0][1] - merged[0][0]) < min_part_s * fs:
        merged[1] = (merged[0][0], merged[1][1])
        merged.pop(0)

    tol = int(tolerance_s * fs)
    motion_edges = set(np.flatnonzero(np.diff(moving.astype(np.int8))).tolist())
    speech_edges = set(np.flatnonzero(np.diff(speaking.astype(np.int8))).tolist())

    parts = []
    for a, b in merged:
        near_motion = any(abs(a - m) <= tol for m in motion_edges)
        near_speech = any(abs(a - s) <= tol for s in speech_edges)
        if a == 0:
            agreement = "both"          # the recording's own start, not a guess
        elif near_motion and near_speech:
            agreement = "both"
        elif near_motion:
            agreement = "motion_only"
        else:
            agreement = "vad_only"

        frac_moving = float(moving[a:b].mean()) if b > a else 0.0
        frac_speech = float(speaking[a:b].mean()) if b > a else 0.0
        parts.append(Action(
            start=a / fs, end=b / fs, source="part",
            labels={"part": "improvisation" if frac_moving > 0.5 and
                    frac_speech < 0.5 else "talk"},
            features={"agreement": agreement,
                      "fraction_moving": round(frac_moving, 3),
                      "fraction_speech": round(frac_speech, 3),
                      "quiet_level": quiet_level}))
    return parts
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_hierarchy.py -v`
Expected: 10 passed. If the part-level tests fail on boundary placement, adjust
`smooth_s` in the fixture call rather than loosening the assertion — the assertion is
the requirement.

- [ ] **Step 5: Verify each guard by removing it**

1. In `children`, replace the midpoint test with an overlap test (`c.start < action.end and action.start < c.end`).
   Expected: `test_children_are_not_shared_between_phrases` FAILS. Restore.
2. Remove the `agreement` computation and set it always to `"both"`.
   Expected: `test_a_boundary_only_one_signal_supports_is_marked_as_such` FAILS. Restore.
3. Replace `quiet_level` with `smooth.mean()`.
   Expected: at least one of the two-improvisation tests FAILS. Restore.

- [ ] **Step 6: Commit**

```bash
git add musicalgestures/_hierarchy.py tests/test_hierarchy.py
git commit -m "Three levels, related by containment, and a part level that can be wrong

Containment is computed on demand rather than stored, so re-cutting one level does
not invalidate another, and children are matched by midpoint so a span on a boundary
belongs to exactly one parent.

The part level cuts on motion and speech together, per ARJ's observation that the
dancers talk between improvisations and hardly at all while dancing, and records on
every boundary whether both signals supported it. Only 'both' is an assertion; the
renderer draws the other two differently.

Three guards verified by removing them."
```

---

## Task 6: `_timeline.py` — decimation that keeps what matters

**Files:**
- Create: `musicalgestures/_timeline.py`
- Test: `tests/test_timeline.py`

**Interfaces:**
- Consumes: `read_columns` from `_tracks`, `Hierarchy` from `_hierarchy`.
- Produces:
  - `decimate_minmax(x, n_columns) -> tuple[np.ndarray, np.ndarray, int]` returning `(mins, maxs, factor)`.
  - `render_timeline(analysis_dir, start_s=0.0, end_s=None, panels=("videogram_v","qom","waveform","speech"), levels=("part",), hierarchy=None, speech=None, audio=None, out=None, dpi=150, title=None) -> Path`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_timeline.py`:

```python
"""A decimated strip that does not say so invites a reader to measure timings off it.

Two properties, and both have burned somebody:

1. **min/max, never a mean.** An overview cannot show 475,680 columns. The whole
   purpose of the overview is to find the brief events worth zooming into, and a mean
   removes exactly those.
2. **the reduction factor is on the figure.** A strip drawn at 1 column per 240 frames
   looks like a strip drawn at 1 column per frame. Printing the factor is what stops a
   reader taking a timing off a picture that cannot support one.
"""
import numpy as np
import pytest

from musicalgestures._timeline import decimate_minmax


def test_a_one_sample_spike_survives():
    x = np.zeros(10000)
    x[4321] = 1.0
    mins, maxs, factor = decimate_minmax(x, 100)
    assert maxs.max() == 1.0, "the spike was averaged away"
    assert factor == 100


def test_a_one_sample_trough_survives():
    x = np.ones(10000)
    x[4321] = -1.0
    mins, maxs, factor = decimate_minmax(x, 100)
    assert mins.min() == -1.0


def test_the_spike_lands_in_the_right_column():
    x = np.zeros(10000)
    x[4321] = 1.0
    _, maxs, _ = decimate_minmax(x, 100)
    assert int(np.argmax(maxs)) == 43


def test_no_decimation_when_it_already_fits():
    x = np.arange(50.0)
    mins, maxs, factor = decimate_minmax(x, 100)
    assert factor == 1
    assert np.array_equal(mins, x) and np.array_equal(maxs, x)


def test_a_mean_would_fail_the_spike_test():
    """Guard on the guard, stated so the property cannot be quietly weakened."""
    x = np.zeros(10000)
    x[4321] = 1.0
    naive = x[: 100 * 100].reshape(100, 100).mean(axis=1)
    assert naive.max() < 0.05, "the fixture is wrong; a mean should lose this"


def test_the_tail_is_not_dropped():
    """10000 samples into 3 columns leaves a remainder that must still be drawn."""
    x = np.zeros(10000)
    x[-1] = 5.0
    mins, maxs, factor = decimate_minmax(x, 3)
    assert maxs[-1] == 5.0, "the last partial column was discarded"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_timeline.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'musicalgestures._timeline'`.

- [ ] **Step 3: Write the decimation**

Create `musicalgestures/_timeline.py` beginning with:

```python
"""The composite sheet: videogram, envelope, waveform and segmentation on one axis.

One renderer, three configurations. The overview, the improvisation sheet and the
action strip differ only in the span of time they cover and in which level's
boundaries they draw, so they are one function called three ways rather than three
functions that drift apart.

**Boundaries are drawn across every panel**, so a proposed cut is read against the
motion, the sound and the picture at once rather than against whichever signal
produced it.

**Video and audio decimate independently.** The design's rule is that audio stays on
its own clock and is never binned to the 20 ms video frame grid, because forcing both
onto one grid quantises away the very asymmetry this corpus was recorded to study.
That rule holds at render time too: each panel reduces its own samples to the
available pixel columns.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

__all__ = ["decimate_minmax", "render_timeline"]


def decimate_minmax(x, n_columns: int):
    """Reduce a signal to `n_columns`, keeping the extreme of each column.

    **Never a mean.** An overview exists to show where the brief events are, and a
    mean is precisely what removes them: a single frame of large movement in a
    four-second column is the thing a viewer zoomed out to find.

    The final partial column is kept rather than truncated away, so the end of a
    recording is drawn.

    Args:
        x: The signal, one dimension.
        n_columns (int): How many output columns are wanted.

    Returns:
        tuple: (mins, maxs, factor), where `factor` is samples per column and is
        meant to be printed on the figure.
    """
    v = np.asarray(x, float).ravel()
    n = v.size
    if n == 0:
        return np.zeros(0), np.zeros(0), 1
    if n_columns >= n:
        return v.copy(), v.copy(), 1

    factor = int(np.ceil(n / n_columns))
    pad = (-n) % factor
    if pad:
        #: Pad with the edge value, not with zeros: zeros would invent a trough at
        #: the end of every recording whose length is not a multiple of the factor.
        v = np.concatenate([v, np.full(pad, v[-1])])
    block = v.reshape(-1, factor)
    return block.min(axis=1), block.max(axis=1), factor
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_timeline.py -v`
Expected: 6 passed.

- [ ] **Step 5: Verify each guard by removing it**

1. Change `block.max(axis=1)` to `block.mean(axis=1)` for both returns.
   Expected: `test_a_one_sample_spike_survives` and `test_a_one_sample_trough_survives` FAIL. Restore.
2. Replace the padding with truncation: `v = v[: (n // factor) * factor]` and drop
   the `pad` block entirely.
   Expected: `test_the_tail_is_not_dropped` FAILS. Restore.
3. Change the padding from `np.full(pad, v[-1])` to `np.zeros(pad)` and add this
   assertion to `test_the_tail_is_not_dropped`: `assert mins[-1] == 0.0` must become
   true, i.e. a trough was invented at the end. Confirm it, then restore the edge
   padding and drop the extra assertion.

- [ ] **Step 6: Commit**

```bash
git add musicalgestures/_timeline.py tests/test_timeline.py
git commit -m "Decimation that keeps the events an overview exists to find

min/max per column, never a mean: a single frame of large movement inside a
four-second column is exactly what a viewer zoomed out to look for. The tail is
padded with the edge value rather than truncated or zero-filled, so the end of a
recording is drawn and no trough is invented there.

Both guards verified by removing them."
```

---

## Task 7: `render_timeline` — the sheet itself

**Files:**
- Modify: `musicalgestures/_timeline.py`
- Test: `tests/test_timeline_render.py`

**Interfaces:**
- Consumes: `decimate_minmax` (Task 6), `read_columns` (`_tracks`), `Hierarchy` and `part_level` (Task 5).
- Produces: `render_timeline(...) -> Path` as declared in Task 6.

- [ ] **Step 1: Write the failing test**

Create `tests/test_timeline_render.py`:

```python
"""The sheet must record what it is showing, or a reader will measure off it.

These are structural assertions on a figure, which is as much as a figure can be
tested for: that it was written, that it carries its reduction factor and its time
range as text, and that a boundary the segmenter is unsure about is drawn differently
from one it is sure about. The last is the important one --- it is the difference
between a picture that reports a hypothesis and one that asserts a result.
"""
import json

import numpy as np
import pytest

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy
from musicalgestures._timeline import render_timeline


@pytest.fixture
def analysis(tmp_path):
    """A small but complete analysis directory."""
    d = tmp_path / "analysis"
    d.mkdir()
    n, H, W, fps = 3000, 16, 24, 50.0
    rng = np.random.default_rng(0)
    qom = (rng.uniform(0, 0.1, n)).astype(np.float32)
    qom[500:1000] = 1.0
    qom[2000:2500] = 1.0
    qom.tofile(d / "qom.f4")
    np.full((n, H), 40, dtype=np.uint8).tofile(d / "videogram_v.u1")
    np.full((n, W), 40, dtype=np.uint8).tofile(d / "videogram_h.u1")
    (d / "tracks.json").write_text(json.dumps({
        "frames": n, "fps": fps, "width": W, "height": H, "duration_s": n / fps,
        "qom": "qom.f4", "videogram_v": "videogram_v.u1",
        "videogram_h": "videogram_h.u1"}))
    return d


@pytest.fixture
def hierarchy():
    return Hierarchy(levels={"part": [
        Action(start=0.0, end=20.0, source="part", labels={"part": "improvisation"},
               features={"agreement": "both"}),
        Action(start=20.0, end=40.0, source="part", labels={"part": "talk"},
               features={"agreement": "motion_only"}),
        Action(start=40.0, end=60.0, source="part", labels={"part": "improvisation"},
               features={"agreement": "both"})]})


def test_a_sheet_is_written(analysis, hierarchy):
    out = render_timeline(analysis, hierarchy=hierarchy, levels=("part",))
    assert out.exists() and out.stat().st_size > 0


def test_the_reduction_factor_is_on_the_figure(analysis, hierarchy):
    """A decimated strip that does not say so is a trap."""
    out = render_timeline(analysis, hierarchy=hierarchy, levels=("part",))
    side = out.with_suffix(".json")
    meta = json.loads(side.read_text())
    assert meta["decimation_factor"] >= 1
    assert meta["printed_on_figure"] is True


def test_the_time_range_is_recorded(analysis, hierarchy):
    out = render_timeline(analysis, start_s=10.0, end_s=30.0, hierarchy=hierarchy)
    meta = json.loads(out.with_suffix(".json").read_text())
    assert meta["start_s"] == 10.0 and meta["end_s"] == 30.0


def test_uncertain_boundaries_are_drawn_differently(analysis, hierarchy):
    """The falsifiable claim, made visible."""
    out = render_timeline(analysis, hierarchy=hierarchy, levels=("part",))
    meta = json.loads(out.with_suffix(".json").read_text())
    styles = {b["agreement"]: b["linestyle"] for b in meta["boundaries"]}
    assert styles["both"] == "solid"
    assert styles["motion_only"] == "dashed"
    assert styles["both"] != styles["motion_only"]


def test_a_span_shorter_than_one_column_still_renders(analysis, hierarchy):
    out = render_timeline(analysis, start_s=0.0, end_s=0.2, hierarchy=hierarchy)
    assert out.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_timeline_render.py -v`
Expected: FAIL with `ImportError: cannot import name 'render_timeline'`.

- [ ] **Step 3: Write the renderer**

Append to `musicalgestures/_timeline.py`:

```python
#: Solid asserts, dashed guesses. The part level records which of its boundaries both
#: the motion floor and the speech detector supported; drawing them the same way would
#: throw that away at exactly the point a reader would use it.
_BOUNDARY_STYLE = {"both": "solid", "motion_only": "dashed",
                   "vad_only": "dashed", None: "dotted"}


def render_timeline(analysis_dir, start_s: float = 0.0, end_s=None,
                    panels=("videogram_v", "qom", "waveform", "speech"),
                    levels=("part",), hierarchy=None, speech=None, audio=None,
                    out=None, dpi: int = 150, title=None):
    """One sheet: videogram, motion, sound and segmentation on a shared time axis.

    The same function makes all three tiers. An overview passes the whole file and
    `levels=("part",)`; an improvisation sheet passes one part's span and
    `levels=("phrase",)`; an action strip passes one phrase and `levels=("action",)`.

    A sidecar `.json` is written beside the image recording the decimation factor, the
    time range and every boundary drawn, so a figure can always be traced back to the
    numbers behind it.

    Args:
        analysis_dir: Directory holding `tracks.json` and the memmaps.
        start_s (float): Where the sheet begins, in seconds.
        end_s: Where it ends. None means the end of the recording.
        panels (tuple): Which panels to stack, top to bottom.
        levels (tuple): Which hierarchy levels to draw boundaries for.
        hierarchy: A `Hierarchy`, or None to draw no boundaries.
        speech: Speech spans for the `speech` panel, or None.
        audio: Path to a WAV for the `waveform` panel, or None to skip it.
        out: Output path. Defaults to a name built from the time range.
        dpi (int): Figure resolution. Defaults to 150.
        title: Figure title. Defaults to the directory name and time range.

    Returns:
        Path: The image written.
    """
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    d = Path(analysis_dir)
    meta = json.loads((d / "tracks.json").read_text())
    fps = float(meta["fps"])
    end_s = float(meta["duration_s"]) if end_s is None else float(end_s)
    start_s = max(0.0, float(start_s))

    #: The number of columns the sheet can actually show. Everything decimates to
    #: this, and nothing is drawn at a resolution the page cannot carry.
    fig_w_in = 16.0
    n_columns = int(fig_w_in * dpi)

    drawn = [p for p in panels if p != "waveform" or audio is not None]
    fig, axes = plt.subplots(len(drawn), 1, figsize=(fig_w_in, 2.0 * len(drawn)),
                             sharex=True, dpi=dpi,
                             gridspec_kw={"hspace": 0.12})
    if len(drawn) == 1:
        axes = [axes]

    factor = 1
    i0, i1 = int(start_s * fps), min(int(end_s * fps), int(meta["frames"]))
    i1 = max(i1, i0 + 1)

    for ax, panel in zip(axes, drawn):
        if panel in ("videogram_v", "videogram_h"):
            from musicalgestures._tracks import read_columns
            cols, spc = read_columns(d, start_s, end_s, max_columns=n_columns,
                                     which=panel)
            if cols.size:
                ax.imshow(cols.T, aspect="auto", origin="lower", cmap="magma",
                          extent=(start_s, end_s, 0, cols.shape[1]))
                factor = max(factor, int(round(spc * fps)))
            ax.set_ylabel(panel.replace("videogram_", "videogram "))
            ax.set_yticks([])

        elif panel == "qom":
            q = np.memmap(d / meta["qom"], dtype=np.float32, mode="r",
                          shape=(int(meta["frames"]),))[i0:i1]
            mins, maxs, f = decimate_minmax(np.asarray(q, float), n_columns)
            factor = max(factor, f)
            t = np.linspace(start_s, end_s, len(maxs))
            #: Fill between the extremes rather than plotting a line through a mean:
            #: the band IS the information at this magnification.
            ax.fill_between(t, mins, maxs, linewidth=0, color="#333333")
            ax.set_ylabel("quantity of motion")

        elif panel == "waveform":
            import librosa
            wav, sr = librosa.load(str(audio), sr=None, mono=True,
                                   offset=start_s, duration=end_s - start_s)
            #: Audio decimates on its OWN clock, to the same pixel columns. It is not
            #: binned to the 20 ms video grid, here or anywhere.
            mins, maxs, _ = decimate_minmax(wav, n_columns)
            t = np.linspace(start_s, end_s, len(maxs))
            ax.fill_between(t, mins, maxs, linewidth=0, color="#1f4e79")
            ax.set_ylabel("audio")

        elif panel == "speech":
            for s in speech or []:
                if s.end > start_s and s.start < end_s:
                    ax.add_patch(Rectangle((s.start, 0.0), s.end - s.start, 1.0,
                                           color="#c44e52", alpha=0.7, linewidth=0))
            ax.set_ylim(0, 1)
            ax.set_ylabel("speech")
            ax.set_yticks([])

        ax.set_xlim(start_s, end_s)
        ax.grid(axis="x", alpha=0.15)

    boundaries = []
    if hierarchy is not None:
        for level in levels:
            for a in hierarchy.levels.get(level, []):
                if a.end <= start_s or a.start >= end_s:
                    continue
                agreement = a.features.get("agreement")
                style = _BOUNDARY_STYLE.get(agreement, "dotted")
                for ax in axes:
                    ax.axvline(a.start, color="#d95f02", linestyle=style,
                               linewidth=1.2, alpha=0.9)
                axes[0].annotate(a.labels.get(level, level),
                                 (a.start, 1.02), xycoords=("data", "axes fraction"),
                                 fontsize=7, rotation=90, va="bottom",
                                 color="#d95f02")
                boundaries.append({"level": level, "start": a.start, "end": a.end,
                                   "agreement": agreement, "linestyle": style,
                                   "label": a.labels.get(level)})

    axes[-1].set_xlabel("time (s), session clock")
    note = (f"1 column = {factor} frames ({factor / fps:.3f} s); "
            f"min/max per column, not mean")
    fig.text(0.995, 0.005, note, ha="right", va="bottom", fontsize=7, color="#555555")
    fig.suptitle(title or f"{d.name}  {start_s:.1f}–{end_s:.1f} s", fontsize=10)

    out = Path(out) if out else d / f"sheet_{int(start_s):06d}_{int(end_s):06d}.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)

    out.with_suffix(".json").write_text(json.dumps(
        {"image": out.name, "start_s": start_s, "end_s": end_s,
         "decimation_factor": factor, "printed_on_figure": True,
         "seconds_per_column": factor / fps, "panels": list(drawn),
         "levels": list(levels), "boundaries": boundaries,
         "note": ("min/max per column, never a mean: a brief movement is what an "
                  "overview exists to find and a mean is what removes it")},
        indent=1) + "\n")
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_timeline_render.py -v`
Expected: 5 passed.

- [ ] **Step 5: Verify each guard by removing it**

1. Set `_BOUNDARY_STYLE` so every agreement maps to `"solid"`.
   Expected: `test_uncertain_boundaries_are_drawn_differently` FAILS. Restore.
2. Remove `"printed_on_figure": True` and the `fig.text(...)` note.
   Expected: `test_the_reduction_factor_is_on_the_figure` FAILS. Restore.

- [ ] **Step 6: Commit**

```bash
git add musicalgestures/_timeline.py tests/test_timeline_render.py
git commit -m "One renderer, three configurations, and a figure that admits what it is

The overview, the improvisation sheet and the action strip differ only in span and
in which level is drawn, so they are one function called three ways.

Every sheet writes a sidecar recording its decimation factor, its time range and
every boundary drawn, and prints the factor on the image itself. Boundaries both
signals supported are solid; boundaries only one supported are dashed, so a reader
sees which cuts to distrust without reading a log.

Both guards verified by removing them."
```

---

## Task 8: `_annotate.py` — export, and prove the tree survives

**Files:**
- Create: `musicalgestures/_annotate.py`
- Test: `tests/test_annotate.py`

**Interfaces:**
- Consumes: `Hierarchy` (Task 5).
- Produces:
  - `to_elan(hierarchy, video, out, levels=None) -> Path`
  - `to_textgrid(hierarchy, out, levels=None, xmax=None) -> Path`
  - `to_tsv(hierarchy, out) -> Path`
  - `from_elan(path) -> Hierarchy`

- [ ] **Step 1: Write the failing test**

Create `tests/test_annotate.py`:

```python
"""Export is only worth having if the tree comes back.

A writer that produces a well-formed file nobody can read into anything is a dead end,
and 'it opened in ELAN' is not the same as 'the nesting survived'. So every writer here
is paired with an assertion about what a reader gets back.

The `.eaf` links the FULL SESSION VIDEO at session-time offsets rather than excerpt
clips. Clips would put every annotation the student makes on a different clock, and
the remapping would have to be right in every direction forever.
"""
import xml.etree.ElementTree as ET

import pytest

from musicalgestures._actions import Action
from musicalgestures._annotate import to_elan, to_textgrid, to_tsv, from_elan
from musicalgestures._hierarchy import Hierarchy


@pytest.fixture
def planted():
    actions, phrases = [], []
    for p in range(2):
        p0 = p * 100.0
        phrases.append(Action(start=p0, end=p0 + 80.0, source="phrase"))
        for a in range(3):
            a0 = p0 + a * 20.0
            actions.append(Action(start=a0, end=a0 + 10.0, source="action"))
    parts = [Action(start=0.0, end=200.0, source="part",
                    labels={"part": "improvisation"},
                    features={"agreement": "both"})]
    return Hierarchy(levels={"part": parts, "phrase": phrases, "action": actions})


def test_elan_round_trips_every_span(planted, tmp_path):
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf")
    back = from_elan(p)
    for level in ("part", "phrase", "action"):
        assert len(back.levels[level]) == len(planted.levels[level]), level
        for a, b in zip(back.levels[level], planted.levels[level]):
            assert a.start == pytest.approx(b.start, abs=0.001)
            assert a.end == pytest.approx(b.end, abs=0.001)


def test_elan_links_the_full_session_video(planted, tmp_path):
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf")
    root = ET.parse(p).getroot()
    md = root.find(".//MEDIA_DESCRIPTOR")
    assert md is not None
    assert md.get("MEDIA_URL").endswith("session.mp4")


def test_elan_nests_the_levels(planted, tmp_path):
    """Flat tiers would lose the hierarchy that is the whole point."""
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf")
    root = ET.parse(p).getroot()
    tiers = {t.get("TIER_ID"): t.get("PARENT_REF") for t in root.iter("TIER")}
    assert tiers["phrase"] == "part"
    assert tiers["action"] == "phrase"


def test_empty_annotation_tiers_are_provided(planted, tmp_path):
    """The student needs somewhere to write, and it must exist before they open it."""
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf",
                levels=("part", "phrase", "action"))
    tiers = {t.get("TIER_ID") for t in ET.parse(p).getroot().iter("TIER")}
    assert "annotation" in tiers


def test_textgrid_is_readable_and_keeps_the_boundaries(planted, tmp_path):
    p = to_textgrid(planted, out=tmp_path / "s.TextGrid", xmax=200.0)
    text = p.read_text()
    assert 'class = "IntervalTier"' in text
    assert "xmax = 200" in text
    assert text.count('intervals [') >= len(planted.levels["action"])


def test_tsv_has_one_row_per_span_plus_a_header(planted, tmp_path):
    p = to_tsv(planted, out=tmp_path / "s.tsv")
    rows = p.read_text().strip().split("\n")
    total = sum(len(v) for v in planted.levels.values())
    assert len(rows) == total + 1
    assert rows[0].split("\t")[:4] == ["level", "start", "end", "label"]


def test_tsv_carries_the_agreement_so_it_is_not_lost_outside_elan(planted, tmp_path):
    p = to_tsv(planted, out=tmp_path / "s.tsv")
    assert "agreement" in p.read_text().split("\n")[0]
    assert "both" in p.read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_annotate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'musicalgestures._annotate'`.

- [ ] **Step 3: Write the implementation**

Create `musicalgestures/_annotate.py`:

```python
"""Three exports from one tree, and a reader so the export is not a dead end.

ELAN is the format the nesting actually fits, so it is the one with a reader. Praat
TextGrid flattens to interval tiers and TSV flattens further; both are conveniences for
tools that cannot read `.eaf`, and neither is expected to round-trip the hierarchy.

**The `.eaf` links the full session video at session-time offsets, not excerpt clips.**
An annotation made against a clip is on the clip's clock, and every use of it
afterwards has to remap --- correctly, in both directions, forever. Session time is the
only clock that stays comparable across levels and across the six recordings.

Round-trip beyond `from_elan` --- taking a student's corrected file back into a
`Hierarchy` complete with their own tiers --- is wanted eventually and not now. The
reader here exists so the writer can be tested, and is the seam that fuller import
attaches to.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy

__all__ = ["to_elan", "from_elan", "to_textgrid", "to_tsv"]

#: Coarse to fine. ELAN needs a parent before its child, and so does a reader.
_ORDER = ("part", "phrase", "action")


def _ordered(hierarchy: Hierarchy, levels=None) -> list[str]:
    names = [n for n in _ORDER if n in hierarchy.levels]
    extra = [n for n in hierarchy.levels if n not in _ORDER]
    chosen = names + sorted(extra)
    return [n for n in chosen if levels is None or n in levels]


def to_elan(hierarchy: Hierarchy, video, out, levels=None, fps: float = 50.0) -> Path:
    """Write an ELAN `.eaf` with one nested tier per level.

    Args:
        hierarchy: The levels to write.
        video: Path to the FULL session video. Annotations are on the session clock.
        out: Path to write.
        levels: Which levels to write, or None for all of them.
        fps (float): Only used to describe the media, not to quantise anything.

    Returns:
        Path: The file written.
    """
    out = Path(out)
    names = _ordered(hierarchy, levels)

    root = ET.Element("ANNOTATION_DOCUMENT", {
        "AUTHOR": "musicalgestures", "DATE": "1970-01-01T00:00:00+00:00",
        "FORMAT": "3.0", "VERSION": "3.0"})
    header = ET.SubElement(root, "HEADER", {"MEDIA_FILE": "", "TIME_UNITS": "milliseconds"})
    ET.SubElement(header, "MEDIA_DESCRIPTOR", {
        "MEDIA_URL": Path(video).as_uri() if Path(video).is_absolute()
        else f"file://{video}",
        "RELATIVE_MEDIA_URL": f"./{Path(video).name}",
        "MIME_TYPE": "video/mp4"})

    order = ET.SubElement(root, "TIME_ORDER")
    slots, counter = {}, [0]

    def slot(t: float) -> str:
        """One time slot per distinct millisecond, as ELAN expects."""
        ms = int(round(t * 1000.0))
        if ms not in slots:
            counter[0] += 1
            sid = f"ts{counter[0]}"
            slots[ms] = sid
            ET.SubElement(order, "TIME_SLOT", {"TIME_SLOT_ID": sid,
                                               "TIME_VALUE": str(ms)})
        return slots[ms]

    #: Slots must be created in time order or ELAN complains, so every boundary is
    #: registered before any tier is written.
    for name in names:
        for a in hierarchy.levels[name]:
            slot(a.start)
            slot(a.end)

    aid = [0]
    for i, name in enumerate(names):
        attrs = {"TIER_ID": name, "LINGUISTIC_TYPE_REF": "segmentation"}
        if i:
            #: Nested, because the hierarchy is the point. A flat set of tiers would
            #: export the spans and lose what relates them.
            attrs["PARENT_REF"] = names[i - 1]
        tier = ET.SubElement(root, "TIER", attrs)
        for a in hierarchy.levels[name]:
            aid[0] += 1
            ann = ET.SubElement(tier, "ANNOTATION")
            al = ET.SubElement(ann, "ALIGNABLE_ANNOTATION", {
                "ANNOTATION_ID": f"a{aid[0]}",
                "TIME_SLOT_REF1": slot(a.start), "TIME_SLOT_REF2": slot(a.end)})
            value = a.labels.get(name, "")
            agreement = a.features.get("agreement")
            if agreement and agreement != "both":
                #: An uncertain boundary says so in the file as well as on the figure,
                #: so a student working only in ELAN still knows which to distrust.
                value = f"{value} [{agreement}]".strip()
            ET.SubElement(al, "ANNOTATION_VALUE").text = value

    #: An empty tier the student writes into. It exists in the exported file rather
    #: than being created by hand, so the tier name is the same in every session.
    ET.SubElement(root, "TIER", {"TIER_ID": "annotation",
                                 "LINGUISTIC_TYPE_REF": "free",
                                 "PARENT_REF": names[-1] if names else "part"})

    ET.SubElement(root, "LINGUISTIC_TYPE", {"LINGUISTIC_TYPE_ID": "segmentation",
                                            "TIME_ALIGNABLE": "true",
                                            "GRAPHIC_REFERENCES": "false"})
    ET.SubElement(root, "LINGUISTIC_TYPE", {"LINGUISTIC_TYPE_ID": "free",
                                            "TIME_ALIGNABLE": "false",
                                            "GRAPHIC_REFERENCES": "false"})

    xml = minidom.parseString(ET.tostring(root)).toprettyxml(indent=" ")
    out.write_text(xml)
    return out


def from_elan(path) -> Hierarchy:
    """Read an `.eaf` back into a `Hierarchy`.

    This exists so `to_elan` can be tested against something other than its own
    output being well-formed, and is the seam a fuller importer attaches to.
    """
    root = ET.parse(str(path)).getroot()
    times = {ts.get("TIME_SLOT_ID"): int(ts.get("TIME_VALUE"))
             for ts in root.iter("TIME_SLOT")}
    levels: dict = {}
    for tier in root.iter("TIER"):
        name = tier.get("TIER_ID")
        spans = []
        for al in tier.iter("ALIGNABLE_ANNOTATION"):
            v = al.find("ANNOTATION_VALUE")
            label = (v.text or "").strip() if v is not None else ""
            spans.append(Action(start=times[al.get("TIME_SLOT_REF1")] / 1000.0,
                                end=times[al.get("TIME_SLOT_REF2")] / 1000.0,
                                source="elan",
                                labels={name: label} if label else {}))
        if spans:
            levels[name] = spans
    return Hierarchy(levels=levels)


def to_textgrid(hierarchy: Hierarchy, out, levels=None, xmax=None) -> Path:
    """Write a Praat TextGrid with one interval tier per level.

    Flattened: TextGrid has no nesting, so the hierarchy is exported as parallel tiers
    and the relationship between them is not carried. That is a property of the format
    and is stated rather than worked around.
    """
    out = Path(out)
    names = _ordered(hierarchy, levels)
    spans = {n: sorted(hierarchy.levels[n], key=lambda a: a.start) for n in names}
    if xmax is None:
        xmax = max((a.end for v in spans.values() for a in v), default=0.0)

    lines = ['File type = "ooTextFile"', 'Object class = "TextGrid"', "",
             "xmin = 0", f"xmax = {xmax}", "tiers? <exists>",
             f"size = {len(names)}", "item []:"]
    for i, name in enumerate(names, start=1):
        #: Praat requires a partition with no holes, so the gaps between spans are
        #: written as empty intervals rather than omitted.
        intervals, t = [], 0.0
        for a in spans[name]:
            if a.start > t:
                intervals.append((t, a.start, ""))
            intervals.append((a.start, a.end, a.labels.get(name, "")))
            t = a.end
        if t < xmax:
            intervals.append((t, xmax, ""))

        lines += [f" item [{i}]:", '  class = "IntervalTier"',
                  f'  name = "{name}"', "  xmin = 0", f"  xmax = {xmax}",
                  f"  intervals: size = {len(intervals)}"]
        for j, (s, e, text) in enumerate(intervals, start=1):
            lines += [f"  intervals [{j}]:", f"   xmin = {s}", f"   xmax = {e}",
                      f'   text = "{text}"']
    out.write_text("\n".join(lines) + "\n")
    return out


def to_tsv(hierarchy: Hierarchy, out, levels=None) -> Path:
    """Write every span as a row, with what produced it and how sure it is.

    The flattest export, and the one that carries the most: `agreement` travels here
    even though TextGrid has nowhere to put it, so a boundary's status is not lost by
    choosing a different tool.
    """
    out = Path(out)
    names = _ordered(hierarchy, levels)
    rows = ["\t".join(["level", "start", "end", "label", "source", "agreement",
                       "duration"])]
    for name in names:
        for a in sorted(hierarchy.levels[name], key=lambda x: x.start):
            rows.append("\t".join([
                name, f"{a.start:.3f}", f"{a.end:.3f}",
                str(a.labels.get(name, "")), a.source,
                str(a.features.get("agreement", "")), f"{a.duration:.3f}"]))
    out.write_text("\n".join(rows) + "\n")
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_annotate.py -v`
Expected: 8 passed.

- [ ] **Step 5: Verify each guard by removing it**

1. In `to_elan`, drop the `PARENT_REF` attribute.
   Expected: `test_elan_nests_the_levels` FAILS. Restore.
2. Remove the empty `annotation` tier.
   Expected: `test_empty_annotation_tiers_are_provided` FAILS. Restore.
3. In `to_textgrid`, stop writing the gap intervals (remove both `intervals.append`
   calls that pass `""`). Praat requires a partition with no holes, so add this
   assertion to `test_textgrid_is_readable_and_keeps_the_boundaries` permanently:
   `assert 'text = ""' in text`, which is the empty gap interval.
   Expected: with the gaps removed that assertion FAILS. Restore the gaps.
4. In `to_tsv`, drop the `agreement` column.
   Expected: `test_tsv_carries_the_agreement_so_it_is_not_lost_outside_elan` FAILS. Restore.

- [ ] **Step 6: Commit**

```bash
git add musicalgestures/_annotate.py tests/test_annotate.py
git commit -m "Three exports from one tree, and a reader so the export is not a dead end

ELAN gets nested tiers, because the nesting is the point, and a reader so the
writer is tested against something other than its own well-formedness. The .eaf
links the full session video on the session clock: an annotation made against an
excerpt is on the excerpt's clock and every later use has to remap it correctly
forever.

An uncertain boundary carries its agreement into the annotation value and into the
TSV, so a student working outside the figures still knows which cuts to distrust.

Four guards verified by removing them."
```

---

## Task 9: `_select.py` — a sample somebody can defend

**Files:**
- Create: `musicalgestures/_select.py`
- Test: `tests/test_select.py`

**Interfaces:**
- Consumes: `Hierarchy` (Task 5), `Action`.
- Produces:
  - `salience(action, qom, fs) -> dict` with keys `onset_clarity`, `motion_range`, `boundary_separation`.
  - `stratified_sample(hierarchy, level="phrase", n=20, strata="part", seed=0) -> list[Action]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_select.py`:

```python
"""A curated sample and a defensible one are different things.

Any claim the student's analysis makes about the corpus is a claim about the sample it
was drawn from. Ranking by how clean the segments look produces easier material to
annotate and a sample whose distribution is a property of the ranking. So selection is
stratified and seeded, and salience is measured on everything and used for nothing ---
which keeps a curated subset available later without re-running anything.
"""
import numpy as np
import pytest

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy
from musicalgestures._select import salience, stratified_sample


def _h(n_per_part=10, n_parts=3):
    phrases, parts = [], []
    for p in range(n_parts):
        p0 = p * 1000.0
        parts.append(Action(start=p0, end=p0 + 1000.0, source="part",
                            labels={"part": "improvisation"}))
        for k in range(n_per_part):
            s = p0 + k * 90.0
            phrases.append(Action(start=s, end=s + 60.0, source="phrase"))
    return Hierarchy(levels={"part": parts, "phrase": phrases})


def test_the_same_seed_gives_the_same_sample():
    h = _h()
    a = stratified_sample(h, level="phrase", n=6, seed=7)
    b = stratified_sample(h, level="phrase", n=6, seed=7)
    assert [(x.start, x.end) for x in a] == [(x.start, x.end) for x in b]


def test_a_different_seed_gives_a_different_sample():
    h = _h()
    a = stratified_sample(h, level="phrase", n=6, seed=1)
    b = stratified_sample(h, level="phrase", n=6, seed=2)
    assert [(x.start, x.end) for x in a] != [(x.start, x.end) for x in b]


def test_every_stratum_is_represented():
    """The whole reason for stratifying: no part may be missed."""
    h = _h()
    chosen = stratified_sample(h, level="phrase", n=6, seed=0)
    parts = {h.parent(c, "part").start for c in chosen}
    assert len(parts) == 3, parts


def test_asking_for_more_than_exists_returns_everything_once():
    h = _h(n_per_part=2, n_parts=2)
    chosen = stratified_sample(h, level="phrase", n=99, seed=0)
    assert len(chosen) == 4
    assert len({(c.start, c.end) for c in chosen}) == 4


def test_the_seed_is_recorded_on_every_chosen_span():
    """A sample nobody can reproduce is not a sample."""
    h = _h()
    for c in stratified_sample(h, level="phrase", n=6, seed=11):
        assert c.features["sample_seed"] == 11


def test_salience_is_measured_but_not_used_for_selection():
    """Selection must not depend on salience, or the sample becomes curated."""
    h = _h()
    fs = 50.0
    qom = np.zeros(int(3000 * fs))
    #: Make exactly one phrase spectacular. It must not become more likely.
    qom[int(90 * fs): int(150 * fs)] = 100.0
    seen = set()
    for _ in range(20):
        for c in stratified_sample(h, level="phrase", n=3, seed=len(seen)):
            seen.add(round(c.start, 1))
    assert len(seen) > 3, "selection collapsed onto a few spans"


def test_salience_reports_the_three_measures():
    fs = 50.0
    qom = np.zeros(int(200 * fs))
    qom[int(50 * fs): int(80 * fs)] = 1.0
    a = Action(start=40.0, end=90.0, source="phrase")
    s = salience(a, qom, fs)
    assert set(s) == {"onset_clarity", "motion_range", "boundary_separation"}
    assert s["motion_range"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_select.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'musicalgestures._select'`.

- [ ] **Step 3: Write the implementation**

Create `musicalgestures/_select.py`:

```python
"""Choosing which segments a person will look at, and doing it defensibly.

**Stratified and seeded, not ranked.** Ranking segments by how clean they look gives
easier material to annotate and a sample whose distribution is a property of the
ranking rather than of the dancing. Any claim the analysis later makes about the
corpus is a claim about this sample, so the sample is spread across the strata that
matter --- improvisations, sessions, conditions --- and the seed is recorded on every
chosen span so it can be drawn again.

**Salience is measured on everything and used for nothing.** It is stored so a curated
subset can be pulled later, deliberately and visibly, without re-running the pipeline
and without having quietly shaped the annotation corpus first.
"""
from __future__ import annotations

import numpy as np

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy

__all__ = ["salience", "stratified_sample"]


def salience(action: Action, qom, fs: float) -> dict:
    """Three measures of how easy a span is to read. Recorded, never selected on.

    Args:
        action: The span to measure.
        qom: Quantity of motion per frame for the whole recording.
        fs (float): Frames per second of `qom`.

    Returns:
        dict: `onset_clarity` (how sharply motion rises at the start, as a ratio),
        `motion_range` (peak minus floor inside the span) and `boundary_separation`
        (how far the span's edges sit below its own peak).
    """
    e = np.asarray(qom, float).ravel()
    i0, i1 = int(action.start * fs), int(action.end * fs)
    i0, i1 = max(0, i0), min(len(e), i1)
    if i1 - i0 < 2:
        return {"onset_clarity": 0.0, "motion_range": 0.0,
                "boundary_separation": 0.0}

    inside = e[i0:i1]
    peak = float(inside.max())
    floor = float(np.percentile(inside, 10))

    lead = e[max(0, i0 - int(fs)): i0]
    lead_level = float(np.percentile(lead, 90)) if lead.size else floor
    onset = (peak - lead_level) / peak if peak > 0 else 0.0

    edge = float(max(inside[0], inside[-1]))
    separation = (peak - edge) / peak if peak > 0 else 0.0

    return {"onset_clarity": round(float(onset), 4),
            "motion_range": round(peak - floor, 4),
            "boundary_separation": round(float(separation), 4)}


def stratified_sample(hierarchy: Hierarchy, level: str = "phrase", n: int = 20,
                      strata: str = "part", seed: int = 0) -> list[Action]:
    """Draw `n` spans from `level`, spread evenly over the strata above them.

    Every stratum is represented before any stratum is sampled twice, so a short
    improvisation cannot be missed entirely by an unlucky draw. Within a stratum the
    choice is uniform and seeded.

    Args:
        hierarchy: The levels to sample from.
        level (str): Which level the excerpts come from. Defaults to "phrase",
            because the action level runs to roughly 2,500 spans per session and is
            far too fine to choose from.
        n (int): How many spans are wanted. Asking for more than exist returns them
            all, once each.
        strata (str): The coarser level to spread across. Defaults to "part".
        seed (int): Recorded on every chosen span, so the sample can be drawn again.

    Returns:
        list: The chosen spans, in time order, each carrying `sample_seed` and
        `sample_stratum` in `features`.
    """
    rng = np.random.default_rng(seed)
    spans = list(hierarchy.levels.get(level, []))
    if not spans:
        return []

    buckets: dict = {}
    for s in spans:
        parent = hierarchy.parent(s, strata)
        buckets.setdefault(parent.start if parent else None, []).append(s)

    #: Shuffle inside each bucket once, then deal round-robin. Dealing rather than
    #: allocating a quota per bucket is what makes every stratum appear before any
    #: stratum repeats, whatever the bucket sizes are.
    for key in buckets:
        order = rng.permutation(len(buckets[key]))
        buckets[key] = [buckets[key][i] for i in order]

    chosen, keys = [], sorted(buckets, key=lambda k: (k is None, k))
    while len(chosen) < n and any(buckets[k] for k in keys):
        for k in keys:
            if buckets[k] and len(chosen) < n:
                s = buckets[k].pop()
                s.features["sample_seed"] = seed
                s.features["sample_stratum"] = k
                chosen.append(s)
    return sorted(chosen, key=lambda a: a.start)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/github/MGT-python && python -m pytest tests/test_select.py -v`
Expected: 7 passed.

- [ ] **Step 5: Verify each guard by removing it**

1. Replace the round-robin deal with `chosen = spans[:n]`.
   Expected: `test_every_stratum_is_represented` FAILS. Restore.
2. Remove `s.features["sample_seed"] = seed`.
   Expected: `test_the_seed_is_recorded_on_every_chosen_span` FAILS. Restore.
3. Sort each bucket by `salience(...)["motion_range"]` instead of shuffling.
   Expected: `test_salience_is_measured_but_not_used_for_selection` FAILS. Restore.

- [ ] **Step 6: Commit**

```bash
git add musicalgestures/_select.py tests/test_select.py
git commit -m "A sample somebody can defend, not the segments that look best

Stratified across parts and seeded, dealt round-robin so every improvisation is
represented before any is sampled twice. Salience is measured on everything and
used for nothing, so a curated subset stays available later without having quietly
shaped the annotation corpus first.

Three guards verified by removing them."
```

---

## Task 10: the corpus driver

**Files:**
- Create: `ProcessedData/Video/PanasonicDownsized/run_corpus.py` (beside the data, on the Seagate — NOT in the MGT repo, and not in a scratchpad)
- Modify: none in MGT.

**Interfaces:**
- Consumes: everything above.
- Produces: per session, an `analysis/<name>/` directory holding the tracks, `tracks_run.json`, sheets, sidecars and exports.

- [ ] **Step 1: Confirm the 27 Nov session finished before starting any other**

Run:
```bash
cd ~/github/MGT-python && python -c "
from musicalgestures._tracks import check_tracks
d='/media/alexanje/Seagate Hub/aktiv/HybridDanceImprov/ProcessedData/Video/PanasonicDownsized/analysis/27CoLocated.Panasonic.A003C505_231127_DJ0B'
r=check_tracks(d); print(r)
assert r['complete'], 'tracks_run.json missing: the run did not finish'
assert r['marker_gaps']==[], r['marker_gaps']"
```
Expected: `complete` True, no gaps. **If this fails, stop.** A path that has never run end to end on one session must not be started on six.

- [ ] **Step 2: Write the driver**

Create `run_corpus.py` beside the videos. It must:

- take a list of the five remaining files (names in `HANDOVER.md`);
- for each, call `extract_tracks_parallel(..., workers=6, resume=True)` then
  `build_pyramid` for both `videogram_v` and `videogram_h`, then write
  `tracks_run.json` **last**;
- run the memory watcher thread from the 27 Nov `run_tracks.py`, writing `memory.log`
  per session;
- process sessions **one at a time**, never in parallel, because the OOM on 2026-08-25
  happened with a single session running and six workers;
- skip any session whose `check_tracks(...)["complete"]` is already True;
- print `check_tracks` output before and after each session.

Copy the structure from
`analysis/27CoLocated.Panasonic.A003C505_231127_DJ0B/run_tracks.py`, which already has
the detachment, logging and memory-watching. The only change is the loop over files.

- [ ] **Step 3: Launch it detached**

Run:
```bash
cd "/media/alexanje/Seagate Hub/aktiv/HybridDanceImprov/ProcessedData/Video/PanasonicDownsized"
setsid nohup bash -c '
  export PYTHONPATH=/home/alexanje/github/MGT-python
  python3 -u run_corpus.py > corpus_run.log 2>&1
  echo "exit=$? at $(date)" > corpus_run.exit
' > /dev/null 2>&1 < /dev/null &
```

**`setsid` is required, not optional.** The 2026-08-25 run died because it was a child
of an interactive session the OOM killer took. A long job on this machine must outlive
the terminal that started it.

Expected: about 3.2 hours for five sessions at roughly 41 minutes each.

- [ ] **Step 4: Verify every session, reading the data rather than the file**

Run:
```bash
cd ~/github/MGT-python && python -c "
import glob, json
from musicalgestures._tracks import check_tracks
base='/media/alexanje/Seagate Hub/aktiv/HybridDanceImprov/ProcessedData/Video/PanasonicDownsized/analysis'
for d in sorted(glob.glob(base+'/*')):
    r=check_tracks(d)
    print(f\"{d.split('/')[-1][:40]:42} complete={r['complete']} \"
          f\"prealloc={r['preallocated']} data_to={r['last_nonzero']} \"
          f\"marker={r['highest_marker']} gaps={r['marker_gaps']}\")"
```
Expected: six rows, all `complete=True`, all `marker_gaps=[]`, and `last_nonzero`
within a few frames of the counts in `HANDOVER.md`.

- [ ] **Step 5: Commit the driver's existence to the project notes**

The driver lives on the Seagate, not in git. Record it in
`/media/alexanje/Seagate Hub/aktiv/HybridDanceImprov/WORKLOG.md` with the date, the
worker count, the wall time per session and whatever `memory.log` showed, so the next
run chooses a worker count from a measurement.

---

## Task 11: produce the three tiers for the corpus

**Files:**
- Create: `ProcessedData/Video/PanasonicDownsized/run_sheets.py` (beside the data)

**Interfaces:**
- Consumes: everything above.
- Produces: per session, `sheets/overview.png`, `sheets/part_NN.png`,
  `sheets/action_NN_MM.png`, each with its `.json` sidecar, plus `session.eaf`,
  `session.TextGrid`, `session.tsv` and `excerpts.json`.

- [ ] **Step 1: Extract audio once per session**

Run, for each of the six videos:
```bash
ffmpeg -v error -y -i "<video>.mp4" -ac 1 -ar 16000 "<analysis_dir>/audio16k.wav"
```
16 kHz mono is what silero-vad wants. Keep the original stereo for the waveform panel
by extracting a second file at 48 kHz if the drawn waveform looks wrong at 16 kHz;
prefer the 16 kHz file otherwise, since a waveform panel is decimated to about 2,400
columns and cannot show more.

- [ ] **Step 2: Run the voice detector over each session**

```python
from musicalgestures._voice import speech_segments
spans = speech_segments(analysis_dir / "audio16k.wav")
```

Expect this to take minutes, not hours, on CPU. Write the spans to
`analysis_dir/speech.json` so the hierarchy can be recomputed without re-running the
model.

- [ ] **Step 3: Build the hierarchy and write the three tiers**

For each session:

```python
import json
import numpy as np
from pathlib import Path
from musicalgestures._actions import Action, segment_actions
from musicalgestures._annotate import to_elan, to_textgrid, to_tsv
from musicalgestures._hierarchy import Hierarchy, part_level
from musicalgestures._select import salience, stratified_sample
from musicalgestures._timeline import render_timeline

d = Path(analysis_dir)
meta = json.loads((d / "tracks.json").read_text())
fps = float(meta["fps"])
qom = np.memmap(d / meta["qom"], dtype=np.float32, mode="r",
                shape=(int(meta["frames"]),))
qom = np.asarray(qom, dtype=float)

speech = [Action(**s) for s in json.loads((d / "speech.json").read_text())]
parts = part_level(qom, fps, speech, min_part_s=60.0)

#: Phrases are cut WITHIN each part, with a robust range, because an improvisation's
#: own dynamic range is what its phrases should be measured against and a session's
#: outlier spikes make the global range meaningless.
phrases = []
for p in parts:
    if p.labels.get("part") != "improvisation":
        continue
    i0, i1 = int(p.start * fps), int(p.end * fps)
    for a in segment_actions(qom[i0:i1], fps, threshold=0.15, min_duration=3.0,
                             min_gap=1.0, source="phrase", range_mode="robust"):
        phrases.append(Action(start=a.start + p.start, end=a.end + p.start,
                              source="phrase"))

actions = []
for ph in phrases:
    i0, i1 = int(ph.start * fps), int(ph.end * fps)
    for a in segment_actions(qom[i0:i1], fps, threshold=0.15, min_duration=0.3,
                             min_gap=0.2, source="action", range_mode="robust"):
        actions.append(Action(start=a.start + ph.start, end=a.end + ph.start,
                              source="action"))

h = Hierarchy(levels={"part": parts, "phrase": phrases, "action": actions})

for ph in phrases:
    ph.features.update(salience(ph, qom, fps))

sheets = d / "sheets"
sheets.mkdir(exist_ok=True)
audio = d / "audio16k.wav"

#: Tier 1: the whole file, part boundaries.
render_timeline(d, hierarchy=h, levels=("part",), speech=speech, audio=audio,
                out=sheets / "overview.png",
                title=f"{d.name} — whole session, parts")

#: Tier 2: one sheet per improvisation, phrase boundaries.
improvs = [p for p in parts if p.labels.get("part") == "improvisation"]
for i, p in enumerate(improvs):
    render_timeline(d, start_s=p.start, end_s=p.end, hierarchy=h,
                    levels=("phrase",), speech=speech, audio=audio,
                    out=sheets / f"part_{i:02d}.png",
                    title=f"{d.name} — improvisation {i}, phrases")

#: Tier 3: the sampled phrases, action boundaries.
chosen = stratified_sample(h, level="phrase", n=20, strata="part", seed=0)
for i, ph in enumerate(chosen):
    render_timeline(d, start_s=ph.start, end_s=ph.end, hierarchy=h,
                    levels=("action",), speech=speech, audio=audio,
                    out=sheets / f"action_{i:02d}.png",
                    title=f"{d.name} — excerpt {i}, actions")

(d / "excerpts.json").write_text(json.dumps(
    [{"index": i, "start": c.start, "end": c.end, "features": c.features}
     for i, c in enumerate(chosen)], indent=1) + "\n")

to_elan(h, video=meta["video"], out=d / "session.eaf")
to_textgrid(h, out=d / "session.TextGrid", xmax=float(meta["duration_s"]))
to_tsv(h, out=d / "session.tsv")
```

- [ ] **Step 4: Cut the excerpt clips**

For each entry in `excerpts.json`:
```bash
ffmpeg -v error -y -ss <start> -i "<video>.mp4" -t <duration> -c copy \
  "<analysis_dir>/excerpts/excerpt_<i>_at_<start_int>s.mp4"
```
The session offset is in the filename as well as in `excerpts.json`, so a clip can
always be put back on the session clock. **The `.eaf` still links the full video**, not
these clips.

- [ ] **Step 5: Sanity-check the part level against the recording**

Open `sheets/overview.png` for the 27 Nov session and check three things by eye:

1. the number of improvisations is plausible for a 2 h 38 min session;
2. the speech ribbon sits in the gaps between them, not inside them — this is ARJ's
   own observation, and if it does not hold the part level is wrong rather than the
   observation;
3. how many boundaries are dashed. A sheet that is mostly dashed means the two signals
   rarely agree, which is a finding to report rather than a parameter to tune away.

Record what you find in `WORKLOG.md`. **Do not tune parameters to make the picture look
better without saying so** — the honest version of this figure is worth more than a
tidy one.

- [ ] **Step 6: Report**

Append to `WORKLOG.md` with the date: what ran, how long it took, how many parts,
phrases and actions each session yielded, how many boundaries were dashed, and
anything the sheets showed that the design did not predict.

---

## Self-Review

**Spec coverage:**

| spec section | task |
|---|---|
| `check_tracks`, three numbers | 1 |
| `build_pyramid` / `read_columns` known answers | 2 |
| robust range for session-scale envelopes | 3 |
| `_voice.py`, silero-vad | 4 |
| `_hierarchy.py`, part/phrase/action, agreement | 5 |
| `decimate_minmax`, min/max and printed factor | 6 |
| `render_timeline`, three tiers, dashed boundaries, Zoom-day caution | 7 |
| `_annotate.py`, ELAN/TextGrid/TSV, full-video link | 8 |
| stratified selection, salience recorded not used | 9 |
| detached runner, corpus run, per-session logging | 10 |
| the three tiers produced for the corpus | 11 |

**Known gap, deliberate:** the Zoom-day synchronisation caution is enforced by
producing one sheet per file and never a two-room sheet, which Task 11 does by
construction. There is no test for it because there is no two-room code path to test;
if one is ever added, it needs a test asserting a shared axis is refused without a
verified sync offset.

**Not in this plan, by design:** per-dancer pose, the gesture-framework layer,
transcription, `_room.py` occupancy, `_crossmodal.py`. Each is a later project.

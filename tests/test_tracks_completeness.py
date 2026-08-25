"""A preallocated memmap reports a finished extraction over a file of zeros.

The bug this exists for, measured on the 27 Nov dance session on 2026-08-25: an
extraction was killed at 08:28 with 44 per cent of the frames missing, and file size,
existence, `ls -la` and reading the last row ALL reported success. Three numbers
disagreed --- 475,688 preallocated, 264,008 written, 222,000 markers --- and each was
right about something different, so `check_tracks` reports all three and reconciles
none of them.
"""
import json
import threading

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


def test_a_run_still_writing_can_be_inspected(tmp_path):
    """The situation check_tracks is most needed for, and the one that broke it.

    `np.flatnonzero` over a live memmap raises "number of non-zero array elements
    changed during function execution" when workers are still writing into it. Asking
    how far an extraction has got IS asking about a file being written, so the scan
    copies each block before testing it.

    Found on 2026-08-25 by running the function against the 27 Nov extraction while it
    was running. **The first version of this test mapped the file writable and wrote
    nothing, so it passed against the broken code** --- numpy only raises when the data
    actually changes during the call. It therefore starts a real writer.
    """
    d = tmp_path / "analysis"
    d.mkdir()
    n = 3 << 20
    q = np.memmap(d / "qom.f4", dtype=np.float32, mode="w+", shape=(n,))
    q[: 2 << 20] = 1.0
    q.flush()

    stop = threading.Event()

    def churn():
        """Flip values on and off, as workers filling their slices would."""
        rng = np.random.default_rng(0)
        while not stop.is_set():
            i = int(rng.integers(0, (2 << 20)))
            q[i] = 0.0 if q[i] else 1.0

    writer = threading.Thread(target=churn, daemon=True)
    writer.start()
    try:
        for _ in range(25):
            r = check_tracks(d)
            assert r["preallocated"] == n
            assert r["last_nonzero"] >= 0
    finally:
        stop.set()
        writer.join(timeout=5)
    del q


def test_the_last_nonzero_is_found_across_a_block_boundary(tmp_path):
    """A backward block scan must not stop at the first block it looks at."""
    d = tmp_path / "analysis"
    d.mkdir()
    n = 3 << 20
    q = np.memmap(d / "qom.f4", dtype=np.float32, mode="w+", shape=(n,))
    q[7] = 1.0                        # only the very first block has data
    q.flush()
    del q
    assert check_tracks(d)["last_nonzero"] == 7

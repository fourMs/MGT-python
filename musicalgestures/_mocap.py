"""Motion-capture file readers and re-exports.

The QTM reader and the cross-modality utilities are re-exported from the
``micromotion`` package. They used to live here and were moved on 2026-07-29 so that
one implementation of quantity of motion exists rather than two, and MGT now depends on
that package instead of carrying its own copy. Behaviour is unchanged: this module's
tests pass against ``micromotion`` unmodified.

The dependency points this way round on purpose. ``micromotion`` needs only numpy, scipy and
pandas, so someone analysing accelerometer data does not have to install a computer-vision
stack; MGT already depends on ``ambiscape`` the same way, and neither of those packages
imports MGT.

Import from ``micromotion`` directly in new code that needs the re-exported functions.
Its API reference, including the band each function uses and what it returns, is at
https://fourms.github.io/micromotion/ and the functions re-exported here are documented
there rather than below.

Beside the re-exports, this module holds MGT's own readers for the formats that most
measurement systems can write --- :func:`read_trc` for the tab-separated TRC format
(OpenSim, Motion Analysis, Pose2Sim, OpenCap), :func:`read_c3d` for the binary C3D
standard (Qualisys, OptiTrack, Vicon, Theia3D) and :func:`read_freemocap` for the
recording folders of the markerless FreeMoCap system. All return exactly the contract
of :func:`read_qtm_tsv` --- ``(marker_names, data, fs)`` with ``data`` of shape
``(frames, markers, 3)``, gaps as ``NaN`` and positions in millimetres --- so everything
downstream of the QTM reader, such as
:func:`~micromotion.mocap.compare_modality_envelopes`, consumes their output unchanged.
"""
from __future__ import annotations

import csv
import io
import json
import warnings
from pathlib import Path

import numpy as np

from micromotion.mocap import (  # noqa: F401
    compare_modality_envelopes,
    dominant_frequency,
    read_qtm_tsv,
)

__all__ = [
    "compare_modality_envelopes",
    "dominant_frequency",
    "read_qtm_tsv",
    "read_trc",
    "read_c3d",
    "read_freemocap",
]


# Conversion factors onto the contract's millimetre convention. QTM TSV exports carry
# millimetres and read_qtm_tsv passes them through, so millimetres are the convention
# every reader in this module converts onto.
_TO_MM = {
    "mm": 1.0,
    "cm": 10.0,
    "dm": 100.0,
    "m": 1000.0,
    "in": 25.4,
    "inch": 25.4,
}


def _scale_to_mm(units: str | None, path: str) -> float:
    """Return the factor that brings ``units`` onto millimetres, warning on unknowns."""
    if units is None or units.strip() == "":
        return 1.0
    factor = _TO_MM.get(units.strip().lower())
    if factor is None:
        warnings.warn(
            f"Unrecognised unit {units!r} in {path!r}; positions are returned "
            f"unconverted. The contract convention is millimetres."
        )
        return 1.0
    return factor


def read_trc(path: str) -> tuple[list[str], np.ndarray, float | None]:
    """
    Read a TRC (Track Row Column) motion-capture export.

    TRC is the tab-separated text format written by Motion Analysis systems and used by
    OpenSim, and it is the marker-trajectory export of the video-based pipelines
    Pose2Sim and OpenCap. The documented layout is a five-line header --- a
    ``PathFileType`` line, a line of field names (``DataRate``, ``CameraRate``,
    ``NumFrames``, ``NumMarkers``, ``Units``, ...), a line of their values, a column-name
    line (``Frame#``, ``Time``, then one marker name per X/Y/Z triple) and a line of
    per-axis labels (``X1``, ``Y1``, ``Z1``, ...) --- followed by the numeric block.
    This reader locates the header rows by their content rather than by line number, so
    files with a missing blank line or extra header material still parse.

    Written against the TRC format as documented for OpenSim and Motion Analysis and the
    synthetic fixtures in ``tests/test_mocap_readers.py``; no vendor sample file was
    available when it was written, so report files it misreads.

    Positions are converted onto the contract's millimetre convention using the header's
    ``Units`` field (``m``, ``cm``, ``dm``, ``mm`` or ``in``; metres, for example, are
    multiplied by 1000). Missing samples --- empty cells, non-numeric cells and
    exact-zero XYZ triples (the gap convention :func:`read_qtm_tsv` also honours) ---
    become ``NaN``, never zeros. The ``Frame#`` and ``Time`` columns are consumed and
    dropped; nothing else is in a TRC file, so nothing else is discarded.

    Args:
        path (str): Path to the ``.trc`` file.

    Returns:
        tuple: ``(marker_names, data, fs)`` where ``marker_names`` is a list of ``M``
            strings, ``data`` is a float array of shape ``(F, M, 3)`` in millimetres
            with gaps as ``NaN``, and ``fs`` is the frame rate in Hz (the header's
            ``DataRate``) or ``None`` if the header does not state one.
    """

    def _read_lines(enc: str) -> list[str]:
        with io.open(path, encoding=enc) as fh:
            return fh.readlines()

    try:
        lines = _read_lines("utf-8")
    except (UnicodeDecodeError, UnicodeError):
        lines = _read_lines("latin-1")

    fs: float | None = None
    units: str | None = None
    n_markers: int | None = None
    marker_names: list[str] = []
    data_start: int | None = None

    i = 0
    while i < len(lines):
        parts = lines[i].rstrip("\r\n").split("\t")
        first = parts[0].strip()
        if first == "DataRate" and i + 1 < len(lines):
            keys = [p.strip() for p in parts]
            values = lines[i + 1].rstrip("\r\n").split("\t")
            header = {k: v.strip() for k, v in zip(keys, values) if k}
            try:
                fs = float(header["DataRate"])
            except (KeyError, ValueError):
                fs = None
            units = header.get("Units")
            try:
                n_markers = int(float(header["NumMarkers"]))
            except (KeyError, ValueError):
                n_markers = None
            i += 2
            continue
        if first == "Frame#":
            marker_names = [p.strip() for p in parts[2:] if p.strip()]
            i += 1
            continue
        try:
            float(first)
            data_start = i
            break
        except ValueError:
            i += 1

    if data_start is None:
        raise ValueError(f"No numeric data block found in {path!r}")
    if not marker_names:
        raise ValueError(f"No 'Frame#' column-name row found in {path!r}")
    if n_markers is not None and n_markers != len(marker_names):
        warnings.warn(
            f"{path!r} declares NumMarkers={n_markers} but names "
            f"{len(marker_names)} markers; the names win."
        )

    M = len(marker_names)
    rows: list[list[float]] = []
    for ln in lines[data_start:]:
        parts = ln.rstrip("\r\n").split("\t")
        if not parts[0].strip():
            continue
        # Frame# and Time lead each row; the marker block is the next 3*M cells.
        cells = parts[2:2 + 3 * M]
        cells += [""] * (3 * M - len(cells))
        row = []
        for cell in cells:
            try:
                row.append(float(cell))
            except ValueError:
                row.append(np.nan)  # empty or unparseable cell: a gap
        rows.append(row)
    if not rows:
        raise ValueError(f"No parseable data rows in {path!r}")

    data = np.array(rows, dtype=float).reshape(len(rows), M, 3)

    # exact-zero triples are gap fills in several exporters -> NaN
    gap = np.all(data == 0, axis=2)
    data[gap] = np.nan

    data *= _scale_to_mm(units, path)
    return marker_names, data, fs


def read_c3d(path: str) -> tuple[list[str], np.ndarray, float]:
    """
    Read the marker trajectories of a C3D motion-capture file.

    C3D is the binary interchange standard of the motion-capture world; Qualisys,
    OptiTrack, Vicon and Theia3D all export it. Reading rides on the optional
    `ezc3d <https://github.com/pyomeca/ezc3d>`_ library, installed with
    ``pip install musicalgestures[c3d]`` (or ``pip install ezc3d``); MGT's C3D *writer*
    (``pose(data_format='c3d')``) uses the lighter pure-Python ``c3d`` package, and the
    ``[c3d]`` extra installs both.

    Written against files written and read back through ezc3d itself (the test suite's
    ground truth) and the C3D specification at https://www.c3d.org; no vendor sample
    file was available when it was written, so report files it misreads.

    Positions are converted onto the contract's millimetre convention using the file's
    ``POINT:UNITS`` parameter (metres, for example, are multiplied by 1000); a file
    without the parameter is taken to be in millimetres already, the format's dominant
    convention. Missing samples become ``NaN``, never zeros: ezc3d already yields ``NaN``
    for samples flagged invalid, and this reader additionally masks any sample whose
    residual is negative --- the C3D convention for missing data.

    Only the point (marker) data are read. Analog channels (force plates, EMG, audio
    sync), events, rotations and the force-platform parameters are NOT read; they are in
    the file untouched, and a reader for them would be a separate function, not a silent
    extension of this one.

    Args:
        path (str): Path to the ``.c3d`` file.

    Returns:
        tuple: ``(marker_names, data, fs)`` where ``marker_names`` is a list of ``M``
            strings (the ``POINT:LABELS`` parameter), ``data`` is a float array of shape
            ``(F, M, 3)`` in millimetres with gaps as ``NaN``, and ``fs`` is the frame
            rate in Hz (the ``POINT:RATE`` parameter).
    """
    try:
        import ezc3d
    except ImportError as exc:
        from musicalgestures._utils import MgError
        raise MgError(
            "Reading C3D files requires the 'ezc3d' package. Install it with: "
            "pip install musicalgestures[c3d] (or: pip install ezc3d)"
        ) from exc

    c = ezc3d.c3d(path)
    point = c["parameters"]["POINT"]
    marker_names = [str(lbl).strip() for lbl in point["LABELS"]["value"]]
    fs = float(np.asarray(point["RATE"]["value"]).ravel()[0])

    units: str | None = None
    if "UNITS" in point and len(point["UNITS"]["value"]) > 0:
        units = str(point["UNITS"]["value"][0])

    # ezc3d stores points as (4, M, F): x, y, z and the homogeneous coordinate.
    points = np.asarray(c["data"]["points"], dtype=float)
    data = points[:3].transpose(2, 1, 0).copy()  # -> (F, M, 3)

    # A negative residual marks a missing sample in the C3D standard. ezc3d already
    # returns NaN for those, but files and readers vary, so mask defensively.
    meta = c["data"].get("meta_points", {})
    if "residuals" in meta:
        residuals = np.asarray(meta["residuals"], dtype=float)
        if residuals.size:
            invalid = residuals.reshape(residuals.shape[-2:]).T < 0  # (F, M)
            data[invalid] = np.nan

    data *= _scale_to_mm(units, path)
    return marker_names, data, fs


# Video cameras run somewhere between 1 and 1000 frames per second; a rate outside that
# range is more likely a parsing or unit error than a real capture rate. The same guard,
# with the same bounds, protects FreeMoCap's own frame-rate derivation
# (freemocap/core/tasks/mocap/mocap_helpers/recording_framerate.py).
_PLAUSIBLE_FPS = (1.0, 1000.0)


def _plausible_fs(fs: float, source: str) -> float | None:
    """Return ``fs`` if it is a believable camera rate, else warn and return ``None``."""
    low, high = _PLAUSIBLE_FPS
    if low <= fs <= high:
        return fs
    warnings.warn(
        f"Derived an implausible frame rate of {fs!r} Hz from {source!r}; ignoring it."
    )
    return None


def _freemocap_fs(recording: Path) -> float | None:
    """Derive a FreeMoCap recording's frame rate from its timestamp records.

    Mirrors the derivation in FreeMoCap's own ``get_recording_framerate``: the median
    rate in skellycam's ``*_stats.json`` first, then the median of the per-frame
    ``from_previous.framerate.hz`` column in the ``*timestamps.csv`` files. Older
    recordings carry neither and instead hold one nanosecond-timestamp ``.npy`` array
    per camera (the layout FreeMoCap's ``DataLoader`` reads), so the median frame
    interval of those is the third source. Returns ``None`` when no record yields a
    believable rate.
    """
    timestamps_dir = recording / "synchronized_videos" / "timestamps"
    if not timestamps_dir.is_dir():
        return None

    for stats_path in sorted(timestamps_dir.rglob("*stats.json")):
        try:
            stats = json.loads(stats_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        median = (stats.get("framerate_stats") or {}).get("median")
        if median is None:
            continue
        fs = _plausible_fs(float(median), str(stats_path))
        if fs is not None:
            return fs

    for csv_path in sorted(timestamps_dir.rglob("*timestamps.csv")):
        rates: list[float] = []
        try:
            with open(csv_path, newline="") as fh:
                for row in csv.DictReader(fh):
                    try:
                        value = float(row["from_previous.framerate.hz"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    if np.isfinite(value) and value > 0:
                        rates.append(value)
        except OSError:
            continue
        if rates:
            # Median, not mean: a dropped frame doubles one interval and would drag a
            # mean downward.
            fs = _plausible_fs(float(np.median(rates)), str(csv_path))
            if fs is not None:
                return fs

    intervals: list[float] = []
    for npy_path in sorted(timestamps_dir.glob("*.npy")):
        try:
            stamps = np.asarray(np.load(str(npy_path)), dtype=float).ravel()
        except (OSError, ValueError):
            continue
        diffs = np.diff(stamps)
        diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
        if diffs.size:
            intervals.append(float(np.median(diffs)))
    if intervals:
        # skellycam timestamps are nanoseconds (``FramePayload.timestamp_ns``).
        return _plausible_fs(1e9 / float(np.median(intervals)), str(timestamps_dir))

    return None


def read_freemocap(path: str) -> tuple[list[str], np.ndarray, float | None]:
    """
    Read the body trajectories of a FreeMoCap recording folder.

    `FreeMoCap <https://freemocap.org>`_ is a markerless, multi-camera video-based
    motion-capture system. Every released version of it (v1.0 through v1.8 verified in
    the source, and the current rewrite still writes the same layout, which its
    recording-structure documentation calls the legacy layout) saves the triangulated
    body trajectories as ``output_data/mediapipe_body_3d_xyz.npy`` inside the recording
    folder --- a float array of shape ``(frames, 33, 3)`` over MediaPipe's 33-landmark
    body topology, in millimetres in the calibrated coordinate frame, with ``NaN``
    wherever a landmark could not be triangulated. Those ``NaN`` values pass through
    unchanged and the millimetres are returned as they are; both conventions match the
    contract already, so nothing is converted.

    ``path`` is the recording folder; passing the ``output_data`` folder or the
    ``*_body_3d_xyz.npy`` file itself also works. A body file written by a tracker
    other than MediaPipe (FreeMoCap also names ``rtmpose_body_3d_xyz.npy`` files), or
    one whose landmark count is not 33, is read with generic marker names
    (``landmark_0``, ...) and a warning rather than mislabelled with MediaPipe names.
    When no body file is found, a :class:`ValueError` names the expected files.

    The frame rate is derived from the recording's own timestamp records under
    ``synchronized_videos/timestamps/``, the same way FreeMoCap's
    ``get_recording_framerate`` derives it: the median rate in skellycam's
    ``*_stats.json``, else the median of the per-frame ``from_previous.framerate.hz``
    column in the ``*timestamps.csv`` files, else the median frame interval of the
    per-camera nanosecond-timestamp ``.npy`` arrays that older recordings carry. The
    per-camera rates reported by the video containers are not used --- cameras in one
    synchronised recording disagree with each other about them --- and when no
    timestamp record exists ``fs`` is ``None`` with a warning, never a guessed default.

    Only the body trajectories are read. The hand and face trajectories
    (``*_right_hand_3d_xyz.npy``, ``*_left_hand_3d_xyz.npy``, ``*_face_3d_xyz.npy``),
    the centre-of-mass data (``center_of_mass/``), the pre-filtering ``raw_data``
    folder with its reprojection errors, the CSV and by-frame JSON exports and the
    videos are NOT read; they are in the folder untouched.

    Written against the FreeMoCap source (the saver in
    ``core_processes/post_process_skeleton_data/split_and_save.py``, the loader in
    ``data_layer/data_saver/data_loader.py`` and the frame-rate derivation in
    ``core/tasks/mocap/mocap_helpers/recording_framerate.py``, at v1.8.2 and current
    main) and the synthetic fixtures in ``tests/test_mocap_readers.py``; no real
    recording was available when it was written, so report recordings it misreads.

    Args:
        path (str): Path to the recording folder (or to its ``output_data`` folder, or
            directly to a ``*_body_3d_xyz.npy`` file).

    Returns:
        tuple: ``(marker_names, data, fs)`` where ``marker_names`` is a list of ``M``
            strings (MediaPipe's 33 landmark names when the file matches that
            topology), ``data`` is a float array of shape ``(F, M, 3)`` in millimetres
            with gaps as ``NaN``, and ``fs`` is the frame rate in Hz derived from the
            recording's timestamps, or ``None`` if no timestamp record exists.
    """
    # The canonical name list lives beside the per-frame pose estimator; imported
    # lazily so this module stays importable with micromotion's dependencies alone.
    from musicalgestures._posetools import MEDIAPIPE_LANDMARK_NAMES

    p = Path(path)
    body_path: Path | None = None
    recording: Path | None = None

    if p.is_file():
        body_path = p
        if p.parent.name == "output_data":
            recording = p.parent.parent
    elif p.is_dir():
        # The recording folder holds output_data; accept output_data itself too.
        for folder, rec in ((p / "output_data", p), (p, p.parent)):
            if not folder.is_dir():
                continue
            candidates = sorted(folder.glob("*_body_3d_xyz.npy"))
            if not candidates:
                continue
            preferred = [c for c in candidates if c.name.startswith("mediapipe_")]
            body_path = preferred[0] if preferred else candidates[0]
            if len(candidates) > 1:
                warnings.warn(
                    f"{str(folder)!r} holds body data from several trackers "
                    f"({', '.join(c.name for c in candidates)}); reading "
                    f"{body_path.name!r}."
                )
            recording = rec
            break
        if body_path is None:
            raise ValueError(
                f"No FreeMoCap body data found under {path!r}: expected "
                f"'output_data/mediapipe_body_3d_xyz.npy' (or another "
                f"'*_body_3d_xyz.npy') inside the recording folder."
            )
    else:
        raise ValueError(f"{path!r} is neither a file nor a folder")

    data = np.asarray(np.load(str(body_path)), dtype=float)
    if data.ndim != 3 or data.shape[2] != 3:
        raise ValueError(
            f"{str(body_path)!r} has shape {data.shape}; expected (frames, landmarks, 3)"
        )

    suffix = "_body_3d_xyz.npy"
    tracker = body_path.name[: -len(suffix)] if body_path.name.endswith(suffix) else ""
    n_landmarks = data.shape[1]
    if n_landmarks == len(MEDIAPIPE_LANDMARK_NAMES) and tracker in ("mediapipe", ""):
        marker_names = list(MEDIAPIPE_LANDMARK_NAMES)
    else:
        warnings.warn(
            f"{body_path.name!r} carries {n_landmarks} landmarks from tracker "
            f"{tracker or 'unknown'!r}, which does not match MediaPipe's "
            f"{len(MEDIAPIPE_LANDMARK_NAMES)}-landmark body topology; using generic "
            f"marker names."
        )
        marker_names = [f"landmark_{i}" for i in range(n_landmarks)]

    fs: float | None = None
    if recording is not None:
        fs = _freemocap_fs(recording)
    if fs is None:
        warnings.warn(
            f"No usable timestamp record found for {path!r}; fs is None. Derive the "
            f"rate from the recording's synchronised videos if you need one --- this "
            f"reader does not invent a default."
        )

    return marker_names, data, fs

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

Beside the re-exports, this module holds MGT's own readers for the two exchange formats
that most measurement systems can write --- :func:`read_trc` for the tab-separated TRC
format (OpenSim, Motion Analysis, Pose2Sim, OpenCap) and :func:`read_c3d` for the binary
C3D standard (Qualisys, OptiTrack, Vicon, Theia3D). Both return exactly the contract of
:func:`read_qtm_tsv` --- ``(marker_names, data, fs)`` with ``data`` of shape
``(frames, markers, 3)``, gaps as ``NaN`` and positions in millimetres --- so everything
downstream of the QTM reader, such as
:func:`~micromotion.mocap.compare_modality_envelopes`, consumes their output unchanged.
"""
from __future__ import annotations

import io
import warnings

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

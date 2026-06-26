"""Enumeration types for MGT-python parameter validation.

Using StrEnum so that enum members compare equal to their string values,
maintaining full backward compatibility with code that passes plain strings.
All enumerations support case-insensitive construction:

    >>> BlurType("average") == BlurType.AVERAGE
    True
    >>> BlurType("AVERAGE") == BlurType.AVERAGE
    True
"""
from __future__ import annotations

import sys
from enum import Enum

# StrEnum is available from Python 3.11; provide a compatible shim for 3.10.
if sys.version_info >= (3, 11):
    from enum import StrEnum as _StrEnumBase
else:
    class _StrEnumBase(str, Enum):  # type: ignore[no-redef]
        """Backward-compatible StrEnum for Python 3.10."""
        def __str__(self) -> str:
            return self.value


class _MgEnum(_StrEnumBase):
    """Private base class that adds case-insensitive lookup to all MGT enums."""

    @classmethod
    def _missing_(cls, value: object) -> "_MgEnum | None":
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class FilterType(_MgEnum):
    """Pixel-value filter applied to the frame-difference stream.

    Attributes
    ----------
    REGULAR:
        Values below *threshold* are set to 0; values above are kept as-is.
    BINARY:
        Values below *threshold* → 0; values above *threshold* → 255.
    BLOB:
        Individual pixels are removed with an erosion filter.
    """
    REGULAR = "Regular"
    BINARY = "Binary"
    BLOB = "Blob"


class BlurType(_MgEnum):
    """Spatial blur applied before the frame-difference computation.

    Attributes
    ----------
    NONE:
        No blurring is applied.
    AVERAGE:
        A 10 × 10 pixel box-blur is applied.
    """
    NONE = "None"
    AVERAGE = "Average"


class CropMode(_MgEnum):
    """Video cropping strategy.

    Attributes
    ----------
    NONE:
        No cropping.
    MANUAL:
        Opens an interactive window; the user draws a rectangle.
    AUTO:
        Automatically detects the area of significant motion.
    """
    NONE = "None"
    MANUAL = "manual"
    AUTO = "auto"


class PoseModel(_MgEnum):
    """Pose estimation skeleton model.

    Attributes
    ----------
    BODY_25:
        OpenPose BODY_25 dataset (25 keypoints).
    COCO:
        COCO dataset (18 keypoints).
    MPI:
        MPII dataset (15 keypoints).
    MEDIAPIPE:
        Google MediaPipe Pose (33 landmarks).
    """
    BODY_25 = "body_25"
    COCO = "coco"
    MPI = "mpi"
    MEDIAPIPE = "mediapipe"


class PoseDevice(_MgEnum):
    """Compute backend for pose estimation inference.

    Attributes
    ----------
    CPU:
        Run on CPU.
    GPU:
        Run on GPU (CUDA / OpenCL).
    """
    CPU = "cpu"
    GPU = "gpu"


class DataFormat(_MgEnum):
    """Output data file format.

    Attributes
    ----------
    CSV:
        Comma-separated values.
    TSV:
        Tab-separated values.
    TXT:
        Plain text (space-separated).

    Note
    ----
    ``JSON`` and ``HDF5`` are reserved for future use and are not yet
    implemented by any processing function.  Passing them will silently
    fall back to CSV.  Use 'csv', 'tsv', or 'txt'.
    """
    CSV = "csv"
    TSV = "tsv"
    TXT = "txt"

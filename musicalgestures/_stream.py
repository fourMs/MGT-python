"""Streaming video reader for MGT-python.

:class:`MgVideoReader` is a context-manager-based iterator that yields video
frames lazily using FFmpeg pipes.  This avoids loading an entire video into
RAM, making it suitable for long recordings.

Examples
--------
>>> from musicalgestures._stream import MgVideoReader
>>> with MgVideoReader("dancer.avi") as reader:
...     for i, (frame, ts) in enumerate(reader):
...         # frame: np.ndarray, shape (H, W, 3), dtype uint8
...         # ts:    float, timestamp in seconds
...         if i >= 5:
...             break
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Generator

import numpy as np

logger = logging.getLogger(__name__)

# Lazy imports – avoid hard dependency at module level
_cv2 = None


def _get_cv2():
    global _cv2
    if _cv2 is None:
        try:
            import cv2 as _cv2_mod
            _cv2 = _cv2_mod
        except ImportError as exc:
            raise ImportError(
                "opencv-python is required for MgVideoReader. "
                "Install it with: pip install opencv-python"
            ) from exc
    return _cv2


class MgVideoReader:
    """Context-manager that streams frames from a video file via FFmpeg.

    Parameters
    ----------
    filename:
        Path to the video file to read.
    start:
        Start time in seconds. Defaults to 0.
    end:
        End time in seconds. Defaults to *None* (read to end of file).
    grayscale:
        If *True*, convert frames to grayscale before yielding.
        Default: False.
    scale:
        Downscale factor (e.g. 0.5 → half resolution). Default: 1.0.
    batch_size:
        Number of frames to read per FFmpeg read call.  Larger values
        reduce subprocess overhead at the cost of more memory.
        Default: 1.

    Yields
    ------
    frame : np.ndarray
        Video frame as a NumPy array, shape ``(H, W, 3)`` (BGR) or
        ``(H, W)`` if *grayscale=True*.
    timestamp : float
        Approximate frame timestamp in seconds.

    Examples
    --------
    >>> import numpy as np
    >>> # Collect every frame as a numpy array:
    >>> frames = []
    >>> with MgVideoReader("dancer.avi") as reader:
    ...     for frame, ts in reader:
    ...         frames.append(frame)
    >>> arr = np.stack(frames)  # shape (N, H, W, 3)
    """

    def __init__(
        self,
        filename: str | Path,
        start: float = 0.0,
        end: float | None = None,
        grayscale: bool = False,
        scale: float = 1.0,
        batch_size: int = 1,
    ) -> None:
        self.filename = Path(filename)
        if not self.filename.exists():
            raise FileNotFoundError(f"Video file not found: {self.filename}")
        self.start = float(start)
        self.end = end
        self.grayscale = grayscale
        self.scale = float(scale)
        self.batch_size = int(batch_size)

        self._width: int = 0
        self._height: int = 0
        self._fps: float = 0.0
        self._process: subprocess.Popen | None = None
        self._frame_index: int = 0

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "MgVideoReader":
        cv2 = _get_cv2()
        cap = cv2.VideoCapture(str(self.filename))
        if not cap.isOpened():
            raise OSError(f"Cannot open video file: {self.filename}")
        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        cap.release()

        self._width = max(1, int(orig_w * self.scale))
        self._height = max(1, int(orig_h * self.scale))

        # Build FFmpeg command
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "quiet"]
        if self.start > 0:
            cmd += ["-ss", str(self.start)]
        cmd += ["-i", str(self.filename)]
        if self.end is not None:
            duration = self.end - self.start
            cmd += ["-t", str(duration)]

        # Video filter for optional scaling and grayscale
        vf_parts = []
        if self.scale != 1.0:
            vf_parts.append(f"scale={self._width}:{self._height}")
        if self.grayscale:
            vf_parts.append("format=gray")
        else:
            vf_parts.append("format=bgr24")
        cmd += ["-vf", ",".join(vf_parts)]
        cmd += ["-f", "rawvideo", "-vcodec", "rawvideo", "-"]

        logger.debug("MgVideoReader FFmpeg command: %s", " ".join(cmd))
        self._process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=-1
        )
        self._frame_index = 0
        return self

    def __exit__(self, *_) -> None:
        if self._process is not None:
            try:
                self._process.stdout.close()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def __iter__(self) -> Generator[tuple[np.ndarray, float], None, None]:
        """Yield ``(frame, timestamp)`` pairs."""
        if self._process is None:
            raise RuntimeError(
                "MgVideoReader must be used as a context manager: "
                "'with MgVideoReader(path) as reader:'"
            )
        channels = 1 if self.grayscale else 3
        frame_bytes = self._height * self._width * channels
        fps = self._fps

        while True:
            raw = self._process.stdout.read(frame_bytes)
            if len(raw) < frame_bytes:
                break
            frame = np.frombuffer(raw, dtype=np.uint8)
            if self.grayscale:
                frame = frame.reshape((self._height, self._width))
            else:
                frame = frame.reshape((self._height, self._width, 3))
            ts = self.start + self._frame_index / fps
            yield frame, ts
            self._frame_index += 1

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def width(self) -> int:
        """Frame width in pixels (after optional scaling)."""
        return self._width

    @property
    def height(self) -> int:
        """Frame height in pixels (after optional scaling)."""
        return self._height

    @property
    def fps(self) -> float:
        """Frames per second of the source video."""
        return self._fps

    def __repr__(self) -> str:
        return (
            f"MgVideoReader('{self.filename}', start={self.start}, "
            f"end={self.end}, grayscale={self.grayscale}, scale={self.scale})"
        )

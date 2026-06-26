"""Pose estimator interface and backends for MGT-python.

This module provides:

* :class:`PoseEstimator` – an abstract base class (ABC) defining the common
  interface that all pose backends must implement.
* :class:`MediaPipePoseEstimator` – a concrete backend powered by Google
  MediaPipe Pose (33 landmarks, CPU-friendly, zero model download).
* :class:`OpenPosePoseEstimator` – a thin wrapper around the legacy OpenPose /
  Caffe-model implementation already present in :mod:`musicalgestures._pose`.

The shared interface means that backends are interchangeable::

    from musicalgestures._pose_estimator import MediaPipePoseEstimator
    est = MediaPipePoseEstimator()
    keypoints = est.predict_frame(frame)   # → np.ndarray shape (33, 3)

Examples
--------
>>> import numpy as np
>>> frame = np.zeros((480, 640, 3), dtype=np.uint8)
>>> # Without mediapipe installed this raises MgDependencyError gracefully.
"""
from __future__ import annotations

import abc
import logging
from pathlib import Path
from typing import Any

import numpy as np

from musicalgestures._exceptions import MgDependencyError
from musicalgestures._enums import PoseModel, PoseDevice

logger = logging.getLogger(__name__)

# Canonical MediaPipe landmark names (index → name)
MEDIAPIPE_LANDMARK_NAMES: list[str] = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear",
    "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_pinky", "right_pinky",
    "left_index", "right_index",
    "left_thumb", "right_thumb",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]


class PoseEstimatorResult:
    """Container for the output of a single-frame pose estimation.

    Parameters
    ----------
    keypoints:
        2-D array of shape ``(n_keypoints, 3)`` where columns are
        ``(x, y, confidence)``.  Coordinates are normalised to [0, 1].
    landmark_names:
        List of keypoint names corresponding to each row.
    frame_index:
        Frame index this result belongs to.
    timestamp:
        Timestamp in seconds.
    """

    def __init__(
        self,
        keypoints: np.ndarray,
        landmark_names: list[str],
        frame_index: int = 0,
        timestamp: float = 0.0,
    ) -> None:
        self.keypoints = np.asarray(keypoints, dtype=float)
        self.landmark_names = landmark_names
        self.frame_index = int(frame_index)
        self.timestamp = float(timestamp)

    @property
    def n_keypoints(self) -> int:
        return len(self.landmark_names)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict representation."""
        return {
            "frame_index": self.frame_index,
            "timestamp": self.timestamp,
            "keypoints": {
                name: {
                    "x": float(self.keypoints[i, 0]),
                    "y": float(self.keypoints[i, 1]),
                    "confidence": float(self.keypoints[i, 2]),
                }
                for i, name in enumerate(self.landmark_names)
            },
        }

    def __repr__(self) -> str:
        return (
            f"PoseEstimatorResult(n_keypoints={self.n_keypoints}, "
            f"frame={self.frame_index}, t={self.timestamp:.3f}s)"
        )


class PoseEstimator(abc.ABC):
    """Abstract base class for pose estimation backends.

    All concrete subclasses must implement :meth:`predict_frame` and
    :meth:`landmark_names`.

    Parameters
    ----------
    model:
        Skeleton model variant.
    device:
        Compute backend (``'cpu'`` or ``'gpu'``).
    """

    def __init__(
        self,
        model: PoseModel | str = PoseModel.MEDIAPIPE,
        device: PoseDevice | str = PoseDevice.CPU,
    ) -> None:
        self.model = PoseModel(model)
        self.device = PoseDevice(device)

    @property
    @abc.abstractmethod
    def landmark_names(self) -> list[str]:
        """Ordered list of keypoint names."""

    @abc.abstractmethod
    def predict_frame(self, frame: np.ndarray) -> PoseEstimatorResult:
        """Run pose estimation on a single BGR frame.

        Parameters
        ----------
        frame:
            Input frame as a NumPy array of shape ``(H, W, 3)`` in BGR order.

        Returns
        -------
        PoseEstimatorResult
        """

    def predict_video(
        self,
        filename: str | Path,
        start: float = 0.0,
        end: float | None = None,
        skip: int = 0,
    ) -> list[PoseEstimatorResult]:
        """Run pose estimation on every frame of a video file.

        Parameters
        ----------
        filename:
            Path to the video file.
        start:
            Start time in seconds.
        end:
            End time in seconds (None = full video).
        skip:
            Process every (1 + skip)-th frame.

        Returns
        -------
        list[PoseEstimatorResult]
        """
        from musicalgestures._stream import MgVideoReader

        results: list[PoseEstimatorResult] = []
        with MgVideoReader(filename, start=start, end=end) as reader:
            for i, (frame, ts) in enumerate(reader):
                if skip > 0 and i % (skip + 1) != 0:
                    continue
                result = self.predict_frame(frame)
                result.frame_index = i
                result.timestamp = ts
                results.append(result)
        return results

    def __repr__(self) -> str:
        return f"{type(self).__name__}(model={self.model}, device={self.device})"


class MediaPipePoseEstimator(PoseEstimator):
    """Pose estimator backed by Google MediaPipe Pose (Tasks API).

    Requires the optional ``mediapipe>=0.10`` package::

        pip install musicalgestures[pose]

    The first time you use a given complexity level the corresponding
    ``.task`` model file (~8–28 MB) is downloaded from Google's model
    storage and cached in ``musicalgestures/models/``.

    Parameters
    ----------
    model_complexity:
        MediaPipe model complexity (0 = lite, 1 = full, 2 = heavy).
        Higher values are more accurate but slower.  Default: 1.
    min_detection_confidence:
        Minimum confidence for initial body detection. Default: 0.5.
    min_tracking_confidence:
        Minimum confidence for landmark tracking. Default: 0.5.

    Examples
    --------
    >>> import numpy as np
    >>> est = MediaPipePoseEstimator()  # doctest: +SKIP
    >>> frame = np.zeros((480, 640, 3), dtype=np.uint8)
    >>> result = est.predict_frame(frame)  # doctest: +SKIP
    >>> result.keypoints.shape  # (33, 3)  # doctest: +SKIP
    """

    # Model download URLs for each complexity level
    _MODEL_URLS: dict[int, str] = {
        0: (
            "https://storage.googleapis.com/mediapipe-models/"
            "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
        ),
        1: (
            "https://storage.googleapis.com/mediapipe-models/"
            "pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
        ),
        2: (
            "https://storage.googleapis.com/mediapipe-models/"
            "pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
        ),
    }
    _MODEL_NAMES: dict[int, str] = {
        0: "pose_landmarker_lite.task",
        1: "pose_landmarker_full.task",
        2: "pose_landmarker_heavy.task",
    }

    def __init__(
        self,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        device: PoseDevice | str = PoseDevice.CPU,
    ) -> None:
        super().__init__(model=PoseModel.MEDIAPIPE, device=device)
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self._landmarker = None  # lazy init

    def _get_model_path(self) -> Path:
        """Return path to the cached model file, downloading if necessary."""
        import musicalgestures as mg

        module_dir = Path(mg.__file__).parent
        models_dir = module_dir / "models"
        models_dir.mkdir(exist_ok=True)

        complexity = self.model_complexity
        if complexity not in self._MODEL_NAMES:
            logger.warning(
                "model_complexity %d is not valid (0-2); defaulting to 1.",
                complexity,
            )
            complexity = 1

        model_path = models_dir / self._MODEL_NAMES[complexity]
        if model_path.exists():
            return model_path

        url = self._MODEL_URLS[complexity]
        logger.info("Downloading MediaPipe model from %s …", url)
        print(f"Downloading MediaPipe pose model ({self._MODEL_NAMES[complexity]}) …")
        try:
            import urllib.request

            urllib.request.urlretrieve(url, model_path)
            logger.info("Model saved to %s", model_path)
        except Exception as exc:
            raise MgDependencyError(
                f"Failed to download MediaPipe pose model from {url}. "
                "Please download it manually and place it at: "
                f"{model_path}"
            ) from exc
        return model_path

    def _ensure_initialized(self) -> None:
        if self._landmarker is not None:
            return
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise MgDependencyError(
                "mediapipe is required for MediaPipePoseEstimator. "
                "Install it with: pip install musicalgestures[pose]"
            ) from exc

        model_path = self._get_model_path()

        BaseOptions = mp.tasks.BaseOptions
        PoseLandmarker = mp.tasks.vision.PoseLandmarker
        PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        def _make_landmarker(delegate):
            options = PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(model_path), delegate=delegate),
                running_mode=VisionRunningMode.IMAGE,
                min_pose_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )
            return PoseLandmarker.create_from_options(options)

        want_gpu = self.device == PoseDevice.GPU
        if want_gpu:
            try:
                self._landmarker = _make_landmarker(BaseOptions.Delegate.GPU)
                logger.debug("MediaPipe PoseLandmarker initialised on GPU (complexity=%d)", self.model_complexity)
                return
            except Exception as exc:
                print(
                    "MediaPipe GPU delegate is unavailable; falling back to CPU.\n  "
                    f"({type(exc).__name__}: {exc})\n  "
                    "GPU inference needs MediaPipe's GPU delegate (Linux with working "
                    "OpenGL/EGL drivers). The model still runs, just on CPU."
                )
                self.device = PoseDevice.CPU

        self._landmarker = _make_landmarker(BaseOptions.Delegate.CPU)
        logger.debug(
            "MediaPipe PoseLandmarker initialised on CPU (complexity=%d)",
            self.model_complexity,
        )

    @property
    def landmark_names(self) -> list[str]:
        return MEDIAPIPE_LANDMARK_NAMES

    def predict_frame(self, frame: np.ndarray) -> PoseEstimatorResult:
        """Run MediaPipe Pose on a single BGR frame.

        Parameters
        ----------
        frame:
            BGR frame, shape ``(H, W, 3)``.

        Returns
        -------
        PoseEstimatorResult
            33 landmarks; ``confidence`` is the visibility score.
        """
        self._ensure_initialized()
        import cv2
        import mediapipe as mp

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        detection_result = self._landmarker.detect(mp_image)

        n = len(MEDIAPIPE_LANDMARK_NAMES)
        keypoints = np.zeros((n, 3), dtype=float)

        if detection_result.pose_landmarks:
            for i, lm in enumerate(detection_result.pose_landmarks[0]):
                keypoints[i] = [lm.x, lm.y, lm.visibility]

        return PoseEstimatorResult(
            keypoints=keypoints,
            landmark_names=MEDIAPIPE_LANDMARK_NAMES,
        )

    def close(self) -> None:
        """Release MediaPipe resources."""
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


class OpenPosePoseEstimator(PoseEstimator):
    """Thin wrapper around the legacy OpenPose / Caffe-model backend.

    This class delegates to :func:`musicalgestures._pose.pose` and is
    provided so that the old OpenPose workflow can be used through the
    same :class:`PoseEstimator` interface.

    Parameters
    ----------
    model:
        One of ``'body_25'``, ``'coco'``, or ``'mpi'``.
    device:
        ``'cpu'`` or ``'gpu'``.
    threshold:
        Minimum confidence threshold.  Default: 0.1.
    """

    def __init__(
        self,
        model: PoseModel | str = PoseModel.BODY_25,
        device: PoseDevice | str = PoseDevice.GPU,
        threshold: float = 0.1,
    ) -> None:
        super().__init__(model=model, device=device)
        self.threshold = threshold
        self._landmark_names: list[str] = []

    @property
    def landmark_names(self) -> list[str]:
        # Set on first call to predict_frame
        return self._landmark_names

    def predict_frame(self, frame: np.ndarray) -> PoseEstimatorResult:
        """Run OpenPose inference on a single BGR frame.

        .. note::
            Full video-level processing is better handled by calling
            :meth:`MgVideo.pose` directly.
        """
        raise NotImplementedError(
            "OpenPosePoseEstimator.predict_frame() is not implemented for "
            "single frames.  Use MgVideo.pose() for full-video inference."
        )


def get_pose_estimator(
    backend: str = "mediapipe",
    **kwargs: Any,
) -> PoseEstimator:
    """Factory function: return a :class:`PoseEstimator` for the requested backend.

    Parameters
    ----------
    backend:
        ``'mediapipe'`` (default) or ``'openpose'``.
    **kwargs:
        Additional keyword arguments forwarded to the estimator constructor.

    Returns
    -------
    PoseEstimator

    Examples
    --------
    >>> est = get_pose_estimator("mediapipe", model_complexity=0)  # doctest: +SKIP
    """
    backend = backend.lower()
    if backend == "mediapipe":
        return MediaPipePoseEstimator(**kwargs)
    elif backend in ("openpose", "caffe"):
        return OpenPosePoseEstimator(**kwargs)
    else:
        raise ValueError(
            f"Unknown pose backend: {backend!r}.  "
            "Choose 'mediapipe' or 'openpose'."
        )

# PoseEstimator

> Auto-generated documentation for [musicalgestures._pose_estimator](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py) module.

Pose estimator interface and backends for MGT-python.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / PoseEstimator
    - [MediaPipePoseEstimator](#mediapipeposeestimator)
        - [MediaPipePoseEstimator().close](#mediapipeposeestimatorclose)
        - [MediaPipePoseEstimator().landmark_names](#mediapipeposeestimatorlandmark_names)
        - [MediaPipePoseEstimator().predict_frame](#mediapipeposeestimatorpredict_frame)
    - [OpenPosePoseEstimator](#openposeposeestimator)
        - [OpenPosePoseEstimator().landmark_names](#openposeposeestimatorlandmark_names)
        - [OpenPosePoseEstimator().predict_frame](#openposeposeestimatorpredict_frame)
    - [PoseEstimator](#poseestimator)
        - [PoseEstimator().landmark_names](#poseestimatorlandmark_names)
        - [PoseEstimator().predict_frame](#poseestimatorpredict_frame)
        - [PoseEstimator().predict_video](#poseestimatorpredict_video)
    - [PoseEstimatorResult](#poseestimatorresult)
        - [PoseEstimatorResult().n_keypoints](#poseestimatorresultn_keypoints)
        - [PoseEstimatorResult().to_dict](#poseestimatorresultto_dict)
    - [get_pose_estimator](#get_pose_estimator)

This module provides:

* class `PoseEstimator` – an abstract base class (ABC) defining the common
  interface that all pose backends must implement.
* class `MediaPipePoseEstimator` – a concrete backend powered by Google
  MediaPipe Pose (33 landmarks, CPU-friendly, zero model download).
* class `OpenPosePoseEstimator` – a thin wrapper around the legacy OpenPose /
  Caffe-model implementation already present in :mod:[Pose](_pose.md#pose).

The shared interface means that backends are interchangeable

```python
from musicalgestures._pose_estimator import MediaPipePoseEstimator
est = MediaPipePoseEstimator()
keypoints = est.predict_frame(frame)   # → np.ndarray shape (33, 3)
```

Examples
--------

```python
>>> import numpy as np
>>> frame = np.zeros((480, 640, 3), dtype=np.uint8)
>>> # Without mediapipe installed this raises MgDependencyError gracefully.

## MediaPipePoseEstimator

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L194)

```python
class MediaPipePoseEstimator(PoseEstimator):
    def __init__(
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        static_image_mode: bool = False,
    ) -> None:
```

Pose estimator backed by Google MediaPipe Pose.

Requires the optional ``mediapipe`` package

```python
pip install musicalgestures[pose]
```

Parameters
----------
model_complexity:
    MediaPipe model complexity (0, 1, or 2).  Higher = more accurate
    but slower.  Default: 1.
min_detection_confidence:
    Minimum confidence for initial body detection. Default: 0.5.
min_tracking_confidence:
    Minimum confidence for landmark tracking. Default: 0.5.
static_image_mode:
    If *True*, treat every frame as a static image (no tracking).
    Default: False.

Examples
--------

```python
>>> import numpy as np
>>> est = MediaPipePoseEstimator()  # doctest: +SKIP
>>> frame = np.zeros((480, 640, 3), dtype=np.uint8)
>>> result = est.predict_frame(frame)  # doctest: +SKIP
>>> result.keypoints.shape  # (33, 3)  # doctest: +SKIP

#### See also

- [PoseEstimator](#poseestimator)

### MediaPipePoseEstimator().close

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L290)

```python
def close() -> None:
```

Release MediaPipe resources.

### MediaPipePoseEstimator().landmark_names

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L255)

```python
@property
def landmark_names() -> list[str]:
```

### MediaPipePoseEstimator().predict_frame

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L259)

```python
def predict_frame(frame: np.ndarray) -> PoseEstimatorResult:
```

Run MediaPipe Pose on a single BGR frame.

Parameters
----------
frame:
    BGR frame, shape ``(H, W, 3)``.

Returns
-------
PoseEstimatorResult
    33 landmarks; ``confidence`` is the visibility score.

#### See also

- [PoseEstimatorResult](#poseestimatorresult)

## OpenPosePoseEstimator

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L303)

```python
class OpenPosePoseEstimator(PoseEstimator):
    def __init__(
        model: PoseModel | str = PoseModel.BODY_25,
        device: PoseDevice | str = PoseDevice.GPU,
        threshold: float = 0.1,
    ) -> None:
```

Thin wrapper around the legacy OpenPose / Caffe-model backend.

This class delegates to :func:[pose](_pose.md#pose) and is
provided so that the old OpenPose workflow can be used through the
same :class:[PoseEstimator](#poseestimator) interface.

Parameters
----------
model:
    One of ``'body_25'``, ``'coco'``, or ``'mpi'``.
device:
    ``'cpu'`` or ``'gpu'``.
threshold:
    Minimum confidence threshold.  Default: 0.1.

#### See also

- [PoseEstimator](#poseestimator)

### OpenPosePoseEstimator().landmark_names

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L330)

```python
@property
def landmark_names() -> list[str]:
```

### OpenPosePoseEstimator().predict_frame

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L335)

```python
def predict_frame(frame: np.ndarray) -> PoseEstimatorResult:
```

Run OpenPose inference on a single BGR frame.

#### Notes

Full video-level processing is better handled by calling
:meth:`MgVideo.pose` directly.

#### See also

- [PoseEstimatorResult](#poseestimatorresult)

## PoseEstimator

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L112)

```python
class PoseEstimator(abc.ABC):
    def __init__(
        model: PoseModel | str = PoseModel.MEDIAPIPE,
        device: PoseDevice | str = PoseDevice.CPU,
    ) -> None:
```

Abstract base class for pose estimation backends.

All concrete subclasses must implement :meth:`predict_frame` and
:meth:`landmark_names`.

Parameters
----------
model:
    Skeleton model variant.
device:
    Compute backend (``'cpu'`` or ``'gpu'``).

### PoseEstimator().landmark_names

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L134)

```python
@property
@abc.abstractmethod
def landmark_names() -> list[str]:
```

Ordered list of keypoint names.

### PoseEstimator().predict_frame

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L139)

```python
@abc.abstractmethod
def predict_frame(frame: np.ndarray) -> PoseEstimatorResult:
```

Run pose estimation on a single BGR frame.

Parameters
----------
frame:
    Input frame as a NumPy array of shape ``(H, W, 3)`` in BGR order.

Returns
-------
PoseEstimatorResult

#### See also

- [PoseEstimatorResult](#poseestimatorresult)

### PoseEstimator().predict_video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L153)

```python
def predict_video(
    filename: str | Path,
    start: float = 0.0,
    end: float | None = None,
    skip: int = 0,
) -> list[PoseEstimatorResult]:
```

Run pose estimation on every frame of a video file.

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

#### See also

- [PoseEstimatorResult](#poseestimatorresult)

## PoseEstimatorResult

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L58)

```python
class PoseEstimatorResult():
    def __init__(
        keypoints: np.ndarray,
        landmark_names: list[str],
        frame_index: int = 0,
        timestamp: float = 0.0,
    ) -> None:
```

Container for the output of a single-frame pose estimation.

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

### PoseEstimatorResult().n_keypoints

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L86)

```python
@property
def n_keypoints() -> int:
```

### PoseEstimatorResult().to_dict

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L90)

```python
def to_dict() -> dict[str, Any]:
```

Return a plain dict representation.

## get_pose_estimator

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_estimator.py#L348)

```python
def get_pose_estimator(
    backend: str = 'mediapipe',
    **kwargs: Any,
) -> PoseEstimator:
```

Factory function: return a :class:[PoseEstimator](#poseestimator) for the requested backend.

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

```python
>>> est = get_pose_estimator("mediapipe", model_complexity=0)  # doctest: +SKIP

#### See also

- [PoseEstimator](#poseestimator)

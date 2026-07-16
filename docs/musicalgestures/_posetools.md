# Posetools

> Auto-generated documentation for [musicalgestures._posetools](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posetools.py) module.

Landmark-trajectory pose tools.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Posetools
    - [extract_pose_landmarks](#extract_pose_landmarks)
    - [impact_events](#impact_events)
    - [limb_speed_from_landmarks](#limb_speed_from_landmarks)
    - [midpoint](#midpoint)

This module implements the *array-level* pose workflow used in several of the
fourMs sound--motion studies: video file -> tidy per-landmark trajectory
arrays (and optionally CSV) -> derived motion signals (limb speed, impact
events).

It complements — and does not replace — the rendering-oriented
``MgVideo.pose()`` pipeline in :mod:[Pose](_pose.md#pose) (overlaid skeleton
video, average-pose image, trajectory image, keypoint CSV) and the per-frame
:class:[PoseEstimator](_pose_estimator.md#poseestimator) interface. Use this
module when you want plain numpy trajectories for downstream signal analysis
(quantity of motion, cross-modal alignment, event detection) rather than
rendered output.

Only :func:`extract_pose_landmarks` needs MediaPipe (an optional dependency,
imported lazily). The derived-signal helpers (:func:`midpoint`,
:func:`limb_speed_from_landmarks`, :func:`impact_events`) are numpy-only and
also work on landmark/point trajectories from any other source (OpenPose,
YOLO-pose, motion capture).

Landmark indices follow the 33-landmark MediaPipe Pose (BlazePose GHUM)
topology used by the mediapipe 0.10.x wheels (e.g. 0 = nose, 11/12 =
left/right shoulder, 13/14 = elbows, 15/16 = wrists); see
`musicalgestures._pose_estimator.MEDIAPIPE_LANDMARK_NAMES` for the full
index -> name mapping.

## extract_pose_landmarks

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posetools.py#L47)

```python
def extract_pose_landmarks(
    filename: str,
    fps: float | None = None,
    width: int | None = None,
    model_complexity: int = 1,
    world_landmarks: bool = False,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
    max_frames: int | None = None,
    target_name: str | None = None,
    quiet: bool = True,
    verbose: bool = True,
) -> dict:
```

Run MediaPipe Pose over a whole video and return tidy per-landmark trajectories.

The video is decoded through an FFmpeg raw-video pipe (optionally resampled
to a lower frame rate and resized), each frame is passed to MediaPipe Pose,
and the 33 landmarks are collected into plain numpy arrays: pixel
coordinates in the analysis frame plus the per-landmark ``visibility``
score, with all-NaN rows on frames where no pose was detected, and a
detection-rate summary. This is the consolidated version of several
near-identical study extractors; downstream method choices (filtering, QoM,
alignment) are deliberately *not* baked in here.

MediaPipe is an optional dependency (``pip install musicalgestures[pose]``)
and is imported lazily, so importing this module works without it. Both
mediapipe API families are supported: the legacy Solutions API
(``mp.solutions.pose.Pose``, wheels up to ~0.10.14) and the Tasks API
(``PoseLandmarker`` in VIDEO running mode, newer 0.10.x wheels where the
Solutions API was removed). With the Tasks API the model file is
auto-downloaded and cached in ``musicalgestures/models/`` on first use
(shared with ``MgVideo.pose()``).

#### Arguments

- `filename` *str* - Path to the input video file.
- `fps` *float, optional* - Analysis frame rate. Frames are resampled to this
    rate by FFmpeg before pose estimation (e.g. 12.5 to halve a 25 fps
    video). Defaults to None (native frame rate).
- `width` *int, optional* - Resize the analysis frames to this width in
    pixels, keeping the aspect ratio. Smaller frames are much faster and
    are usually sufficient for trajectory-level analysis (the studies
    used 256-640 px). Defaults to None (native resolution).
- `model_complexity` *int, optional* - MediaPipe model variant: 0 (lite),
    1 (full) or 2 (heavy). Defaults to 1.
- `world_landmarks` *bool, optional* - Whether to also collect MediaPipe's 3D
    world landmarks (metres, hip-centred). Defaults to False.
- `min_detection_confidence` *float, optional* - MediaPipe person-detection
    confidence threshold (also used as the presence threshold with the
    Tasks API). Defaults to 0.5.
- `min_tracking_confidence` *float, optional* - MediaPipe landmark-tracking
    confidence threshold. Defaults to 0.5.
- `max_frames` *int, optional* - Stop after this many analysed frames (handy
    for quick tests). Defaults to None (whole video).
- `target_name` *str, optional* - If given, also write the trajectories to
    this path as a tidy CSV with columns ``time`` and, per landmark
    name, ``<name>_x``, ``<name>_y``, ``<name>_v`` (and ``<name>_wx``,
    ``<name>_wy``, ``<name>_wz`` when ``world_landmarks=True``).
    Defaults to None (no file written).
- `quiet` *bool, optional* - Suppress MediaPipe's native C++/GL console logs
    during inference. Defaults to True.
- `verbose` *bool, optional* - Print a one-line detection-rate summary per
    video. Defaults to True.

#### Returns

- `dict` - A dictionary with keys:

- ``time`` (np.ndarray, shape (F,)): Frame timestamps in seconds.
- ``landmarks`` (np.ndarray, shape (F, 33, 3)): Per frame and
  landmark ``(x_px, y_px, visibility)`` in analysis-frame pixels;
  all-NaN rows where no pose was detected.
- ``world`` (np.ndarray, shape (F, 33, 3) or None): 3D world
  landmarks ``(x, y, z)`` in metres (hip-centred) when
  ``world_landmarks=True``, else None.
- ``detected`` (np.ndarray of bool, shape (F,)): Per-frame
  detection flags.
- ``detection_rate`` (float): Fraction of frames with a detected
  pose.
- ``fps`` (float): Analysis frame rate of the returned arrays.
- ``width``, ``height`` (int): Analysis frame size in pixels.
- ``names`` (list of str): The 33 landmark names (row order of the
  landmark axis).

Source:
    Consolidated from the author's study extractors: stillstanding
    (mp_extract_westney.py, pose_motion.py) and Westney-comparisons
    (concert_mediapipe.py, reh_pose.py, a1_labstage.py) (Jensenius).

## impact_events

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posetools.py#L477)

```python
def impact_events(
    pos_by_point: np.ndarray,
    fps: float,
    rel_thresh: float = 0.12,
    min_interval_s: float = 0.1,
) -> dict:
```

Detect candidate impact events from point trajectories via acceleration peaks.

Each candidate point's position (2D or 3D; e.g. the two hand points of a
mocap model, or the two wrist landmarks) is differentiated twice with
central differences to obtain its acceleration vector, the vector magnitude
is taken, and the points are merged by element-wise maximum so that a
strike by *either* hand registers (bilateral max). Impacts are then
peak-picked on the merged acceleration magnitude with a relative threshold
of ``rel_thresh`` x the signal's maximum and a minimum inter-impact
interval of ``min_interval_s``.

The threshold parameters are taken directly (the small relative-threshold
peak picker is implemented inline here); a general adaptive peak-picker,
``pick_peaks``, is provided by the sibling core-signal-methods PR in
[Peaks](_peaks.md#peaks). The defaults (0.12 x peak, 100 ms) are the
cymbal study's provisional values for 120 Hz mocap hand data and should be
tuned per dataset. Note the study's caveat: double-differentiating
(model-reconstructed) positions is noisy and also responds to the
backswing, not only the collision — treat the detected peaks as *candidate*
impacts and validate against another modality (e.g. audio onsets) where
possible. For whole-image visual impact detection from video (no
landmarks), see ``MgVideo.impacts()`` instead.

#### Arguments

- `pos_by_point` *np.ndarray* - Point positions, shape (F, P, D) for P
    candidate points in D spatial dimensions (2 or 3), or (F, D) for a
    single point. Units are the caller's (m or px); NaNs (dropouts)
    propagate into the acceleration and are never picked as peaks.
- `fps` *float* - Sampling rate of the trajectories (Hz).
- `rel_thresh` *float, optional* - Relative peak threshold as a fraction of
    the merged acceleration magnitude's maximum. Defaults to 0.12.
- `min_interval_s` *float, optional* - Minimum interval between detected
    impacts in seconds (stronger peaks win). Defaults to 0.10.

#### Returns

- `dict` - A dictionary with keys:

- ``index`` (np.ndarray of int): Sample indices of the detected
  impacts, ascending.
- ``time`` (np.ndarray): Impact times in seconds (``index / fps``).
- ``magnitude`` (np.ndarray): Merged acceleration magnitude at each
  impact (position-units/s^2).
- ``accel`` (np.ndarray, shape (F,)): The full merged acceleration-
  magnitude signal (for plotting/inspection).

Source:
    Cymbal-comparison study, kinematic impact detection from Xsens hand
    points (reimplemented from the paper's method description; defaults
    are the paper's provisional values) (Jensenius).

## limb_speed_from_landmarks

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posetools.py#L374)

```python
def limb_speed_from_landmarks(
    xy: np.ndarray,
    confidence: np.ndarray | None,
    fps: float,
    conf_gate: float = 0.5,
    merge: str | None = 'max_lr',
    smooth_taps: int = 3,
) -> np.ndarray:
```

Confidence-gated image-plane speed of one or more candidate limbs.

For each candidate limb (e.g. the left and right wrist), frames whose
landmark confidence/visibility falls below ``conf_gate`` are masked out
(NaN), and the limb speed is formed as the central-difference magnitude of
the pixel path (px/s). Candidate limbs are then merged by element-wise
maximum — so that motion of *either* limb registers, mirroring the
bilateral merge used for inertial hand data — and lightly smoothed with a
short NaN-aware moving average. Peaks of the resulting signal mark, e.g.,
strike downstrokes of the striking wrist.

Caveats (from the cymbal study): these are 2D apparent kinematics from a
single camera — motion toward/away from the lens is foreshortened and pixel
speed is not metric speed. Moreover, a limb-speed peak marks *maximum
downstroke speed*, which systematically precedes the contact/arrest that an
audio onset or an acceleration peak registers; account for this bias when
comparing event times across modalities.

Peak-picking on the returned signal is left to the caller (a general
adaptive peak-picker, ``pick_peaks``, is provided by the sibling
core-signal-methods PR in [Peaks](_peaks.md#peaks); the cymbal study used
a relative threshold of 0.4 x the take's peak with a 0.2 s minimum
interval).

#### Arguments

- `xy` *np.ndarray* - Pixel positions, shape (F, L, 2) for L candidate limbs
    or (F, 2) for a single limb.
- `confidence` *np.ndarray, optional* - Per-frame landmark confidence
    (MediaPipe ``visibility``), shape (F, L) or (F,). Pass None to skip
    confidence gating.
- `fps` *float* - Frame rate of the trajectory (Hz).
- `conf_gate` *float, optional* - Frames with confidence below this value
    are masked (NaN) before differentiation. Defaults to 0.5.
- `merge` *str, optional* - ``"max_lr"`` (or ``"max"``) merges the candidate
    limbs by element-wise (NaN-aware) maximum; None returns per-limb
    speeds. Defaults to "max_lr".
- `smooth_taps` *int, optional* - Length of the NaN-aware moving-average
    smoother applied after merging. Use 0 or 1 to disable. Defaults
    to 3. With ``smooth_taps > 1``, samples right at the edge of a
    confidence-gated (NaN) region can be partially reconstructed:
    the NaN-aware average only requires *some* finite values inside
    its window, so an edge sample whose window straddles both valid
    and gated frames is averaged from the valid ones rather than
    staying NaN.

#### Returns

- `np.ndarray` - Speed in px/s: shape (F,) when merged, else (F, L). NaN
    where the position (or a central-difference neighbour) is masked
    or missing.

Source:
    Cymbal-comparison study, markerless striking-wrist speed
    (reimplemented from the paper's method description; defaults are the
    paper's provisional values) (Jensenius).

## midpoint

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_posetools.py#L351)

```python
def midpoint(a: np.ndarray, b: np.ndarray) -> np.ndarray:
```

Element-wise midpoint of two landmark trajectories.

Typical use is the shoulder midpoint (MediaPipe landmarks 11 and 12) as an
upper-torso proxy point, e.g. ``midpoint(lm[:, 11, :2], lm[:, 12, :2])``.
NaNs (detection dropouts) propagate: the midpoint is NaN wherever either
input is NaN.

#### Arguments

- `a` *np.ndarray* - First trajectory, any shape (e.g. (F, 2)).
- `b` *np.ndarray* - Second trajectory, broadcast-compatible with ``a``.

#### Returns

- `np.ndarray` - ``(a + b) / 2``.

Source:
    Stillstanding study, pose_motion.py (shoulder-midpoint torso
    micromotion) (Jensenius).

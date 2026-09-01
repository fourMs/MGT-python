# Pose Tracking

Task reference for pose estimation and motion capture in MGT-python: rendering skeleton
video, extracting landmark trajectories as numpy arrays, deriving motion signals,
segmenting postures, and reading mocap files. The full course narrative, including
worked examples and the reasoning behind the defaults, is in
[chapter 10 of the wiki](https://github.com/fourMs/MGT-python/wiki/10-%E2%80%90-Pose-and-Motion-Capture).

## Pose extraction

```bash
pip install musicalgestures[pose]   # MediaPipe backend (default)
```

```python
import musicalgestures as mg

mv = mg.MgVideo('dance.avi')
mv.pose().show()                          # MediaPipe: 33 landmarks, single person
mv.pose(model='body_25')                  # OpenPose: multi-person, needs opencv-python<5
traj = mg.extract_pose_landmarks('dance.avi', fps=30, width=640)
```

`pose()` returns an `MgVideo` with the skeleton overlaid and writes a keypoint data file
(CSV/TSV/TXT/C3D via `data_format`); repeat calls with the same `model` and `threshold`
reuse cached keypoints. `extract_pose_landmarks()` returns a dict whose `landmarks` array
is `(F, 33, 3)` as `(x_px, y_px, visibility)`, with `NaN` rows for undetected frames and a
`detection_rate` field; it requires MediaPipe. Without MediaPipe, `pose()` falls back to
OpenPose `body_25`, and on OpenCV 5 the OpenPose backends raise `MgDependencyError`
because the Caffe importer is gone.

## Visualisations

```python
mv.pose(style='skeleton', overlay=False, background='white', marker_history=10)
mv.pose_waterfall(style='trajectories').show()   # (x, time, y) waterfall
mv.pose_segments(n_bins=24).show()               # circular statistics per body segment
```

All return `MgVideo` or `MgFigure` objects and reuse cached keypoints from a prior
`pose()` call. `pose()` also saves an average-pose image and a marker-trajectories image
by default (`save_average_pose`, `save_trajectories`), each with a companion stats CSV.

## Centring and normalising

```python
mv.pose_center().show()      # centre pose data on its global centroid (mccenter port)
mv.pose_distance().show()    # per-marker cumulative distance (mccumdist port)

from musicalgestures import normalise_poses
normalised = normalise_poses(traj['landmarks'])   # (F, L, 2), pelvis-centred, torso-scaled
```

`normalise_poses()` is detector-agnostic: it recognises MediaPipe-33, YOLO/COCO-17 and
the OpenPose skeletons by landmark count, and takes explicit `anchors` for anything else.
Frames the detector missed come back as `NaN`, never interpolated.

## Posegram and pose timeline

```python
mv.posegram()                          # one landmark per row, coloured by speed
mv.posegram_spatial()                  # image position on the y-axis, motiongram-like
mv.pose_timeline(view='strip')         # postures at regular instants; 'room', 'bands'
```

All return `MgFigure`. The posegram shows landmark speed, so a held posture is dark; the
timeline's `bands` view shows joint angles, so a held posture is a flat band. See the
[`_posegram`](../musicalgestures/_posegram.md) and
[`_posetimeline`](../musicalgestures/_posetimeline.md) API pages.

## Derived signals

```python
wrists = traj['landmarks'][:, [15, 16], :2]
conf = traj['landmarks'][:, [15, 16], 2]
speed = mg.limb_speed_from_landmarks(wrists, conf, traj['fps'])   # (F,) px/s
impacts = mg.impact_events(wrists, traj['fps'])                    # {'time', 'magnitude', ...}
qom, env, fs = mg.normalized_qom(traj['landmarks'][..., :2], traj['fps'])  # body-lengths/s
```

All are numpy-only and NaN-aware, so they work without MediaPipe installed and on
landmarks from any source. A limb-speed peak precedes the actual contact moment, and
`impact_events()` also responds to the backswing, so treat impacts as candidates and
validate against another modality.

## Posture segmentation

```python
postures = mv.postures_from_pose()               # list of Posture spans (held configurations)

from musicalgestures._postures import key_postures, match_postures
groups = key_postures(postures, radius=0.2)      # recurring postures, longest-held first
match_postures(postures, template, 'T-shape')    # label matches; a pose by example
```

`segment_postures()` judges stillness body-relatively, so a held shape carried across the
frame is one posture; a recording in which the body never stops holds no postures. Poses
are only ever proposed as labels on postures, never detected; the
[Concepts page](../concepts.md) carries the position/posture/pose scheme.

## Mocap I/O

```python
names, data, fs = mg.read_qtm_tsv('take01.tsv')     # data: (T, M, 3), zeros -> NaN
result = mg.compare_modality_envelopes(env_video, env_mocap, fs_a, fs_b)
result['r'], result['n']                             # Pearson r, overlapping seconds
```

`compare_modality_envelopes()` takes precomputed 1-D envelopes, bins to a 1 s grid, and
returns `NaN` for `r` below 3 s of overlap. The per-second step is integer-rounded, so
29.97 fps material drifts over long signals: use it for validation, not alignment. These
functions live in [micromotion](https://fourms.github.io/micromotion/) and are
re-exported here.

## Further

- [Chapter 10 of the wiki](https://github.com/fourMs/MGT-python/wiki/10-%E2%80%90-Pose-and-Motion-Capture)—the course chapter this page summarises
- [`_posetools`](../musicalgestures/_posetools.md)—landmark extraction and derived signals
- [`_postures`](../musicalgestures/_postures.md)—posture segmentation and matching
- [`_posegram`](../musicalgestures/_posegram.md) · [`_posetimeline`](../musicalgestures/_posetimeline.md)—the pose pictures
- [`_pose`](../musicalgestures/_pose.md) · [`_pose_visualize`](../musicalgestures/_pose_visualize.md)—the `MgVideo.pose()` pipeline
- [`_mocap`](../musicalgestures/_mocap.md)—mocap I/O re-exports
- [Video Analysis](video-analysis.md#pose-estimation)—full `MgVideo.pose()` signature

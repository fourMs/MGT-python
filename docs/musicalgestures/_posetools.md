# Posetools

Pose trajectories from video, in one contract across three detector families.

## The extractor family

Three extractors return the same tidy result --- per-frame timestamps, a
landmarks array with confidence in the last channel, detection flags, and an
optional CSV --- so an analysis written against one runs against the others, and
two detectors can be compared on a shared clock:

| function | family | topology | needs |
|---|---|---|---|
| `extract_pose_landmarks` | MediaPipe | 33 landmarks | `[pose]`, runs on CPU |
| `extract_pose_landmarks_yolo` | YOLO11-pose | 17 COCO keypoints | `[yolo]` (Ultralytics, AGPL) |
| `extract_pose_landmarks_rtmpose` | RTMPose via rtmlib | 17 COCO keypoints | `[rtmpose]` (ONNX runtime, Apache) |

Which to reach for, measured on a dark dance stage rather than read from
leaderboards: localisation has converged across every serious model, so the axis
that separates them is detection rate. MediaPipe holds ~99% at ~45 fps on CPU for
a single person and remains the answer without a GPU; `yolo11m` is the GPU knee
(99.7% at ~114 fps); RTMPose matches it at 100% with a separate person detector
that never loses the person, and is the Apache-licensed family.

## More than one body

With two bodies in frame, choosing the highest-confidence detection per frame
teleports the trajectory whenever the choice flips --- between two dancers, or
between a dancer and their life-size projection on a videoconference screen,
which is a person to any detector. Two tools answer this:

- `extract_pose_tracks_yolo` returns every identity's trajectory separately as
  track *fragments* (`track=True` on the extractor follows the most persistent
  identity instead). A fragment is trustworthy within itself; over a long
  recording a body is many fragments.
- `associate_fragments` chains fragments into persistent movers using position
  and time only, refusing where honesty demands: a crossing at a fragment
  boundary becomes a recorded break for a human to adjudicate, never a guess.

## Drawing what was tracked

`skeleton_timeline` draws posture at sampled moments on a real time axis ---
stick figures, torso-normalised so the strip reads body shape rather than place
in the room, with honest gaps where tracking dropped. The derived-signal helpers
below (`midpoint`, filtering, and the rest) turn landmark arrays into the
trajectories the [Effort layer](_effort.md) and other analyses consume.

## API reference

::: musicalgestures._posetools

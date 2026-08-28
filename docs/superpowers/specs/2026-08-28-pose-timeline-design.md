# `pose_timeline` — postures and trajectories over time

**Status:** design, awaiting review
**Date:** 2026-08-28

## What it is

One function, three views of the same landmarks:

```python
video.pose_timeline(view='strip')   # normalised postures in a row, a path threading through
video.pose_timeline(view='room')    # skeletons at true positions, a path connecting them
video.pose_timeline(view='bands')   # per-region bands, an hour compressed into one strip
```

## Why one function and not three

Three sibling functions over one pose pipeline would repeat a mistake made earlier the same
day: `stroboscope()` and `multishot()` drew the same kind of picture two ways, and having
both meant a reader had to know which before they could choose. They were merged into one
function with options, and `stroboscope()` now delegates. Three skeleton views arriving as
three names would recreate the problem immediately, and this time knowingly.

The three share a pipeline — landmarks, visibility gating, normalisation — and differ only
in what they draw. That is an argument, not a coincidence.

## What already exists, and what each view adds

| existing | what it shows |
|---|---|
| `pose_waterfall(style='both')` | skeletons and trajectories, **in 3D**, needing rotation to read |
| `posegram` | one row per landmark, brightness for **speed** |
| `pose_spatial_map` | where the body was, as a heat map |
| `pose_segments` | polar plots per bone |
| `multishot` | photographic cut-outs of many moments |

- **strip** — flat and scannable where `pose_waterfall` is a perspective view. A score, not
  a sculpture.
- **room** — the `multishot` composition as line drawings, so many more moments fit before
  they occlude each other.
- **bands** — `posegram` carries speed, so **a held posture reads as nothing**. This carries
  configuration, so a held shape reads as a steady band.

## The shared core

1. **Landmarks** from a cached `pose()` result when present, else `extract_pose_landmarks`,
   matching how `posegram` already resolves them.
2. **Visibility gating** at `min_visibility`, the parameter added in 1.21.0. A landmark
   MediaPipe is guessing at jitters, and a jittering limb is not a posture.
3. **Normalisation** — centre on the pelvis midpoint, scale by torso length. `strip` needs
   it so two postures are comparable when the dancer is at different distances; `room`
   deliberately skips it, since true position is its whole subject; `bands` needs it so a
   joint angle does not change with how far away somebody stands.

Reused rather than redefined: `ANATOMICAL_ORDER` and `BANDS` from `_posegram`,
`MEDIAPIPE_POSE_CONNECTIONS` from `_pose`.

## The three views

**strip.** `n_samples` postures at even intervals, each normalised into its own cell, drawn
as bones. Beneath them, the centroid's horizontal position over the whole recording as a
continuous line, with ticks marking which instants the postures came from. Even sampling is
right here: the question is what the body looked like at regular times.

**room.** Skeletons at their true frame positions, thin, colour ramped early to late, with
the centroid path drawn through them. Moments chosen for spatial separation, reusing
`choose_spaced` from `_multishot` — the same reasoning as there, that evenly spaced moments
land on top of each other.

**bands.** One row per anatomical region from `BANDS` — head, arms, hands, torso, legs —
carrying the mean **joint angle** of that region's bones against the vertical, over time.
Bright is extended, dark is folded. A held posture is a flat band; a change of shape is an
edge.

## Returns

`MgFigure` for `strip` and `bands`, `MgImage` for `room`, matching the pose family.

## What it cannot do

**It is downstream of MediaPipe detection** — but measured, the detector is far better on
this corpus than the design first claimed.

The original text here said 01 December returns zero results for a small dark figure against
a black curtain, and that these views would fail on the hardest Portal footage. **That was
wrong, and it was generalised from a single frame.** Whole-section extraction gives a
detection rate of **0.99 on 01 December's Performance** (8 gaps in 9000 frames) and **1.00 on
27 November** (30 gaps). What actually returned nothing was the *segmentation* path on one
frame tried at 6500 s, which is a different question from whether landmarks are found.

The real limit is narrower: individual landmarks drop below visibility often — the wrists
most of all — and those frames are gaps in the rows that need them. That is visible in the
bands view as white columns in the hands row.

**A frame with no detection is a gap, not a zero.** Interpolating across it would invent
posture. Gaps are left as gaps and their extent is reported.

## Testing

Synthetic, following `_synth`, with a known articulated figure:

- a stick figure whose arm angle sweeps a known arc → `bands` shows a monotonic ramp in the
  arms row and a flat torso row
- a figure translating across frame at constant speed → `room` places it at spread positions;
  `strip` shows the same posture repeatedly while the trajectory line ramps
- landmarks below `min_visibility` → excluded, and their frames reported as gaps
- a video with no detectable person → raises rather than returning an empty figure
- each test asserted against a deliberately broken implementation before being trusted

## Not in scope

- 3D. `pose_waterfall` has that axis and this is deliberately flat.
- Multi-person. The pose extractor returns one figure; a second dancer is a separate question.
- Interpolating gaps.

# Pose timeline

Postures and trajectories over time, flat enough to read at a glance. Three views of one
pose pipeline, behind one function.

```python
import musicalgestures as mg

video = mg.MgVideo("session.mp4")
video.pose_timeline(view='strip', trajectories='traces')   # postures, each with a history
video.pose_timeline(view='room')                           # skeletons where they stood
video.pose_timeline(view='bands')                          # an hour compressed to a strip
```

## The three views

**`strip`** — postures at regular instants, each centred and scaled so two can be compared
even if the dancer was at different distances, with the body's path underneath.

**`room`** — skeletons at their true positions in the frame, with the route drawn over them
and a dot where each drawn posture stands. Moments are chosen for spatial separation, using
the same reasoning as `multishot`: evenly spaced ones land on top of each other.

**`bands`** — one row per region of the body, carrying its joint angles over time. Dark is
folded, bright is extended, and **a held posture is a flat band** — which is what `posegram`
cannot show, since it carries landmark *speed* and a held limb has none.

Rows read down the body: head, torso, arms, hands, legs. `posegram` was reordered to match,
so the two can be read row for row.

## Trajectories on the strip

| `trajectories=` | what it draws |
|---|---|
| `'traces'` | every landmark, as fading ghost skeletons behind each posture |
| `'connect'` | head, pelvis and feet threaded through the postures, lane to lane |
| `'path'` | the room route across the lanes — a **schematic**, see below |
| `None` | postures alone |

**`traces` is usually the one you want.** The fade is the information: a history at constant
alpha says a limb was in several places without saying which it reached last. It also keeps
density *local to each figure*, so a busy passage reads as a busy figure rather than as a
scribble across the whole strip — which is what a single line through a fast section becomes.

**`connect` follows averaged groups, in room space.** Head, pelvis and feet together carry
what a body does vertically; one landmark cannot. They are averages of several landmarks,
which is steadier than any one. Note that in the strip's *body* space the pelvis is the
origin by construction — `normalise_poses` centres on it — so following it there draws a
dead straight line whatever the dancer did. Stability of that kind lives in room coordinates.

**`path` is a schematic and is drawn as one.** Normalising the postures is what removed
their translation, so a room route cannot be to scale in that space.

## What is deliberately absent

**Colour.** The skeletons are black. A ramp across the strip says only "this one came later",
which the left-to-right order already says, and it costs contrast: a pale figure at the end
is harder to read than a black one, and its ghosts nearly invisible.

**Titles and captions.** The only text is the time axis and its unit — `time (s)` when a time
base is available, `time (frames)` when it is not, because 175 is a different claim in each
and nothing else on the figure says which. Everything a caption would say belongs in the
caption of whatever the figure goes into; a plot carrying its own explanation cannot be put
beside another one.

## What it cannot do

**Gaps stay gaps.** Frames the detector missed are not interpolated — filling them would
invent posture. In `bands` they are the white columns that show how much of a row is
actually measured.

**It is downstream of the pose detector**, which on a dance corpus finds a body in 99 to 100
per cent of frames, including on a dark costume against a black curtain. What it loses is
individual *landmarks* — the wrists most often — and a row that needs one is a gap wherever
it is missing.

**It assumes a subject who moves.** On a seated musician the postures are nearly identical
and the strip says little that a single frame would not.

::: musicalgestures._posetimeline

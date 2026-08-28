# Noise floor

A motion gate measured from the recording instead of guessed at.

Every motion measure has a floor. Frame differencing sees sensor noise wherever the picture
is bright enough; motion vectors carry the encoder's rate decisions, 46 per cent of them
exactly zero and the median non-zero one 0.79 px of quarter-pel noise; optical flow sits at
0.009 px per pixel per frame across most of the picture. A `threshold` is what keeps that
out of a result --- and a threshold in absolute units cannot serve two recordings whose
floors differ.

Measured on a corpus of six dance recordings, one fixed setting lit **0.52** times the area
the dancers covered in one recording and **1.90** times it in another. Too tight and too
loose at the same number.

So the floor is taken from the material. The [room plate](_plate.md) says which pixels have
nobody in front of them; whatever their frame-to-frame difference shows, nothing there
moved. The gate is a quantile of that distribution, which makes the parameter a
**false-positive rate** rather than a magnitude.

```python
import musicalgestures as mg

floor = mg.frame_difference_floor("session.mp4")
if floor["refused"]:
    print(floor["reason"])
else:
    video = mg.MgVideo("session.mp4")
    video.motion(threshold=floor["threshold"] / 255)   # the gate is in grey levels
```

## It can refuse, and that is the point

Otsu will split pure noise and report a threshold with no sign of distress: on one recording
it proposed an 82-minute "section" from a microphone that had never heard a conversation,
and the answer looked no different from a real one. An estimator that always answers has the
same fault.

This one declines when there are too few samples to estimate from, and when the gate it
would propose keeps almost none of the moving part --- which is what a camera move, a
lighting change or an empty recording looks like from the inside. A refusal carries
`threshold: None`, so there is nothing to reach for by accident.

## What it buys, and what it does not

Equalising the false-positive rate makes **spatial maps** comparable across recordings. It
does **not** make magnitudes comparable: each recording ends at its own operating point, so
a quantity of motion gated this way is harder to defend across sessions than one gated at a
fixed number, not easier.

Both are therefore kept, and the choice belongs to the analysis:

| you are comparing | use |
|---|---|
| magnitudes across recordings | a fixed `threshold`, the same in every one |
| pictures, maps, or where movement happened | a measured floor, per recording |

Note that H.264 codes to quarter-pel, so a motion-vector gate at or below **0.25 px** cannot
remove anything: 0.25 is the smallest non-zero displacement the format can express.

::: musicalgestures._noisefloor

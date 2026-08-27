# `threshold` does not threshold the difference — 2026-08-27

Found while explaining why one recording in the Hybrid Dance corpus had a compressed
quantity-of-motion dynamic range, after five other explanations had been measured and
eliminated. It is not a property of that recording. It is a property of this package.

**This needs a decision, not an afternoon.** The obvious fix changes every
quantity-of-motion number MGT has ever produced.

---

## What happens

`_filter.filter_frame_ffmpeg` builds, for `filtertype='Regular'`:

```
format=gbrp, tblend=all_mode=difference[diff], [0:v][1][2][diff]threshold
```

with `[1]` a flat grey at `threshold*255` and `[2]` black.

ffmpeg's `threshold` filter takes four streams — **input, threshold, min, max** — and emits
`min` where *input* is below *threshold*, and `max` elsewhere. The input here is `[0:v]`,
**the original video**. `[diff]` is only the max.

So the parameter zeroes motion where the **picture** is dark, and passes every difference
through untouched, however small, wherever the picture is bright enough.

It is a darkness mask, not a noise gate.

## What the docstrings say

`_motionvideo.py`, in its own module header:

> `threshold=0.05` discards small pixel differences, which removes sensor noise

and in `mg_motion`'s argument list:

> 'Regular' turns all values below `threshold` to 0

Neither is what happens on this path. Sensor noise is never removed.

## Verified, not read

A synthetic clip: left half at brightness 200, right half at 5, with a uniform 3-level
change added between the two frames. Through the exact chain above at `threshold=0.05`
(grey 13):

| region | picture | change | output |
|---|---|---|---|
| left | 200 | 3 | **3.04** |
| right | 5 | 3 | **0.05** |

Documented behaviour would return ~0 on both sides, since 3 is far below 12.75. The small
difference survives intact wherever the picture is bright.

## The two code paths disagree

`_filter.filter_frame`, the numpy one, does the documented thing:

```python
motion_frame = (motion_frame > threshold*255)*motion_frame
```

So `threshold=0.05` means one quantity in some functions and a different quantity in
others, from identical arguments:

| path | behaviour | used by |
|---|---|---|
| `filter_frame` (numpy) | thresholds the **difference**, as documented | `_impacts`, `_directograms` |
| `filter_frame_ffmpeg` | masks **dark picture**, difference untouched | `mg_motion`, `_tracks`, `_utils` (×2) |

`mg_motion` is on the wrong side of that table, and it is the function most users reach
for.

## What it costs in practice

Measured on six 100-minute recordings, reproducing the pipeline's chain exactly first
(r = 1.000000 against the stored `qom.f4`, identical integers, 198 frames — a
decomposition of a quantity you cannot reproduce is a decomposition of something else),
then splitting each motion frame by whether the pixel had anybody in front of it:

**Between a third and six-sevenths of the quantity of motion came from pixels with nobody
in front of them**, and across the six the share predicts how compressed that recording's
dynamic range is, Spearman −0.83 to −0.89.

The practical consequence for that project: absolute quantity of motion is not comparable
between recordings, because each carries a different additive noise term set by how much of
its frame escapes the darkness mask. Within-session work is unaffected — the term is
roughly constant there, and median-anchored segmentation still behaves.

## The decision

Three options, and the first is not obviously right.

1. **Fix the filter** so the threshold applies to `[diff]`. Correct, matches the
   documentation and the numpy path — and **changes every quantity-of-motion number this
   package has produced**, including any that are published. It would need to be a major
   version and to say so loudly.

2. **Document what it actually does** and leave the behaviour. Cheap and honest, but leaves
   two functions in the package computing different things from the same argument, which is
   the part users cannot be expected to discover.

3. **Fix the filter and keep the darkness mask** as a separate, named parameter, since
   masking dark regions is a defensible thing to want and is presumably why nobody noticed:
   on bright studio footage it does something reasonable for the wrong reason.

Whichever way it goes, `filter_frame` and `filter_frame_ffmpeg` should stop disagreeing.

## Where the evidence is

- Measurement and the reproduction check:
  `HybridDanceImprov/ProcessedData/Video/PanasonicDownsized/run_qomfloor.py`, output in
  `qom_floor.json`
- The account, with the five eliminated explanations that preceded it:
  `HybridDanceImprov/WORKLOG.md`, 2026-08-27 and 2026-08-26 evening

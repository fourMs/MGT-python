# The Effort layer: MGT's own operationalisation, designed before built

**Status:** design, for ARJ's approval. No code exists. Follows his 2026-08-30
decision to build #373's Effort layer on our own SPARC implementation rather than on
`pyeyesweb`; the survey that framed the choice is `2026-08-23-pyeyesweb-and-laban.md`,
and its measurements carry over here as validation targets. That survey recommended
the dependency; ARJ chose ownership with its validation burden, eyes open, and this
design is what the burden costs in full.

## What is claimed, and as what

Laban's Effort is a qualitative observational system; every computational version is
somebody's operationalisation. This one is named as MGT's throughout --- docstrings
say "the MGT operationalisation of Laban's Weight", never "Laban's Weight" --- and
each factor ships with the evidence for it, which differs by factor:

| factor | poles | operationalised as | validated against |
|---|---|---|---|
| Time | sudden ↔ sustained | burst structure of the speed profile | Sound Actions labels: 365 clips, impulsive 126 / sustained 83 / iterative 125 --- "impulsive vs sustained" IS a Time distinction |
| Flow | free ↔ bound | smoothness, by SPARC | the canonical minimum-jerk battery, and a dev-only cross-check |
| Space | direct ↔ indirect | path directness: displacement over path length, windowed | synthetic paths with known directness |
| Weight | light ↔ strong | speed-magnitude scale against the mover's own distribution | face validity on corpus examples, and said so |

Weight is the weakest claim and is labelled as such: without mass or force plates,
"strong" from video is a kinetic proxy. The honest form is a continuous index with a
documented direction, never a classification shipped as fact.

## SPARC, implemented from the paper

Spectral arc length per Balasubramanian, Melendez-Calderon, Roby-Brami & Burdet
(2015), *On the analysis of movement smoothness*: the arc length of the normalised
Fourier magnitude spectrum of the speed profile, with the adaptive cutoff
(default fc = 10 Hz, amplitude threshold 0.05) that makes it robust to tracker noise.
Three validation tiers, all as tests:

1. **The textbook ordering.** A minimum-jerk reach against 2 and 3 submovements must
   give the ordering the survey already measured: about −1.45, −2.22, −2.59.
2. **The noise table.** Under 2--10 per cent added tracker noise, SPARC of a
   minimum-jerk reach stays within a few per cent of its clean value while still
   separating submovement count --- the property that is the reason SPARC exists,
   and the reason jerk RMS is NOT offered as the smoothness number from pose data
   (at 10 per cent noise, jerk RMS cannot distinguish noise from tripled
   submovements; the survey's table).
3. **A dev-only cross-check** against `pyeyesweb`'s SPARC on the canonical profiles,
   `skipif` it is not installed, so ours provably agrees with the lab that
   originated the line without MGT depending on it.

## API

A new `_effort.py`, input-agnostic per the house rule: functions take arrays and a
sample rate, not videos, so mocap, pose trajectories and QoM tracks all qualify.

```python
sparc(speed, fs, padlevel=4, fc=10.0, amp_th=0.05) -> float
effort_time(speed, fs) -> float        # higher = more sudden
effort_flow(speed, fs) -> float        # higher = more bound (from -SPARC)
effort_space(xy, fs, window_s) -> np.ndarray   # directness per window, 0..1
effort_weight(speed) -> float          # scale index against own distribution
effort_profile(speed_or_xy, fs, window_s) -> dict   # all four, windowed tracks
```

Every function's docstring carries the operationalisation sentence, the direction of
its scale, and its validation numbers. An `MgVideo`-level convenience can follow once
the array level is trusted; it is not part of this design.

## Non-goals

- **Shape and Space Harmony** --- absent from every surveyed package, a larger
  undertaking, out of scope.
- **Labanotation** --- gated on a second camera per the survey: symbols quantised
  from a monocular depth guess are confidently wrong in a way symbols cannot
  express.
- **A pyeyesweb runtime dependency** --- ARJ's decision; it remains a dev-only
  cross-check.
- **`effort_time` classification labels** --- the Sound Actions validation reports a
  confusion matrix in the docs; the function itself returns the continuous index.

## Sequencing

After 1.26. Implementation is test-first from this document's validation tiers; the
Sound Actions confusion matrix is measured before the docs make any claim about
Time. Nothing here blocks or is blocked by 2.0.

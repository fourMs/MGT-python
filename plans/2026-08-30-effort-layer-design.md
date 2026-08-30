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

## What Haga (2008) added, after the fact

ARJ pointed at Egil Haga's thesis (*Correspondences between music and body
movement*, UiO 2008) after the first implementation, and three things from its
chapter 4 and section 7.7 went straight in:

1. **The eight basic effort actions** (his Table 20, from Laban 1971): Weight x
   Time x Space pole combinations named thrusting, slashing, pressing, wringing,
   dabbing, flicking, gliding, floating --- with Flow deliberately a colouring
   element outside the combination (his footnote 107). Implemented as
   `basic_effort_actions`: octants against the mover's own medians, offered as
   proposals in Laban's register.
2. **Fluctuation, not level** (his p. 73): effort elements denote change ---
   "gentler and firmer" --- so the windowed contours are the analytical object and
   a whole-recording scalar flattens the concept. Now stated in the module.
3. **The scholarly frame for the proxy honesty**: dynamics are inferred from
   kinematics (Runeson & Frykholm's kinematic-specification-of-dynamics, via his
   4.4--4.5), Time being kinematical and Weight/Flow dynamical; and effort is the
   qualitative reading on top of Stern's activation contour --- which is what a
   QoM track measures. Both now in the module docstring, cited.

## The Sound Actions validation, measured

Run 2026-08-30 over the deposited 365 clips (labels from `overview.csv` with the
deposit's own corrections applied; substrate the frame-difference QoM, since these
are close-ups where pose has nothing to hold; script and per-clip results in the
collection's `5-processed/effort_time_validation/`).

The index orders the classes exactly as the operationalisation predicts ---
impulsive median 3.52, sustained 3.01, iterative 2.69, the last lowest because
continuous repetition raises the mean speed and burst *concentration* is a ratio
--- but the impulsive-versus-sustained separation is modest: **ROC AUC 0.645**,
balanced accuracy 0.628 at the best threshold, with 33 per cent of iterative
clips on the impulsive side of it. The measured conclusion, now in the docs: the
Time index is a descriptive contour whose direction is validated, not a
classifier, and no classification claim is made --- which was the layer's stance
before the number existed, and survives it.

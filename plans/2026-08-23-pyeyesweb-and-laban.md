# Building #373 on EyesWeb, and what Laban would actually cost

Written overnight 2026-08-23 after ARJ asked whether the gesture-recognition work should
build on Camurri's EyesWeb line through `pyeyesweb`, whether Laban Movement Analysis can be
part of it, and whether Labanotation can be produced from video.

Three answers, in decreasing order of how good the news is.

---

## 1. `pyeyesweb` is real, well-sourced, and mostly *complementary* to what we have

| | |
|---|---|
| version | 1.0.1, uploaded 2026-04-07 |
| licence | MIT |
| authors | Sabharwal, Corbellini, Ghisio, Coletta, Romano, Al Foysal, Camurri — InfoMus / Casa Paganini |
| paper | MOCO '26, Montpellier, **doi:10.1145/3802842.3802904** |
| size | 3,560 lines |
| dependencies | numpy, scipy, scikit-learn, tqdm |
| stars / last push | 12 / 2026-04-07 |

**It does no pose extraction.** MediaPipe and OpenCV are `dev` extras only. It takes movement
data you already have — which is precisely the boundary MGT and micromotion already sit on,
so it slots in rather than competing.

### What it computes

- **low_level** — `smoothness` (SPARC, jerk RMS), `contraction_expansion` (bounding box,
  convex hull, ellipsoid vs a baseline), `equilibrium` (an ellipse between two feet and the
  barycentre), `geometric_symmetry` (per joint-pair symmetry error), `kinetic_energy`
  (mass-weighted joint velocities), `direction_change`
- **mid_level** — `impulsivity` (direction change × suddenness), `lightness`,
  `suddenness` (a stable distribution fitted to the velocity distribution)
- **analysis_primitives** — `synchronization` (phase-locking value), `rarity`,
  `clusterability`, `mse_dominance`, `statistical_moment`

### The overlap with micromotion is one function, not a package

Checked by grep against all 125 exported names:

| pyeyesweb | already in micromotion? |
|---|---|
| SPARC | **no** |
| jerk RMS | **yes** — `features.jerk`, at WIDEBAND with its own documented band caveat |
| phase-locking value | **no** |
| geometric symmetry | **no** |
| convex hull / contraction | **no** (`dispersion_radius` and `ellipse_area_95` are 2-D sway extent, a different quantity) |
| mass-weighted kinetic energy | **no** (`qom`/`group_qom` are unweighted) |
| direction change | adjacent — `heading_persistence` is the same family, not the same measure |

So adopting it is mostly *addition*. The four-toolbox rule is not violated by a dependency
that owns expressive-quality features while micromotion owns markers; it would be violated by
reimplementing SPARC ourselves.

### One measured caution that changes how it should be used

`Smoothness` is correct on the canonical case — a minimum-jerk reach against 2 and 3
submovements gives SPARC −1.45, −2.22, −2.59, the textbook ordering. But the two measures it
returns behave completely differently under *tracker* noise, which is what pose landmarks
have. Speed profiles from a minimum-jerk reach, 15 repeats per level:

| added noise | SPARC (× base) | jerk RMS (× base) |
|---|---|---|
| 0 % | 1.00 | 1.0 |
| 2 % | 1.00 | 2.1 |
| 5 % | 1.00 | 4.7 |
| 10 % | 1.00 | 8.6 |
| 20 % | 1.15 | 17.2 |
| *3 submovements, no noise* | *1.79* | *9.0* |

**Jerk RMS cannot distinguish 10 % tracker noise from genuinely tripling the submovements** —
both read about nine times base. SPARC separates them cleanly, because its adaptive cutoff
was designed for exactly this. This is not a defect; it is the reason SPARC exists. But it
means a smoothness claim about a performer, computed from MediaPipe landmarks with jerk,
is largely a claim about MediaPipe.

*This is the same failure this project keeps cataloguing:* a number that moves for a reason
that is not the reason you think.

---

## 2. Laban: two thirds of Effort is already there, unlabelled

Laban's Effort has four factors, each a pair of poles:

| Effort factor | poles | in pyeyesweb? |
|---|---|---|
| **Weight** | light ↔ strong | `lightness` — computes a "weight index" from kinetic-energy rarity |
| **Time** | sudden ↔ sustained | `suddenness` — a stable distribution fitted to velocity |
| **Space** | direct ↔ indirect | nothing. `direction_change` is the nearest substrate |
| **Flow** | free ↔ bound | nothing. `smoothness` is the nearest substrate |

**No module in the package names Laban.** The mapping above is mine, read from the source.
So a Laban Effort layer is not a port — it is: take Weight and Time as given, define Space
from direction change, define Flow from smoothness, and be explicit that the last two are our
operationalisation rather than Camurri's.

That is a real research contribution and also a real hazard, because Effort is a *qualitative
observational* system and every computational version of it is somebody's operationalisation.
The honest form is a named, cited one — not "Laban Effort" as though there were one.

Shape and Space Harmony (the kinesphere, the scales) are absent entirely, and are a much
larger undertaking than Effort.

---

## 3. Labanotation from video: thinner than it sounds, and the wrong target

The only substantial implementation is **microsoft/LabanotationSuite** (51 stars, last pushed
2024-12-20, so unmaintained for 20 months). It works from **Kinect depth**, not ordinary
video. Everything else found on GitHub is toy-scale — next largest 10 stars, dormant since
2020.

**The deeper problem is not tooling, it is the notation.** Labanotation encodes, per limb, a
*direction* and a *level* (high / middle / low) against metric time. Direction and level are
three-dimensional and body-relative. A single static camera gives you neither reliably: MediaPipe
world landmarks are a monocular metric guess whose depth is the weakest axis, and level is
mostly depth once a performer turns.

So generating Labanotation from a single view means quantising a noisy 3-D estimate onto a
symbol grid, and the quantisation will be confidently wrong in a way the symbols do not
express. A staff full of definite symbols derived from an indefinite estimate is the worst
version of this project's recurring fault.

### What is actually reachable on ARJ's corpus

Static camera, few people, music / dance / theatre / lecture:

1. **Pose → Effort features** — solid, and the largest part of the value. Continuous
   quantities with error bars, not symbols.
2. **Effort → coarse Laban categories** — defensible if reported as a classification with a
   confusion matrix against human coding, never as notation.
3. **→ Labanotation proper** — only worth attempting with two views, where #355's
   `fuse_pose_views` gives a genuine 3-D skeleton and a cross-view residual that *states the
   uncertainty the symbols cannot*. That residual is the reason to want a second camera.

---

## Recommendation

**Adopt `pyeyesweb` as an optional extra, do not vendor it.** It is MIT, small, cited, and
from the lab that originated this line of work. `musicalgestures[expressive]` alongside
`[pose]`, imported lazily, with a thin adapter that maps MGT's landmark arrays onto its
`SlidingWindow` — the same shape as `_soundscape` and `_qom`. One crossing point, stated.

**Do not reimplement its measures**, and do not let its `jerk_rms` be the smoothness number
we report from pose data. Prefer SPARC and say why.

**Treat the Laban layer as our own contribution**, built on Weight and Time from pyeyesweb and
Space and Flow defined by us, validated against the *Sound Actions* labels the way #373's plan
already proposes — 365 clips, impulsive 126 / sustained 83 / iterative 125. Note that
"impulsive versus sustained" is *already a Time-effort distinction*, so that corpus is a
better validation set for a Laban layer than it is for a generic action classifier.

**Leave Labanotation alone until there are two cameras.**

### Open questions for ARJ

1. Optional extra, or stay dependency-free and implement SPARC ourselves? The rule says one
   implementation; the counter-argument is a 12-star package as a hard dependency.
2. Is a Laban Effort layer a *toolbox* feature or a *paper*? It is closer to a research claim
   than the rest of MGT.
3. Does the two-camera path interest you enough to record one? It is cheap at recording time
   and unrecoverable afterwards — the same lesson as the outdoor reference microphone in the
   SINS work.

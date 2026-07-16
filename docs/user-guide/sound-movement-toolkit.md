# Sound–Movement Analysis Toolkit

Alongside the `MgVideo`/`MgAudio` methods, MGT-python ships a lower-level toolkit of
plain-numpy sound–movement analysis functions, ported from the author's own research
pipelines: the **ro** ritual-drumming study, the **stillstanding**/standstill-championship
posturography study, the **Westney** with/without-audience piano comparisons, and the
**cymbal**-comparison striking study. Unlike the `MgVideo`/`MgAudio` methods, these functions
operate directly on numpy arrays (onset times, position/landmark trajectories, waveforms) —
no video decoding or rendering — so they drop straight into notebooks, batch scripts, or your
own analysis pipeline. Every function is importable directly from `musicalgestures` (except
where noted) and documents its own provenance and default-parameter caveats in its docstring;
see the [API Reference](../musicalgestures/index.md) for full signatures.

---

## Peak-picking core

`pick_peaks(x, fs=1.0, smooth=3, rel_threshold=0.5, min_interval=0.3, rel_prominence=0.2, ...)`
(`_peaks`) is the single adaptive peak-picker — moving-average smoothing, a relative or
absolute amplitude threshold, a minimum inter-peak interval, and an optional prominence gate —
shared by every event detector in the toolkit (`_pulse`, `_alignment`, `_qom`,
`_audiofeatures`). Its docstring records the provisional per-signal-type defaults used across
the source studies (e.g. hand-acceleration impacts vs. audio energy onsets vs. wrist-speed
peaks); tune the parameters to the signal at hand rather than relying on the defaults.

---

## Pulse and cycle segmentation (`_pulse`)

Tools for accelerating rhythmic sequences (developed for the *ro* ritual's accelerating
double-drum-stroke cycles): group onsets into per-cycle stroke groups, tabulate per-cycle
metrics, and fit an exponential accelerando.

```python
import numpy as np
from musicalgestures import segment_cycles, cycle_table, fit_accelerando, motion_onsets

onsets = np.array([0.10, 0.34, 1.02, 1.24, 1.85, 2.02, 2.55, 2.68])   # seconds
cycles = segment_cycles(onsets)                    # list[Cycle]: DP segmentation over stroke gaps
table = cycle_table(cycles, clip_id='ro_2023')      # per-cycle DataFrame (t, ioi, n_strokes, ...)
ioi0, t_double, r2 = fit_accelerando(table['t'], table['ioi'])
print(f"tempo doubles every {t_double:.1f}s (R²={r2:.2f})")

# Steepest sustained rises of a motion signal (e.g. per-frame QoM), for
# correlating movement onsets with the stroke cycles above:
motion_times = motion_onsets(qom_signal, fs=25.0)
```

`group_strokes()` (used internally by `segment_cycles`) segments onsets by dynamic programming
over candidate group boundaries, encoding structural priors for accelerating cyclic patterns
(group-size cost, within-group gap plausibility, ordering, and a non-increasing-gap
accelerando prior). `Cycle` is a small dataclass (`index`, `strokes`, `event`,
plus `t_start`/`n_strokes`/`stroke_gap` properties).

---

## Cross-modal alignment (`_alignment`)

Lead/lag and coupling between two (or more) time-aligned signals — the audio-vs-movement
counterpart of the `_pulse` module.

- `xcorr_lag(x, y, fs, max_lag=1.5)` / `envelope_lag(...)` — cross-correlation lead/lag between
  two envelopes.
- `per_cycle_motion_delta(...)` — per-cycle timing offset between a stroke cycle and a motion
  onset.
- `anchor_and_match(...)` / `offset_stats(...)` — one-to-one event matching against an anchor
  stream, with offset summary statistics.
- `sliding_correlation(...)` — windowed correlation over time (does coupling drift?).
- `envelope_agreement(...)` — N-source envelope agreement score.

```python
from musicalgestures import xcorr_lag

lag, corr = xcorr_lag(audio_envelope, motion_envelope, fs=25.0, max_lag=1.5)
print(f"movement lags audio by {lag:.3f}s (r={corr:.2f})")
```

---

## Quantity-of-motion cores (`_qom`)

Band-limited QoM (with an automatic decimate+SOS regime for very low frequency bands),
accelerometer-to-speed integration, per-landmark-group pose QoM, body-scale normalization for
framing-invariant comparisons, spatial grid QoM, and small envelope/binning helpers.

```python
from musicalgestures import extract_pose_landmarks, normalized_qom

traj = extract_pose_landmarks('performance.mp4', fps=25, width=480)   # needs [pose] extra
qom, speed, fs_out = normalized_qom(traj['landmarks'][..., :2], traj['fps'])
print(f"{qom:.3f} body-lengths/s")   # dimensionless -- comparable across framing/zoom
```

`normalized_qom()` divides `pose_qom()` by `body_scale()` (median torso length, shoulder
midpoint to hip midpoint), so the result is invariant to camera framing and zoom — the
technique used for the Westney study's with/without-audience piano comparison. `group_qom()`
generalises `pose_qom()` to any group of marker/landmark trajectories (mocap markers included),
and `accel_to_speed()` integrates a 3-axis accelerometer to a speed signal (the "corpus method"
from the stillstanding study).

---

## Audio feature extraction (`_audiofeatures`)

Scipy-only audio features and onset detectors that complement the librosa-based, figure-producing
`MgAudio` methods with lightweight numeric outputs: `rms_envelope`, `spectral_flux`,
`spectral_flux_onsets`, `energy_onsets`, `t60_backward_decay` (reverberation time), and
`attack_spectral_centroid`. All onset detectors use `pick_peaks` under the hood.

```python
from musicalgestures import rms_envelope, energy_onsets

env, rate = rms_envelope(y, sr, window=0.02)
onsets = energy_onsets(y, sr)     # onset times (s) from the RMS envelope
```

---

## Postural sway metrics (`_posture`)

Posturography ported from the stillstanding study, operating on plain centre-of-pressure (CoP)
or marker-position arrays — no study-specific loaders or axis conventions:

- **Sway amount / geometry** — `cop_sway_metrics`, `confidence_ellipse_area`, `convex_hull_area`.
- **Control dynamics / complexity** — `stabilogram_diffusion` (Collins–De Luca SDA), `dfa`
  (detrended fluctuation analysis), `sample_entropy`, `spectral_edges`, `sway_texture`,
  `principal_axis_projection`.
- **Direction / extent** — `sway_orientation`, `axial_rayleigh`, `spatial_extent`.

```python
from musicalgestures import cop_sway_metrics

metrics = cop_sway_metrics(cop_xy, fs=100.0)   # cop_xy: (T, 2) array [ML, AP], mm
print(metrics['path_len'], metrics['area95'], metrics['ap_ml_sd_ratio'])
```

`cop_sway_metrics()` returns CoP path length/rate, the 95% confidence-ellipse area,
medio-lateral (ML) and antero-posterior (AP) ranges/standard deviations and their ratios, and
the mean sway frequency per axis. The from-scratch SDA/DFA/sample-entropy implementations are
validated in the test suite against known-answer synthetic signals.

---

## Physiology features (`_physio`)

`respiration_rate(waveform, fs, band=(0.1, 0.6), window_s=30, step_s=30)` — windowed breathing
rate (breaths/min) via band-pass filtering and a per-window Welch spectral peak — and
`spectral_band_fractions(...)` — the fraction of a signal's Welch power in each of a set of
caller-supplied named frequency bands (a generic spectral-composition diagnostic, e.g. for
cardiorespiratory QoM), both ported from the stillstanding study's Deichman/Equivital
physiology analyses.

---

## Motion-capture I/O and cross-modality comparison (`_mocap`)

`read_qtm_tsv(path)` is a single robust reader for Qualisys Track Manager (QTM) TSV exports,
consolidating several near-duplicate study loaders (marker-name recovery, numeric-block
autodetection, gap-fill-to-NaN conversion, UTF-8/latin-1 fallback).
`compare_modality_envelopes(...)` resamples two motion envelopes (e.g. video-pose vs. mocap) onto
a common per-second grid and correlates them.

!!! note "`dominant_frequency` is not re-exported from `_mocap`"
    `_mocap` also defines its own `dominant_frequency` (a Welch-peak variant from the Westney
    study). It is intentionally **not** re-exported at the `musicalgestures` top level, since it
    would shadow the pre-existing `musicalgestures.dominant_frequency` (from `_analysis`). Reach
    it explicitly as `musicalgestures._mocap.dominant_frequency`.

---

## Pose-landmark trajectory extraction (`_posetools`)

The *array-level* pose workflow: video file → tidy per-landmark trajectory arrays (and
optionally CSV) → derived motion signals (limb speed, impact events). It complements — and does
not replace — the rendering-oriented `MgVideo.pose()` pipeline; use `_posetools` when you want
plain numpy trajectories for downstream signal analysis rather than rendered output.

```python
from musicalgestures import extract_pose_landmarks, limb_speed_from_landmarks, impact_events

traj = extract_pose_landmarks('strike.mp4', fps=30, width=640)   # needs the [pose] extra
wrists = traj['landmarks'][:, [15, 16], :2]           # left/right wrist, px
conf = traj['landmarks'][:, [15, 16], 2]              # MediaPipe visibility
speed = limb_speed_from_landmarks(wrists, conf, traj['fps'])   # px/s, bilateral max
impacts = impact_events(wrists, traj['fps'])                   # candidate strike events
```

Only `extract_pose_landmarks()` needs MediaPipe — install it with the optional extra:

```bash
pip install musicalgestures[pose]
```

It is imported lazily, so importing `musicalgestures` (and using the numpy-only helpers
`midpoint`, `limb_speed_from_landmarks`, `impact_events`) works without MediaPipe installed.
`extract_pose_landmarks()` supports both MediaPipe API families (the legacy Solutions API and
the newer Tasks API), since the wheels that removed Solutions vary across environments.

---

## Numpy-level motiongram data

`motiongram_data(frames, orientation='vertical', frame_diff=True, normalize=True)` (in
`_motionanalysis`) computes a motiongram as a plain numpy array from a stack of grayscale
frames, with a selectable `orientation` — `'vertical'` collapses each frame to its per-row mean
(image row vs. time, e.g. a mallet's approach-and-rebound path), `'horizontal'` to its
per-column mean (image column vs. time, side-to-side motion). It is the numpy-level counterpart
of `MgVideo.motiongrams()`'s rendered `_mgv`/`_mgh` images — use it when you want the motiongram
as data for further analysis, e.g. feeding it to `grid_qom()` or a peak-picker.

---

## Next steps

- [Audio-Video Analysis](audio-video.md) — the `MgVideo`-method-level audio–movement comparisons
  (`tempo_similarity`, `phase_synchrony`, `body_audio_coupling`, ...)
- [API Reference](../musicalgestures/index.md) — full signatures for every function above
- [Examples](../examples.md) — a runnable pulse-segmentation example

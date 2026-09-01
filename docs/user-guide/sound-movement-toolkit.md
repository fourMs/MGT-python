# Sound–Movement Analysis Toolkit

Alongside the `MgVideo`/`MgAudio` methods, MGT-python ships a lower-level toolkit of
plain-numpy sound–movement analysis functions, ported from the author's research pipelines.
They operate directly on arrays—onset times, trajectories, waveforms—with no video decoding
or rendering, and every function is importable from `musicalgestures` except where noted.
This page is a task reference; the course treatment, with worked narratives and study
context, is in
[chapter 11](https://github.com/fourMs/MGT-python/wiki/11-%E2%80%90-Pulse,-Cycles-and-Alignment)
and
[chapter 13](https://github.com/fourMs/MGT-python/wiki/13-%E2%80%90-Motion,-Audio-and-Posturography-Toolkit)
of the wiki course.

## Peak-picking core

```python
from musicalgestures import pick_peaks

idx = pick_peaks(qom_curve, fs=30.0, rel_threshold=0.4, min_interval=0.2)
```

`pick_peaks()` is the single adaptive peak-picker shared by the event detectors in `_pulse`
and `_audiofeatures`; it returns integer sample indices. Suitable values differ by signal
type, so tune the parameters rather than relying on the defaults, which the docstring
records as provisional.

## Pulse and cycle segmentation

```python
import numpy as np
from musicalgestures import segment_cycles, cycle_table, fit_accelerando

onsets = np.array([0.10, 0.34, 1.02, 1.24, 1.85, 2.02, 2.55, 2.68])   # seconds
cycles = segment_cycles(onsets)                 # list[Cycle]
table = cycle_table(cycles, clip_id='take01')   # per-cycle DataFrame (t, ioi, n_strokes, ...)
ioi0, t_double, r2 = fit_accelerando(table['t'], table['ioi'])
```

`segment_cycles()` groups onsets into stroke cycles by dynamic programming, `cycle_table()`
tabulates per-cycle metrics, and `fit_accelerando()` fits an exponential accelerando.
`motion_onsets()` returns the steepest sustained rises of a motion signal, for correlating
motion with the cycles.

## Cross-modal alignment

```python
from musicalgestures import xcorr_lag, anchor_and_match, offset_stats

lag, r = xcorr_lag(audio_envelope, motion_envelope, fs=25.0, max_lag=1.5)
offsets = anchor_and_match(impact_times, audio_onset_times, window=0.15)
stats = offset_stats(offsets)
```

`xcorr_lag()` returns `(lag, r)`, where a positive lag means the second signal happens after
the first. `sliding_correlation()` gives a windowed correlation profile, and
`envelope_agreement()` scores agreement among N parallel envelopes.

## Quantity-of-motion cores

```python
from musicalgestures import band_limited_qom, accel_to_speed

speed, fs_out = band_limited_qom(marker_xyz, fs=100.0)   # 0.2–5 Hz band
qom_speed = accel_to_speed(accel_xyz, fs=100.0)          # speed series (m/s)
```

Implemented in [micromotion](https://github.com/fourMs/micromotion) and re-exported here;
micromotion's documentation is the signature reference. Never average the raw acceleration
magnitude: a stationary accelerometer reads 1 g, so the mean of the raw norm measures
calibration rather than motion, which `accel_to_speed()` or `band_limited_qom()` avoids.
For the pose-specific `pose_qom()`/`body_scale()`/`normalized_qom()` see
[Pose Tracking](pose-tracking.md#derived-signals).

## Audio feature extraction

```python
from musicalgestures import rms_envelope, energy_onsets, t60_backward_decay

env, rate = rms_envelope(y, sr, window=0.02)
onsets = energy_onsets(y, sr)          # onset times (s) from the RMS envelope
t60, span = t60_backward_decay(y, sr)  # reverberation time
```

Scipy-only features complementing the librosa-based `MgAudio` methods; also
`spectral_flux()`, `spectral_flux_onsets()`, and `attack_spectral_centroid()`.
`energy_onsets()` is reliable for discrete strokes but over-fragments sustained rolls.

## Postural sway metrics

```python
from musicalgestures import cop_sway_metrics

metrics = cop_sway_metrics(cop_xy, fs=100.0)   # cop_xy: (T, 2) array [ML, AP], mm
print(metrics['path_len'], metrics['area95'], metrics['ap_ml_sd_ratio'])
```

Returns CoP path length and rate, the 95% confidence-ellipse area, ML/AP ranges, SDs and
their ratios, and mean sway frequency per axis. The complexity and direction measures
(`stabilogram_diffusion()`, `dfa()`, `sample_entropy()`, `sway_orientation()`, ...) are
implemented in micromotion and re-exported here.

## Physiology features

```python
from musicalgestures import respiration_rate, spectral_band_fractions

resp = respiration_rate(breathing_waveform, fs=25.0)   # {'rate_bpm', 'times_s', 'median_bpm'}
fractions = spectral_band_fractions(
    chest_qom, fs=25.0, bands={'cardiac': (0.9, 1.3), 'resp': (0.12, 0.5)})
```

`respiration_rate()` gives a windowed breathing rate in breaths/min, and
`spectral_band_fractions()` gives the fraction of Welch power in each caller-supplied named
band.

## Motion-capture I/O

```python
from musicalgestures import read_qtm_tsv, compare_modality_envelopes

names, data, fs = read_qtm_tsv('/path/to/session.tsv')   # data: (T, M, 3)
agreement = compare_modality_envelopes(mocap_env, video_env, fs_a=fs, fs_b=30.0)
```

`read_qtm_tsv()` reads Qualisys Track Manager TSV exports, with gap-fills converted to NaN.
Note that `_mocap` defines its own `dominant_frequency()`, which is not re-exported at the
top level; reach it as `musicalgestures._mocap.dominant_frequency`.

## Pose-landmark trajectories

The array-level pose workflow (`extract_pose_landmarks()`, `limb_speed_from_landmarks()`,
`impact_events()`, mocap validation) is covered in full on
[Pose Tracking](pose-tracking.md).

## Numpy-level motiongram data

```python
from musicalgestures import motiongram_data

mgv = motiongram_data(frames, orientation='vertical')     # image row vs. time
mgh = motiongram_data(frames, orientation='horizontal')   # image column vs. time
```

`motiongram_data()` (in `_motionanalysis`) computes a motiongram as a plain numpy array from
a stack of grayscale frames, the data counterpart of `MgVideo.motiongrams()`'s rendered
images.

## Further

- [Chapter 11: Pulse, Cycles and Alignment](https://github.com/fourMs/MGT-python/wiki/11-%E2%80%90-Pulse,-Cycles-and-Alignment)—the course treatment of peak-picking, cycle segmentation and cross-modal alignment
- [Chapter 13: Motion, Audio and Posturography Toolkit](https://github.com/fourMs/MGT-python/wiki/13-%E2%80%90-Motion,-Audio-and-Posturography-Toolkit)—the course treatment of QoM, audio features, sway and physiology
- API reference: [`_peaks`](../musicalgestures/_peaks.md), [`_pulse`](../musicalgestures/_pulse.md), [`_alignment`](../musicalgestures/_alignment.md), [`_qom`](../musicalgestures/_qom.md), [`_posture`](../musicalgestures/_posture.md), [`_physio`](../musicalgestures/_physio.md), [`_audiofeatures`](../musicalgestures/_audiofeatures.md), [`_mocap`](../musicalgestures/_mocap.md), [`_motionanalysis`](../musicalgestures/_motionanalysis.md)

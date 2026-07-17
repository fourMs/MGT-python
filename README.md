# MGT-python

[![PyPi version](https://badgen.net/pypi/v/musicalgestures/)](https://pypi.org/project/musicalgestures)
[![GitHub license](https://img.shields.io/github/license/fourMs/MGT-python.svg)](https://github.com/fourMs/MGT-python/blob/master/LICENSE)
[![CI](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml)
[![Documentation](https://github.com/fourMs/MGT-python/actions/workflows/docs.yml/badge.svg)](https://fourms.github.io/MGT-python/)

The **Musical Gestures Toolbox for Python** is a collection of tools for visualizing and analysing audio and video files.

![MGT python](https://raw.githubusercontent.com/fourMs/MGT-python/master/musicalgestures/documentation/figures/promo/ipython_example.gif)

📖 **[Documentation & Examples](https://fourms.github.io/MGT-python/)**

## Quick Start

### Installation

```bash
pip install musicalgestures
```

`musicalgestures` installs its core Python dependencies automatically. You still need a working `ffmpeg` installation on your system for video processing. For the pose-landmark-trajectory tools (`extract_pose_landmarks`, see below), add the optional `[pose]` extra: `pip install musicalgestures[pose]` (installs MediaPipe).

### Basic Usage

```python
import musicalgestures as mg

# Load a video (mp4, avi, mov, … all supported)
v = mg.MgVideo('dance.mp4')

# Create visualizations — call .show() to display the result
v.grid().show()
v.videograms().show()
v.average().show()
v.history().show()
v.heatmap().show()              # where the video changes most

# Motion analysis
v.motion().show()
v.motiontempo().show()          # dominant movement tempo (Hz/BPM)
v.motiondescriptors().show()    # motion energy, smoothness, entropy, spectral descriptors
v.eulerian(mode='motion').show()  # amplify subtle motion (EVM)

# Audio analysis
v.audio.waveform().show()
v.audio.spectrogram().show()
v.audio.mfcc().show()
v.audio.tempo().show()          # tempo + beat tracking
v.sonomotiongram().show()       # sonify the motiongram

# Pose estimation (MediaPipe is GPU-capable on the standard pip OpenCV)
v.pose(model='mediapipe').show()
```

> Display happens via `.show()` — analysis methods return result objects (`MgVideo`/`MgImage`/`MgFigure`) and do not auto-render.

### Runtime Notes

- `import musicalgestures` is fast: heavy dependencies are lazy-loaded, so the relevant backends load on first use rather than at import time.
- `ffmpeg` is required for video I/O and preprocessing.
- `pose()` defaults to the MediaPipe backend and downloads its weights on first use if they are missing; the OpenPose models (`'body_25'`/`'coco'`/`'mpi'`) download their larger Caffe weights on first use instead.
- In notebooks and other non-interactive runs, missing pose weights are downloaded automatically when possible.
- If `device='gpu'` is requested but OpenCV CUDA support is unavailable, `pose()` falls back to CPU execution.
- `flow.dense()`, `flow.sparse()`, and `blur_faces()` use CPU by default (`use_gpu=False`). Set `use_gpu=True` to opt into CUDA acceleration with automatic CPU fallback.
- `get_cuda_device_count()` is available to quickly check whether OpenCV sees CUDA devices.
- `blur_faces()` returns the generated result object consistently, including when `save_data=True`.

### Try Online

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

### Quick Links

- [Installation Guide](https://fourms.github.io/MGT-python/installation/)
- [Quick Start Tutorial](https://fourms.github.io/MGT-python/quickstart/)
- [API Reference](https://fourms.github.io/MGT-python/musicalgestures/)
- [Sound–Movement Analysis Toolkit](#soundmovement-analysis-toolkit)
- [Wiki & How-Tos](https://github.com/fourMs/MGT-python/wiki)
- [Contributing](docs/contributing.md)

## Features

- **Video Analysis**: Motion detection, optical flow, motion vectors, movement tempo, Eulerian Video Magnification, frame-rate/speed resampling (`resample()`), motion descriptors (energy/smoothness/entropy/spectral via `motiondescriptors()`)
- **Pose Estimation**: MediaPipe (default; fast on plain CPU, GPU-capable) and OpenPose (multi-person) backends, with average-pose and trajectory summaries (per-marker quantity of motion + dominant frequency), optional marker motion trails, a 3D pose waterfall (`pose_waterfall()`), per-segment circular statistics (`pose_segments()`), centroid centring (`pose_center()`), and per-marker distance travelled (`pose_distance()`)
- **Audio–movement analysis**: Compare a single performer's sound and motion — tempo similarity, phase synchrony, structural similarity, per-body-part audio coupling, and loudness/dynamics coupling
- **Sound–movement research toolkit**: Lower-level, array-based functions from the author's ro/stillstanding/Westney/cymbal studies — pulse/cycle segmentation, cross-modal alignment, body-scale-normalized quantity of motion, postural sway metrics, physiology features, mocap I/O, and pose-landmark trajectory extraction (see [Sound–Movement Analysis Toolkit](#soundmovement-analysis-toolkit) below)
- **Audio Processing**: Waveforms, spectrograms, MFCC, chromagrams, tempo/beat tracking, spectral descriptors
- **Visualizations**: Motiongrams, videograms, motion history, heatmaps, sonomotiongrams (motion → sound)
- **Space-time displays**: Stroboscope (chronophotography), silhouette waterfall, Motion History Image, 3D space-time volume, combined motion SSM
- **Integration**: Works with NumPy, SciPy, librosa, and Matplotlib ecosystems
- **Cross-platform**: Linux, macOS, Windows support

## Sound–Movement Analysis Toolkit

Alongside the `MgVideo`/`MgAudio` methods above, MGT-python exposes a lower-level toolkit of
plain-numpy sound–movement analysis functions, ported from the author's own research pipelines
(the **ro** ritual-drumming study, the **stillstanding**/standstill-championship posturography
study, the **Westney** with/without-audience piano comparisons, and the **cymbal**-comparison
striking study). They work on arrays — not on `MgVideo`/`MgAudio` objects — so they drop straight
into notebooks, batch scripts, or your own analysis pipeline, and are all importable directly from
`musicalgestures`:

- **`_peaks`** — `pick_peaks`: the one adaptive peak-picker (smoothing, relative threshold, minimum
  interval, prominence gate) shared by every event detector below.
- **`_pulse`** — `Cycle`, `group_strokes`, `segment_cycles`, `cycle_table`, `fit_accelerando`,
  `motion_onsets`: group onsets into rhythmic cycles and fit an exponential accelerando.
- **`_alignment`** — `xcorr_lag`, `envelope_lag`, `per_cycle_motion_delta`, `anchor_and_match`,
  `offset_stats`, `sliding_correlation`, `envelope_agreement`: lead/lag and coupling between two
  (or more) time-aligned signals.
- **`_qom`** — `band_limited_qom`, `accel_to_speed`, `group_qom`, `pose_qom`, `body_scale`,
  `normalized_qom`, `grid_qom`, `envelope`, `bin_series`: quantity-of-motion cores for position,
  pose-landmark and accelerometer data, including body-scale (framing-invariant) normalization.
- **`_audiofeatures`** — `rms_envelope`, `spectral_flux`, `spectral_flux_onsets`, `energy_onsets`,
  `t60_backward_decay`, `attack_spectral_centroid`: scipy-only audio features and onset detectors.
- **`_posture`** — `cop_sway_metrics`, `confidence_ellipse_area`, `convex_hull_area`,
  `stabilogram_diffusion`, `dfa`, `sample_entropy`, `spectral_edges`, `sway_texture`,
  `sway_orientation`, `axial_rayleigh`, `spatial_extent`, `principal_axis_projection`: standing-sway
  and postural-control metrics from a centre-of-pressure or marker trace.
- **`_physio`** — `respiration_rate`, `spectral_band_fractions`: breathing rate and spectral
  composition of physiological waveforms.
- **`_mocap`** — `read_qtm_tsv`, `compare_modality_envelopes`: a robust Qualisys (QTM) TSV reader
  and cross-modality envelope comparison. (`_mocap` also defines its own `dominant_frequency`, a
  Welch-peak variant kept as `musicalgestures._mocap.dominant_frequency` rather than re-exported at
  top level, since it would otherwise shadow the pre-existing `musicalgestures.dominant_frequency`.)
- **`_posetools`** — `extract_pose_landmarks`, `midpoint`, `limb_speed_from_landmarks`,
  `impact_events`: video → tidy per-landmark trajectory arrays, plus derived limb-speed and
  impact-event signals. `extract_pose_landmarks` needs MediaPipe (`pip install musicalgestures[pose]`),
  imported lazily — the derived-signal helpers are numpy-only.
- **`motiongram_data`** (in `_motionanalysis`) gained an `orientation='vertical'|'horizontal'`
  option for the numpy-level motiongram, matching the two `motiongrams()` render directions.

A few illustrative snippets:

```python
# Pulse-train segmentation: group stroke onsets into rhythmic cycles and fit
# an accelerando (ro study)
import numpy as np
from musicalgestures import segment_cycles, cycle_table, fit_accelerando

onsets = np.array([0.10, 0.34, 1.02, 1.24, 1.85, 2.02, 2.55, 2.68])  # seconds
cycles = segment_cycles(onsets)                  # -> list[Cycle]
table = cycle_table(cycles, clip_id='ro_2023')    # per-cycle DataFrame
ioi0, t_double, r2 = fit_accelerando(table['t'], table['ioi'])
print(f"tempo doubles every {t_double:.1f}s (R²={r2:.2f})")
```

![Pulse segmentation: onsets grouped into stroke cycles with a fitted accelerando](https://raw.githubusercontent.com/fourMs/MGT-python/master/docs/images/examples/pulse_segmentation.gif)

```python
# Quantity of motion + body-scale normalization: framing-invariant QoM in
# body-lengths/second, comparable across recordings/zoom levels (Westney study)
from musicalgestures import extract_pose_landmarks, normalized_qom

traj = extract_pose_landmarks('performance.mp4', fps=25, width=480)
qom, speed, fs_out = normalized_qom(traj['landmarks'][..., :2], traj['fps'])
print(f"{qom:.3f} body-lengths/s")
```

```python
# Standing-sway metrics from a centre-of-pressure (or marker) trace (stillstanding study)
from musicalgestures import cop_sway_metrics

metrics = cop_sway_metrics(cop_xy, fs=100.0)     # cop_xy: (T, 2) array [ML, AP], mm
print(metrics['path_len'], metrics['area95'], metrics['ap_ml_sd_ratio'])
```

```python
# Pose-trajectory extraction and impact detection from striking gestures (cymbal study)
from musicalgestures import extract_pose_landmarks, limb_speed_from_landmarks, impact_events

traj = extract_pose_landmarks('strike.mp4', fps=30, width=640)
wrists = traj['landmarks'][:, [15, 16], :2]           # left/right wrist, px
conf = traj['landmarks'][:, [15, 16], 2]
speed = limb_speed_from_landmarks(wrists, conf, traj['fps'])   # px/s, bilateral max
impacts = impact_events(wrists, traj['fps'])                   # acceleration-peak events
```

See the [API reference](https://fourms.github.io/MGT-python/musicalgestures/) for full signatures
and each function's provenance note.

## Presentation

See this short video presentation made for the Nordic Sound and Music Computing Conference 2021:

[![nordicsmc2021-thumbnail_640](https://github.com/user-attachments/assets/150b1143-0730-4083-af52-8c062a080deb)](https://www.youtube.com/watch?v=tZVX_lDFrwc)

## Requirements

- Python 3.10+
- FFmpeg
- See [installation guide](docs/installation.md) for complete requirements

## Research Background

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/). Many researchers and research assistants have helped its development over the years, including [Balint Laczko](https://github.com/balintlaczko), [Joachim Poutaraud](https://github.com/joachimpoutaraud), [Frida Furmyr](https://github.com/fridafu), [Marcus Widmer](https://github.com/marcuswidmer), [Alexander Refsum Jensenius](https://github.com/alexarje/)

The software is currently maintained by the [fourMs lab](https://github.com/fourMs) at [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/) at the University of Oslo.

## Reference

If you use this toolbox in your research, please cite this article:

- Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](http://urn.nb.no/URN:NBN:no-91935). *Proceedings of the Nordic Sound and Music Computing Conference*, Copenhagen.

```bibtex
@inproceedings{laczkoReflectionsDevelopmentMusical2021,
    title = {Reflections on the Development of the Musical Gestures Toolbox for Python},
    author = {Laczkó, Bálint and Jensenius, Alexander Refsum},
    booktitle = {Proceedings of the Nordic Sound and Music Computing Conference},
    year = {2021},
    address = {Copenhagen},
    url = {http://urn.nb.no/URN:NBN:no-91935}
}
```

## License

This toolbox is released under the [GNU General Public License 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).

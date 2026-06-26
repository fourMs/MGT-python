# Video Analysis

All video analysis methods are called on an `MgVideo` object. Each method writes output files alongside the source video and returns a result object you can use directly or pass to further methods.

```python
import musicalgestures as mg

mv = mg.MgVideo('/path/to/video.avi')
```

## AVI conversion (`convert`)

Most analysis methods stream frames straight through FFmpeg and run on any container, including MP4 — e.g. `motion()`, `motiongrams()`, `average()`/`blend()`, `videograms()`, `heatmap()`, `eulerian()`, `motiontempo()`, `sonomotiongram()`, `grid()`, `subtract()`, and `history()`.

A few methods that decode frame-by-frame with OpenCV first convert the input to an all-intra **MJPEG `.avi`** (cached once as `self.as_avi`) for frame-accurate decoding: `pose()`, `flow.dense()`/`flow.sparse()`, `directograms()`, `impacts()`, `motion_mp()`, and `history_cv2()`. The motion **video output** is also written as `.avi`.

If your MP4 decodes reliably and you want to skip that conversion (faster, no extra file), pass `convert=False`:

```python
mv = mg.MgVideo('clip.mp4')
mv.pose(model='mediapipe', convert=False)     # read the mp4 directly
mv.flow.dense(convert=False)
mv.directograms(convert=False)
```

The default `convert=True` keeps the safe, frame-accurate behaviour.

---

## Threshold and filter parameters

Many methods accept `threshold` and `filtertype`:

- `threshold` (float, 0–1): pixels with a value below this fraction of 255 are set to zero. The default is `0.05`. Higher values remove more background noise but may lose subtle motion.
- `filtertype` (str): `'Regular'` (default) thresholds and median-filters; `'Binary'` binarises the output; `'Blob'` applies erosion instead.

See the [filter reference](../musicalgestures/_filter.md) for details.

---

## Motion analysis

`motion()` is the primary analysis method. It renders a motion video, horizontal and vertical motiongrams, a motion plot, and a CSV of per-frame motion data, all in one call. It returns an `MgVideo` pointing to the motion video.

```python
motion_video = mv.motion()      # returns MgVideo
motion_video.show()
mv.show(key='motion')           # equivalent shorthand
```

### Shortcuts

```python
motion_vid = mv.motionvideo()   # motion video only — returns MgVideo

motiondata = mv.motiondata()    # CSV only — returns list of paths
motiondata = mv.motiondata(motion_analysis='aom')

motionplots = mv.motionplots()  # motion plot image — returns MgImage
motionplots = mv.motionplots(audio_descriptors=True)
motionplots.show()
mv.show(key='plot')

motiongrams = mv.motiongrams()  # returns MgList[MgImage, MgImage]
motiongrams[0].show()           # horizontal motiongram (mgx)
motiongrams[1].show()           # vertical motiongram (mgy)
mv.show(key='mgx')
mv.show(key='mgy')

score = mv.motionscore()        # average VMAF motion score — returns float
```

### Motion data columns

The CSV produced by `motion()` and `motiondata()` contains one row per frame:

| Column | Description |
|---|---|
| Time | Frame timestamp in milliseconds |
| Qom | Quantity of motion (sum of active pixels) |
| ComX, ComY | Centroid of motion (normalised 0–1) |
| AomX1, AomY1, AomX2, AomY2 | Bounding box of motion area (normalised) |

---

## Motion heatmap

`heatmap()` accumulates the absolute frame-to-frame difference across the whole video into a single colour-mapped image, so hot regions mark where the most change happened. By default the heat is overlaid on a dimmed average frame for spatial context.

```python
heat = mv.heatmap()                                    # returns MgImage
heat = mv.heatmap(colormap='jet', overlay=False)       # bare heatmap on black
heat = mv.heatmap(blur=3, gamma=0.4, colormap='viridis')
heat.show()
```

- `colormap`: any matplotlib colormap (`'inferno'` default)
- `overlay`: composite on the dimmed average frame (default `True`); `alpha`/`background_dim` tune the mix
- `blur`: optional Gaussian smoothing radius; `gamma` (<1) boosts faint motion
- `normalize`: scale the most active pixel to the top of the colormap

---

## Movement tempo

`motiontempo()` estimates the dominant movement tempo from the quantity of motion (mean absolute frame difference) via an FFT, reported in both Hz and BPM.

```python
mt = mv.motiontempo()                       # returns MgFigure
print(mt.data['tempo_bpm'])                 # dominant tempo in BPM
print(mt.data['dominant_frequency'])        # in Hz
mt.show()                                   # QoM signal + movement spectrum
```

Restrict the search band with `fmin`/`fmax` (Hz).

---

## Motion vectors

`motionvectors()` visualises the motion vectors carried by inter-frame codecs (MPEG, H.264, H.265) using FFmpeg's `codecview` filter — a decoder-level view of motion with no recomputation.

```python
mvecs = mv.motionvectors()      # returns MgVideo
mvecs.show()
```

!!! note
    Intra-only formats (e.g. MJPEG in many `.avi` files) carry no motion vectors. Convert to an mp4/H.264 source first to see them.

---

## Eulerian Video Magnification

`eulerian()` amplifies subtle changes that are normally invisible (Wu et al., SIGGRAPH 2012).

```python
# Amplify subtle COLOUR changes (e.g. pulse, breathing)
evm = mv.eulerian(mode='color', freq_low=0.83, freq_high=1.0, amplification=50)

# Amplify subtle MOTION
evm = mv.eulerian(mode='motion', freq_low=0.4, freq_high=3.0, amplification=20)
evm.show()
```

- `mode='color'` uses a Gaussian pyramid + ideal FFT temporal band-pass (two-pass, low memory)
- `mode='motion'` uses a Laplacian pyramid + streaming IIR band-pass (frame-by-frame, low memory)
- `freq_low`/`freq_high` set the temporal band in Hz; `amplification` is the gain; `levels` the pyramid depth

---

## Sonomotiongram

`sonomotiongram()` sonifies the motiongram: the motiongram matrix is treated as a magnitude spectrogram (spatial position → frequency, motion intensity → amplitude) and resynthesised to audio via an inverse STFT (Griffin–Lim). It returns an [`MgAudio`](audio-analysis.md), so you can analyse or play the result.

```python
son = mv.sonomotiongram(sonogram='vertical')   # or 'horizontal' — returns MgAudio
son.waveform().show()
son.spectrogram().show()
# rendered WAV at son.filename
```

---

## Videograms

Videograms apply the motiongram technique to the source video directly, without first computing frame differences. They show the full scene content over time rather than motion only.

```python
videograms = mv.videograms()    # returns MgList[MgImage, MgImage]
videograms[0].show()            # horizontal videogram (vgx)
videograms[1].show()            # vertical videogram (vgy)
mv.show(key='vgx')
mv.show(key='vgy')
```

---

## Self-Similarity Matrix (SSM)

SSMs compare each column or row of a motiongram or videogram against all others, revealing periodic structure in the motion.

```python
motionssm = mv.ssm(features='motiongrams')              # returns MgList
motionssm = mv.ssm(features='motiongrams', cmap='viridis', norm=2)
motionssm[0].show()     # horizontal SSM
motionssm[1].show()     # vertical SSM
mv.show(key='ssm')

videossm = mv.ssm(features='videograms')
chromassm = mv.ssm(features='chromagram', cmap='magma', norm=2)
spectrossm = mv.ssm(features='spectrogram')
```

---

## Background subtraction

`subtract()` removes a static background from each frame. If no background image is provided, it computes the frame average automatically.

```python
subtraction = mv.subtract()                                             # returns MgVideo
subtraction = mv.subtract(bg_img='/path/to/background.png', bg_color='#ffffff')
subtraction = mv.subtract(bg_img='/path/to/background.png', curves=0.3)
subtraction.show()
mv.show(key='subtract')
```

---

## Grid preview

`grid()` assembles a strip of evenly-spaced frames into a single image, useful for quickly reviewing a recording.

```python
grid = mv.grid(height=300, rows=3, columns=3)  # returns MgImage
grid.show()
grid_array = mv.grid(height=300, rows=3, columns=3, return_array=True)
```

---

## History video

`history()` overlays the last `history_length` frames onto each frame, making the trajectory of motion visible.

```python
history = mv.history(history_length=20)     # returns MgVideo
history.show()
mv.show(key='history')
```

Applying history to a motion video emphasises movement traces:

```python
motionhistory = mv.motionvideo().history()
mv.show(key='motionhistory')
```

---

## Blend

`blend()` combines all frames into a single image using a compositing mode.

```python
average = mv.average()                          # returns MgImage (mean of all frames)
average = mv.blend(component_mode='average')    # equivalent
lighten = mv.blend(component_mode='lighten')
darken  = mv.blend(component_mode='darken')
average.show()
mv.show(key='blend')
```

Motion average — blend applied to a motion video — shows where movement was concentrated:

```python
motion_average = mv.motionvideo().blend(component_mode='average')
motion_average.show()
```

---

## Pose estimation

`pose()` runs skeleton estimation on each frame, with two backends:

- **MediaPipe** (`model='mediapipe'`): Google MediaPipe Pose, 33 landmarks. Model auto-downloads (~8–28 MB). Supports GPU via MediaPipe's own delegate, independent of OpenCV's CUDA build — so it works on the standard pip OpenCV.
- **OpenPose** (`model='body_25'`/`'coco'`/`'mpi'`): Caffe models (~200 MB on first use). GPU here needs an OpenCV compiled with CUDA.

```python
pose = mv.pose(model='mediapipe', device='gpu')                 # recommended; GPU-capable
pose = mv.pose(model='coco', device='cpu', downsampling_factor=4)
pose = mv.pose(model='body_25', device='gpu', threshold=0.1)
pose.show()
mv.show(key='pose')

# draw only the markers on a black background (no video underneath)
pose = mv.pose(model='mediapipe', style='markers', overlay=False)
# draw only the skeleton (joint lines) over the video
pose = mv.pose(model='mediapipe', style='skeleton')
# markers/skeleton on a white background
pose = mv.pose(model='mediapipe', overlay=False, background='white')
```

- `model`: `'mediapipe'`, `'body_25'` (default), `'coco'`, or `'mpi'`
- `style`: `'both'` (default), `'markers'` (keypoints only), or `'skeleton'` (joint lines only)
- `overlay`: `True` (draw on the video) or `False` (draw on a plain background)
- `background`: `'black'` (default) or `'white'` — the background colour when `overlay=False` (colours adapt for contrast)
- `device`: `'cpu'` or `'gpu'`. For OpenPose models, if `device='gpu'` is requested but OpenCV lacks CUDA, `pose()` automatically switches to the MediaPipe backend (when installed) so the GPU is still used; otherwise it falls back to CPU.
- `downsampling_factor`: reduces input resolution before inference (OpenPose only); higher is faster but less accurate
- `threshold`: minimum network confidence to accept a keypoint (normalised 0–1)

`pose()` also renders two summary images of the whole video (disable with `save_average_pose=False` / `save_trajectories=False`), attached to the returned video:

```python
pv = mv.pose(model='mediapipe')
pv.average_pose.show()     # average pose; markers coloured/labelled by QoM (px/frame) + dominant frequency (Hz)
pv.trajectories.show()     # every marker's spatial path over the whole video
# a per-marker stats CSV (<name>_pose_average_stats.csv) with average QoM and frequency is also saved
```

!!! tip "GPU acceleration"
    `pose(model='mediapipe', device='gpu')` gives GPU acceleration with the standard pip OpenCV. The OpenCV-based methods (`flow.dense(use_gpu=True)`, `blur_faces(use_gpu=True)`, OpenPose `device='gpu'`) need an OpenCV built with CUDA. Use `mg.cuda_build_available()` to check, and `mg.cuda_unavailable_reason()` for an explanation.

---

## Optical flow

### Sparse

Sparse optical flow tracks a small set of salient feature points and draws their trajectories.

```python
flow_sparse = mv.flow.sparse()      # returns MgVideo
flow_sparse.show()
mv.show(key='sparse')
```

### Dense

Dense optical flow estimates movement at every pixel, colour-coding direction.

```python
flow_dense = mv.flow.dense()                    # returns MgVideo
flow_dense = mv.flow.dense(use_gpu=True)        # CUDA acceleration with CPU fallback
flow_dense.show()
mv.show(key='dense')
```

### Velocity

Setting `velocity=True` computes per-frame speed instead of direction, and returns an `MgFigure` with the velocity plot and associated data.

```python
velocity = mv.flow.dense(velocity=True)
velocity_per_meters = mv.flow.dense(velocity=True, distance=3.5, angle_of_view=80)
xvel = velocity.data['xvel']
yvel = velocity.data['yvel']
velocity.figure
```

---

## Face anonymisation

`blur_faces()` detects faces in every frame and applies a blur, black rectangle, or image mask.

```python
blur = mv.blur_faces()                                  # returns MgVideo
blur = mv.blur_faces(use_gpu=True)
blur = mv.blur_faces(save_data=True, data_format='csv')
blur.show()
mv.show(key='blur')

source_image = '/path/to/mask.jpg'
mv.blur_faces(mask='image', mask_image=source_image)
```

To render a heatmap of face detection centroids instead:

```python
heatmap = mv.blur_faces(draw_heatmap=True, neighbours=128, resolution=500, save_data=False)
heatmap.show()
```

---

## Warp audiovisual beats

`warp_audiovisual_beats()` temporally aligns visual beats (extracted from directograms) with audio beats to create a re-timed video.

```python
warp = mv.warp_audiovisual_beats('/path/to/audio.wav')  # returns MgVideo
warp.show()
mv.show(key='warp')
```

### Directograms

Directograms factor motion magnitude into angular bins, analogous to a spectrogram with angles replacing frequencies.

```python
directograms = mv.directograms()    # returns MgFigure
directograms.data['directogram']
directograms.show()
```

### Impacts

Impacts are visual analogues of audio onset envelopes, derived from directogram deceleration.

```python
impacts = mv.impacts(detection=False)                               # returns MgFigure
impacts = mv.impacts(detection=True, local_mean=0.1, local_maxima=0.15)
impacts.data['impact envelopes']
impacts.show()
```

---

## Next steps

- [Audio Analysis](audio-analysis.md) — waveforms, spectrograms, and audio features
- [Working with Results](results.md) — combining and displaying MgFigure, MgImage, and MgList
- [API Reference](../musicalgestures/_motionvideo.md) — complete motion method signatures

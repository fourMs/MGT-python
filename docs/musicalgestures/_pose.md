# Pose

> Auto-generated documentation for [musicalgestures._pose](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Pose
    - [download_model](#download_model)
    - [mg_pose_center](#mg_pose_center)
    - [mg_pose_distance](#mg_pose_distance)
    - [mg_pose_segments](#mg_pose_segments)
    - [mg_pose_waterfall](#mg_pose_waterfall)
    - [pose](#pose)

#### Attributes

- `MEDIAPIPE_POSE_CONNECTIONS` - MediaPipe Pose skeleton connections (pairs of landmark indices): `[(0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5)...`
- `OPENPOSE_NAMES` - OpenPose marker names per model (order matches the network keypoint indices): `{'coco': ['Nose', 'Neck', 'Right Shoulder', 'Ri...`

## download_model

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L1347)

```python
def download_model(modeltype):
```

Download the OpenPose Caffe weights (.caffemodel) for the given model type into the package's
``pose/`` folder.

Uses Python's ``urllib`` directly (cross-platform, no external ``wget`` / shell scripts /
bundled binary). The ``.prototxt`` configs ship with the package; only the large weights file
is fetched.

## mg_pose_center

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L961)

```python
def mg_pose_center(
    self,
    save_data=True,
    dpi=200,
    target_name=None,
    overwrite=True,
    **pose_kwargs,
) -> 'MgFigure':
```

Centre the pose data on its global centroid — a 2D port of the MoCap Toolbox ``mccenter``.

A single offset per coordinate (the mean of the per-marker temporal means, missing detections
ignored) is subtracted from every marker so the overall spatiotemporal centroid sits at the
origin (0, 0). This removes the performer's absolute position in the frame, leaving relative
posture/movement — useful before comparing or further analysing trajectories. Plots the centred
marker trajectories and (by default) saves a CSV of the centred coordinates. Uses cached pose
keypoints when available, otherwise runs ``pose()`` first (``**pose_kwargs`` are forwarded).

#### Arguments

- `save_data` *bool, optional* - Save a CSV of the centred coordinates. Defaults to True.
- `dpi` *int, optional* - Output DPI. Defaults to 200.
- `target_name` *str, optional* - Output name. Defaults to None ("_pose_centered.png").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.
- `**pose_kwargs` - Forwarded to ``pose()`` if keypoints have to be computed.

#### Returns

- `MgFigure` - the centred-trajectories figure; ``.data['coords']`` holds the (T, n, 2) centred
coordinates and ``.data['offset']`` the removed centroid. None if there are too few frames.

## mg_pose_distance

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L1011)

```python
def mg_pose_distance(
    self,
    dpi=200,
    target_name=None,
    overwrite=True,
    **pose_kwargs,
) -> 'MgFigure':
```

Per-marker distance travelled and the average across markers — a 2D port of the MoCap Toolbox
``mccumdist``.

Sums each marker's frame-to-frame Euclidean displacement (in pixels) and accumulates it over
time. The figure shows the per-marker cumulative-distance curves and a ranked bar chart of the
total distance per marker with the across-marker average marked; a CSV of the totals (plus the
average) is saved. Uses cached pose keypoints when available, otherwise runs ``pose()`` first
(``**pose_kwargs`` are forwarded).

#### Arguments

- `dpi` *int, optional* - Output DPI. Defaults to 200.
- `target_name` *str, optional* - Output name. Defaults to None ("_pose_distance.png").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.
- `**pose_kwargs` - Forwarded to ``pose()`` if keypoints have to be computed.

#### Returns

- `MgFigure` - ``.data['total']`` (per-marker totals), ``.data['average']`` (mean total), and
``.data['cumulative']`` (per-marker cumulative curves). None if there are too few frames.

## mg_pose_segments

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L916)

```python
def mg_pose_segments(
    self,
    segments=None,
    n_bins=36,
    cmap='viridis',
    dpi=200,
    ncols=6,
    target_name=None,
    overwrite=True,
    **pose_kwargs,
) -> 'MgFigure':
```

Circular (polar) motion plots and statistics for each body segment.

A *segment* is the bone between two connected joints (e.g. shoulder–elbow). For every segment
this computes its per-frame orientation angle and draws a polar rose histogram of the angle
distribution with the mean-direction resultant vector, annotated with circular statistics
(mean angle, resultant length R, and range of motion). A CSV of the per-segment statistics —
mean angle, R, circular std, range of motion, and mean angular speed — is saved alongside the
image. Uses cached pose keypoints from a previous ``pose()`` call when available; otherwise it
runs pose estimation first (``model``/``device``/… are forwarded to ``pose()``).

#### Arguments

- `segments` *list, optional* - Subset of connections as ``(a, b)`` joint-index tuples.
    Defaults to all skeleton connections.
- `n_bins` *int, optional* - Number of angular bins per rose. Defaults to 36 (10° bins).
- `cmap` *str, optional* - Matplotlib colormap for the bars. Defaults to 'viridis'.
- `dpi` *int, optional* - Output DPI. Defaults to 200.
- `ncols` *int, optional* - Columns in the subplot grid. Defaults to 6.
- `target_name` *str, optional* - Output name. Defaults to None ("_pose_segments.png").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.
- `**pose_kwargs` - Forwarded to ``pose()`` if keypoints have to be computed.

#### Returns

- `MgFigure` - the grid of circular plots (per-segment stats in ``.data['stats']``), or None.

## mg_pose_waterfall

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L861)

```python
def mg_pose_waterfall(
    self,
    style='trajectories',
    n_samples=40,
    markers=None,
    color_by=None,
    cmap='hsv',
    dpi=200,
    elev=20,
    azim=-60,
    lw=1.0,
    axes=True,
    crop=False,
    target_name=None,
    overwrite=True,
    **pose_kwargs,
) -> 'MgFigure':
```

Render a 3D spatio-temporal waterfall of the pose, cascading along the time (depth) axis —
a pose-based counterpart to ``silhouette_waterfall()``. Uses cached pose keypoints from a
previous ``pose()`` call when available; otherwise it runs pose estimation first (extra
keyword arguments such as ``model``/``device``/``downsampling_factor`` are forwarded to
``pose()``).

#### Arguments

- `style` *str, optional* - What to draw. ``'trajectories'`` (default) draws each marker's
    continuous path through (x, time, y); ``'markers'`` scatters the markers at
    ``n_samples`` time slices; ``'skeleton'`` draws the skeleton joint lines at each
    time slice; ``'both'`` draws markers + skeleton.
- `n_samples` *int, optional* - Number of time slices for the marker/skeleton styles.
    Defaults to 40 (ignored for ``'trajectories'``).
- `markers` *list, optional* - Subset of marker names or indices to draw. Defaults to all.
- `color_by` *str, optional* - ``'marker'`` or ``'time'``. Defaults to None ("auto"):
    'marker' for trajectories, 'time' for the slice styles.
- `cmap` *str, optional* - Matplotlib colormap. Defaults to 'hsv'.
- `dpi` *int, optional* - Output DPI. Defaults to 200.
- `elev` *float, optional* - 3D elevation angle. Defaults to 20.
- `azim` *float, optional* - 3D azimuth angle. Defaults to -60.
- `lw` *float, optional* - Line width. Defaults to 1.0.
- `axes` *bool, optional* - Draw the axes and tick labels. Set to False for a clean render
    with all axes and text removed. Defaults to True.
- `crop` *bool, optional* - Tighten the spatial limits to the marker extent and trim the
    surrounding whitespace, so the figure shows mostly the data. Defaults to False.
- `target_name` *str, optional* - Output name. Defaults to None ("_pose_waterfall.png").
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.
- `**pose_kwargs` - Forwarded to ``pose()`` if keypoints have to be computed.

#### Returns

- `MgFigure` - the 3D waterfall figure, or None if there are too few frames.

## pose

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L104)

```python
def pose(
    self,
    model='mediapipe',
    device='gpu',
    threshold=0.1,
    downsampling_factor=2,
    use_cache=True,
    save_data=True,
    data_format='csv',
    save_video=True,
    style='both',
    overlay=True,
    background='black',
    convert=None,
    quiet=True,
    marker_history=0,
    save_average_pose=True,
    save_trajectories=True,
    transparent_trajectories=None,
    trajectory_background=None,
    trajectory_labels=False,
    target_name_video=None,
    target_name_data=None,
    target_name_average=None,
    target_name_trajectories=None,
    overwrite=True,
) -> 'musicalgestures.MgVideo':
```

Renders a video with the pose estimation (aka. "keypoint detection" or "skeleton tracking") overlaid on it.
Outputs the predictions in a text file containing the normalized x and y coordinates of each keypoint
(default format is csv).

Supports two backends:

* **MediaPipe** (``model='mediapipe'``): Uses Google's MediaPipe Pose which detects 33
  landmarks. Runs on CPU, or on GPU via MediaPipe's GPU delegate when ``device='gpu'``
  (with automatic CPU fallback if the delegate is unavailable). Requires the optional
  ``mediapipe`` package (``pip install musicalgestures[pose]``). On first use, the model
  file (~8–28 MB) is downloaded automatically and cached in ``musicalgestures/models/``.
* **OpenPose** (``model='body_25'``, ``'coco'``, or ``'mpi'``): Uses Caffe-based OpenPose
  models.  Model weights (~200 MB) are downloaded on first use. GPU here requires an
  OpenCV built with CUDA; if unavailable while ``device='gpu'``, ``pose()`` automatically
  switches to the MediaPipe backend (when installed) for GPU acceleration.

#### Arguments

- `model` *str, optional* - Pose model to use. ``'mediapipe'`` (default) uses MediaPipe Pose (33
    landmarks with depth + visibility, model auto-downloaded on first use); it is fast on plain
    CPU, needs no CUDA build, and is best for single-person analysis. ``'body_25'`` loads the
    OpenPose BODY_25 model (25 keypoints), ``'mpi'`` loads the MPII model (15 keypoints),
    ``'coco'`` loads the COCO model (18 keypoints). The OpenPose models support multi-person
    scenes but are slow without a CUDA-enabled OpenCV build. Defaults to 'mediapipe'.
- `device` *str, optional* - Compute backend ('cpu' or 'gpu'). For OpenPose models this
    selects the OpenCV DNN backend (GPU needs a CUDA-enabled OpenCV). For MediaPipe
    it selects the inference delegate (GPU delegate with CPU fallback). Defaults to 'gpu'.
- `threshold` *float, optional* - The normalized confidence threshold that decides whether we
    keep or discard a predicted point. Discarded points get substituted with (0, 0) in the
    output data. Defaults to 0.1.
- `downsampling_factor` *int, optional* - Decides how much we downsample the video before we
    pass it to the neural network. Ignored when ``model='mediapipe'``. Defaults to 2.
- `use_cache` *bool, optional* - If True (default), reuse keypoints from a previous pose() run on
    this object (same model/threshold) to re-render a different `style`/`overlay`/`background`
    without re-running the network — e.g. run `style='markers'` then `style='skeleton'` fast.
    Defaults to True.
- `save_data` *bool, optional* - Whether we save the predicted pose data to a file. Defaults to True.
- `data_format` *str, optional* - Specifies format of pose-data. Accepted values are 'csv', 'tsv',
    'txt' and 'c3d' (motion-capture format; requires the optional ``c3d`` package). For multiple
    output formats, use a list, e.g. ['csv', 'c3d']. Defaults to 'csv'.
- `save_video` *bool, optional* - Whether we save the video with the estimated pose overlaid on it.
    Defaults to True.
- `style` *str, optional* - How to draw the pose. `'both'` draws markers (keypoints) connected by
    joint lines (the skeleton); `'markers'` draws only the keypoints; `'skeleton'` draws only
    the connecting joint lines. Defaults to 'both'.
- `overlay` *bool, optional* - If True, draw the pose on top of the original video frames. If False,
    draw it on a plain background instead (a "markers only" video with no video underneath).
    Defaults to True.
- `background` *str, optional* - Background colour used when `overlay=False`: `'black'` (default) or
    `'white'`. With `'white'` the skeleton and markers are drawn in black (an inverted, print-friendly
    look). With `'black'` they are drawn in bright colours. Ignored when `overlay=True`.
- `marker_history` *int, optional* - If greater than 0, draw a motion trail for every marker by joining its
    positions over the last `marker_history` frames. Defaults to 0 (no trails). Works in all rendering
    paths (OpenPose, MediaPipe, and cached re-render).
- `convert` *bool, optional* - Whether non-AVI input is first converted to an all-intra MJPEG `.avi`
    (cached as ``self.as_avi``) for frame-accurate decoding. Defaults to None ("auto"): the
    MediaPipe backend reads the source file directly (it decodes sequentially through an FFmpeg
    pipe and needs no intra-frame AVI), while the OpenPose backend converts. Pass True/False to
    force the behaviour.
- `quiet` *bool, optional* - MediaPipe only. If True (default), suppress MediaPipe's native C++/GL
    console logs (EGL init, absl INFO/WARNING, GPU-delegate messages) during inference. Set to
    False to see them for debugging.
- `target_name_video` *str, optional* - Target output name for the video. Defaults to None (which
    assumes that the input filename with the suffix "_pose" should be used).
- `save_average_pose` *bool, optional* - Whether to also render an image of the average pose over
    the whole video, with each marker coloured/labelled by its average quantity of motion
    (px/frame) and labelled with its dominant movement frequency (Hz). A CSV of the per-marker
    statistics is saved alongside it. Defaults to True.
- `save_trajectories` *bool, optional* - Whether to also render an image of every marker's spatial
    trajectory across the whole video. Defaults to True.
- `trajectory_labels` *bool, optional* - Whether to annotate the trajectories image with each
    marker's name. Defaults to False (cleaner image).
- `trajectory_background` *str, optional* - Background of the trajectories PNG: ``'black'``,
    ``'white'``, or ``'transparent'`` (for overlaying on the video). Defaults to None
    - `("auto")` - transparent when the trajectories image is the only one exported, else black.
    Takes precedence over the legacy ``transparent_trajectories`` flag.
- `target_name_data` *str, optional* - Target output name for the data. Defaults to None (which
    assumes that the input filename with the suffix "_pose" should be used).
- `target_name_average` *str, optional* - Target output name for the average-pose image. Defaults
    to None (input filename with the suffix "_pose_average.png").
- `target_name_trajectories` *str, optional* - Target output name for the trajectories image.
    Defaults to None (input filename with the suffix "_pose_trajectories.png").
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically
    increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgVideo` - An MgVideo pointing to the output video. The average-pose and trajectories images
    (when rendered) are attached as ``.average_pose`` and ``.trajectories`` (MgImage), and the
    collected keypoints are available on the parent object as ``self.pose_average`` /
    ``self.pose_trajectories``.

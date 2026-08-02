# Pose Visualize

> Auto-generated documentation for [musicalgestures._pose_visualize](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_visualize.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Pose Visualize
    - [pose_center](#pose_center)
    - [pose_distance](#pose_distance)
    - [render_average_pose](#render_average_pose)
    - [render_pose_center](#render_pose_center)
    - [render_pose_distance](#render_pose_distance)
    - [render_pose_waterfall](#render_pose_waterfall)
    - [render_segment_circular](#render_segment_circular)
    - [render_trajectories](#render_trajectories)

## pose_center

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_visualize.py#L565)

```python
def pose_center(data, names):
```

Centre pose data on its global centroid (a 2D port of the MoCap Toolbox ``mccenter``).

Computes a single offset per coordinate dimension—the mean of the per-marker temporal means
(missing detections ignored)—and subtracts it from every marker so the overall
spatiotemporal centroid sits at the origin (0, 0).

#### Arguments

- `data` *list* - Collected pose rows ``[time_ms, x0, y0, ...]`` (normalised coords).
- `names` *list* - Marker names (length n_points).

#### Returns

- `tuple` - ``(centered, offset, times)`` where ``centered`` is a (T, n, 2) array of centred
    normalised coordinates (NaN for missing), ``offset`` is the (x, y) centroid that was
    removed, and ``times`` is the per-frame time in seconds.

## pose_distance

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_visualize.py#L638)

```python
def pose_distance(data, names, width, height):
```

Per-marker cumulative distance travelled (a 2D port of the MoCap Toolbox ``mccumdist``).

Sums the frame-to-frame Euclidean displacement of each marker (in pixels) and accumulates it
over time. Gaps from missing detections contribute no distance.

#### Arguments

- `data` *list* - Collected pose rows ``[time_ms, x0, y0, ...]`` (normalised coords).
- `names` *list* - Marker names (length n_points).
width, height (int): Frame size in pixels (to scale the normalised coordinates).

#### Returns

- `tuple` - ``(cumulative, total, average, times)`` where ``cumulative`` is a (T-1, n) array of
    cumulative distance per marker (pixels), ``total`` is the per-marker total (n,),
    ``average`` is the mean total across markers, and ``times`` are the per-frame times (s).

## render_average_pose

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_visualize.py#L92)

```python
def render_average_pose(
    data,
    names,
    connections,
    width,
    height,
    fps,
    avg_frame,
    target_name,
    overwrite=True,
    fmin=0.2,
    fmax=8.0,
    style='both',
):
```

Render the average pose of the whole video, with per-marker quantity of motion
(colour + label) and dominant frequency (label) annotated.

``style`` matches the video: 'both' draws markers + skeleton lines, 'markers' draws
only the markers, 'skeleton' draws only the connecting joint lines. Per-marker labels
are shown in all cases.

Returns an MgImage, or None if there are too few frames.

## render_pose_center

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_visualize.py#L591)

```python
def render_pose_center(
    data,
    names,
    width,
    height,
    target_name,
    overwrite=True,
    cmap='hsv',
    dpi=200,
):
```

Centre the pose data (see :func:[pose_center](#pose_center)) and plot the centred marker trajectories.

Returns an MgFigure whose ``.data`` holds the centred coordinates and the removed offset, or
None if there are too few frames.

## render_pose_distance

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_visualize.py#L666)

```python
def render_pose_distance(
    data,
    names,
    width,
    height,
    fps,
    target_name,
    overwrite=True,
    cmap='hsv',
    dpi=200,
):
```

Plot per-marker cumulative distance travelled over time plus a ranked total per marker.

Returns an MgFigure (``.data`` holds the totals, average, and cumulative curves) and saves a
CSV of the per-marker totals; None if there are too few frames.

## render_pose_waterfall

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_visualize.py#L258)

```python
def render_pose_waterfall(
    data,
    names,
    width,
    height,
    fps,
    target_name,
    overwrite=True,
    style='trajectories',
    connections=None,
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
):
```

Render a 3D spatio-temporal waterfall of the pose, cascading along the time (depth) axis, a
 pose-based counterpart to ``silhouette_waterfall()``.

``style`` selects what is drawn:

* ``'trajectories'`` (default): each marker's path is a continuous line through (x, time, y).
* ``'markers'``: the markers themselves are scattered at ``n_samples`` time slices.
* ``'skeleton'``: the skeleton joint lines are drawn at ``n_samples`` time slices.
* ``'both'``: markers + skeleton at each time slice.

#### Arguments

- `data` *list* - Collected pose rows ``[time_ms, x0, y0, x1, y1, ...]`` (normalised coords).
- `names` *list* - Marker names (length n_points).
width, height (int): Frame size in pixels (used to scale normalised coords).
- `fps` *float* - Frames per second (for the time axis).
- `target_name` *str* - Output PNG path.
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.
- `style` *str, optional* - ``'trajectories'`` (default), ``'markers'``, ``'skeleton'``, or
    ``'both'``.
- `connections` *list, optional* - Skeleton connection pairs (indices); required for the
    ``'skeleton'``/``'both'`` styles.
- `n_samples` *int, optional* - Number of time slices for the marker/skeleton styles.
    Defaults to 40.
- `markers` *list, optional* - Subset of marker names or indices to draw. Defaults to all.
- `color_by` *str, optional* - ``'marker'`` (one colour per marker) or ``'time'`` (colour by
    time). Defaults to None ("auto"): 'marker' for trajectories, 'time' for the slice styles.
- `cmap` *str, optional* - Matplotlib colormap. Defaults to 'hsv'.
- `dpi` *int, optional* - Output DPI. Defaults to 200.
- `elev` *float, optional* - 3D elevation angle. Defaults to 20.
- `azim` *float, optional* - 3D azimuth angle. Defaults to -60.
- `lw` *float, optional* - Line width. Defaults to 1.0.
- `axes` *bool, optional* - Draw the axes and tick labels. Set to False for a clean render
    with all axes and text removed. Defaults to True.
- `crop` *bool, optional* - Tighten the spatial axis limits to the actual marker extent and
    trim the surrounding whitespace, so the figure shows mostly the data. Defaults to False.

#### Returns

- `MgFigure` - the 3D waterfall figure, or None if there are too few frames.

## render_segment_circular

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_visualize.py#L450)

```python
def render_segment_circular(
    data,
    names,
    connections,
    width,
    height,
    fps,
    target_name,
    overwrite=True,
    segments=None,
    n_bins=36,
    cmap='viridis',
    dpi=200,
    ncols=6,
):
```

Circular (polar) motion plots and statistics for every body segment.

A *segment* is the bone between two connected joints. For each segment this computes the
per-frame orientation angle and draws a polar rose histogram of the angle distribution with
the mean-direction resultant vector overlaid, annotated with the segment's circular statistics.
A CSV of the per-segment statistics is saved alongside the image.

#### Arguments

- `data` *list* - Collected pose rows ``[time_ms, x0, y0, ...]`` (normalised coords).
- `names` *list* - Marker names (length n_points).
- `connections` *list* - Segment connection pairs (joint-index tuples).
width, height (int): Frame size in pixels (to scale coordinates).
- `fps` *float* - Frames per second (for angular speed).
- `target_name` *str* - Output PNG path.
- `overwrite` *bool, optional* - Overwrite or auto-increment the filename. Defaults to True.
- `segments` *list, optional* - Subset of connections (as ``(a, b)`` index tuples) to plot.
    Defaults to all connections.
- `n_bins` *int, optional* - Number of angular bins in each rose. Defaults to 36 (10° bins).
- `cmap` *str, optional* - Matplotlib colormap for the bars (by bin count). Defaults to 'viridis'.
- `dpi` *int, optional* - Output DPI. Defaults to 200.
- `ncols` *int, optional* - Number of columns in the subplot grid. Defaults to 6.

#### Returns

- `MgFigure` - the grid of circular plots (per-segment stats in ``.data``), or None if there
are too few frames.

## render_trajectories

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose_visualize.py#L193)

```python
def render_trajectories(
    data,
    names,
    width,
    height,
    fps,
    target_name,
    overwrite=True,
    background='black',
    labels=False,
):
```

Render every marker's spatial trajectory across the whole video.

``background`` chooses the PNG background: ``'black'`` (default), ``'white'``, or
``'transparent'`` (so the PNG can be overlaid on the original video later). Set
``labels=True`` to annotate each trajectory with its marker name (off by default).
Returns an MgImage, or None if there are too few frames.

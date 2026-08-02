# Flow

> Auto-generated documentation for [musicalgestures._flow](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_flow.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Flow
    - [Flow](#flow)
        - [Flow().dense](#flowdense)
        - [Flow().get_acceleration](#flowget_acceleration)
        - [Flow().get_velocity](#flowget_velocity)
        - [Flow().sparse](#flowsparse)
        - [Flow().velocity_meters_per_second](#flowvelocity_meters_per_second)

## Flow

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_flow.py#L14)

```python
class Flow():
    def __init__(parent, filename, color, has_audio):
```

Class container for the sparse and dense optical flow processes.

### Flow().dense

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_flow.py#L34)

```python
def dense(
    filename: str | None = None,
    pyr_scale: float = 0.5,
    levels: int = 3,
    winsize: int = 15,
    iterations: int = 3,
    poly_n: int = 5,
    poly_sigma: float = 1.2,
    flags: int = 0,
    velocity: bool = False,
    distance: int | None = None,
    timestep: int = 1,
    move_step: int = 1,
    angle_of_view: int = 0,
    scaledown: int = 1,
    skip_empty: bool = False,
    use_gpu: bool = False,
    convert: bool = True,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'musicalgestures.MgVideo':
```

Renders a dense optical flow video of the input video file using `cv2.calcOpticalFlowFarneback()`. The description of the matching parameters are taken from the cv2 documentation.

#### Arguments

- `filename` *str, optional* - Path to the input video file. If None the video file of the MgVideo is used. Defaults to None.
- `pyr_scale` *float, optional* - Specifies the image scale (<1) to build pyramids for each image. `pyr_scale=0.5` means a classical pyramid, where each next layer is twice smaller than the previous one. Defaults to 0.5.
- `levels` *int, optional* - The number of pyramid layers including the initial image. `levels=1` means that no extra layers are created and only the original images are used. Defaults to 3.
- `winsize` *int, optional* - The averaging window size. Larger values increase the algorithm robustness to image noise and give more chances for fast motion detection, but yield more blurred motion field. Defaults to 15.
- `iterations` *int, optional* - The number of iterations the algorithm does at each pyramid level. Defaults to 3.
- `poly_n` *int, optional* - The size of the pixel neighborhood used to find polynomial expansion in each pixel. Larger values mean that the image will be approximated with smoother surfaces, yielding more robust algorithm and more blurred motion field, typically poly_n =5 or 7. Defaults to 5.
- `poly_sigma` *float, optional* - The standard deviation of the Gaussian that is used to smooth derivatives used as a basis for the polynomial expansion. For `poly_n=5`, you can set `poly_sigma=1.1`, for `poly_n=7`, a good value would be `poly_sigma=1.5`. Defaults to 1.2.
- `flags` *int, optional* - Operation flags that can be a combination of the following: - **OPTFLOW_USE_INITIAL_FLOW** uses the input flow as an initial flow approximation. - **OPTFLOW_FARNEBACK_GAUSSIAN** uses the Gaussian \f$\texttt{winsize}\times\texttt{winsize}\f$ filter instead of a box filter of the same size for optical flow estimation. Usually, this option gives z more accurate flow than with a box filter, at the cost of lower speed. Normally, `winsize` for a Gaussian window should be set to a larger value to achieve the same level of robustness. Defaults to 0.
- `velocity` *bool, optional* - Whether to compute optical flow velocity or not. Defaults to False.
- `distance` *int, optional* - Distance in meters to image (focal length) for returning flow in meters per second. Defaults to None.
- `timestep` *int, optional* - Time step in seconds for returning flow in meters per second. Defaults to 1.
- `move_step` *int, optional* - step size in pixels for sampling the flow image. Defaults to 1.
- `angle_of_view` *int, optional* - angle of view of camera, for reporting flow in meters per second. Defaults to 0.
- `scaledown` *int, optional* - factor to scaledown frame size of the video. Defaults to 1.
- `skip_empty` *bool, optional* - If True, repeats previous frame in the output when encounters an empty frame. Defaults to False.
- `use_gpu` *bool, optional* - Whether to attempt GPU (CUDA) acceleration using `cv2.cuda.FarnebackOpticalFlow`. When `True`, falls back to CPU automatically if CUDA is unavailable or the required OpenCV CUDA modules are not installed. When `False`, CPU processing is used unconditionally. Defaults to False.
- `target_name` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_flow_dense" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgVideo` - A new MgVideo pointing to the output video file.

### Flow().get_acceleration

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_flow.py#L281)

```python
def get_acceleration(velocity: list, fps: int):
```

### Flow().get_velocity

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_flow.py#L291)

```python
def get_velocity(
    flow: np.ndarray,
    sum_flow_pixels: float,
    flow_shape: int,
    distance_meters: int | float | None,
    timestep_seconds: int | float,
    move_step: int,
    angle_of_view: int | float,
):
```

### Flow().sparse

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_flow.py#L306)

```python
def sparse(
    filename: str | None = None,
    corner_max_corners: int = 100,
    corner_quality_level: float = 0.3,
    corner_min_distance: int = 7,
    corner_block_size: int = 7,
    of_win_size: tuple = (15, 15),
    of_max_level: int = 2,
    of_criteria: tuple = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
    use_gpu: bool = False,
    convert: bool = True,
    target_name: str | None = None,
    overwrite: bool = True,
) -> 'musicalgestures.MgVideo':
```

Renders a sparse optical flow video of the input video file using `cv2.calcOpticalFlowPyrLK()`. `cv2.goodFeaturesToTrack()` is used for the corner estimation. The description of the matching parameters are taken from the cv2 documentation.

#### Arguments

- `filename` *str, optional* - Path to the input video file. If None, the video file of the MgVideo is used. Defaults to None.
- `corner_max_corners` *int, optional* - Maximum number of corners to return. If there are more corners than are found, the strongest of them is returned. `maxCorners <= 0` implies that no limit on the maximum is set and all detected corners are returned. Defaults to 100.
- `corner_quality_level` *float, optional* - Parameter characterising the minimal accepted quality of image corners. The parameter value is multiplied by the best corner quality measure, which is the minimal eigenvalue (see cornerMinEigenVal in cv2 docs) or the Harris function response (see cornerHarris in cv2 docs). The corners with the quality measure less than the product are rejected. For example, if the best corner has the quality measure = 1500, and the qualityLevel=0.01, then all the corners with the quality measure less than 15 are rejected. Defaults to 0.3.
- `corner_min_distance` *int, optional* - Minimum possible Euclidean distance between the returned corners. Defaults to 7.
- `corner_block_size` *int, optional* - Size of an average block for computing a derivative covariation matrix over each pixel neighborhood. See cornerEigenValsAndVecs in cv2 docs. Defaults to 7.
- `of_win_size` *tuple, optional* - Size of the search window at each pyramid level. Defaults to (15, 15).
- `of_max_level` *int, optional* - 0-based maximal pyramid level number. If set to 0, pyramids are not used (single level), if set to 1, two levels are used, and so on. If pyramids are passed to input then the algorithm will use as many levels as pyramids have but no more than `maxLevel`. Defaults to 2.
- `of_criteria` *tuple, optional* - Specifies the termination criteria of the iterative search algorithm (after the specified maximum number of iterations criteria.maxCount or when the search window moves by less than criteria.epsilon). Defaults to (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03).
- `use_gpu` *bool, optional* - Whether to attempt GPU (CUDA) acceleration using `cv2.cuda.SparsePyrLKOpticalFlow`. When `True`, falls back to CPU automatically if CUDA is unavailable or the required OpenCV CUDA modules are not installed. When `False`, CPU processing is used unconditionally. Defaults to False.
- `target_name` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_flow_sparse" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.

#### Returns

- `MgVideo` - A new MgVideo pointing to the output video file.

### Flow().velocity_meters_per_second

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_flow.py#L299)

```python
def velocity_meters_per_second(
    velocity_pixels_per_second: float,
    flow_shape: int,
    distance_meters: int | float,
    angle_of_view: int | float,
):
```

# 360video

> Auto-generated documentation for [musicalgestures._360video](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / 360video
    - [Mg360Video](#mg360video)
        - [Mg360Video().convert_projection](#mg360videoconvert_projection)
        - [Mg360Video.from_dual_fisheye](#mg360videofrom_dual_fisheye)
        - [Mg360Video().view](#mg360videoview)
    - [Projection](#projection)
    - [calibrate_dual_fisheye_fov](#calibrate_dual_fisheye_fov)
    - [detect_projection](#detect_projection)
    - [make_seam_mask](#make_seam_mask)
    - [stitch_dual_fisheye](#stitch_dual_fisheye)

## Mg360Video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L293)

```python
class Mg360Video(MgVideo):
    def __init__(
        filename: str,
        projection: Union[str, Projection] = None,
        camera: str = None,
        **kwargs,
    ):
```

Class for 360 videos.

#### See also

- [MgVideo](_video.md#mgvideo)
- [Projection](#projection)

### Mg360Video().convert_projection

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L395)

```python
def convert_projection(
    target_projection: Union[Projection, str],
    options: Dict[str, str] = None,
    print_cmd: bool = False,
    test: bool = False,
):
```

Convert the video to a different projection.

#### Arguments

- `target_projection` *Projection* - Target projection.
options (Dict[str, str], optional): Options for the conversion. Defaults to None.
- `print_cmd` *bool, optional* - Print the ffmpeg command. Defaults to False.

#### See also

- [Projection](#projection)

### Mg360Video.from_dual_fisheye

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L383)

```python
@classmethod
def from_dual_fisheye(
    front_file,
    back_file,
    camera: str = None,
    **stitch_kwargs,
):
```

Stitch a dual-fisheye pair (e.g. the `_00_`/`_10_` .insv files of an
Insta360 camera) into an equirectangular video and open it as an
Mg360Video. See [stitch_dual_fisheye](#stitch_dual_fisheye) for the stitching options
(`fov=None` auto-calibrates the lens FOV on a probe frame).

### Mg360Video().view

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L339)

```python
def view(
    yaw: float = 0,
    pitch: float = 0,
    roll: float = 0,
    h_fov: float = 90,
    v_fov: float = 60,
    width: int = None,
    height: int = None,
    target_name: str = None,
    print_cmd: bool = False,
) -> 'MgVideo':
```

Extract a flat (rectilinear/perspective) view in a chosen direction
from the 360 video, via ffmpeg's v360 filter, and return it as a
regular MgVideo — a non-destructive alternative to
[Mg360Video().convert_projection](#mg360videoconvert_projection) for running any standard MGT analysis
(motiongrams, optical flow, pose...) on one direction of the scene.

#### Arguments

- `yaw` *float* - Viewing direction, degrees, as ffmpeg v360's `yaw`
    rotation (0 = the equirectangular center). Note: v360's sign
    convention is not the ambisonic azimuth convention used by
    `anglegram`; verify direction on your own footage.
- `pitch` *float* - Vertical viewing direction in degrees.
- `roll` *float* - In-plane rotation in degrees.
h_fov, v_fov (float): Horizontal/vertical field of view of the
    extracted view in degrees. Defaults to 90 x 60.
width, height (int): Output size. Defaults to source height *
    (h_fov/90) by source height * (v_fov/90), rounded to even.
- `target_name` *str* - Output path. Defaults to
    `<input>_view_y<yaw>_p<pitch>.mp4`.
- `print_cmd` *bool* - Print the ffmpeg command. Defaults to False.

#### Returns

- `MgVideo` - The extracted view.

## Projection

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L14)

```python
class Projection(Enum):
```

same as https://ffmpeg.org/ffmpeg-filters.html#v360.

## calibrate_dual_fisheye_fov

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L132)

```python
def calibrate_dual_fisheye_fov(
    front_file,
    back_file,
    time_s: float = 1.0,
    candidates=None,
    print_result: bool = False,
):
```

Estimate the effective lens field of view of a dual-fisheye pair
(e.g. the two .insv files of an Insta360 camera) by projecting one frame
of each lens to equirectangular at candidate FOVs and measuring the
photometric mismatch in the seam bands at longitude ±90°.

#### Arguments

- `front_file` *str* - Video of the front lens.
- `back_file` *str* - Video of the back lens.
- `time_s` *float* - Timestamp of the probe frame.
- `candidates` *list* - FOVs (degrees) to try. Default 185–205.

#### Returns

- `float` - The FOV with the smallest seam mismatch.

## detect_projection

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L256)

```python
def detect_projection(filename: str):
```

Guess the projection of a 360 video file. First looks for spherical
metadata (the `Spherical Mapping` side data that GoPro MAX exports,
Insta360 Studio, Garmin VIRB, and the RICOH THETA app all write to
their equirectangular files), then falls back to the frame geometry:
an exact 2:1 aspect ratio is taken as equirectangular, 1:1 as dual
fisheye stacked in one square frame is NOT assumed (too ambiguous).

#### Arguments

- `filename` *str* - Path to the video file.

#### Returns

- `Projection` - The detected projection, or None if undetectable.

## make_seam_mask

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L107)

```python
def make_seam_mask(width: int, height: int, feather_deg: float = 8.0):
```

Column mask for feather-blending two hemispheres on an equirectangular
canvas: 0 where the front lens (yaw 0) should be used, 255 for the back
lens (yaw 180), with a linear ramp of ±feather_deg around the seams at
longitude ±90°.

#### Arguments

- `width` *int* - Mask width in pixels (full 360° canvas).
- `height` *int* - Mask height in pixels.
- `feather_deg` *float* - Half-width of the blend ramp in degrees.

#### Returns

- `np.ndarray` - uint8 mask of shape (height, width).

## stitch_dual_fisheye

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L189)

```python
def stitch_dual_fisheye(
    front_file,
    back_file,
    target_name: str = None,
    fov: float = None,
    feather_deg: float = 8.0,
    width: int = None,
    height: int = None,
    crf: int = 21,
    preset: str = 'fast',
    print_cmd: bool = False,
):
```

Stitch a dual-fisheye pair (two single-lens files, e.g. Insta360
`_00_`/`_10_` .insv) into one equirectangular video with a feathered
seam blend. Each lens is projected to equirectangular separately
(back lens at yaw 180) and the two are merged with a soft column mask,
which avoids the hard seams of a plain `v360=dfisheye` conversion.
Audio is taken from the front-lens file when present.
Also fits Garmin VIRB 360 RAW-mode recordings, which store the two
~200-degree hemispheres as separate files.

#### Arguments

- `front_file` *str* - Video of the front lens.
- `back_file` *str* - Video of the back lens.
- `target_name` *str* - Output path. Defaults to `<front>_equirect.mp4`.
- `fov` *float* - Lens FOV in degrees. None runs
    [calibrate_dual_fisheye_fov](#calibrate_dual_fisheye_fov) on a probe frame first.
- `feather_deg` *float* - Half-width of the seam blend in degrees.
width, height (int): Output size. Defaults to lens height × 2 by
    lens height (2:1 equirectangular).
crf (int), preset (str): x264 rate control.

#### Returns

- `str` - Path of the stitched video.

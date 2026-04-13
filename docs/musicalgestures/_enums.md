# Enums

> Auto-generated documentation for [musicalgestures._enums](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_enums.py) module.

Enumeration types for MGT-python parameter validation.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Enums
    - [BlurType](#blurtype)
    - [CropMode](#cropmode)
    - [DataFormat](#dataformat)
    - [FilterType](#filtertype)
    - [PoseDevice](#posedevice)
    - [PoseModel](#posemodel)

Using StrEnum so that enum members compare equal to their string values,
maintaining full backward compatibility with code that passes plain strings.
All enumerations support case-insensitive construction:

```python
>>> BlurType("average") == BlurType.AVERAGE
True
>>> BlurType("AVERAGE") == BlurType.AVERAGE
True

## BlurType

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_enums.py#L56)

```python
class BlurType(_MgEnum):
```

Spatial blur applied before the frame-difference computation.

Attributes
----------
NONE:
    No blurring is applied.
AVERAGE:
    A 10 × 10 pixel box-blur is applied.

## CropMode

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_enums.py#L70)

```python
class CropMode(_MgEnum):
```

Video cropping strategy.

Attributes
----------
NONE:
    No cropping.
MANUAL:
    Opens an interactive window; the user draws a rectangle.
AUTO:
    Automatically detects the area of significant motion.

## DataFormat

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_enums.py#L121)

```python
class DataFormat(_MgEnum):
```

Output data file format.

Attributes
----------
CSV:
    Comma-separated values.
TSV:
    Tab-separated values.
TXT:
    Plain text (space-separated).
JSON:
    JSON with metadata.
HDF5:
    HDF5 / Zarr for large feature matrices.

## FilterType

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_enums.py#L39)

```python
class FilterType(_MgEnum):
```

Pixel-value filter applied to the frame-difference stream.

Attributes
----------
REGULAR:
    Values below *thresh* are set to 0; values above are kept as-is.
BINARY:
    Values below *thresh* → 0; values above *thresh* → 255.
BLOB:
    Individual pixels are removed with an erosion filter.

## PoseDevice

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_enums.py#L107)

```python
class PoseDevice(_MgEnum):
```

Compute backend for pose estimation inference.

Attributes
----------
CPU:
    Run on CPU.
GPU:
    Run on GPU (CUDA / OpenCL).

## PoseModel

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_enums.py#L87)

```python
class PoseModel(_MgEnum):
```

Pose estimation skeleton model.

Attributes
----------
BODY_25:
    OpenPose BODY_25 dataset (25 keypoints).
COCO:
    COCO dataset (18 keypoints).
MPI:
    MPII dataset (15 keypoints).
MEDIAPIPE:
    Google MediaPipe Pose (33 landmarks).

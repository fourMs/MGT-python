# Pose

> Auto-generated documentation for [musicalgestures._pose](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Pose
    - [download_model](#download_model)
    - [pose](#pose)

## download_model

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L370)

```python
def download_model(modeltype):
```

Helper function to automatically download model (.caffemodel) files.

## pose

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L30)

```python
def pose(
    self,
    model='body_25',
    device='gpu',
    threshold=0.1,
    downsampling_factor=2,
    save_data=True,
    data_format='csv',
    save_video=True,
    target_name_video=None,
    target_name_data=None,
    overwrite=False,
):
```

Renders a video with the pose estimation (aka. "keypoint detection" or "skeleton tracking") overlaid on it.
Outputs the predictions in a text file containing the normalized x and y coordinates of each keypoint
(default format is csv).

Supports two backends:

- **MediaPipe** (`model='mediapipe'`): Uses Google's MediaPipe Pose which detects 33 landmarks entirely on CPU. Requires the optional `mediapipe` package (`pip install musicalgestures[pose]`). The model file (~8–28 MB) is auto-downloaded on first use and cached in `musicalgestures/models/`.
- **OpenPose** (`model='body_25'`, `'coco'`, or `'mpi'`): Uses Caffe-based OpenPose models. Model weights (~200 MB) are downloaded on first use.

#### Arguments

- `model` *str, optional* - Pose model to use. `'mediapipe'` uses MediaPipe Pose (33 landmarks, model auto-downloaded on first use). `'body_25'` loads the OpenPose BODY_25 model (25 keypoints), `'mpi'` loads the MPII model (15 keypoints), `'coco'` loads the COCO model (18 keypoints). Defaults to 'body_25'.
- `device` *str, optional* - Sets the backend to use for the neural network ('cpu' or 'gpu'). Ignored when `model='mediapipe'` (MediaPipe always runs on CPU). Defaults to 'gpu'.
- `threshold` *float, optional* - The normalized confidence threshold that decides whether we keep or discard a predicted point. Discarded points get substituted with (0, 0) in the output data. Defaults to 0.1.
- `downsampling_factor` *int, optional* - Decides how much we downsample the video before we pass it to the neural network. Ignored when `model='mediapipe'`. Defaults to 2.
- `save_data` *bool, optional* - Whether we save the predicted pose data to a file. Defaults to True.
- `data_format` *str, optional* - Specifies format of pose-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
- `save_video` *bool, optional* - Whether we save the video with the estimated pose overlaid on it. Defaults to True.
- `target_name_video` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_pose" should be used).
- `target_name_data` *str, optional* - Target output name for the data. Defaults to None (which assumes that the input filename with the suffix "_pose" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgVideo` - An MgVideo pointing to the output video.

# Pose

> Auto-generated documentation for [_pose](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Pose
    - [download_model](#download_model)
    - [pose](#pose)

## download_model

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L317)

```python
def download_model(modeltype):
```

Helper function to automatically download model (.caffemodel) files.

## pose

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py#L13)

```python
def pose(
    self,
    model='mpi',
    device='cpu',
    threshold=0.1,
    downsampling_factor=4,
    save_data=True,
    data_format='csv',
    save_video=True,
    target_name_video=None,
    target_name_data=None,
    overwrite=False,
):
```

Renders a video with the pose estimation (aka. "keypoint detection" or "skeleton tracking") overlaid on it.
Outputs the predictions in a text file containing the normalized x and y coordinates of each keypoints
(default format is csv). Uses models from the [openpose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) project.

#### Arguments

- `model` *str, optional* - 'mpi' loads the model trained on the Multi-Person Dataset (MPII), 'coco' loads one trained on the COCO dataset. The MPII model outputs 15 points, while the COCO model produces 18 points. Defaults to 'mpi'.
- `device` *str, optional* - Sets the backend to use for the neural network ('cpu' or 'gpu'). Defaults to 'cpu'.
- `threshold` *float, optional* - The normalized confidence threshold that decides whether we keep or discard a predicted point. Discarded points get substituted with (0, 0) in the output data. Defaults to 0.1.
- `downsampling_factor` *int, optional* - Decides how much we downsample the video before we pass it to the neural network. For example `downsampling_factor=4` means that the input to the network is one-fourth the resolution of the source video. Heaviver downsampling reduces rendering time but produces lower quality pose estimation. Defaults to 4.
- `save_data` *bool, optional* - Whether we save the predicted pose data to a file. Defaults to True.
- `data_format` *str or list, optional* - Specifies format of pose-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
- `save_video` *bool, optional* - Whether we save the video with the estimated pose overlaid on it. Defaults to True.
- `target_name_video` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_pose" should be used).
- `target_name_data` *str, optional* - Target output name for the data. Defaults to None (which assumes that the input filename with the suffix "_pose" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgObject` - An MgObject pointing to the output video.

# Pose

> Auto-generated documentation for [\_pose](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pose.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Pose
  - [pose](#pose)

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
):
```

Renders a video with the pose estimation (aka. "keypoint detection" or "skeleton tracking") overlaid on it. Outputs the predictions in a text file (default format is csv). Uses models from the [openpose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) project.

#### Arguments

- `model` _str, optional_ - 'mpi' loads the model trained on the Multi-Person Dataset (MPII), 'coco' loads one trained on the COCO dataset. The MPII model outputs 15 points, while the COCO model produces 18 points. MPII is faster. Defaults to 'mpi'.
- `device` _str, optional_ - Sets the backend to use for the neural network ('cpu' or 'gpu'). Defaults to 'cpu'.
- `threshold` _float, optional_ - The normalized confidence threshold that decides whether we keep or discard a predicted point. Discarded points get substituted with (0, 0) in the output data. Defaults to 0.1.
- `downsampling_factor` _int, optional_ - Decides how much we downsample the video before we pass it to the neural network. For example `downsampling_factor=4` means that the input to the network is one-fourth the resolution of the source video. Heavier downsampling reduces rendering time but produces lower quality pose estimation. Defaults to 4.
- `save_data` _bool, optional_ - Whether we save the predicted pose data to a file. Defaults to True.
- `data_format` _str or list, optional_ - Specifies format of pose-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
- `save_video` _bool, optional_ - Whether we save the video with the estimated pose overlaid on it. Defaults to True.

#### Outputs

- `filename`\_pose.avi - The source video with pose overlay.
- `filename`\_pose.`data_format` - A text file containing the normalized x and y coordinates of each keypoints (such as head, left shoulder, right shoulder, etc) for each frame in the source video with timecodes in milliseconds. Available formats: csv, tsv, txt.

#### Returns

- `MgObject` - An MgObject pointing to the output '\_pose' video.

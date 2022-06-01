# Motionvideo

> Auto-generated documentation for [_motionvideo](https://github.com/fourMs/MGT-python/blob/master/_motionvideo.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Motionvideo
    - [mg_motion](#mg_motion)
    - [mg_motiondata](#mg_motiondata)
    - [mg_motiongrams](#mg_motiongrams)
    - [mg_motionplots](#mg_motionplots)
    - [mg_motionvideo](#mg_motionvideo)
    - [plot_motion_metrics](#plot_motion_metrics)
    - [save_txt](#save_txt)

## mg_motion

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_motionvideo.py#L267)

```python
def mg_motion(
    self,
    filtertype='Regular',
    thresh=0.05,
    blur='None',
    kernel_size=5,
    inverted_motionvideo=False,
    inverted_motiongram=False,
    unit='seconds',
    equalize_motiongram=True,
    save_plot=True,
    plot_title=None,
    save_data=True,
    data_format='csv',
    save_motiongrams=True,
    save_video=True,
    target_name_video=None,
    target_name_plot=None,
    target_name_data=None,
    target_name_mgx=None,
    target_name_mgy=None,
    overwrite=False,
):
```

Finds the difference in pixel value from one frame to the next in an input video, and saves the frames into a new video.
Describes the motion in the recording. Outputs: a motion video, a plot describing the centroid of motion and the
quantity of motion, horizontal and vertical motiongrams, and a text file containing the quantity of motion and the
centroid of motion for each frame with timecodes in milliseconds.

#### Arguments

- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `kernel_size` *int, optional* - Size of structuring element. Defaults to 5.
- `inverted_motionvideo` *bool, optional* - If True, inverts colors of the motion video. Defaults to False.
- `inverted_motiongram` *bool, optional* - If True, inverts colors of the motiongrams. Defaults to False.
- `unit` *str, optional* - Unit in QoM plot. Accepted values are 'seconds' or 'samples'. Defaults to 'seconds'.
- `equalize_motiongram` *bool, optional* - If True, converts the motiongrams to hsv-color space and flattens the value channel (v). Defaults to True.
- `save_plot` *bool, optional* - If True, outputs motion-plot. Defaults to True.
- `plot_title` *str, optional* - Optionally add title to the plot. Defaults to None, which uses the file name as a title.
- `save_data` *bool, optional* - If True, outputs motion-data. Defaults to True.
- `data_format` *str/list, optional* - Specifies format of motion-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
- `save_motiongrams` *bool, optional* - If True, outputs motiongrams. Defaults to True.
- `save_video` *bool, optional* - If True, outputs the motion video. Defaults to True.
- `target_name_video` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
- `target_name_plot` *str, optional* - Target output name for the plot. Defaults to None (which assumes that the input filename with the suffix "_motion_com_qom" should be used).
- `target_name_data` *str, optional* - Target output name for the data. Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
- `target_name_mgx` *str, optional* - Target output name for the vertical motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgx" should be used).
- `target_name_mgy` *str, optional* - Target output name for the horizontal motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgy" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgVideo` - A new MgVideo pointing to the output video file. If `save_video=False`, it returns an MgVideo pointing to the input video file.

## mg_motiondata

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_motionvideo.py#L87)

```python
def mg_motiondata(
    self,
    filtertype='Regular',
    thresh=0.05,
    blur='None',
    kernel_size=5,
    data_format='csv',
    target_name=None,
    overwrite=False,
):
```

Shortcut for [mg_motion](#mg_motion) to only render motion data.

#### Arguments

- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `kernel_size` *int, optional* - Size of structuring element. Defaults to 5.
- `data_format` *str/list, optional* - Specifies format of motion-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
- `target_name` *str, optional* - Target output name for the data. Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `str/list` - The path(s) to the rendered data file(s).

## mg_motiongrams

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_motionvideo.py#L14)

```python
def mg_motiongrams(
    self,
    filtertype='Regular',
    thresh=0.05,
    blur='None',
    use_median=False,
    kernel_size=5,
    inverted_motiongram=False,
    equalize_motiongram=True,
    target_name_mgx=None,
    target_name_mgy=None,
    overwrite=False,
):
```

Shortcut for [mg_motion](#mg_motion) to only render motiongrams.

#### Arguments

- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `use_median` *bool, optional* - If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
- `kernel_size` *int, optional* - Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
- `inverted_motiongram` *bool, optional* - If True, inverts colors of the motiongrams. Defaults to False.
- `equalize_motiongram` *bool, optional* - If True, converts the motiongrams to hsv-color space and flattens the value channel (v). Defaults to True.
- `target_name_mgx` *str, optional* - Target output name for the vertical motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgx" should be used).
- `target_name_mgy` *str, optional* - Target output name for the horizontal motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgy" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgList` - An MgList pointing to the output motiongram images (as MgImages).

## mg_motionplots

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_motionvideo.py#L156)

```python
def mg_motionplots(
    self,
    filtertype='Regular',
    thresh=0.05,
    blur='None',
    kernel_size=5,
    unit='seconds',
    title=None,
    target_name=None,
    overwrite=False,
):
```

Shortcut for [mg_motion](#mg_motion) to only render motion plots.

#### Arguments

- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `kernel_size` *int, optional* - Size of structuring element. Defaults to 5.
- `unit` *str, optional* - Unit in QoM plot. Accepted values are 'seconds' or 'samples'. Defaults to 'seconds'.
- `title` *str, optional* - Optionally add title to the plot. Defaults to None, which uses the file name as a title.
- `target_name` *str, optional* - Target output name for the plot. Defaults to None (which assumes that the input filename with the suffix "_motion_com_qom" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgImage` - An MgImage pointing to the exported image (png) of the motion plots.

## mg_motionvideo

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_motionvideo.py#L207)

```python
def mg_motionvideo(
    self,
    filtertype='Regular',
    thresh=0.05,
    blur='None',
    use_median=False,
    kernel_size=5,
    inverted_motionvideo=False,
    target_name=None,
    overwrite=False,
):
```

Shortcut to only render the motion video. Uses musicalgestures._utils.motionvideo_ffmpeg. Note that this does not apply median filter by default. If you need it use `use_median=True`.

#### Arguments

- `filtertype` *str, optional* - 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
- `thresh` *float, optional* - Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
- `blur` *str, optional* - 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
- `use_median` *bool, optional* - If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
- `kernel_size` *int, optional* - Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
- `inverted_motionvideo` *bool, optional* - If True, inverts colors of the motion video. Defaults to False.
- `target_name` *str, optional* - Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

#### Returns

- `MgVideo` - A new MgVideo pointing to the output '_motion' video file.

## plot_motion_metrics

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_motionvideo.py#L541)

```python
def plot_motion_metrics(
    of,
    fps,
    com,
    qom,
    width,
    height,
    unit,
    title,
    target_name_plot,
    overwrite,
):
```

Helper function to plot the centroid and quantity of motion using matplotlib.

## save_txt

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_motionvideo.py#L582)

```python
def save_txt(
    of,
    time,
    com,
    qom,
    width,
    height,
    data_format,
    target_name_data,
    overwrite,
):
```

Helper function to export motion data as textfile(s).

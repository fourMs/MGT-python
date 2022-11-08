# Musicalgestures

> Auto-generated documentation for [musicalgestures](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/__init__.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / Musicalgestures
    - [Examples](#examples)
    - [MgVideo](#mgvideo)
        - [MgVideo().get_video](#mgvideoget_video)
        - [MgVideo().info](#mgvideoinfo)
        - [MgVideo().test_input](#mgvideotest_input)
    - Modules
        - [Audio](_audio.md#audio)
        - [Average](_average.md#average)
        - [Blurfaces](_blurfaces.md#blurfaces)
        - [CenterFace](_centerface.md#centerface)
        - [Cropping Window](_cropping_window.md#cropping-window)
        - [Cropvideo](_cropvideo.md#cropvideo)
        - [Directograms](_directograms.md#directograms)
        - [Filter](_filter.md#filter)
        - [Flow](_flow.md#flow)
        - [Grid](_grid.md#grid)
        - [History](_history.md#history)
        - [Impacts](_impacts.md#impacts)
        - [Input Test](_input_test.md#input-test)
        - [MgList](_mglist.md#mglist)
        - [Motionanalysis](_motionanalysis.md#motionanalysis)
        - [Motionvideo](_motionvideo.md#motionvideo)
        - [Motionvideo Mp Render](_motionvideo_mp_render.md#motionvideo-mp-render)
        - [Motionvideo Mp Run](_motionvideo_mp_run.md#motionvideo-mp-run)
        - [Pose](_pose.md#pose)
        - [Show](_show.md#show)
        - [Show Window](_show_window.md#show-window)
        - [Ssm](_ssm.md#ssm)
        - [Utils](_utils.md#utils)
        - [Videoadjust](_videoadjust.md#videoadjust)
        - [Videograms](_videograms.md#videograms)
        - [Videoreader](_videoreader.md#videoreader)
        - [Warp](_warp.md#warp)
        - [Examples](examples/index.md#examples)

## Examples

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/__init__.py#L148)

```python
class Examples():
    def __init__():
```

## MgVideo

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/__init__.py#L9)

```python
class MgVideo():
    def __init__(
        filename,
        filtertype='Regular',
        thresh=0.05,
        starttime=0,
        endtime=0,
        blur='None',
        skip=0,
        frames=0,
        rotate=0,
        color=True,
        contrast=0,
        brightness=0,
        crop='None',
        keep_all=False,
        returned_by_process=False,
    ):
```

This is the class for working with video files in the Musical Gestures Toolbox.
There is a set of preprocessing tools you can use when you load a video, such as:
- trimming: to extract a section of the video,
- skipping: to shrink the video by skipping N frames after keeping one,
- rotating: to rotate the video by N degrees,
- applying brightness and contrast
- cropping: to crop the video either automatically (by assessing the area of motion) or manually with a pop-up user interface,
- converting to grayscale

These preprocesses will apply upon creating the MgVideo. Further processes are available as class methods.

### MgVideo().get_video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/__init__.py#L125)

```python
def get_video():
```

Creates a video attribute to the Musical Gestures object with the given correct settings.

### MgVideo().info

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/__init__.py#L113)

```python
def info(type='video'):
```

Retrieves the information related to video, audio and format.

### MgVideo().test_input

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/__init__.py#L109)

```python
def test_input():
```

Gives feedback to user if initialization from input went wrong.

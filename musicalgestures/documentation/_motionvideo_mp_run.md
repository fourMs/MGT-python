# Motionvideo Mp Run

> Auto-generated documentation for [_motionvideo_mp_run](https://github.com/fourMs/MGT-python/blob/main/_motionvideo_mp_run.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Motionvideo Mp Run
    - [TrackMultiProgress](#trackmultiprogress)
        - [TrackMultiProgress().progress](#trackmultiprogressprogress)
        - [TrackMultiProgress().reset](#trackmultiprogressreset)
    - [concat_videos](#concat_videos)
    - [mg_motion_mp](#mg_motion_mp)
    - [run_socket_server](#run_socket_server)

## TrackMultiProgress

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_motionvideo_mp_run.py#L328)

```python
class TrackMultiProgress():
    def __init__(numprocesses):
```

### TrackMultiProgress().progress

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_motionvideo_mp_run.py#L333)

```python
def progress(node, iteration):
```

### TrackMultiProgress().reset

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_motionvideo_mp_run.py#L337)

```python
def reset():
```

## concat_videos

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_motionvideo_mp_run.py#L341)

```python
def concat_videos(
    list_of_videos,
    target_name=None,
    overwrite=False,
    pb_prefix='Concatenating videos:',
    stream=True,
):
```

## mg_motion_mp

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_motionvideo_mp_run.py#L16)

```python
def mg_motion_mp(
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
    num_processes=-1,
):
```

## run_socket_server

[[find in source code]](https://github.com/fourMs/MGT-python/blob/main/_motionvideo_mp_run.py#L295)

```python
def run_socket_server(host, port, pb, numprocesses):
```

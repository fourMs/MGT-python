# Show

> Auto-generated documentation for [musicalgestures._show](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_show.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Show
    - [mg_show](#mg_show)
    - [show_in_new_process](#show_in_new_process)

## mg_show

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_show.py#L14)

```python
def mg_show(
    self,
    filename=None,
    key=None,
    mode='windowed',
    window_width=640,
    window_height=480,
    window_title=None,
    **ipython_kwargs,
):
```

General method to show an image or video file either in a window, or inline in a jupyter notebook.

#### Arguments

- `filename` *str, optional* - If given, [mg_show](#mg_show) will show this file instead of what it inherits from its parent object. Defaults to None.
- `key` *str, optional* - If given, [mg_show](#mg_show) will search for file names corresponding to certain processes you have previously rendered on your source. It is meant to be a shortcut, so you don't have to remember the exact name (and path) of eg. a motion video corresponding to your source in your MgVideo, but you rather just use `MgVideo('path/to/vid.mp4').show(key='motion')`. Accepted values are 'mgx', 'mgy', 'vgx', 'vgy', 'blend', 'plot', 'motion', 'history', 'motionhistory', 'sparse', and 'dense'. Defaults to None.
- `mode` *str, optional* - Whether to show things in a separate window or inline in the jupyter notebook. Accepted values are 'windowed' and 'notebook'. Defaults to 'windowed'.
- `window_width` *int, optional* - The width of the window. Defaults to 640.
- `window_height` *int, optional* - The height of the window. Defaults to 480.
- `window_title` *str, optional* - The title of the window. If None, the title of the window will be the file name. Defaults to None.
- `ipython_kwargs` *dict, optional* - Additional arguments for IPython.display.Image or IPython.display.Video. Defaults to None.

## show_in_new_process

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_show.py#L301)

```python
def show_in_new_process(cmd):
```

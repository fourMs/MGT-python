# 360video

> Auto-generated documentation for [musicalgestures._360video](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / 360video
    - [Mg360Video](#mg360video)
        - [Mg360Video().convert_projection](#mg360videoconvert_projection)
    - [Projection](#projection)

## Mg360Video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L91)

```python
class Mg360Video(MgVideo):
    def __init__(
        filename: str,
        projection: Union[str, Projection],
        camera: str = None,
        **kwargs,
    ):
```

Class for 360 videos.

#### See also

- [MgVideo](_video.md#mgvideo)
- [Projection](#projection)

### Mg360Video().convert_projection

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L123)

```python
def convert_projection(
    target_projection: Union[Projection, str],
    options: Dict[str, str] = None,
    print_cmd: bool = False,
):
```

Convert the video to a different projection.

#### Arguments

- `target_projection` *Projection* - Target projection.
options (Dict[str, str], optional): Options for the conversion. Defaults to None.
- `print_cmd` *bool, optional* - Print the ffmpeg command. Defaults to False.

#### See also

- [Projection](#projection)

## Projection

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_360video.py#L9)

```python
class Projection(Enum):
```

same as https://ffmpeg.org/ffmpeg-filters.html#v360.

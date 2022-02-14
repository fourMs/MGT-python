# Warping

> Auto-generated documentation for [_warping](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_warping.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / Warping
    - [beats_diff](#beats_diff)
    - [mg_warping_audiovisual_beats](#mg_warping_audiovisual_beats)

## beats_diff

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_warping.py#L14)

```python
@jit(nopython=True)
def beats_diff(beats, media):
```

## mg_warping_audiovisual_beats

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_warping.py#L21)

```python
def mg_warping_audiovisual_beats(
    self,
    audio_file,
    speed=(0.5, 2),
    data=None,
    filtertype='Adaptative',
    thresh=0.05,
    kernel_size=5,
    target_name=None,
    overwrite=False,
):
```

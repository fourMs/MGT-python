# Motionvectors

> Auto-generated documentation for [musicalgestures._motionvectors](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motionvectors.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Motionvectors
    - [mg_motionvectors](#mg_motionvectors)

## mg_motionvectors

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_motionvectors.py#L6)

```python
def mg_motionvectors(
    self,
    target_name=None,
    overwrite=True,
) -> 'musicalgestures.MgVideo':
```

Renders a video visualising the motion vectors encoded in the input video.

Inter-frame codecs (MPEG-1/2/4, H.264, H.265, …) store motion vectors that describe
how macroblocks move between frames. This method uses FFmpeg's ``codecview`` filter
(with ``-flags2 +export_mvs``) to draw those vectors as arrows on top of the video,
giving a quick, decoder-level view of motion without any re-computation.

NB: Only codecs that actually carry motion vectors will show arrows. Intra-only
formats (e.g. MJPEG, common in ``.avi`` files) have none. Convert to an inter-frame
codec first (e.g. via ``show(mode='notebook')`` which makes an mp4, or any mp4/h264
source) to see motion vectors.

#### Arguments

- `target_name` *str, optional* - Target output name for the video. Defaults to None
    (which uses the input filename with the suffix "_motionvectors").
- `overwrite` *bool, optional* - Whether to allow overwriting existing files or to
    automatically increment the target filename. Defaults to True.

#### Returns

- `MgVideo` - An MgVideo pointing to the rendered motion-vector video.

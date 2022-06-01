# CenterFace

> Auto-generated documentation for [_centerface](https://github.com/fourMs/MGT-python/blob/master/_centerface.py) module.

- [Musicalgestures](README.md#musicalgestures-index) / [Modules](MODULES.md#musicalgestures-modules) / CenterFace
    - [CenterFace](#centerface)
        - [CenterFace().decode](#centerfacedecode)
        - [CenterFace().inference_opencv](#centerfaceinference_opencv)
        - [CenterFace().nms](#centerfacenms)
        - [CenterFace().postprocess](#centerfacepostprocess)
        - [CenterFace().transform](#centerfacetransform)

## CenterFace

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_centerface.py#L7)

```python
class CenterFace(object):
    def __init__(landmarks=True):
```

### CenterFace().decode

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_centerface.py#L53)

```python
def decode(heatmap, scale, offset, landmark, size, threshold=0.1):
```

### CenterFace().inference_opencv

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_centerface.py#L21)

```python
def inference_opencv(img, threshold):
```

### CenterFace().nms

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_centerface.py#L87)

```python
def nms(boxes, scores, nms_thresh):
```

### CenterFace().postprocess

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_centerface.py#L35)

```python
def postprocess(heatmap, lms, offset, scale, threshold):
```

### CenterFace().transform

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/_centerface.py#L30)

```python
def transform(h, w):
```

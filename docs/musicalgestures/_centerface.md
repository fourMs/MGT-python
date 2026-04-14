# CenterFace

> Auto-generated documentation for [musicalgestures._centerface](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_centerface.py) module.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / CenterFace
    - [CenterFace](#centerface)
        - [CenterFace().decode](#centerfacedecode)
        - [CenterFace().inference_opencv](#centerfaceinference_opencv)
        - [CenterFace().nms](#centerfacenms)
        - [CenterFace().postprocess](#centerfacepostprocess)
        - [CenterFace().transform](#centerfacetransform)

## CenterFace

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_centerface.py#L8)

```python
class CenterFace(object):
    def __init__(landmarks=True, use_gpu=False):
```

### CenterFace().decode

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_centerface.py#L62)

```python
def decode(heatmap, scale, offset, landmark, size, threshold=0.1):
```

### CenterFace().inference_opencv

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_centerface.py#L30)

```python
def inference_opencv(img, threshold):
```

### CenterFace().nms

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_centerface.py#L96)

```python
def nms(boxes, scores, nms_thresh):
```

### CenterFace().postprocess

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_centerface.py#L44)

```python
def postprocess(heatmap, lms, offset, scale, threshold):
```

### CenterFace().transform

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_centerface.py#L39)

```python
def transform(h, w):
```

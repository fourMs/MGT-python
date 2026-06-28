# Pipeline

> Auto-generated documentation for [musicalgestures._pipeline](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pipeline.py) module.

Scikit-learn–style processing pipeline for MGT-python.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Pipeline
    - [MgPipeline](#mgpipeline)
        - [MgPipeline().add_step](#mgpipelineadd_step)
        - [MgPipeline().describe](#mgpipelinedescribe)
        - [MgPipeline().fit](#mgpipelinefit)
        - [MgPipeline().fit_transform](#mgpipelinefit_transform)
        - [MgPipeline().transform](#mgpipelinetransform)
    - [MgStep](#mgstep)
        - [MgStep().\_\_call\_\_](#mgstep__call__)

class `MgPipeline` chains a sequence of named steps where each step is a
callable (function) or a duck-typed transformer with a ``transform`` method.
This enables reproducible, serialisable analysis graphs.

The design is intentionally minimal and compatible with
class `sklearn.pipeline.Pipeline` conventions (``fit`` / ``transform`` /
``fit_transform``).

Examples
--------

```python
>>> from musicalgestures._pipeline import MgPipeline, MgStep
>>> import numpy as np
>>>
>>> def scale(x):
...     return x / x.max()
>>>
>>> pipe = MgPipeline([
...     MgStep("scale", scale),
... ])
>>> result = pipe.transform(np.array([1.0, 2.0, 4.0]))
>>> result
array([0.25, 0.5 , 1.  ])

## MgPipeline

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pipeline.py#L63)

```python
class MgPipeline():
    def __init__(
        steps: list[MgStep | tuple[str, Callable]] | None = None,
    ) -> None:
```

Chain multiple processing steps into a reproducible pipeline.

Parameters
----------
steps:
    Ordered list of :class:[MgStep](#mgstep) objects (or 2-tuples
    ``(name, callable)``).

Examples
--------
Build a pipeline that normalises a 1-D feature array:

```python
>>> import numpy as np
>>> from musicalgestures._pipeline import MgPipeline, MgStep
>>> def subtract_mean(x): return x - x.mean()
>>> def divide_std(x): return x / (x.std() + 1e-8)
>>> pipe = MgPipeline([("center", subtract_mean), ("scale", divide_std)])
>>> arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
>>> pipe.transform(arr)
array([-1.41421356, -0.70710678,  0.        ,  0.70710678,  1.41421356])

### MgPipeline().add_step

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pipeline.py#L99)

```python
def add_step(step: MgStep | tuple[str, Callable]) -> 'MgPipeline':
```

Append a step to the pipeline.

Parameters
----------
step:
    An :class:[MgStep](#mgstep) instance, or a 2-tuple ``(name, callable)``.

Returns
-------
MgPipeline
    Returns *self* to allow chaining.

### MgPipeline().describe

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pipeline.py#L208)

```python
def describe() -> list[dict[str, Any]]:
```

Return a human-readable description of all steps.

Returns
-------
list[dict[str, Any]]

### MgPipeline().fit

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pipeline.py#L159)

```python
def fit(X: Any, y: Any = None) -> 'MgPipeline':
```

Fit each step in sequence (for sklearn compatibility).

For steps that have a ``fit`` method, it is called.  Otherwise
the step is treated as stateless and nothing happens.

Parameters
----------
X:
    Training data.
y:
    Target labels (passed through to sklearn-compatible steps).

Returns
-------
MgPipeline
    Returns *self*.

### MgPipeline().fit_transform

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pipeline.py#L187)

```python
def fit_transform(X: Any, y: Any = None) -> Any:
```

Fit then transform.

Parameters
----------
X:
    Input data.
y:
    Target labels.

Returns
-------
Any

### MgPipeline().transform

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pipeline.py#L138)

```python
def transform(X: Any) -> Any:
```

Apply all steps sequentially to *X*.

Parameters
----------
X:
    Input data.  The type is determined by the first step.

Returns
-------
Any
    The output of the last step.

## MgStep

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pipeline.py#L38)

```python
dataclass
class MgStep():
```

A single named step in an :class:[MgPipeline](#mgpipeline).

Parameters
----------
name:
    Human-readable step name (used in repr and serialisation).
func:
    A callable that accepts one positional argument (the data from the
    previous step) and optional ``**kwargs``, and returns transformed data.
    Alternatively, an object with a ``transform(X)`` method.
kwargs:
    Keyword arguments forwarded to *func* on every call.

### MgStep().\_\_call\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_pipeline.py#L56)

```python
def __call__(X: Any) -> Any:
```

Apply this step to *X*.

# Features

> Auto-generated documentation for [musicalgestures._features](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py) module.

MgFeatures – a named time-series container for motion and audio descriptors.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Features
    - [MgFeatures](#mgfeatures)
        - [MgFeatures().\_\_array\_\_](#mgfeatures__array__)
        - [MgFeatures().\_\_getitem\_\_](#mgfeatures__getitem__)
        - [MgFeatures().\_\_iter\_\_](#mgfeatures__iter__)
        - [MgFeatures().\_\_len\_\_](#mgfeatures__len__)
        - [MgFeatures().feature_names](#mgfeaturesfeature_names)
        - [MgFeatures.from_dataframe](#mgfeaturesfrom_dataframe)
        - [MgFeatures.from_json](#mgfeaturesfrom_json)
        - [MgFeatures().n_features](#mgfeaturesn_features)
        - [MgFeatures().n_samples](#mgfeaturesn_samples)
        - [MgFeatures().shape](#mgfeaturesshape)
        - [MgFeatures().times](#mgfeaturestimes)
        - [MgFeatures().to_dataframe](#mgfeaturesto_dataframe)
        - [MgFeatures().to_json](#mgfeaturesto_json)
        - [MgFeatures().to_numpy](#mgfeaturesto_numpy)

class `MgFeatures` holds one or more named feature arrays (e.g. quantity of
motion, centroid of motion, optical flow statistics, spectral features) together
with shared metadata (sampling rate, time axis, source filename).  It is the
primary data structure for feeding MGT-python analysis results into machine-
learning pipelines.

The design follows conventions established by librosa (feature arrays + sample
rate) and MNE-Python (named channels + metadata dict).

Examples
--------

```python
>>> import numpy as np
>>> from musicalgestures._features import MgFeatures
>>> t = np.linspace(0, 10, 100)
>>> feat = MgFeatures(
...     data={"qom": np.random.rand(100), "com_x": np.random.rand(100)},
...     times=t,
...     sr=25.0,
...     source="dancer.avi",
... )
>>> feat.shape
(2, 100)
>>> arr = feat.to_numpy()   # shape (2, 100)
>>> df  = feat.to_dataframe()  # pandas DataFrame, columns = feature names

## MgFeatures

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L41)

```python
class MgFeatures():
    def __init__(
        data: dict[str, np.ndarray],
        times: np.ndarray | None = None,
        sr: float = 1.0,
        source: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
```

Named time-series container for motion and audio descriptors.

Parameters
----------
data:
    A mapping of ``{feature_name: 1-D numpy array}``.  All arrays must
    have the same length (number of time samples).
times:
    1-D array of time stamps in seconds corresponding to each sample.
    If *None*, integer sample indices are used.
sr:
    Sampling rate of the feature time series in Hz (frames per second
    for video-derived features, Hz for audio-derived features).
source:
    Path to the source file that the features were derived from.
metadata:
    Optional free-form dictionary of additional metadata (parameters
    used, processing chain description, etc.).

Attributes
----------
feature_names : list[str]
    Names of the features stored in this container.
n_features : int
    Number of named feature channels.
n_samples : int
    Number of time samples per channel.
shape : tuple[int, int]
    ``(n_features, n_samples)``

### MgFeatures().\_\_array\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L151)

```python
def __array__(dtype=None, copy=None) -> np.ndarray:
```

Return a 2-D array of shape ``(n_features, n_samples)``.

### MgFeatures().\_\_getitem\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L140)

```python
def __getitem__(key: str) -> np.ndarray:
```

Return a single feature array by name.

### MgFeatures().\_\_iter\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L147)

```python
def __iter__():
```

Iterate over feature names.

### MgFeatures().\_\_len\_\_

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L136)

```python
def __len__() -> int:
```

Return the number of feature channels.

### MgFeatures().feature_names

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L107)

```python
@property
def feature_names() -> list[str]:
```

Names of the feature channels.

### MgFeatures.from_dataframe

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L237)

```python
@classmethod
def from_dataframe(
    df: pd.DataFrame,
    sr: float = 1.0,
    source: str | Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> 'MgFeatures':
```

Create an :class:[MgFeatures](#mgfeatures) from a class `pandas.DataFrame`.

Parameters
----------
df:
    DataFrame whose columns are feature names and whose index is
    the time axis in seconds.
sr:
    Sampling rate in Hz.
source:
    Optional source file path.
metadata:
    Optional metadata dictionary.

Returns
-------
MgFeatures

### MgFeatures.from_json

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L213)

```python
@classmethod
def from_json(path: str | Path) -> 'MgFeatures':
```

Load an :class:[MgFeatures](#mgfeatures) instance from a JSON file.

Parameters
----------
path:
    Path to the JSON file previously created by :meth:[MgFeatures().to_json](#mgfeaturesto_json).

Returns
-------
MgFeatures

### MgFeatures().n_features

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L112)

```python
@property
def n_features() -> int:
```

Number of feature channels.

### MgFeatures().n_samples

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L117)

```python
@property
def n_samples() -> int:
```

Number of time samples per channel.

### MgFeatures().shape

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L122)

```python
@property
def shape() -> tuple[int, int]:
```

``(n_features, n_samples)``.

### MgFeatures().times

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L127)

```python
@property
def times() -> np.ndarray:
```

Time axis in seconds.

### MgFeatures().to_dataframe

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L171)

```python
def to_dataframe() -> pd.DataFrame:
```

Return features as a class `pandas.DataFrame`.

Returns
-------
pd.DataFrame
    Columns are feature names, index is the time axis in seconds.

### MgFeatures().to_json

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L183)

```python
def to_json(path: str | Path | None = None) -> str:
```

Serialise to JSON (with metadata).

Parameters
----------
path:
    Optional file path to write the JSON to.  If *None*, returns
    the JSON string.

Returns
-------
str
    JSON-encoded string representation.

### MgFeatures().to_numpy

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_features.py#L160)

```python
def to_numpy() -> np.ndarray:
```

Return all features as a 2-D NumPy array ``(n_features, n_samples)``.

Returns
-------
np.ndarray
    Shape ``(n_features, n_samples)``.  Row order matches
    :attr:[MgFeatures().feature_names](#mgfeaturesfeature_names).

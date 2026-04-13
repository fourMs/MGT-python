# Dataset

> Auto-generated documentation for [musicalgestures._dataset](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py) module.

Dataset and Corpus classes for managing collections of media files.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Dataset
    - [MediaItem](#mediaitem)
        - [MediaItem().is_audio](#mediaitemis_audio)
        - [MediaItem().is_video](#mediaitemis_video)
        - [MediaItem().stem](#mediaitemstem)
        - [MediaItem().suffix](#mediaitemsuffix)
    - [MgCorpus](#mgcorpus)
    - [MgDataset](#mgdataset)
        - [MgDataset().filter](#mgdatasetfilter)
        - [MgDataset().filter_by_label](#mgdatasetfilter_by_label)
        - [MgDataset.from_directory](#mgdatasetfrom_directory)
        - [MgDataset.from_json](#mgdatasetfrom_json)
        - [MgDataset().labels](#mgdatasetlabels)
        - [MgDataset().to_json](#mgdatasetto_json)
        - [MgDataset().train_test_split](#mgdatasettrain_test_split)
        - [MgDataset().unique_labels](#mgdatasetunique_labels)

class `MgDataset` manages a collection of media files (video or audio) and
provides batch processing, train/test splitting, and metadata management,
following conventions from :mod:`librosa` and MNE-Python.

class `MgCorpus` is a higher-level convenience wrapper that scans a directory
tree for media files and builds an class `MgDataset` automatically.

Examples
--------

```python
>>> from musicalgestures._dataset import MgDataset
>>> ds = MgDataset.from_directory("/path/to/videos", pattern="*.avi")
>>> train, test = ds.train_test_split(test_size=0.2)
>>> for item in train:
...     print(item["path"], item["label"])

## MediaItem

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L34)

```python
dataclass
class MediaItem():
```

A single item in an :class:[MgDataset](#mgdataset).

Parameters
----------
path:
    Absolute path to the media file.
label:
    Optional class label or annotation string.
metadata:
    Optional free-form metadata dict.

### MediaItem().is_audio

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L68)

```python
@property
def is_audio() -> bool:
```

True if this is a recognised audio file.

### MediaItem().is_video

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L63)

```python
@property
def is_video() -> bool:
```

True if this is a recognised video file.

### MediaItem().stem

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L53)

```python
@property
def stem() -> str:
```

Filename without extension.

### MediaItem().suffix

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L58)

```python
@property
def suffix() -> str:
```

File extension (lower-case).

## MgCorpus

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L346)

```python
class MgCorpus(MgDataset):
    def __init__(
        root: str | Path,
        pattern: str = '**/*',
        label_from: str = 'parent',
    ) -> None:
```

Corpus: an :class:[MgDataset](#mgdataset) built by scanning a directory tree.

This is a convenience subclass.  Use :meth:[MgDataset.from_directory](#mgdatasetfrom_directory)
for equivalent functionality.

Parameters
----------
root:
    Root directory of the corpus.
pattern:
    Glob pattern.  Default: ``'**/*'``.
label_from:
    ``'parent'``, ``'stem'``, or ``'none'``.  Default: ``'parent'``.

Examples
--------

```python
>>> corpus = MgCorpus("/data/recordings", label_from="parent")  # doctest: +SKIP
>>> len(corpus)  # doctest: +SKIP
120
>>> train, test = corpus.train_test_split(test_size=0.2)  # doctest: +SKIP

#### See also

- [MgDataset](#mgdataset)

## MgDataset

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L77)

```python
class MgDataset():
    def __init__(
        items: list[MediaItem] | None = None,
        name: str = 'MgDataset',
    ) -> None:
```

A labelled collection of media files.

Parameters
----------
items:
    List of :class:[MediaItem](#mediaitem) objects.
name:
    Optional human-readable name for this dataset.

Examples
--------

```python
>>> from pathlib import Path
>>> from musicalgestures._dataset import MgDataset, MediaItem
>>> items = [
...     MediaItem(Path("/data/dance1.avi"), label="dance"),
...     MediaItem(Path("/data/piano1.avi"), label="piano"),
... ]
>>> ds = MgDataset(items, name="demo")
>>> len(ds)
2

### MgDataset().filter

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L243)

```python
def filter(func) -> 'MgDataset':
```

Return a new dataset containing only items for which *func(item)* is True.

Parameters
----------
func:
    Callable accepting a :class:[MediaItem](#mediaitem) and returning bool.

Returns
-------
MgDataset

### MgDataset().filter_by_label

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L257)

```python
def filter_by_label(label: str) -> 'MgDataset':
```

Return a new dataset containing only items with the given *label*.

Parameters
----------
label:
    Label string to match.

Returns
-------
MgDataset

### MgDataset.from_directory

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L128)

```python
@classmethod
def from_directory(
    directory: str | Path,
    pattern: str = '**/*',
    label_from: str = 'parent',
    recursive: bool = True,
    name: str | None = None,
) -> 'MgDataset':
```

Build a dataset by scanning a directory for media files.

Parameters
----------
directory:
    Root directory to scan.
pattern:
    Glob pattern relative to *directory*. Default: ``'**/*'``.
label_from:
    How to derive labels: ``'parent'`` uses the immediate parent
    directory name; ``'stem'`` uses the filename stem;
    ``'none'`` assigns no label.
recursive:
    If *True* (default), scan sub-directories.
name:
    Optional dataset name.

Returns
-------
MgDataset

### MgDataset.from_json

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L181)

```python
@classmethod
def from_json(path: str | Path) -> 'MgDataset':
```

Load a dataset from a JSON file saved by :meth:[MgDataset().to_json](#mgdatasetto_json).

Parameters
----------
path:
    Path to the JSON file.

Returns
-------
MgDataset

### MgDataset().labels

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L271)

```python
@property
def labels() -> list[str | None]:
```

List of all item labels (in order).

### MgDataset().to_json

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L285)

```python
def to_json(path: str | Path | None = None) -> str:
```

Serialise the dataset to JSON.

Parameters
----------
path:
    Optional file path to write.  If *None*, returns the JSON string.

Returns
-------
str

### MgDataset().train_test_split

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L209)

```python
def train_test_split(
    test_size: float = 0.2,
    shuffle: bool = True,
    seed: int | None = None,
) -> tuple['MgDataset', 'MgDataset']:
```

Split the dataset into train and test subsets.

Parameters
----------
test_size:
    Fraction of items to include in the test set. Default: 0.2.
shuffle:
    Whether to shuffle before splitting. Default: True.
seed:
    Random seed for reproducibility.

Returns
-------
train : MgDataset
test  : MgDataset

### MgDataset().unique_labels

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_dataset.py#L276)

```python
@property
def unique_labels() -> list[str]:
```

Sorted list of unique non-None labels.

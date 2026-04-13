"""Dataset and Corpus classes for managing collections of media files.

:class:`MgDataset` manages a collection of media files (video or audio) and
provides batch processing, train/test splitting, and metadata management,
following conventions from :mod:`librosa` and MNE-Python.

:class:`MgCorpus` is a higher-level convenience wrapper that scans a directory
tree for media files and builds an :class:`MgDataset` automatically.

Examples
--------
>>> from musicalgestures._dataset import MgDataset
>>> ds = MgDataset.from_directory("/path/to/videos", pattern="*.avi")
>>> train, test = ds.train_test_split(test_size=0.2)
>>> for item in train:
...     print(item["path"], item["label"])
"""
from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)

_VIDEO_EXTENSIONS = {".avi", ".mp4", ".mov", ".mkv", ".mpg", ".mpeg", ".webm"}
_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".aac", ".m4a"}


@dataclass
class MediaItem:
    """A single item in an :class:`MgDataset`.

    Parameters
    ----------
    path:
        Absolute path to the media file.
    label:
        Optional class label or annotation string.
    metadata:
        Optional free-form metadata dict.
    """
    path: Path
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.path = Path(self.path)

    @property
    def stem(self) -> str:
        """Filename without extension."""
        return self.path.stem

    @property
    def suffix(self) -> str:
        """File extension (lower-case)."""
        return self.path.suffix.lower()

    @property
    def is_video(self) -> bool:
        """True if this is a recognised video file."""
        return self.suffix in _VIDEO_EXTENSIONS

    @property
    def is_audio(self) -> bool:
        """True if this is a recognised audio file."""
        return self.suffix in _AUDIO_EXTENSIONS

    def __repr__(self) -> str:
        return f"MediaItem('{self.path.name}', label={self.label!r})"


class MgDataset:
    """A labelled collection of media files.

    Parameters
    ----------
    items:
        List of :class:`MediaItem` objects.
    name:
        Optional human-readable name for this dataset.

    Examples
    --------
    >>> from pathlib import Path
    >>> from musicalgestures._dataset import MgDataset, MediaItem
    >>> items = [
    ...     MediaItem(Path("/data/dance1.avi"), label="dance"),
    ...     MediaItem(Path("/data/piano1.avi"), label="piano"),
    ... ]
    >>> ds = MgDataset(items, name="demo")
    >>> len(ds)
    2
    """

    def __init__(
        self,
        items: list[MediaItem] | None = None,
        name: str = "MgDataset",
    ) -> None:
        self._items: list[MediaItem] = list(items) if items else []
        self.name = name

    # ------------------------------------------------------------------
    # Sequence protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, key: int | slice) -> MediaItem | list[MediaItem]:
        return self._items[key]

    def __iter__(self) -> Iterator[MediaItem]:
        return iter(self._items)

    def __contains__(self, item: MediaItem) -> bool:
        return item in self._items

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_directory(
        cls,
        directory: str | Path,
        pattern: str = "**/*",
        label_from: str = "parent",
        recursive: bool = True,
        name: str | None = None,
    ) -> "MgDataset":
        """Build a dataset by scanning a directory for media files.

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
        """
        root = Path(directory)
        if not root.is_dir():
            raise NotADirectoryError(f"Not a directory: {root}")

        all_extensions = _VIDEO_EXTENSIONS | _AUDIO_EXTENSIONS
        items: list[MediaItem] = []

        for p in sorted(root.glob(pattern)):
            if not p.is_file():
                continue
            if p.suffix.lower() not in all_extensions:
                continue
            label: str | None = None
            if label_from == "parent":
                label = p.parent.name
            elif label_from == "stem":
                label = p.stem
            items.append(MediaItem(path=p.resolve(), label=label))

        ds_name = name or root.name
        logger.info("Loaded %d media files from '%s'", len(items), root)
        return cls(items, name=ds_name)

    @classmethod
    def from_json(cls, path: str | Path) -> "MgDataset":
        """Load a dataset from a JSON file saved by :meth:`to_json`.

        Parameters
        ----------
        path:
            Path to the JSON file.

        Returns
        -------
        MgDataset
        """
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        items = [
            MediaItem(
                path=Path(item["path"]),
                label=item.get("label"),
                metadata=item.get("metadata", {}),
            )
            for item in data["items"]
        ]
        return cls(items, name=data.get("name", "MgDataset"))

    # ------------------------------------------------------------------
    # Splitting / filtering
    # ------------------------------------------------------------------

    def train_test_split(
        self,
        test_size: float = 0.2,
        shuffle: bool = True,
        seed: int | None = None,
    ) -> tuple["MgDataset", "MgDataset"]:
        """Split the dataset into train and test subsets.

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
        """
        items = list(self._items)
        if shuffle:
            rng = random.Random(seed)
            rng.shuffle(items)
        n_test = max(1, int(len(items) * test_size))
        test_items = items[:n_test]
        train_items = items[n_test:]
        return (
            MgDataset(train_items, name=f"{self.name}_train"),
            MgDataset(test_items, name=f"{self.name}_test"),
        )

    def filter(self, func) -> "MgDataset":
        """Return a new dataset containing only items for which *func(item)* is True.

        Parameters
        ----------
        func:
            Callable accepting a :class:`MediaItem` and returning bool.

        Returns
        -------
        MgDataset
        """
        return MgDataset([item for item in self._items if func(item)], name=self.name)

    def filter_by_label(self, label: str) -> "MgDataset":
        """Return a new dataset containing only items with the given *label*.

        Parameters
        ----------
        label:
            Label string to match.

        Returns
        -------
        MgDataset
        """
        return self.filter(lambda item: item.label == label)

    @property
    def labels(self) -> list[str | None]:
        """List of all item labels (in order)."""
        return [item.label for item in self._items]

    @property
    def unique_labels(self) -> list[str]:
        """Sorted list of unique non-None labels."""
        return sorted({lbl for lbl in self.labels if lbl is not None})

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def to_json(self, path: str | Path | None = None) -> str:
        """Serialise the dataset to JSON.

        Parameters
        ----------
        path:
            Optional file path to write.  If *None*, returns the JSON string.

        Returns
        -------
        str
        """
        payload = {
            "name": self.name,
            "n_items": len(self._items),
            "items": [
                {"path": str(item.path), "label": item.label, "metadata": item.metadata}
                for item in self._items
            ],
        }
        json_str = json.dumps(payload, indent=2)
        if path is not None:
            Path(path).write_text(json_str, encoding="utf-8")
            logger.info("MgDataset saved to %s", path)
        return json_str

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"MgDataset(name={self.name!r}, n_items={len(self)}, "
            f"labels={self.unique_labels})"
        )

    def _repr_html_(self) -> str:
        """Rich HTML display for Jupyter notebooks."""
        rows = "".join(
            f"<tr><td>{i}</td><td><code>{item.path.name}</code></td>"
            f"<td>{item.label or '—'}</td>"
            f"<td>{'video' if item.is_video else 'audio' if item.is_audio else '?'}</td></tr>"
            for i, item in enumerate(self._items[:20])
        )
        extra = f"<tr><td colspan='4'>… {len(self)-20} more items</td></tr>" if len(self) > 20 else ""
        return f"""
<div style="font-family:monospace; font-size:0.9em; border:1px solid #ddd;
padding:8px; border-radius:4px; display:inline-block;">
  <b>MgDataset</b> '{self.name}' — {len(self)} items, labels: {self.unique_labels}
  <table style="border-collapse:collapse; margin-top:6px;">
    <thead><tr>
      <th style="padding:2px 8px; border-bottom:1px solid #aaa;">#</th>
      <th style="padding:2px 8px; border-bottom:1px solid #aaa;">File</th>
      <th style="padding:2px 8px; border-bottom:1px solid #aaa;">Label</th>
      <th style="padding:2px 8px; border-bottom:1px solid #aaa;">Type</th>
    </tr></thead>
    <tbody>{rows}{extra}</tbody>
  </table>
</div>"""


class MgCorpus(MgDataset):
    """Corpus: an :class:`MgDataset` built by scanning a directory tree.

    This is a convenience subclass.  Use :meth:`MgDataset.from_directory`
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
    >>> corpus = MgCorpus("/data/recordings", label_from="parent")  # doctest: +SKIP
    >>> len(corpus)  # doctest: +SKIP
    120
    >>> train, test = corpus.train_test_split(test_size=0.2)  # doctest: +SKIP
    """

    def __init__(
        self,
        root: str | Path,
        pattern: str = "**/*",
        label_from: str = "parent",
    ) -> None:
        ds = MgDataset.from_directory(root, pattern=pattern, label_from=label_from)
        super().__init__(ds._items, name=Path(root).name)
        self.root = Path(root)

    def __repr__(self) -> str:
        return (
            f"MgCorpus(root='{self.root}', n_items={len(self)}, "
            f"labels={self.unique_labels})"
        )

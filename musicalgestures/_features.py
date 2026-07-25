"""MgFeatures – a named time-series container for motion and audio descriptors.

:class:`MgFeatures` holds one or more named feature arrays (e.g. quantity of
motion, centroid of motion, optical flow statistics, spectral features) together
with shared metadata (sampling rate, time axis, source filename).  It is the
primary data structure for feeding MGT-python analysis results into machine-
learning pipelines.

The design follows conventions established by librosa (feature arrays + sample
rate) and MNE-Python (named channels + metadata dict).

Examples
--------
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
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MgFeatures:
    """Named time-series container for motion and audio descriptors.

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
    """

    def __init__(
        self,
        data: dict[str, np.ndarray],
        times: np.ndarray | None = None,
        sr: float = 1.0,
        source: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not data:
            raise ValueError("'data' must contain at least one feature array.")
        lengths = {name: len(arr) for name, arr in data.items()}
        unique_lengths = set(lengths.values())
        if len(unique_lengths) != 1:
            raise ValueError(
                f"All feature arrays must have the same length.  Got: {lengths}"
            )
        self._data: dict[str, np.ndarray] = {k: np.asarray(v) for k, v in data.items()}
        n = next(iter(unique_lengths))
        if times is None:
            self._times = np.arange(n, dtype=float)
        else:
            self._times = np.asarray(times, dtype=float)
            if len(self._times) != n:
                raise ValueError(
                    f"'times' length ({len(self._times)}) must match feature length ({n})."
                )
        self.sr = float(sr)
        self.source = Path(source) if source is not None else None
        self.metadata: dict[str, Any] = dict(metadata) if metadata else {}

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def feature_names(self) -> list[str]:
        """Names of the feature channels."""
        return list(self._data.keys())

    @property
    def n_features(self) -> int:
        """Number of feature channels."""
        return len(self._data)

    @property
    def n_samples(self) -> int:
        """Number of time samples per channel."""
        return len(self._times)

    @property
    def shape(self) -> tuple[int, int]:
        """``(n_features, n_samples)``."""
        return (self.n_features, self.n_samples)

    @property
    def times(self) -> np.ndarray:
        """Time axis in seconds."""
        return self._times

    def absolute_times(self) -> np.ndarray:
        """Wall-clock time stamps (epoch seconds) for each sample.

        Requires ``metadata["start_datetime"]`` — a ``datetime`` or ISO
        string, e.g. from ``musicalgestures._timecode.media_start_datetime``.
        """
        import datetime as _dt

        start = (self.metadata or {}).get("start_datetime")
        if start is None:
            raise ValueError(
                "no metadata['start_datetime']; set it (see "
                "musicalgestures._timecode) to place features on the "
                "wall clock")
        if isinstance(start, str):
            start = _dt.datetime.fromisoformat(start)
        return start.timestamp() + np.asarray(self.times, dtype=float)

    # ------------------------------------------------------------------
    # Sequence / array protocols
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        """Return the number of feature channels."""
        return self.n_features

    def __getitem__(self, key: str) -> np.ndarray:
        """Return a single feature array by name."""
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __iter__(self):
        """Iterate over feature names."""
        return iter(self._data)

    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        """Return a 2-D array of shape ``(n_features, n_samples)``."""
        arr = np.stack(list(self._data.values()), axis=0)
        return arr if dtype is None else arr.astype(dtype)

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    def to_numpy(self) -> np.ndarray:
        """Return all features as a 2-D NumPy array ``(n_features, n_samples)``.

        Returns
        -------
        np.ndarray
            Shape ``(n_features, n_samples)``.  Row order matches
            :attr:`feature_names`.
        """
        return np.array(self)

    def to_dataframe(self) -> pd.DataFrame:
        """Return features as a :class:`pandas.DataFrame`.

        Returns
        -------
        pd.DataFrame
            Columns are feature names, index is the time axis in seconds.
        """
        df = pd.DataFrame(self._data, index=self._times)
        df.index.name = "time_s"
        return df

    def to_json(self, path: str | Path | None = None) -> str:
        """Serialise to JSON (with metadata).

        Parameters
        ----------
        path:
            Optional file path to write the JSON to.  If *None*, returns
            the JSON string.

        Returns
        -------
        str
            JSON-encoded string representation.
        """
        payload: dict[str, Any] = {
            "source": str(self.source) if self.source else None,
            "sr": self.sr,
            "n_features": self.n_features,
            "n_samples": self.n_samples,
            "feature_names": self.feature_names,
            "times": self._times.tolist(),
            "data": {k: v.tolist() for k, v in self._data.items()},
            "metadata": self.metadata,
        }
        json_str = json.dumps(payload, indent=2)
        if path is not None:
            Path(path).write_text(json_str, encoding="utf-8")
            logger.info("MgFeatures saved to %s", path)
        return json_str

    @classmethod
    def from_json(cls, path: str | Path) -> "MgFeatures":
        """Load an :class:`MgFeatures` instance from a JSON file.

        Parameters
        ----------
        path:
            Path to the JSON file previously created by :meth:`to_json`.

        Returns
        -------
        MgFeatures
        """
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        data = {k: np.array(v) for k, v in payload["data"].items()}
        times = np.array(payload["times"])
        return cls(
            data=data,
            times=times,
            sr=payload.get("sr", 1.0),
            source=payload.get("source"),
            metadata=payload.get("metadata", {}),
        )

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        sr: float = 1.0,
        source: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "MgFeatures":
        """Create an :class:`MgFeatures` from a :class:`pandas.DataFrame`.

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
        """
        data = {col: df[col].to_numpy() for col in df.columns}
        times = df.index.to_numpy(dtype=float)
        return cls(data=data, times=times, sr=sr, source=source, metadata=metadata)

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        src = f"'{self.source}'" if self.source else "None"
        return (
            f"MgFeatures(features={self.feature_names}, "
            f"n_samples={self.n_samples}, sr={self.sr}, source={src})"
        )

    def _repr_html_(self) -> str:
        """Rich HTML representation for Jupyter notebooks."""
        rows = "".join(
            f"<tr><td><code>{name}</code></td>"
            f"<td>{self._data[name].shape}</td>"
            f"<td>{self._data[name].dtype}</td>"
            f"<td>{self._data[name].min():.4g} … {self._data[name].max():.4g}</td></tr>"
            for name in self.feature_names
        )
        src = f"<code>{self.source}</code>" if self.source else "—"
        return f"""
<div style="font-family:monospace; font-size:0.9em; border:1px solid #ddd; padding:8px; border-radius:4px; display:inline-block;">
  <b>MgFeatures</b> — {self.n_features} feature(s) × {self.n_samples} samples @ {self.sr} Hz<br>
  Source: {src}
  <table style="border-collapse:collapse; margin-top:6px;">
    <thead><tr>
      <th style="text-align:left; padding:2px 8px; border-bottom:1px solid #aaa;">Feature</th>
      <th style="padding:2px 8px; border-bottom:1px solid #aaa;">Shape</th>
      <th style="padding:2px 8px; border-bottom:1px solid #aaa;">dtype</th>
      <th style="padding:2px 8px; border-bottom:1px solid #aaa;">range</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""

"""Scikit-learn–style processing pipeline for MGT-python.

:class:`MgPipeline` chains a sequence of named steps where each step is a
callable (function) or a duck-typed transformer with a ``transform`` method.
This enables reproducible, serialisable analysis graphs.

The design is intentionally minimal and compatible with
:class:`sklearn.pipeline.Pipeline` conventions (``fit`` / ``transform`` /
``fit_transform``).

Examples
--------
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
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable


logger = logging.getLogger(__name__)


@dataclass
class MgStep:
    """A single named step in an :class:`MgPipeline`.

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
    """
    name: str
    func: Callable[..., Any]
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __call__(self, X: Any) -> Any:
        """Apply this step to *X*."""
        if hasattr(self.func, "transform"):
            return self.func.transform(X, **self.kwargs)
        return self.func(X, **self.kwargs)


class MgPipeline:
    """Chain multiple processing steps into a reproducible pipeline.

    Parameters
    ----------
    steps:
        Ordered list of :class:`MgStep` objects (or 2-tuples
        ``(name, callable)``).

    Examples
    --------
    Build a pipeline that normalises a 1-D feature array:

    >>> import numpy as np
    >>> from musicalgestures._pipeline import MgPipeline, MgStep
    >>> def subtract_mean(x): return x - x.mean()
    >>> def divide_std(x): return x / (x.std() + 1e-8)
    >>> pipe = MgPipeline([("center", subtract_mean), ("scale", divide_std)])
    >>> arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> pipe.transform(arr)
    array([-1.41421356, -0.70710678,  0.        ,  0.70710678,  1.41421356])
    """

    def __init__(
        self, steps: list[MgStep | tuple[str, Callable]] | None = None
    ) -> None:
        self._steps: list[MgStep] = []
        if steps:
            for step in steps:
                self.add_step(step)
        self._fit_params: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Building the pipeline
    # ------------------------------------------------------------------

    def add_step(self, step: MgStep | tuple[str, Callable]) -> "MgPipeline":
        """Append a step to the pipeline.

        Parameters
        ----------
        step:
            An :class:`MgStep` instance, or a 2-tuple ``(name, callable)``.

        Returns
        -------
        MgPipeline
            Returns *self* to allow chaining.
        """
        if isinstance(step, MgStep):
            self._steps.append(step)
        elif isinstance(step, tuple) and len(step) == 2:
            name, func = step
            self._steps.append(MgStep(name=name, func=func))
        else:
            raise TypeError(
                f"Expected MgStep or (name, callable) tuple, got {type(step)}"
            )
        return self

    def __len__(self) -> int:
        return len(self._steps)

    def __getitem__(self, key: int | str) -> MgStep:
        if isinstance(key, int):
            return self._steps[key]
        for step in self._steps:
            if step.name == key:
                return step
        raise KeyError(f"No step named {key!r}")

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def transform(self, X: Any) -> Any:
        """Apply all steps sequentially to *X*.

        Parameters
        ----------
        X:
            Input data.  The type is determined by the first step.

        Returns
        -------
        Any
            The output of the last step.
        """
        data = X
        for step in self._steps:
            t0 = time.perf_counter()
            data = step(data)
            elapsed = time.perf_counter() - t0
            logger.debug("Step '%s' completed in %.3f s", step.name, elapsed)
        return data

    def fit(self, X: Any, y: Any = None) -> "MgPipeline":
        """Fit each step in sequence (for sklearn compatibility).

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
        """
        data = X
        for step in self._steps:
            if hasattr(step.func, "fit"):
                step.func.fit(data, y, **step.kwargs)
            if hasattr(step.func, "transform"):
                data = step.func.transform(data, **step.kwargs)
            elif callable(step.func):
                data = step.func(data, **step.kwargs)
        return self

    def fit_transform(self, X: Any, y: Any = None) -> Any:
        """Fit then transform.

        Parameters
        ----------
        X:
            Input data.
        y:
            Target labels.

        Returns
        -------
        Any
        """
        self.fit(X, y)
        return self.transform(X)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def describe(self) -> list[dict[str, Any]]:
        """Return a human-readable description of all steps.

        Returns
        -------
        list[dict[str, Any]]
        """
        return [
            {
                "index": i,
                "name": step.name,
                "func": getattr(step.func, "__name__", repr(step.func)),
                "kwargs": step.kwargs,
            }
            for i, step in enumerate(self._steps)
        ]

    def __repr__(self) -> str:
        step_strs = ", ".join(
            f"'{s.name}'" for s in self._steps
        )
        return f"MgPipeline(steps=[{step_strs}])"

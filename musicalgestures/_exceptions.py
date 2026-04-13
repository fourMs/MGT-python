"""Typed exception hierarchy for MGT-python.

All library-specific errors inherit from :class:`MgError` so that callers
can catch any toolbox error with a single ``except MgError``.
"""
from __future__ import annotations


class MgError(Exception):
    """Base class for all MGT-python exceptions."""


class MgInputError(MgError):
    """Raised when a user-supplied argument is invalid."""


class MgProcessingError(MgError):
    """Raised when a processing step fails unexpectedly."""


class MgIOError(MgError):
    """Raised for file I/O failures (missing files, permission errors, etc.)."""


class MgDependencyError(MgError):
    """Raised when an optional dependency is not installed."""

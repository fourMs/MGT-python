"""Logging configuration for MGT-python.

The library exposes a single logger named ``'musicalgestures'``.  Users can
adjust verbosity at the application level::

    import logging
    logging.getLogger('musicalgestures').setLevel(logging.DEBUG)

By default the logger has no handlers (quiet) so it does not interfere with
the host application's logging setup.  A convenience :func:`set_log_level`
helper is provided for interactive / script use.
"""
from __future__ import annotations

import logging

#: Module-level logger.  All sub-modules should use
#: ``logging.getLogger(__name__)`` which will be a child of this logger.
logger: logging.Logger = logging.getLogger("musicalgestures")

# Avoid propagating to the root logger by default; the library should be silent
# unless the user explicitly enables logging.
logger.addHandler(logging.NullHandler())


def set_log_level(level: int | str) -> None:
    """Set the verbosity of the *musicalgestures* logger.

    Parameters
    ----------
    level:
        A :mod:`logging` level constant (e.g. ``logging.DEBUG``) or a
        level name string (e.g. ``'DEBUG'``, ``'INFO'``, ``'WARNING'``).

    Examples
    --------
    >>> import musicalgestures
    >>> musicalgestures.set_log_level('DEBUG')
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    logger.setLevel(level)
    # Attach a simple StreamHandler if none exists yet so messages are visible.
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)

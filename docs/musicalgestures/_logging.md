# Logging

> Auto-generated documentation for [musicalgestures._logging](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_logging.py) module.

Logging configuration for MGT-python.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Logging
    - [set_log_level](#set_log_level)

The library exposes a single logger named ``'musicalgestures'``.  Users can
adjust verbosity at the application level

```python
import logging
logging.getLogger('musicalgestures').setLevel(logging.DEBUG)
```

By default the logger has no handlers (quiet) so it does not interfere with
the host application's logging setup.  A convenience :func:`set_log_level`
helper is provided for interactive / script use.

## set_log_level

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_logging.py#L26)

```python
def set_log_level(level: int | str) -> None:
```

Set the verbosity of the *musicalgestures* logger.

Parameters
----------
level:
    A :mod:`logging` level constant (e.g. ``logging.DEBUG``) or a
    level name string (e.g. ``'DEBUG'``, ``'INFO'``, ``'WARNING'``).

Examples
--------

```python
>>> import musicalgestures
>>> musicalgestures.set_log_level('DEBUG')

# Exceptions

> Auto-generated documentation for [musicalgestures._exceptions](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_exceptions.py) module.

Typed exception hierarchy for MGT-python.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Exceptions
    - [MgDependencyError](#mgdependencyerror)
    - [MgError](#mgerror)
    - [MgIOError](#mgioerror)
    - [MgInputError](#mginputerror)
    - [MgProcessingError](#mgprocessingerror)

All library-specific errors inherit from class `MgError` so that callers
can catch any toolbox error with a single ``except MgError``.

## MgDependencyError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_exceptions.py#L25)

```python
class MgDependencyError(MgError):
```

Raised when an optional dependency is not installed.

#### See also

- [MgError](#mgerror)

## MgError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_exceptions.py#L9)

```python
class MgError(Exception):
```

Base class for all MGT-python exceptions.

## MgIOError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_exceptions.py#L21)

```python
class MgIOError(MgError):
```

Raised for file I/O failures (missing files, permission errors, etc.).

#### See also

- [MgError](#mgerror)

## MgInputError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_exceptions.py#L13)

```python
class MgInputError(MgError):
```

Raised when a user-supplied argument is invalid.

#### See also

- [MgError](#mgerror)

## MgProcessingError

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_exceptions.py#L17)

```python
class MgProcessingError(MgError):
```

Raised when a processing step fails unexpectedly.

#### See also

- [MgError](#mgerror)

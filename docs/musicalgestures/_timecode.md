# Timecode

> Auto-generated documentation for [musicalgestures._timecode](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_timecode.py) module.

Absolute-clock helpers: parse recording start times from filenames.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Timecode
    - [filename_datetime](#filename_datetime)
    - [media_start_datetime](#media_start_datetime)

The regexes are byte-identical to ambiscape's (``ambiscape/io.py``), so a
folder of phone/recorder/360-camera files resolves to the same wall-clock
timeline in both toolboxes.

## filename_datetime

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_timecode.py#L17)

```python
def filename_datetime(path) -> dt.datetime | None:
```

Parse a ``YYYYMMDD_HHMMSS`` / ``YYMMDD_HHMMSS`` filename stamp.

## media_start_datetime

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_timecode.py#L37)

```python
def media_start_datetime(path) -> dt.datetime | None:
```

Start time of a recording: filename stamp, else file mtime.

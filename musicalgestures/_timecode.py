"""Absolute-clock helpers: parse recording start times from filenames.

The regexes are byte-identical to ambiscape's (``ambiscape/io.py``), so a
folder of phone/recorder/360-camera files resolves to the same wall-clock
timeline in both toolboxes.
"""
import datetime as dt
import os
import re
from pathlib import Path

# leading YYYYMMDD_HHMMSS or YYMMDD_HHMMSS in a filename (phone / recorder)
_TS_LONG = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})")
_TS_SHORT = re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})")


def filename_datetime(path) -> dt.datetime | None:
    """Parse a ``YYYYMMDD_HHMMSS`` / ``YYMMDD_HHMMSS`` filename stamp."""
    name = Path(path).name
    m = _TS_LONG.search(name)
    if m:
        y, mo, d, hh, mm, ss = (int(g) for g in m.groups())
        try:
            return dt.datetime(y, mo, d, hh, mm, ss)
        except ValueError:
            pass
    m = _TS_SHORT.search(name)
    if m:
        yy, mo, d, hh, mm, ss = (int(g) for g in m.groups())
        try:
            return dt.datetime(2000 + yy, mo, d, hh, mm, ss)
        except ValueError:
            pass
    return None


def media_start_datetime(path) -> dt.datetime | None:
    """Start time of a recording: filename stamp, else file mtime."""
    stamped = filename_datetime(path)
    if stamped is not None:
        return stamped
    try:
        return dt.datetime.fromtimestamp(os.path.getmtime(path))
    except OSError:
        return None

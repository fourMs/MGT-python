"""Read ELAN's exported text, which is how other people's annotations arrive.

`_annotate.from_elan` reads `.eaf`, ELAN's own project file. This reads the other thing
ELAN produces and the one collaborators actually send: File > Export > Tab-delimited
text, usually saved with a `.csv` extension and comma separators.

**The provenance line is the most important thing in the file.** An ELAN export begins
with a comment naming the media it was annotated against and that media's duration. Times
in the body are on THAT file's clock. Annotations of a cut, re-encoded or differently
trimmed copy will land silently in the wrong place if the reader takes the numbers and
throws the header away, so every span carries `source_file` and `source_duration_s` and
the caller can compare them against the recording it is about to attach them to.

This is not hypothetical. The human annotations of this project's dance corpus were made
on cut 25 fps videos running 36 to 39 per cent of our recordings' length, with a different
ratio per session --- so no single scale maps them, and a reader that hid the provenance
would have made that impossible to notice.

Three time columns are exported for every boundary: `hh:mm:ss.ms`, seconds, and PAL
timecode. Only seconds is read. The other two are derived from it, and PAL assumes 25 fps,
which is a property of the export rather than of the recording.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy

__all__ = ["read_elan_csv"]

#: ELAN appends its internal annotation id in square brackets: "Repeating from top [a492]".
#: The id is stable across exports and worth keeping; it is not part of the label.
_ID = re.compile(r"\s*\[([a-zA-Z]\d+)\]\s*$")

#: The provenance comment: "#file:///path/to.mp4 -- offset: 0, duration: 00:05:00.000 /
#: 300.000 / 300000, ms per sample: 40.0". The path is taken up to " -- offset:" rather
#: than to the first space: real media paths contain spaces, and stopping at one silently
#: records a fragment as the source file.
_HEAD = re.compile(r"#file:(?P<url>.+?)\s+--\s+offset:.*?"
                   r"duration:\s*[\d:.]+\s*/\s*(?P<secs>[\d.]+)")

_TIME_PREFIXES = ("Begin Time", "End Time", "Duration")


def _split_id(text: str) -> tuple[str, str | None]:
    """The label without ELAN's annotation id, and the id."""
    m = _ID.search(text)
    if not m:
        return text.strip(), None
    return _ID.sub("", text).strip(), m.group(1)


def read_elan_csv(path, source: str = "elan") -> Hierarchy:
    """Read an ELAN tab-delimited export into a :class:`Hierarchy`.

    Every non-time column becomes a level named after the column, which is the tier name
    ELAN wrote. Rows with an empty cell in a column contribute nothing to that level:
    an export carries one row per span on ANY tier, so blanks are the normal state and
    turning them into annotations would invent data.

    Args:
        path: The exported file.
        source (str): Recorded on each Action, so spans pooled from several sources can
            be told apart. Defaults to ``"elan"``.

    Returns:
        Hierarchy: One level per annotation column, each in time order. Every Action
        carries `source_file` and `source_duration_s` in its features, from the export's
        provenance line, plus `elan_id` where ELAN supplied one.

    Raises:
        ValueError: If no header row with a seconds column can be found.
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    rows = list(csv.reader(text.splitlines()))

    src_file, src_dur = None, None
    header_i = None
    for i, row in enumerate(rows):
        if not row:
            continue
        joined = ",".join(row)
        if src_file is None:
            m = _HEAD.search(joined)
            if m:
                src_file, src_dur = m.group("url"), float(m.group("secs"))
                continue
        if any(c.startswith("Begin Time") for c in row):
            header_i = i
            break
    if header_i is None:
        raise ValueError(f"{path}: no ELAN header row found")

    header = rows[header_i]
    try:
        begin_i = header.index("Begin Time - ss.msec")
        end_i = header.index("End Time - ss.msec")
    except ValueError as exc:
        raise ValueError(f"{path}: no seconds column in the header") from exc

    ann_cols = [(i, name) for i, name in enumerate(header)
                if name and not name.startswith(_TIME_PREFIXES)]

    common = {"source_file": src_file, "source_duration_s": src_dur}
    levels: dict[str, list[Action]] = {name: [] for _, name in ann_cols}
    for row in rows[header_i + 1:]:
        if len(row) <= end_i or not row[begin_i].strip():
            continue
        start, end = float(row[begin_i]), float(row[end_i])
        for i, name in ann_cols:
            if i >= len(row):
                continue
            raw = row[i].strip()
            if not raw:
                continue
            label, elan_id = _split_id(raw)
            features = dict(common)
            if elan_id:
                features["elan_id"] = elan_id
            levels[name].append(Action(start=start, end=end, source=source,
                                       labels={name: label}, features=features))

    for spans in levels.values():
        spans.sort(key=lambda a: a.start)
    return Hierarchy(levels=levels)

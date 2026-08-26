"""Three exports from one tree, and a reader so the export is not a dead end.

ELAN is the format the nesting actually fits, so it is the one with a reader. Praat
TextGrid flattens to interval tiers and TSV flattens further; both are conveniences for
tools that cannot read `.eaf`, and neither is expected to round-trip the hierarchy.

**The `.eaf` links the full session video at session-time offsets, not excerpt clips.**
An annotation made against a clip is on the clip's clock, and every use of it
afterwards has to remap --- correctly, in both directions, forever. Session time is the
only clock that stays comparable across levels and across the six recordings.

Round-trip beyond `from_elan` --- taking a student's corrected file back into a
`Hierarchy` complete with their own tiers --- is wanted eventually and not now. The
reader here exists so the writer can be tested, and is the seam that fuller import
attaches to.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy

__all__ = ["to_elan", "from_elan", "to_textgrid", "to_tsv"]

#: Coarse to fine. ELAN needs a parent before its child, and so does a reader.
_ORDER = ("part", "phrase", "action")


def _ordered(hierarchy: Hierarchy, levels=None) -> list[str]:
    names = [n for n in _ORDER if n in hierarchy.levels]
    extra = [n for n in hierarchy.levels if n not in _ORDER]
    chosen = names + sorted(extra)
    return [n for n in chosen if levels is None or n in levels]


def to_elan(hierarchy: Hierarchy, video, out, levels=None, nest: bool = True,
            vocabularies=None) -> Path:
    """Write an ELAN `.eaf`, one tier per level.

    Args:
        hierarchy: The levels to write. A level with no spans still gets its tier, so
            that a tier the annotator fills herself has the same name in every session
            instead of being created by hand.
        video: Path to the FULL session video. Annotations are on the session clock.
        out: Path to write.
        levels: Which levels to write, or None for all of them.
        nest (bool): Nest each level inside the previous one. True is right for a
            hierarchy --- actions inside phrases inside parts --- and wrong for layers
            that merely coincide. Speech is not inside motion, laughter is not inside
            speech, and another researcher's reference tier is not inside anything of
            ours; nesting those asserts a containment that does not exist and stops the
            annotator drawing a span where she needs one. Defaults to True so nothing
            already exported changes.
        vocabularies (dict): Level name to the list of allowed values, written as ELAN
            controlled vocabularies so the annotator picks from a dropdown. Free text
            produces `ENJOYMENT`, `enjoyment` and `Enjoyment` in one session and nothing
            groups afterwards. Defaults to None.

    Returns:
        Path: The file written.
    """
    vocabularies = dict(vocabularies or {})
    out_path: Path = Path(out)
    names = _ordered(hierarchy, levels)

    root = ET.Element("ANNOTATION_DOCUMENT", {
        "AUTHOR": "musicalgestures", "DATE": "1970-01-01T00:00:00+00:00",
        "FORMAT": "3.0", "VERSION": "3.0"})
    header = ET.SubElement(root, "HEADER",
                           {"MEDIA_FILE": "", "TIME_UNITS": "milliseconds"})
    vpath = Path(video)
    ET.SubElement(header, "MEDIA_DESCRIPTOR", {
        "MEDIA_URL": vpath.as_uri() if vpath.is_absolute() else f"file://{video}",
        "RELATIVE_MEDIA_URL": f"./{vpath.name}",
        "MIME_TYPE": "video/mp4"})

    order = ET.SubElement(root, "TIME_ORDER")
    slots, counter = {}, [0]

    def slot(t: float) -> str:
        """One time slot per distinct millisecond, as ELAN expects."""
        ms = int(round(t * 1000.0))
        if ms not in slots:
            counter[0] += 1
            sid = f"ts{counter[0]}"
            slots[ms] = sid
            ET.SubElement(order, "TIME_SLOT", {"TIME_SLOT_ID": sid,
                                               "TIME_VALUE": str(ms)})
        return slots[ms]

    #: Every boundary is registered before any tier is written, so the TIME_ORDER
    #: block is complete and in file order before anything refers into it.
    for name in names:
        for a in hierarchy.levels[name]:
            slot(a.start)
            slot(a.end)

    aid = [0]
    for i, name in enumerate(names):
        #: A ROOT TIER AND A CHILD TIER NEED DIFFERENT LINGUISTIC TYPES. ELAN requires
        #: that any tier with a PARENT_REF use a type carrying a CONSTRAINTS attribute,
        #: and refuses the file otherwise --- so exporting every tier with one
        #: unconstrained type produces a well-formed document that ELAN will not open,
        #: which is the only thing the export exists to do.
        if name in vocabularies:
            ltype = f"cv_{name}"
        elif nest and i:
            ltype = "subdivision"
        else:
            ltype = "segmentation"
        attrs = {"TIER_ID": name, "LINGUISTIC_TYPE_REF": ltype}
        if nest and i and name not in vocabularies:
            #: Nested, because the hierarchy is the point. A flat set of tiers would
            #: export the spans and lose what relates them.
            attrs["PARENT_REF"] = names[i - 1]
        tier = ET.SubElement(root, "TIER", attrs)
        for a in hierarchy.levels[name]:
            aid[0] += 1
            ann = ET.SubElement(tier, "ANNOTATION")
            al = ET.SubElement(ann, "ALIGNABLE_ANNOTATION", {
                "ANNOTATION_ID": f"a{aid[0]}",
                "TIME_SLOT_REF1": slot(a.start), "TIME_SLOT_REF2": slot(a.end)})
            value = a.labels.get(name, "")
            agreement = a.features.get("agreement")
            if agreement and agreement != "both":
                #: An uncertain boundary says so in the file as well as on the figure,
                #: so a student working only in ELAN still knows which to distrust.
                value = f"{value} [{agreement}]".strip()
            ET.SubElement(al, "ANNOTATION_VALUE").text = value

    #: An empty tier the student writes into. It exists in the exported file rather
    #: than being created by hand, so the tier name is the same in every session.
    #: An empty tier the student writes into, TIME-ALIGNABLE so they can draw their own
    #: spans inside an action --- which is what annotating gesture phases requires. It
    #: exists in the exported file rather than being created by hand, so the tier name
    #: is the same in every session.
    #: Only when nesting. In flat mode the caller declares its own tiers, empty ones
    #: included, and adding a second unexplained free-text tier beside theirs invites an
    #: annotator to put half her notes in each.
    if nest and "annotation" not in hierarchy.levels:
        ET.SubElement(root, "TIER", {"TIER_ID": "annotation",
                                     "LINGUISTIC_TYPE_REF": "subdivision",
                                     "PARENT_REF": names[-1] if names else "part"})

    ET.SubElement(root, "LINGUISTIC_TYPE", {"LINGUISTIC_TYPE_ID": "segmentation",
                                            "TIME_ALIGNABLE": "true",
                                            "GRAPHIC_REFERENCES": "false"})
    ET.SubElement(root, "LINGUISTIC_TYPE", {"LINGUISTIC_TYPE_ID": "subdivision",
                                            "TIME_ALIGNABLE": "true",
                                            "CONSTRAINTS": "Included_In",
                                            "GRAPHIC_REFERENCES": "false"})
    for name, values in vocabularies.items():
        #: TIME_ALIGNABLE stays true: she must be able to draw the span as well as pick
        #: its label, which is what annotating anything of her own requires.
        ET.SubElement(root, "LINGUISTIC_TYPE", {
            "LINGUISTIC_TYPE_ID": f"cv_{name}", "TIME_ALIGNABLE": "true",
            "GRAPHIC_REFERENCES": "false",
            "CONTROLLED_VOCABULARY_REF": f"cv_{name}_values"})

    #: The stereotype each constrained type names must itself be declared, and the
    #: element order matters: ELAN's schema puts CONSTRAINT after LINGUISTIC_TYPE.
    ET.SubElement(root, "CONSTRAINT", {
        "STEREOTYPE": "Included_In",
        "DESCRIPTION": "Time alignable annotations within the parent annotation's "
                       "time interval, gaps are allowed"})

    if vocabularies:
        #: EAF 3.0 resolves every LANG_REF against a LANGUAGE element in the document.
        #: Without this the file is well-formed XML that ELAN objects to, which is the
        #: same class of fault as an export ELAN will not open.
        ET.SubElement(root, "LANGUAGE", {
            "LANG_DEF": "http://cdb.iso.org/lg/CDB-00130975-001",
            "LANG_ID": "und", "LANG_LABEL": "undetermined (und)"})

    for name, values in vocabularies.items():
        cv = ET.SubElement(root, "CONTROLLED_VOCABULARY",
                           {"CV_ID": f"cv_{name}_values"})
        ET.SubElement(cv, "DESCRIPTION", {"LANG_REF": "und"}).text = name
        for j, value in enumerate(values):
            entry = ET.SubElement(cv, "CV_ENTRY_ML",
                                  {"CVE_ID": f"cve_{name}_{j}"})
            ET.SubElement(entry, "CVE_VALUE",
                          {"LANG_REF": "und"}).text = str(value)

    xml = minidom.parseString(ET.tostring(root)).toprettyxml(indent=" ")
    out_path.write_text(xml)
    return out_path


def from_elan(path) -> Hierarchy:
    """Read an `.eaf` back into a `Hierarchy`.

    This exists so `to_elan` can be tested against something other than its own
    output being well-formed, and is the seam a fuller importer attaches to.
    """
    root = ET.parse(str(path)).getroot()
    #: A slot without a TIME_VALUE is a malformed file. Skipping it and failing later
    #: on a missing key beats int(None) raising TypeError from inside a comprehension.
    times = {ts.get("TIME_SLOT_ID"): int(v)
             for ts in root.iter("TIME_SLOT")
             if (v := ts.get("TIME_VALUE")) is not None}
    levels: dict = {}
    for tier in root.iter("TIER"):
        name = tier.get("TIER_ID")
        spans = []
        for al in tier.iter("ALIGNABLE_ANNOTATION"):
            v = al.find("ANNOTATION_VALUE")
            label = (v.text or "").strip() if v is not None else ""
            spans.append(Action(start=times[al.get("TIME_SLOT_REF1")] / 1000.0,
                                end=times[al.get("TIME_SLOT_REF2")] / 1000.0,
                                source="elan",
                                labels={name: label} if label else {}))
        if spans:
            levels[name] = spans
    return Hierarchy(levels=levels)


def to_textgrid(hierarchy: Hierarchy, out, levels=None, xmax=None) -> Path:
    """Write a Praat TextGrid with one interval tier per level.

    Flattened: TextGrid has no nesting, so the hierarchy is exported as parallel tiers
    and the relationship between them is not carried. That is a property of the format
    and is stated rather than worked around.
    """
    out_path: Path = Path(out)
    names = _ordered(hierarchy, levels)
    spans = {n: sorted(hierarchy.levels[n], key=lambda a: a.start) for n in names}
    if xmax is None:
        xmax = max((a.end for v in spans.values() for a in v), default=0.0)

    lines = ['File type = "ooTextFile"', 'Object class = "TextGrid"', "",
             "xmin = 0", f"xmax = {xmax}", "tiers? <exists>",
             f"size = {len(names)}", "item []:"]
    for i, name in enumerate(names, start=1):
        #: Praat requires a partition with no holes, so the gaps between spans are
        #: written as empty intervals rather than omitted.
        intervals, t = [], 0.0
        for a in spans[name]:
            if a.start > t:
                intervals.append((t, a.start, ""))
            intervals.append((a.start, a.end, a.labels.get(name, "")))
            t = a.end
        if t < xmax:
            intervals.append((t, xmax, ""))

        lines += [f" item [{i}]:", '  class = "IntervalTier"',
                  f'  name = "{name}"', "  xmin = 0", f"  xmax = {xmax}",
                  f"  intervals: size = {len(intervals)}"]
        for j, (s, e, text) in enumerate(intervals, start=1):
            lines += [f"  intervals [{j}]:", f"   xmin = {s}", f"   xmax = {e}",
                      f'   text = "{text}"']
    out_path.write_text("\n".join(lines) + "\n")
    return out_path


def to_tsv(hierarchy: Hierarchy, out, levels=None) -> Path:
    """Write every span as a row, with what produced it and how sure it is.

    The flattest export, and the one that carries the most: `agreement` travels here
    even though TextGrid has nowhere to put it, so a boundary's status is not lost by
    choosing a different tool.
    """
    out_path: Path = Path(out)
    names = _ordered(hierarchy, levels)
    rows = ["\t".join(["level", "start", "end", "label", "source", "agreement",
                       "duration"])]
    for name in names:
        for a in sorted(hierarchy.levels[name], key=lambda x: x.start):
            rows.append("\t".join([
                name, f"{a.start:.3f}", f"{a.end:.3f}",
                str(a.labels.get(name, "")), a.source,
                str(a.features.get("agreement", "")), f"{a.duration:.3f}"]))
    out_path.write_text("\n".join(rows) + "\n")
    return out_path

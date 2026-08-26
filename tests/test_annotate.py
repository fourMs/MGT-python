"""Export is only worth having if the tree comes back.

A writer that produces a well-formed file nobody can read into anything is a dead end,
and 'it opened in ELAN' is not the same as 'the nesting survived'. So every writer here
is paired with an assertion about what a reader gets back.

The `.eaf` links the FULL SESSION VIDEO at session-time offsets rather than excerpt
clips. Clips would put every annotation the student makes on a different clock, and
the remapping would have to be right in every direction forever.
"""
import xml.etree.ElementTree as ET

import pytest

from musicalgestures._actions import Action
from musicalgestures._annotate import to_elan, to_textgrid, to_tsv, from_elan
from musicalgestures._hierarchy import Hierarchy


@pytest.fixture
def planted():
    actions, phrases = [], []
    for p in range(2):
        p0 = p * 100.0
        phrases.append(Action(start=p0, end=p0 + 80.0, source="phrase"))
        for a in range(3):
            a0 = p0 + a * 20.0
            actions.append(Action(start=a0, end=a0 + 10.0, source="action"))
    parts = [Action(start=0.0, end=200.0, source="part",
                    labels={"part": "improvisation"},
                    features={"agreement": "both"})]
    return Hierarchy(levels={"part": parts, "phrase": phrases, "action": actions})


def test_elan_round_trips_every_span(planted, tmp_path):
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf")
    back = from_elan(p)
    for level in ("part", "phrase", "action"):
        assert len(back.levels[level]) == len(planted.levels[level]), level
        for a, b in zip(back.levels[level], planted.levels[level]):
            assert a.start == pytest.approx(b.start, abs=0.001)
            assert a.end == pytest.approx(b.end, abs=0.001)


def test_elan_links_the_full_session_video(planted, tmp_path):
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf")
    root = ET.parse(p).getroot()
    md = root.find(".//MEDIA_DESCRIPTOR")
    assert md is not None
    assert md.get("MEDIA_URL").endswith("session.mp4")


def test_elan_nests_the_levels(planted, tmp_path):
    """Flat tiers would lose the hierarchy that is the whole point."""
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf")
    root = ET.parse(p).getroot()
    tiers = {t.get("TIER_ID"): t.get("PARENT_REF") for t in root.iter("TIER")}
    assert tiers["phrase"] == "part"
    assert tiers["action"] == "phrase"


def test_empty_annotation_tiers_are_provided(planted, tmp_path):
    """The student needs somewhere to write, and it must exist before they open it."""
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf",
                levels=("part", "phrase", "action"))
    tiers = {t.get("TIER_ID") for t in ET.parse(p).getroot().iter("TIER")}
    assert "annotation" in tiers


def test_an_uncertain_boundary_says_so_inside_the_eaf(tmp_path):
    """A student working only in ELAN must still see which cuts are guesses."""
    h = Hierarchy(levels={"part": [
        Action(start=0.0, end=10.0, source="part", labels={"part": "improvisation"},
               features={"agreement": "both"}),
        Action(start=10.0, end=20.0, source="part", labels={"part": "talk"},
               features={"agreement": "motion_only"})]})
    p = to_elan(h, video="/data/s.mp4", out=tmp_path / "s.eaf")
    values = [v.text for v in ET.parse(p).getroot().iter("ANNOTATION_VALUE")]
    assert "improvisation" in values
    assert any(v and "motion_only" in v for v in values), values


def test_textgrid_is_readable_and_keeps_the_boundaries(planted, tmp_path):
    p = to_textgrid(planted, out=tmp_path / "s.TextGrid", xmax=200.0)
    text = p.read_text()
    assert 'class = "IntervalTier"' in text
    assert "xmax = 200" in text
    assert text.count("intervals [") >= len(planted.levels["action"])


def _tier_intervals(text, name):
    """The (xmin, xmax) pairs of one tier, in file order."""
    import re
    block = text.split(f'name = "{name}"', 1)[1]
    block = block.split("item [", 1)[0]
    xs = [float(v) for v in re.findall(r"x(?:min|max) = ([\d.]+)", block)]
    #: The first pair is the tier's own extent; the rest are the intervals.
    return list(zip(xs[2::2], xs[3::2]))


def test_textgrid_tiers_tile_the_timeline_with_no_holes(planted, tmp_path):
    """Praat refuses an interval tier with a gap in it.

    Asserting that an empty label appears somewhere does NOT test this --- phrase and
    action spans carry no label either, so `text = ""` is in the file whether the gaps
    were written or not, and that assertion passed against the mutation it existed to
    catch. What must hold is that consecutive intervals meet exactly and that together
    they cover the whole recording.
    """
    p = to_textgrid(planted, out=tmp_path / "s.TextGrid", xmax=200.0)
    text = p.read_text()
    for name in ("part", "phrase", "action"):
        iv = _tier_intervals(text, name)
        assert iv, name
        assert iv[0][0] == pytest.approx(0.0), f"{name} does not start at 0"
        assert iv[-1][1] == pytest.approx(200.0), f"{name} does not reach xmax"
        for (_, end), (start, _) in zip(iv, iv[1:]):
            assert start == pytest.approx(end), f"{name} has a hole at {end}"


def test_tsv_has_one_row_per_span_plus_a_header(planted, tmp_path):
    p = to_tsv(planted, out=tmp_path / "s.tsv")
    rows = p.read_text().strip().split("\n")
    total = sum(len(v) for v in planted.levels.values())
    assert len(rows) == total + 1
    assert rows[0].split("\t")[:4] == ["level", "start", "end", "label"]


def test_tsv_carries_the_agreement_so_it_is_not_lost_outside_elan(planted, tmp_path):
    p = to_tsv(planted, out=tmp_path / "s.tsv")
    text = p.read_text()
    assert "agreement" in text.split("\n")[0]
    assert "both" in text


def test_every_child_tier_declares_a_constraint(planted, tmp_path):
    """ELAN refuses a nested tier whose linguistic type has no CONSTRAINTS.

    A file can be well-formed XML, round-trip through `from_elan` perfectly, and still
    not open in ELAN --- which is the only thing this export exists to do. So the rule
    is asserted against the schema's requirement rather than against our own reader:
    every tier with a PARENT_REF must reference a type carrying CONSTRAINTS, and every
    stereotype named must be declared in a CONSTRAINT element.

    Found by validating the real session.eaf rather than the fixtures.
    """
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf")
    root = ET.parse(p).getroot()

    types = {lt.get("LINGUISTIC_TYPE_ID"): lt for lt in root.iter("LINGUISTIC_TYPE")}
    declared = {c.get("STEREOTYPE") for c in root.iter("CONSTRAINT")}

    child_tiers = [t for t in root.iter("TIER") if t.get("PARENT_REF")]
    assert child_tiers, "no nested tiers to check"
    for t in child_tiers:
        lt = types.get(t.get("LINGUISTIC_TYPE_REF"))
        assert lt is not None, f"{t.get('TIER_ID')} references an undeclared type"
        stereotype = lt.get("CONSTRAINTS")
        assert stereotype, (
            f"tier {t.get('TIER_ID')} is nested but its type "
            f"{t.get('LINGUISTIC_TYPE_REF')} declares no CONSTRAINTS; ELAN will "
            "refuse the file")
        assert stereotype in declared, f"stereotype {stereotype} is never declared"


def test_the_students_tier_is_time_alignable(planted, tmp_path):
    """Gesture phases are spans, so the tier they go on must accept spans."""
    p = to_elan(planted, video="/data/session.mp4", out=tmp_path / "s.eaf")
    root = ET.parse(p).getroot()
    types = {lt.get("LINGUISTIC_TYPE_ID"): lt for lt in root.iter("LINGUISTIC_TYPE")}
    tier = [t for t in root.iter("TIER") if t.get("TIER_ID") == "annotation"][0]
    assert types[tier.get("LINGUISTIC_TYPE_REF")].get("TIME_ALIGNABLE") == "true"

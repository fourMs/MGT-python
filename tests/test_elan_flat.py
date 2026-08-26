"""Independent tiers and controlled vocabularies in the ELAN export.

`to_elan` nests each level inside the previous one, which is right for a hierarchy ---
actions inside phrases inside parts. It is wrong for the layers an annotator compares:
speech is not inside motion, laughter is not inside speech, and a reference tier from
another researcher is not inside anything of ours. Nesting them would assert a
containment that does not exist and would stop her drawing a span where she needs one.

Controlled vocabularies matter for the same practical reason. Free text produces
`ENJOYMENT`, `enjoyment` and `Enjoyment` in one session and nothing groups afterwards.
A vocabulary in the file gives her a dropdown.
"""
from xml.etree import ElementTree as ET

import pytest

from musicalgestures._actions import Action
from musicalgestures._annotate import to_elan
from musicalgestures._hierarchy import Hierarchy


@pytest.fixture
def h():
    return Hierarchy(levels={
        "motion": [Action(start=0.0, end=1.0, source="m", labels={"motion": "x"})],
        "speech": [Action(start=0.5, end=2.0, source="v", labels={"speech": "y"})],
    })


def tiers(path):
    root = ET.parse(path).getroot()
    return {t.get("TIER_ID"): t for t in root.findall("TIER")}


def test_flat_export_gives_every_tier_its_own_root(h, tmp_path):
    out = to_elan(h, "v.mp4", tmp_path / "f.eaf", nest=False)
    for name, t in tiers(out).items():
        assert t.get("PARENT_REF") is None, f"{name} should be a root tier"


def test_nested_export_is_unchanged(h, tmp_path):
    """The hierarchy export still nests, because that is what it is for."""
    out = to_elan(h, "v.mp4", tmp_path / "n.eaf")
    assert tiers(out)["speech"].get("PARENT_REF") == "motion"


def test_a_vocabulary_is_written_and_referenced(h, tmp_path):
    out = to_elan(h, "v.mp4", tmp_path / "cv.eaf", nest=False,
                  vocabularies={"speech": ["with", "without"]})
    root = ET.parse(out).getroot()
    cvs = root.findall("CONTROLLED_VOCABULARY")
    assert len(cvs) == 1
    entries = {e.find("CVE_VALUE").text for e in cvs[0].findall("CV_ENTRY_ML")}
    assert entries == {"with", "without"}
    ltype = tiers(out)["speech"].get("LINGUISTIC_TYPE_REF")
    lt = [t for t in root.findall("LINGUISTIC_TYPE")
          if t.get("LINGUISTIC_TYPE_ID") == ltype][0]
    assert lt.get("CONTROLLED_VOCABULARY_REF") == cvs[0].get("CV_ID")


def test_a_tier_with_a_vocabulary_is_still_time_alignable(h, tmp_path):
    """She must be able to draw the span, not only pick the label for someone else's."""
    out = to_elan(h, "v.mp4", tmp_path / "cv2.eaf", nest=False,
                  vocabularies={"speech": ["with", "without"]})
    root = ET.parse(out).getroot()
    ltype = tiers(out)["speech"].get("LINGUISTIC_TYPE_REF")
    lt = [t for t in root.findall("LINGUISTIC_TYPE")
          if t.get("LINGUISTIC_TYPE_ID") == ltype][0]
    assert lt.get("TIME_ALIGNABLE") == "true"


def test_an_empty_level_still_produces_its_tier(tmp_path):
    """Tiers she fills herself must exist in the file, or she has to create them by
    hand and name them differently from every other session."""
    h = Hierarchy(levels={"motion": [Action(start=0.0, end=1.0, source="m")],
                          "notes": []})
    out = to_elan(h, "v.mp4", tmp_path / "e.eaf", nest=False)
    assert "notes" in tiers(out)


def test_every_language_referenced_is_declared(h, tmp_path):
    """EAF 3.0 resolves LANG_REF against LANGUAGE elements in the document.

    A controlled vocabulary written with `LANG_REF="und"` and no matching LANGUAGE
    element is well-formed XML that ELAN complains about, which is the same failure this
    exporter has already shipped once: a valid-looking .eaf that will not open is not an
    export.
    """
    out = to_elan(h, "v.mp4", tmp_path / "lang.eaf", nest=False,
                  vocabularies={"speech": ["with", "without"]})
    root = ET.parse(out).getroot()
    declared = {e.get("LANG_ID") for e in root.findall("LANGUAGE")}
    used = {e.get("LANG_REF") for e in root.iter() if e.get("LANG_REF")}
    assert used, "the vocabulary should reference a language"
    assert used <= declared, f"undeclared languages: {used - declared}"


def test_flat_export_does_not_invent_tiers_the_caller_did_not_ask_for(h, tmp_path):
    """In flat mode the caller declares the tiers, including the empty ones.

    Handing an annotator two indistinguishable empty free-text tiers, one of them named
    by the exporter, invites her to put half her notes in each.
    """
    out = to_elan(h, "v.mp4", tmp_path / "noextra.eaf", nest=False)
    assert set(tiers(out)) == {"motion", "speech"}

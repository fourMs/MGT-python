"""Levels are checked for CONTAINMENT, not for plausibility.

A segmenter that returns roughly the right number of roughly the right-looking spans
passes any eyeball check. What it must actually do is nest: every action lies inside a
phrase, every phrase inside a part. So the fixture plants a hierarchy --- three
phrases of four actions --- and the assertions are about containment.

The part level is the one with a claim worth falsifying. ARJ's observation is that the
dancers talk between improvisations and hardly at all while dancing, so an
improvisation is where motion is high and speech is absent, and the gap between them
is the converse. Two weak signals that agree beat one strong one. Where they DISAGREE
the boundary is a guess, and it must be recorded as one rather than smoothed over.
"""
import numpy as np
import pytest

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy, part_level


def _planted():
    """Three phrases of four actions, on a 50 fps grid.

    The phrases are CONTIGUOUS --- 0-100, 100-200, 200-300 --- so that a span sitting
    on a boundary is possible. An earlier version left gaps between them, which made
    overlap and midpoint containment agree on every span and let the midpoint test
    pass against overlap containment.
    """
    actions, phrases = [], []
    for p in range(3):
        p0 = p * 100.0
        phrases.append(Action(start=p0, end=p0 + 100.0, source="phrase"))
        for a in range(4):
            a0 = p0 + a * 20.0
            actions.append(Action(start=a0, end=a0 + 10.0, source="action"))
    parts = [Action(start=0.0, end=300.0, source="part")]
    return Hierarchy(levels={"part": parts, "phrase": phrases, "action": actions})


def test_every_action_has_exactly_one_phrase_parent():
    h = _planted()
    for a in h.levels["action"]:
        assert h.parent(a, "phrase") is not None, f"{a} is an orphan"


def test_each_phrase_has_its_four_actions():
    h = _planted()
    for ph in h.levels["phrase"]:
        assert len(h.children(ph, "action")) == 4


def test_children_are_not_shared_between_phrases():
    """Containment by time must not double-count a span on a boundary."""
    h = _planted()
    seen = [id(c) for ph in h.levels["phrase"] for c in h.children(ph, "action")]
    assert len(seen) == len(set(seen)) == 12


def test_a_level_can_be_recomputed_without_touching_the_others():
    """The reason containment is computed on demand rather than stored as a tree."""
    h = _planted()
    h.levels["action"] = h.levels["action"][:4]
    assert len(h.children(h.levels["phrase"][0], "action")) == 4
    assert len(h.children(h.levels["phrase"][1], "action")) == 0


def test_a_span_on_a_boundary_belongs_to_exactly_one_parent():
    """The midpoint rule, tested with a span that overlap containment double-counts.

    An action from 95 s to 105 s lies partly in the phrase ending at 100 s and partly
    in the one starting there. Overlap containment returns it to BOTH, and twelve
    actions under three phrases then count as thirteen.
    """
    h = _planted()
    straddler = Action(start=95.0, end=105.0, source="action")
    h.levels["action"].append(straddler)

    owners = [ph for ph in h.levels["phrase"]
              if straddler in h.children(ph, "action")]
    assert len(owners) == 1, f"claimed by {len(owners)} phrases"
    assert owners[0].start == 100.0, "the midpoint at 100 s belongs to the later phrase"

    total = sum(len(h.children(ph, "action")) for ph in h.levels["phrase"])
    assert total == 13, total


def _session(fs=50.0):
    """Two improvisations with a talking gap between them.

    Motion high 0-100 s and 200-300 s; speech only in 100-200 s. This is the shape
    ARJ described, made into a fixture.
    """
    n = int(300 * fs)
    qom = np.full(n, 0.02)
    qom[: int(100 * fs)] = 1.0
    qom[int(200 * fs):] = 1.0
    #: ONE OUTLIER, and it is load-bearing. Without it the session mean and its 25th
    #: percentile both fall between the quiet floor and the activity level, so a
    #: quiet_level taken from the mean works just as well and the percentile is
    #: untested. Measured on this fixture: two seconds of outlier put the mean at
    #: 0.9917, still just below the activity level of 1.0, and the mean-based version
    #: passed. Four seconds puts it at about 1.34 --- ABOVE the dancing --- so a mean
    #: threshold marks only the outlier as movement and finds one improvisation
    #: instead of two. That is what a camera flash or someone crossing close to the
    #: lens does to a real session envelope.
    qom[int(50 * fs): int(54 * fs)] = 50.0
    speech = [Action(start=110.0, end=190.0, source="vad")]
    return qom, fs, speech


def test_two_improvisations_are_found():
    qom, fs, speech = _session()
    parts = part_level(qom, fs, speech, min_part_s=30.0)
    improv = [p for p in parts if p.labels.get("part") == "improvisation"]
    assert len(improv) == 2, [(p.start, p.end, p.labels) for p in parts]


def test_the_talking_section_is_labelled_talk():
    qom, fs, speech = _session()
    parts = part_level(qom, fs, speech, min_part_s=30.0)
    talk = [p for p in parts if p.labels.get("part") == "talk"]
    assert len(talk) == 1
    assert talk[0].start == pytest.approx(100.0, abs=10.0)


def test_agreement_is_recorded_on_every_part():
    """The falsifiable claim: which boundaries both signals support."""
    qom, fs, speech = _session()
    for p in part_level(qom, fs, speech, min_part_s=30.0):
        assert p.features["agreement"] in {"both", "motion_only", "vad_only"}


def test_a_boundary_only_one_signal_supports_is_marked_as_such():
    """Motion drops but nobody speaks: the boundary is a guess and must say so."""
    qom, fs, _ = _session()
    parts = part_level(qom, fs, speech=[], min_part_s=30.0)
    assert any(p.features["agreement"] == "motion_only" for p in parts), \
        [p.features for p in parts]


def test_no_speech_and_no_motion_change_yields_one_part():
    fs = 50.0
    parts = part_level(np.full(int(300 * fs), 1.0), fs, speech=[], min_part_s=30.0)
    assert len(parts) == 1

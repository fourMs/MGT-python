"""A curated sample and a defensible one are different things.

Any claim the student's analysis makes about the corpus is a claim about the sample it
was drawn from. Ranking by how clean the segments look produces easier material to
annotate and a sample whose distribution is a property of the ranking. So selection is
stratified and seeded, and salience is measured on everything and used for nothing ---
which keeps a curated subset available later without re-running anything.
"""
import numpy as np
import pytest

from musicalgestures._actions import Action
from musicalgestures._hierarchy import Hierarchy
from musicalgestures._select import salience, stratified_sample


def _h(n_per_part=10, n_parts=3):
    phrases, parts = [], []
    for p in range(n_parts):
        p0 = p * 1000.0
        parts.append(Action(start=p0, end=p0 + 1000.0, source="part",
                            labels={"part": "improvisation"}))
        for k in range(n_per_part):
            s = p0 + k * 90.0
            phrases.append(Action(start=s, end=s + 60.0, source="phrase"))
    return Hierarchy(levels={"part": parts, "phrase": phrases})


def test_the_same_seed_gives_the_same_sample():
    a = stratified_sample(_h(), level="phrase", n=6, seed=7)
    b = stratified_sample(_h(), level="phrase", n=6, seed=7)
    assert [(x.start, x.end) for x in a] == [(x.start, x.end) for x in b]


def test_a_different_seed_gives_a_different_sample():
    a = stratified_sample(_h(), level="phrase", n=6, seed=1)
    b = stratified_sample(_h(), level="phrase", n=6, seed=2)
    assert [(x.start, x.end) for x in a] != [(x.start, x.end) for x in b]


def test_every_stratum_is_represented():
    """The whole reason for stratifying: no part may be missed."""
    h = _h()
    chosen = stratified_sample(h, level="phrase", n=6, seed=0)
    parts = {h.parent(c, "part").start for c in chosen}
    assert len(parts) == 3, parts


def test_a_small_sample_still_reaches_every_stratum():
    """Three drawn from three parts must be one each, not three from the first."""
    h = _h(n_per_part=20, n_parts=3)
    chosen = stratified_sample(h, level="phrase", n=3, seed=0)
    assert len({h.parent(c, "part").start for c in chosen}) == 3


def test_an_uneven_corpus_does_not_starve_the_small_stratum():
    """A short improvisation must appear even when another has ten times as many."""
    phrases, parts = [], []
    for p, count in enumerate((30, 3)):
        p0 = p * 10000.0
        parts.append(Action(start=p0, end=p0 + 10000.0, source="part"))
        for k in range(count):
            phrases.append(Action(start=p0 + k * 100.0, end=p0 + k * 100.0 + 60.0,
                                  source="phrase"))
    h = Hierarchy(levels={"part": parts, "phrase": phrases})
    chosen = stratified_sample(h, level="phrase", n=6, seed=0)
    assert len({h.parent(c, "part").start for c in chosen}) == 2


def test_asking_for_more_than_exists_returns_everything_once():
    h = _h(n_per_part=2, n_parts=2)
    chosen = stratified_sample(h, level="phrase", n=99, seed=0)
    assert len(chosen) == 4
    assert len({(c.start, c.end) for c in chosen}) == 4


def test_the_seed_is_recorded_on_every_chosen_span():
    """A sample nobody can reproduce is not a sample."""
    for c in stratified_sample(_h(), level="phrase", n=6, seed=11):
        assert c.features["sample_seed"] == 11


def test_selection_does_not_prefer_the_most_salient_spans():
    """Selection must not depend on salience, or the sample becomes curated.

    One phrase is made spectacular. Across many seeds it must be chosen about as often
    as any other --- if selection ranked on salience it would be chosen every time.
    """
    h = _h(n_per_part=10, n_parts=3)
    spectacular = h.levels["phrase"][4].start
    hits = 0
    for seed in range(30):
        chosen = stratified_sample(_h(), level="phrase", n=3, seed=seed)
        hits += any(c.start == spectacular for c in chosen)
    assert hits < 25, f"chosen {hits}/30 times; selection looks ranked, not random"


def test_salience_reports_the_three_measures():
    fs = 50.0
    qom = np.zeros(int(200 * fs))
    qom[int(50 * fs): int(80 * fs)] = 1.0
    s = salience(Action(start=40.0, end=90.0, source="phrase"), qom, fs)
    assert set(s) == {"onset_clarity", "motion_range", "boundary_separation"}
    assert s["motion_range"] > 0


def test_salience_of_a_span_past_the_end_is_not_an_error():
    fs = 50.0
    s = salience(Action(start=500.0, end=600.0, source="phrase"),
                 np.zeros(int(100 * fs)), fs)
    assert s["motion_range"] == 0.0


def test_exactly_n_are_returned_when_enough_exist():
    """A per-stratum quota under-delivers whenever n does not divide evenly.

    Five wanted from three improvisations gives a quota of one each and returns three.
    Dealing round-robin returns five, which is what was asked for. The other
    stratification tests all pass under a quota, so this is the one that distinguishes
    the two --- without it the round-robin deal is untested.
    """
    h = _h(n_per_part=10, n_parts=3)
    assert len(stratified_sample(h, level="phrase", n=5, seed=0)) == 5
    assert len(stratified_sample(_h(), level="phrase", n=7, seed=0)) == 7

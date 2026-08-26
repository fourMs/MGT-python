"""Locating one recording inside another by sound.

These live in `_alignment` beside `xcorr_lag`, which answers the neighbouring question:
how far apart two signals are that already cover the same stretch of time. A separate
`_align` module would have been a second alignment module with a near-identical name.

Two recordings of one event share content even when they share nothing else --- different
cameras, different rooms, a cut and re-encoded copy. Their loudness envelopes can be
correlated, and the lag that matches them is the offset between their clocks.

Three faults this must not have, all met on real data:

- a probe that matches nothing must say so rather than return its best guess. Every
  cross-correlation has a maximum; the maximum of noise is still a maximum;
- the summary of several probes must be the offset that RECURS, not the middle of a list.
  On the LoLa recordings, where clip microphones were matched against a room microphone,
  most probes matched nothing and landed anywhere, and a median of that is meaningless;
- correlation must be normalised over the actual overlap, or a one-sample overlap scores
  perfectly.
"""
import numpy as np
import pytest

from musicalgestures._alignment import align_by_audio, locate_probe


def _reference(n, seed=0):
    rng = np.random.default_rng(seed)
    return np.abs(rng.normal(size=n)) + 0.1


def test_a_probe_cut_from_the_reference_is_found_at_its_offset():
    ref = _reference(4000)
    probe = ref[1500:1700]
    pos, r = locate_probe(probe, ref)
    assert pos == 1500
    assert r == pytest.approx(1.0)


def test_a_probe_matching_nothing_is_reported_as_no_match():
    ref = _reference(4000, seed=1)
    probe = _reference(200, seed=99)
    pos, r = locate_probe(probe, ref)
    assert r < 0.5


def test_a_flat_probe_cannot_be_located_and_says_so():
    """Zero variance makes correlation undefined. A confident answer would be a lie."""
    ref = _reference(2000)
    pos, r = locate_probe(np.ones(100), ref)
    assert pos is None


def test_the_offset_is_the_one_that_recurs_not_the_median():
    """Half the probes land at the true offset, half scattered. The median is nonsense."""
    ref = _reference(20000, seed=3)
    cut = ref[5000:15000]
    offset, conf, n_agree, n_total = align_by_audio(cut, ref, fs=1.0, n_probes=8,
                                                    probe_s=500.0)
    assert offset == pytest.approx(5000.0, abs=2.0)
    assert n_agree >= n_total // 2


def test_offsets_are_returned_in_seconds_not_samples():
    ref = _reference(8000, seed=4)
    cut = ref[2000:6000]
    offset, conf, _, _ = align_by_audio(cut, ref, fs=100.0, n_probes=5, probe_s=10.0)
    assert offset == pytest.approx(20.0, abs=0.1)


def test_a_cut_that_is_not_in_the_reference_returns_no_offset():
    ref = _reference(8000, seed=5)
    other = _reference(4000, seed=1234)
    offset, conf, n_agree, n_total = align_by_audio(other, ref, fs=1.0, n_probes=6,
                                                    probe_s=200.0)
    assert offset is None

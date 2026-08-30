# Fragment re-association: from track fragments to persistent movers, honestly

**Status:** design, for ARJ's approval. No code exists. This is the identity claim
that per-dancer Effort on the co-located day waits for, named in report 16 and the
TODO since the ensemble repair.

## The problem, measured

Identity tracking over a long session yields fragments, not people: 1,630 fragments
for the two co-located dancers over 2.6 hours (mean about 6 s), 529 for the dancer
and her projection on 30 Nov RITMO. A fragment is trustworthy --- within it, a
trajectory cannot teleport --- but nothing links fragment 412 to fragment 413, and
the ensemble analyses deliberately refused to guess. Re-association is the module
that turns fragments into K persistent movers, with the refusals kept.

## What the associator may use, and what it may not

Position and time only, in v1. The stored fragments carry keypoints, times and
frame indices --- no appearance embeddings, and re-decoding the corpus for ReID
features is a separate, heavier decision. That sets a hard, honest limit up front:
**position-only association cannot disambiguate two movers who cross while one
fragment ends and another begins.** At such moments the associator must refuse ---
record a break with both candidates --- rather than pick. The design treats
refusal points as output, not failure: an analyst can resolve a handful of breaks
by watching seconds of video, and a chain between breaks is then trustworthy.

## API sketch

```python
associate_fragments(tracks, n_movers=2, max_gap_s=2.0, max_speed=None) -> dict
```

Input is `extract_pose_tracks_yolo`'s output. The associator:

1. Orders fragments by start time.
2. Holds the **exclusivity constraint**: fragments overlapping in time must belong
   to different movers --- with `n_movers=2` this alone chains long stretches.
3. Links a fragment to a mover when the gap to the mover's last fragment is at
   most `max_gap_s` and the implied bridging speed of the shoulder midpoint is
   plausible (below `max_speed`, defaulting to a multiple of the corpus's own
   within-fragment speed distribution --- measured, not guessed).
4. **Refuses at ambiguity**: when more than one mover could accept a fragment
   under the same tests, or none can, it records a break. Chains restart after
   breaks with fresh mover labels; a `segments` list maps chain-segments to
   movers-within-segment, and nothing claims continuity across a break.

Returns per-mover trajectories in the single-person extractor's contract, plus
`breaks` (time, candidates, reason) and coverage statistics.

## Validation plan, test-first as always

- **Synthetic, exact**: two crossing sinusoidal walkers, fragmented at known
  points. Fragments cut AWAY from crossings must re-chain perfectly; a fragment
  boundary placed AT a simultaneous crossing must produce a refusal, not a guess
  --- the test asserts the refusal.
- **Corpus, statistical**: on 27 Nov, chained coverage per mover, break count, and
  the sanity check that two movers' chains never overlap in time. Success is not
  zero breaks; it is few breaks, each at a moment a human can adjudicate quickly.
- **Downstream**: per-dancer Effort profiles recomputed on the two longest
  between-break segments, compared against the ensemble: the ensemble should sit
  between the two dancers' individual contours.

## Non-goals

- Appearance/ReID embeddings (v2 if the break count on real material demands it;
  it would also need the re-decode).
- Cross-session identity ("dancer A on Tuesday is dancer A on Thursday") --- out
  of scope entirely.
- Any claim about which mover is which *person*: the output says "mover 1" and
  "mover 2" per segment, and mapping movers to Ole and Lisa stays a human act.

## Measured on the corpus, same day

Run on the co-located day (1,630 fragments, 159 minutes): with three mover slots
(the third absorbs researchers entering frame), 374 breaks --- 351 "no plausible
mover", 23 ambiguous --- yielding 375 segments, the longest 6.6 minutes. Only one
segment over two minutes has BOTH movers covering most of its span (2.6 minutes at
minute 111): chains are real but thin, and the v2 lever the design named ---
appearance ReID, with its re-decode --- is what more per-dancer coverage costs.

And the downstream check was measured and found to be wrongly designed. The
expectation that the ensemble sits between the two movers held for Space only
(0.12 between 0.07 and 0.15) and failed for Time, Weight and Flow, where the
ensemble sits ABOVE both movers --- correctly: burst concentration and spectral
roughness of a MIXTURE of two movers exceed each component's, because interleaved
burst patterns are burstier than either alone. These indices are not convex in
their inputs, so "between" was never the right prediction. The check to keep is
Space's; the failed three are a lesson about the indices, not about the chains.

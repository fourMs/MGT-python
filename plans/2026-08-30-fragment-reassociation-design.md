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

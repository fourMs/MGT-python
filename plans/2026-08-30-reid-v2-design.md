# Appearance for the associator: the v2 the break count asked for

**Status:** design, for ARJ's approval. No code exists. The v1 associator
(`2026-08-30-fragment-reassociation-design.md`) measured its own limit on the
co-located day: position-and-time chaining yields segments up to 6.6 minutes but
only one two-minute-plus stretch holding both dancers, with 351 of 374 breaks
being "no plausible mover" --- a dancer re-entering after occlusion, too far or
too late for a positional bridge. Appearance is the information that survives an
occlusion. This design prices three ways of getting it.

## What is actually needed

Not open-set person re-identification. The problem is closed over one session:
two dancers (occasionally a researcher), constant clothing, one camera. A small
embedding per fragment --- even a colour/texture statistic --- that says "these
two fragments wear the same body" across a gap of seconds to minutes is enough to
link chains across most of the 351 positional breaks. The v1 rules stay: an
appearance link must still pass exclusivity, and a link the embedding cannot
decide stays a break. Refusal remains output.

## Three routes, priced

1. **Boundary crops by seeking.** Decode only each fragment's first and last
   frame (2 x 1,630 seeks on the co-located day) and embed the person crop.
   Cheapest in compute, but this drive has already taught that scattered seeks
   cost more than decoding past (the lesson is written into three extractors), so
   about 3,300 seeks is plausibly SLOWER than one sequential pass --- and two
   frames per fragment is a thin sample of a dancer mid-turn.
2. **A sequential low-cost appearance pass.** One more sequential decode at
   working resolution; for every stored detection row, cut the person's bounding
   box (derivable from its keypoints) and keep a cheap embedding --- a colour
   histogram in a robust space, or a tiny OSNet-class ReID net on the GPU. One
   decode ≈ the extraction's own cost (about an hour per multi-body recording),
   embeddings for EVERY row, fragment appearance = a robust mean over many
   frames. This is the recommended route: the drive's own economics, and dense
   sampling where route 1 is thin.
3. **Re-extract with embeddings in the loop.** Fold an embedding model into
   `extract_pose_tracks_yolo` itself so future extractions carry appearance from
   birth. Right as the eventual toolbox shape (a `embed=` option), wasteful as
   the way to get THIS corpus's embeddings --- it redoes pose that already
   exists.

Recommendation: **route 2 now, route 3's option folded into the extractor
whenever it is next touched.**

## API sketch

```python
fragment_embeddings(filename, tracks_data, method="hist") -> dict   # id -> vector
associate_fragments(tracks_data, ..., embeddings=None,
                    min_separation=None) -> dict
```

With `embeddings`, the associator adds one rule: a positional break of kind "no
plausible mover" may be bridged when exactly one mover's recent appearance is
within the match threshold AND the other movers' are clearly not ---
`min_separation` between best and second-best match, measured from the session's
own within-fragment embedding spread, never guessed. Ambiguity still breaks.

## Validation

- **Within-fragment consistency**: embeddings of one fragment's early and late
  rows must agree better than embeddings across the two movers of an overlapping
  pair --- measurable on the corpus with no ground truth needed, and the gate for
  whether a cheap histogram suffices or the small net is required.
- **Synthetic**: the v1 walker tests extended with two "appearances"; the
  crossing-cut case must now LINK (appearance disambiguates it) while a
  same-appearance crossing must still break.
- **Corpus outcome measure**: two-mover coverage minutes on the co-located day,
  before against after. v1's number to beat: one segment, 2.6 minutes.

## Non-goals

Unchanged from v1: no cross-session identity, no named persons --- mover-to-Ole
mapping stays a human act, now needed once per appearance-linked chain rather
than once per fragment.

## Measured on the corpus, same day

The recommended route ran: one sequential pass, embeddings for 1,334 of 1,630
fragments (the rest too small or low-confidence for a torso crop), colour
histograms only. Against v1's number to beat --- one two-mover segment of 2.6
minutes --- appearance gives **ten segments over two minutes, the longest 8.2,
and 71 minutes of summed two-mover coverage** in the 159-minute session, with 67
of 374 breaks bridged. The histogram sufficed; nothing heavier is currently
justified.

Per-dancer Effort now exists as ten valid within-segment pairs
(`effort_per_dancer.json` beside the corpus scripts), with real contrasts inside
them --- in one stretch one dancer moves almost four times more directly than the
other. One boundary holds until the next step: mover labels restart at every
break, so nothing aggregates a dancer ACROSS segments yet. Appearance can link
mover-chains across breaks the same way it links fragments; that is the v2.1
refinement, small and priced at zero new decodes.

# The development plan after 1.25.0

**Status:** approved by ARJ 2026-08-30; the four structuring decisions below are his.
Supersedes the sequencing half of `2026-08-22-road-to-2.0-design.md`, whose central
decision --- 2.0 is API hygiene only, nothing architectural rides on it --- stands
unchanged. Implementation plans are written per feature, not here.

## The four decisions of 2026-08-30

1. **The Effort layer (#373) is built on our own SPARC implementation**, not on
   pyeyesweb. We own the whole layer and its validation burden; no new dependency.
   The Laban mapping is named as our own operationalisation, per the assessment in
   `2026-08-23-pyeyesweb-and-laban.md`.
2. **The YOLO pose wrapper (#359) happens**, with Ultralytics as an optional extra in
   the established pattern: import guarded, documented, tested when present.
3. **#312, the in-memory workflow, is closed as won't-do.** Three years without
   demand, and the disk-writing chains are what students actually debug. The issue
   gets the reason in writing and reopens if a real use case appears.
4. **`motiongram_data` aligns with the x/y scheme**: `orientation="x"` / `"y"` like
   `motiongrams()`, with `"vertical"` / `"horizontal"` deprecated until 2.0.

## The release sequence

### 1.26 --- the last deprecation batch (soon)

The point of 1.26 is to complete the set of deprecations so they all age together and
2.0 becomes one clean removal. Content:

- `motiongram_data` orientation alignment (decision 4), with the deprecation warning.
- The YOLO pose wrapper (#359), additive.
- The 12.6 Hz P-frame motion envelope, additive and now nearly free: it was priced as
  "needs PyAV, a new optional dependency" when assessed, and PyAV has since become the
  `motionvectors` extra --- the envelope reader belongs behind the same extra. Its
  honest limits ship in the docstring: a 12.6 Hz envelope, not a 50 Hz track; median
  r = 0.82 against exact QoM, falling to 0.57 in near-still windows; B-frames excluded.

After 1.26, no further deprecations without a strong reason: everything breaking
should be warning by then.

### 1.27+ --- the Effort layer (autumn/winter 2026)

#373 on our own SPARC (decision 1). This is the one item that needs a real design
document before code: which Effort qualities are claimed (Weight and Time have
established operationalisations; Space and Flow have only substrates), what each is
validated against, and the naming that says whose operationalisation this is. The
existing action-recognition foundation from 1.15.0 is the base. No date promised;
design first.

### JOSS (#311) --- revived to land with 2.0

The paper is written against the API that 2.0 freezes, so the two are one project:
draft through spring 2027 as the deprecations age, submit around the 2.0 cut. The
current `paper/paper.md` is the 48-line 2020 stub; the author list is ARJ's call.

### 2.0 --- June 2027, removals only

Per the 2026-08-30 discussion: the deprecation warnings only became visible on
2026-08-23, and the largest alias batch (the x/y gram renames) is days old, so
release-counting overstates the warning period enormously. 2.0 cuts at a semester
boundary at least one full semester after 1.26's warnings: June 2027. Content is
removals and nothing else --- migrating stays mechanical, and the release pairs with
the JOSS submission as the "the API is now stable" statement.

## Explicit non-goals

- **#312** --- closed, not parked (decision 3).
- **A second camera** is recording practice, not toolbox code; it stays advice in the
  #373 assessment.
- **Corpus-specific machinery stays in the corpus.** The HybridDanceImprov scripts
  consume MGT; nothing tuned to those six recordings comes upstream. What does come
  upstream is the generalisable kind the last week produced: plates, floors, texture,
  bounded sampling, paged views.

## Candidate, gated on a corpus decision

Whether the vector noise floor should sample textured cells only (the Portal-curtain
interaction, in the corpus TODO) has an MGT half if ARJ decides yes: an optional
`mask=` on the floor functions. Additive, small, and waits for his answer.

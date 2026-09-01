# A reorganisation of the MGT documentation, proposed

Written 2026-09-01 at ARJ's request. The brief: the docs site and the wiki are hard to
navigate, with very many subsections. The first user group is music researchers and
students, then psychologists, then human movement science, and finally computer
scientists. The toolbox should align with the relevant theories and support both
qualitative and quantitative approaches.

*Status, updated later the same day after ARJ approved:* the site restructure is
implemented (five-section nav, Home with audience paths, new `docs/concepts.md` and
`docs/gallery.md`, API menu regrouped), and the wiki is renumbered by pedagogy with
all internal links swept. The editorial part followed the same day: tutorial prose
from 7 User Guide pages moved into 10 wiki chapters (723 lines gained there, 1,531
removed from the site), the site pages became task references, and every inbound
anchor was kept alive and verified. The reorganisation is complete.

## What makes it hard to navigate today, measured

- The site's API Reference menu lists 46 entries, 16 of them inside one
  "Segmentation and annotation" submenu, ordered neither alphabetically nor
  conceptually. Finding `_posegram` requires already knowing it exists.
- The User Guide's 9 pages are organised by medium and algorithm (Video Analysis,
  Audio Analysis, Pose Tracking), which is the computer scientist's map --- the
  fourth audience's --- handed to the first.
- The wiki's 16 numbered chapters say they read in order, and they do, but the
  numbering encodes history rather than pedagogy: 360 video (ch. 14) sits between
  ambiscape (13) and segmentation (15), and the reader who wants annotation meets
  it last.
- Wiki and User Guide overlap: loading, preprocessing, video-based processes and
  audio-based processes each exist in both places, similar but not identical, so
  neither is authoritative and both must be maintained.

## The organising idea: navigate by the theory, not by the algorithm

The toolbox now has a conceptual spine that the documentation does not use: two rows
and three levels, measured, segmented, interpreted.

| | measured | segmented | interpreted |
|---|---|---|---|
| dynamic | motion | action | gesture |
| static | position | posture | pose |

This ladder is the theory the first audience already knows (it is the *Sound Actions*
scheme, rooted in the musical-gestures literature), it names honest boundaries for
the other audiences (interpretation is the human's job, which is precisely the
qualitative/quantitative division of labour), and every module in the toolbox sits
somewhere on it. So the proposal is to let it organise the documentation, with the
media types (video, audio, 360) as properties of pages rather than as top-level
sections.

## Proposed structure of the docs site

Five top-level sections instead of the current heap:

**1. Start.** Install, a first analysis in five lines, and a visual gallery. The
gallery matters most: this is a visual field, and a page of thumbnails --- one per
output type, each linking to the page that makes it --- is the most welcoming index a
dance student can get. The material exists (the documentation figures and the
examples gallery); it needs to become the front door rather than an appendix.

**2. Concepts.** One short chapter, mostly prose, little code: the two-row ladder
with the terminology passage; quantity of motion and what it can and cannot claim;
visualisation as a way of looking (the motiongram tradition); Laban effort as a
qualitative language with computational reading aids; what pose estimation measures
in these terms. Each concept ends with pointers into the literature of each
audience, so a psychologist finds de Gelder and a movement scientist finds Horak
next to the function that concerns them. This is where theory alignment lives, once,
instead of being repeated thinly in every module docstring.

**3. Ways of looking (qualitative first).** Video playback, videograms, motiongrams,
average images, history videos, pose timelines, posegrams. Framed as instruments for
human looking, because that is what they are: the qualitative approach is the
toolbox's oldest layer and the first audience's daily practice.

**4. Ways of measuring and segmenting (quantitative).** Ordered by the ladder, not
by medium: measuring motion and position (QoM, flow, landmarks, sway); segmenting
actions and postures (actions, postures, pulse and cycles, long-video segmentation);
towards interpretation (annotation, ELAN, labels, correlation and co-occurrence,
effort). Audio analysis joins here as measurement of the sound row rather than as a
separate world.

**5. Reference.** The API stubs, regrouped under the same headings as sections 3
and 4, with the complete alphabetical list kept as one page for those who know what
they want. The Development pages (contributing, testing, releasing) stay where they
are; they serve the fourth audience, who will find them.

Four audience paths on the Home page, three links each, in the user's own
vocabulary: a music researcher starts at the gallery, the ladder and motiongrams; a
psychologist at posture and pose, annotation and co-occurrence; a movement scientist
at landmarks, sway and segmentation; a computer scientist at the API, the module
conventions and contributing. Each path is three lines of Home-page text, not a
separate documentation tree; the paths share the same pages and differ only in the
door.

## Proposed division of labour between wiki and site

Today the two surfaces compete. The clean split:

- **The wiki is the course.** Numbered chapters read in order, basics first, one
  concept at a time, exercises with the bundled example videos. It keeps its
  narrative voice and its ordering promise, and its chapters get renumbered by
  pedagogy: basics, looking, measuring, segmenting, annotating, and only then the
  special hardware chapters (360, ambiscape, physiological).
- **The site is the reference.** Gallery, concepts, task pages, API. It answers
  "how do I do X" and "what exactly does this return", never "teach me from the
  beginning".
- Duplication is resolved by deletion with redirects: the User Guide pages whose
  content is tutorial move their prose into the corresponding wiki chapter and
  shrink to task summaries with API links. mkdocs-redirects already exists in the
  config for exactly this, so old bookmarks keep resolving.

## What this costs and what it does not

The regrouping of the API menu and the Home-page paths are an afternoon each, since
no content changes. The Concepts chapter is mostly written already: the terminology
survey, the `_actions` and `_postures` docstrings, and the Laban survey contain the
text; it needs assembling and a style pass rather than research. The wiki
renumbering is the only structurally risky move, because wiki links embed chapter
names; it should be done in one pass with a link sweep, the way the posegram
reordering was handled.

What this proposal does not do: it does not rename any function, it does not split
the repository, and it does not write a separate documentation set per audience.
One set of pages, ordered by the theory the toolbox itself now states, with four
doors into it.

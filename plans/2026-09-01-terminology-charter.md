# The terminology charter: sharp terms and where their boundaries run

Written 2026-09-01 at ARJ's request, extending the four-levels rule to the rest of
the specialised vocabulary. Sources: the `Sensing Sound and Music` glossary (the
freshest statement of his definitions), `Sound Actions`, the settled corpus rules,
and this session's rulings. The charter is the reference for consistency sweeps
across MGT, the wikis, the course, and the book manuscripts; each sweep fixes only
clear violations and lists everything arguable.

## The frame: four levels

Physical signal, digital representation, perception, interpretation ("the air, the
file, the ear, or the listener"). Word choice follows the level, and cross-modal
pairings must pair within a level: audio–video (files), auditory–visual
(perception), sound–movement (phenomena), audio–motion (data).

## The two ladders (settled)

| | measured | segmented | interpreted |
|---|---|---|---|
| dynamic | motion | action | gesture |
| static | position | posture | pose |

Motion is physical displacement, continuous, objectively measurable. An action is
a chunk of motion with a fuzzy beginning and end, inferred by an observer. A
gesture is the meaning-bearing component of an action. The static row mirrors it.
Movement is the experienced counterpart of motion (how moving is felt), and motion
is the measured quantity: motion data, motion envelope, quantity of motion.

Misuses to hunt: "gesture" where nothing meaning-bearing is claimed (gesture data,
gesture tracking for raw trajectories); "action" for continuous motion; "movement"
for the measured quantity. Special names stay: Musical Gestures Toolbox, cited
terms from other authors.

## The percept–physics pairs (psychoacoustics)

| perceived | physical/measured |
|---|---|
| pitch | (fundamental) frequency |
| loudness | amplitude, sound pressure level |
| timbre | spectrum and temporal envelope |
| beat, pulse | onsets, periodicity |
| perceived onset | measured onset |

Timbre is "the sound quality that distinguishes two tones of identical pitch and
loudness"; it belongs to a listener. A file has a spectrum, a spectral envelope, a
spectral centroid; it does not have a timbre until someone listens. The same test
separates pitch from frequency and loudness from amplitude. Misuses to hunt: "the
timbre of the signal/file/spectrum", "the pitch of the signal" where a measured
f0 is meant, "loudness" for RMS level, and the reverse errors (frequency for
perceived height in prose about experience).

## The rhythm cluster

- **Rhythm**: a pattern of durations formed by intervals between *perceived*
  sound events; may or may not be periodic. Perception level.
- **Pulse / beat (tactus)**: the regular felt beat listeners tap to. Perception.
- **Metre**: the hierarchical framework of nested pulse levels rhythms are heard
  against. Perception/cognition.
- **Periodicity**: a signal property; the measured counterpart. A quantity-of-
  motion envelope has periodicity; a listener hears rhythm.
- **Tempo**: the rate of the pulse in BPM; a measurement made on a perceptual
  construct, so "estimated tempo" is honest wording for algorithm output.
- **Groove**: the pattern-plus-urge-to-move; interpretation level.
- **Onset**: the measurable start of an event; may differ from the perceived
  start. Data level; "onset detection" is correct algorithm language.

Misuses to hunt: "the rhythm of the signal/envelope" where periodicity is meant;
"beat" for detected onsets ("beat tracking" is the field's established name for
the algorithm family and stays, with the position stated where it matters).

## Coupling, mapping, and their statistical cousins

- **Action–sound coupling**: the lawful, mechanical link on an acoustic
  instrument.
- **Action–sound mapping**: the designed relation in an electronic instrument,
  arbitrary and reprogrammable.
- **Correlation**: a statistical association between two series; claims nothing
  about mechanism.
- **Entrainment**: the process of one rhythmic system synchronising with another;
  a dynamic process, not a similarity score. A correlation is evidence for
  entrainment at best, never the thing itself.
- **Synchronisation**: alignment in time; may be imposed, designed, or emergent.

Misuses to hunt: "mapping" for mechanical links, "coupling" for designed digital
relations, "entrainment" for a mere correlation or tempo similarity.

## Boundary objects proposed for sharp definitions (new)

Terms that different communities share while meaning different things, worth a
stated definition wherever they carry weight:

- **Soundscape vs acoustic environment**: ISO 12913 splits them exactly along the
  levels: the acoustic environment is physical; the soundscape is that
  environment *as perceived and experienced*. ambiscape's territory; the split
  deserves stating once in every soundscape-adjacent document.
- **Room vs space vs place**: physical enclosure, spatial extent, and humanly
  meaningful location; `Sound Spaces` builds on the distinction and should own
  it explicitly.
- **Stillness vs standstill vs micromotion**: the experienced quality, the
  deliberate practice/condition, and the measured residual motion. Micromotion is
  ARJ's term for the measured level.
- **Noise**: signal-level (the unwanted part relative to a signal of interest)
  versus aesthetic judgement; the two senses should never sit unmarked in one
  paragraph.
- **Segmentation vs chunking**: algorithmic cutting of data versus perceptual
  grouping by a listener/observer. This pair carries a live tension: the glossary
  says actions "cannot be read directly from motion data", while MGT's
  `segment_actions()` returns `Action` spans from an envelope. Flag, do not fix:
  the resolution (rename the spans, or state that the segmenter *proposes*
  actions) is ARJ's call.
- **Sound object vs sound event vs sound action**: Schaeffer's perceptual unit;
  the neutral physical/digital occurrence; ARJ's action–sound unit.
- **Co-located vs telematic vs hybrid**: the HybridDanceImprov axis; hybrid means
  the mix, not a synonym for telematic.
- **Instrument vs measurement device**, **modality vs data type**,
  **recording vs person-recording vs participant**: already settled corpus rules,
  restated here so sweeps enforce them.

## Sweep rules

Fix only clear violations of a stated definition. Never rename another author's
term, a proper name, a function or file name, or anything quoted; state ARJ's
position beside kept names only where he has asked for it. Historical records
(changelogs, release notes, published deposits) keep their wording. Everything
arguable goes on a list for ARJ, not into an edit.

## Addendum: what the sweeps found, 2026-09-01

Seven corpora were swept against this charter the day it was written: MGT docs,
wiki and code prose; the course chapters and glossary; both book manuscripts; the
standstill analysis reports (306 files); the soundscape analysis reports (61); and
the dance corpus (read-only first, then its priority fixes). Roughly 190 clear
violations were fixed, none touching an identifier, a number, a quotation, or a
published record. The pattern of the violations was consistent everywhere: movement
where motion is measured, loudness where a level is metered, gesture where a
segmenter's span carries no meaning claim, rhythm where a signal has periodicity,
and coupling where a correlation was computed.

The items that survived every sweep as judgment calls, for ARJ:

1. `segment_actions()` returns `Action` spans, and the glossary says actions cannot
   be read from motion data. Report 12 of the dance corpus already contains the
   resolution in prose: every boundary is "a proposal about where a phrase begins,
   not a fact". Whether the class is renamed or the proposal stance is stated in
   the API is the open decision.
2. `motion_audio_coupling()` and `dynamics_coupling()` compute correlations; the
   surrounding prose now says correlation, and the names assert coupling.
3. The dance corpus says "distributed" where this charter says "telematic", with
   one report using both; and nothing in that corpus is hybrid in the charter's
   sense, so the project name promises a condition the data does not contain.
4. "Instrument" in the measuring sense is load-bearing scaffolding across five
   soundscape reports, in a title, a heading and several arguments; the settled
   device rule cannot reach it by sweep.
5. The books' knowing extensions: a room's rhythm defined on the measured side
   (Sound Spaces ch. 10, unreconciled with ch. 8, which never states its own
   definition of rhythm); "standstill level" for measured mm/s where this charter
   says micromotion; "capturing a soundscape" as a heading pair; pulse redefined
   as heart rate where marked. Each wants either a licensing sentence or a ruling.
6. Feature names welded to published records ("loudness" streams, `visual_motion`,
   the `subject` CSV column) restyle only at a record's next version.

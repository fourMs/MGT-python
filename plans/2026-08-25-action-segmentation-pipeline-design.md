# Action segmentation and the three-level videogram — design

For the Hybrid Dance Improvisation corpus: six recordings, 12 h 14 m, 2,202,696 frames,
all 1920x1080 at 50 fps with AAC stereo at 48 kHz. The deliverable is material a student
can start a gesture analysis from, and this design covers the segmentation and the
figures only. The gesture-analysis frameworks are a later project, specified separately.

Supersedes nothing. It builds on `2026-08-24-long-video-segmentation-design.md`, which
remains the architecture, and settles what that document left open for ARJ.

ARJ's requirement, 2026-08-25, in three levels:

1. overview visualisations of all six recordings that allow the material to be segmented
   into talking and improvising sections, as videograms with waveforms and segmentation,
   one per file;
2. videograms and waveforms of each improvisation section;
3. selected segments at action or action-sequence level, targeting semantic analysis.

---

## What changed since the 2026-08-24 design, and why it matters

**The full-resolution pass is no longer expensive, so the downsampling question is
closed.** The 6.5 h figure in the earlier design was `mg_motion` computing the full
feature set with motiongrams. `extract_tracks_parallel` is a different path: the first
run wrote 264,008 frames between 08:08 and 08:27, which is about 11,500 frames per
minute, so a full session is roughly 41 minutes and the whole corpus is **about 3.2 hours
at native 1920**. One overnight job covers all six.

That removes open question 2 of the earlier design. There is no reason to accept the
boundary shift downsampling costs — a median 160 ms and a worst case of 2.94 s at 960
wide — when the accurate pass fits in a night. **Segment at native resolution
throughout.** Downsampling remains correct for occupancy alone, which is a slow presence
signal rather than a boundary crossing, and that asymmetry is stated wherever both are
configured.

**The first extraction run stopped because the machine went out of memory**, and the
diagnosis matters because it changes the runner rather than the extractor. At 08:17:58 on
2026-08-25 the kernel killed `msedge`, then `code` at 08:18:11, `gnome-software` at
08:22:17, **`claude` at 08:27:07** and `gvfsd-google` at 08:27:18. The extraction stopped
at 08:28. The killed `claude` process was the runner's parent, so the runner died with
it. Nothing in the extraction failed; it was killed, and the absence of a traceback was
the correct signal for a cause nobody had looked for.

Three requirements follow, and they belong to any long job on this machine:

- **a long run must not be a child of an interactive session.** Launch detached, so a
  session ending cannot take the job with it.
- **stderr and the exit status must be recorded beside the data.** Their absence is what
  made a memory kill look like a silent stop for a day.
- **memory must be logged while the job runs**, so a worker count rests on a measurement.

**`segment_actions` has a session-scale fault.** Its threshold is a fraction of the
envelope's global min–max range. Over 2 h 38 m a handful of outlier spikes compress
everything else toward the floor, so a threshold tuned on a clip means something
different on a session, silently. This is the same shape as the two long-video faults
already fixed: invisible on a clip, wrong on a session, and it does not raise. The fix is
a robust range option, described under `_actions.py` below.

---

## Architecture

Five modules over the cached feature table `_tracks.py` already writes.

```
video ──(once, ~41 min/session)──> _tracks.py ──> feature table on disk
                                        │
audio ──> _voice.py ──> speech segments │
              │                         │
              └────────────┬────────────┘
                           ▼
                     _hierarchy.py  (part / phrase / action)
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        _timeline.py               _annotate.py
     (three sheet tiers)      (.eaf / .TextGrid / .tsv)
```

| module | status | responsibility |
|---|---|---|
| `_tracks.py` | shipped 1.14.2, incomplete | extraction; gains a completeness check and tests |
| `_actions.py` | shipped | gains a robust range for session-scale envelopes |
| `_voice.py` | **new** | speech segments from audio, via silero-vad |
| `_hierarchy.py` | **new** | three levels of `Action`, related by containment |
| `_timeline.py` | **new** | the composite sheet, one renderer, three configurations |
| `_annotate.py` | **new** | ELAN, TextGrid and TSV from one `Hierarchy` |

`Action` is unchanged. Its split between `features` (measured) and `labels` (claimed) is
the seam the later gesture-framework layer attaches to, and nothing here should blur it.

---

## 1. `_tracks.py` — finish it, and make incompleteness visible

The extractor works and is validated. What is missing is the ability to know that it
finished.

`extract_tracks_parallel` preallocates the memmaps to an estimated frame count and
workers fill them in chunks, so the files reach full size in the first second of a run.
Every cheap check — file size, existence, `ls -la`, reading the last row — reports a
complete extraction over a file that is 44 per cent zeros.

```python
check_tracks(analysis_dir) -> dict
```

It returns **three numbers separately and refuses to reconcile them**, because on this
material they disagreed by 42,000 and 211,000 frames and each was right about something
different:

| number | what it means | on the stalled run |
|---|---|---|
| `preallocated` | the estimate the memmaps were sized to; never a measurement | 475,688 |
| `last_nonzero` | where data actually stops; workers write continuously | 264,008 |
| `highest_marker` | the last closed chunk; what `resume=True` trusts | 222,000 |

Plus `complete`, true only when `tracks_run.json` exists, and `marker_gaps`, because
contiguous markers and a gap at chunk 12 are different situations and a count cannot tell
them apart.

`tracks_run.json` is written last and by the runner alone, so its absence stays the
reliable signal that a run did not finish. Nothing else may create it.

**`build_pyramid` and `read_columns` have never produced output and have no tests.**
They shipped in 1.14.2 untested. Nothing may be built on either until each has a
known-answer test: a small array with planted extremes, so a pyramid level is checked for
*containment of the extreme* rather than for plausibility. A decimation that averages a
spike away passes a plausibility check and fails this one, which is the point.

---

## 2. `_actions.py` — a range that survives a session

```python
segment_actions(..., range_mode="minmax" | "robust", range_percentiles=(1.0, 99.0))
```

`minmax` is the current behaviour and stays the default, so nothing already measured
changes. `robust` takes the range between percentiles, so a handful of spikes cannot
depress the threshold for two hours of recording.

The phrase level additionally computes its range **within each part** rather than across
the session, because an improvisation's own dynamic range is what its phrases should be
cut against. A quiet improvisation and an energetic one are not usefully thresholded by
the same absolute level.

---

## 3. `_voice.py` — where speech is

```python
speech_segments(audio, threshold=0.5, min_speech_s=0.25, min_silence_s=0.5) -> list[Action]
```

silero-vad, an optional dependency, returning `Action` spans with `source="vad"` so
speech pools with everything else. It decides **where** speech is; it does not transcribe
and does not identify anyone.

The screening probe measured PANNs and silero-vad disagreeing on the same 60 s — `Speech
0.86` from the tagger against 1.6 s of speech from the detector, plus `Snort`, `Gasp`,
`Animal` and `Horse` on dancers breathing. So the division of labour is fixed: silero-vad
decides where speech is, PANNs decides whether there is music, and disagreements are
recorded rather than resolved silently.

---

## 4. `_hierarchy.py` — three levels, and honesty about each

```python
build_hierarchy(analysis_dir, speech=None, levels=("part", "phrase", "action")) -> Hierarchy
```

`Hierarchy` holds levels by name and computes `children()` / `parent()` **by time
containment on demand** rather than storing a tree, so any level can be recomputed
without invalidating the others.

### The part level: talking versus improvising

Not cut from motion alone. Per ARJ's observation — the dancers talk between
improvisations and hardly at all while dancing — a between-improvisation section is where
speech is present **and** motion is low, and an improvisation is the converse. Two weak
signals that agree beat one strong one, and this keys on what the session does rather
than on how an envelope happens to bend.

Each part boundary records in `features`:

- `agreement`: `"both"` when the VAD and the motion floor mark the same transition
  within a tolerance, otherwise `"vad_only"` or `"motion_only"`;
- the two candidate times, so a disagreement can be inspected rather than only counted.

**This is what makes the segmentation falsifiable.** Proposed parts should be separated
by stretches both signals agree on. Where they disagree the boundary is a guess, and it
is drawn differently on the figure so a reader sees which boundaries to distrust without
reading a log.

### The phrase level

`segment_actions` on a smoothed envelope with a long `min_duration`, computed within each
improvisation part with `range_mode="robust"`. This is the practical unit for excerpt
selection: roughly 2,500 action-level segments per session is far too fine to choose
from.

### The action level

`segment_actions` at the working scale plus `motion_onsets`, at native 1920.

**Nothing here claims the levels are correct.** They are a starting point for a person to
correct, and the export exists so the correction happens in a tool built for it.

---

## 5. `_timeline.py` — one renderer, three configurations

The main new public function, and the thing the corpus has no equivalent of today.
`videograms_ffmpeg` produces a bare strip and `MgAudio.waveform` a standalone figure;
nothing composes panels on a shared time axis with boundaries drawn across them.

```python
render_timeline(analysis_dir, start_s=0.0, end_s=None,
                panels=("videogram_v", "qom", "waveform", "speech"),
                levels=("part",), out=None, dpi=150) -> Path
```

Panels stack on one shared time axis: the videogram strip, the quantity-of-motion
envelope, the audio waveform, a speech ribbon from the VAD, and boundary overlays drawn
across all panels so a boundary is read against every signal at once.

**Decimation is explicit, min/max, and printed on the figure.** An overview cannot show
475,680 columns. Reduction is min and max per output column, never a mean, so a brief
spike survives instead of averaging away; and the factor is printed in the corner,
because a decimated strip that does not say so invites a reader to measure timings off
it.

**Video and audio decimate to pixel columns independently.** This is how audio stays on
its own clock rather than being binned to the 20 ms frame grid — the earlier design's
rule, preserved at render time as well as in the table.

The three tiers differ only in span and in which level is drawn:

| tier | span | boundaries drawn | count |
|---|---|---|---|
| overview | whole file | part | 6 pages, one per recording |
| improvisation sheet | one part | phrase | one per improvisation |
| action strip | one phrase | action, one row each | one per selected phrase |

**The two Zoom days do not go on a shared time axis.** The cameras in RITMO and Portal
are not known to be synchronised and nothing has checked. A shared axis asserts
synchrony, so until a clap or another shared event verifies it, one page per file. The
figure must not make a claim the data does not support.

---

## 6. `_annotate.py` — three exports from one tree

ELAN `.eaf` with nested tiers, the format the hierarchy actually fits; Praat `TextGrid`
with flattened interval tiers; and TSV. One writer per format over a common `Hierarchy`,
so a fourth format is a function and not a pipeline.

The `.eaf` **links the full session video at session-time offsets**, not excerpt clips.
Clips would create a timestamp-remapping problem in every annotation the student makes,
and session time is the only clock that stays comparable across levels. It carries
populated Part, Phrase and Action tiers plus empty child tiers ready for an annotation
scheme.

Round-trip is wanted eventually and not now: export first, built so an importer attaches
without rework.

---

## 7. Excerpt selection

Stratified across improvisations, sessions and conditions, with the random seed recorded
in the sidecar so the sample is reproducible rather than merely arbitrary. A defensible
sample matters if the analysis makes any claim about the corpus.

Salience measures — onset clarity, motion range, boundary separation — are computed and
stored on **every** phrase segment but are not used for selection, so a curated subset can
be pulled later without re-running anything.

Excerpt clips are cut as a convenience for viewing, with the session offset in both the
filename and the sidecar, so a clip can always be put back on the session clock.

---

## Testing

Synthetic known-answer throughout, as `micromotion` and `_posetools` do:

- a generated video with movement at planted times, so segment boundaries have a right
  answer rather than a plausible one;
- a small array with planted extremes for `build_pyramid`, checked for containment of the
  extreme, and for `read_columns`, checked against a known slice;
- an envelope with a planted hierarchy — three phrases of four actions — so containment
  is checkable;
- an envelope with one huge spike, where `minmax` and `robust` must give different
  segment counts, which is the session-scale fault made into a test;
- a `.eaf` and a `TextGrid` written and re-read, asserting the tree survives;
- a truncated memmap with known marker gaps, so `check_tracks` is tested against the
  situation it exists for;
- resumption tested by killing the extractor mid-file and restarting it.

**Every guard is checked by removing it and watching the test fail.** Three tests written
for this work already could not fail, and each was found only by running it against
broken code. On this project a suite that passes the first time has told you nothing yet.

---

## The corpus run

1. Diagnose why the first run stopped — **done: OOM kill of the parent session.**
2. Finish the 27 Nov extraction with a detached, logged runner.
3. `check_tracks`, then known-answer tests for `build_pyramid` and `read_columns`.
4. The other five sessions, roughly 3.2 h at native resolution, resumable and logged per
   session.
5. silero-vad over all six.
6. Hierarchy, sheets and exports.

Do not start step 4 until step 2 has finished once and `build_pyramid` has produced
output. A path that has never run end to end on one session should not be started on six.

---

## Scope

**Not here:** per-dancer pose with identity, the gesture-analysis framework layer
(Kendon, Laban, Eshkol-Wachman, Bressem, NEUROGES), an interactive viewer, gesture
recognition, and transcription. Each is a later project with its own spec.

Two of those have a dependency worth recording now: **Kendon phases and Laban Effort are
both defined on an individual mover's kinematics, and whole-frame quantity of motion
cannot carry either.** Ole's stroke and Lisa's hold sum to a number that is neither. So
the framework layer needs per-dancer pose first, and this pipeline is deliberately built
to stop at proposing excerpts a person annotates — which is also why it needs no pose.

**Settled and not to be relitigated:** audio stays on its own clock; `_crossmodal` takes a
crossing fraction per modality and refuses a single scalar; the sensor-to-dancer map is
swapped on the LoLa day and must be encoded wherever sensors are read, not left in a Word
file.

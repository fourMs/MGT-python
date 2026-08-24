# Hierarchical action segmentation for long recordings — design

For a 2 h 38 min two-dancer improvisation session, and for the corpora like it that
follow. ARJ's requirement, in his words: a videogram of the whole recording with the major
parts marked, actions segmented throughout at several levels as the basis for a student's
gesture analysis, continuous motion features displayed, the ability to zoom from the whole
session down to a single action, and preparation for manual annotation. Parts of it must
rest on audio as well as video, because the question underneath is when an action begins
relative to the sound it makes.

Test material: `27CoLocated.Panasonic.A003C505_231127_DJ0B.mp4`, 1920x1080 at 50 fps,
9513.6 s, **475,680 frames**, AAC stereo at 48 kHz.

---

## What the probe established, before any design

Everything below rests on four measurements taken on 2026-08-24 against a 60 s cut from
the middle of that file. They are the reason the design looks as it does.

**1. Decoding is not the cost.** 3 s to decode 60 s at full resolution; the whole file
decodes in about 8 minutes. At 640 wide it is 2 s. So I/O is irrelevant and any design
that optimises decoding is optimising the wrong thing.

**2. The per-frame Python is the cost, and it scales with pixel area.**

| analysis width | seconds per 60 s of video | extrapolated for the full file |
|---|---|---|
| 1920 | 147 | **6.5 h** |
| 960 | 45 | 2.0 h |
| 640 | 23 | 1.0 h |
| 320 | 8 | 21 min |

**3. Downsampling moves the segment boundaries, and this corpus is not Sound Actions.**
Running `segment_actions` on the envelope from each width:

| width | actions in 60 s | median start shift | worst |
|---|---|---|---|
| 1920 | 16 | — | — |
| 960 | 18 | 160 ms | 2.94 s |
| 640 | 19 | 410 ms | 2.64 s |
| 320 | 17 | 680 ms | 3.64 s |

This project's own parameter sweep found motion onsets *identical* at 160x90 and above, on
365 Sound Actions clips, and **that finding does not transfer.** It was measured on clips
holding one discrete action with a rise from rest, where the onset is a single robust
crossing of a threshold. Continuous improvisation has no rest: boundaries are relative dips
and rises, so an envelope correlating 0.945 with the full-resolution one still relocates
boundaries by up to 3.6 s and changes how many actions there are.

*The general lesson, worth carrying past this design:* a parameter validated on segmented
single-action clips is not thereby validated on continuous recordings, and the difference
is not the resolution but what the measurement is a crossing of.

**4. There are far too many actions to annotate by hand.** 16 in 60 s is one per 3.7 s,
which extrapolates to roughly **2,500** over the session at that level alone. The hierarchy
is not a convenience; without it there is nothing a person can start from.

---

## Architecture

Four modules, each readable and testable alone, and one cached artefact they all read.

```
video ──(once, ~6.5 h)──> _tracks.py ──> feature table on disk
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                     ▼                     ▼
                  _hierarchy.py         _timeline.py           _annotate.py
                 (levels of Action)   (image pyramid)      (.eaf/.TextGrid/.tsv)
                        │                     ▲                     ▲
                        └─────────────────────┴─────────────────────┘
```

`_crossmodal.py` is a fifth, reading the table and a level of the hierarchy, and is
independent of everything except the table.

### 1. `_tracks.py` — extract once, at native resolution

The decision the probe forces: **compute at 1920 wide, once, overnight, and cache.** A
one-off 6.5 h background job buys every zoom level, every re-segmentation and every later
experiment for nothing. Downsampling saves hours once and costs boundary accuracy for as
long as the corpus is used.

`extract_tracks(video, out=None, width=None, resume=True) -> Path`

- decodes in chunks through an ffmpeg pipe, as `extract_pose_landmarks` already does
- writes one tidy table beside the video: `time`, `qom`, `com_x`, `com_y`, `aom_*`
- **resumable by chunk**, because a crash at hour five must not cost hours one to four
- records its parameters in a sidecar so a table can never be read without knowing the
  width, filter and threshold that made it

**Audio is kept on its own clock and is not binned to the frame grid.** Video gives 20 ms
at 50 fps; audio onsets are finer. Forcing both onto one grid quantises away the very
asymmetry the study is about. The table therefore holds video features per frame, and
audio *onset times* as timestamps in a second table, plus an RMS/flux envelope at its own
rate. `_crossmodal.py` compares them at full precision.

*Why not reuse `mg_motion` directly:* it decodes the whole file in one pass, holds the
motiongram arrays in memory, and cannot resume. It stays the right tool for a clip.

### 2. `_hierarchy.py` — levels, from one envelope

Three levels, coarse to fine, each a list of `Action` — the class merged for #373, which
already carries `features` (measured) and `labels` (claimed) and so has somewhere to put
what a level asserts.

| level | what it cuts | how |
|---|---|---|
| **part** | the major sections ARJ wants marked | novelty peaks from `ssm()` computed on a coarse feature stack |
| **phrase** | runs of related activity | `segment_actions` on a smoothed envelope, long `min_duration` |
| **action** | individual movements | `segment_actions` at the working scale, plus `motion_onsets` |

`build_hierarchy(tracks, levels=("part", "phrase", "action")) -> Hierarchy`

`Hierarchy` is a thin container: levels by name, and `children(action)` / `parent(action)`
by time containment rather than by a stored tree, so a level can be recomputed without
invalidating the others.

**Nothing here claims the levels are correct.** They are a starting point for a person to
correct, and the export exists so that correction happens in a tool built for it.

### 3. `_timeline.py` — the image pyramid

Static images, per ARJ's choice. Three zoom tiers, all rendered from the cached table:

- **overview**: the whole session on one page — videogram strip, qom envelope, audio
  envelope, and the part boundaries drawn across all of them
- **part sheets**: one page per major part, phrase boundaries marked
- **action strips**: a contact-sheet-like page per phrase, one row per action

The overview cannot show 475,680 columns, so the strip is decimated with an explicit,
recorded reduction (min/max per column rather than a mean, so a brief spike survives
decimation instead of averaging away). The reduction factor is printed on the figure,
because a decimated strip that does not say so invites a reader to measure timings off it.

### 4. `_annotate.py` — three exports from one tree

ELAN `.eaf` (hierarchical tiers, one per level — the format the nesting actually fits),
Praat `TextGrid` (interval tiers, flattened), and TSV. One writer per format over a common
`Hierarchy`, so a fourth format is a new function and not a new pipeline.

Round-trip matters more than export: a reader that takes a corrected `.eaf` back into a
`Hierarchy` is what makes the automatic segmentation a draft rather than a dead end. Export
first, import second.

### 5. `_crossmodal.py` — action before sound, sound after action

Per action from a chosen level: the motion onset, the nearest audio onset, the signed lead,
and how long audio activity continues past the motion offset. Reported per action and
summarised over a level.

The lesson from report 07 is built in rather than rediscovered: **the two modalities want
different crossing fractions.** Audio has a noise floor a low fraction triggers on, so it
needs a high one; motion has a genuinely still lead-in, so a low fraction catches the first
movement. Applying one fraction to both guarantees one of them is wrong, and the
cancellation the method appears to rest on is an accident of how far the two errors happen
to match. The API therefore takes a fraction per modality and refuses a single scalar.

---

## Testing

Synthetic known-answer throughout, as `micromotion` and `_posetools` do:

- a generated video with movement at known times, so segment boundaries have a right answer
- an envelope with a planted hierarchy — three phrases of four actions — so `build_hierarchy`
  can be checked for containment rather than only for plausibility
- audio with onsets at known offsets from the motion, so `_crossmodal` has a signed lead with
  a known sign and size
- `.eaf` and `.TextGrid` written and re-read, asserting the tree survives the round trip
- resumption tested by killing the extractor mid-file and restarting it

**And every guard checked by removing it and watching the test fail**, because on this
project a suite that passes first time has told you nothing yet.

---

## Scope, and what is deliberately not here

Not in this design: per-dancer separation (needs pose with identity across 475k frames, which
fails silently when dancers overlap), an interactive viewer, and gesture *recognition* —
this produces the segments a student's analysis starts from, not the analysis.

Open for ARJ:

1. **Where does the cached table live** — beside the video on the Seagate, or in the project
   tree? It is ~475k rows, tens of MB, and derived, so it is regenerable but expensive.
2. **Is 6.5 h acceptable** for the one-off extraction, or should the first pass run at 960
   wide (2 h) to get something on screen sooner, with the full pass following? The boundary
   shift at 960 is a median 160 ms, which may be tolerable for a first look and is not
   tolerable for the final analysis.
3. **Which level the student annotates first.** The export can carry all three, but the tier
   they work in decides how many segments they meet.

---

# Addendum: the room, not only the dancers

ARJ, 2026-08-24: the foreground is half the interest. The room they perform in needs
describing too --- visual features averaged either over frames where the dancers are absent
or over enough frames in different positions that the room is what survives, and audio
features that MGT can analyse or hand to ambiscape and musiscape.

This lands on a boundary the four toolboxes have not settled, so that is stated before the
design rather than after it.

## The visual room: a plate, and everything else follows from it

**Take the temporal MEDIAN, not the mean.** A mean over frames with dancers in different
places keeps a ghost of them: every dancer contributes brightness everywhere they were,
faintly, forever. A median over enough such frames removes them outright, because at any
pixel the dancers are a minority of the samples. `mg_pixelarray` averages, which is the
right tool for the motion-history look it was built for and the wrong one here.

    room_plate(video, n=2000, method="median") -> np.ndarray

Frames sampled across the whole session rather than from one stretch, because a plate built
from ten minutes describes the lighting of ten minutes.

**Then the plate gives the occupancy signal for free.** Each frame's departure from the
plate is how much of the room is currently covered by something that is not the room ---
which is a presence measure that needs no pose estimation and cannot silently mis-identify
a dancer, because it never identifies anyone. `mg_subtract` already does the subtraction.

    occupancy(video, plate) -> track alongside qom

That, in turn, answers ARJ's first strategy without needing it as a separate path: **the
emptiest frames are the ones with the least departure**, so "average the frames where the
dancers are absent" becomes a selection over a measure the plate already provides. Iterate
once --- plate from a blind sample, then plate again from the emptiest 10 % --- and the
second plate is the room with the dancers gone rather than merely diluted.

*This is the book's figure/ground thesis as an algorithm:* the background is what does not
change, and the foreground is the difference from it. Report 20 makes the same move on a
dwelling's sound floor.

**Cost: near zero, if it rides along.** The plate needs a few thousand sampled frames, not
475,680, and the extraction pass is decoding every frame anyway. Occupancy does need a
second pass, but **occupancy tolerates the downsampling that segmentation does not** ---
it is a slow presence signal, not a boundary crossing, so 320 wide and 21 minutes is
sufficient and the 3.6 s boundary shift measured above is irrelevant to it. That asymmetry
should be stated wherever both are configured, or someone will reasonably assume one width
serves both.

## The audio room: hand it across, do not reimplement it

MGT's `MgAudio` already gives spectrogram, MFCC, chromagram, HPSS, tempo and descriptors,
and that is enough for anything staying inside MGT. For the room as a *soundscape* ---
level, spectrum, ecology indices, tonality, the noise floor --- ambiscape owns the
vocabulary and the fix is small, because the crossing point already exists.

`_soundscape.py` declares itself the one crossing and states the principle. Today it takes
an ambiscape *session folder*. It needs to take a video:

    soundscape_features(video) -> MgFeatures     # extract WAV, open_recording, extract_session

`ambiscape.io.open_recording` opens a single file as a one-take session, so no folder
layout is needed --- this is a WAV export and one call. From there `ambiscape.music` reaches
musiscape for anything musical, which is the existing route and needs nothing new.

**The room tone specifically** is a low percentile per band over time, not a mean: the
quietest tenth of each band across the session is the floor the room sits at, and the mean
is dominated by whatever happened in it. That is ambiscape's `floor` concept and report
20's method, and it belongs on the ambiscape side of the crossing.

## The boundary this sits on, which is ARJ's to settle

**`ambiscape.vision` already computes per-frame visual features** --- `luma`,
`frame_features`, `frame_delta`, `frame_series`, `summarize_vision` --- while the stated
rule is that MGT owns pixels and ambiscape owns samples. Sound Spaces' own notes flag
`ambiscape.vision.frame_delta` as a seventh copy of the frame difference that a six-copy
audit missed. This requirement lands on exactly that seam.

For this design I propose the split that avoids duplicating work rather than the one that
settles the principle:

- **MGT makes the plate**, because MGT is already decoding the video and a second decode
  through another toolbox costs another pass over 475,680 frames.
- **ambiscape may describe it**, because the plate is a single image: `frame_features(plate)`
  is one call on one array with no decoding at all, and it gives the room ambiscape's
  descriptor vocabulary so the visual and audio descriptions of the room are in the same
  language.

That is a crossing of exactly the kind `_soundscape.py` was created to be, and it does not
decide who owns per-frame visual features in general. **[ARJ]** that question is the
open toolbox-alignment item and should be settled deliberately, not by whichever design
touches it next.

## What this adds to the plan

One module, `_room.py`, holding `room_plate`, `occupancy` and the emptiest-frame selection;
one extension to `_soundscape.py` to accept a video; and one new track in the feature table.
The renderer gains the plate as a panel on the overview page and occupancy as a strip
beneath qom, so foreground and background are read against each other rather than
separately --- which is the point.

Testing follows the same rule as the rest: a synthetic video with a known static background
and a moving rectangle, where the plate has a right answer pixel for pixel and occupancy has
a known duty cycle.

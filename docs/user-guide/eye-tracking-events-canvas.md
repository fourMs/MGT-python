# Eye Tracking, Events and the Canvas

Three additions from a study of live painting to music, each of which is general: a wearer's eye
tracker put on the video's clock, events of one stream tested against events of another, and the
painting itself measured as a time series.

```python
import musicalgestures as mg
```

---

## Eye tracking on the video's clock (`eyetracking()`, `gazegrams()`, `eyetracking_timeline()`)

A Pupil Labs Neon records a scene video, gaze at 200 Hz, pupil size, blinks, fixations, saccades
and head motion, and Pupil Cloud exports all of it with absolute nanosecond timestamps. None of that
is on the clock of the video you will analyse. `eyetracking()` reads the export and places this
video on the recording clock by naming the event it starts at:

```python
v = mg.MgVideo("scene_music.mp4")                      # a cut of the scene camera
frames = v.eyetracking("pupil_cloud_export/", start="Music begins")
frames.columns
# frame, time, gaze_x, gaze_y, gaze_az, gaze_el, gaze_vel, worn, fixation, fixation_id,
# saccade, saccade_id, blink, blink_id, pupil_left, pupil_right, pupil_mean,
# head_gyro, head_acc, head_roll, head_pitch, head_yaw
```

One row per frame, so it sits beside the motion data from `motion()` directly. Gaze inside blinks
is missing rather than trusted; pupil size is masked around blinks and interpolated; frames with
no sample stay NaN. Then:

```python
v.gazegrams()             # where the wearer looked per second, oriented like the motiongrams
v.eyetracking_timeline()  # gaze velocity, fixation and blink rates, pupil, head rotation
from musicalgestures import eyetracking_rates, head_turns
rates = eyetracking_rates(frames, v.fps)          # per-second rates, events counted once
turns = head_turns(frames, v.fps, threshold_deg=25)   # spans where the head is turned away
```

`head_turns` reads the IMU yaw against a 60 s running median, because an absolute heading means
little to a wearer whose "straight ahead" is wherever the work is; the spans are not attributed ---
the scene video says what was looked at. The standalone functions (`read_pupil_export`,
`pupil_to_frames`, `eye_events`, `gazegram`) work without an `MgVideo`.

---

## Events against events (`event_alignment`, `event_xcorr`)

`_alignment` and `_correlate` compare envelopes. `event_alignment` compares *events*: how far
each event of one stream falls from the nearest event of another, and on which side, against
references placed uniformly at random over the recording.

```python
from musicalgestures import event_alignment, event_xcorr
strokes = [a.start for a in v.actions_from_motion(envelope=hand_speed, fs=v.fps)]
notes = onset_times                                    # e.g. from librosa
a = event_alignment(strokes, notes, duration_s=v.duration, tolerance_s=0.25)
a.verdict            # "attract" | "avoid" | "chance"
a.median_nearest_s, a.surrogate_median_s, a.p_closer, a.p_farther
a.frac_reference_first                                 # share of strokes where the note came first
lags, r = event_xcorr(strokes, notes, v.duration, bin_s=0.1, max_lag_s=3)
```

Both directions of departure from chance are findings. On the painter--pianist session this was
written for, strokes *avoided* note onsets in the free improvisation (painting in the piano's
silences), sat at chance when the painter led, and *attracted* them when the pianist led ---
three takes that no envelope correlation had separated.

`cross_recurrence(x, y, fs)` in `_correlate` is the envelope-level companion: recurrence rate at a
fixed radius quantile, determinism, mean line length and the diagonal recurrence profile, each
against circular-shift surrogates, so two smooth series are not mistaken for a coordinated pair.

---

## The painting as a time series (`painting()`)

Every other tool follows the performer. `painting()` follows the work. Given a video --- or a
crop --- that frames the canvas, it reduces each second to one frame from which the painter's hand
has been removed by a temporal median, and measures that frame:

```python
canvas = mg.MgVideo("part1_canvas.mp4")               # a fixed crop of the canvas
fig = canvas.painting(reference_s=5)                  # the first 5 s are the initial canvas
canvas.painting                                       # DataFrame, one row per second
canvas.colourgram_image                               # hue down, time across
fig.data["composition"]["symmetry_lr"], fig.data["palette"]
```

Per second: painted share and a monotone coverage that ignores occlusion, chromatic share, the hue
histogram (the *colourgram*, the painting's own gram), warm and cool shares, edge density as
structural detail, and the composition --- paint centre and spread, left--right symmetry, edge
orientation and anisotropy. Per minute, the dominant colours. The standalone
`painting_content(video)` and `composition(frame)` do the same without an `MgVideo`.

The canvas must be fixed in the frame. A head camera needs rectification first, which is a harder
problem and not solved here.

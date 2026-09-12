# People on stage and camera motion

A concert video answers two questions a motion measure cannot: *how many people are
performing*, and *is the picture moving because they move or because the camera does*.
Both are read from the video alone.

## Counting who is on stage

```python
import musicalgestures as mg

det = mg.detect_people("concert.mp4", fps=1.0)          # YOLO person boxes, once per second
mg.performer_count(det, start_s=378, end_s=668)          # {'estimate': 1, 'median': 1, 'max': 1, ...}
```

A person detector finds the audience too: heads and shoulders in the lower part of the
frame, cut off by the bottom edge. Performers stand or sit on a raised stage, so their
heads are in the upper half; `on_stage` keeps those boxes and drops the rest. Because an
operated camera rarely shows everyone at once, the span statistic is a high percentile of
the per-frame counts (the wide shots), reported with the median and maximum so the
variation in framing stays visible.

## Camera cuts and pan/tilt/zoom

```python
cam = mg.camera_motion("concert.mp4")                    # on a 2 fps proxy, about a minute per hour
cam["summary"]                                           # {'still': 0.86, 'moving': 0.14, 'cut': 0.002}
cam["cuts"], cam["shots"]                                # cut times, spans between cuts
mg.still_runs(cam, 378, 668)                             # the framings: still runs between moves and cuts
mg.camera_state_at(cam, [400.0, 401.0])                  # 'still' | 'moving' | 'cut'
```

Between consecutive frames of the proxy, ORB features and a partial-affine RANSAC fit give
a translation, a scale change and an inlier count. Consistent geometry with a shift or a
zoom is a camera move; no consistent geometry with a large change of the picture is a cut.
Two uses follow:

- **Motion without the camera.** Mask the seconds where the camera moved or cut before
  summarising quantity of motion, a motiongram or an envelope; otherwise a pan is the
  biggest "gesture" in the piece.
- **Counting per framing.** Pass the camera analysis to `performer_count(det, a, b,
  camera=cam)` and the unit becomes a *framing*, a still run of at least ten seconds. Each
  framing gets the 75th percentile of its counts and the widest framing is the estimate. On
  a concert with a moving camera this was exact for a soloist, a duo and a five-piece band
  where the plain percentile counted the audience in the band's wide shot; a choir stays
  under-counted because singers occlude each other.

## Lecture halls and long files

A lecture or defence recording differs in two ways. There is no raised stage, so pass
`head_below=1.0, cut_head_below=1.0` to switch the audience filter off; and the widest framings
show the hall and the projected slides, whose figures are not the speakers, so count the *typical*
framing: `performer_count(det, a, b, camera=cam, stat="typical")` takes the median over framings
instead of the maximum. On a defence this gave 1, 1, 2, 2 for the lecture, the introduction and
the two opponent discussions.

A 36 GB 1080p50 file decodes on the GPU by passing ffmpeg input options through:
`detect_people(video, ffmpeg_input_args=["-hwaccel", "cuda"])` and
`camera_motion(video, ffmpeg_input_args=["-hwaccel", "cuda"])`.

Both analyses cache well: keep the proxy and the detections next to the recording and the
counts for any span are instant.

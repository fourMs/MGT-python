# Multi-shot

Many moments of one recording in a single picture: a chronophotograph.

The room is recovered as a [plate](_plate.md) — what was there before anybody came in —
bodies are cut out of frames spread through the recording, and all of them are laid back
onto it. One image then carries where somebody was, how they were shaped, and how far apart
the moments were. It answers nothing a motiongram answers and shows something no gram does.

```python
import musicalgestures as mg
import cv2

picture, plate = mg.multishot("session.mp4", n_bodies=8, start=1932, end=4478)
if picture is not None:
    cv2.imwrite("rehearsal_multishot.png", picture)
```

## Frames are chosen for separation, not at intervals

Evenly spaced frames put bodies on top of each other as often as not, and two overlapping
silhouettes read as one smear rather than as two moments. Candidates are scored by how far
each sits from every body already placed, and the greediest spacing wins.

**More bodies is not simply better.** A room is finite, so each body after the first takes
the emptiest remaining spot and the spots run out. Past a dozen or so they overlap whatever
the selection does. Eight suits a studio; a long section with a lot of travel takes more.

## Give it a section, not a whole recording

A whole session is usually mostly setup, and the picture then fills with people standing
about rather than with the work. `start` and `end` take seconds.

## What it cannot do

- **It composites whoever is in shot.** Somebody sitting at a laptop differs from the room
  like anybody else. Where that matters, mask the region or restrict the span.
- **It inherits the plate's faults exactly.** A prop that stood in the room through a break
  appears here as a hole or a ghost. `room_plate` spreads its sampling and warns when it
  cannot, but heed the warning.
- **Figure-ground separation is the limit.** A dark costume against a dark background barely
  differs from the plate, and the silhouette goes semi-transparent. Rooms differ enormously
  in how well this works, and it is the room and not the setting that decides.

::: musicalgestures._multishot

# Multi-shot

Many moments of one recording in a single picture: a chronophotograph.

The room is recovered as a [plate](_plate.md) — what was there before anybody came in —
bodies are cut out of frames spread through the recording, and all of them are laid back
onto it. One image then carries where somebody was, how they were shaped, and how far apart
the moments were. It answers nothing a motiongram answers and shows something no gram does.

As a method, which is how the rest of the object API reads:

```python
import musicalgestures as mg

video = mg.MgVideo("session.mp4")
video.multishot(n_bodies=8, start=1932, end=4478)   # -> MgImage
video.plate(width=1920)                             # the room on its own -> MgImage
```

Or as a function, when the arrays are wanted rather than a file:

```python
picture, plate = mg.multishot("session.mp4", n_bodies=8, start=1932, end=4478)
```

The method raises `ValueError` when no frame held a body of a plausible size, rather than
handing back a picture of an empty room — which would look like the recording was empty
instead of like the size bounds matching nothing.

## It absorbed `stroboscope()`

MGT had chronophotography before this, as `stroboscope()`: silhouettes at **evenly sampled**
times on a **mean average** frame, tinted by time. Having two functions make the same picture
two ways meant a reader had to know which — so they are one, and `stroboscope()` is a
deprecated wrapper that delegates here until 2.0.

Both ways survive:

| what `stroboscope()` did | how to ask for it now |
|---|---|
| even sampling | `select='even'` |
| mean-average background | `background='average'` |
| time tint | `colorize=True` |
| flat or first-frame ground | `background='black' / 'white' / 'first'` |

```python
video.multishot(select='even', background='average', colorize=True)   # the old picture
video.multishot()                                                    # the new default
```

**The defaults are an opinion, and worth stating.** Even sampling is what makes two moments
land in the same place, and a mean average keeps a faint ghost of everyone who crossed —
which is exactly what a median plate exists to remove. Even spacing still answers a real
question, though, and it is the one a time tint belongs to: how a body looked at regular
instants, the Muybridge reading. Spatial separation answers where it went.

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

## It assumes a subject that moves through space

Separation is spatial, so a subject who stays put gives it nothing to separate. On a seated
pianist it returns heads and hands stacked in one place: the static torso is part of the
room by then, and only the moving parts survive the mask. The picture is reflecting what the
recording contains, which is the intended behaviour — but it is an overlay of moving limbs
rather than a chronophotograph, and worth knowing which of the two you are looking at.

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

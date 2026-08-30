# Room and occupancy

The empty room, how much of the frame anybody fills, and which pixels change whatever is in
front of them.

![The room, and how restless each pixel is](../images/examples/room_and_restless.png)

Left: the room recovered as a per-pixel median over sampled frames. Median and not mean,
because a mean keeps a faint ghost of everyone who crossed, and subtracting a ghost leaves
holes shaped like people.

Right: how restless each pixel is. The bright region here is not the video-call screen on the
left of the room but a table on the right, with a laptop and a seated researcher—in
shot for the whole recording, and counted by quantity of motion like anybody else. On this
corpus that non-dancer motion was 2.8 to 7.1 per cent of the total.

Occupancy answers what motion cannot: somebody standing still has no motion and plenty of
occupancy.

## The frames the plate is built from must be spread over the recording

The median is taken twice: once over a blind sample, then again over the emptiest of
those frames, which tightens the plate where passing traffic left residue.

The catch is that the emptiest frames are not spread through a recording. They cluster in
whatever stretch nobody was working—a break, a setup, a pack-down—and anything
standing in the room during that stretch enters the plate as though it were furniture.

On one recording here a stepladder stood in the middle of the floor for about ten
minutes of a two-hour session. Those frames were the emptiest by a wide margin, all of the
refinement's frames came from them, and the ladder became part of "the room". Every
occupancy figure afterwards then read that region as occupied 18.6 per cent of the time
--- as though a body were standing there—because the plate expected a ladder that was
usually absent.

So the second pass takes the emptiest frame from each of `k` equal stretches rather than the
emptiest `k` overall. The choice is still made on emptiness; it simply cannot all come from
one place. `stratify=False` restores the older behaviour, and `plate_spread` reports how
much of the recording the chosen frames span—`room_plate` warns below half.

```python
plate, used = mg.room_plate("session.mp4")
mg.plate_spread(used, n_frames)      # near 1 is spread, near 0 is one stretch
```

## A refinement that changes the room is concentrating, and backs off

What the second pass cannot do is remove somebody who stood in one place for most of the
recording: no selection of frames recovers a room that no frame shows. Worse, on material
where the subject rarely leaves—standstill recordings—the frames most like the first
plate are exactly the ones with the subject in place, and re-taking the median over them
makes the subject solid where the full sample had washed them out. On a 2012 standstill
performance recording the refined plate acquired a performer standing solidly in an
otherwise empty room.

The failure is detectable at the output. Under a median first pass the kept frames are the
ones that agree with the plate, so a refinement that changes the room materially is
concentrating, not cleaning. `room_plate` measures that change and returns the unrefined
plate with a warning when it exceeds `max_refine_change` (default 0.02 of the frame—above
a body's residue and below a body). On material where the subject never leaves, pass
`refine=False` and skip the second pass altogether.

::: musicalgestures._plate

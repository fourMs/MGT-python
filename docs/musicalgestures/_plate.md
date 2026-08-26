# Room and occupancy

The empty room, how much of the frame anybody fills, and which pixels change whatever is in
front of them.

![The room, and how restless each pixel is](../images/examples/room_and_restless.png)

Left: the room recovered as a per-pixel **median** over sampled frames. Median and not mean,
because a mean keeps a faint ghost of everyone who crossed, and subtracting a ghost leaves
holes shaped like people.

Right: how restless each pixel is. The bright region here is not the video-call screen on the
left of the room but a table on the right, with a laptop and a **seated researcher** --- in
shot for the whole recording, and counted by quantity of motion like anybody else. On this
corpus that non-dancer motion was 2.8 to 7.1 per cent of the total.

Occupancy answers what motion cannot: somebody standing still has no motion and plenty of
occupancy.

::: musicalgestures._plate

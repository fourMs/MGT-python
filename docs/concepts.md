# Concepts

The toolbox is organised around a small set of ideas from music and movement research.
This page explains them in plain words, so that the function names make sense before you
call them, and so that readers from different fields can see where their own literature
connects. Everything here deepens gradually: read to where your question is answered and
stop there.

## Two rows, three levels

The toolbox describes movement at three levels. Motion is continuous displacement in
space over time, and is what the tools measure: quantity of motion, optical flow,
landmark trajectories. An action is a segment of motion with a beginning and an end,
such as a drum stroke or a reach for a cup. A gesture is an action carrying meaning,
and meaning is not a property of the signal, so gestures are interpreted rather than
detected.

Bodies that are not moving need the same three levels, and the words are position,
posture, and pose.

Position is the measured level: where a point is in space. A pose-estimation model
returns positions, for example 33 landmark coordinates per frame, and nothing more.
The name "pose estimation" is the computer-vision convention and is kept in function
names such as `pose()` and `posegram()`; in the terms used here, what those functions
return are landmark positions.

Posture is a configuration: how the parts of the body are placed relative to each
other, with the location in the room taken out. Standing, sitting, and kneeling are
postures, and so is the shape of a hand on a keyboard. Turning positions into a
posture requires a choice of segments and reference frame, which is what
`pose_center()` does when it removes absolute position and keeps the relative
configuration. A posture is to position what an action is to motion: a chunk that a
person would name.

Pose is a posture with meaning, typically assumed for an observer. A static thumbs-up
is a pose, and lifting the hand to show the thumb is a gesture; a breaker's freeze is
a pose timed to the music. Like gestures, poses have to be interpreted, so the toolbox
measures positions, segments postures, and only ever proposes poses.

| | measured | segmented | interpreted |
|---|---|---|---|
| dynamic | motion | action | gesture |
| static | position | posture | pose |

The two rows run through the whole toolbox. The measured level is quantitative and
automatic. The segmented level is where analysis choices enter: a threshold cuts
motion into actions (`actions_from_motion()`), a stability criterion cuts landmark
trajectories into postures (`postures_from_pose()`). The interpreted level belongs to
the human analyst, and the toolbox supports it with annotation tools and with labels
that recognisers may *propose* on actions and postures, never decide.

Two neighbouring fields use these words differently, and the difference is worth
knowing when reading their literature. Movement science treats posture as an actively
regulated process, which is why the balance functions in `_posture` quantify the
small movements of holding a posture rather than the posture itself. And in Movement
Pattern Analysis, posture means a movement of the whole body as opposed to a body
part (Lamb 1965), a dynamic sense unrelated to the static one used here.

## Quantity of motion, and what it can claim

Quantity of motion (QoM) is the toolbox's basic measured signal: how much motion
there is at each moment, computed from pixel differences or from landmark
trajectories. It is deliberately simple, and its limit should be stated with it: QoM
measures activation, not quality. A dancer using the whole body reads high in QoM
whether the movement is heavy or weightless, bound or free, and nothing in the number
distinguishes those. Where the analysis needs quality rather than amount, QoM is the
substrate and a human judgement, or the effort layer below, sits on top of it.

## Ways of looking

The oldest layer of the toolbox turns video into images made for human looking:
average images, motion videos, motiongrams, videograms, history videos, and the
space-time displays. These are not measurements that happen to be visible; they are
instruments for a qualitative practice, in which the researcher looks at a recording
from a different temporal or spatial perspective and sees something the running video
hides. A motiongram compresses an hour of dance into one image in which a lifted arm
is a visible streak, which is a different kind of claim than a number, and often the
more useful one. The quantitative and qualitative approaches are both first-class
here: computation supplies contours and pictures for the looking, and does not
replace it.

## Movement quality: the effort layer

Laban Movement Analysis is an observational language for movement quality, and its
effort factors (time, weight, space, flow) name what QoM cannot: how a movement is
performed rather than how much of it there is. The toolbox's effort layer computes
continuous, mover-relative indices as reading aids for that qualitative system. The
indices are scaled to the mover's own range rather than to absolute values, they
output contours rather than categories, and anything affective remains the analyst's
inference. Video alone under-determines some factors (weight especially wants dynamic
and physiological channels), so the weight index should be read as a kinetic proxy.

## Pose estimation, and swapping detectors

Several detectors can supply landmark positions: MediaPipe, the YOLO family, OpenPose
models, RTMPose. They differ in skeleton layout, and the toolbox recognises the
topology by landmark count, so the higher-level analysis is the same whichever
detector produced the data. What every detector returns is positions in the sense
above; postures and poses are made from them by the segmentation and interpretation
layers, not by the detector. Detector output also trembles, and the posture
segmentation is built to tell a detector trembling from a body moving.

## Where your literature connects

- **Music research.** The motion/action/gesture levels come from the musical-gestures
  literature (Jensenius, Wanderley, Godøy & Leman 2010; Jensenius, *Sound Actions*,
  MIT Press 2022). Godøy's coarticulation work ties postures to action chunking as
  goal postures. The visualisation tradition descends from the motiongram work
  (Jensenius 2007).
- **Psychology.** What this toolbox calls posture is the static configuration your
  literature measures as the bodily channel of expression (de Gelder 2006); what it
  calls a pose corresponds to a deliberately produced display, as in posed versus
  spontaneous expressions. Annotation, co-occurrence, and the segmentation layers are
  the bridge from video to codeable units.
- **Human movement science.** The countable, configurational sense of posture used
  here matches ISO 11226 ("position of body segments and joints"); postural control
  and sway in your sense live in the balance functions, which quantify the dynamics
  of maintaining quiet stance (Prieto et al. 1996). Landmark trajectories from video
  are positions in the kinematic sense and can feed your own pipelines directly.
- **Computer science.** Pose estimation output sits at the measurement level;
  recognition hierarchies (action primitives, actions, activities) map onto the
  segmented and interpreted levels, with the caveat that this toolbox keeps
  segmentation and recognition deliberately apart, and treats meaning as out of scope
  for classifiers.

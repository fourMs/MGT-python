# Position, posture, and pose

*Draft for arj.no, written 2026-09-01. The review behind it is in
`plans/2026-09-01-position-posture-pose-terminology.md`; British spelling throughout,
except inside quotations.*

---

In [Sound Actions](https://direct.mit.edu/books/oa-monograph/5459/Sound-ActionsConceptualizing-Musical-Instruments)
I differentiate between motion, action, and gesture. Motion is continuous displacement
in space over time, and is what our tools measure. An action is a segment of motion
with a beginning and an end, such as a drum stroke. A gesture is an action carrying
meaning, and meaning is not something a camera can see. This three-level thinking has
served us well in the [Musical Gestures Toolbox](https://github.com/fourMs/MGT-python),
where segmentation and recognition are now kept deliberately apart.

But what about bodies that are not moving? Working on the toolbox this week, I needed
the static counterpart, and I have to admit that I could not remember which way I had
set up the three words myself. Was pose the neutral snapshot and posture the meaningful
stance, or the other way around? I even suggested the swap before checking my own book.
That confusion seemed worth taking seriously, so we ran a small literature review
across computer vision, robotics, biomechanics, ergonomics, psychology, HCI,
linguistics, dance, animation, and music research, to see how the fields actually use
the words.

The short answer is that the fields disagree with each other, but not about the
question that matters. Computer vision has claimed "pose" for the bottom level: a pose
in [pose estimation](https://arxiv.org/abs/1812.08008) is a set of joint keypoints,
and in robotics it is position plus orientation, with no meaning anywhere in sight.
Movement science, for its part, refuses to treat posture as static at all: from
[Massion](https://pubmed.ncbi.nlm.nih.gov/7895011/) to
[Horak](https://academic.oup.com/ageing/article/35/suppl_2/ii7/15654), posture is an
actively regulated process, and posturography measures the constant micro-motion of
standing "still". And in Warren Lamb's movement analysis, posture is a movement of the
whole body as opposed to a body part, which is the opposite polarity again.

Yet on the question of which word carries meaning, the evidence points one way.
Dictionaries define a pose as a posture "assumed for artistic effect", often "to
impress or deceive". Psychology contrasts posed with spontaneous expressions.
Animation is built on key poses that carry the composition while the in-betweens carry
the motion. Ballet's codified positions of the feet combine into the poses of the
classical dance. A breaker ends a round with a freeze, a musically timed concluding
pose. Nobody, in any field we checked, uses posture as the more communicative of the
two words. And [Rolf Inge Godøy's](https://pmc.ncbi.nlm.nih.gov/articles/PMC8725797/)
goal postures, the effector shapes that anchor coarticulated action chunks, tie
posture to the action level from the music side.

So the book had it right, and the table looks like this:

| | measured | segmented | interpreted |
|---|---|---|---|
| dynamic | motion | action | gesture |
| static | position | posture | pose |

Each static term is the time-frozen counterpart of its dynamic partner, and the
apparent clash with computer vision resolves itself nicely: what a pose-estimation
model returns is a set of landmark positions, so the loanword lives at the position
level, and the meaningful sense of pose remains free one level up.

This is now implemented in the toolbox. A new posture layer cuts landmark trajectories
into held configurations, using the criterion sign-language phonology settled long ago
in the [Movement--Hold model](https://en.wikipedia.org/wiki/American_Sign_Language_phonology):
a hold is a stretch in which everything remains stationary, so stillness is judged on
the fastest-moving part of the body rather than on the average. Configurations are
body-normalised, which means a dancer walking across the stage in a held T-shape reads
as one posture, since position is not posture. Recurring configurations can be grouped
into the key postures of a recording, and a pose can be proposed by example, as a
label attached to a posture. Proposed, not detected: like gestures, poses need to be
interpreted to be understood, and that remains the human's job.

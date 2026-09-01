# Position, posture, and pose: what seven fields do with the words

Written 2026-09-01 at ARJ's request. The toolbox now separates motion, action, and
gesture on the dynamic side, and the question is what the matching static triad should
be. `Sound Actions` (pp. 68–69) pairs position with motion, posture with action, and
pose with gesture. An alternative pairing, with pose parallel to action and posture
parallel to gesture, was on the table. The review below checked computer vision,
robotics, biomechanics and medicine, ergonomics, psychology, HCI, linguistics, gesture
studies, sign-language linguistics, dance, theatre, animation, and music research.
Definitional claims were verified against fetched abstracts or full texts; the
sources list at the end links the load-bearing ones.

## What Sound Actions already says, and does

The book's section "Position, Posture, and Pose" (pp. 68–69) defines position as the
measurable location of a body or body part in space, posture as how a person holds
their body ("posture is related to the position in a similar way that action is
related to motion"), and pose as a posture with a meaning-bearing component
("gestures are dynamic while poses are static"; a static thumbs-up is a pose, a
dynamic one a gesture). Chapter 12 then uses the scheme in earnest: "key postures",
"posture recognition" as spatial thresholding, a "posture classifier" in Dance
Jockey, and the closing analogy that a posture-based instrument is like a piano
while an action-based instrument is like a violin. The book is internally
consistent, with posture at the segmentation level and pose at the meaning level.

The toolbox has, without anyone deciding it, already followed the book. Some 20
public functions carry `pose` in the computer-vision loanword sense (raw landmark
extraction), while the prose of `_posetimeline` and `_posegram` uses posture for the
readable configuration at an instant: a held posture reads as a flat band, filling
detection gaps would invent posture, `posture_traces`. And `pose_center()` /
`normalise_poses()` are operationally the book's position–posture distinction:
subtract absolute position, normalise by the body, and what remains is posture.

## What each field does with the words

### Computer vision and robotics

Pose is claimed, irrevocably, for the bottom level. In human pose estimation the
word means the per-frame set of joint keypoints and nothing more: DeepPose
formulates "pose estimation... as a DNN-based regression problem towards body
joints" (Toshev & Szegedy 2014), OpenPose detects "the 2D pose of multiple people in
an image" as keypoint sets (Cao et al. 2019), and BlazePose returns 33 landmark
coordinates. In robotics, ISO 8373 defines pose as the combination of position and
orientation of a rigid body. No meaning component exists in either sense.

Posture, by contrast, is the field's word for a named static class one level up.
The fall-detection and monitoring literature classifies postures such as standing,
sitting, lying, and bending, typically on top of pose estimation (Iazzi et al.
2021). The canonical recognition hierarchies are purely dynamic: Poppe (2010),
following Moeslund et al. (2006), runs action primitive, action, activity, and
treats pose estimation as a regression stage outside the semantic ladder. Aggarwal
& Ryoo (2011) put gesture at the atomic bottom, below action, which is the inverse
of our usage and a reminder that no external taxonomy settles this.

The hand-gesture literature is the interesting complication. There the established
static/dynamic pairing is posture versus gesture: "static hand gestures or
postures" (Pavlovic et al. 1997), LaViola's 1999 survey of "hand posture and
gesture recognition", and Oudah et al. (2020): "posture focuses more on the shape
of the hand whereas gesture focuses on the hand movement". A static command hand
shape is called a posture there, so HCI pairs posture directly with gesture. Note,
though, that these postures are meaning-neutral shape classes for a recogniser; the
meaning lives in the mapping, not in the word.

### Movement science: biomechanics, motor control, ergonomics, medicine

Motor control will not certify posture as static. From Massion to Horak the word
names an actively regulated process: "postural orientation involves the active
alignment of the trunk and head" (Horak 2006), and postural control "involves
controlling the body's position in space" (Shumway-Cook & Woollacott). Posturography
is the sharp case, since its entire signal is micro-motion, the centre-of-pressure
sway during nominally quiet standing (Prieto et al. 1996; Duarte & Freitas 2010).
The field measuring posture measures movement.

The countable sense is the honest static one. ISO 11226 defines a working posture
as the "position of body segments and joints while executing a work task" and a
static working posture as one maintained longer than 4 s; the AAOS 1947 definition
is "the relative arrangement of the parts of the body". RULA and REBA score held
segment configurations for load. Position, meanwhile, is cleanly the point term
everywhere: robotics defines a configuration as "the positions of all points"
(Lynch & Park 2017), and proprioception is the sense of position and movement.
Pose barely exists in biomechanics except inside the imported compound "pose
estimation"; Cronin (2021) uses scare quotes for it and never writes posture at
all. The word arrives semantically empty.

### Psychology and human factors

Posture is consistently the meaning-neutral channel. De Gelder's emotional
body-language work uses posture for the static configuration and gives the meaning
to "expression" and "body language"; her 2015 review uses posture 9 times and pose
0. Pose is the marked, intentional term: psychology's standard opposition is posed
versus spontaneous expressions, where to pose is to produce a display deliberately
for an observer. The power-posing literature equates the referents ("physical
postures that express power and dominance (power poses)", Ranehill et al. 2015)
but keeps the micro-pattern: posture names the configuration, pose and posing name
the act of assuming it. Dictionaries agree, and even define the words in terms of
each other in one direction: position is a place or arrangement, posture is "a
position of a person's body or body parts", and a pose is "a sustained posture;
especially: one assumed for artistic effect" (Merriam-Webster), "often assumed in
an attempt to impress or deceive" (American Heritage). The lexical hierarchy runs
position, then posture, then pose.

### Dance, theatre, animation

Pose is the meaning-carrying static term wherever performance is involved. Ballet
codifies elementary positions of the feet and arms (Beauchamp, via Rameau 1725)
and composes them into the poses of the classical dance, croisée, effacée, the
arabesques (Vaganova 1934), so position and pose already sit at two levels there.
Animation's pose-to-pose principle (Thomas & Johnston 1981) has the key poses carry
the composition and emotion while the in-betweens carry the motion, which digital
animation inherited as keyframes; Godøy cites exactly this analogy. Theatre
contributes the tableau, a group of actors frozen in poses that make a picture,
and breaking contributes the freeze, a named, intentional, musically timed
concluding pose. One caution: ballet's positions are codified and meaningful, so
our measurement-level use of position is deliberately narrower than dance usage.

### Gesture studies, sign language, linguistics

Gesture studies' own static term is neither pose nor posture but hold: the gesture
phrase runs preparation, stroke, holds, retraction (Kendon 2004; Kita et al.
1998), and a held thumbs-up is an emblem on Kendon's continuum (McNeill 1992).
Sign-language linguistics offers the most rigorous static/dynamic decomposition on
record: Stokoe's simultaneous parameters (handshape, location, movement) and
Liddell & Johnson's Movement–Hold model, where holds are segments in which "all
aspects of the signer's configuration remain stationary". Linguistic typology has
posture verbs as an established technical term for sit, stand, and lie (Newman
2002; Ameka & Levinson 2007), and pose does not occur as a technical term at all.

Warren Lamb's tradition is the one outright collision: in Movement Pattern
Analysis, posture is a movement consistent through the whole body and gesture a
movement of a body part, with the Posture–Gesture Merger as the diagnostic unit
(Lamb 1965). Lamb's posture is dynamic. Any definition of posture as static should
footnote him.

### Music research

The dynamic ladder is well rooted (Jensenius, Wanderley, Godøy & Leman 2010;
Cadoz & Wanderley 2000, whose taxonomy is wholly action-based with held body
configurations only as a residual of the ancillary category). The strongest
independent support for posture at the action level is Godøy's coarticulation
work: "goal-points are goal-postures in the form of the position and shape of the
effectors... at certain important moments in the flow of musical sound" (Godøy
2014), imported from Rosenbaum's posture-based motion planning and explicitly
compared to animation keyframes (Godøy 2021). Performance science uses playing
posture for the sustained task configuration and measures it objectively, which
pushes against defining posture as subjective. Pose has little terminological
standing in academic music research, where NIME papers use it only in the CV
sense; its allies are vernacular and adjacent, the breaking freeze above all, plus
the audience stilling response (Upham et al. 2024) as evidence that meaningful
stillness is a real phenomenon rather than an empty cell in a table.

## The collisions, tabulated

| word | claimed elsewhere as | collides with our use? |
|---|---|---|
| position | point coordinates (kinematics, robotics); codified configurations in ballet | no; ballet's richer use needs one sentence |
| posture | regulated control process (motor control); whole-body movement (Lamb 1965); static hand shape paired with gesture (HCI) | yes, twice: footnote Lamb, and state the configurational (ISO 11226) sense; HCI's pairing is at a different level |
| pose | per-frame keypoint set (CV); position + orientation (ISO 8373) | yes, and unavoidably: the toolbox's own `pose_*` functions use the CV sense |

## Weighing the two pairings

Does anything support pose parallel to action and posture parallel to gesture? The
best that can be said for it is that CV's pose is low-level and technical, and that
HCI pairs hand posture with gesture as static against dynamic. But the HCI posture
is a meaning-neutral shape class, not the communicative member of the pair, and
CV's pose sits at the position level, not the action level, since a keypoint set is
precisely a set of positions. Against the swap stand the dictionaries (pose is the
assumed-for-effect word in every one of them), psychology's posed expressions,
animation's key poses, ballet's poses above its positions, the breaking freeze,
Godøy's goal postures anchoring action chunks, ergonomics' held working postures,
posture verbs in linguistics, and the book itself together with the toolbox's own
existing prose. No field uses posture as the more communicative of the two words.

The original pairing also survives the strongest objections, at the price of three
explicit footnotes. CV's pose estimation is resolved rather than merely tolerated:
what a pose-estimation model returns is a set of landmark positions, so the CV
loanword lives at our position level and the function names can stand as they are.
Lamb is a genuine collision and gets a citation. And motor control's dynamic
posture is handled by stating that the toolbox uses the countable, configurational
sense, with the sway metrics described as quantifying the dynamics of maintaining
a posture, which is what that literature itself says they measure.

## Recommendation

Keep the pairing of `Sound Actions`: position with motion, posture with action,
pose with gesture. Each static term is the time-frozen counterpart of its dynamic
partner at the same level of description, and each boundary is the same boundary.

| | measured | segmented | interpreted |
|---|---|---|---|
| dynamic | motion | action | gesture |
| static | position | posture | pose |

Two refinements to how the book words it, both prompted by the review. First,
"subjective" is better said as "requires a choice": performance science measures
postures objectively, and what the book means is that naming a posture requires
someone to choose the segments and the frame of reference, exactly as segmenting
an action requires a threshold someone chose. Second, the pipeline sentence is
worth making explicit, since it is the same sentence on both rows: measure
positions and motion, segment them into postures and actions, and only then
interpret some of them as poses and gestures. The `_actions` module already keeps
segmentation apart from recognition for the dynamic row; the static row should be
described the same way.

## Consequences for the toolbox

- The `pose_*` function names stay. The docs state once that "pose estimation" is
  the computer-vision loanword, and that what it returns are landmark positions in
  our terms.
- `pose_center()` and `normalise_poses()` are the position-to-posture operators and
  can be documented as such.
- The `_posture` module's sway metrics are correctly named only if described as
  measuring the dynamics of maintaining a posture, which matches Prieto's own
  wording. The docstring should say so; whether the module is better called
  `_balance` or `_sway` is a road-to-2.0 question, not a 1.x rename.
- The static row's meaning level is proposals, not detections, exactly as
  `_actions` attaches labels to spans. Nothing in the toolbox detects a pose; it
  can only propose that a held posture is one.

## Draft terminology passage for the documentation

The passage below is written for the docs (basics-first, no project history), to
sit wherever the motion/action/gesture ladder is introduced.

---

### Position, posture, and pose

The toolbox describes movement at three levels. Motion is continuous displacement
in space over time, and is what the tools measure: quantity of motion, optical
flow, landmark trajectories. An action is a segment of motion with a beginning and
an end, such as a drum stroke or a reach for a cup. A gesture is an action
carrying meaning, and meaning is not a property of the signal, so gestures are
interpreted rather than detected.

Bodies that are not moving need the same three levels, and the words are position,
posture, and pose.

Position is the measured level: where a point is in space. A pose-estimation model
returns positions, for example 33 landmark coordinates per frame, and nothing
more. The name "pose estimation" is the computer-vision convention and is kept in
function names such as `pose()` and `posegram()`; in the terms used here, what
those functions return are landmark positions.

Posture is a configuration: how the parts of the body are placed relative to each
other, with the location in the room taken out. Standing, sitting, and kneeling
are postures, and so is the shape of a hand on a keyboard. Turning positions into
a posture requires a choice of segments and reference frame, which is what
`pose_center()` does when it removes absolute position and keeps the relative
configuration. A posture is to position what an action is to motion: a chunk that
a person would name.

Pose is a posture with meaning, typically assumed for an observer. A static
thumbs-up is a pose, and lifting the hand to show the thumb is a gesture; a
breaker's freeze is a pose timed to the music. Like gestures, poses have to be
interpreted, so the toolbox measures positions, segments postures, and only ever
proposes poses.

| | measured | segmented | interpreted |
|---|---|---|---|
| dynamic | motion | action | gesture |
| static | position | posture | pose |

Two neighbouring fields use these words differently, and the difference is worth
knowing when reading their literature. Movement science treats posture as an
actively regulated process, which is why the balance functions in `_posture`
quantify the small movements of holding a posture rather than the posture itself.
And in Movement Pattern Analysis, posture means a movement of the whole body as
opposed to a body part (Lamb 1965), a dynamic sense unrelated to the static one
used here.

---

## Sources

- [Sound Actions (Jensenius, MIT Press 2022), pp. 68–69 and ch. 12](https://direct.mit.edu/books/oa-monograph/5459/Sound-ActionsConceptualizing-Musical-Instruments)
- [DeepPose (Toshev & Szegedy, CVPR 2014)](https://arxiv.org/abs/1312.4659)
- [OpenPose (Cao et al., TPAMI 2019)](https://arxiv.org/abs/1812.08008)
- [Deep learning-based human pose estimation: a survey (Zheng et al., ACM CSUR 2023)](https://arxiv.org/abs/2012.13392)
- [Head pose estimation survey (Murphy-Chutorian & Trivedi, TPAMI 2009)](https://people.ict.usc.edu/~gratch/CSCI534/Old-Readings/Head%20Pose%20estimation.pdf)
- [A survey on vision-based human action recognition (Poppe, IVC 2010)](https://www.cs.utexas.edu/~jsinapov/teaching/cs309_spring2017/readings/A_survey_on_vision-based_human_action_re.pdf)
- [Human activity analysis: a review (Aggarwal & Ryoo, ACM CSUR 2011)](https://cvrc.ece.utexas.edu/mryoo/papers/review_ryoo_hdr.pdf)
- [Fall detection by posture recognition (Iazzi et al., J. Imaging 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8321307/)
- [Visual interpretation of hand gestures for HCI (Pavlovic et al., TPAMI 1997)](https://people.cs.rutgers.edu/~vladimir/pub/pavlovic97pami.pdf)
- [Hand posture and gesture recognition survey (LaViola, 1999)](https://cs.brown.edu/research/pubs/techreports/reports/CS-99-11.html)
- [Hand gesture recognition review (Oudah et al., J. Imaging 2020)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8321080/)
- [Postural orientation and equilibrium (Horak, Age & Ageing 2006)](https://academic.oup.com/ageing/article/35/suppl_2/ii7/15654)
- [Measures of postural steadiness (Prieto et al., IEEE TBME 1996)](https://pubmed.ncbi.nlm.nih.gov/9214811/)
- [Revision of posturography (Duarte & Freitas, RBF 2010)](https://pubmed.ncbi.nlm.nih.gov/20730361/)
- [ISO 11226:2000, static working postures](https://www.iso.org/standard/25573.html)
- [RULA (McAtamney & Corlett, Applied Ergonomics 1993)](https://pubmed.ncbi.nlm.nih.gov/15676903/)
- [Modern Robotics (Lynch & Park, 2017), ch. 2 on configuration](http://modernrobotics.org)
- [Markerless motion capture in biomechanics (Cronin, J. Biomech 2021)](https://pubmed.ncbi.nlm.nih.gov/34029787/)
- [Emotional body language (de Gelder, Nat. Rev. Neurosci. 2006)](https://pubmed.ncbi.nlm.nih.gov/16495945/)
- [Assessing the robustness of power posing (Ranehill et al., Psych. Sci. 2015)](https://journals.sagepub.com/doi/10.1177/0956797614553946)
- [Posture and Gesture (Lamb, 1965; reissued 2012)](https://www.everand.com/book/268338058/Posture-and-Gesture-An-Introduction-to-the-Study-of-Physical-Behaviour)
- [Perceptual study of posture and gesture for virtual characters (Luo & Neff, MIG 2012)](https://www.cs.ucdavis.edu/~neff/papers/FinalPDF-MIGLuoNeff.pdf)
- [Gesture: Visible Action as Utterance (Kendon, 2004)](https://www.cambridge.org/core/books/gesture/5C13D9CF3C32BFB825E7DFF6BE3E2E30)
- [Movement phases in signs and co-speech gestures (Kita et al., 1998)](https://pure.mpg.de/rest/items/item_3018209_1/component/file_3018210/content)
- [Hand and Mind (McNeill, 1992)](https://press.uchicago.edu/ucp/books/book/chicago/H/bo3641188.html)
- [ASL: the phonological base (Liddell & Johnson, Sign Language Studies 1989)](https://educacao.sme.prefeitura.sp.gov.br/wp-content/uploads/Portals/1/Files/19376.pdf)
- [The typology of locative predicates (Ameka & Levinson, Linguistics 2007)](https://pure.mpg.de/rest/items/item_468383/component/file_468382/content)
- [The Linguistics of Sitting, Standing and Lying (Newman ed., 2002)](https://benjamins.com/catalog/tsl.51)
- [Ballet positions (Britannica)](https://www.britannica.com/art/ballet-position)
- [Basic Principles of Classical Ballet (Vaganova, 1934)](https://books.google.com/books/about/Basic_Principles_of_Classical_Ballet.html?id=vTvCAgAAQBAJ)
- [The Illusion of Life (Thomas & Johnston, 1981), pose-to-pose](https://en.wikipedia.org/wiki/Straight_ahead_animation)
- [Musical gestures: concepts and methods in research (Jensenius, Wanderley, Godøy & Leman, 2010)](https://www.duo.uio.no/handle/10852/59647)
- [Understanding coarticulation in musical experience (Godøy, 2014)](https://link.springer.com/chapter/10.1007/978-3-319-12976-1_32)
- [Constraint-based sound-motion objects (Godøy, Frontiers 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8725797/)
- [Gesture-Music (Cadoz & Wanderley, 2000)](https://www.researchgate.net/publication/281419029_Gesture-Music)
- [The stilling response (Upham, Høffding & Rosas, Music & Science 2024)](https://journals.sagepub.com/doi/10.1177/20592043241233422)
- [Freeze (breaking)](https://en.wikipedia.org/wiki/Freeze_(breakdancing_move))

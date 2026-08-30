# Computational Laban: the field, the two Oslo theses, and where MGT's layer sits

Written 2026-08-30 at ARJ's request, alongside the Effort layer's first
implementation. The question: how do Jensenius (2007) and Haga (2008) relate to the
research that has tried to put Laban Movement Analysis into computer-based systems,
and what does the comparison say about how MGT's layer should behave?

## The field, in four lines of work

**Synthesis.** The EMOTE model (Chi, Costa, Zhao & Badler, SIGGRAPH 2000) is the
canonical implementation: Effort and Shape as *parameters* applied to an
independently defined movement, so quality is explicitly separated from trajectory.
Successors refine the same move --- Chao's LMA-Effort simulator with dynamics
parameters (2006), Durupinar et al.'s PERFORM mapping OCEAN personality through
Laban parameters. Synthesis work is the mirror image of analysis: it *assumes*
Effort is parametrisable and asks whether the result looks right.

**Recognition and classification.** Zhao & Badler inverted EMOTE toward
recognition; Aristidou & Chrysanthou built LMA-feature spaces from mocap for
emotion indexing (SIGGRAPH Asia 2013; CGF 2015) and folk-dance retrieval and
evaluation (JOCCH 2015); Fdili Alaoui, Françoise, Schiphorst, Studd & Bevilacqua
(CHI 2017) put certified Laban analysts in the loop and found that multimodal
sensing --- positional plus dynamic plus physiological --- characterises Efforts
better than any single stream. The recent turn is deep learning against annotated
datasets: multitask learning for LMA annotation, dance-style recognition via LMA
(arXiv 2504.21166, 2025), reporting correlations against certified-analyst coding
(e.g. Weight 81 per cent, Time 77 per cent on an affective arm-movement set).

**Applied systems.** Robot and character expressivity (the Laban line surveyed in
*Laban Movement Analysis and Affective Movement Generation for Robots*, Springer
2016), dance education and cultural-heritage retrieval (Aristidou's folk-dance
work), and interactive performance (the EyesWeb expressive-gesture line from Casa
Paganini, whose current `pyeyesweb` was assessed in
`2026-08-23-pyeyesweb-and-laban.md`).

**Reviews.** Larboulette & Gibet's 2015 review of computable movement descriptors
catalogues the substrate features nearly every implementation draws on: velocity,
acceleration, jerk, path curvature, bounding volumes --- the same substrates MGT's
indices use.

## What the two Oslo theses did instead

Neither thesis computes Laban, and that is their position, not their limitation.

**Jensenius (2007)** builds quantitative video tools --- QoM, motiongrams --- and
brings in LMA as the *qualitative complement*, with Schrader's observation
questions (structured in time? in space? in effort --- bound or free?) as the way a
person uses the concepts. Its QoM caution is the founding example of the
activation/effort distinction: whole-body dancing reads high in QoM while nothing
perceptually salient happens, so the quantitative track cannot carry the
qualitative claim. It also keeps the kinesphere --- the imaginary box of movement
possibility --- as the space-element concept the field mostly ignores.

**Haga (2008)** uses effort and activation as *annotation concepts* for
music-movement correspondence: the basic effort actions as descriptive metaphors on
an annotation board, effort as the intentionality-bearing quality read on top of a
neutral activation contour, and the insistence that effort elements denote
fluctuation, not level. It deliberately avoids conflating terms (his refusal of
"flow" for dynamical shaping because Laban's Flow already means something).

The common stance: LMA is a language for humans looking, and computation supplies
substrates and contours for that looking --- it does not replace the looking.

## Where MGT's layer sits, by contrast with the field

| dimension | most of the field | MGT's layer |
|---|---|---|
| input | mocap, multimodal sensors | video-derived trajectories and QoM tracks |
| output | categories (emotions, styles, Efforts as classes) | continuous indices, windowed contours; octant labels only as proposals |
| scale | absolute feature values | the mover's own medians --- descriptions of one mover's range |
| validation | acted-emotion labels, analyst-coded datasets | per-factor: SPARC battery for Flow, Sound Actions for Time, synthetic paths for Space, stated face-validity for Weight |
| stance | recognise/classify Laban | continue the theses: computation as reading aid for a qualitative system |

Three lessons taken from the field rather than against it. From EMOTE: quality is
separable from trajectory, which is exactly why the indices take a speed profile
and not a pose. From Fdili Alaoui et al.: video alone under-determines Effort ---
Weight especially wants dynamic and physiological channels --- which is the
scholarly backing for calling our Weight a kinetic proxy (and a reason to remember
the Equivital sensors if they surface). From Aristidou: LMA feature spaces index
material usefully even when they only partially capture the components --- which is
what the per-section basic-action histograms do for this corpus.

And one divergence held deliberately: the field's dominant validation target ---
acted emotion --- is precisely what this corpus does not have and does not want.
The layer's claims stay at the movement-description level the theses operate on,
and anything affective remains the human analyst's inference.

## Addendum: video specifically

Asked directly whether others have done Laban-based VIDEO analysis (as opposed to
mocap): yes, in two eras with a gap between them.

**The silhouette era.** Camurri's EyesWeb Expressive Gesture Processing Library
(2003-2004) is the canonical camera-based work: quantity of motion and contraction
index from silhouettes, mapped onto Laban's Space and Time, driving real-time
performance systems --- and a companion line classified hand gestures on tangible
interfaces by Effort's Space and Time. This is the direct ancestor of the video
approach MGT sits in, contemporary with Jensenius (2007), and pre-pose-estimation:
its features are pixel-level, like MGT's own QoM.

**The pose-estimation era.** Since about 2023 the deep-learning turn reached video
LMA: pipelines that estimate LMA elements from RGB clips directly (TSN, SlowFast,
video transformers) or from 2D/3D pose extracted from video (PoseC3D and kin), used
for bodily-expressed emotion understanding and for emotion recognition in
contemporary dance recordings (arXiv 2504.21154, 2025). These validate against
emotion labels and report classification accuracy, inheriting the recognition
stance of the mocap era rather than the descriptive stance of the theses.

**The gap between the eras is where MGT's layer stands**: video input like both,
descriptive continuous indices like neither --- the silhouette era mapped a few
substrates to two factors for real-time control, the deep-learning era classifies
affect end-to-end, and this layer computes all four factors as mover-relative
contours with per-factor validation and no affective claim.

## Sources

- [The EMOTE model for effort and shape (Chi, Costa, Zhao & Badler, 2000)](http://graphics.cs.cmu.edu/nsp/course/15-464/Fall05/papers/chi00emote.pdf)
- [An LMA-Effort simulator with dynamics parameters (Chao, 2006)](https://onlinelibrary.wiley.com/doi/10.1002/cav.120)
- [Seeing, Sensing and Recognizing Laban Movement Qualities (Fdili Alaoui et al., CHI 2017)](https://dl.acm.org/doi/10.1145/3025453.3025530)
- [Emotion Analysis and Classification: the LMA Entities (Aristidou et al., CGF 2015)](https://onlinelibrary.wiley.com/doi/abs/10.1111/cgf.12598)
- [Folk Dance Evaluation Using Laban Movement Analysis (Aristidou et al., JOCCH 2015)](https://dl.acm.org/doi/abs/10.1145/2755566)
- [Motion indexing of different emotional states using LMA components (SIGGRAPH Asia 2013)](https://dl.acm.org/doi/10.1145/2542355.2542381)
- [LMA and Affective Movement Generation for Robots (Springer, 2016)](https://link.springer.com/chapter/10.1007/978-3-319-25739-6_2)
- [Dance Style Recognition Using Laban Movement Analysis (arXiv 2504.21166, 2025)](https://arxiv.org/pdf/2504.21166)
- [Modeling Laban Effort qualities (Fdili Alaoui, project page)](https://saralaoui.com/2015/03/effortmodeling/)
- [PERFORM: perceptual approach for adding OCEAN personality (Durupinar et al.)](https://www.cs.ucdavis.edu/~neff/papers/PERFORM_TOG.pdf)
- [The EyesWeb Expressive Gesture Processing Library (Camurri et al., 2004)](https://link.springer.com/content/pdf/10.1007/978-3-540-24598-8_42.pdf)
- [Expressive hand gestures classified by Effort's Space and Time (Springer, 2009)](https://link.springer.com/chapter/10.1007/978-3-540-92865-2_16)
- [Bodily expressed emotion understanding through integrating LMA (2023)](https://www.sciencedirect.com/science/article/pii/S266638992300185X)
- [Emotion Recognition in Contemporary Dance Performances Using LMA (arXiv 2504.21154, 2025)](https://arxiv.org/html/2504.21154v1)

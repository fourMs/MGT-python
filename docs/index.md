# MGT-python: Musical Gestures Toolbox

[![PyPi version](https://badgen.net/pypi/v/musicalgestures/)](https://pypi.org/project/musicalgestures)
[![GitHub license](https://img.shields.io/github/license/fourMs/MGT-python.svg)](https://github.com/fourMs/MGT-python/blob/master/LICENSE)
[![CI](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml)
[![Documentation](https://github.com/fourMs/MGT-python/actions/workflows/docs.yml/badge.svg)](https://fourms.github.io/MGT-python/)

The Musical Gestures Toolbox for Python (`musicalgestures`) is a collection of tools for
visualising and analysing motion in video recordings, together with the sound that
accompanies them. It was developed for research on music-related body motion, but it
works on any video or audio file, and it supports qualitative and quantitative
approaches on equal terms: images made for human looking, and measurements made for
further computation.

![MGT python demo](https://raw.githubusercontent.com/fourMs/MGT-python/master/musicalgestures/documentation/figures/promo/ipython_example.gif)

## Two doors in

- **[Gallery](gallery.md)** — every kind of picture the toolbox makes, each linking to
  the page that makes it. Start here if you know what you want an analysis to look
  like but not what it is called.
- **[Concepts](concepts.md)** — the ideas the toolbox is organised around: motion,
  action, and gesture; position, posture, and pose; quantity of motion and its limits;
  visualisation as a way of looking; the effort layer. Start here if you want the
  function names to make sense before you call them.

## Where to start, by field

- **Music researchers and students**: the [Gallery](gallery.md) shows the analyses at
  a glance; [Concepts](concepts.md) connects them to the musical-gestures literature;
  the [Quick Start](quickstart.md) gets a first motiongram out of your own video in
  minutes.
- **Psychologists**: [Concepts](concepts.md) maps posture and pose onto your
  literature's terms; [pose tracking](user-guide/pose-tracking.md) turns video into
  codeable trajectories; the annotation and co-occurrence tools (see the
  [API reference](musicalgestures/index.md)) carry the step from video to coded units.
- **Human movement scientists**: [pose tracking](user-guide/pose-tracking.md) gives
  landmark trajectories from plain video; the
  [sound–movement toolkit](user-guide/sound-movement-toolkit.md) holds the
  array-level functions, postural sway included; [Concepts](concepts.md) states
  exactly what is meant by position and posture here.
- **Computer scientists**: the [API reference](musicalgestures/index.md) and
  [core classes](user-guide/core-classes.md) describe the machinery;
  [contributing](contributing.md) and [testing](testing.md) describe the workshop.

## Quick start

```bash
pip install musicalgestures
```

The package installs its Python dependencies automatically. Install `ffmpeg`
separately to enable video processing; see the [installation guide](installation.md).

```python
import musicalgestures as mg

# Load a video
v = mg.MgVideo('dance.mp4')

# Create visualisations — call .show() to display the result
v.motiongrams().show()
v.average().show()

# Motion and audio analysis
v.motion().show()
v.audio.spectrogram().show()
```

Analysis methods return result objects (`MgVideo`, `MgImage`, or `MgFigure`) and do
not auto-render; `.show()` displays them.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

## What the toolbox does

- **Video analysis**: motion detection, optical flow, motion vectors, motion tempo, Eulerian video magnification, and motion descriptors (energy, smoothness, entropy, spectral)
- **Visualisations**: motiongrams, videograms, motion history, heatmaps, and space-time displays (stroboscope, silhouette waterfall, 3D space-time volume)
- **Pose estimation**: MediaPipe (default), YOLO, RTMPose and OpenPose backends on one trajectory contract, with trajectory summaries, motion trails, and per-segment statistics
- **Segmentation**: actions cut from motion envelopes, postures cut from landmark trajectories, pulse and cycle segmentation, long-video segmentation, and person tracking
- **Audio analysis**: waveforms, spectrograms, MFCC, chromagrams, tempo and beat tracking, and sonomotiongrams (motion turned into sound)
- **Audio–motion analysis**: tempo similarity, phase synchrony, structural similarity, and per-body-part audio coupling for a single performer
- **Sound–movement research toolkit**: lower-level, array-based functions for pulse and cycle segmentation, cross-modal alignment, quantity of motion, postural sway, physiology, and motion-capture I/O—see the [Sound–Movement Analysis Toolkit](user-guide/sound-movement-toolkit.md)
- **360 video**: projection handling, per-direction views, the anglegram, and audio-energy-map overlays—see [Video Analysis](user-guide/video-analysis.md)
- **Integration**: works with the NumPy, SciPy, librosa, and Matplotlib ecosystems, on Linux, macOS, and Windows

## Learning path

The [wiki](https://github.com/fourMs/MGT-python/wiki) is the course: numbered chapters
that read in order, basics first, with exercises on the bundled example videos. This
site is the reference: it answers "how do I do X" and "what exactly does this
return". The two link to each other throughout.

- **[Installation Guide](installation.md)**—detailed setup instructions
- **[Quick Start Tutorial](quickstart.md)**—up and running in minutes
- **[Examples](examples.md)**—sample code and use cases
- **[User Guide](user-guide/core-classes.md)**—task-oriented documentation

## Runtime behaviour

- `pose()` defaults to the MediaPipe backend and downloads its weights on demand; the OpenPose models download their larger Caffe weights on first use instead.
- In notebook and batch execution, pose weight downloads are attempted automatically instead of prompting for stdin.
- If CUDA-backed OpenCV DNN support is unavailable, `pose(device='gpu')` runs on the CPU instead (switching to the MediaPipe backend when it is installed).
- `flow.dense()`, `flow.sparse()`, and `blur_faces()` run on CPU by default (`use_gpu=False`); pass `use_gpu=True` to attempt CUDA acceleration with automatic CPU fallback.
- `get_cuda_device_count()` can be used to check CUDA visibility from OpenCV.

## Related toolboxes

Four toolboxes come out of the [fourMs lab](https://github.com/fourMs) at the University of Oslo. They are separate packages with separate release cycles, but they are built to be used together and share several implementations, so a measure computed in one agrees with the same measure computed in another.

- [ambiscape](https://github.com/fourMs/ambiscape)—soundscapes: the sonic ambience of a place, across level, spectral, spatial, temporal, ecological and source descriptors
- [musiscape](https://github.com/fourMs/musiscape)—music collections: comparing many tracks and albums held as audio files in folders
- [micromotion](https://github.com/fourMs/micromotion)—human micromotion: quantity of motion from optical markers, accelerometers, respiration belts and force plates

MGT-python and ambiscape divide the work cleanly: MGT owns the pixels (motion analysis, pose, 360 handling, video visualisation), while ambiscape owns the samples (soundscape levels, spatial audio, sound-event taxonomies). MGT's audio functions cover quick looks; for serious soundscape work, install the bridge—`pip install "musicalgestures[soundscape]"`—and pull ambiscape's session features straight into `MgFeatures` on a shared wall-clock time base (see `musicalgestures._soundscape` and `musicalgestures._timecode`).

## Academic background

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/). The software is maintained by the [fourMs lab](https://github.com/fourMs) at [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/), University of Oslo.

## Support and community

- **Issues**: [GitHub Issues](https://github.com/fourMs/MGT-python/issues)
- **Source code**: [GitHub repository](https://github.com/fourMs/MGT-python)
- **Wiki**: [the course, chapter by chapter](https://github.com/fourMs/MGT-python/wiki)

## Citing

If you use MGT-python in your research, please cite the article and the software:

- Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](http://urn.nb.no/URN:NBN:no-91935). *Proceedings of the Nordic Sound and Music Computing Conference*, Copenhagen.
- Jensenius, A. R., Laczkó, B., Poutaraud, J., Widmer, M., & Furmyr, F. (2026). *Musical Gestures Toolbox for Python* [Computer software]. Zenodo. <https://doi.org/10.5281/zenodo.21965729>

The Zenodo DOI above is the concept DOI and always resolves to the newest version;
where the exact behaviour matters, cite the version-specific DOI of the release you
ran as well (listed on the Zenodo record).

```bibtex
@inproceedings{laczkoReflectionsDevelopmentMusical2021,
    title = {Reflections on the Development of the Musical Gestures Toolbox for Python},
    author = {Laczkó, Bálint and Jensenius, Alexander Refsum},
    booktitle = {Proceedings of the Nordic Sound and Music Computing Conference},
    year = {2021},
    address = {Copenhagen},
    url = {http://urn.nb.no/URN:NBN:no-91935}
}
```

## License

MGT-python is released under the [GNU General Public License v3 (GPLv3)](https://github.com/fourMs/MGT-python/blob/master/LICENSE).

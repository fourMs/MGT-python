# MGT-python

[![PyPi version](https://badgen.net/pypi/v/musicalgestures/)](https://pypi.org/project/musicalgestures)
[![Python](https://img.shields.io/pypi/pyversions/musicalgestures.svg)](https://pypi.org/project/musicalgestures/)
[![GitHub license](https://img.shields.io/github/license/fourMs/MGT-python.svg)](https://github.com/fourMs/MGT-python/blob/master/LICENSE)
[![CI](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml)
[![Documentation](https://github.com/fourMs/MGT-python/actions/workflows/docs.yml/badge.svg)](https://fourms.github.io/MGT-python/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21965729.svg)](https://doi.org/10.5281/zenodo.21965729)

The **Musical Gestures Toolbox for Python** (`musicalgestures`) is a collection of tools for visualising and analysing motion in video recordings, along with the accompanying sound. It was developed for research on music-related body motion, but it works on any video or audio file.

![MGT python](https://raw.githubusercontent.com/fourMs/MGT-python/master/musicalgestures/documentation/figures/promo/ipython_example.gif)

## Installation

```bash
pip install musicalgestures
```

You also need [FFmpeg](https://ffmpeg.org) on your system; everything else installs automatically. The [installation guide](https://fourms.github.io/MGT-python/installation/) covers optional extras such as posture estimation.

## Quickstart

```python
import musicalgestures as mg

v = mg.MgVideo(mg.examples.dance)   # or your own file: mg.MgVideo('dance.mp4')
v.motiongrams().show()
```

This draws motiongrams: images that trace where motion happens in the frame over time, like a spectrogram for the body. Analysis methods return result objects, and `.show()` displays them.

You can also try the toolbox in the browser, with no installation:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

## Documentation

- [Documentation site](https://fourms.github.io/MGT-python/) — installation, user guide, and API reference
- [Wiki](https://github.com/fourMs/MGT-python/wiki) — examples and discussion of the methods
- [Contributing](docs/contributing.md) — how to report issues and submit changes

## The four toolboxes

As the toolbox has grown, we split it into four related packages, each released separately on PyPI. They are complementary but focus on different things:

| you have | use | it gives you |
|---|---|---|
| a video file, with or without sound | musicalgestures (this one) | motiongrams, videograms, motion analysis from video |
| a motion time series from markers or sensors | [micromotion](https://github.com/fourMs/micromotion) | quantity of motion (0.2–5 Hz), posture, balance |
| environmental audio recordings — mono, stereo, binaural or ambisonic | [ambiscape](https://github.com/fourMs/ambiscape) | level, spectrum, space, time, sources |
| long music recordings (concerts or in environments) | [musiscape](https://github.com/fourMs/musiscape) | many tracks compared at a glance |

The toolboxes are designed to call relevant functions between them using a single implementation, so results don't depend on which package you called. 

## Citing

If you use this toolbox in your research, please cite this article:

> Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](http://urn.nb.no/URN:NBN:no-91935). *Proceedings of the Nordic Sound and Music Computing Conference*, Copenhagen.

If you want to cite the toolbox itself, use the Zenodo CONCEPT DOI, which always resolves to the newest version:

> Jensenius, A. R., Laczkó, B., Poutaraud, J., Widmer, M., Furmyr, F., Guo, J., Clim, A., Upham, F., & von Arnim, H. A. (2026). *Musical Gestures Toolbox for Python* [Computer software]. Zenodo https://doi.org/10.5281/zenodo.21965729

Where the exact behaviour matters, cite the version you ran.

## Credits

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/). Many researchers and research assistants have helped its development (both directly and indirectly) over the years; see the [contributor list](https://doi.org/10.5281/zenodo.21965729) on Zenodo for details.

The software is developed at the [fourMs lab](https://github.com/fourMs), [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/), University of Oslo.

## License

This toolbox is released under the [GNU General Public License 3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

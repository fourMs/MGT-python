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

You also need [FFmpeg](https://ffmpeg.org) on your system; everything else installs automatically. The [installation guide](https://fourms.github.io/MGT-python/installation/) covers optional extras such as pose estimation.

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

- [Documentation site](https://fourms.github.io/MGT-python/) — installation, quickstart, user guide, and full API reference
- [Wiki](https://github.com/fourMs/MGT-python/wiki) — worked examples and discussion of the methods
- [Contributing](docs/contributing.md) — how to report issues and submit changes

## The four toolboxes

Four packages from the fourMs Lab at the University of Oslo, each released separately on PyPI. Which one you want is decided by what you have in hand rather than by what you want to know:

| you have | use | it gives you |
|---|---|---|
| a video file, with or without its sound | musicalgestures (this one) | motiongrams, videograms, motion analysis from ordinary video |
| a motion time series from a body — optical markers, an accelerometer, a respiration belt, a force plate | [micromotion](https://github.com/fourMs/micromotion) | quantity of motion, posture, balance, and the band conventions the others follow |
| a recording of a place — mono, stereo, binaural or ambisonic | [ambiscape](https://github.com/fourMs/ambiscape) | the sonic ambience of that place: level, spectrum, space, time, sources |
| a folder of music, or a concert recording | [musiscape](https://github.com/fourMs/musiscape) | many tracks and albums compared at a glance |

Where a measure appears in more than one package it has a single owner and a single implementation, so the answer does not depend on which package you called. This package owns everything that starts from pixels; micromotion owns filtering, lag estimation and circular statistics, and this package requires it, re-exporting its `group_qom`, `bandpass` and `xcorr_lag` rather than keeping its own. A test here checks the numbers against micromotion's and fails if they diverge.

Locating one recording inside another is the reverse direction of the same rule. micromotion's `search_lag` owns bounded lag estimation between two series; `musicalgestures.align_by_audio` searches a whole recording for where a short one sits, which needs an FFT rather than a direct search and starts from a media file's audio. Use `search_lag` when the offset is known to be small, `align_by_audio` when you do not know where the piece sits at all.

One name is deliberately NOT shared. `musicalgestures.dominant_frequency` takes an FFT peak over 0.5–8.0 Hz, for locomotion and dance; `micromotion.dominant_frequency` takes a Welch peak over 0.3–4.0 Hz, for a body trying to stay still. They answer different questions and can disagree completely, so state which one produced any number you report.


## Citing

If you use this toolbox in your research, please cite:

> Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](http://urn.nb.no/URN:NBN:no-91935). *Proceedings of the Nordic Sound and Music Computing Conference*, Copenhagen.

If you want to cite the toolbox itself, use the Zenodo CONCEPT DOI, which always resolves to the newest version:

> Jensenius, A. R., Laczkó, B., Poutaraud, J., Widmer, M., Furmyr, F., Guo, J., Clim, A., Upham, F., & von Arnim, H. A. (2026). *Musical Gestures Toolbox for Python* [Computer software]. Zenodo https://doi.org/10.5281/zenodo.21965729

Where the exact behaviour matters, cite the version you ran.

An older concept DOI, https://doi.org/10.5281/zenodo.21949007, is frozen at 1.11.1. It was created by a hand deposit made on 2026-08-15, before the Zenodo GitHub integration was archiving this repository; the integration began working the next day and every release since is under the DOI above. Zenodo cannot merge two concepts, so both records exist and only one of them advances. Cite the DOI above.

`CITATION.cff` in this repository carries the same information in machine-readable form.

## Credits

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/). Many researchers and research assistants have helped its development (both directly and indirectly) over the years; see the contributor list on Zenodo for details.

The [fourMs lab](https://github.com/fourMs) maintains the software at the [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/), University of Oslo.

## License

This toolbox is released under the [GNU General Public License 3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

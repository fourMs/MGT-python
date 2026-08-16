# MGT-python

[![PyPi version](https://badgen.net/pypi/v/musicalgestures/)](https://pypi.org/project/musicalgestures)
[![Python](https://img.shields.io/pypi/pyversions/musicalgestures.svg)](https://pypi.org/project/musicalgestures/)
[![GitHub license](https://img.shields.io/github/license/fourMs/MGT-python.svg)](https://github.com/fourMs/MGT-python/blob/master/LICENSE)
[![CI](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml)
[![Documentation](https://github.com/fourMs/MGT-python/actions/workflows/docs.yml/badge.svg)](https://fourms.github.io/MGT-python/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21965729.svg)](https://doi.org/10.5281/zenodo.21965729)

The **Musical Gestures Toolbox for Python** (`musicalgestures`) is a collection of tools for visualising and analysing motion in video recordings, together with the sound that accompanies them. It was developed for research on music-related body motion, but it works on any video or audio file.

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

This draws motiongrams: images that trace where in the frame movement happens over time, like a spectrogram for the body. Analysis methods return result objects, and `.show()` displays them.

You can also try the toolbox in the browser, with no installation:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

## Documentation

- [Documentation site](https://fourms.github.io/MGT-python/) — installation, quickstart, user guide, and full API reference
- [Wiki](https://github.com/fourMs/MGT-python/wiki) — worked examples and discussion of the methods
- [Contributing](docs/contributing.md) — how to report issues and submit changes

## Related toolboxes

These come out of the same lab, as separate packages with separate release cycles. They are built to
be used together and share several implementations, so a measure computed in one agrees with the
same measure computed in another.

- [micromotion](https://github.com/fourMs/micromotion)—human micromotion: quantity of motion from
  optical markers, accelerometers, respiration belts and force plates. This package re-exports its
  corrected `group_qom` and requires it
- [ambiscape](https://github.com/fourMs/ambiscape)—soundscapes: the sonic ambience of a place
- [musiscape](https://github.com/fourMs/musiscape)—music collections: comparing many tracks and
  albums held as audio files in folders

The boundary is the input rather than the question: this package starts from a VIDEO file, and the
other three from motion series, a room recording and a music collection.

## Credits

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/). Many researchers and research assistants have helped its development over the years, including [Balint Laczko](https://github.com/balintlaczko), [Joachim Poutaraud](https://github.com/joachimpoutaraud), [Frida Furmyr](https://github.com/fridafu), [Marcus Widmer](https://github.com/marcuswidmer), and [Alexander Refsum Jensenius](https://github.com/alexarje/).

The software is maintained by the [fourMs lab](https://github.com/fourMs) at [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/), University of Oslo.

If you use this toolbox in your research, please cite:

- Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](http://urn.nb.no/URN:NBN:no-91935). *Proceedings of the Nordic Sound and Music Computing Conference*, Copenhagen.

## License

This toolbox is released under the [GNU General Public License 3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

## Citing

Cite the CONCEPT DOI, which always resolves to the newest version:

> Jensenius, A. R., Laczkó, B., Poutaraud, J., Widmer, M., & Furmyr, F. (2026). *Musical Gestures Toolbox for Python* (Version 1.11.1) [Computer software]. Zenodo.
> https://doi.org/10.5281/zenodo.21965729

Where the exact behaviour matters, cite the version you ran instead. Version 1.11.1 is https://doi.org/10.5281/zenodo.21949008.

`CITATION.cff` in this repository carries the same information in machine-readable form.

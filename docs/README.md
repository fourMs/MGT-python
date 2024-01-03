# MGT-python

> Auto-generated documentation index.

[![PyPi version](https://badgen.net/pypi/v/musicalgestures/)](https://pypi.org/project/musicalgestures)
[![GitHub license](https://img.shields.io/github/license/fourMs/MGT-python.svg)](https://github.com/fourMs/MGT-python/blob/master/LICENSE)
[![Github all releases](https://img.shields.io/github/downloads/fourMs/MGT-python/total.svg)](https://GitHub.com/fourMs/MGT-python/releases/)
[![CI](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml)

Full Mgt-python project documentation can be found in [Modules](MODULES.md#mgt-python-modules)

- [MGT-python](#mgt-python)
    - [Usage](#usage)
    - [Description](#description)
    - [History](#history)
    - [Reference](#reference)
    - [Credits](#credits)
    - [License](#license)
  - [Mgt-python Modules](MODULES.md#mgt-python-modules)

The Musical Gestures Toolbox for Python is a collection of tools for visualization and analysis of audio and video.

![MGT python](https://raw.githubusercontent.com/fourMs/MGT-python/master/musicalgestures/documentation/figures/promo/ipython_example.gif)

## Usage

The easiest way to get started is to take a look at the Jupyter notebook [MusicalGesturesToolbox](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb), which shows examples of the usage of the toolbox.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

The standard installation via `pip`: paste and execute the following code in the Terminal (OSX, Linux) or the PowerShell (Windows):

`pip install musicalgestures`

MGT is developed in Python 3 and relies on `FFmpeg` and `OpenCV`. See the [wiki documentation](https://github.com/fourMs/MGT-python/wiki#installation) for more details on the installation process.

## Description

Watch a 10-minute introduction to the toolbox: 

[![Video](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/video/nordicsmc2021-thumbnail.png)](https://youtu.be/tZVX_lDFrwc)

MGT can generate both dynamic and static visualizations of video files, including motion videos, history videos, average images, motiongrams, and videograms. It can also extract various features from video files, including the quantity, centroid, and area of motion. The toolbox also integrates well with other libraries, such as OpenPose for skeleton tracking, and Librosa for audio analysis. All the features are described in the [wiki documentation](https://github.com/fourMs/MGT-python/wiki).

## History

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/).

The software is currently maintained by the [fourMs lab](https://github.com/fourMs) at [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/) at the University of Oslo.

## Reference

If you use this toolbox in your research, please cite this article:

- Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](https://www.duo.uio.no/bitstream/handle/10852/89331/Laczk%25C3%25B3_et_al_2021_Reflections_on_the_Development_of_the.pdf?sequence=2&isAllowed=y). *Proceedings of the Nordic Sound and Music Computing Conference*, Copenhagen.

## Credits

Developers: [Balint Laczko](https://github.com/balintlaczko), [Joachim Poutaraud](https://github.com/joachimpoutaraud), [Frida Furmyr](https://github.com/fridafu), [Marcus Widmer](https://github.com/marcuswidmer), [Alexander Refsum Jensenius](https://github.com/alexarje/)

## License

This toolbox is released under the [GNU General Public License 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).

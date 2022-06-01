# MGT-python

> Auto-generated documentation index.

The Musical Gestures Toolbox for Python is a collection of tools for video visualization and video analysis.

Full Mgt-python project documentation can be found in [Modules](MODULES.md#mgt-python-modules)

- [MGT-python](#mgt-python)
    - [About](#about)
    - [Description](#description)
    - [Installation](#installation)
        - [Windows, OSX and Linux](#windows-osx-and-linux)
    - [Usage](#usage)
    - [History](#history)
    - [Reference](#reference)
    - [Credits](#credits)
    - [License](#license)
  - [Mgt-python Modules](MODULES.md#mgt-python-modules)

![MGT python](https://raw.githubusercontent.com/fourMs/MGT-python/master/musicalgestures/documentation/figures/promo/ipython_example.gif)

## About

Videos can be used to develop new visualisations to be used for analysis. The aim of creating such alternate displays from video recordings is to uncover features, structures and similarities within the material itself, and in relation to, for example, score material. Three useful visualisation techniques here are motion images, motion history images and motiongrams.

MGT can generate both dynamic and static visualizations, as well as some quantitative data:

- dynamic visualisations (video files)
    - motion videos
    - motion history videos
- static visualisations (images)
    - motion average images
    - motiongrams
    - videograms
- motion data (csv files)
    - quantity of motion
    - centroid of motion
    - area of motion

## Description

Watch 10-minute intro video to the toolbox: 

[![Video](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/video/nordicsmc2021-thumbnail.png)](https://youtu.be/tZVX_lDFrwc)

## Installation

### Windows, OSX and Linux

The standard installation via pip: paste and execute the following code in the Terminal (OSX, Linux) or the PowerShell (Windows):

`pip install musicalgestures`

MGT is developed in Python 3 and relies on FFmpeg and OpenCV. See [the wiki](https://github.com/fourMs/MGT-python/wiki#installation) for more details on the installation process.

## Usage

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

The Jupyter notebook [MotionGesturesToolbox.ipynb](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb) shows examples of the usage of the toolbox.

## History

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/).

The software is currently maintained by the [fourMs lab](https://github.com/fourMs) at [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/) at the University of Oslo.

## Reference

If you use this toolbox in your research, please cite this article:

- Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](https://nordicsmc.create.aau.dk/wp-content/NordicSMC/Nordic_SMC_2021_paper_38.pdf). Proceedings of the Nordic Sound and Music Computing Conference.

## Credits

Developers: [Frida Furmyr](https://github.com/fridafu), [Marcus Widmer](https://github.com/marcuswidmer), [Balint Laczko](https://github.com/balintlaczko), [Alexander Refsum Jensenius](https://github.com/alexarje/)

## License

This toolbox is released under the [GNU General Public License 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).

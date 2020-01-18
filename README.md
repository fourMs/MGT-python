# MGT-python

The Musical Gestures Toolbox for Python is a collection of tools for video visualization and video analysis.

This toolbox is a port and further development of the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab), which again was a port of Musical Gestures Toolbox for Max.


## About

Videos can be used to develop new visualisations to be used for analysis. The aim of creating such alternate displays from video recordings is to uncover features, structures and similarities within the material itself, and in relation to, for example, score material. Three useful visualisation techniques here are motion images, motion history images and motiongrams.

MGT can generate both dynamic and static visualizations, as well as some quantitative data:

- dynamic visualisations (video files)
    - motion video
    - motion history video
- static visualisations (images)
    - motion average image
    - motiongrams
    - videograms
- motion data (csv files)
    - quantity of motion
    - centroid of motion
    - area of motion

## Installation


### Windows, macOS and Linux

Step 1: Clone the git repository:

    git clone https://github.com/fourMs/MGT-python.git

Step 2 (if Python 3 is not installed): Install Python 3 either by installing [Anaconda 3](https://www.anaconda.com/distribution/) (Python distribution) or directly at [python.org](http://www.python.org).

Step 3: Install the necessary packages: [OpenCV](https://opencv.org/releases/), [moviepy](https://zulko.github.io/moviepy/install.html),[dvipng](https://ctan.org/pkg/dvipng?lang=en) and [FFmpeg](https://ffmpeg.org/download.html). Some of these packages have many dependencies, so remember to check that everything installs correctly. With pip you can run:

    pip3 install opencv-python moviepy ffmpeg ffmpeg-python scipy


## Usage

The documentation folder in this repository holds the main documentation file [MGT-doc.pdf](Module_documentation/MGT_doc.pdf), which describes all functionalities.

The Jupyter notebook "MotionGesturesToolbox.ipynb" shows examples of the usage of the toolbox.

For terminal usage, try the two examples in the One example file of how it can be run is mgmodule/tests/test_mg.py where any .avi-video can be input as filename. To run in terminal (in correct directory): python test_mg.py

## History

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](http://www.uio.no/english/research/groups/fourms/downloads/software/musicalgesturestoolbox/).

The software is currently maintained by the [fourMs lab](https://github.com/fourMs) at [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/) at the University of Oslo.

## Reference

If you use this toolbox for research purposes, please reference this publication: 

- Jensenius, Alexander Refsum (2018). [The Musical Gestures Toolbox for Matlab](http://hdl.handle.net/10852/65559). Proceedings of the 19th International Society for Music Information Retrieval Conference, Late Breaking Demos Session.


## Credits

Main developers: [Frida Furmyr](https://github.com/fridafu), [Marcus Widmer](https://github.com/marcuswidmer), [Alexander Refsum Jensenius](https://github.com/alexarje/)

## License

This toolbox is using the [GNU General Public License 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).

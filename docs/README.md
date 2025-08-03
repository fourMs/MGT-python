# MGT-python

> Auto-generated documentation index.

[![PyPi version](https://badgen.net/pypi/v/musicalgestures/)](https://pypi.org/project/musicalgestures)
[![GitHub license](https://img.shields.io/github/license/fourMs/MGT-python.svg)](https://github.com/fourMs/MGT-python/blob/master/LICENSE)
[![CI](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml)
[![Documentation](https://github.com/fourMs/MGT-python/actions/workflows/docs.yml/badge.svg)](https://fourms.github.io/MGT-python/)

The **Musical Gestures Toolbox for Python** is a collection of tools for visualizing and analysing audio and video files.

![MGT python](https://raw.githubusercontent.com/fourMs/MGT-python/master/musicalgestures/documentation/figures/promo/ipython_example.gif)

📖 **[Documentation & Examples](https://fourms.github.io/MGT-python/)**

## Quick Start

### Installation

```bash
pip install musicalgestures
```

### Basic Usage

```python
import musicalgestures as mg

# Load a video
v = mg.MgVideo('dance.avi')

# Create visualizations
v.grid()
v.videograms()
v.average()
v.history()

# Perform motion analysis
v.motion()

# Audio analysis
v.audio.waveform()
v.audio.spectrogram()
v.audio.tempogram()
```

### Try Online

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

### Quick Links

Full Mgt-python project documentation can be found in [Modules](MODULES.md#mgt-python-modules)

- [Installation Guide](docs/installation.md)
- [Quick Start Tutorial](docs/quickstart.md)
- [Examples & Tutorials](docs/examples.md)
- [User Guide](docs/user-guide/core-classes.md)
- [API Reference](docs/musicalgestures/index.md)
- [Contributing](docs/contributing.md)
  - [Mgt-python Modules](MODULES.md#mgt-python-modules)

## Features

- **Video Analysis**: Motion detection, optical flow, pose estimation
- **Audio Processing**: Spectrograms, audio descriptors, tempo analysis
- **Visualizations**: Motiongrams, videograms, motion history
- **Integration**: Works with NumPy, SciPy, and Matplotlib ecosystems
- **Cross-platform**: Linux, macOS, Windows support

## Requirements

- Python 3.7+
- FFmpeg
- See [installation guide](docs/installation.md) for complete requirements

## Research Background

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/). Many researchers and research assistants have helped its development over the years, including [Balint Laczko](https://github.com/balintlaczko), [Joachim Poutaraud](https://github.com/joachimpoutaraud), [Frida Furmyr](https://github.com/fridafu), [Marcus Widmer](https://github.com/marcuswidmer), [Alexander Refsum Jensenius](https://github.com/alexarje/)

The software is currently maintained by the [fourMs lab](https://github.com/fourMs) at [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/) at the University of Oslo.

[![nordicsmc2021-thumbnail_640](https://github.com/user-attachments/assets/150b1143-0730-4083-af52-8c062a080deb)](https://www.youtube.com/watch?v=tZVX_lDFrwc)

## Reference

If you use this toolbox in your research, please cite this article:

- Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](https://www.duo.uio.no/bitstream/handle/10852/89331/Laczk%25C3%25B3_et_al_2021_Reflections_on_the_Development_of_the.pdf?sequence=2&isAllowed=y). *Proceedings of the Nordic Sound and Music Computing Conference*, Copenhagen.

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

This toolbox is released under the [GNU General Public License 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).

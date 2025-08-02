# MGT-python

> Auto-generated documentation index.

[![PyPi version](https://badgen.net/pypi/v/musicalgestures/)](https://pypi.org/project/musicalgestures)
[![GitHub license](https://img.shields.io/github/license/fourMs/MGT-python.svg)](https://github.com/fourMs/MGT-python/blob/master/LICENSE)
[![CI](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/mgt-python/badge/?version=latest)](https://mgt-python.readthedocs.io/en/latest/?badge=latest)

Full Mgt-python project documentation can be found in [Modules](MODULES.md#mgt-python-modules)

- [MGT-python](#mgt-python)
    - [Quick Start](#quick-start)
        - [Installation](#installation)
        - [Basic Usage](#basic-usage)
        - [Try Online](#try-online)
    - [Documentation](#documentation)
        - [Quick Links](#quick-links)
    - [Features](#features)
    - [Requirements](#requirements)
    - [Research Background](#research-background)
    - [Reference](#reference)
    - [Credits](#credits)
    - [License](#license)
  - [Mgt-python Modules](MODULES.md#mgt-python-modules)

The **Musical Gestures Toolbox for Python** is a comprehensive collection of tools for visualization and analysis of audio and video, with a focus on motion capture and musical gesture analysis.

![MGT python](https://raw.githubusercontent.com/fourMs/MGT-python/master/musicalgestures/documentation/figures/promo/ipython_example.gif)

## Quick Start

### Installation

```bash
pip install musicalgestures
```

### Basic Usage

```python
import musicalgestures as mg

# Load a video
mv = mg.MgVideo('dance.avi')

# Perform motion analysis
motion = mv.motion()

# Create visualizations
motiongrams = mv.motiongrams()
average = mv.average()

# Audio analysis
spectrogram = mv.audio.spectrogram()
```

### Try Online

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

## Documentation

📚 **Complete documentation is available at: [https://mgt-python.readthedocs.io/](https://mgt-python.readthedocs.io/)**

### Quick Links

- **[Installation Guide](docs/installation.md)** - Setup instructions
- **[Quick Start Tutorial](docs/quickstart.md)** - Get started in minutes  
- **[Examples & Tutorials](docs/examples.md)** - Comprehensive examples
- **[User Guide](docs/user-guide/core-classes.md)** - Detailed documentation
- **[API Reference](docs/musicalgestures/index.md)** - Complete API docs
- **[Contributing](docs/contributing.md)** - How to contribute

## Features

- **Video Analysis**: Motion detection, optical flow, pose estimation
- **Audio Processing**: Spectrograms, audio descriptors, tempo analysis
- **Visualizations**: Motiongrams, videograms, motion history
- **Integration**: Works with NumPy, SciPy, Matplotlib ecosystem
- **Cross-platform**: Linux, macOS, Windows support

## Requirements

- Python 3.7+
- FFmpeg (for video processing)
- See [installation guide](docs/installation.md) for complete requirements

## Research Background

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/).

The software is currently maintained by the [fourMs lab](https://github.com/fourMs) at [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/) at the University of Oslo.

## Reference

If you use this toolbox in your research, please cite this article:

- Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](https://www.duo.uio.no/bitstream/handle/10852/89331/Laczk%25C3%25B3_et_al_2021_Reflections_on_the_Development_of_the.pdf?sequence=2&isAllowed=y). *Proceedings of the Nordic Sound and Music Computing Conference*, Copenhagen.

## Credits

Developers: [Balint Laczko](https://github.com/balintlaczko), [Joachim Poutaraud](https://github.com/joachimpoutaraud), [Frida Furmyr](https://github.com/fridafu), [Marcus Widmer](https://github.com/marcuswidmer), [Alexander Refsum Jensenius](https://github.com/alexarje/)

## License

This toolbox is released under the [GNU General Public License 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).

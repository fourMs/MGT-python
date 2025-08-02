# MGT-python: Musical Gestures Toolbox

[![PyPi version](https://badgen.net/pypi/v/musicalgestures/)](https://pypi.org/project/musicalgestures)
[![GitHub license](https://img.shields.io/github/license/fourMs/MGT-python.svg)](https://github.com/fourMs/MGT-python/blob/master/LICENSE)
[![CI](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fourMs/MGT-python/actions/workflows/ci.yml)
[![Documentation](https://github.com/fourMs/MGT-python/actions/workflows/docs.yml/badge.svg)](https://fourms.github.io/MGT-python/)

The **Musical Gestures Toolbox for Python** is a comprehensive collection of tools for visualization and analysis of audio and video, with a focus on motion capture and musical gesture analysis.

![MGT python demo](https://raw.githubusercontent.com/fourMs/MGT-python/master/musicalgestures/documentation/figures/promo/ipython_example.gif)

## What is MGT-python?

MGT-python provides researchers, artists, and developers with powerful tools to:

- **Analyze motion** in video recordings
- **Extract audio features** from multimedia files  
- **Generate visualizations** like motiongrams, videograms, and motion history images
- **Process and manipulate** video content with computer vision techniques
- **Integrate seamlessly** with scientific Python ecosystem (NumPy, SciPy, Matplotlib)

## Key Features

### 🎥 Video Analysis

- Motion detection and tracking
- Optical flow analysis
- Frame differencing and motion history
- Video preprocessing (cropping, filtering, rotation)

### 🎵 Audio Processing

- Waveform analysis and visualization
- Spectrograms and chromagrams
- Tempo and beat tracking
- Audio feature extraction

### 📊 Visualization Tools

- Motiongrams (motion over time)
- Videograms (pixel intensity over time)
- Average images and motion plots
- Interactive plotting with Matplotlib

### 🔧 Utilities

- Video format conversion
- Batch processing capabilities
- Integration with OpenPose for pose estimation
- Export functionality for further analysis

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

# Generate motion analysis
motion = mv.motion()

# Create visualizations
motiongram = mv.motiongrams()
average_image = mv.average()

# Audio analysis
audio = mg.MgAudio('music.wav')
spectrogram = audio.spectrogram()
```

### Try it Online

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

## Getting Started

- **[Installation Guide](installation.md)** - Detailed setup instructions
- **[Quick Start Tutorial](quickstart.md)** - Get up and running in minutes
- **[Examples](examples.md)** - Sample code and use cases
- **[User Guide](user-guide/core-classes.md)** - Comprehensive documentation

## Academic Background

This toolbox builds upon years of research in musical gesture analysis:

- **[Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/)** (Original)
- **[Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/)** (Previous version)
- **MGT-python** (Current version)

## Support and Community

- **Documentation**: You're reading it! 📚
- **Issues**: [GitHub Issues](https://github.com/fourMs/MGT-python/issues)
- **Source Code**: [GitHub Repository](https://github.com/fourMs/MGT-python)
- **Research Group**: [fourMs Lab](https://github.com/fourMs) at [RITMO](https://www.uio.no/ritmo/english/)

## Citation

If you use MGT-python in your research, please cite:

```bibtex
@software{mgt_python,
  title={Musical Gestures Toolbox for Python},
  author={University of Oslo fourMs Lab},
  url={https://fourms.github.io/MGT-python/},
  version={1.3.2},
  year={2024}
}
```

## License

MGT-python is released under the [GNU General Public License v3 (GPLv3)](https://github.com/fourMs/MGT-python/blob/master/LICENSE).

---

**Ready to explore musical gestures?** Start with our [Quick Start Guide](quickstart.md) or jump into the [examples](examples.md)!

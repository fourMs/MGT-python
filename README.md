# MGT-python

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

`musicalgestures` installs its core Python dependencies automatically. You still need a working `ffmpeg` installation on your system for video processing.

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

# Pose estimation
v.pose(model='body_25', device='cpu')
```

### Runtime Notes

- `ffmpeg` is required for video I/O and preprocessing.
- `pose()` downloads OpenPose weights on first use if they are missing.
- In notebooks and other non-interactive runs, missing pose weights are downloaded automatically when possible.
- If `device='gpu'` is requested but OpenCV CUDA support is unavailable, `pose()` falls back to CPU execution.
- `flow.dense()`, `flow.sparse()`, and `blur_faces()` use CPU by default (`use_gpu=False`). Set `use_gpu=True` to opt into CUDA acceleration with automatic CPU fallback.
- `get_cuda_device_count()` is available to quickly check whether OpenCV sees CUDA devices.
- `blur_faces()` returns the generated result object consistently, including when `save_data=True`.

### Try Online

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fourMs/MGT-python/blob/master/musicalgestures/MusicalGesturesToolbox.ipynb)

### Quick Links

- [Installation Guide](https://fourms.github.io/MGT-python/installation/)
- [Quick Start Tutorial](https://fourms.github.io/MGT-python/quickstart/)
- [API Reference](https://fourms.github.io/MGT-python/musicalgestures/)
- [Wiki & How-Tos](https://github.com/fourMs/MGT-python/wiki)
- [Contributing](docs/contributing.md)

## Features

- **Video Analysis**: Motion detection, optical flow, pose estimation
- **Audio Processing**: Spectrograms, audio descriptors, tempo analysis
- **Visualizations**: Motiongrams, videograms, motion history
- **Integration**: Works with NumPy, SciPy, and Matplotlib ecosystems
- **Cross-platform**: Linux, macOS, Windows support

## Presentation

See this short video presentation made for the Nordic Sound and Music Computing Conference 2021:

[![nordicsmc2021-thumbnail_640](https://github.com/user-attachments/assets/150b1143-0730-4083-af52-8c062a080deb)](https://www.youtube.com/watch?v=tZVX_lDFrwc)

## Requirements

- Python 3.10+
- FFmpeg
- See [installation guide](docs/installation.md) for complete requirements

## Research Background

This toolbox builds on the [Musical Gestures Toolbox for Matlab](https://github.com/fourMs/MGT-matlab/), which again builds on the [Musical Gestures Toolbox for Max](https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-max/). Many researchers and research assistants have helped its development over the years, including [Balint Laczko](https://github.com/balintlaczko), [Joachim Poutaraud](https://github.com/joachimpoutaraud), [Frida Furmyr](https://github.com/fridafu), [Marcus Widmer](https://github.com/marcuswidmer), [Alexander Refsum Jensenius](https://github.com/alexarje/)

The software is currently maintained by the [fourMs lab](https://github.com/fourMs) at [RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion](https://www.uio.no/ritmo/english/) at the University of Oslo.

## Reference

If you use this toolbox in your research, please cite this article:

- Laczkó, B., & Jensenius, A. R. (2021). [Reflections on the Development of the Musical Gestures Toolbox for Python](http://urn.nb.no/URN:NBN:no-91935). *Proceedings of the Nordic Sound and Music Computing Conference*, Copenhagen.

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

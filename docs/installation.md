# Installation Guide

## Quick Installation

The easiest way to install MGT-python is via pip:

```bash
pip install musicalgestures
```

## System Requirements

### Python Version

MGT-python requires **Python 3.7 or higher**. We recommend using the latest stable version of Python.

```bash
python --version  # Should be 3.7+
```

### Operating Systems

MGT-python is cross-platform and supports:

- **Linux** (Ubuntu, CentOS, etc.)
- **macOS** (10.14+)
- **Windows** (10+)

## Dependencies

MGT-python automatically installs the following core dependencies:

### Core Scientific Libraries
- `numpy` - Numerical computing
- `pandas` - Data manipulation and analysis  
- `scipy` - Scientific computing
- `matplotlib` - Plotting and visualization

### Computer Vision & Media Processing
- `opencv-python` - Computer vision algorithms
- `scikit-image` - Image processing
- `librosa` - Audio analysis

### Interactive Computing
- `ipython>=7.12` - Enhanced Python shell

## External Dependencies

### FFmpeg (Required)

MGT-python relies on **FFmpeg** for video processing. Install it based on your operating system:

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS (with Homebrew)
```bash
brew install ffmpeg
```

#### Windows
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract and add to your system PATH
3. Or use Chocolatey: `choco install ffmpeg`

#### Verify FFmpeg Installation
```bash
ffmpeg -version
```

### OpenCV (Usually automatic)

OpenCV is typically installed automatically with `opencv-python`. If you encounter issues:

#### Linux additional packages
```bash
sudo apt install libgl1-mesa-glx libglib2.0-0
```

## Installation Methods

### 1. Standard Installation (Recommended)

```bash
pip install musicalgestures
```

### 2. Development Installation

For contributing or using the latest features:

```bash
# Clone the repository
git clone https://github.com/fourMs/MGT-python.git
cd MGT-python

# Install in development mode
pip install -e .
```

### 3. Conda Installation

While not officially supported, you can use conda for dependency management:

```bash
# Create a new environment
conda create -n mgt python=3.9
conda activate mgt

# Install pip dependencies
pip install musicalgestures
```

## Virtual Environments (Recommended)

Using virtual environments prevents dependency conflicts:

### Using venv
```bash
# Create virtual environment
python -m venv mgt-env

# Activate (Linux/macOS)
source mgt-env/bin/activate

# Activate (Windows)
mgt-env\Scripts\activate

# Install MGT-python
pip install musicalgestures
```

### Using conda
```bash
conda create -n mgt python=3.9
conda activate mgt
pip install musicalgestures
```

## Verification

Test your installation:

```python
import musicalgestures as mg

# Check version
print(mg.__version__)

# Load example data
examples = mg.examples
print(f"Dance video: {examples.dance}")
print(f"Pianist video: {examples.pianist}")

# Basic functionality test
mv = mg.MgVideo(examples.dance)
print(f"Video loaded: {mv.filename}")
print(f"Duration: {mv.length:.2f} seconds")
```

## Troubleshooting

### Common Issues

#### 1. FFmpeg not found
```
Error: ffmpeg not found
```
**Solution**: Install FFmpeg following the instructions above.

#### 2. OpenCV import errors
```
ImportError: libGL.so.1: cannot open shared object file
```
**Solution** (Linux):
```bash
sudo apt install libgl1-mesa-glx
```

#### 3. Permission errors on Windows
```
PermissionError: [WinError 5] Access is denied
```
**Solution**: Run terminal as Administrator or use `--user` flag:
```bash
pip install --user musicalgestures
```

#### 4. Jupyter Notebook integration
If using in Jupyter notebooks, you might need:
```bash
pip install jupyter ipywidgets
```

### Getting Help

If you encounter installation issues:

1. **Check the [GitHub Issues](https://github.com/fourMs/MGT-python/issues)** for known problems
2. **Create a new issue** with:
   - Your operating system and version
   - Python version (`python --version`)
   - Complete error message
   - Installation method used

## Next Steps

Once installed successfully:

- **[Quick Start Guide](quickstart.md)** - Your first steps with MGT-python
- **[Examples](examples.md)** - Sample code and tutorials
- **[User Guide](user-guide/core-classes.md)** - Comprehensive documentation

## Performance Optimization

### For Large Video Files
Consider installing additional optimized libraries:

```bash
# For faster NumPy operations
pip install mkl

# For GPU acceleration (if available)
pip install opencv-contrib-python
```

### Memory Management
For processing large videos, ensure adequate RAM and consider:
- Processing videos in chunks
- Using lower resolution for initial analysis
- Monitoring memory usage with `htop` or Task Manager

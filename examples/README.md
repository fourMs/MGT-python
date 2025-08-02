# MGT-python Examples

This directory contains comprehensive examples demonstrating the capabilities of the Musical Gestures Toolbox for Python.

## Getting Started

If you're new to MGT-python, start with these examples in order:

1. **`advanced_video_processing.py`** - Comprehensive video analysis introduction
2. **`audio_analysis_example.py`** - Audio processing features
3. **`batch_processing_example.py`** - Process multiple files efficiently
4. **`pose_estimation_example.py`** - Human pose tracking and analysis

## Example Files

### Python Scripts

- **`advanced_video_processing.py`** - Advanced video processing techniques with multiple analysis methods
- **`audio_analysis_example.py`** - Comprehensive audio analysis and feature extraction
- **`batch_processing_example.py`** - Batch processing multiple videos with progress tracking
- **`pose_estimation_example.py`** - Human pose estimation and movement analysis

### Jupyter Notebooks

- **`notebooks/comprehensive_tutorial.ipynb`** - Interactive tutorial covering all features
- **`notebooks/research_workflow.ipynb`** - Academic research workflow example

## Sample Data

All examples use the built-in sample videos accessed via:

```python
import musicalgestures as mg

# Access sample videos
dance_video = mg.examples.dance      # Dancer video
pianist_video = mg.examples.pianist  # Pianist video
```

## Running Examples

Each example script can be run independently:

```bash
# Advanced video processing
python examples/advanced_video_processing.py

# Audio analysis
python examples/audio_analysis_example.py

# Batch processing
python examples/batch_processing_example.py

# Pose estimation
python examples/pose_estimation_example.py
```

For Jupyter notebooks:

```bash
# Start Jupyter
jupyter notebook

# Open notebooks/comprehensive_tutorial.ipynb
```

## Example Categories

### Beginner Examples
- Basic motion analysis
- Simple visualizations
- Audio waveforms and spectrograms

### Intermediate Examples
- Custom preprocessing
- Multiple analysis methods
- Parameter optimization

### Advanced Examples
- Batch processing workflows
- Custom analysis pipelines
- Research-oriented analysis

### Integration Examples
- Using with other Python libraries
- Exporting data for external analysis
- Real-time processing concepts

## Output Files

Examples create output files in the same directory unless specified otherwise. Common outputs include:

- `*_motion.mp4` - Motion detection videos
- `*_average.png` - Average images
- `*_mgx.png`, `*_mgy.png` - Motiongrams
- `*_motion.csv` - Motion data files
- `*_spectrogram.png` - Audio spectrograms

## Customization

All examples are designed to be easily customized:

1. **Change input files** - Replace sample videos with your own
2. **Modify parameters** - Experiment with different settings
3. **Add analysis steps** - Combine multiple analysis methods
4. **Custom output** - Specify your own output directories

## Need Help?

- **Documentation**: See the [complete documentation](../docs/index.md)
- **Issues**: Report problems on [GitHub Issues](https://github.com/fourMs/MGT-python/issues)
- **Community**: Join discussions in [GitHub Discussions](https://github.com/fourMs/MGT-python/discussions)

## Contributing Examples

Have a great example to share? We welcome contributions!

1. Create a clear, well-documented example script
2. Include comments explaining each step
3. Test with the built-in sample videos
4. Submit a pull request

See our [Contributing Guide](../docs/contributing.md) for details.

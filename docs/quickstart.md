# Quick Start Guide

Welcome to MGT-python! This guide will get you up and running with the Musical Gestures Toolbox in just a few minutes.

## Prerequisites

Make sure you have MGT-python installed. If not, see the [Installation Guide](installation.md).

```bash
pip install musicalgestures
```

## Your First MGT-python Script

Let's start with a simple example using the built-in sample videos:

```python
import musicalgestures as mg

# Access example videos
examples = mg.examples
print(f"Dance video: {examples.dance}")
print(f"Pianist video: {examples.pianist}")

# Load a video
mv = mg.MgVideo(examples.dance)
print(f"Loaded: {mv.filename}")
print(f"Duration: {mv.length:.2f} seconds")
print(f"Frame rate: {mv.fps} fps")
```

## Core Concepts

### MgVideo Class

The `MgVideo` class is your main interface for video analysis:

```python
# Load your own video
mv = mg.MgVideo('path/to/your/video.mp4')

# Or use preprocessing options
mv = mg.MgVideo(
    'path/to/video.mp4',
    starttime=10,      # Start at 10 seconds
    endtime=30,        # End at 30 seconds  
    color=False,       # Convert to grayscale
    filtertype='Regular',  # Motion detection filter
    thresh=0.1         # Motion threshold
)
```

### MgAudio Class

For audio-only analysis:

```python
# Load audio from video or audio file
ma = mg.MgAudio('path/to/audio.wav')

# Or extract audio from video
mv = mg.MgVideo('video.mp4')
ma = mv.audio  # Get the audio component
```

## Basic Analysis Workflows

### 1. Motion Analysis

Extract motion information from your video:

```python
mv = mg.MgVideo(examples.dance)

# Perform motion analysis
motion_data = mv.motion()

# This creates several outputs:
print(f"Motion video: {motion_data['motion_video']}")
print(f"Data file: {motion_data['motion_data']}")

# Access motion metrics
import pandas as pd
data = pd.read_csv(motion_data['motion_data'])
print(data.head())
```

### 2. Create Visualizations

Generate various visualizations:

```python
mv = mg.MgVideo(examples.pianist)

# Motiongrams (motion over time)
motiongrams = mv.motiongrams()
print(f"Horizontal motiongram: {motiongrams['mg_x']}")
print(f"Vertical motiongram: {motiongrams['mg_y']}")

# Average image
average_img = mv.average()
print(f"Average image saved: {average_img}")

# Motion history
history = mv.history()
print(f"Motion history: {history}")
```

### 3. Audio Analysis

Analyze the audio component:

```python
mv = mg.MgVideo(examples.pianist)

# Get audio object
audio = mv.audio

# Create waveform plot
waveform = audio.waveform()
print(f"Waveform plot: {waveform}")

# Generate spectrogram
spectrogram = audio.spectrogram()
print(f"Spectrogram: {spectrogram}")

# Extract audio descriptors
descriptors = audio.descriptors()
print(f"Descriptors: {descriptors}")
```

## Working with Your Own Videos

### Supported Formats

MGT-python works with most common video formats:
- MP4, AVI, MOV, MKV
- Audio: WAV, MP3, FLAC, etc.

### Basic Processing Pipeline

```python
# 1. Load and preprocess
mv = mg.MgVideo(
    'my_video.mp4',
    starttime=5,       # Skip first 5 seconds
    endtime=60,        # Use only first minute
    color=False        # Grayscale for motion analysis
)

# 2. Perform motion analysis
motion = mv.motion()

# 3. Create visualizations
motiongrams = mv.motiongrams()
average = mv.average()

# 4. Analyze audio
audio_analysis = mv.audio.spectrogram()

print("Analysis complete!")
print(f"Motion data: {motion['motion_data']}")
print(f"Visualizations created in: {mv.outdir}")
```

## Understanding Output Files

MGT-python creates several types of output files:

### Video Files
- `*_motion.mp4` - Motion detection video
- `*_history.mp4` - Motion history visualization

### Image Files
- `*_average.png` - Average of all frames
- `*_mgx.png` - Horizontal motiongram
- `*_mgy.png` - Vertical motiongram

### Data Files
- `*_motion.csv` - Numerical motion data
- `*_audio_descriptors.csv` - Audio feature data

### Working Directory

By default, outputs are saved in the same directory as your input video. You can specify a different location:

```python
mv = mg.MgVideo('video.mp4', outdir='/path/to/output/')
```

## Interactive Analysis

### Jupyter Notebooks

MGT-python works great in Jupyter notebooks:

```python
import musicalgestures as mg
import matplotlib.pyplot as plt

# Load video
mv = mg.MgVideo(mg.examples.dance)

# Create motion analysis
motion = mv.motion()

# Display results inline
plt.figure(figsize=(12, 4))
mv.show()  # Shows the video player
```

### Batch Processing

Process multiple videos:

```python
import glob

video_files = glob.glob('videos/*.mp4')

for video_file in video_files:
    print(f"Processing: {video_file}")
    mv = mg.MgVideo(video_file)
    
    # Perform analysis
    motion = mv.motion()
    motiongrams = mv.motiongrams()
    
    print(f"Completed: {video_file}")
```

## Next Steps

Now that you're familiar with the basics, explore more advanced features:

- **[Core Classes](user-guide/core-classes.md)** - Detailed class documentation
- **[Video Processing](user-guide/video-processing.md)** - Advanced video techniques
- **[Audio Analysis](user-guide/audio-analysis.md)** - Comprehensive audio features
- **[Examples](examples.md)** - More complete examples and use cases

## Common Issues

### Video Won't Load
```python
# Check if file exists and is readable
import os
video_path = 'my_video.mp4'
if os.path.exists(video_path):
    print(f"File found: {video_path}")
else:
    print(f"File not found: {video_path}")
```

### FFmpeg Errors
If you get FFmpeg-related errors, ensure FFmpeg is installed:
```bash
ffmpeg -version
```

See the [Installation Guide](installation.md) for help with FFmpeg setup.

### Memory Issues with Large Videos
For large videos, consider:
```python
# Process shorter segments
mv = mg.MgVideo('large_video.mp4', starttime=0, endtime=30)

# Or reduce resolution during preprocessing
mv = mg.MgVideo('large_video.mp4', scale=0.5)  # 50% size
```

Ready to dive deeper? Check out our comprehensive [User Guide](user-guide/core-classes.md)!

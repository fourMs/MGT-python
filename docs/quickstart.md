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
    threshold=0.1      # Motion threshold
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

# Perform motion analysis — returns MgVideo pointing to the motion video
motion_video = mv.motion()
motion_video.show()           # watch the motion video
mv.show(key='motion')         # equivalent shorthand via source MgVideo

# Motion data (QoM, CoM, AoM per frame) is saved as a CSV alongside the video
import pandas as pd
import os
csv_path = os.path.splitext(motion_video.filename)[0].replace('_motion', '_motiondata') + '.csv'
data = pd.read_csv(csv_path)
print(data.head())
```

Recent motion-analysis fixes ensure centroid-of-motion coordinates are computed as scalar values during `motion()` and `motiondata()` runs, which makes notebook and batch execution more robust.

### 2. Create Visualizations

Generate various visualizations:

```python
mv = mg.MgVideo(examples.pianist)

# Motiongrams — returns MgList with [horizontal_mgram, vertical_mgram]
motiongrams = mv.motiongrams()
motiongrams[0].show()  # horizontal motiongram
motiongrams[1].show()  # vertical motiongram
mv.show(key='horizontal')  # shorthand from source MgVideo

# Average image (blend of all frames)
average_img = mv.average()
average_img.show()

# Motion history
history = mv.history()
history.show()
```

Face anonymization also returns a usable result object even when exporting face-coordinate data:

```python
blurred = mv.blur_faces(save_data=True, data_format='csv')
blurred.show(mode='notebook')
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

### 4. Pose Estimation

```python
mv = mg.MgVideo(examples.dance)

# pose() defaults to the MediaPipe backend: fast on plain CPU, no CUDA-enabled
# OpenCV build needed, 33 landmarks with depth + visibility (best for one person).
pose_video = mv.pose()
pose_video.show(mode='notebook')

# OpenPose models ('body_25', 'coco', 'mpi') support multi-person analysis but are
# slow without a CUDA-enabled OpenCV build:
pose_video = mv.pose(model='mpi', device='gpu', downsampling_factor=2)
```

On first use, pose estimation downloads the requested model weights if they are not already present (MediaPipe weights by default).

### 5. Optional GPU Acceleration

```python
mv = mg.MgVideo(examples.dance)

# CPU is the default for flow and blur_faces.
dense_cpu = mv.flow.dense()
blur_cpu = mv.blur_faces()

# Opt in to CUDA acceleration (falls back to CPU automatically).
dense_gpu = mv.flow.dense(use_gpu=True)
sparse_gpu = mv.flow.sparse(use_gpu=True)
blur_gpu = mv.blur_faces(use_gpu=True)

# Check CUDA availability reported by OpenCV.
print(mg.get_cuda_device_count())
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

By default, outputs are saved in the same directory as your input video. Use `target_name` on individual methods to control the output path for a specific result.

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

- **[Loading & Showing](user-guide/loading.md)** - How to load videos and display results
- **[Preprocessing](user-guide/preprocessing.md)** - Trim, crop, rotate, and adjust videos
- **[Video Analysis](user-guide/video-analysis.md)** - Motion analysis, optical flow, pose estimation
- **[Audio Analysis](user-guide/audio-analysis.md)** - Waveforms, spectrograms, and audio features
- **[Working with Results](user-guide/results.md)** - MgFigure, MgImage, MgList, and chaining
- **[API Reference](musicalgestures/index.md)** - Complete method documentation

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

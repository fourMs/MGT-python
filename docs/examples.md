# Examples and Tutorials

This page provides comprehensive examples showing how to use MGT-python for various musical gesture analysis tasks.

## Basic Examples

### Example 1: Simple Motion Analysis

```python
import musicalgestures as mg

# Load the example dance video
mv = mg.MgVideo(mg.examples.dance)

# Perform motion analysis
motion_data = mv.motion()

print(f"Motion video created: {motion_data['motion_video']}")
print(f"Motion data saved: {motion_data['motion_data']}")

# Load and examine the motion data
import pandas as pd
df = pd.read_csv(motion_data['motion_data'])
print("Motion statistics:")
print(df.describe())
```

### Example 2: Audio-Visual Analysis

```python
import musicalgestures as mg
import matplotlib.pyplot as plt

# Load pianist video
mv = mg.MgVideo(mg.examples.pianist)

# Create motion visualizations
motiongrams = mv.motiongrams()
average_img = mv.average()

# Analyze audio
audio = mv.audio
waveform = audio.waveform()
spectrogram = audio.spectrogram()
descriptors = audio.descriptors()

print("Analysis complete! Files created:")
print(f"Motiongrams: {motiongrams}")
print(f"Average image: {average_img}")
print(f"Audio analysis: {descriptors}")
```

## Advanced Examples

### Example 3: Custom Video Preprocessing

```python
import musicalgestures as mg

# Load video with extensive preprocessing
mv = mg.MgVideo(
    mg.examples.dance,
    starttime=5.0,          # Start at 5 seconds
    endtime=25.0,           # End at 25 seconds
    color=False,            # Convert to grayscale
    contrast=0.3,           # Increase contrast
    brightness=0.1,         # Slightly brighten
    filtertype='Regular',   # Motion filter type
    thresh=0.05,           # Motion threshold
    skip=2,                # Keep every 3rd frame
    rotate=10              # Rotate 10 degrees
)

# Perform analysis on preprocessed video
motion = mv.motion()
motiongrams = mv.motiongrams()

print(f"Preprocessed video analysis complete")
print(f"Original length: {mv.length:.2f} seconds")
print(f"Frame rate: {mv.fps} fps")
```

### Example 4: Batch Processing Multiple Videos

```python
import musicalgestures as mg
import os
import glob

def analyze_video_batch(video_pattern, output_dir):
    """
    Analyze multiple videos matching a pattern
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all matching videos
    video_files = glob.glob(video_pattern)
    
    results = []
    for video_file in video_files:
        print(f"Processing: {video_file}")
        
        try:
            # Load video
            mv = mg.MgVideo(video_file, outdir=output_dir)
            
            # Perform analysis
            motion_data = mv.motion()
            motiongrams = mv.motiongrams()
            
            # Store results
            results.append({
                'video': video_file,
                'motion_data': motion_data['motion_data'],
                'motiongrams': motiongrams,
                'success': True
            })
            
        except Exception as e:
            print(f"Error processing {video_file}: {e}")
            results.append({
                'video': video_file,
                'error': str(e),
                'success': False
            })
    
    return results

# Example usage
# results = analyze_video_batch('videos/*.mp4', 'output/')
```

### Example 5: Detailed Audio Analysis

```python
import musicalgestures as mg
import matplotlib.pyplot as plt
import numpy as np

# Load video with audio
mv = mg.MgVideo(mg.examples.pianist)
audio = mv.audio

# Multiple audio analyses
waveform_plot = audio.waveform(dpi=300)
spectrogram_plot = audio.spectrogram(
    window_size=4096,
    overlap=0.9
)

# Audio descriptors with custom parameters
descriptors = audio.descriptors(
    window_size=1024,
    hop_size=512
)

# Tempo and beat analysis
tempogram = audio.tempogram()

# Self-similarity matrix
ssm = audio.ssm()

print("Audio analysis files:")
print(f"Waveform: {waveform_plot}")
print(f"Spectrogram: {spectrogram_plot}")
print(f"Descriptors: {descriptors}")
print(f"Tempogram: {tempogram}")
print(f"SSM: {ssm}")
```

## Specialized Use Cases

### Example 6: Pose Estimation Integration

```python
import musicalgestures as mg

# Load video for pose analysis
mv = mg.MgVideo(mg.examples.dance)

# Extract pose information (requires OpenPose)
try:
    pose_data = mv.pose()
    print(f"Pose estimation complete: {pose_data}")
except Exception as e:
    print(f"Pose estimation requires OpenPose: {e}")
    
# Alternative: Use centroid tracking
centroid = mv.centroid()
print(f"Motion centroid tracking: {centroid}")
```

### Example 7: 360-Degree Video Analysis

```python
import musicalgestures as mg

# For 360-degree videos (experimental)
try:
    mv360 = mg.Mg360Video('360_video.mp4')
    
    # Specific 360 analysis methods
    motion_360 = mv360.motion()
    
    print(f"360 video analysis: {motion_360}")
except:
    print("360 video analysis requires specific video format")
```

### Example 8: Custom Visualization Parameters

```python
import musicalgestures as mg

mv = mg.MgVideo(mg.examples.pianist)

# Motiongrams with custom parameters
motiongrams = mv.motiongrams(
    filtertype='Regular',
    thresh=0.1,
    blur='Medium',
    use_median=True
)

# History video with custom settings
history = mv.history(
    history_length=60,  # 60 frame history
    normalize=True
)

# Average image with different methods
average_standard = mv.average()
average_median = mv.average(method='median')

print("Custom visualizations created:")
print(f"Motiongrams: {motiongrams}")
print(f"History: {history}")
print(f"Averages: {average_standard}, {average_median}")
```

## Research Examples

### Example 9: Motion Feature Extraction

```python
import musicalgestures as mg
import pandas as pd
import numpy as np

def extract_motion_features(video_path):
    """
    Extract comprehensive motion features for research
    """
    mv = mg.MgVideo(video_path)
    
    # Basic motion analysis
    motion_data = mv.motion()
    
    # Load motion data
    df = pd.read_csv(motion_data['motion_data'])
    
    # Calculate additional features
    features = {
        'total_motion': df['Quantity of Motion'].sum(),
        'avg_motion': df['Quantity of Motion'].mean(),
        'motion_std': df['Quantity of Motion'].std(),
        'peak_motion': df['Quantity of Motion'].max(),
        'motion_range': df['Quantity of Motion'].max() - df['Quantity of Motion'].min(),
        
        # Centroid features
        'centroid_x_range': df['Centroid X'].max() - df['Centroid X'].min(),
        'centroid_y_range': df['Centroid Y'].max() - df['Centroid Y'].min(),
        
        # Area features
        'avg_area': df['Area of Motion'].mean(),
        'max_area': df['Area of Motion'].max(),
    }
    
    return features, motion_data

# Example usage
features, data = extract_motion_features(mg.examples.dance)
print("Motion features:")
for key, value in features.items():
    print(f"{key}: {value:.3f}")
```

### Example 10: Comparative Analysis

```python
import musicalgestures as mg
import pandas as pd
import matplotlib.pyplot as plt

def compare_videos(video1, video2, label1="Video 1", label2="Video 2"):
    """
    Compare motion characteristics between two videos
    """
    # Analyze both videos
    mv1 = mg.MgVideo(video1)
    mv2 = mg.MgVideo(video2)
    
    motion1 = mv1.motion()
    motion2 = mv2.motion()
    
    # Load motion data
    df1 = pd.read_csv(motion1['motion_data'])
    df2 = pd.read_csv(motion2['motion_data'])
    
    # Create comparison plot
    plt.figure(figsize=(12, 8))
    
    # Motion quantity over time
    plt.subplot(2, 2, 1)
    plt.plot(df1['Frame'], df1['Quantity of Motion'], label=label1)
    plt.plot(df2['Frame'], df2['Quantity of Motion'], label=label2)
    plt.title('Quantity of Motion')
    plt.xlabel('Frame')
    plt.ylabel('Motion')
    plt.legend()
    
    # Centroid X
    plt.subplot(2, 2, 2)
    plt.plot(df1['Frame'], df1['Centroid X'], label=label1)
    plt.plot(df2['Frame'], df2['Centroid X'], label=label2)
    plt.title('Centroid X')
    plt.xlabel('Frame')
    plt.ylabel('X Position')
    plt.legend()
    
    # Centroid Y
    plt.subplot(2, 2, 3)
    plt.plot(df1['Frame'], df1['Centroid Y'], label=label1)
    plt.plot(df2['Frame'], df2['Centroid Y'], label=label2)
    plt.title('Centroid Y')
    plt.xlabel('Frame')
    plt.ylabel('Y Position')
    plt.legend()
    
    # Area of motion
    plt.subplot(2, 2, 4)
    plt.plot(df1['Frame'], df1['Area of Motion'], label=label1)
    plt.plot(df2['Frame'], df2['Area of Motion'], label=label2)
    plt.title('Area of Motion')
    plt.xlabel('Frame')
    plt.ylabel('Area')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('video_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return df1, df2

# Example: Compare dance and pianist videos
# df_dance, df_pianist = compare_videos(
#     mg.examples.dance, 
#     mg.examples.pianist,
#     "Dance", "Pianist"
# )
```

## Interactive Examples

### Example 11: Jupyter Notebook Integration

```python
# Cell 1: Setup
import musicalgestures as mg
import matplotlib.pyplot as plt
%matplotlib inline

# Load video
mv = mg.MgVideo(mg.examples.pianist)

# Cell 2: Quick motion analysis
motion = mv.motion()
print(f"Motion analysis complete: {motion}")

# Cell 3: Display results
# This will show the video player in Jupyter
mv.show()

# Cell 4: Create and display motiongrams
motiongrams = mv.motiongrams()

# Load and display the motiongrams
from PIL import Image
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Display horizontal motiongram
img_x = Image.open(motiongrams['mg_x'])
ax1.imshow(img_x)
ax1.set_title('Horizontal Motiongram')
ax1.axis('off')

# Display vertical motiongram  
img_y = Image.open(motiongrams['mg_y'])
ax2.imshow(img_y)
ax2.set_title('Vertical Motiongram')
ax2.axis('off')

plt.tight_layout()
plt.show()
```

### Example 12: Real-time Analysis Workflow

```python
import musicalgestures as mg
import time

def analyze_workflow(video_path, verbose=True):
    """
    Complete analysis workflow with timing
    """
    start_time = time.time()
    
    if verbose:
        print(f"Starting analysis of: {video_path}")
    
    # Load video
    load_start = time.time()
    mv = mg.MgVideo(video_path)
    load_time = time.time() - load_start
    
    if verbose:
        print(f"Video loaded in {load_time:.2f}s")
        print(f"Video info: {mv.width}x{mv.height}, {mv.length:.2f}s, {mv.fps}fps")
    
    # Motion analysis
    motion_start = time.time()
    motion = mv.motion()
    motion_time = time.time() - motion_start
    
    if verbose:
        print(f"Motion analysis completed in {motion_time:.2f}s")
    
    # Visualizations
    viz_start = time.time()
    motiongrams = mv.motiongrams()
    average = mv.average()
    viz_time = time.time() - viz_start
    
    if verbose:
        print(f"Visualizations created in {viz_time:.2f}s")
    
    # Audio analysis
    audio_start = time.time()
    spectrogram = mv.audio.spectrogram()
    audio_time = time.time() - audio_start
    
    if verbose:
        print(f"Audio analysis completed in {audio_time:.2f}s")
    
    total_time = time.time() - start_time
    
    results = {
        'motion_data': motion,
        'visualizations': {
            'motiongrams': motiongrams,
            'average': average
        },
        'audio': {
            'spectrogram': spectrogram
        },
        'timing': {
            'load_time': load_time,
            'motion_time': motion_time,
            'viz_time': viz_time,
            'audio_time': audio_time,
            'total_time': total_time
        }
    }
    
    if verbose:
        print(f"Total analysis time: {total_time:.2f}s")
    
    return results

# Run complete workflow
results = analyze_workflow(mg.examples.dance)
```

## Next Steps

These examples demonstrate the versatility of MGT-python. For more detailed information:

- **[User Guide](user-guide/core-classes.md)** - Comprehensive documentation
- **[API Reference](musicalgestures/index.md)** - Complete function reference
- **[GitHub Repository](https://github.com/fourMs/MGT-python)** - Source code and issues

## Contributing Examples

Have a great use case for MGT-python? We'd love to include it! Please:

1. Fork the repository
2. Add your example to this page
3. Submit a pull request

Include a brief description, complete code, and expected output for the best examples.

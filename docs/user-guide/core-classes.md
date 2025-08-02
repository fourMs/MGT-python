# Core Classes

MGT-python is built around several core classes that provide the main functionality for musical gesture analysis. This guide covers the primary classes and their key methods.

## Class Hierarchy

```
MgVideo (inherits from MgAudio)
├── MgAudio
├── Mg360Video (specialized video class)
└── Flow (optical flow analysis)

Utility Classes:
├── MgFigure (plotting utilities)
├── MgImage (image handling)
└── MgList (list processing)
```

## MgVideo Class

The `MgVideo` class is the primary interface for video analysis and inherits all audio functionality from `MgAudio`.

### Constructor

```python
MgVideo(
    filename,           # Video file path or list of paths
    array=None,         # Optional: numpy array input
    fps=None,           # Override frame rate
    path=None,          # Output path
    # Preprocessing options
    filtertype="Regular", # Motion filter type
    thresh=0.05,        # Motion detection threshold
    starttime=0,        # Start time in seconds
    endtime=0,          # End time in seconds (0 = full video)
    blur="None",        # Blur type: "None", "Heavy", "Medium"
    skip=0,             # Frame skipping (0 = no skip)
    frames=0,           # Limit number of frames
    rotate=0,           # Rotation angle in degrees
    color=True,         # Color (True) or grayscale (False)
    contrast=0,         # Contrast adjustment (-1 to 1)
    brightness=0,       # Brightness adjustment (-1 to 1)
    # Cropping options
    crop_movement=False, # Auto-crop to motion area
    motion_box_thresh=0.1, # Motion detection threshold for cropping
    motion_box_margin=1,   # Margin around motion box
    # Manual cropping
    cropx=None,         # Manual crop x coordinates [start, end]
    cropy=None,         # Manual crop y coordinates [start, end]
    # Output options
    target_name=None,   # Custom output filename
    overwrite=False,    # Overwrite existing files
    outdir=None        # Output directory
)
```

### Key Properties

```python
mv = mg.MgVideo('video.mp4')

# Basic video properties
print(f"Filename: {mv.filename}")
print(f"Width: {mv.width}")
print(f"Height: {mv.height}")
print(f"Length: {mv.length} seconds")
print(f"Frame rate: {mv.fps}")
print(f"Frame count: {mv.framecount}")
print(f"Output directory: {mv.outdir}")

# Check if color or grayscale
print(f"Color video: {mv.color}")

# Access underlying OpenCV VideoCapture
print(f"Video capture object: {mv.cap}")
```

### Motion Analysis Methods

#### Basic Motion Analysis

```python
# Complete motion analysis - most common method
motion_data = mv.motion(
    filtertype='Regular',     # 'Regular', 'Binary', 'Blob'
    thresh=0.05,             # Motion threshold (0-1)
    blur='None',             # Blur: 'None', 'Heavy', 'Medium'
    use_median=False,        # Use median filtering
    kernel_size=5,           # Morphological kernel size
    normalize=False,         # Normalize motion values
    inverted_motiongram=False, # Invert motiongram colors
    target_name=None,        # Custom output name
    overwrite=False          # Overwrite existing files
)

# Returns dictionary with:
# - 'motion_video': path to motion video
# - 'motion_data': path to CSV data file
```

#### Optical Flow Analysis

```python
# Dense optical flow
flow_data = mv.flow(
    type='Dense',            # 'Dense' or 'Sparse'
    target_name=None,
    overwrite=False
)

# Sparse optical flow with feature tracking
flow_sparse = mv.flow(
    type='Sparse',
    corners_max=100,         # Maximum corners to track
    quality_level=0.3,       # Corner detection quality
    min_distance=7,          # Minimum distance between corners
    block_size=7             # Size of averaging window
)
```

### Visualization Methods

#### Motiongrams

```python
# Create horizontal and vertical motiongrams
motiongrams = mv.motiongrams(
    filtertype='Regular',
    thresh=0.05,
    blur='None',
    use_median=False,
    normalize=False,
    inverted_motiongram=False,
    target_name_x=None,      # Custom name for horizontal
    target_name_y=None,      # Custom name for vertical
    overwrite=False
)

# Returns dictionary:
# - 'mg_x': horizontal motiongram path
# - 'mg_y': vertical motiongram path
```

#### Average Images

```python
# Standard average
average_img = mv.average(
    method='mean',           # 'mean', 'median'
    target_name=None,
    overwrite=False
)

# Median average (good for removing outliers)
median_avg = mv.average(method='median')
```

#### Motion History

```python
# Create motion history visualization
history = mv.history(
    history_length=10,       # Number of frames in history
    target_name=None,
    overwrite=False,
    normalize=False
)
```

#### Videograms

```python
# Extract pixel intensity over time
videograms = mv.videograms(
    target_name_x=None,
    target_name_y=None,
    overwrite=False
)

# Returns paths to horizontal and vertical videograms
```

### Centroid and Feature Extraction

```python
# Motion centroid tracking
centroid = mv.centroid(
    filtertype='Regular',
    thresh=0.05,
    target_name=None,
    overwrite=False
)

# Pose estimation (requires OpenPose)
pose_data = mv.pose(
    pose_model='BODY_25',    # Pose model type
    target_name=None,
    overwrite=False
)
```

### Video Processing Methods

```python
# Apply video effects and transformations
blend_result = mv.blend(
    blend_mode='difference',  # Blending mode
    target_name=None,
    overwrite=False
)

# Subtract background
subtract_result = mv.subtract(
    method='mog2',           # Background subtraction method
    target_name=None,
    overwrite=False
)

# Create video grid
grid_result = mv.grid(
    height=300,              # Grid cell height
    rows=3,                  # Number of rows
    cols=3,                  # Number of columns
    padding=0,               # Padding between cells
    margin=0,                # Margin around grid
    target_name=None,
    overwrite=False
)
```

## MgAudio Class

The `MgAudio` class handles all audio processing functionality and is inherited by `MgVideo`.

### Constructor

```python
MgAudio(
    filename,               # Audio/video file path
    array=None,            # Optional: numpy array input
    sr=None,               # Sample rate override
    offset=0.0,            # Start offset in seconds
    duration=None,         # Duration to load in seconds
    mono=True,             # Convert to mono
    dtype=np.float32       # Data type for audio array
)
```

### Audio Analysis Methods

#### Waveform Visualization

```python
audio = mg.MgAudio('audio.wav')

waveform = audio.waveform(
    mono=True,              # Mono or stereo display
    title='Waveform',       # Plot title
    target_name=None,       # Output filename
    overwrite=False,
    dpi=300,               # Image resolution
    autoshow=True          # Display plot automatically
)
```

#### Spectrogram Analysis

```python
spectrogram = audio.spectrogram(
    window_size=4096,       # FFT window size
    overlap=0.5,           # Window overlap (0-1)
    mel=True,              # Use mel scale
    power=2.0,             # Power for amplitude
    title='Spectrogram',
    target_name=None,
    overwrite=False,
    autoshow=True
)
```

#### Audio Descriptors

```python
descriptors = audio.descriptors(
    window_size=1024,       # Analysis window size
    hop_size=512,          # Hop size between windows
    target_name=None,
    overwrite=False
)

# Creates CSV file with:
# - Spectral centroid
# - Spectral rolloff  
# - Spectral bandwidth
# - Zero crossing rate
# - MFCC coefficients
# - Chroma features
# - Tonnetz features
```

#### Tempo and Beat Analysis

```python
tempogram = audio.tempogram(
    window_size=384,        # Window size for tempo analysis
    hop_size=192,          # Hop size
    target_name=None,
    overwrite=False,
    autoshow=True
)
```

#### Self-Similarity Matrix

```python
ssm = audio.ssm(
    feature='mfcc',         # Feature type: 'mfcc', 'chroma', 'tonnetz'
    distance_metric='cosine', # Distance metric
    target_name=None,
    overwrite=False,
    autoshow=True
)
```

## Flow Class

Specialized class for optical flow analysis.

### Constructor

```python
flow = Flow(
    filename,               # Video file path
    color=True,            # Color or grayscale
    starttime=0,           # Start time
    endtime=0,             # End time
    target_name=None,      # Output name
    overwrite=False
)
```

### Flow Analysis Methods

```python
# Dense optical flow
dense_flow = flow.dense(
    save_plot=True,         # Save flow visualization
    save_data=True,         # Save flow data
    save_video=True         # Save flow video
)

# Sparse optical flow
sparse_flow = flow.sparse(
    corners_max=100,
    quality_level=0.3,
    min_distance=7,
    block_size=7,
    save_plot=True,
    save_data=True,
    save_video=True
)
```

## Utility Classes

### MgFigure

Handle plot creation and customization:

```python
from musicalgestures._utils import MgFigure

fig = MgFigure(
    figure=plt.figure(),    # Matplotlib figure
    figure_type='plot',     # Type of figure
    data=data_array,        # Associated data
    layers=[],             # Plot layers
    title='My Plot'        # Figure title
)
```

### MgImage

Handle image operations:

```python
from musicalgestures._utils import MgImage

img = MgImage(
    image=image_array,      # Image data
    title='My Image',       # Image title
    xlabel='X Label',       # X-axis label
    ylabel='Y Label'        # Y-axis label
)
```

## Common Usage Patterns

### Complete Analysis Workflow

```python
import musicalgestures as mg

# Load video with preprocessing
mv = mg.MgVideo(
    'performance.mp4',
    starttime=10,           # Skip intro
    endtime=120,            # First 2 minutes
    color=False,            # Grayscale for motion
    filtertype='Regular',   # Motion filter
    thresh=0.1             # Motion threshold
)

# Perform all analyses
motion = mv.motion()
motiongrams = mv.motiongrams()
average = mv.average()
history = mv.history()

# Audio analysis
spectrogram = mv.audio.spectrogram()
descriptors = mv.audio.descriptors()
tempogram = mv.audio.tempogram()

print("Analysis complete!")
```

### Error Handling

```python
import musicalgestures as mg

try:
    mv = mg.MgVideo('video.mp4')
    motion = mv.motion()
    print("Success!")
    
except FileNotFoundError:
    print("Video file not found")
except ValueError as e:
    print(f"Invalid parameters: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Next Steps

- **[Video Processing Guide](video-processing.md)** - Advanced video techniques
- **[Audio Analysis Guide](audio-analysis.md)** - Detailed audio processing
- **[Motion Analysis Guide](motion-analysis.md)** - Motion detection techniques
- **[API Reference](../musicalgestures/index.md)** - Complete method documentation

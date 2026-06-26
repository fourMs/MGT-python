# Examples and Tutorials

This page provides working examples for common MGT-python tasks.

## Basic Examples

### Example 1: Simple Motion Analysis

```python
import musicalgestures as mg

mv = mg.MgVideo(mg.examples.dance)

# motion() returns an MgVideo pointing to the rendered motion video
motion_video = mv.motion()
motion_video.show()

# The motion data CSV is saved alongside the video
import os, pandas as pd
csv_path = os.path.splitext(motion_video.filename)[0].replace('_motion', '_motiondata') + '.csv'
df = pd.read_csv(csv_path)
print(df.head())
```

### Example 2: Audio-Visual Analysis

```python
import musicalgestures as mg

mv = mg.MgVideo(mg.examples.pianist)

# Video visualizations
motiongrams = mv.motiongrams()   # MgList: [horizontal MgImage, vertical MgImage]
average_img = mv.average()       # MgImage: pixel average of all frames

motiongrams[0].show()   # horizontal motiongram
motiongrams[1].show()   # vertical motiongram
average_img.show()

# Audio analysis
waveform = mv.audio.waveform()
spectrogram = mv.audio.spectrogram()
descriptors = mv.audio.descriptors()
```

## Advanced Examples

### Example 3: Custom Video Preprocessing

```python
import musicalgestures as mg

mv = mg.MgVideo(
    mg.examples.dance,
    starttime=5.0,        # start at 5 seconds
    endtime=25.0,         # end at 25 seconds
    color=False,          # grayscale
    contrast=30,          # contrast adjustment (-100 to 100)
    brightness=10,        # brightness adjustment (-100 to 100)
    filtertype='Regular', # motion filter: 'Regular', 'Binary', or 'Blob'
    threshold=0.05,       # motion pixel threshold (0–1)
    skip=2,               # keep every 3rd frame
    rotate=10,            # rotate 10 degrees
)

motion_video = mv.motion()
motiongrams = mv.motiongrams()

print(f"Duration: {mv.length:.2f}s at {mv.fps} fps")
```

### Example 4: Batch Processing Multiple Videos

```python
import musicalgestures as mg
import glob

def analyze_video_batch(video_pattern):
    video_files = glob.glob(video_pattern)
    results = []

    for video_file in video_files:
        print(f"Processing: {video_file}")
        try:
            mv = mg.MgVideo(video_file)
            motion_video = mv.motion()
            motiongrams = mv.motiongrams()
            results.append({'video': video_file, 'motion': motion_video, 'success': True})
        except Exception as e:
            print(f"Error processing {video_file}: {e}")
            results.append({'video': video_file, 'error': str(e), 'success': False})

    return results

# results = analyze_video_batch('videos/*.mp4')
```

### Example 5: Detailed Audio Analysis

```python
import musicalgestures as mg

mv = mg.MgVideo(mg.examples.pianist)
audio = mv.audio

waveform = audio.waveform(dpi=300)
spectrogram = audio.spectrogram()
tempogram = audio.tempogram()
hpss_fig = audio.hpss()
ssm_fig = audio.ssm(features='spectrogram')
descriptors = audio.descriptors()

# MgFigure objects: access the underlying matplotlib figure via .figure
spectrogram.show()
spectrogram.figure   # matplotlib Figure
```

### Example 6: Pose Estimation

```python
import musicalgestures as mg

mv = mg.MgVideo(mg.examples.dance)

# Pose estimation — downloads model weights on first use
# device='gpu' falls back to CPU if CUDA is unavailable
try:
    pose_video = mv.pose(model='coco', device='cpu', downsampling_factor=4)
    pose_video.show()
except Exception as e:
    print(f"Pose estimation failed: {e}")
```

### Example 7: Optical Flow

```python
import musicalgestures as mg

mv = mg.MgVideo(mg.examples.dance)

# Dense optical flow — colors encode direction, brightness encodes speed
flow_dense = mv.flow.dense()
flow_dense.show()

# Sparse optical flow — tracks a set of feature points
flow_sparse = mv.flow.sparse()
flow_sparse.show()

# Dense flow with velocity measurement (requires real-world camera parameters)
velocity = mv.flow.dense(velocity=True, distance=3.5, angle_of_view=80)
xvel = velocity.data['xvel']
yvel = velocity.data['yvel']
```

### Example 8: Custom Visualization Parameters

```python
import musicalgestures as mg

mv = mg.MgVideo(mg.examples.pianist)

# Motiongrams with custom filter settings
motiongrams = mv.motiongrams(
    filtertype='Regular',
    threshold=0.1,
    blur='Average',
    use_median=True,
)

# History video (overlay of the last N frames on the current frame)
history = mv.history(history_length=60, normalize=True)

# Average image of all frames
average_img = mv.average()

motiongrams.show()
history.show()
average_img.show()
```

## Research Examples

### Example 9: Motion Feature Extraction

```python
import musicalgestures as mg
import pandas as pd
import os

def extract_motion_features(video_path):
    mv = mg.MgVideo(video_path)
    motion_video = mv.motion()

    # CSV columns: Time (ms), Qom, ComX, ComY, AomX1, AomY1, AomX2, AomY2
    csv_path = os.path.splitext(motion_video.filename)[0].replace('_motion', '_motiondata') + '.csv'
    df = pd.read_csv(csv_path)

    features = {
        'total_qom':   df['Qom'].sum(),
        'avg_qom':     df['Qom'].mean(),
        'peak_qom':    df['Qom'].max(),
        'qom_std':     df['Qom'].std(),
        'com_x_range': df['ComX'].max() - df['ComX'].min(),
        'com_y_range': df['ComY'].max() - df['ComY'].min(),
    }
    return features

features = extract_motion_features(mg.examples.dance)
for key, value in features.items():
    print(f"{key}: {value:.4f}")
```

### Example 10: Comparative Motion Analysis

```python
import musicalgestures as mg
import pandas as pd
import matplotlib.pyplot as plt
import os

def load_motion_csv(motion_video):
    csv_path = os.path.splitext(motion_video.filename)[0].replace('_motion', '_motiondata') + '.csv'
    return pd.read_csv(csv_path)

mv1 = mg.MgVideo(mg.examples.dance)
mv2 = mg.MgVideo(mg.examples.pianist)

df1 = load_motion_csv(mv1.motion())
df2 = load_motion_csv(mv2.motion())

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].plot(df1['Time'], df1['Qom'], label='Dance')
axes[0].plot(df2['Time'], df2['Qom'], label='Pianist')
axes[0].set_title('Quantity of Motion')
axes[0].set_xlabel('Time (ms)')
axes[0].legend()

axes[1].plot(df1['Time'], df1['ComX'], label='Dance')
axes[1].plot(df2['Time'], df2['ComX'], label='Pianist')
axes[1].set_title('Centroid X')
axes[1].set_xlabel('Time (ms)')
axes[1].legend()

plt.tight_layout()
plt.savefig('comparison.png', dpi=150)
plt.show()
```

### Example 11: Stacking Figures with MgList

```python
import musicalgestures as mg

mv = mg.MgVideo(mg.examples.pianist)

# Each analysis returns an MgFigure or MgList
spectrogram = mv.audio.spectrogram(title='Spectrogram')
tempogram = mv.audio.tempogram(title='Tempogram')
descriptors = mv.audio.descriptors(title='Descriptors')

# motiongrams() returns MgList — index 0 is horizontal, 1 is vertical
motiongrams = mv.motiongrams()

# Combine into a single stacked time-aligned figure
combined = mg.MgList(motiongrams[0], spectrogram, tempogram)
fig = combined.as_figure(title='Motion and Audio Analysis')
fig.show()
```

### Example 12: Method Chaining

```python
import musicalgestures as mg

# Each method returns its result, enabling chaining
mg.MgVideo(mg.examples.dance, skip=4).motion().show()

# Chain motion → history → show
mg.MgVideo(mg.examples.dance, skip=3).motionvideo().history(normalize=True).show()

# Chain motion → average image → show
mg.MgVideo(mg.examples.dance, skip=15).motionvideo().average().show()
```

## Next Steps

- **[User Guide](user-guide/loading.md)** — Loading, preprocessing, and all analysis methods
- **[API Reference](musicalgestures/index.md)** — Complete function reference
- **[Wiki](https://github.com/fourMs/MGT-python/wiki)** — Visual examples and how-tos

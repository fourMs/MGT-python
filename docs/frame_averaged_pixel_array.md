# Frame-Averaged Pixel Array

## Overview

The Frame-Averaged Pixel Array functionality creates a unique visualization where each frame of a video is reduced to a single pixel representing its average color. All these frame-pixels are then arranged in a grid to create a compact overview of the entire video's color progression over time.

This implementation is based on the bash script concept that uses FFmpeg to scale each frame to 1x1 pixel and then tiles them into a single image.

## Features

- **FFmpeg-based processing**: Fast and efficient using the same approach as the original bash script
- **OpenCV alternative**: More control over the averaging process
- **Detailed statistics**: Get comprehensive information about the video processing
- **Chainable**: Works with the MGT chaining system
- **Customizable width**: Control the output image dimensions

## Methods

### `frame_averaged_pixel_array(width=640, target_name=None, overwrite=False)`

Creates a frame-averaged pixel array using FFmpeg (equivalent to the bash script).

**Parameters:**
- `width` (int): Width of the output image in pixels (default: 640)
- `target_name` (str): Custom output filename (default: auto-generated)
- `overwrite` (bool): Whether to overwrite existing files (default: False)

**Returns:** `MgImage` object pointing to the output image

### `frame_averaged_pixel_array_cv2(width=640, target_name=None, overwrite=False)`

Alternative implementation using OpenCV for more control over the process.

**Parameters:** Same as above

**Returns:** `MgImage` object pointing to the output image

### `frame_averaged_pixel_array_stats(width=640, include_stats=True)`

Creates a frame-averaged pixel array with detailed statistics output.

**Parameters:**
- `width` (int): Width of the output image in pixels (default: 640)
- `include_stats` (bool): Whether to include detailed statistics (default: True)

**Returns:** Dictionary containing:
- `image`: The `MgImage` object
- `filename`: Absolute path to the source video
- `duration`: Video duration in HH:MM:SS.ms format
- `duration_seconds`: Duration in seconds
- `fps`: Frames per second (rounded)
- `total_frames`: Total number of frames
- `output_width`: Width of output image
- `output_height`: Height of output image
- `filter_description`: FFmpeg filter used

## Usage Examples

### Basic Usage

```python
import musicalgestures as mg

# Load a video
video = mg.MgVideo('path/to/video.mp4')

# Create frame-averaged pixel array
result = video.frame_averaged_pixel_array()
result.show()
```

### Custom Width

```python
# Create a narrower visualization
result = video.frame_averaged_pixel_array(width=320)
result.show()
```

### With Statistics

```python
# Get detailed information
stats = video.frame_averaged_pixel_array_stats(width=480)
stats['image'].show()

print(f"Duration: {stats['duration']}")
print(f"Total frames: {stats['total_frames']}")
print(f"Output size: {stats['output_width']}x{stats['output_height']}")
```

### Chaining with Motion Analysis

```python
# Create frame-averaged pixel array of motion video
video.motion().frame_averaged_pixel_array(width=640).show()
```

### In Jupyter Notebooks

```python
# Display inline in notebook
video.frame_averaged_pixel_array().show(mode="notebook")
```

## Technical Details

### Algorithm

1. Each frame of the video is scaled down to 1x1 pixel using area interpolation
2. The resulting pixel values represent the average color of each frame
3. All frame-pixels are arranged in a grid with the specified width
4. Height is calculated automatically based on total frames and width

### Output Format

- **File format**: PNG
- **Dimensions**: `width` × `ceil(total_frames / width)`
- **Color space**: Preserves original (RGB or grayscale)

### Equivalent FFmpeg Command

The function essentially performs this FFmpeg operation:

```bash
ffmpeg -i input.mp4 -vf "scale=1:1,tile=WIDTHxHEIGHT" -frames:v 1 output.png
```

Where:
- `WIDTH` is the specified width parameter
- `HEIGHT` is calculated as `ceil(total_frames / width)`

## Performance

- **FFmpeg method**: Fast, leverages optimized video processing
- **OpenCV method**: Slower but provides more control
- **Memory usage**: Minimal, processes frame by frame
- **Output size**: Typically very small (width × height pixels)

## Integration with MGT

The Frame-Averaged Pixel Array functionality integrates seamlessly with the Musical Gestures Toolbox:

- **Chaining**: Can be chained with other MGT methods
- **File management**: Follows MGT naming conventions
- **Overwrite protection**: Automatically increments filenames to prevent overwrites
- **Progress indicators**: Shows processing progress
- **Return types**: Returns standard `MgImage` objects

## Comparison with Original Bash Script

This Python implementation provides the same core functionality as the original bash script:

| Feature | Bash Script | Python Implementation |
|---------|-------------|----------------------|
| Frame scaling | `scale=1:1` | ✓ Same FFmpeg filter |
| Grid arrangement | `tile=WxH` | ✓ Same FFmpeg filter |
| Statistics output | Shell variables | ✓ Structured dictionary |
| Progress display | FFmpeg stats | ✓ Progress bars |
| Error handling | Basic | ✓ Enhanced with try/catch |
| Integration | Standalone | ✓ Full MGT integration |

## Files Generated

- `<videoname>_framearray_<width>.png`: The frame-averaged pixel array image
- `<videoname>_framearray_cv2_<width>.png`: OpenCV version (if used)

## See Also

- [MGT Documentation](https://github.com/fourMs/MGT-python/wiki)
- [Original Bash Script](https://oioiiooixiii.blogspot.com)
- [Musical Gestures Toolbox](https://github.com/fourMs/MGT-python)

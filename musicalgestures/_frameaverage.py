import numpy as np
import os
import cv2
from musicalgestures._utils import MgImage, generate_outfilename, get_framecount, get_length, ffmpeg_cmd, get_widthheight


def mg_pixelarray(self, width=640, target_name=None, overwrite=False):
    """
    Creates a 'Frame-Averaged Pixel Array' of a video by reducing each frame to a single pixel
    and arranging all frames into a single image. This is equivalent to the bash script that
    scales each frame to 1x1 pixel and then tiles them into a grid.
    
    Based on the original bash script concept:
    - Each frame is reduced to a single pixel (average color of the frame)
    - All pixel values are arranged in a grid with specified width
    - Height is calculated automatically based on total frames and width
    
    Args:
        width (int, optional): Width of the output image in pixels (number of frame-pixels per row). 
                              Defaults to 640.
        target_name (str, optional): The name of the output image file. If None, uses input filename 
                                   with '_framearray_<width>' suffix. Defaults to None.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically 
                                  increment target filenames to avoid overwriting. Defaults to False.
    
    Returns:
        MgImage: A new MgImage pointing to the output frame-averaged pixel array image file.
    """
    
    if target_name is None:
        target_name = f"{self.of}_pixelarray_{width}.png"
    if not overwrite:
        target_name = generate_outfilename(target_name)
    
    # Get video properties
    frames = get_framecount(self.filename)
    height = int(np.ceil(frames / width))
    video_length = get_length(self.filename)
    
    print(f"Processing {self.filename}")
    print(f"Total frames: {frames}")
    print(f"Output dimensions: {width}x{height}")
    print(f"Filter: scale=1:1,tile={width}x{height}")
    
    # Method 1: Using FFmpeg (similar to the bash script)
    # This directly replicates the bash script functionality
    cmd = [
        'ffmpeg', '-y', '-i', self.filename,
        '-vf', f'scale=1:1,tile={width}x{height}',
        '-frames:v', '1',
        target_name
    ]
    
    ffmpeg_cmd(cmd, video_length, pb_prefix='Creating frame-averaged pixel array:')
    
    # Save result as the pixelarray for parent MgVideo
    self.pixelarray = MgImage(target_name)
    
    return self.pixelarray


def mg_pixelarray_cv2(self, width=640, target_name=None, overwrite=False):
    """
    Alternative implementation using OpenCV for more control over the process.
    Creates a 'Frame-Averaged Pixel Array' by reading each frame, calculating its average color,
    and arranging these average colors in a grid.
    
    Args:
        width (int, optional): Width of the output image in pixels. Defaults to 640.
        target_name (str, optional): The name of the output image file. Defaults to None.
        overwrite (bool, optional): Whether to allow overwriting existing files. Defaults to False.
    
    Returns:
        MgImage: A new MgImage pointing to the output frame-averaged pixel array image file.
    """
    
    if target_name is None:
        target_name = f"{self.of}_pixelarray_cv2_{width}.png"
    if not overwrite:
        target_name = generate_outfilename(target_name)
    
    # Open video
    cap = cv2.VideoCapture(self.filename)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate output dimensions
    height = int(np.ceil(total_frames / width))
    
    print(f"Processing {self.filename}")
    print(f"Total frames: {total_frames}")
    print(f"Output dimensions: {width}x{height}")
    
    # Create output array
    if self.color:
        output_array = np.zeros((height, width, 3), dtype=np.uint8)
    else:
        output_array = np.zeros((height, width), dtype=np.uint8)
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to grayscale if needed
            if not self.color:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                average_color = np.mean(frame)
            else:
                # Calculate average color for each channel
                average_color = np.mean(frame, axis=(0, 1))
            
            # Calculate position in output grid
            row = frame_count // width
            col = frame_count % width
            
            # Only process if within our output bounds
            if row < height:
                output_array[row, col] = average_color.astype(np.uint8)
            
            frame_count += 1
            
            # Progress indicator
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
    
    finally:
        cap.release()
    
    # Save the image
    cv2.imwrite(target_name, output_array)
    
    print(f"Frame-averaged pixel array saved as: {target_name}")
    
    # Save result as the pixelarray_cv2 for parent MgVideo
    self.pixelarray_cv2 = MgImage(target_name)
    
    return self.pixelarray_cv2


def mg_pixelarray_stats(self, width=640, include_stats=True):
    """
    Creates a frame-averaged pixel array and optionally returns statistics about the video.
    This function provides additional information similar to the bash script's output.
    
    Args:
        width (int, optional): Width of the output image in pixels. Defaults to 640.
        include_stats (bool, optional): Whether to return detailed statistics. Defaults to True.
    
    Returns:
        dict: Dictionary containing the generated MgImage and optional statistics.
    """
    
    # Get video properties for statistics (similar to bash script)
    cap = cv2.VideoCapture(self.filename)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration_seconds = total_frames / fps if fps > 0 else 0
    cap.release()
    
    # Calculate dimensions
    height = int(np.ceil(total_frames / width))
    
    # Create the frame-averaged pixel array
    result_image = mg_pixelarray(self, width=width)
    
    result = {
        'image': result_image,
        'filename': os.path.abspath(self.filename)
    }
    
    if include_stats:
        # Format duration similar to ffprobe output (HH:MM:SS.ms)
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = duration_seconds % 60
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        
        result.update({
            'duration': duration_str,
            'duration_seconds': int(duration_seconds),
            'fps': int(fps + 0.5),  # Round fps like in bash script
            'total_frames': total_frames,
            'output_width': width,
            'output_height': height,
            'filter_description': f"scale=1:1,tile={width}x{height}"
        })
        
        # Print statistics (similar to bash script output)
        print(f"{result['filename']}")
        print(f"___Duration: {duration_str[:-1]}")  # Remove last character like bash script
        print(f"____Seconds: {result['duration_seconds']}")
        print(f"________FPS: {result['fps']}")
        print(f"_____Frames: {result['total_frames']}")
        print(f"_____Height: {result['output_height']}")
        print(f"____Filters: {result['filter_description']}")
    
    return result

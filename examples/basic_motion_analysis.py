#!/usr/bin/env python3
"""
Example script demonstrating the Frame-Averaged Pixel Array functionality
in the Musical Gestures Toolbox for Python.

This script creates several variations of frame-averaged pixel arrays
using the included example videos.
"""

import musicalgestures as mg
import os

def main():
    print("Frame-Averaged Pixel Array - Example Script")
    print("=" * 50)
    
    # Use the built-in example video
    video_path = mg.examples.dance
    print(f"Using example video: {os.path.basename(video_path)}")
    
    try:
        # Load the video
        video = mg.MgVideo(video_path)
        print(f"✓ Video loaded: {video.width}x{video.height}, {video.fps} FPS, {video.length:.1f}s")
        
        # Example 1: Basic frame-averaged pixel array
        print("\n1. Creating basic frame-averaged pixel array (width=640)...")
        result1 = video.frame_averaged_pixel_array(width=640)
        print(f"✓ Created: {os.path.basename(result1.filename)}")
        
        # Example 2: Narrower version
        print("\n2. Creating narrow frame-averaged pixel array (width=160)...")
        result2 = video.frame_averaged_pixel_array(width=160)
        print(f"✓ Created: {os.path.basename(result2.filename)}")
        
        # Example 3: With detailed statistics
        print("\n3. Creating frame-averaged pixel array with statistics...")
        stats_result = video.frame_averaged_pixel_array_stats(width=320)
        print(f"✓ Created: {os.path.basename(stats_result['image'].filename)}")
        print(f"  Duration: {stats_result['duration']}")
        print(f"  Total frames: {stats_result['total_frames']}")
        print(f"  Output dimensions: {stats_result['output_width']}x{stats_result['output_height']}")
        
        # Example 4: Chained with motion analysis (using a shorter video section)
        print("\n4. Creating frame-averaged pixel array of motion video...")
        short_video = mg.MgVideo(video_path, starttime=5, endtime=10)
        motion_result = short_video.motion().frame_averaged_pixel_array(width=400)
        print(f"✓ Created motion frame array: {os.path.basename(motion_result.filename)}")
        
        # Example 5: OpenCV version for comparison
        print("\n5. Creating OpenCV-based frame-averaged pixel array...")
        cv2_result = video.frame_averaged_pixel_array_cv2(width=320)
        print(f"✓ Created: {os.path.basename(cv2_result.filename)}")
        
        print("\n" + "=" * 50)
        print("✓ All examples completed successfully!")
        print("\nGenerated files:")
        print(f"  - {os.path.basename(result1.filename)}")
        print(f"  - {os.path.basename(result2.filename)}")
        print(f"  - {os.path.basename(stats_result['image'].filename)}")
        print(f"  - {os.path.basename(motion_result.filename)}")
        print(f"  - {os.path.basename(cv2_result.filename)}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nExample completed successfully! Check the generated PNG files.")
    else:
        print("\nExample failed. Please check the error messages above.")
    
    exit(0 if success else 1)

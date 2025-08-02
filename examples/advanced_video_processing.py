#!/usr/bin/env python3
"""
Advanced Video Processing Example - MGT-python

This example    # Motion history with different lengths
    print("\n5. Motion history analysis...")

    # Short history (shows recent motion)
    history_short = mv.history(
        history_length=10,
        target_name=f"{output_dir}/pianist_history_short"
    )

    # Long history (shows motion trails)
    history_long = mv.history(
        history_length=50,
        target_name=f"{output_dir}/pianist_history_long"
    )

    print(f"   ✅ Motion history analysis complete")anced video processing techniques including:
- Custom preprocessing options
- Multiple analysis methods
- Parameter optimization
- Comprehensive output generation

Author: MGT-python team
"""

import musicalgestures as mg
import os
import pandas as pd
import matplotlib.pyplot as plt

def advanced_video_processing():
    """
    Demonstrate advanced video processing with custom parameters.
    """
    print("Advanced Video Processing Example")
    print("=" * 40)

    # Use the pianist example video for more complex motion
    video_path = mg.examples.pianist
    print(f"Processing: {os.path.basename(video_path)}")

    # Create output directory
    output_dir = "advanced_output"
    os.makedirs(output_dir, exist_ok=True)

    # Load video with extensive preprocessing
    print("\n1. Loading video with custom preprocessing...")
    mv = mg.MgVideo(
        video_path,
        starttime=5,            # Skip first 5 seconds
        endtime=25,             # Process 20 seconds
        color=False,            # Convert to grayscale for motion analysis
        contrast=20,            # Increase contrast (0-100 scale)
        brightness=10,          # Slightly brighten (0-100 scale)
        filtertype='Regular',   # Motion detection filter
        thresh=0.08            # Custom motion threshold
    )

    print(f"   Video info: {mv.width}x{mv.height}, {mv.length:.1f}s at {mv.fps}fps")

    # Perform motion analysis
    print("   Running motion analysis...")
    mv.motion(
        filtertype='Regular',
        thresh=0.05,
        target_name_video='pianist_motion_video',
        target_name_data='pianist_motion_data',
        target_name_mgx='pianist_mgx.png',
        target_name_mgy='pianist_mgy.png'
    )

    print("   ✅ Motion analysis complete")

    # Create motiongrams
    print("   Creating motiongrams...")
    mv.motiongrams(
        target_name_mgx='pianist_motiongrams_mgx.png',
        target_name_mgy='pianist_motiongrams_mgy.png'
    )

    print("   ✅ Motiongrams complete")

    # Generate multiple average images
    print("\n4. Creating average images...")

    # Mean average
    mv.average(
        method='mean',
        target_name=f"{output_dir}/pianist_average_mean"
    )

    # Median average (removes outliers)
    mv.average(
        method='median',
        target_name=f"{output_dir}/pianist_average_median"
    )

    print("   ✅ Mean and median averages complete")

    # Motion history with different lengths
    print("\n5. Motion history analysis...")

    # Short history (recent motion)
    mv.history(
        history_length=10,
        target_name=f"{output_dir}/pianist_history_short"
    )

    # Long history (accumulated motion)
    mv.history(
        history_length=50,
        target_name=f"{output_dir}/pianist_history_long"
    )

    print("   ✅ Motion history analysis complete")

    # Motion data analysis (look for motion data file)
    print("\n6. Motion data analysis...")
    motion_data_file = 'pianist_motion_data.csv'
    if os.path.exists(motion_data_file):
        analyze_motion_data(motion_data_file)
    else:
        print("   Motion data file not found, skipping analysis")

    # Video effects
    print("\n7. Creating video effects...")

    # Blend modes
    mv.blend(
        component_mode='difference',
        target_name=f"{output_dir}/pianist_blend_diff"
    )
    print("   Blend result created")

    print(f"\nAdvanced processing complete! Check the '{output_dir}' directory for outputs.")
    return output_dir

def analyze_motion_data(motion_data_path):
    """
    Analyze the motion data and create plots.
    """
    # Load motion data
    df = pd.read_csv(motion_data_path)

    print(f"   Motion data shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")

    # Basic statistics
    motion_stats = {
        'Total Motion': df['Quantity of Motion'].sum(),
        'Average Motion': df['Quantity of Motion'].mean(),
        'Peak Motion': df['Quantity of Motion'].max(),
        'Motion Std': df['Quantity of Motion'].std(),
        'Active Frames': (df['Quantity of Motion'] > 0.01).sum(),
        'Motion Range': df['Quantity of Motion'].max() - df['Quantity of Motion'].min()
    }

    print("\n   Motion Statistics:")
    for key, value in motion_stats.items():
        print(f"     {key}: {value:.4f}")

    # Create motion analysis plot
    plt.figure(figsize=(15, 10))

    # Motion quantity over time
    plt.subplot(2, 3, 1)
    plt.plot(df['Frame'], df['Quantity of Motion'])
    plt.title('Quantity of Motion Over Time')
    plt.xlabel('Frame')
    plt.ylabel('Motion Quantity')
    plt.grid(True, alpha=0.3)

    # Centroid movement
    plt.subplot(2, 3, 2)
    plt.plot(df['Frame'], df['Centroid X'], label='X', alpha=0.7)
    plt.plot(df['Frame'], df['Centroid Y'], label='Y', alpha=0.7)
    plt.title('Motion Centroid Over Time')
    plt.xlabel('Frame')
    plt.ylabel('Position')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Area of motion
    plt.subplot(2, 3, 3)
    plt.plot(df['Frame'], df['Area of Motion'])
    plt.title('Area of Motion Over Time')
    plt.xlabel('Frame')
    plt.ylabel('Area')
    plt.grid(True, alpha=0.3)

    # Motion distribution
    plt.subplot(2, 3, 4)
    plt.hist(df['Quantity of Motion'], bins=50, alpha=0.7, edgecolor='black')
    plt.title('Motion Quantity Distribution')
    plt.xlabel('Motion Quantity')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)

    # Centroid trajectory
    plt.subplot(2, 3, 5)
    plt.scatter(df['Centroid X'], df['Centroid Y'],
               c=df['Frame'], cmap='viridis', alpha=0.6, s=10)
    plt.colorbar(label='Frame')
    plt.title('Motion Centroid Trajectory')
    plt.xlabel('X Position')
    plt.ylabel('Y Position')
    plt.grid(True, alpha=0.3)

    # Motion vs Area correlation
    plt.subplot(2, 3, 6)
    plt.scatter(df['Quantity of Motion'], df['Area of Motion'], alpha=0.6, s=10)
    plt.title('Motion Quantity vs Area')
    plt.xlabel('Quantity of Motion')
    plt.ylabel('Area of Motion')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save the analysis plot
    output_dir = os.path.dirname(motion_data_path)
    plot_path = os.path.join(output_dir, 'motion_analysis.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   Motion analysis plot saved: {plot_path}")

if __name__ == "__main__":
    try:
        output_directory = advanced_video_processing()
        print(f"\n✅ Success! All outputs saved to: {output_directory}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

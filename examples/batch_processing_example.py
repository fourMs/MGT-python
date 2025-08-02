#!/usr/bin/env python3
"""
Batch Processing Example - MGT-python

This example demonstrates how to process multiple videos efficiently:
- Processing multiple video files in sequence
- Organizing outputs systematically
- Error handling for robust batch processing
- Progress tracking and reporting
- Batch analysis and comparison

Author: MGT-python team
"""

import musicalgestures as mg
import os
import glob
import pandas as pd
import time
from pathlib import Path

def batch_processing_example():
    """
    Demonstrate batch processing of multiple videos.
    """
    print("Batch Processing Example")
    print("=" * 30)
    
    # For this example, we'll process the same video multiple times
    # with different parameters to simulate batch processing
    video_path = mg.examples.dance
    print(f"Base video: {os.path.basename(video_path)}")
    
    # Create output directory
    output_dir = "batch_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Define different processing configurations
    processing_configs = [
        {
            'name': 'standard',
            'params': {
                'filtertype': 'Regular',
                'thresh': 0.05,
                'color': False
            }
        },
        {
            'name': 'binary',
            'params': {
                'filtertype': 'Binary',
                'thresh': 0.1,
                'color': False
            }
        },
        {
            'name': 'blob',
            'params': {
                'filtertype': 'Blob',
                'thresh': 0.08,
                'color': False
            }
        },
        {
            'name': 'color_sensitive',
            'params': {
                'filtertype': 'Regular',
                'thresh': 0.03,
                'color': True
            }
        }
    ]
    
    # Process each configuration
    print(f"\n1. Processing {len(processing_configs)} different configurations...")
    
    results = []
    total_start_time = time.time()
    
    for i, config in enumerate(processing_configs):
        print(f"\n   Processing {i+1}/{len(processing_configs)}: {config['name']}")
        
        try:
            result = process_single_video(
                video_path, 
                config['name'], 
                config['params'], 
                output_dir
            )
            results.append(result)
            print(f"   ✅ {config['name']} completed successfully")
            
        except Exception as e:
            print(f"   ❌ {config['name']} failed: {e}")
            results.append({
                'config_name': config['name'],
                'status': 'failed',
                'error': str(e)
            })
    
    total_time = time.time() - total_start_time
    
    # Generate batch report
    print(f"\n2. Generating batch processing report...")
    generate_batch_report(results, output_dir, total_time)
    
    # Compare results
    print(f"\n3. Comparing motion analysis results...")
    compare_batch_results(results, output_dir)
    
    print(f"\nBatch processing complete! Check the '{output_dir}' directory for outputs.")
    return output_dir

def process_single_video(video_path, config_name, params, output_dir):
    """
    Process a single video with given parameters.
    """
    start_time = time.time()
    
    # Create subdirectory for this configuration
    config_dir = os.path.join(output_dir, config_name)
    os.makedirs(config_dir, exist_ok=True)
    
    # Load video with specified parameters
    mv = mg.MgVideo(video_path, **params)
    
    # Perform motion analysis
    motion_result = mv.motion(
        filtertype=params['filtertype'],
        thresh=params['thresh'],
        target_name_video=os.path.join(config_dir, f"{config_name}_motion"),
        target_name_data=os.path.join(config_dir, f"{config_name}_motion"),
        target_name_mgx=os.path.join(config_dir, f"{config_name}_mgx"),
        target_name_mgy=os.path.join(config_dir, f"{config_name}_mgy")
    )
    
    # Create average image
    average_result = mv.average(
        target_name=os.path.join(config_dir, f"{config_name}_average")
    )
    
    # Create history visualization
    history_result = mv.history(
        target_name=os.path.join(config_dir, f"{config_name}_history")
    )
    
    # Load and analyze motion data
    motion_data_path = motion_result['motion_data']
    motion_stats = analyze_motion_data(motion_data_path)
    
    processing_time = time.time() - start_time
    
    return {
        'config_name': config_name,
        'status': 'success',
        'processing_time': processing_time,
        'motion_data': motion_data_path,
        'motion_stats': motion_stats,
        'outputs': {
            'motion_video': motion_result['motion_video'],
            'motion_data': motion_result['motion_data'],
            'average': average_result,
            'history': history_result
        }
    }

def analyze_motion_data(motion_data_path):
    """
    Analyze motion data and return key statistics.
    """
    try:
        df = pd.read_csv(motion_data_path)
        
        stats = {
            'total_frames': len(df),
            'total_motion': df['Quantity of Motion'].sum(),
            'avg_motion': df['Quantity of Motion'].mean(),
            'max_motion': df['Quantity of Motion'].max(),
            'motion_std': df['Quantity of Motion'].std(),
            'active_frames': (df['Quantity of Motion'] > 0.01).sum(),
            'active_percentage': (df['Quantity of Motion'] > 0.01).mean() * 100,
            'centroid_x_range': df['Centroid X'].max() - df['Centroid X'].min(),
            'centroid_y_range': df['Centroid Y'].max() - df['Centroid Y'].min(),
            'avg_area': df['Area of Motion'].mean(),
            'max_area': df['Area of Motion'].max()
        }
        
        return stats
        
    except Exception as e:
        print(f"Error analyzing motion data: {e}")
        return {}

def generate_batch_report(results, output_dir, total_time):
    """
    Generate a comprehensive batch processing report.
    """
    report_path = os.path.join(output_dir, 'batch_report.txt')
    
    with open(report_path, 'w') as f:
        f.write("MGT-python Batch Processing Report\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"Total processing time: {total_time:.2f} seconds\n")
        f.write(f"Total configurations: {len(results)}\n")
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        f.write(f"Successful: {len(successful)}\n")
        f.write(f"Failed: {len(failed)}\n\n")
        
        # Detailed results
        f.write("Configuration Details:\n")
        f.write("-" * 20 + "\n")
        
        for result in results:
            f.write(f"\nConfiguration: {result['config_name']}\n")
            f.write(f"Status: {result['status']}\n")
            
            if result['status'] == 'success':
                f.write(f"Processing time: {result['processing_time']:.2f}s\n")
                
                # Motion statistics
                stats = result['motion_stats']
                f.write("Motion Statistics:\n")
                f.write(f"  Total motion: {stats.get('total_motion', 'N/A'):.4f}\n")
                f.write(f"  Average motion: {stats.get('avg_motion', 'N/A'):.4f}\n")
                f.write(f"  Peak motion: {stats.get('max_motion', 'N/A'):.4f}\n")
                f.write(f"  Active frames: {stats.get('active_frames', 'N/A')}\n")
                f.write(f"  Active percentage: {stats.get('active_percentage', 'N/A'):.1f}%\n")
                
            else:
                f.write(f"Error: {result['error']}\n")
        
        # Performance summary
        if successful:
            avg_time = sum(r['processing_time'] for r in successful) / len(successful)
            f.write(f"\nAverage processing time: {avg_time:.2f} seconds\n")
    
    print(f"   Batch report saved: {report_path}")

def compare_batch_results(results, output_dir):
    """
    Compare motion analysis results across different configurations.
    """
    successful_results = [r for r in results if r['status'] == 'success']
    
    if len(successful_results) < 2:
        print("   Need at least 2 successful results for comparison")
        return
    
    # Create comparison DataFrame
    comparison_data = []
    
    for result in successful_results:
        stats = result['motion_stats']
        row = {
            'Configuration': result['config_name'],
            'Total Motion': stats.get('total_motion', 0),
            'Avg Motion': stats.get('avg_motion', 0),
            'Peak Motion': stats.get('max_motion', 0),
            'Active Frames': stats.get('active_frames', 0),
            'Active %': stats.get('active_percentage', 0),
            'Processing Time': result['processing_time']
        }
        comparison_data.append(row)
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Save comparison CSV
    comparison_path = os.path.join(output_dir, 'configuration_comparison.csv')
    df_comparison.to_csv(comparison_path, index=False)
    
    print(f"   Configuration comparison saved: {comparison_path}")
    
    # Print summary to console
    print("\n   Configuration Comparison Summary:")
    print("   " + "-" * 50)
    for _, row in df_comparison.iterrows():
        print(f"   {row['Configuration']:15} | "
              f"Total: {row['Total Motion']:8.3f} | "
              f"Peak: {row['Peak Motion']:6.3f} | "
              f"Active: {row['Active %']:5.1f}%")

def process_multiple_videos(video_pattern, output_base_dir):
    """
    Example function for processing multiple actual video files.
    This is a template for real batch processing scenarios.
    """
    print("\nTemplate for Multiple Video Processing")
    print("=" * 40)
    
    # Find all videos matching pattern
    video_files = glob.glob(video_pattern)
    
    if not video_files:
        print("No video files found matching pattern")
        return
    
    print(f"Found {len(video_files)} video files")
    
    results = []
    
    for i, video_file in enumerate(video_files):
        print(f"\nProcessing {i+1}/{len(video_files)}: {os.path.basename(video_file)}")
        
        try:
            # Create output directory for this video
            video_name = os.path.splitext(os.path.basename(video_file))[0]
            video_output_dir = os.path.join(output_base_dir, video_name)
            os.makedirs(video_output_dir, exist_ok=True)
            
            # Load and process video
            mv = mg.MgVideo(video_file)
            
            # Standard processing
            motion_result = mv.motion()
            motiongrams = mv.motiongrams()
            average = mv.average()
            
            # Collect results
            motion_stats = analyze_motion_data(motion_result['motion_data'])
            
            results.append({
                'video_file': video_file,
                'video_name': video_name,
                'status': 'success',
                'motion_stats': motion_stats,
                'outputs': {
                    'motion': motion_result,
                    'motiongrams': motiongrams,
                    'average': average
                }
            })
            
            print(f"✅ Completed: {video_name}")
            
        except Exception as e:
            print(f"❌ Failed: {os.path.basename(video_file)} - {e}")
            results.append({
                'video_file': video_file,
                'video_name': os.path.splitext(os.path.basename(video_file))[0],
                'status': 'failed',
                'error': str(e)
            })
    
    return results

if __name__ == "__main__":
    try:
        output_directory = batch_processing_example()
        print(f"\n✅ Success! All outputs saved to: {output_directory}")
        
        # Uncomment the line below to test with actual multiple videos
        # results = process_multiple_videos("path/to/videos/*.mp4", "multi_video_output")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

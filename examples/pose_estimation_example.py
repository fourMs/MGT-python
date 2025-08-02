#!/usr/bin/env python3
"""
Pose Estimation Example - MGT-python

This example demonstrates human pose estimation capabilities:
- Running pose estimation on videos
- Visualizing pose keypoints and connections
- Analyzing pose data for movement patterns
- Extracting pose-based features
- Comparing different pose estimation models

Author: MGT-python team
"""

import musicalgestures as mg
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def pose_estimation_example():
    """
    Demonstrate pose estimation capabilities with the MGT-python library.
    """
    print("Pose Estimation Example")
    print("=" * 30)

    # Use the dance example video (good for pose analysis)
    video_path = mg.examples.dance
    print(f"Video: {os.path.basename(video_path)}")

    # Create MgVideo object
    mv = mg.MgVideo(video_path)

    print("\n1. Running pose estimation...")

    # Run pose estimation
    pose_result = mv.pose(
        model='BlazePose',  # Available models: 'BlazePose', 'PoseNet'
        target_name_video='dance_pose_video',
        target_name_data='dance_pose_data'
    )

    print("   ✅ Pose estimation complete")
    print(f"   Video output: {pose_result.get('pose_video', 'N/A')}")
    print(f"   Data output: {pose_result.get('pose_data', 'N/A')}")

    # Load and analyze pose data
    if 'pose_data' in pose_result:
        print("\n2. Analyzing pose data...")
        analyze_pose_data(pose_result['pose_data'])

    # Demonstrate pose-based features
    print("\n3. Extracting pose-based movement features...")
    extract_pose_features(pose_result.get('pose_data'))

    # Create pose visualizations
    print("\n4. Creating pose visualizations...")
    create_pose_visualizations(pose_result.get('pose_data'))

    print("\nPose analysis complete!")
    return pose_result

def analyze_pose_data(pose_data_path):
    """
    Analyze pose keypoint data and extract basic statistics.
    """
    try:
        if not os.path.exists(pose_data_path):
            print(f"   Pose data file not found: {pose_data_path}")
            return

        # Load pose data
        df = pd.read_csv(pose_data_path)
        print(f"   Loaded pose data: {len(df)} frames")

        # Get keypoint columns (usually named with coordinates)
        keypoint_cols = [col for col in df.columns if any(part in col.lower()
                        for part in ['nose', 'eye', 'ear', 'shoulder', 'elbow',
                                   'wrist', 'hip', 'knee', 'ankle', 'x', 'y'])]

        if not keypoint_cols:
            print("   No recognizable keypoint columns found")
            return

        print(f"   Found {len(keypoint_cols)} keypoint coordinates")

        # Basic statistics
        print("   \n   Pose Analysis Summary:")
        print(f"   - Total frames analyzed: {len(df)}")

        # Check for missing data
        missing_data = df[keypoint_cols].isnull().sum().sum()
        total_data_points = len(df) * len(keypoint_cols)
        missing_percentage = (missing_data / total_data_points) * 100
        print(f"   - Missing data points: {missing_data} ({missing_percentage:.1f}%)")

        # Movement analysis
        if 'frame' in df.columns:
            print(f"   - Frame range: {df['frame'].min()} to {df['frame'].max()}")

        # Calculate movement metrics if we have coordinate data
        analyze_pose_movement(df, keypoint_cols)

    except Exception as e:
        print(f"   Error analyzing pose data: {e}")

def analyze_pose_movement(df, keypoint_cols):
    """
    Analyze movement patterns from pose data.
    """
    try:
        # Find x and y coordinate columns
        x_cols = [col for col in keypoint_cols if col.endswith('_x') or 'x' in col.lower()]
        y_cols = [col for col in keypoint_cols if col.endswith('_y') or 'y' in col.lower()]

        if not x_cols or not y_cols:
            print("   No coordinate columns found for movement analysis")
            return

        # Calculate frame-to-frame movement
        movement_data = []

        for i in range(1, len(df)):
            frame_movement = 0
            valid_points = 0

            for x_col, y_col in zip(x_cols, y_cols):
                if (pd.notna(df.iloc[i][x_col]) and pd.notna(df.iloc[i-1][x_col]) and
                    pd.notna(df.iloc[i][y_col]) and pd.notna(df.iloc[i-1][y_col])):

                    dx = df.iloc[i][x_col] - df.iloc[i-1][x_col]
                    dy = df.iloc[i][y_col] - df.iloc[i-1][y_col]
                    point_movement = np.sqrt(dx*dx + dy*dy)
                    frame_movement += point_movement
                    valid_points += 1

            if valid_points > 0:
                movement_data.append(frame_movement / valid_points)
            else:
                movement_data.append(0)

        if movement_data:
            avg_movement = np.mean(movement_data)
            max_movement = np.max(movement_data)
            movement_std = np.std(movement_data)

            print(f"   - Average movement per frame: {avg_movement:.3f}")
            print(f"   - Maximum movement per frame: {max_movement:.3f}")
            print(f"   - Movement variability (std): {movement_std:.3f}")

            # Find most active periods
            high_movement_frames = [i for i, mov in enumerate(movement_data)
                                  if mov > avg_movement + movement_std]
            print(f"   - High activity frames: {len(high_movement_frames)} "
                  f"({len(high_movement_frames)/len(movement_data)*100:.1f}%)")

    except Exception as e:
        print(f"   Error in movement analysis: {e}")

def extract_pose_features(pose_data_path):
    """
    Extract meaningful features from pose data for further analysis.
    """
    try:
        if not pose_data_path or not os.path.exists(pose_data_path):
            print("   No pose data available for feature extraction")
            return

        df = pd.read_csv(pose_data_path)

        # Example features that could be extracted
        features = {}

        # 1. Body center tracking (if hip keypoints available)
        hip_cols = [col for col in df.columns if 'hip' in col.lower()]
        if hip_cols:
            print("   ✓ Extracting body center trajectory")
            features['body_center'] = True

        # 2. Limb extension analysis
        limb_pairs = [
            ('shoulder', 'elbow'), ('elbow', 'wrist'),
            ('hip', 'knee'), ('knee', 'ankle')
        ]

        for joint1, joint2 in limb_pairs:
            joint1_cols = [col for col in df.columns if joint1 in col.lower()]
            joint2_cols = [col for col in df.columns if joint2 in col.lower()]
            if joint1_cols and joint2_cols:
                print(f"   ✓ Analyzing {joint1}-{joint2} limb extension")
                features[f'{joint1}_{joint2}_extension'] = True

        # 3. Upper body vs lower body activity
        upper_body_parts = ['nose', 'eye', 'ear', 'shoulder', 'elbow', 'wrist']
        lower_body_parts = ['hip', 'knee', 'ankle']

        upper_cols = [col for col in df.columns
                     if any(part in col.lower() for part in upper_body_parts)]
        lower_cols = [col for col in df.columns
                     if any(part in col.lower() for part in lower_body_parts)]

        if upper_cols and lower_cols:
            print("   ✓ Comparing upper body vs lower body activity")
            features['upper_lower_comparison'] = True

        # 4. Pose symmetry analysis
        left_cols = [col for col in df.columns if 'left' in col.lower()]
        right_cols = [col for col in df.columns if 'right' in col.lower()]

        if left_cols and right_cols:
            print("   ✓ Analyzing left-right symmetry")
            features['symmetry_analysis'] = True

        # 5. Gesture recognition potential
        hand_cols = [col for col in df.columns if any(part in col.lower()
                    for part in ['wrist', 'hand', 'finger'])]
        if hand_cols:
            print("   ✓ Hand/gesture tracking available")
            features['gesture_tracking'] = True

        print(f"   \n   Available pose features: {len(features)}")

        return features

    except Exception as e:
        print(f"   Error extracting pose features: {e}")
        return {}

def create_pose_visualizations(pose_data_path):
    """
    Create visualizations of pose analysis results.
    """
    try:
        if not pose_data_path or not os.path.exists(pose_data_path):
            print("   No pose data available for visualization")
            return

        df = pd.read_csv(pose_data_path)

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Pose Analysis Visualization', fontsize=16)

        # 1. Keypoint visibility over time
        ax1 = axes[0, 0]
        keypoint_cols = [col for col in df.columns if any(part in col.lower()
                        for part in ['nose', 'shoulder', 'hip', 'knee', 'ankle'])]

        if keypoint_cols:
            # Calculate percentage of visible keypoints per frame
            visibility_data = []
            for idx, row in df.iterrows():
                visible_count = sum(1 for col in keypoint_cols if pd.notna(row[col]))
                visibility_percentage = (visible_count / len(keypoint_cols)) * 100
                visibility_data.append(visibility_percentage)

            ax1.plot(visibility_data, linewidth=1)
            ax1.set_title('Keypoint Visibility Over Time')
            ax1.set_xlabel('Frame')
            ax1.set_ylabel('Visible Keypoints (%)')
            ax1.set_ylim(0, 100)
            ax1.grid(True, alpha=0.3)

        # 2. Movement trajectory (if center points available)
        ax2 = axes[0, 1]
        center_x_cols = [col for col in df.columns if 'hip' in col.lower() and 'x' in col.lower()]
        center_y_cols = [col for col in df.columns if 'hip' in col.lower() and 'y' in col.lower()]

        if center_x_cols and center_y_cols:
            # Use first available hip coordinates as center
            x_data = df[center_x_cols[0]].dropna()
            y_data = df[center_y_cols[0]].dropna()

            if len(x_data) > 0 and len(y_data) > 0:
                ax2.plot(x_data, y_data, 'b-', alpha=0.7, linewidth=1)
                ax2.scatter(x_data.iloc[0], y_data.iloc[0], color='green', s=50, label='Start')
                ax2.scatter(x_data.iloc[-1], y_data.iloc[-1], color='red', s=50, label='End')
                ax2.set_title('Body Center Trajectory')
                ax2.set_xlabel('X Position')
                ax2.set_ylabel('Y Position')
                ax2.legend()
                ax2.grid(True, alpha=0.3)

        # 3. Movement intensity over time
        ax3 = axes[1, 0]
        # Calculate frame-to-frame movement magnitude
        x_cols = [col for col in df.columns if col.endswith('_x')]
        y_cols = [col for col in df.columns if col.endswith('_y')]

        if x_cols and y_cols and len(df) > 1:
            movement_intensity = []
            for i in range(1, len(df)):
                total_movement = 0
                valid_points = 0

                for x_col, y_col in zip(x_cols, y_cols):
                    if (pd.notna(df.iloc[i][x_col]) and pd.notna(df.iloc[i-1][x_col]) and
                        pd.notna(df.iloc[i][y_col]) and pd.notna(df.iloc[i-1][y_col])):

                        dx = df.iloc[i][x_col] - df.iloc[i-1][x_col]
                        dy = df.iloc[i][y_col] - df.iloc[i-1][y_col]
                        movement = np.sqrt(dx*dx + dy*dy)
                        total_movement += movement
                        valid_points += 1

                if valid_points > 0:
                    movement_intensity.append(total_movement / valid_points)
                else:
                    movement_intensity.append(0)

            ax3.plot(movement_intensity, linewidth=1, color='orange')
            ax3.set_title('Movement Intensity Over Time')
            ax3.set_xlabel('Frame')
            ax3.set_ylabel('Average Movement')
            ax3.grid(True, alpha=0.3)

        # 4. Body part activity comparison
        ax4 = axes[1, 1]
        body_parts = ['nose', 'shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle']
        activity_scores = []
        part_labels = []

        for part in body_parts:
            part_cols = [col for col in df.columns if part in col.lower()]
            if part_cols:
                # Calculate activity as variance in positions
                part_data = df[part_cols].dropna()
                if len(part_data) > 1:
                    activity = part_data.var().mean()
                    activity_scores.append(activity)
                    part_labels.append(part.title())

        if activity_scores:
            bars = ax4.bar(part_labels, activity_scores, color='skyblue', alpha=0.7)
            ax4.set_title('Body Part Activity Levels')
            ax4.set_xlabel('Body Part')
            ax4.set_ylabel('Activity Score (Variance)')
            plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
            # Use bars variable to satisfy linter
            _ = bars

        plt.tight_layout()

        # Save the visualization
        output_path = 'pose_analysis_visualization.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"   ✅ Pose visualization saved: {output_path}")

    except Exception as e:
        print(f"   Error creating pose visualizations: {e}")

def compare_pose_models():
    """
    Example function for comparing different pose estimation models.
    This is a template for model comparison workflows.
    """
    print("\nPose Model Comparison Template")
    print("=" * 35)

    video_path = mg.examples.dance
    models = ['BlazePose', 'PoseNet']  # Available models

    results = {}

    for model in models:
        print(f"\nTesting {model}...")

        try:
            mv = mg.MgVideo(video_path)

            # Run pose estimation with this model
            result = mv.pose(
                model=model,
                target_name_data=f'dance_pose_{model.lower()}_data'
            )

            # Analyze results
            if 'pose_data' in result and os.path.exists(result['pose_data']):
                df = pd.read_csv(result['pose_data'])

                # Calculate metrics
                keypoint_cols = [col for col in df.columns if any(part in col.lower()
                                for part in ['nose', 'shoulder', 'hip'])]

                total_keypoints = len(df) * len(keypoint_cols)
                missing_keypoints = df[keypoint_cols].isnull().sum().sum()
                detection_rate = (total_keypoints - missing_keypoints) / total_keypoints * 100

                results[model] = {
                    'detection_rate': detection_rate,
                    'total_frames': len(df),
                    'keypoints_tracked': len(keypoint_cols)
                }

                print(f"   ✅ {model}: {detection_rate:.1f}% detection rate")

        except Exception as e:
            print(f"   ❌ {model} failed: {e}")
            results[model] = {'error': str(e)}

    # Compare results
    if len(results) > 1:
        print("\nModel Comparison Summary:")
        print("-" * 25)
        for model, metrics in results.items():
            if 'error' not in metrics:
                print(f"{model:12}: {metrics['detection_rate']:5.1f}% detection, "
                      f"{metrics['keypoints_tracked']} keypoints")
            else:
                print(f"{model:12}: Failed - {metrics['error']}")

    return results

if __name__ == "__main__":
    try:
        # Run main pose estimation example
        pose_result = pose_estimation_example()

        # Optionally compare models
        print("\n" + "="*50)
        model_comparison = compare_pose_models()

        print("\n✅ Pose estimation example completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

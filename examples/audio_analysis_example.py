#!/usr/bin/env python3
"""
Audio Analysis Example - MGT-python

This example demonstrates comprehensive audio analysis features including:
- Waveform visualization
- Spectrograms and mel-spectrograms
- Audio descriptors extraction
- Tempo and beat analysis
- Self-similarity matrices

Author: MGT-python team
"""

import musicalgestures as mg
import os
import pandas as pd
import matplotlib.pyplot as plt

def audio_analysis_example():
    """
    Demonstrate comprehensive audio analysis capabilities.
    """
    print("Audio Analysis Example")
    print("=" * 30)

    # Use the pianist example video (has interesting audio)
    video_path = mg.examples.pianist
    print(f"Processing audio from: {os.path.basename(video_path)}")

    # Create output directory
    output_dir = "audio_output"
    os.makedirs(output_dir, exist_ok=True)

    # Load video - MgVideo inherits audio functionality from MgAudio
    print("\n1. Loading video for audio analysis...")
    mv = mg.MgVideo(video_path)

    print(f"   Video duration: {mv.length:.2f} seconds")
    print(f"   Has audio: {mv.has_audio}")

    # Basic waveform analysis
    print("\n2. Creating waveform visualization...")
    waveform_result = mv.waveform(
        title='Pianist - Audio Waveform',
        target_name=f"{output_dir}/pianist_waveform"
    )

    print(f"   Waveform: {waveform_result}")

    # Spectrogram analysis
    print("\n3. Creating spectrogram...")
    spectrogram_result = mv.spectrogram(
        title='Pianist - Spectrogram',
        target_name=f"{output_dir}/pianist_spectrogram"
    )

    print(f"   Spectrogram: {spectrogram_result}")

    # Audio descriptors
    print("\n4. Extracting audio descriptors...")
    descriptors = mv.descriptors(
        target_name=f"{output_dir}/pianist_audio_descriptors"
    )

    print(f"   Audio descriptors: {descriptors}")

    # Analyze descriptors data
    analyze_audio_descriptors(descriptors)

    # Tempo analysis
    print("\n5. Tempo analysis...")
    tempogram = mv.tempogram(
        target_name=f"{output_dir}/pianist_tempogram"
    )

    print(f"   Tempogram: {tempogram}")

    # Self-similarity matrices
    print("\n6. Creating self-similarity matrices...")

    # MFCC-based SSM
    ssm_result = mv.ssm(
        feature='mfcc',
        target_name=f"{output_dir}/pianist_ssm_mfcc"
    )

    print(f"   SSM result: {ssm_result}")

    # Create comprehensive audio analysis plot
    print("\n7. Creating comprehensive analysis plot...")
    create_audio_summary_plot(descriptors, output_dir)

    print(f"\nAudio analysis complete! Check the '{output_dir}' directory for outputs.")
    return output_dir

def analyze_audio_descriptors(descriptors_path):
    """
    Analyze the audio descriptors data.
    """
    try:
        # Load descriptors data
        df = pd.read_csv(descriptors_path)

        print(f"   Descriptors shape: {df.shape}")
        print(f"   Available features: {list(df.columns)}")

        # Basic statistics for key features
        key_features = ['spectral_centroid', 'spectral_rolloff', 'zero_crossing_rate']
        available_features = [f for f in key_features if f in df.columns]

        if available_features:
            print("\n   Feature Statistics:")
            for feature in available_features:
                mean_val = df[feature].mean()
                std_val = df[feature].std()
                min_val = df[feature].min()
                max_val = df[feature].max()
                print(f"     {feature}:")
                print(f"       Mean: {mean_val:.4f}, Std: {std_val:.4f}")
                print(f"       Range: {min_val:.4f} - {max_val:.4f}")

    except Exception as e:
        print(f"   Could not analyze descriptors: {e}")

def create_audio_summary_plot(descriptors_path, output_dir):
    """
    Create a comprehensive audio analysis summary plot.
    """
    try:
        # Load descriptors data
        df = pd.read_csv(descriptors_path)

        plt.figure(figsize=(16, 12))

        # Define time axis (assuming default hop_size)
        time_frames = len(df)
        time_axis = range(time_frames)

        # Plot 1: Spectral Centroid
        plt.subplot(3, 3, 1)
        if 'spectral_centroid' in df.columns:
            plt.plot(time_axis, df['spectral_centroid'])
            plt.title('Spectral Centroid')
            plt.xlabel('Frame')
            plt.ylabel('Hz')
            plt.grid(True, alpha=0.3)

        # Plot 2: Spectral Rolloff
        plt.subplot(3, 3, 2)
        if 'spectral_rolloff' in df.columns:
            plt.plot(time_axis, df['spectral_rolloff'])
            plt.title('Spectral Rolloff')
            plt.xlabel('Frame')
            plt.ylabel('Hz')
            plt.grid(True, alpha=0.3)

        # Plot 3: Zero Crossing Rate
        plt.subplot(3, 3, 3)
        if 'zero_crossing_rate' in df.columns:
            plt.plot(time_axis, df['zero_crossing_rate'])
            plt.title('Zero Crossing Rate')
            plt.xlabel('Frame')
            plt.ylabel('Rate')
            plt.grid(True, alpha=0.3)

        # Plot 4: MFCC features (first few coefficients)
        plt.subplot(3, 3, 4)
        mfcc_cols = [col for col in df.columns if 'mfcc' in col.lower()][:5]
        if mfcc_cols:
            for i, col in enumerate(mfcc_cols):
                plt.plot(time_axis, df[col], alpha=0.7, label=f'MFCC{i+1}')
            plt.title('MFCC Coefficients (1-5)')
            plt.xlabel('Frame')
            plt.ylabel('Coefficient')
            plt.legend()
            plt.grid(True, alpha=0.3)

        # Plot 5: Chroma features
        plt.subplot(3, 3, 5)
        chroma_cols = [col for col in df.columns if 'chroma' in col.lower()][:6]
        if chroma_cols:
            for col in chroma_cols:
                plt.plot(time_axis, df[col], alpha=0.7)
            plt.title('Chroma Features')
            plt.xlabel('Frame')
            plt.ylabel('Intensity')
            plt.grid(True, alpha=0.3)

        # Plot 6: Spectral Bandwidth
        plt.subplot(3, 3, 6)
        if 'spectral_bandwidth' in df.columns:
            plt.plot(time_axis, df['spectral_bandwidth'])
            plt.title('Spectral Bandwidth')
            plt.xlabel('Frame')
            plt.ylabel('Hz')
            plt.grid(True, alpha=0.3)

        # Plot 7: Tonnetz features
        plt.subplot(3, 3, 7)
        tonnetz_cols = [col for col in df.columns if 'tonnetz' in col.lower()][:3]
        if tonnetz_cols:
            for col in tonnetz_cols:
                plt.plot(time_axis, df[col], alpha=0.7)
            plt.title('Tonnetz Features')
            plt.xlabel('Frame')
            plt.ylabel('Value')
            plt.grid(True, alpha=0.3)

        # Plot 8: Feature correlation heatmap
        plt.subplot(3, 3, 8)
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns[:10]
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            plt.imshow(corr_matrix, cmap='coolwarm', aspect='auto')
            plt.colorbar()
            plt.title('Feature Correlation')
            plt.xticks(range(len(numeric_cols)), numeric_cols, rotation=45)
            plt.yticks(range(len(numeric_cols)), numeric_cols)

        # Plot 9: Feature distribution
        plt.subplot(3, 3, 9)
        if 'spectral_centroid' in df.columns:
            plt.hist(df['spectral_centroid'], bins=30, alpha=0.7, edgecolor='black')
            plt.title('Spectral Centroid Distribution')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Count')
            plt.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save the analysis plot
        plot_path = os.path.join(output_dir, 'audio_analysis_summary.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"   Audio summary plot saved: {plot_path}")

    except Exception as e:
        print(f"   Could not create summary plot: {e}")

if __name__ == "__main__":
    try:
        output_directory = audio_analysis_example()
        print(f"\n✅ Success! All outputs saved to: {output_directory}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

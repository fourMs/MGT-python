import os
import cv2
import numpy as np
from scipy import signal
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import FuncFormatter
import librosa 
import librosa.display

import musicalgestures
from musicalgestures._motionvideo import mg_motiongrams
from musicalgestures._videograms import videograms_ffmpeg
from musicalgestures._mglist import MgList
from musicalgestures._utils import MgProgressbar, MgImage, MgFigure, has_audio, generate_outfilename 

def smooth_downsample_feature_sequence(X, sr, filt_len=41, down_sampling=10, w_type='boxcar'):
    """
    Smoothes and downsamples a feature sequence. Smoothing is achieved by convolution with a filter kernel

    Args:
        X (np.ndarray): Feature sequence.
        sr (int): Sampling rate.
        filt_len (int, optional): Length of smoothing filter. Defaults to 41.
        down_sampling (int, optional): Downsampling factor. Defaults to 10.
        w_type (str, optional): Window type of smoothing filter. Defaults to 'boxcar'.

    Returns:
        X_smooth (np.ndarray): Smoothed and downsampled feature sequence.
        sr_feature (scalar): Sampling rate of `X_smooth`.
    """
    
    def inside(x, pos):
        del pos
        down_sampling = 10
        return str(round(x*down_sampling, 1))
        
    formatter = FuncFormatter(inside)

    filt_kernel = np.expand_dims(signal.get_window(w_type, filt_len), axis=0)
    X_smooth = signal.convolve(X, filt_kernel, mode='same') / filt_len
    X_smooth = X_smooth[:, ::down_sampling]
    sr_feature = sr / down_sampling
    return X_smooth, sr_feature, formatter


def mg_ssm(
        self,
        features='motiongrams',
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        norm=np.inf,
        threshold=0.001,
        cmap='gray_r',
        use_median=False,
        kernel_size=5,
        invert_yaxis=True,
        title=None,
        target_name=None,
        overwrite=False):
    """
    Compute Self-Similarity Matrix (SSM) by converting the input signal into a suitable feature sequence and comparing each element of the feature sequence with all other elements of the sequence.
    SSMs can be computed over different input features such as 'motiongrams', 'spectrogram', 'chromagram' and 'tempogram'.

    Args:
        features (str, optional): Defines the type of features on which to compute SSM. Possible to compute SSM on 'motiongrams', 'videograms', 'spectrogram', 'chromagram' and 'tempogram'. Defaults to 'motiongrams'.
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        norm (int, optional): Normalize the columns of the feature sequence. Possible to compute Manhattan norm (1), Euclidean norm (2), Minimum norm (-np.inf), Maximum norm (np.inf), etc. Defaults to np.inf.
        threshold (float, optional): Only the columns with norm at least the amount of `threshold` indicated are normalized. Defaults to 0.001.
        cmap (str, optional): A Colormap instance or registered colormap name. The colormap maps the C values to colors. Defaults to 'gray_r'.
        use_median (bool, optional): If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
        kernel_size (int, optional):  Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
        invert_axis (bool, optional): Whether to invert the y axis of the SSM. Defaults to True.
        title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
        target_name ([type], optional): Target output name for the SSM. Defaults to None.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        # if features='motiongrams':
        MgList: An MgList pointing to the output SSM images (as MgImages).
        # else:
        MgImage: An MgImage to the output SSM.
    """

    # Save figure to png
    if target_name == None:
        target_name = self.of + '_ssm.png'
    else:
        # enforce png
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    if features == 'motiongrams':
        out_x, out_y = None, None
        target_name_mgx = os.path.splitext(target_name)[0] + '_mgx.png'
        target_name_mgy = os.path.splitext(target_name)[0] + '_mgy.png'

        if not overwrite:
            out_x = generate_outfilename(target_name_mgx)
            out_y = generate_outfilename(target_name_mgy)
        else:
            out_x, out_y = target_name_mgx, target_name_mgy

        mg_motiongrams(
            self,
            filtertype=filtertype,
            thresh=thresh,
            blur=blur,
            use_median=use_median,
            kernel_size=kernel_size,
            inverted_motiongram=False,
            equalize_motiongram=True,
            target_name_mgx=out_x,
            target_name_mgy=out_y,
            overwrite=True)

        pb = MgProgressbar(total=self.length, prefix='Rendering self-similarity matrices:')

        # Normalize feature sequence        
        X = librosa.util.normalize(self.ssm_fig.data[0].astype('float64'), norm=norm, threshold=threshold)
        Y = librosa.util.normalize(self.ssm_fig.data[1].astype('float64'), norm=norm, threshold=threshold)
        # Compute SSM using dot product
        X_ssm = np.dot(np.transpose(X), X)
        Y_ssm = np.dot(np.transpose(Y), Y)

        pb.progress(self.length)
    
       # Plotting Self-Similarity Matrices for motiongrams
        fig = plt.figure(figsize=(8,8))
        gs = gridspec.GridSpec(4, 1)
        
        ax0 = fig.add_subplot(gs[0])
        ax0.xaxis.set_major_locator(MaxNLocator(8))
        if title == None:
            title = ''
        if title == 'filename':
            title = 'Vertical motiongram: ' + os.path.basename(self.of + self.fex)
        ax0.set_title(title)
        if invert_yaxis:
            ax0.invert_yaxis()
        img0 = ax0.imshow(X, aspect='auto', cmap=cmap)
        fig.colorbar(img0, ax=ax0, aspect=15)
        ax0.set_xlabel('')

        ax1 = fig.add_subplot(gs[1:])
        ax1.xaxis.set_major_locator(MaxNLocator(8))
        ax1.yaxis.set_major_locator(MaxNLocator(8))
        img1 = ax1.imshow(X_ssm, aspect='auto', cmap=cmap)
        if invert_yaxis:
            ax1.invert_yaxis()
        ax1.set_xlabel('Time [frames]')
        ax1.set_ylabel('Time [frames]')
        # Normalize colobar
        norm = mpl.colors.Normalize(vmin=0, vmax=1.0)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax1, aspect=50)
        fig.tight_layout()

        plt.savefig(out_x, format='png', facecolor='white', transparent=False)
        plt.close()

        fig = plt.figure(figsize=(8,8))
        gs = gridspec.GridSpec(4, 1)

        ax0 = fig.add_subplot(gs[0])
        ax0.xaxis.set_major_locator(MaxNLocator(8))
        if title == None:
            title = ''
        if title == 'filename':
            title = 'Horizontal motiongram: ' + os.path.basename(self.of + self.fex)
        ax0.set_title(title)
        ax0.invert_yaxis()
        img0 = ax0.imshow(Y, aspect='auto', cmap=cmap)
        fig.colorbar(img0, ax=ax0, aspect=15)
        ax0.set_xlabel('')

        ax1 = fig.add_subplot(gs[1:])
        ax1.xaxis.set_major_locator(MaxNLocator(8))
        ax1.yaxis.set_major_locator(MaxNLocator(8))
        img1 = ax1.imshow(Y_ssm, aspect='auto', cmap=cmap)
        if invert_yaxis:
            ax1.invert_yaxis()
        ax1.set_xlabel('Time [frames]')
        ax1.set_ylabel('Time [frames]')
        # Normalize colorbar
        norm = mpl.colors.Normalize(vmin=0, vmax=1.0)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax1, aspect=50)
        fig.tight_layout()

        plt.savefig(out_y, format='png', facecolor='white', transparent=False)
        plt.close()

        # mg_ssm also saves the motiongrams SSM as MgImages to self.motiongram_x and self.motiongram_y of the parent MgVideo
        return MgList(MgImage(out_x), MgImage(out_y))
    
    elif features == 'videograms':
        out_x, out_y = None, None
        target_name_vgx = os.path.splitext(target_name)[0] + '_vgx.png'
        target_name_vgy = os.path.splitext(target_name)[0] + '_vgy.png'

        if not overwrite:
            out_x = generate_outfilename(target_name_vgx)
            out_y = generate_outfilename(target_name_vgy)
        else:
            out_x, out_y = target_name_vgx, target_name_vgy

        videograms = videograms_ffmpeg(self,
                                       target_name_x=out_x,
                                       target_name_y=out_y,
                                       overwrite=True)

        pb = MgProgressbar(total=self.length, prefix='Rendering self-similarity matrices:')

        # Load videograms and normalize them
        vgx = cv2.cvtColor(cv2.imread(videograms[0].filename), cv2.COLOR_RGB2GRAY)
        vgy = cv2.cvtColor(cv2.imread(videograms[1].filename), cv2.COLOR_RGB2GRAY)

        X = librosa.util.normalize(vgx.astype('float64'), norm=norm, threshold=threshold)
        Y = librosa.util.normalize(vgy.astype('float64'), norm=norm, threshold=threshold)
        # Compute SSM using dot product
        X_ssm = np.dot(np.transpose(X), X)
        Y_ssm = np.dot(np.transpose(Y), Y)

        pb.progress(self.length)
    
       # Plotting Self-Similarity Matrices for motiongrams
        fig = plt.figure(figsize=(8,8))
        gs = gridspec.GridSpec(4, 1)
        
        ax0 = fig.add_subplot(gs[0])
        ax0.xaxis.set_major_locator(MaxNLocator(8))
        if title == None:
            title = ''
        if title == 'filename':
            title = 'Vertical videogram: ' + os.path.basename(self.of + self.fex)
        ax0.set_title(title)
        ax0.invert_yaxis()
        img0 = ax0.imshow(X, aspect='auto', cmap=cmap)
        fig.colorbar(img0, ax=ax0, aspect=15)
        ax0.set_xlabel('')

        ax1 = fig.add_subplot(gs[1:])
        ax1.xaxis.set_major_locator(MaxNLocator(8))
        ax1.yaxis.set_major_locator(MaxNLocator(8))
        img1 = ax1.imshow(X_ssm, aspect='auto', cmap=cmap)
        ax1.invert_yaxis()
        ax1.set_xlabel('Time [frames]')
        ax1.set_ylabel('Time [frames]')
        # Normalize colobar
        norm = mpl.colors.Normalize(vmin=0, vmax=1.0)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax1, aspect=50)
        fig.tight_layout()

        plt.savefig(out_x, format='png', facecolor='white', transparent=False)
        plt.close()

        fig = plt.figure(figsize=(8,8))
        gs = gridspec.GridSpec(4, 1)

        ax0 = fig.add_subplot(gs[0])
        ax0.xaxis.set_major_locator(MaxNLocator(8))
        if title == None:
            title = ''
        if title == 'filename':
            title = 'Horizontal videogram: ' + os.path.basename(self.of + self.fex)
        ax0.set_title(title)
        ax0.invert_yaxis()
        img0 = ax0.imshow(Y, aspect='auto', cmap=cmap)
        fig.colorbar(img0, ax=ax0, aspect=15)
        ax0.set_xlabel('')

        ax1 = fig.add_subplot(gs[1:])
        ax1.xaxis.set_major_locator(MaxNLocator(8))
        ax1.yaxis.set_major_locator(MaxNLocator(8))
        img1 = ax1.imshow(Y_ssm, aspect='auto', cmap=cmap)
        ax1.invert_yaxis()
        ax1.set_xlabel('Time [frames]')
        ax1.set_ylabel('Time [frames]')
        # Normalize colorbar
        norm = mpl.colors.Normalize(vmin=0, vmax=1.0)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax1, aspect=50)
        fig.tight_layout()

        self.ssm_fig = MgFigure(figure=None, figure_type='video.ssm', data=(vgx, vgy), layers=None, image=(target_name_vgx, target_name_vgy))

        plt.savefig(out_y, format='png', facecolor='white', transparent=False)
        plt.close()

        # mg_ssm also saves the motiongrams SSM as MgImages to self.motiongram_x and self.motiongram_y of the parent MgVideo
        return MgList(MgImage(out_x), MgImage(out_y))

    elif features == 'spectrogram':
        pb = MgProgressbar(total=self.length, prefix='Rendering spectrogram SSM:')

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        sr = librosa.get_samplerate(self.filename)
        x, sr = librosa.load(self.filename, sr=sr)
        frame_length = 512
        hop_length = 128
        spectrogram = np.abs(librosa.stft(x, n_fft=frame_length, hop_length=hop_length))

        pb.progress(self.length)

        X, sr_X, formatter = smooth_downsample_feature_sequence(spectrogram, sr/hop_length)
        # Normalize columns of the feature sequence
        X = librosa.util.normalize(X.astype('float64'), norm=norm, threshold=threshold)
        # Compute SSM using dot product
        X_ssm = np.dot(np.transpose(X), X)
       # Plotting SSM for spectrogram
        fig = plt.figure(figsize=(8,8))
        gs = gridspec.GridSpec(4, 1)

        ax0 = fig.add_subplot(gs[0])
        if title == None:
            title = ''
        if title == 'filename':
            title = 'Spectrogram: ' + os.path.basename(self.of + self.fex)
        ax0.set_title(title)
        img0 = librosa.display.specshow(librosa.amplitude_to_db(X, ref=np.max), y_axis='linear', x_axis='time', cmap=cmap, sr=sr, hop_length=hop_length)
        fig.colorbar(img0, ax=ax0, format="%+2.f dB")
        # Format ticks
        ax0.xaxis.set_major_formatter(formatter)
        ax0.xaxis.set_major_locator(MaxNLocator(8))
        ax0.set_xlabel('')
        
        ax1 = fig.add_subplot(gs[1:])
        ax1.xaxis.set_major_locator(MaxNLocator(8))
        ax1.yaxis.set_major_locator(MaxNLocator(8))
        left = - (frame_length / sr) / 2
        right = spectrogram.shape[1] * hop_length / sr + (frame_length / sr) / 2

        img1 = ax1.imshow(librosa.amplitude_to_db(X_ssm, ref=np.max), aspect='auto', cmap=cmap, extent=[left,right,right,left])
        if invert_yaxis:
            ax1.invert_yaxis()
        ax1.set_xlabel('Time [seconds]')
        ax1.set_ylabel('Time [seconds]')
        fig.colorbar(img1, ax=ax1, aspect=50, format="%+2.f dB")
        fig.tight_layout()

        self.ssm_fig = MgFigure(figure=fig, figure_type='audio.ssm', data=X_ssm, layers=None, image=target_name)

        plt.savefig(target_name, format='png', facecolor='white', transparent=False)
        plt.close()

        return MgImage(target_name)

    elif features == 'chromagram':
        pb = MgProgressbar(total=self.length, prefix='Rendering chromagram SSM:')

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        sr = librosa.get_samplerate(self.filename)
        x, sr = librosa.load(self.filename, sr=sr)
        frame_length = 512
        hop_length = 128
        spectrogram = np.abs(librosa.stft(x, n_fft=frame_length, hop_length=hop_length))
        chromagram = librosa.feature.chroma_stft(S=spectrogram, sr=sr, hop_length=hop_length, n_fft=frame_length)

        pb.progress(self.length)

        X, sr_X, formatter = smooth_downsample_feature_sequence(chromagram, sr/hop_length)
        # Normalize feature sequence 
        X = librosa.util.normalize(X.astype('float64'), norm=norm, threshold=threshold)
        # Compute SSM using dot product
        X_ssm = np.dot(np.transpose(X), X)

       # Plotting SSM for chromagram
        fig = plt.figure(figsize=(8,8))
        gs = gridspec.GridSpec(4, 1)

        ax0 = fig.add_subplot(gs[0])
        if title == None:
            title = ''
        if title == 'filename':
            title = 'Chromagram: ' + os.path.basename(self.of + self.fex)
        ax0.set_title(title)
        img0 = librosa.display.specshow(X, y_axis='chroma', x_axis='time', cmap=cmap, sr=sr, hop_length=hop_length)

        # Format ticks
        ax0.xaxis.set_major_formatter(formatter)
        ax0.xaxis.set_major_locator(MaxNLocator(8))
        # Normalize colorbar
        norm = mpl.colors.Normalize(vmin=0, vmax=1.0)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax0, aspect=15)
        ax0.set_xlabel('')
        
        ax1 = fig.add_subplot(gs[1:])
        ax1.xaxis.set_major_locator(MaxNLocator(8))
        ax1.yaxis.set_major_locator(MaxNLocator(8))
        left = - (frame_length / sr) / 2
        right = chromagram.shape[1] * hop_length / sr + (frame_length / sr) / 2

        img1 = ax1.imshow(X_ssm, aspect='auto', cmap=cmap, extent=[left,right,right,left])
        if invert_yaxis:
            ax1.invert_yaxis()
        ax1.set_xlabel('Time [seconds]')
        ax1.set_ylabel('Time [seconds]')
        # Normalize colorbar
        norm = mpl.colors.Normalize(vmin=0, vmax=1.0)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax1, aspect=50)
        fig.tight_layout()

        self.ssm_fig = MgFigure(figure=fig, figure_type='audio.ssm', data=X_ssm, layers=None, image=target_name)

        plt.savefig(target_name, format='png', facecolor='white', transparent=False)
        plt.close()

        return MgImage(target_name)

    elif features == 'tempogram':
        pb = MgProgressbar(total=self.length, prefix='Rendering tempogram SSM:')

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        sr = librosa.get_samplerate(self.filename)
        x, sr = librosa.load(self.filename, sr=sr)
        frame_length = 1024
        hop_length = 512

        oenv = librosa.onset.onset_strength(y=x, sr=sr, hop_length=hop_length)
        tempogram = librosa.feature.tempogram(onset_envelope=oenv, sr=sr, hop_length=hop_length, win_length=frame_length)
        # Estimate the global tempo for display purposes
        tempo = librosa.beat.tempo(onset_envelope=oenv, sr=sr, hop_length=hop_length)[0]

        pb.progress(self.length)

        X, sr_X, formatter = smooth_downsample_feature_sequence(tempogram, sr/hop_length)
        # Normalize feature sequence
        X = librosa.util.normalize(X.astype('float64'), norm=norm, threshold=threshold)
        # Compute SSM using dot product
        X_ssm = np.dot(np.transpose(X), X)

       # Plotting SSM for tempogram
        fig = plt.figure(figsize=(8,8))
        gs = gridspec.GridSpec(4, 1)

        ax0 = fig.add_subplot(gs[0])
        if title == None:
            title = ''
        if title == 'filename':
            title = 'Tempogram: ' + os.path.basename(self.of + self.fex)
        ax0.set_title(title)
        img0 = librosa.display.specshow(X, y_axis='tempo', x_axis='time', cmap=cmap, sr=sr, hop_length=hop_length)
        
        # Normalize colorbar
        norm = mpl.colors.Normalize(vmin=0, vmax=1.0)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax0, aspect=15)
        ax0.axhline(tempo, color='w', linestyle='--', alpha=1, label='Estimated tempo={:g}'.format(tempo))
        ax0.xaxis.set_major_locator(MaxNLocator(8))
        ax0.xaxis.set_major_formatter(formatter)
        ax0.legend(loc='upper right')
        ax0.set_xlabel('')
        
        ax1 = fig.add_subplot(gs[1:])
        ax1.xaxis.set_major_locator(MaxNLocator(8))
        ax1.yaxis.set_major_locator(MaxNLocator(8))
        left = - (frame_length / sr) / 2
        right = tempogram.shape[1] * hop_length / sr + (frame_length / sr) / 2

        img1 = ax1.imshow(X_ssm, aspect='auto', cmap=cmap, extent=[left,right,right,left])
        if invert_yaxis:
            ax1.invert_yaxis()
        ax1.set_xlabel('Time [seconds]')
        ax1.set_ylabel('Time [seconds]')
        norm = mpl.colors.Normalize(vmin=0, vmax=1.0)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax1, aspect=50)
        fig.tight_layout()

        self.ssm_fig = MgFigure(figure=fig, figure_type='audio.ssm', data=X_ssm, layers=None, image=target_name)

        plt.savefig(target_name, format='png', facecolor='white', transparent=False)
        plt.close()

        return MgImage(target_name)

    else:
        print(f'Unrecognized feature: "{features}". Try "motiongrams", "videograms, "spectrogram", "chromagram" or "tempogram".')




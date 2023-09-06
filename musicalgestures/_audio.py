import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib
import numpy as np
from musicalgestures._utils import MgFigure, get_length, generate_outfilename, get_metadata, has_audio

# preventing librosa-matplotlib deadlock
plt.plot()
plt.close()

import warnings
warnings.filterwarnings("ignore")


class MgAudio:
    """
    Class container for audio analysis processes.
    """

    def __init__(
            self, 
            filename,
            sr=22050,
            n_fft=2048, 
            hop_length=512,
            ):
        """
        Initializes the MgAudio class.

        Args:
            filename (str): Path to the audio file. Passed by the parent MgAudio.
            sr (int, optional): Sampling rate of the audio file. Defaults to 22050.
            n_fft (int, optional): Length of the FFT window. Defaults to 2048.
            hop_length (int, optional): Number of samples between successive frames. Defaults to 512.
        """
        
        self.filename = filename
        self.of, self.fex = os.path.splitext(filename)
        self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.length = get_length(self.filename)

    from musicalgestures._ssm import mg_ssm as ssm

    def format_time(self, ax):
            """
            Format time for audio plotting of video file. This is useful if one wants to plot the original time of the video when frames have been skipped beforehand.

            Args:
                ax (str, optional): Axis of the figure.
            """
            # Get original duration from video file
            try:
                original_duration = float(get_metadata(self.filename)[2]['TAG:title'])
            except:
                return 
            
            time = np.round(np.linspace(0, original_duration, 10), 2)
            ax.xaxis.set_major_locator(ticker.MaxNLocator(len(time)))

            # Insert an additional zero at the beginning of the array for visualization
            time = np.insert(time, 0, 0, axis=0) 

            for i, v in enumerate(time):
                if original_duration > 3600:
                    if v > 60:
                        minutes, sec = divmod(v, 60)
                        hour, minutes = divmod(minutes, 60)
                        time[i] = '%d.%02d.%02d' % (hour, minutes, sec)
                else:
                    if v > 60:
                        minutes, sec = divmod(v, 60)
                        time[i] = '%02d.%02d' % (minutes, sec)


            ax.xaxis.set_major_formatter(ticker.FixedFormatter(list(time)))           


    def waveform(self, dpi=300, autoshow=True, raw=False, original_time=True, title=None, target_name=None, overwrite=False):
        """
        Renders a figure showing the waveform of the video/audio file.

        Args:
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            sr (int, optional): Sampling rate of the audio file. Defaults to 22050.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            raw (bool, optional): Whether to show labels and ticks on the plot. Defaults to False.
            original_time (bool, optional): Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to True.
            title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_waveform.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name == None:
            target_name = self.of + '_waveform.png'
        else:
            #enforce png
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)

        fig, ax = plt.subplots(figsize=(12, 4), dpi=dpi)

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # add title
        if title == None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        librosa.display.waveshow(y, sr=sr, ax=ax)
        
        # Adapt audio file plotting when skipping frames of a video file
        if original_time:
            self.format_time(ax)

        if raw:
            fig.patch.set_visible(False)
            fig.suptitle('')
            ax.axis('off')

        plt.tight_layout()    
        plt.savefig(target_name, format='png', transparent=False)

        if not autoshow:
            plt.close()

        # create MgFigure
        data = {
            "sr": sr,
            "of": self.of,
            "y": y,
            "length": self.length
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.waveform',
            data=data,
            layers=None,
            image=target_name)

        return mgf

    def spectrogram(self, fmin=0.0, fmax=None, n_mels=128, power=2, dpi=300, autoshow=True, raw=False, original_time=False, title=None, target_name=None, overwrite=False):
        """
        Renders a figure showing the mel-scaled spectrogram of the video/audio file.

        Args:
            n_mels (int, optional): The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 128.
            fmin (float, optional): Lowest frequency (in Hz). Defaults to 0.0.
            fmax (float, optional): Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0.
            power (float, optional): The steepness of the curve for the color mapping. Defaults to 2.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            raw (bool, optional): Whether to show labels and ticks on the plot. Defaults to False.
            original_time (bool, optional): Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to False.
            title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_spectrogram.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name == None:
            target_name = self.of + '_spectrogram.png'
        else:
            # enforce png
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)

        S = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=n_mels, n_fft=self.n_fft, hop_length=self.hop_length, power=power, fmin=fmin, fmax=fmax)

        fig, ax = plt.subplots(figsize=(12, 6), dpi=dpi)

        # Make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # Add title
        if title == None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        # Display spectrogram
        img = librosa.display.specshow(librosa.power_to_db(S, ref=np.max, top_db=120), 
                                       sr=sr, y_axis='mel', fmin=fmin, fmax=fmax, x_axis='time', hop_length=self.hop_length, ax=ax)

        colorbar_ticks = range(-120, 1, 10)
        cb = fig.colorbar(img, format='%+2.0f dB', ticks=colorbar_ticks)

        # get rid of "default" ticks
        ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

        # ax.set(title=os.path.basename(self.filename))
        plot_xticks = np.arange(0, self.length+0.1, self.length/20)
        ax.set(xticks=plot_xticks)

        freq_ticks = [elem*100 for elem in range(10)]
        freq_ticks = []
        freq = 100
        while freq < sr/2:
            freq_ticks.append(freq)
            freq *= 1.3

        freq_ticks = [round(elem, -2) for elem in freq_ticks]
        freq_ticks.append(sr/2)
        freq_ticks_labels = [str(round(elem/1000, 1)) + 'k' if elem > 1000 else int(round(elem)) for elem in freq_ticks]

        ax.set(yticks=(freq_ticks))
        ax.set(yticklabels=(freq_ticks_labels))

        # Adapt the plotting of the audio file's time when skipping frames of a video file
        if original_time:
            self.format_time(ax)

        if raw:
            fig.patch.set_visible(False)
            fig.suptitle('')
            ax.axis('off')
            cb.remove()

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        if not autoshow:
            plt.close()

        # create MgFigure
        data = {
            "hop_size": self.hop_length,
            "sr": sr,
            "of": self.of,
            "S": S,
            "length": self.length
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.spectrogram',
            data=data,
            layers=None,
            image=target_name)

        return mgf

    def tempogram(self, dpi=300, autoshow=True, raw=False, original_time=False, title=None, target_name=None, overwrite=False):
        """
        Renders a figure with a plots of onset strength and tempogram of the video/audio file.

        Args:
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            raw (bool, optional): Whether to show labels and ticks on the plot. Defaults to False.
            original_time (bool, optional): Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to False.
            title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempogram.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name == None:
            target_name = self.of + '_tempogram.png'
        else:
            #enforce png
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)

        oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=self.hop_length)

        tempogram = librosa.feature.tempogram(
            onset_envelope=oenv, sr=sr, hop_length=self.hop_length)

        # Estimate the global tempo for display purposes
        tempo = librosa.beat.tempo(
            onset_envelope=oenv, sr=sr, hop_length=self.hop_length)[0]

        fig, ax = plt.subplots(nrows=2, figsize=(12, 6), dpi=dpi, sharex=True)

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # add title
        if title == None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        times = librosa.times_like(oenv, sr=sr, hop_length=self.hop_length)

        ax[0].plot(times, oenv, label='Onset strength')
        ax[0].label_outer()
        ax[0].legend(frameon=True)

        librosa.display.specshow(tempogram, sr=sr, hop_length=self.hop_length,
                                 x_axis='time', y_axis='tempo', cmap='magma', ax=ax[1])
        ax[1].axhline(tempo, color='w', linestyle='--', alpha=1,
                      label='Estimated tempo={:g}'.format(tempo))
        ax[1].legend(loc='upper right')
        ax[1].set(title='Tempogram')

        # Adapt the plotting of the audio file's time when skipping frames of a video file
        if original_time:
            self.format_time(ax[1])

        if raw:
            fig.patch.set_visible(False)
            fig.suptitle('')
            ax.axis('off')

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        if not autoshow:
            plt.close()

        # create MgFigure
        data = {
            "hop_size": self.hop_length,
            "sr": sr,
            "of": self.of,
            "times": times,
            "onset_env": oenv,
            "tempogram": tempogram,
            "tempo": tempo
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.tempogram',
            data=data,
            layers=None,
            image=target_name)

        return mgf
    
    def hpss(self, n_mels=128, fmin=0.0, fmax=None, kernel_size=31, margin=(1.0,5.0), power=2.0, mask=False, residual=False, dpi=300, autoshow=True, original_time=False, title=None, target_name=None, overwrite=False):
        """
        Renders a figure with a plots of harmonic and percussive components of the audio file.

        Args:
            n_mels (int, optional): Number of Mel bands to generate. Defaults to 128.
            fmin (float, optional): Lowest frequency (in Hz). Defaults to 0.0.
            fmax (float, optional): Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0.
            kernel_size (int or tuple, optional): Kernel size(s) for the median filters. If tuple, the first value specifies the width of the harmonic filter, and the second value specifies the width of the percussive filter. Defaults to 31.
            margin (float or tuple, optional): Margin size(s) for the masks (as described in this [paper](https://archives.ismir.net/ismir2014/paper/000127.pdf)). If tuple, the first value specifies the margin of the harmonic mask, and the second value specifies the margin of the percussive mask. Defaults to (1.0,5.0).
            power (float, optional): Exponent for the Wiener filter when constructing soft mask matrices. Defaults to 2.0.
            mask (bool, optional): Return the masking matrices instead of components. Defaults to False.
            residual (bool, optional): Whether to return residual components of the audio file or not. Defaults to False.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            original_time (bool, optional): Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to False.
            title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempogram.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name == None:
            target_name = self.of + '_hpss.png'
        else:
            #enforce png
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)
        D = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length, n_mels=n_mels, fmin=fmin, fmax=fmax)

        # Separate into harmonic and percussive components
        H, P = librosa.decompose.hpss(D, kernel_size=kernel_size, margin=margin, power=power, mask=mask)

        if residual:
            fig, ax = plt.subplots(nrows=3, figsize=(12, 8), dpi=dpi, sharex=True)
        else:
            fig, ax = plt.subplots(nrows=2, figsize=(12, 6), dpi=dpi, sharex=True)

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # add title
        if title == None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        librosa.display.specshow(librosa.amplitude_to_db(np.abs(H), ref=np.max(np.abs(D))), 
                                sr=sr, hop_length=self.hop_length, fmin=fmin, fmax=fmax, x_axis='time', y_axis='mel', cmap='magma', ax=ax[0]
                                )
        ax[0].set(title='Harmonic')

        librosa.display.specshow(librosa.amplitude_to_db(np.abs(P), ref=np.max(np.abs(D))), 
                                sr=sr, hop_length=self.hop_length, fmin=fmin, fmax=fmax, x_axis='time', y_axis='mel', cmap='magma', ax=ax[1]
                                )
        ax[1].set(title='Percussive')

        # Adapt the plotting of the audio file's time when skipping frames of a video file
        if original_time:
            self.format_time(ax[1])

        if residual:
            R = D - (H + P)
            librosa.display.specshow(librosa.amplitude_to_db(np.abs(R), ref=np.max(np.abs(D))), 
                        sr=sr, hop_length=self.hop_length, fmin=fmin, fmax=fmax, x_axis='time', y_axis='mel', cmap='magma', ax=ax[2]
                        )
            ax[2].set(title='Residual')

            # Adapt the plotting of the audio file's time when skipping frames of a video file
            if original_time:
                self.format_time(ax[2])

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        if not autoshow:
            plt.close()

        # create MgFigure
        data = {
            "hop_size": self.hop_length,
            "sr": sr,
            "of": self.of,
            "mel_spectrogram": D,
            "harmonic": H,
            "percussive": P,
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.hpss',
            data=data,
            layers=None,
            image=target_name)

        return mgf


    def descriptors(self, n_mels=128, fmin=0.0, fmax=None, power=2, dpi=300, autoshow=True, original_time=False, title=None, target_name=None, overwrite=False):
        """
        Renders a figure of plots showing spectral/loudness descriptors, including RMS energy, spectral flatness, centroid, bandwidth, rolloff of the video/audio file.

        Args:
            n_mels (int, optional): The number of mel filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 128.
            fmin (float, optional): Lowest frequency (in Hz). Defaults to 0.0.
            fmax (float, optional): Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0
            power (float, optional): The steepness of the curve for the color mapping. Defaults to 2.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            original_time (bool, optional): Whether to plot original time or not. This parameter can be useful if the file has been shortened beforehand (e.g. skip). Defaults to False.
            title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_descriptors.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """
        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name == None:
            target_name = self.of + '_descriptors.png'
        else:
            #enforce png
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)

        cent = librosa.feature.spectral_centroid(
            y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length)
        spec_bw = librosa.feature.spectral_bandwidth(
            y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length)
        flatness = librosa.feature.spectral_flatness(
            y=y, n_fft=self.n_fft, hop_length=self.hop_length)
        rolloff = librosa.feature.spectral_rolloff(
            y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length, roll_percent=0.99)
        rolloff_min = librosa.feature.spectral_rolloff(
            y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length, roll_percent=0.01)
        rms = librosa.feature.rms(
            y=y, frame_length=self.n_fft, hop_length=self.hop_length)
        
        S = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=n_mels, n_fft=self.n_fft, hop_length=self.hop_length, power=power, fmin=fmin, fmax=fmax)

        fig, ax = plt.subplots(figsize=(12, 8), dpi=dpi, nrows=3, sharex=True)

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # add title
        if title == None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        img = librosa.display.specshow(librosa.power_to_db(
            S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmin=fmin, fmax=fmax, x_axis='time', hop_length=self.hop_length, ax=ax[2])

        # get rid of "default" ticks
        ax[2].yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

        # ax[0].set(title=os.path.basename(self.filename))
        plot_xticks = np.arange(0, self.length+0.1, self.length/20)
        ax[2].set(xticks=plot_xticks)

        freq_ticks = [elem*100 for elem in range(10)]
        freq_ticks = [250]
        freq = 500
        while freq < sr/2:
            freq_ticks.append(freq)
            freq *= 1.5

        freq_ticks = [round(elem, -1) for elem in freq_ticks]
        freq_ticks_labels = [str(round(elem/1000, 1)) +
                             'k' if elem > 1000 else int(round(elem)) for elem in freq_ticks]

        ax[2].set(yticks=(freq_ticks))
        ax[2].set(yticklabels=(freq_ticks_labels))

        times = librosa.times_like(
            cent, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length)

        ax[2].fill_between(times, cent[0] - spec_bw[0], cent[0] +
                           spec_bw[0], alpha=0.5, label='Centroid +- bandwidth')
        ax[2].plot(times, cent.T, label='Centroid', color='y')
        ax[2].plot(times, rolloff[0], label='Roll-off frequency (0.99)')
        ax[2].plot(times, rolloff_min[0], color='r',
                   label='Roll-off frequency (0.01)')

        # ax[2].legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax[2].legend(loc='upper right')

        ax[1].plot(times, flatness.T, label='Flatness', color='y')
        # ax[1].legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax[1].legend(loc='upper right')

        ax[0].semilogy(times, rms[0], label='RMS Energy')
        # ax[0].legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax[0].legend(loc='upper right')

        # Adapt the plotting of the audio file's time when skipping frames of a video file
        if original_time:
            self.format_time(ax[2])
        
        plt.tight_layout()
        if autoshow:
            plt.savefig(target_name, format='png', transparent=False)
        else:
            plt.close()

        # create MgFigure
        data = {
            "hop_size": self.hop_length,
            "sr": sr,
            "of": self.of,
            "times": times,
            "S": S,
            "length": self.length,
            "cent": cent,
            "spec_bw": spec_bw,
            "rolloff": rolloff,
            "rolloff_min": rolloff_min,
            "flatness": flatness,
            "rms": rms
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.descriptors',
            data=data,
            layers=None,
            image=target_name)

        return mgf
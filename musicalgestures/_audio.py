import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib
import numpy as np

from musicalgestures._utils import MgFigure, get_length, generate_outfilename, has_audio
from musicalgestures._info import mg_info as info
from musicalgestures._colored import MgAudioProcessor, MgWaveformImage

import warnings
warnings.filterwarnings("ignore")

# preventing librosa-matplotlib deadlock
plt.plot()
plt.close()


class MgAudio:
    """
    Class container for audio analysis processes.
    """

    def __init__(
            self, 
            filename,
            sr=None,
            n_fft=2048, 
            hop_length=512,
            ):
        """
        Initializes the MgAudio class.

        Args:
            filename (str): Path to the audio file. Passed by the parent MgVideo.
            sr (int, optional): Sampling rate of the audio file. Possible to specify a target sampling rate. Defaults to None (i.e. original sampling rate).
            n_fft (int, optional): Length of the FFT window. Defaults to 2048.
            hop_length (int, optional): Number of samples between successive frames. Defaults to 512.
        """
        
        self.filename = filename
        self.of, self.fex = os.path.splitext(filename)
        if sr is None:
            self.sr = librosa.get_samplerate(self.filename)
        else:
            self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.length = get_length(self.filename)

    from musicalgestures._ssm import mg_ssm as ssm

    def numpy(self):
        "Read the original file of the MgAudio object as a numpy array using librosa."
        self.y, self.sr = librosa.load(self.filename, sr=self.sr)
        return self.y


    def format_time(self, ax, original_time=True, original_duration=None):
            """
            Format time for audio plotting of video file. This is useful if one wants to plot the original time of the video when frames have been skipped beforehand.

            Args:
                ax (str, optional): Axis of the figure.
                original_time (bool, optional): Whether to get the original time for audio plotting or not. Defaults to True.
                original_duration (bool, optional): Whether to add the original duration of the file to be formatted manually. Defaults to None.
            """
            # Get original duration from video file
            try:
                if original_duration is not None:
                    original_duration = original_duration
                else:
                    if original_time:
                        original_duration = float(info(self.filename)[2]['TAG:title'])
                    else:
                        original_duration = float(info(self.filename)[2]['duration'])
            except:
                return 

            time = np.round(np.linspace(0, original_duration, 10), 1)

            for i, v in enumerate(time):
                if original_duration > 3600:
                    minutes, sec = divmod(v, 60)
                    hour, minutes = divmod(minutes, 60)
                    time[i] = '%d.%02d.%02d' % (hour, minutes, sec)
                if original_duration > 60:
                    minutes, sec = divmod(v, 60)
                    time[i] = '%02d.%02d' % (minutes, sec)

            ax.xaxis.set_major_locator(ticker.LinearLocator(numticks=10))
            if original_duration > 60:
                ax.xaxis.set_major_formatter(ticker.FixedFormatter(list(map(lambda x: str(x).replace('.', ':'), list(time)))))
            else:  
                ax.xaxis.set_major_formatter(ticker.FixedFormatter(list(time)))

    def waveform(self, dpi=300, autoshow=True, raw=False, colored=False, image_width=2500, image_height=500, fmin=500, fmax=None, cmap='freesound', original_time=True, title=None, target_name=None, overwrite=False):
        """
        Renders a figure showing the waveform of the video/audio file.

        Args:
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            raw (bool, optional): Whether to show labels and ticks on the plot. Defaults to False.
            colored (bool, optional): Whether to create a colored waveform image (freesound-style) from an audio input file. Defauts to False.
            image_width (int, optional): Number of pixels for the colored waveform image width. Defaults to 2500.
            image_height (int, optional): Number of pixels for the colored waveform image height. Defaults to 500.
            fmin (int, optional): Minimum frequency for computing spectral centroid for the colored waveform image. Defaults to 500.
            fmax (int, optional): Maximum frequency for computing spectral centroid for the colored waveform image. Defaults to None (i.e. Nyquist frequency).
            cmap (str, optional): Colormap used for coloring the waveform, all colormaps included with matplotlib can be used. Defaults to 'freesound'.
            original_time (bool, optional): Whether to plot original time or not. This parameter can be useful if the video file has been shortened beforehand (e.g. skip). Defaults to True.
            title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_waveform.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name is None:
            target_name = self.of + '_waveform.png'
        else:
            #enforce png
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        if colored:
            # Process audio chunks and compute spectral centroid for creating the colored waveform
            processor = MgAudioProcessor(self.filename, self.n_fft, fmin, fmax)
            y = MgWaveformImage(image_width, image_height, cmap)
            sr = processor.audio_file.samplerate

            samples_per_pixel = processor.audio_file.frames / float(image_width)
            
            for x in range(image_width):
                seek_point = int(x * samples_per_pixel)
                next_seek_point = int((x + 1) * samples_per_pixel)
                spectral_centroid = processor.spectral_centroid(seek_point) 
                peaks = processor.peaks(seek_point, next_seek_point)        
                y.draw_peaks(x, peaks, spectral_centroid) 
        else:
            y, sr = librosa.load(self.filename, sr=self.sr)

        fig, ax = plt.subplots(figsize=(12, 4), dpi=dpi)
        fig.patch.set_facecolor('white') # make sure background is white
        fig.patch.set_alpha(1)

        # add title
        if title is None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        if colored:
            # Get the original duration of the audio file and format it to HH:MM:SS
            original_duration = float(processor.audio_file.frames / processor.audio_file.samplerate)
            self.format_time(ax, original_duration=original_duration)
            ax.imshow(y.image.astype('uint8'), interpolation='nearest')
            # Replace yticks with values between -1 and 1 for practicalities
            ax.yaxis.set_major_locator(ticker.LinearLocator(numticks=len(ax.get_yticks())))

            if abs(processor.max_level) < 0.1 or abs(processor.min_level) < 0.1:
                ax.yaxis.set_major_formatter(ticker.FixedFormatter(list(np.round(np.linspace(processor.max_level, processor.min_level, len(ax.get_yticks())),2))))
            else:
                print(abs(processor.max_level), abs(processor.min_level))
                ax.yaxis.set_major_formatter(ticker.FixedFormatter(list(np.round(np.linspace(processor.max_level, processor.min_level, len(ax.get_yticks())),1))))

        else:
            # Adapt audio file plotting when skipping frames of a video file
            self.format_time(ax, original_time=original_time)
            librosa.display.waveshow(y, sr=sr, ax=ax)

        if raw:
            fig.patch.set_visible(False)
            fig.suptitle('')
            ax.axis('off')

        fig.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        # Always close the pyplot figure: the returned MgFigure displays the saved
        # PNG via its rich repr, so leaving the figure open would cause the inline
        # backend to render a second (duplicate) copy in notebooks.
        plt.close(fig)

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


    def spectrogram(self, fmin=0.0, fmax=None, n_mels=128, power=2.0, top_db=80.0, dpi=300, autoshow=True, raw=False, original_time=False, title=None, target_name=None, overwrite=False):
        """
        Renders a figure showing the mel-scaled spectrogram of the video/audio file.

        Args:
            n_mels (int, optional): The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 128.
            fmin (float, optional): Lowest frequency (in Hz). Defaults to 0.0.
            fmax (float, optional): Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0.
            power (float, optional): The steepness of the curve for the color mapping. Defaults to 2.
            top_db (float, optional): threshold the output at top_db below the peak: max(20 * log10(S/ref)) - top_db. Defaults to 80.0.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            raw (bool, optional): Whether to show labels and ticks on the plot. Defaults to False.
            original_time (bool, optional): Whether to plot original time or not. This parameter can be useful if the video file has been shortened beforehand (e.g. skip). Defaults to False.
            title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_spectrogram.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name is None:
            target_name = self.of + '_spectrogram.png'
        else:
            # enforce png
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)

        S = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=n_mels, n_fft=self.n_fft, hop_length=self.hop_length, power=power, fmin=fmin, fmax=fmax)

        fig, ax = plt.subplots(figsize=(12, 4), dpi=dpi)
        # Add title
        if title is None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)
        
        fig.patch.set_facecolor('white') # make sure background is white
        fig.patch.set_alpha(1)

        # Display spectrogram
        img = librosa.display.specshow(librosa.power_to_db(S, ref=np.max, top_db=top_db), 
                                       sr=sr, y_axis='mel', fmin=fmin, fmax=fmax, x_axis='time', hop_length=self.hop_length, ax=ax)

        colorbar_ticks = range(-120, 1, 10)
        cb = fig.colorbar(img, format='%+2.0f dB', ticks=colorbar_ticks)

        # get rid of "default" ticks
        ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

        # Pin the time axis to the actual spectrogram extent so the container
        # duration (which can be longer than the decoded audio) does not leave
        # trailing whitespace or mislabel the timeline.
        xmax = S.shape[1] * self.hop_length / sr
        ax.set_xlim(0, xmax)

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
        self.format_time(ax, original_time, original_duration=None if original_time else xmax)

        if raw:
            fig.patch.set_visible(False)
            fig.suptitle('')
            ax.axis('off')
            cb.remove()

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        # Always close the pyplot figure: the returned MgFigure displays the saved
        # PNG via its rich repr, so leaving the figure open would cause the inline
        # backend to render a second (duplicate) copy in notebooks.
        plt.close(fig)

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
            original_time (bool, optional): Whether to plot original time or not. This parameter can be useful if the video file has been shortened beforehand (e.g. skip). Defaults to False.
            title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempogram.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name is None:
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

        fig, ax = plt.subplots(nrows=2, figsize=(12, 4), dpi=dpi, sharex=True)
        fig.patch.set_facecolor('white') # make sure background is white
        fig.patch.set_alpha(1)

        # add title
        if title is None:
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
        self.format_time(ax[1], original_time)

        if raw:
            fig.patch.set_visible(False)
            fig.suptitle('')
            ax.axis('off')

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        # Always close the pyplot figure: the returned MgFigure displays the saved
        # PNG via its rich repr, so leaving the figure open would cause the inline
        # backend to render a second (duplicate) copy in notebooks.
        plt.close(fig)

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
    
    def hpss(self, dim=2, n_mels=128, fmin=0.0, fmax=None, kernel_size=31, margin=(1.0,5.0), power=2.0, top_db=80.0, mask=False, residual=False, dpi=300, autoshow=True, original_time=False, title=None, target_name=None, overwrite=False):
        """
        Renders a figure with a plots of harmonic and percussive components of the audio file.

        Args:
            dim (str, optional): Whether to plot hpss in one (i.e. waveform) or two (i.e. spectrogram) dimensions. Defaults to 2.
            n_mels (int, optional): Number of Mel bands to generate. Defaults to 128.
            fmin (float, optional): Lowest frequency (in Hz). Defaults to 0.0.
            fmax (float, optional): Highest frequency (in Hz). Defaults to None, use fmax = sr / 2.0.
            kernel_size (int or tuple, optional): Kernel size(s) for the median filters. If tuple, the first value specifies the width of the harmonic filter, and the second value specifies the width of the percussive filter. Defaults to 31.
            margin (float or tuple, optional): Margin size(s) for the masks (as described in this [paper](https://archives.ismir.net/ismir2014/paper/000127.pdf)). If tuple, the first value specifies the margin of the harmonic mask, and the second value specifies the margin of the percussive mask. Defaults to (1.0,5.0).
            power (float, optional): Exponent for the Wiener filter when constructing soft mask matrices. Defaults to 2.0.
            top_db (float, optional): threshold the output at top_db below the peak: max(20 * log10(S/ref)) - top_db. Defaults to 80.0.
            mask (bool, optional): Return the masking matrices instead of components. Defaults to False.
            residual (bool, optional): Whether to return residual components of the audio file or not. Defaults to False.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            original_time (bool, optional): Whether to plot original time or not. This parameter can be useful if the video file has been shortened beforehand (e.g. skip). Defaults to False.
            title (str, optional): Optionally add title to the figure. Possible to set the filename as the title using the string 'filename'. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_hpss.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name is None:
            target_name = self.of + '_hpss.png'
        else:
            #enforce png
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)
        if dim == 2:
            D = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length, n_mels=n_mels, fmin=fmin, fmax=fmax)
            # Separate into harmonic and percussive components
            H, P = librosa.decompose.hpss(D, kernel_size=kernel_size, margin=margin, power=power, mask=mask)
        elif dim == 1:
            h, p = librosa.effects.hpss(y)
        else:
            print('MgAudio.hpss() can only be computed on 1 (i.e. waveform) or 2 (i.e. spectrogram) dimensions.')
            return

        if dim == 2:
            if residual:
                fig, ax = plt.subplots(nrows=3, figsize=(12, 8), dpi=dpi, sharex=True)
            else:
                fig, ax = plt.subplots(nrows=2, figsize=(12, 6), dpi=dpi, sharex=True)

            # Display spectrograms
            librosa.display.specshow(
                librosa.amplitude_to_db(np.abs(H), ref=np.max(np.abs(D)), top_db=top_db), sr=sr, hop_length=self.hop_length, 
                fmin=fmin, fmax=fmax, x_axis='time', y_axis='mel', cmap='magma', ax=ax[0]
                                )
            librosa.display.specshow(
                librosa.amplitude_to_db(np.abs(P), ref=np.max(np.abs(D)), top_db=top_db), sr=sr, hop_length=self.hop_length, 
                fmin=fmin, fmax=fmax, x_axis='time', y_axis='mel', cmap='magma', ax=ax[1]
                                )
            ax[0].set(title='Harmonic')
            ax[1].set(title='Percussive')

        else:
            fig, ax = plt.subplots(figsize=(12, 4), dpi=dpi, sharex=True)
            librosa.display.waveshow(
                h, sr=sr, alpha=0.5, label='Harmonic'
                                     )
            librosa.display.waveshow(
                p, sr=sr, alpha=0.5, label='Percussive'
                                     )

        fig.patch.set_facecolor('white') # make sure background is white
        fig.patch.set_alpha(1)

        # add title
        if title is None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        if residual:
            if dim == 2:
                R = D - (H + P)
                librosa.display.specshow(
                    librosa.amplitude_to_db(np.abs(R), ref=np.max(np.abs(D)), top_db=top_db), sr=sr, hop_length=self.hop_length, 
                    fmin=fmin, fmax=fmax, x_axis='time', y_axis='mel', cmap='magma', ax=ax[2]
                            )
                ax[2].set(title='Residual')

            else:
                r = y - (h + p)
                librosa.display.waveshow(
                    r, sr=sr, alpha=0.5, label='Residual'
                                     )

        # Adapt the plotting of the audio file's time when skipping frames of a video file
        if dim == 2:
            if residual:
                self.format_time(ax[2], original_time)
            else:
                self.format_time(ax[1], original_time)
        else:
            self.format_time(ax, original_time)

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        if dim == 1:
            # Add labels to plot
            plt.legend()

        # Always close the pyplot figure: the returned MgFigure displays the saved
        # PNG via its rich repr, so leaving the figure open would cause the inline
        # backend to render a second (duplicate) copy in notebooks.
        plt.close(fig)

        # create MgFigure
        if dim == 2:
            data = {
                "hop_size": self.hop_length,
                "sr": sr,
                "of": self.of,
                "mel_spectrogram": D,
                "harmonic": H,
                "percussive": P,
            }
        else:
            data = {
                "hop_size": self.hop_length,
                "sr": sr,
                "of": self.of,
                "waveform": y,
                "harmonic": h,
                "percussive": p,
            }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.hpss',
            data=data,
            layers=None,
            image=target_name)

        return mgf


    def descriptors(self, n_mels=128, fmin=0.0, fmax=None, power=2, dpi=300, autoshow=True, original_time=False, title=None, target_name=None, save_data=False, data_format='csv', target_name_data=None, overwrite=False):
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
            save_data (bool, optional): Whether to also save the per-frame descriptor time series (time, RMS, centroid, bandwidth, rolloff, rolloff_min, flatness) to a data file. Defaults to False.
            data_format (str/list, optional): Format of the saved descriptor data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple formats, use a list, e.g. ['csv', 'txt']. Defaults to 'csv'.
            target_name_data (str, optional): The name of the output data file. Defaults to None (which uses the input filename with the suffix "_descriptors").
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """
        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name is None:
            target_name = self.of + '_descriptors.png'
        else:
            # enforce png
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
        # add title
        if title is None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        librosa.display.specshow(librosa.power_to_db(
            S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmin=fmin, fmax=fmax, x_axis='time', hop_length=self.hop_length, ax=ax[2])

        # get rid of "default" ticks
        ax[2].yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

        # Pin the time axis to the actual spectrogram extent (see spectrogram()).
        xmax = S.shape[1] * self.hop_length / sr
        ax[2].set_xlim(0, xmax)

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
        self.format_time(ax[2], original_time, original_duration=None if original_time else xmax)

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        # Always close the pyplot figure: the returned MgFigure displays the saved
        # PNG via its rich repr, so leaving the figure open would cause the inline
        # backend to render a second (duplicate) copy in notebooks.
        plt.close(fig)

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

        # Optionally save the per-frame descriptor time series to disk
        if save_data:
            columns = {
                'Time': times,
                'RMS': rms[0],
                'Centroid': cent[0],
                'Bandwidth': spec_bw[0],
                'Rolloff': rolloff[0],
                'RolloffMin': rolloff_min[0],
                'Flatness': flatness[0],
            }
            _save_audio_data(self.of + '_descriptors', columns, data_format, target_name_data, overwrite)

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.descriptors',
            data=data,
            layers=None,
            image=target_name)

        return mgf

    def chromagram(self, n_chroma=12, norm=np.inf, chroma_type='cqt', cmap='coolwarm', dpi=300, autoshow=True, raw=False, original_time=False, title=None, target_name=None, overwrite=False):
        """
        Renders a figure showing the chromagram of the video/audio file.

        A chromagram maps audio energy onto the 12 pitch classes (C, C#, D, …, B) over time,
        making it useful for analysing harmony and chord progressions.

        Args:
            n_chroma (int, optional): Number of chroma bins (pitch classes). Defaults to 12.
            norm (float or None, optional): Column-wise normalisation. np.inf gives maximum-norm,
                1 gives L1-norm, 2 gives L2-norm, None disables normalisation. Defaults to np.inf.
            chroma_type (str, optional): Algorithm used to compute the chroma features.
                'cqt'  — Constant-Q transform (best for music, handles low frequencies well).
                'stft' — Short-time Fourier transform (faster, slightly lower pitch resolution).
                'cens' — Chroma Energy Normalised Statistics (robust to dynamics and timbre).
                Defaults to 'cqt'.
            cmap (str, optional): Matplotlib colormap for the chromagram display. Defaults to 'coolwarm'.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            raw (bool, optional): Whether to show labels and ticks on the plot. Defaults to False.
            original_time (bool, optional): Whether to plot original time or not. Defaults to False.
            title (str, optional): Optionally add title to the figure. Use 'filename' to set the filename as title. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_chromagram.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """
        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name is None:
            target_name = self.of + '_chromagram.png'
        else:
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)

        chroma_type = chroma_type.lower()
        if chroma_type == 'cqt':
            chroma = librosa.feature.chroma_cqt(
                y=y, sr=sr, hop_length=self.hop_length, n_chroma=n_chroma, norm=norm)
        elif chroma_type == 'stft':
            chroma = librosa.feature.chroma_stft(
                y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length, n_chroma=n_chroma, norm=norm)
        elif chroma_type == 'cens':
            chroma = librosa.feature.chroma_cens(
                y=y, sr=sr, hop_length=self.hop_length, n_chroma=n_chroma, norm=norm)
        else:
            print(f"Unknown chroma_type '{chroma_type}'. Use 'cqt', 'stft', or 'cens'.")
            return

        fig, ax = plt.subplots(figsize=(12, 4), dpi=dpi)
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        if title is None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        img = librosa.display.specshow(
            chroma, sr=sr, hop_length=self.hop_length,
            x_axis='time', y_axis='chroma', cmap=cmap, ax=ax)

        fig.colorbar(img, ax=ax)
        ax.set(title=f'Chromagram ({chroma_type.upper()})')

        self.format_time(ax, original_time)

        if raw:
            fig.patch.set_visible(False)
            fig.suptitle('')
            ax.axis('off')

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        # Always close the pyplot figure: the returned MgFigure displays the saved
        # PNG via its rich repr, so leaving the figure open would cause the inline
        # backend to render a second (duplicate) copy in notebooks.
        plt.close(fig)

        data = {
            "hop_size": self.hop_length,
            "sr": sr,
            "of": self.of,
            "chroma": chroma,
            "chroma_type": chroma_type,
            "n_chroma": n_chroma,
            "length": self.length,
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.chromagram',
            data=data,
            layers=None,
            image=target_name)

        return mgf

    def mfcc(self, n_mfcc=13, cmap='RdBu_r', dpi=300, autoshow=True, raw=False, original_time=False, title=None, target_name=None, overwrite=False):
        """
        Renders a figure showing the Mel-frequency cepstral coefficients (MFCCs) of the video/audio file.

        MFCCs compactly describe the spectral envelope (timbre) of a sound over time and are
        widely used as features for audio classification and similarity.

        Args:
            n_mfcc (int, optional): Number of MFCCs to compute. Defaults to 13.
            cmap (str, optional): Matplotlib colormap for the display. Defaults to 'RdBu_r'.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            raw (bool, optional): Whether to show labels and ticks on the plot. Defaults to False.
            original_time (bool, optional): Whether to plot original time or not. Defaults to False.
            title (str, optional): Optionally add title to the figure. Use 'filename' to set the filename as title. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_mfcc.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object referring to the internal figure and its data.
        """
        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name is None:
            target_name = self.of + '_mfcc.png'
        else:
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)

        mfccs = librosa.feature.mfcc(
            y=y, sr=sr, n_mfcc=n_mfcc, n_fft=self.n_fft, hop_length=self.hop_length)

        fig, ax = plt.subplots(figsize=(12, 4), dpi=dpi)
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        if title is None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        img = librosa.display.specshow(
            mfccs, sr=sr, hop_length=self.hop_length, x_axis='time', cmap=cmap, ax=ax)
        fig.colorbar(img, ax=ax)
        ax.set(ylabel='MFCC coefficient', title='MFCC')

        self.format_time(ax, original_time)

        if raw:
            fig.patch.set_visible(False)
            fig.suptitle('')
            ax.axis('off')

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        # Always close the pyplot figure: the returned MgFigure displays the saved
        # PNG via its rich repr, so leaving the figure open would cause the inline
        # backend to render a second (duplicate) copy in notebooks.
        plt.close(fig)

        data = {
            "hop_size": self.hop_length,
            "sr": sr,
            "of": self.of,
            "mfcc": mfccs,
            "n_mfcc": n_mfcc,
            "length": self.length,
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.mfcc',
            data=data,
            layers=None,
            image=target_name)

        return mgf

    def tempo(self, dpi=300, autoshow=True, raw=False, original_time=False, title=None, target_name=None, overwrite=False):
        """
        Estimates tempo and beat positions, and renders the waveform with beat markers.

        Uses librosa's beat tracker. In addition to the figure, the returned object's
        ``.data`` dictionary contains the estimated tempo, beat times, inter-beat
        intervals, a beat-regularity measure, and circular beat statistics (phase
        deviation of each beat from a fitted ideal grid, plus a Rayleigh test of
        timing consistency).

        Args:
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            raw (bool, optional): Whether to show labels and ticks on the plot. Defaults to False.
            original_time (bool, optional): Whether to plot original time or not. Defaults to False.
            title (str, optional): Optionally add title to the figure. Use 'filename' to set the filename as title. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempo.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object. Access numeric results via ``.data``:
                'tempo', 'beat_times', 'ibi', 'beat_regularity', 'beat_phases',
                'deviations_s', 'R_beat', 'mu_beat', 'T_fit', 't0_fit', 'p_rayleigh'.
        """
        from musicalgestures._analysis import circular_stats, rayleigh_test

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        if target_name is None:
            target_name = self.of + '_tempo.png'
        else:
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        y, sr = librosa.load(self.filename, sr=self.sr)

        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=self.hop_length)
        tempo = float(np.atleast_1d(tempo)[0])

        # Beat regularity from inter-beat intervals
        if len(beat_times) > 1:
            ibi = np.diff(beat_times)
            beat_regularity = float(1.0 - ibi.std() / ibi.mean()) if ibi.mean() > 0 else 0.0
        else:
            ibi = np.array([0.0])
            beat_regularity = 0.0

        # Circular beat statistics: fit an ideal grid and measure phase deviations
        if len(beat_times) >= 4:
            k = np.arange(len(beat_times))
            T_fit, t0_fit = np.polyfit(k, beat_times, 1)
            deviations_s = beat_times - (t0_fit + k * T_fit)
            beat_phases = (deviations_s / T_fit) * 2 * np.pi % (2 * np.pi)
            R_beat, mu_beat = circular_stats(beat_phases)
            _, p_rayleigh = rayleigh_test(beat_phases)
        else:
            beat_phases = deviations_s = np.array([])
            T_fit, t0_fit = (60.0 / tempo if tempo > 0 else 0.0), 0.0
            R_beat = mu_beat = 0.0
            p_rayleigh = 1.0

        fig, ax = plt.subplots(figsize=(12, 4), dpi=dpi)
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        if title is None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        librosa.display.waveshow(y, sr=sr, ax=ax, alpha=0.6)
        for bt in beat_times:
            ax.axvline(bt, color='r', alpha=0.6, linewidth=0.8)
        ax.set(title=f'Tempo: {tempo:.1f} BPM   |   Beats: {len(beat_times)}   |   Regularity: {beat_regularity:.1%}')

        self.format_time(ax, original_time)

        if raw:
            fig.patch.set_visible(False)
            fig.suptitle('')
            ax.axis('off')

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        # Always close the pyplot figure: the returned MgFigure displays the saved
        # PNG via its rich repr, so leaving the figure open would cause the inline
        # backend to render a second (duplicate) copy in notebooks.
        plt.close(fig)

        data = {
            "sr": sr,
            "of": self.of,
            "length": self.length,
            "tempo": tempo,
            "beat_times": beat_times,
            "ibi": ibi,
            "beat_regularity": beat_regularity,
            "beat_phases": beat_phases,
            "deviations_s": deviations_s,
            "R_beat": R_beat,
            "mu_beat": mu_beat,
            "T_fit": T_fit,
            "t0_fit": t0_fit,
            "p_rayleigh": p_rayleigh,
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.tempo',
            data=data,
            layers=None,
            image=target_name)

        return mgf

    def beat_statistics(self, n_bins=32, cmap='YlOrRd', dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
        """
        Renders circular statistics of beat-timing consistency.

        Fits an ideal isochronous beat grid to the detected beats and visualises how
        each beat deviates from it: a polar histogram of beat phases (with the mean
        resultant vector) and a time series of millisecond deviations. This reveals
        whether a performer rushes, drags, or keeps steady time.

        Args:
            n_bins (int, optional): Number of bins in the polar phase histogram. Defaults to 32.
            cmap (str, optional): Matplotlib colormap for the polar histogram. Defaults to 'YlOrRd'.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            title (str, optional): Optionally add title to the figure. Use 'filename' to set the filename as title. Defaults to None.
            target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_beatstats.png" should be used).
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

        Returns:
            MgFigure: An MgFigure object whose ``.data`` mirrors the beat statistics from tempo(),
                or None if fewer than four beats are detected.
        """
        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        # Reuse tempo() for the beat analysis (without showing its figure)
        beat_mgf = self.tempo(autoshow=False, overwrite=overwrite)
        if beat_mgf is None:
            return
        plt.close(beat_mgf.figure)
        d = beat_mgf.data

        beat_phases = d["beat_phases"]
        if len(beat_phases) < 4:
            print('Not enough beats detected for circular statistics (need at least 4).')
            return

        if target_name is None:
            target_name = self.of + '_beatstats.png'
        else:
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        deviations_ms = d["deviations_s"] * 1000
        R, mu = d["R_beat"], d["mu_beat"]

        fig = plt.figure(figsize=(14, 6), dpi=dpi)
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # Polar histogram of beat phases
        ax_p = fig.add_subplot(121, projection='polar')
        bin_edges = np.linspace(0, 2 * np.pi, n_bins + 1)
        counts, _ = np.histogram(beat_phases, bins=bin_edges)
        theta_c = (bin_edges[:-1] + bin_edges[1:]) / 2
        norm_c = counts / (counts.max() + 1e-9)
        ax_p.bar(theta_c, counts, width=2 * np.pi / n_bins * 0.88,
                 color=matplotlib.colormaps[cmap](norm_c), alpha=0.85,
                 edgecolor='white', linewidth=0.3)
        if counts.max() > 0:
            ax_p.annotate('', xy=(np.radians(mu), R * counts.max()), xytext=(0, 0),
                          arrowprops=dict(arrowstyle='-|>', color='#333333', lw=2.0, mutation_scale=16))
        ax_p.set_xticks([0, np.pi / 2, np.pi, 3 * np.pi / 2])
        ax_p.set_xticklabels(['on beat', '1/4 late', '1/2', '1/4 early'], fontsize=8)
        ax_p.set_title(f'Beat phase deviation\nR = {R:.3f}   μ = {mu:.1f}°   p = {d["p_rayleigh"]:.4f}', fontsize=10)

        # Time series of deviations
        ax_t = fig.add_subplot(122)
        sc = ax_t.scatter(d["beat_times"], deviations_ms, c=d["beat_times"], cmap='plasma', s=18, alpha=0.8)
        ax_t.axhline(0, color='#888888', lw=1.0, ls='--', alpha=0.7)
        ax_t.axhline(float(deviations_ms.mean()), color='#1f77b4', lw=1.2, ls=':',
                     label=f'mean {float(deviations_ms.mean()):.1f} ms')
        ax_t.set(xlabel='Time (s)', ylabel='Deviation from ideal grid (ms)', title='Beat timing deviation')
        ax_t.legend()
        cb = fig.colorbar(sc, ax=ax_t)
        cb.set_label('Time (s)')

        if title is None:
            title = ''
        if title == 'filename':
            title = os.path.basename(self.filename)
        fig.suptitle(f'{title}   Tempo: {d["tempo"]:.1f} BPM   σ = {float(deviations_ms.std()):.1f} ms'.strip(),
                     fontsize=13, fontweight='bold')

        plt.tight_layout(rect=[0, 0, 1, 0.93])
        plt.savefig(target_name, format='png', transparent=False)

        # Always close the pyplot figure: the returned MgFigure displays the saved
        # PNG via its rich repr, so leaving the figure open would cause the inline
        # backend to render a second (duplicate) copy in notebooks.
        plt.close(fig)

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.beat_statistics',
            data=d,
            layers=None,
            image=target_name)

        return mgf

def _save_audio_data(of, columns, data_format, target_name_data, overwrite):
    """
    Save a dictionary of equal-length 1-D arrays as a data file (csv/tsv/txt).

    Mirrors how motion data is saved in motion(): supports 'csv', 'tsv', and 'txt'
    (a single format string or a list of formats).

    Args:
        of (str): Output path stem (without extension).
        columns (dict): Ordered mapping of column name -> 1-D array of values.
        data_format (str or list): One or more of 'csv', 'tsv', 'txt'.
        target_name_data (str or None): Optional explicit output path stem.
        overwrite (bool): Whether to overwrite or auto-increment the filename.
    """
    import pandas as pd

    # Align to the shortest column length to be safe
    n = min(len(np.asarray(v).ravel()) for v in columns.values())
    df = pd.DataFrame({k: np.asarray(v).ravel()[:n] for k, v in columns.items()})

    formats = data_format if isinstance(data_format, (list, tuple)) else [data_format]
    stem = target_name_data if target_name_data is not None else of
    stem = os.path.splitext(stem)[0]

    written = []
    for fmt in formats:
        fmt = fmt.lower()
        if fmt not in ('csv', 'tsv', 'txt'):
            print(f"Unknown data_format '{fmt}', skipping. Use 'csv', 'tsv' or 'txt'.")
            continue
        target = stem + '.' + fmt
        if not overwrite:
            target = generate_outfilename(target)
        sep = ',' if fmt == 'csv' else '\t'
        df.to_csv(target, sep=sep, index=False)
        written.append(target)

    return written

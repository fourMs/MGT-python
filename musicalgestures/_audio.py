import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from musicalgestures._utils import MgImage, MgFigure, get_length, has_audio, generate_outfilename
import musicalgestures

# preventing librosa-matplotlib deadlock
plt.plot()
plt.close()

import warnings
from matplotlib import MatplotlibDeprecationWarning
# suppress "Pysoundfile Failed" warnings when dealing with mp3 files/audio tracks
warnings.filterwarnings("ignore", "PySoundFile failed. Trying audioread instead.", category=UserWarning, module="librosa")
# suppress librosa MatplotlibDeprecationWarnings
warnings.filterwarnings("ignore", "", category=MatplotlibDeprecationWarning, module="librosa")


class Audio:
    """
    Class container for audio analysis processes.
    """

    def __init__(self, filename):
        """
        Initializes the Audio class.

        Args:
            filename (str): Path to the video file. Passed by the parent MgObject.
        """
        self.filename = filename
        self.of, self.fex = os.path.splitext(filename)


    def waveform(self, mono=False, dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
        """
        Renders a figure showing the waveform of the video/audio file.

        Args:
            mono (bool, optional): Convert the signal to mono. Defaults to False.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            title (str, optional): Optionally add title to the figure. Defaults to None, which uses the file name as a title. Defaults to None.
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

        y, sr = librosa.load(self.filename, sr=None, mono=mono)

        length = get_length(self.filename)

        fig, ax = plt.subplots(figsize=(12, 4), dpi=dpi)

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # add title
        if title == None:
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        librosa.display.waveplot(y, sr=sr, ax=ax)

        plt.tight_layout()

        plt.savefig(target_name, format='png', transparent=False)

        if not autoshow:
            plt.close()

        # create MgFigure
        data = {
            "sr": sr,
            "of": self.of,
            "y": y,
            "length": length
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.waveform',
            data=data,
            layers=None,
            image=target_name)

        return mgf

    def spectrogram(self, window_size=4096, overlap=8, mel_filters=512, power=2, dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
        """
        Renders a figure showing the mel-scaled spectrogram of the video/audio file.

        Args:
            window_size (int, optional): The size of the FFT frame. Defaults to 4096.
            overlap (int, optional): The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
            mel_filters (int, optional): The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
            power (float, optional): The steepness of the curve for the color mapping. Defaults to 2.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            title (str, optional): Optionally add title to the figure. Defaults to None, which uses the file name as a title.
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
            #enforce png
            target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        hop_size = int(window_size / overlap)

        y, sr = librosa.load(self.filename, sr=None)

        S = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=mel_filters, fmax=sr/2, n_fft=window_size, hop_length=hop_size, power=power)

        fig, ax = plt.subplots(figsize=(12, 6), dpi=dpi)

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # add title
        if title == None:
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        img = librosa.display.specshow(librosa.power_to_db(
            S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmax=sr/2, x_axis='time', hop_length=hop_size, ax=ax)

        colorbar_ticks = range(-120, 1, 10)
        fig.colorbar(img, format='%+2.0f dB', ticks=colorbar_ticks)

        # get rid of "default" ticks
        ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

        # ax.set(title=os.path.basename(self.filename))
        length = get_length(self.filename)
        plot_xticks = np.arange(0, length+0.1, length/20)
        ax.set(xticks=plot_xticks)

        freq_ticks = [elem*100 for elem in range(10)]
        freq_ticks = []
        freq = 100
        while freq < sr/2:
            freq_ticks.append(freq)
            freq *= 1.3

        freq_ticks = [round(elem, -2) for elem in freq_ticks]
        freq_ticks.append(sr/2)
        freq_ticks_labels = [str(round(elem/1000, 1)) +
                             'k' if elem > 1000 else int(round(elem)) for elem in freq_ticks]

        ax.set(yticks=(freq_ticks))
        ax.set(yticklabels=(freq_ticks_labels))

        plt.tight_layout()

        plt.savefig(target_name, format='png', transparent=False)

        if not autoshow:
            plt.close()

        # create MgFigure
        data = {
            "hop_size": hop_size,
            "sr": sr,
            "of": self.of,
            "S": S,
            "length": length
        }

        mgf = MgFigure(
            figure=fig,
            figure_type='audio.spectrogram',
            data=data,
            layers=None,
            image=target_name)

        return mgf

    def descriptors(self, window_size=4096, overlap=8, mel_filters=512, power=2, dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
        """
        Renders a figure of plots showing spectral/loudness descriptors, including RMS energy, spectral flatness, centroid, bandwidth, rolloff of the video/audio file.

        Args:
            window_size (int, optional): The size of the FFT frame. Defaults to 4096.
            overlap (int, optional): The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
            mel_filters (int, optional): The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
            power (float, optional): The steepness of the curve for the color mapping. Defaults to 2.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            title (str, optional): Optionally add title to the figure. Defaults to None, which uses the file name as a title.
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

        hop_size = int(window_size / overlap)

        y, sr = librosa.load(self.filename, sr=None)

        cent = librosa.feature.spectral_centroid(
            y=y, sr=sr, n_fft=window_size, hop_length=hop_size)
        spec_bw = librosa.feature.spectral_bandwidth(
            y=y, sr=sr, n_fft=window_size, hop_length=hop_size)
        flatness = librosa.feature.spectral_flatness(
            y=y, n_fft=window_size, hop_length=hop_size)
        rolloff = librosa.feature.spectral_rolloff(
            y=y, sr=sr, n_fft=window_size, hop_length=hop_size, roll_percent=0.99)
        rolloff_min = librosa.feature.spectral_rolloff(
            y=y, sr=sr, n_fft=window_size, hop_length=hop_size, roll_percent=0.01)
        rms = librosa.feature.rms(
            y=y, frame_length=window_size, hop_length=hop_size)

        S = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=mel_filters, fmax=sr/2, n_fft=window_size, hop_length=hop_size, power=power)

        fig, ax = plt.subplots(figsize=(12, 8), dpi=dpi, nrows=3, sharex=True)

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # add title
        if title == None:
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        img = librosa.display.specshow(librosa.power_to_db(
            S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmax=sr/2, x_axis='time', hop_length=hop_size, ax=ax[2])

        # get rid of "default" ticks
        ax[2].yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

        # ax[0].set(title=os.path.basename(self.filename))
        length = get_length(self.filename)
        plot_xticks = np.arange(0, length+0.1, length/20)
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
            cent, sr=sr, n_fft=window_size, hop_length=hop_size)

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

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)

        if not autoshow:
            plt.close()

        # create MgFigure
        data = {
            "hop_size": hop_size,
            "sr": sr,
            "of": self.of,
            "times": times,
            "S": S,
            "length": length,
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

    def tempogram(self, window_size=4096, overlap=8, mel_filters=512, power=2, dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
        """
        Renders a figure with a plots of onset strength and tempogram of the video/audio file.

        Args:
            window_size (int, optional): The size of the FFT frame. Defaults to 4096.
            overlap (int, optional): The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
            mel_filters (int, optional): The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
            power (float, optional): The steepness of the curve for the color mapping. Defaults to 2.
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            title (str, optional): Optionally add title to the figure. Defaults to None, which uses the file name as a title.
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

        hop_size = int(window_size / overlap)

        y, sr = librosa.load(self.filename, sr=None)

        oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_size)

        tempogram = librosa.feature.tempogram(
            onset_envelope=oenv, sr=sr, hop_length=hop_size)

        # Estimate the global tempo for display purposes
        tempo = librosa.beat.tempo(
            onset_envelope=oenv, sr=sr, hop_length=hop_size)[0]

        fig, ax = plt.subplots(nrows=2, figsize=(10, 6), dpi=dpi, sharex=True)

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        # add title
        if title == None:
            title = os.path.basename(self.filename)
        fig.suptitle(title, fontsize=16)

        times = librosa.times_like(oenv, sr=sr, hop_length=hop_size)

        ax[0].plot(times, oenv, label='Onset strength')
        ax[0].label_outer()
        ax[0].legend(frameon=True)

        librosa.display.specshow(tempogram, sr=sr, hop_length=hop_size,
                                 x_axis='time', y_axis='tempo', cmap='magma', ax=ax[1])
        ax[1].axhline(tempo, color='w', linestyle='--', alpha=1,
                      label='Estimated tempo={:g}'.format(tempo))
        ax[1].legend(loc='upper right')
        ax[1].set(title='Tempogram')

        plt.savefig(target_name, format='png', transparent=False)

        if not autoshow:
            plt.close()

        # create MgFigure
        data = {
            "hop_size": hop_size,
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

def mg_audio_waveform(filename=None, mono=False, dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
    """
    Renders a figure showing the waveform of the video/audio file.

    Args:
        filename (str, optional): Path to the audio/video file to be processed. Defaults to None.
        mono (bool, optional): Convert the signal to mono. Defaults to False.
        dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
        autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
        title (str, optional): Optionally add title to the figure. Defaults to None, which uses the file name as a title. Defaults to None.
        target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_waveform.png" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgFigure: An MgFigure object referring to the internal figure and its data.
    """

    if filename == None:
        print("No filename was given.")
        return

    if not has_audio(filename):
        print('The video has no audio track.')
        return

    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '_waveform.png'
    else:
        #enforce png
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    y, sr = librosa.load(filename, sr=None, mono=mono)

    length = get_length(filename)

    fig, ax = plt.subplots(figsize=(12, 4), dpi=dpi)

    # make sure background is white
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)

    # add title
    if title == None:
        title = os.path.basename(filename)
    fig.suptitle(title, fontsize=16)

    librosa.display.waveplot(y, sr=sr, ax=ax)

    plt.tight_layout()

    plt.savefig(target_name, format='png', transparent=False)

    if not autoshow:
        plt.close()

    # create MgFigure
    data = {
        "sr": sr,
        "of": of,
        "y": y,
        "length": length
    }

    mgf = MgFigure(
        figure=fig,
        figure_type='audio.waveform',
        data=data,
        layers=None,
        image=target_name)

    return mgf


def mg_audio_spectrogram(filename=None, window_size=4096, overlap=8, mel_filters=512, power=2, dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
    """
    Renders a figure showing the mel-scaled spectrogram of the video/audio file.

    Args:
        filename (str, optional): Path to the audio/video file to be processed. Defaults to None.
        window_size (int, optional): The size of the FFT frame. Defaults to 4096.
        overlap (int, optional): The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
        mel_filters (int, optional): The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
        power (float, optional): The steepness of the curve for the color mapping. Defaults to 2.
        dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
        autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
        title (str, optional): Optionally add title to the figure. Defaults to None, which uses the file name as a title.
        target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_spectrogram.png" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgFigure: An MgFigure object referring to the internal figure and its data.
    """

    if filename == None:
        print("No filename was given.")
        return

    if not has_audio(filename):
        print('The video has no audio track.')
        return

    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '_spectrogram.png'
    else:
        #enforce png
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    hop_size = int(window_size / overlap)

    y, sr = librosa.load(filename, sr=None)

    S = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=mel_filters, fmax=sr/2, n_fft=window_size, hop_length=hop_size, power=power)

    fig, ax = plt.subplots(figsize=(12, 6), dpi=dpi)

    # make sure background is white
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)

    # add title
    if title == None:
        title = os.path.basename(filename)
    fig.suptitle(title, fontsize=16)

    img = librosa.display.specshow(librosa.power_to_db(
        S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmax=sr/2, x_axis='time', hop_length=hop_size, ax=ax)

    colorbar_ticks = range(-120, 1, 10)
    fig.colorbar(img, format='%+2.0f dB', ticks=colorbar_ticks)

    # get rid of "default" ticks
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

    # ax.set(title=os.path.basename(filename))
    length = get_length(filename)
    plot_xticks = np.arange(0, length+0.1, length/20)
    ax.set(xticks=plot_xticks)

    freq_ticks = [elem*100 for elem in range(10)]
    freq_ticks = []
    freq = 100
    while freq < sr/2:
        freq_ticks.append(freq)
        freq *= 1.3

    freq_ticks = [round(elem, -2) for elem in freq_ticks]
    freq_ticks.append(sr/2)
    freq_ticks_labels = [str(round(elem/1000, 1)) +
                         'k' if elem > 1000 else int(round(elem)) for elem in freq_ticks]

    ax.set(yticks=(freq_ticks))
    ax.set(yticklabels=(freq_ticks_labels))

    plt.tight_layout()

    plt.savefig(target_name, format='png', transparent=False)

    if not autoshow:
        plt.close()

    # create MgFigure
    data = {
        "hop_size": hop_size,
        "sr": sr,
        "of": of,
        "S": S,
        "length": length
    }

    mgf = MgFigure(
        figure=fig,
        figure_type='audio.spectrogram',
        data=data,
        layers=None,
        image=target_name)

    return mgf


def mg_audio_descriptors(filename=None, window_size=4096, overlap=8, mel_filters=512, power=2, dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
    """
    Renders a figure of plots showing spectral/loudness descriptors, including RMS energy, spectral flatness, centroid, bandwidth, rolloff of the video/audio file.

    Args:
        filename (str, optional): Path to the audio/video file to be processed. Defaults to None.
        window_size (int, optional): The size of the FFT frame. Defaults to 4096.
        overlap (int, optional): The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
        mel_filters (int, optional): The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
        power (float, optional): The steepness of the curve for the color mapping. Defaults to 2.
        dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
        autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
        title (str, optional): Optionally add title to the figure. Defaults to None, which uses the file name as a title.
        target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_descriptors.png" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgFigure: An MgFigure object referring to the internal figure and its data.
    """

    if filename == None:
        print("No filename was given.")
        return

    if not has_audio(filename):
        print('The video has no audio track.')
        return

    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '_descriptors.png'
    else:
        #enforce png
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    hop_size = int(window_size / overlap)

    y, sr = librosa.load(filename, sr=None)

    cent = librosa.feature.spectral_centroid(
        y=y, sr=sr, n_fft=window_size, hop_length=hop_size)
    spec_bw = librosa.feature.spectral_bandwidth(
        y=y, sr=sr, n_fft=window_size, hop_length=hop_size)
    flatness = librosa.feature.spectral_flatness(
        y=y, n_fft=window_size, hop_length=hop_size)
    rolloff = librosa.feature.spectral_rolloff(
        y=y, sr=sr, n_fft=window_size, hop_length=hop_size, roll_percent=0.99)
    rolloff_min = librosa.feature.spectral_rolloff(
        y=y, sr=sr, n_fft=window_size, hop_length=hop_size, roll_percent=0.01)
    rms = librosa.feature.rms(
        y=y, frame_length=window_size, hop_length=hop_size)

    S = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=mel_filters, fmax=sr/2, n_fft=window_size, hop_length=hop_size, power=power)

    fig, ax = plt.subplots(figsize=(12, 8), dpi=dpi, nrows=3, sharex=True)

    # make sure background is white
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)

    # add title
    if title == None:
        title = os.path.basename(filename)
    fig.suptitle(title, fontsize=16)

    img = librosa.display.specshow(librosa.power_to_db(
        S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmax=sr/2, x_axis='time', hop_length=hop_size, ax=ax[2])

    # get rid of "default" ticks
    ax[2].yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

    # ax[0].set(title=os.path.basename(filename))
    length = get_length(filename)
    plot_xticks = np.arange(0, length+0.1, length/20)
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
        cent, sr=sr, n_fft=window_size, hop_length=hop_size)

    ax[2].fill_between(times, cent[0] - spec_bw[0], cent[0] +
                       spec_bw[0], alpha=0.5, label='Centroid +- bandwidth')
    ax[2].plot(times, cent.T, label='Centroid', color='y')
    ax[2].plot(times, rolloff[0], label='Roll-off frequency (0.99)')
    ax[2].plot(times, rolloff_min[0], color='r',
               label='Roll-off frequency (0.01)')

    ax[2].legend(loc='upper right')

    ax[1].plot(times, flatness.T, label='Flatness', color='y')
    ax[1].legend(loc='upper right')

    ax[0].semilogy(times, rms[0], label='RMS Energy')
    ax[0].legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(target_name, format='png', transparent=False)

    if not autoshow:
        plt.close()

    # create MgFigure
    data = {
        "hop_size": hop_size,
        "sr": sr,
        "of": of,
        "times": times,
        "S": S,
        "length": length,
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


def mg_audio_tempogram(filename=None, window_size=4096, overlap=8, mel_filters=512, power=2, dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
    """
    Renders a figure with a plots of onset strength and tempogram of the video/audio file.

    Args:
        filename (str, optional): Path to the audio/video file to be processed. Defaults to None.
        window_size (int, optional): The size of the FFT frame. Defaults to 4096.
        overlap (int, optional): The window overlap. The hop size is window_size / overlap. Example: window_size=1024, overlap=4 -> hop=256. Defaults to 8.
        mel_filters (int, optional): The number of filters to use for filtering the frequency domain. Affects the vertical resolution (sharpness) of the spectrogram. NB: Too high values with relatively small window sizes can result in artifacts (typically black lines) in the resulting image. Defaults to 512.
        power (float, optional): The steepness of the curve for the color mapping. Defaults to 2.
        dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
        autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
        title (str, optional): Optionally add title to the figure. Defaults to None, which uses the file name as a title.
        target_name (str, optional): The name of the output image. Defaults to None (which assumes that the input filename with the suffix "_tempogram.png" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgFigure: An MgFigure object referring to the internal figure and its data.
    """

    if filename == None:
        print("No filename was given.")
        return

    if not has_audio(filename):
        print('The video has no audio track.')
        return

    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '_tempogram.png'
    else:
        #enforce png
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    hop_size = int(window_size / overlap)

    y, sr = librosa.load(filename, sr=None)

    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_size)

    tempogram = librosa.feature.tempogram(
        onset_envelope=oenv, sr=sr, hop_length=hop_size)

    # Estimate the global tempo for display purposes
    tempo = librosa.beat.tempo(
        onset_envelope=oenv, sr=sr, hop_length=hop_size)[0]

    fig, ax = plt.subplots(nrows=2, figsize=(10, 6), dpi=dpi, sharex=True)

    # make sure background is white
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)

    # add title
    if title == None:
        title = os.path.basename(filename)
    fig.suptitle(title, fontsize=16)

    times = librosa.times_like(oenv, sr=sr, hop_length=hop_size)

    ax[0].plot(times, oenv, label='Onset strength')
    ax[0].label_outer()
    ax[0].legend(frameon=True)

    librosa.display.specshow(tempogram, sr=sr, hop_length=hop_size,
                             x_axis='time', y_axis='tempo', cmap='magma', ax=ax[1])
    ax[1].axhline(tempo, color='w', linestyle='--', alpha=1,
                  label='Estimated tempo={:g}'.format(tempo))
    ax[1].legend(loc='upper right')
    ax[1].set(title='Tempogram')

    plt.savefig(target_name, format='png', transparent=False)

    if not autoshow:
        plt.close()

    # create MgFigure
    data = {
        "hop_size": hop_size,
        "sr": sr,
        "of": of,
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

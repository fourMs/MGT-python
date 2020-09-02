import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from musicalgestures._utils import MgImage, extract_wav, get_length, has_audio
import musicalgestures


class Audio:
    """
    Class container for audio functions.

    Attributes
    ----------
    - filename : str

        Path to the input video file. Passed by parent MgObject.

    - has_audio : bool

        Indicates whether source video file has an audio track. Passed by parent MgObject.

    Methods
    -------
    - spectrogram()

        Renders a mel-scaled spectrogram of the video/audio file.
    - descriptors()

        Renders a plot of spectral/loudness descriptors, including RMS energy, spectral flatness,
        centroid, bandwidth, rolloff

    """

    def __init__(self, filename):
        self.filename = filename
        self.of, self.fex = os.path.splitext(filename)

    def spectrogram(self, window_size=4096, overlap=8, mel_filters=512, power=2, autoshow=False):
        """
        Renders a mel-scaled spectrogram of the video/audio file.

        Parameters
        ----------
        - window_size : int, optional

            The size of the FFT frame. Default is 4096.

        - overlap : int, optional

            The window overlap. The hop size is window_size / overlap.
            Example: window_size=1024, overlap=4 -> hop=256

        - mel_filters : int, optional

            The number of filters to use for filtering the frequency domain. Affects the
            vertical resolution (sharpness) of the spectrogram. NB: Too high values with
            relatively small window sizes can result in artifacts (typically black lines)
            in the resulting image. Default is 512.

        - power : int, float

            The steepness of the curve for the color mapping. Default is 2.

        - autoshow: bool, optional

            Whether to show the resulting plot automatically. Default is `False` (plot is not shown).

        Outputs
        -------

        - `self.filename` + '_spectrogram.png'

        Returns
        -------
        - MgPlot

            An MgPlot object referring to the output plot and its analysis data.
        """

        if not has_audio(self.filename):
            print('The video has no audio track.')
            return

        hop_size = int(window_size / overlap)

        y, sr = librosa.load(self.filename, sr=None)

        S = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=mel_filters, fmax=sr/2, n_fft=window_size, hop_length=hop_size, power=power)

        fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

        img = librosa.display.specshow(librosa.power_to_db(
            S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmax=sr/2, x_axis='time', hop_length=hop_size, ax=ax)

        colorbar_ticks = range(-120, 1, 10)
        fig.colorbar(img, format='%+2.0f dB', ticks=colorbar_ticks)

        # get rid of "default" ticks
        ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

        ax.set(title=os.path.basename(self.filename))
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

        plt.savefig('%s_spectrogram.png' % self.of, format='png')

        if not autoshow:
            plt.close()

        return MgImage(self.of + '_spectrogram.png')


def mg_spectrogram(filename=None, window_size=4096, overlap=8, mel_filters=512, power=2, autoshow=False):
    """
    Renders a mel-scaled spectrogram of the video/audio file.

    Parameters
    ----------
    - window_size : int, optional

        The size of the FFT frame. Default is 4096.

    - overlap : int, optional

        The window overlap. The hop size is window_size / overlap.
        Example: window_size=1024, overlap=4 -> hop=256

    - mel_filters : int, optional

        The number of filters to use for filtering the frequency domain. Affects the
        vertical resolution (sharpness) of the spectrogram. NB: Too high values with
        relatively small window sizes can result in artifacts (typically black lines)
        in the resulting image. Default is 512.

    - power : int, float

        The steepness of the curve for the color mapping. Default is 2.

    - autoshow: bool, optional

        Whether to show the resulting plot automatically. Default is `False` (plot is not shown).

    Outputs
    -------

    - `filename` + '_spectrogram.png'

    Returns
    -------
    - MgImage

        An MgImage object referring to the output image file.
    """
    if filename == None:
        return

    if not has_audio(filename):
        print('The video has no audio track.')
        return

    of, fex = os.path.splitext(filename)

    hop_size = int(window_size / overlap)

    y, sr = librosa.load(filename, sr=None)

    S = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=mel_filters, fmax=sr/2, n_fft=window_size, hop_length=hop_size, power=power)

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

    img = librosa.display.specshow(librosa.power_to_db(
        S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmax=sr/2, x_axis='time', hop_length=hop_size, ax=ax)

    colorbar_ticks = range(-120, 1, 10)
    fig.colorbar(img, format='%+2.0f dB', ticks=colorbar_ticks)

    # get rid of "default" ticks
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

    ax.set(title=os.path.basename(filename))
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

    plt.savefig('%s_spectrogram.png' % of, format='png')

    if not autoshow:
        plt.close()

    return MgImage(of + '_spectrogram.png')

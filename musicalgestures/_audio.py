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
        centroid, bandwidth, rolloff of the video/audio file.

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

    def descriptors(self, window_size=4096, overlap=8, mel_filters=512, power=2, autoshow=False):
        """
        Renders a plot of spectral/loudness descriptors, including RMS energy, spectral flatness,
        centroid, bandwidth, rolloff of the video/audio file.

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

        - `self.filename` + '_descriptors.png'

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

        fig, ax = plt.subplots(figsize=(12, 8), dpi=300, nrows=3, sharex=True)

        img = librosa.display.specshow(librosa.power_to_db(
            S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmax=sr/2, x_axis='time', hop_length=hop_size, ax=ax[2])

        # get rid of "default" ticks
        ax[2].yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

        ax[0].set(title=os.path.basename(self.filename))
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
        ax[2].plot(times, cent.T, label='Centroid', color='w')
        ax[2].plot(times, rolloff[0], label='Roll-off frequency (0.99)')
        ax[2].plot(times, rolloff_min[0], color='r',
                   label='Roll-off frequency (0.01)')

        ax[2].legend(loc='upper left', bbox_to_anchor=(1, 1))

        ax[1].plot(times, flatness.T, label='Flatness', color='y')
        ax[1].legend(loc='upper left', bbox_to_anchor=(1, 1))

        ax[0].semilogy(times, rms[0], label='RMS Energy')
        ax[0].legend(loc='upper left', bbox_to_anchor=(1, 1))

        plt.tight_layout()
        plt.savefig('%s_descriptors.png' % self.of, format='png')

        if not autoshow:
            plt.close()

        return MgImage(self.of + '_descriptors.png')

    def tempogram(self, window_size=4096, overlap=8, mel_filters=512, power=2, autoshow=False):
        """
        Renders four plots of:
            - onset strength, 
            - tempogram,  
            - Mean local & global autocorrelation vs lag (seconds),
            - Mean local & global autocorrelation vs BPM, and estimated tempo
        of the video/audio file.

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

        - `self.filename` + '_tempogram.png'

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

        oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_size)

        tempogram = librosa.feature.tempogram(
            onset_envelope=oenv, sr=sr, hop_length=hop_size)

        # Compute global onset autocorrelation
        ac_global = librosa.autocorrelate(oenv, max_size=tempogram.shape[0])
        ac_global = librosa.util.normalize(ac_global)

        # Estimate the global tempo for display purposes
        tempo = librosa.beat.tempo(
            onset_envelope=oenv, sr=sr, hop_length=hop_size)[0]

        fig, ax = plt.subplots(nrows=4, figsize=(12, 8), dpi=300)
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

        x = np.linspace(
            0, tempogram.shape[0] * float(hop_size) / sr, num=tempogram.shape[0])
        ax[2].plot(x, np.mean(tempogram, axis=1),
                   label='Mean local autocorrelation')
        ax[2].plot(x, ac_global, '--', alpha=0.75,
                   label='Global autocorrelation')
        ax[2].set(xlabel='Lag (seconds)')
        ax[2].legend(frameon=True)

        freqs = librosa.tempo_frequencies(
            tempogram.shape[0], hop_length=hop_size, sr=sr)
        ax[3].semilogx(freqs[1:], np.mean(tempogram[1:], axis=1),
                       label='Mean local autocorrelation', basex=2)
        ax[3].semilogx(freqs[1:], ac_global[1:], '--', alpha=0.75,
                       label='Global autocorrelation', basex=2)
        ax[3].axvline(tempo, color='black', linestyle='--',
                      alpha=.8, label='Estimated tempo={:g}'.format(tempo))
        ax[3].legend(frameon=True)
        ax[3].set(xlabel='BPM')
        ax[3].grid(True)

        plt.savefig('%s_tempogram.png' % self.of, format='png')

        if not autoshow:
            plt.close()

        return MgImage(self.of + '_tempogram.png')


def mg_audio_spectrogram(filename=None, window_size=4096, overlap=8, mel_filters=512, power=2, autoshow=False):
    """
    Renders a mel-scaled spectrogram of the video/audio file.

    Parameters
    ----------
    - filename : str, optional

        Path to the audio/video file to be processed.

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
        print("No filename was given.")
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


def mg_audio_descriptors(filename=None, window_size=4096, overlap=8, mel_filters=512, power=2, autoshow=False):
    """
    Renders a plot of spectral/loudness descriptors, including RMS energy, spectral flatness,
    centroid, bandwidth, rolloff of the video/audio file.

    Parameters
    ----------
    - filename : str, optional

        Path to the audio/video file to be processed.

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

    - `self.filename` + '_descriptors.png'

    Returns
    -------
    - MgPlot

        An MgPlot object referring to the output plot and its analysis data.
    """

    if filename == None:
        print("No filename was given.")
        return

    if not has_audio(filename):
        print('The video has no audio track.')
        return

    of, fex = os.path.splitext(filename)

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

    fig, ax = plt.subplots(figsize=(12, 8), dpi=300, nrows=3, sharex=True)

    img = librosa.display.specshow(librosa.power_to_db(
        S, ref=np.max, top_db=120), sr=sr, y_axis='mel', fmax=sr/2, x_axis='time', hop_length=hop_size, ax=ax[2])

    # get rid of "default" ticks
    ax[2].yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

    ax[0].set(title=os.path.basename(filename))
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
    ax[2].plot(times, cent.T, label='Centroid', color='w')
    ax[2].plot(times, rolloff[0], label='Roll-off frequency (0.99)')
    ax[2].plot(times, rolloff_min[0], color='r',
               label='Roll-off frequency (0.01)')

    ax[2].legend(loc='upper left', bbox_to_anchor=(1, 1))

    ax[1].plot(times, flatness.T, label='Flatness', color='y')
    ax[1].legend(loc='upper left', bbox_to_anchor=(1, 1))

    ax[0].semilogy(times, rms[0], label='RMS Energy')
    ax[0].legend(loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.savefig('%s_descriptors.png' % of, format='png')

    if not autoshow:
        plt.close()

    return MgImage(of + '_descriptors.png')


def mg_audio_tempogram(window_size=4096, overlap=8, mel_filters=512, power=2, autoshow=False):
    """
    Renders four plots of:
        - onset strength, 
        - tempogram,  
        - Mean local & global autocorrelation vs lag (seconds),
        - Mean local & global autocorrelation vs BPM, and estimated tempo
    of the video/audio file.

    Parameters
    ----------
    - filename : str, optional

        Path to the audio/video file to be processed.

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

    - `self.filename` + '_tempogram.png'

    Returns
    -------
    - MgPlot

        An MgPlot object referring to the output plot and its analysis data.
    """
    if filename == None:
        print("No filename was given.")
        return

    if not has_audio(filename):
        print('The video has no audio track.')
        return

    of, fex = os.path.splitext(filename)

    hop_size = int(window_size / overlap)

    y, sr = librosa.load(filename, sr=None)

    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_size)

    tempogram = librosa.feature.tempogram(
        onset_envelope=oenv, sr=sr, hop_length=hop_size)

    # Compute global onset autocorrelation
    ac_global = librosa.autocorrelate(oenv, max_size=tempogram.shape[0])
    ac_global = librosa.util.normalize(ac_global)

    # Estimate the global tempo for display purposes
    tempo = librosa.beat.tempo(
        onset_envelope=oenv, sr=sr, hop_length=hop_size)[0]

    fig, ax = plt.subplots(nrows=4, figsize=(12, 8), dpi=300)
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

    x = np.linspace(
        0, tempogram.shape[0] * float(hop_size) / sr, num=tempogram.shape[0])
    ax[2].plot(x, np.mean(tempogram, axis=1),
               label='Mean local autocorrelation')
    ax[2].plot(x, ac_global, '--', alpha=0.75,
               label='Global autocorrelation')
    ax[2].set(xlabel='Lag (seconds)')
    ax[2].legend(frameon=True)

    freqs = librosa.tempo_frequencies(
        tempogram.shape[0], hop_length=hop_size, sr=sr)
    ax[3].semilogx(freqs[1:], np.mean(tempogram[1:], axis=1),
                   label='Mean local autocorrelation', basex=2)
    ax[3].semilogx(freqs[1:], ac_global[1:], '--', alpha=0.75,
                   label='Global autocorrelation', basex=2)
    ax[3].axvline(tempo, color='black', linestyle='--',
                  alpha=.8, label='Estimated tempo={:g}'.format(tempo))
    ax[3].legend(frameon=True)
    ax[3].set(xlabel='BPM')
    ax[3].grid(True)

    plt.savefig('%s_tempogram.png' % of, format='png')

    if not autoshow:
        plt.close()

    return MgImage(of + '_tempogram.png')

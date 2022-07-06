import cv2
import os
import numpy as np
from numba import jit
from scipy.signal import medfilt2d
import matplotlib.pyplot as plt
import musicalgestures
from musicalgestures._directograms import directogram
from musicalgestures._utils import MgProgressbar, MgFigure, convert_to_avi, generate_outfilename
from musicalgestures._filter import filter_frame

def impact_envelope(directogram, kernel_size=5):

    # Apply a median filter to the directogram using a local window-size given by kernel_size
    filtered_directogram = medfilt2d(directogram, kernel_size)
    flux = np.zeros(directogram.shape)
    flux[1:, :] = (filtered_directogram - np.roll(filtered_directogram, 1, axis=0))[1:, :]
    flux[flux < 0] = 0.0

    impact_envelope = flux.sum(axis=1)
    # To account for large outlying spikes that sometimes happen at shot boundaries (i.e., cuts)
    # we clip the 99th percentile of values to the 98th percentile.
    clip_threshold = np.percentile(impact_envelope, 98)
    impact_envelope[impact_envelope > clip_threshold] = 0
    impact_envelope = impact_envelope / impact_envelope.max()

    return impact_envelope

@jit(nopython=True)
def impact_detection(envelopes, time, fps, local_mean=0.1, local_maxima=0.15):

    global_max = envelopes.max()

    mean_window_delta = int(local_mean / 2 * fps)
    max_window_delta = int(local_maxima / 2 * fps)

    impact = []

    for i in range(max_window_delta + 4, len(time) - max_window_delta - 4):
        local_mean_window = (envelopes[i - mean_window_delta:i].mean() + envelopes[i+1:i+1 + mean_window_delta].mean()) / 2
        local_max_window = max(envelopes[i - max_window_delta:i].max(), envelopes[i+1:i+1 + max_window_delta].max()) 

        current = envelopes[i]
        if current > local_max_window and (current - local_mean_window) > 0.1 * global_max:
            impact.append(i)

    return impact 


def mg_impacts(self, title=None, detection=True, local_mean=0.1, local_maxima=0.15, filtertype='Adaptative', thresh=0.05, kernel_size=5, target_name=None, overwrite=False):
    """
    Compute a visual analogue of an onset envelope, aslo known as an impact envelope (Abe Davis).
    This is computed by summing over positive entries in the columns of the directogram. This gives an impact envelope with precisely the same
    form as an onset envelope. To account for large outlying spikes that sometimes happen at shot boundaries (i.e., cuts), the 99th percentile
    of the impact envelope values are clipped to the 98th percentile. Then, the impact envelopes are normalized by their maximum to make calculations
    more consistent across video resolutions. Fianlly, the local mean of the impact envelopes are calculated using a 0.1-second window, and local maxima
    using a 0.15-second window. Impacts are defined as local maxima that are above their local mean by at least 10% of the envelope’s global maximum.

    Source: Abe Davis -- [Visual Rhythm and Beat](http://www.abedavis.com/files/papers/VisualRhythm_Davis18.pdf) (section 4.2 and 4.3)

    Args:
        title (str, optional): Optionally add title to the figure. Defaults to None, which uses 'Directogram' as a title. Defaults to None.
        detection (bool, optional): Whether to allow the detection of impacts based on local mean and local maxima or not.
        local_mean (float, optional): Size of the local mean window in seconds which reduces the amount of intensity variation between one impact and the next.
        local_maxima (float, optional): Size of the local maxima window in seconds for the impact envelopes
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. 'Adaptative' perform adaptative threshold as the weighted sum of 11 neighborhood pixels where weights are a Gaussian window. Defaults to 'Adaptative'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        kernel_size (int, optional): Size of structuring element. Defaults to 5.
        target_name (str, optional): Target output name for the directogram. Defaults to None (which assumes that the input filename with the suffix "_dg" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgFigure: An MgFigure object referring to the internal figure and its data.
    """

    of, fex = os.path.splitext(self.filename)

    if fex != '.avi':
        # first check if there already is a converted version, if not create one and register it to self
        if "as_avi" not in self.__dict__.keys():
            file_as_avi = convert_to_avi(of + fex, overwrite=overwrite)
            # register it as the avi version for the file
            self.as_avi = musicalgestures.MgVideo(file_as_avi)
        # point of and fex to the avi version
        of, fex = self.as_avi.of, self.as_avi.fex
        filename = of + fex
    else:
        filename = self.filename

    vidcap = cv2.VideoCapture(filename)
    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

    pb = MgProgressbar(total=length, prefix='Rendering impact envelopes:')

    directograms = []
    directogram_times = []
    ret, frame = vidcap.read()
    prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    i = 0

    while vidcap.isOpened():

        ret, frame = vidcap.read()

        if ret == True:
            next_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if filtertype == 'Adaptative':
                next_frame = cv2.adaptiveThreshold(
                    next_frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            else:
                # Frame Thresholding: apply threshold filter and median filter (of `kernel_size`x`kernel_size`) to the frame.
                next_frame = filter_frame(next_frame, filtertype, thresh, kernel_size)

            # Renders a dense optical flow video of the input video file using `cv2.calcOpticalFlowFarneback()`.
            # The description of the matching parameters are taken from the cv2 documentation.
            optical_flow = cv2.calcOpticalFlowFarneback(
                prev_frame, next_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            directograms.append(directogram(optical_flow))
            directogram_times.append(len(directograms) / fps) 
            prev_frame = next_frame

        else:
            pb.progress(length)
            break

        pb.progress(i)
        i += 1

    vidcap.release()

    # Compute impact envelopes and impact detection
    impact_envelopes = impact_envelope(np.array(directograms))
    impacts = np.array(impact_detection(impact_envelopes, np.array(directogram_times), fps, local_mean=local_mean, local_maxima=local_maxima)) / fps # convert to seconds

    fig, ax = plt.subplots(figsize=(12, 4), dpi=300)

    # make sure background is white
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)

    # add title
    if title == None:
        title = os.path.basename(
            f'Impact Envelopes (filter type: {filtertype})')

    fig.suptitle(title, fontsize=16)

    ax.plot(directogram_times, impact_envelopes)
    ax.set_xlabel('Time [Seconds]')
    ax.set_yticks([])
    ax.margins(x=0)

    if detection:
        ax.vlines(impacts, 0, max(impact_envelopes), colors='red', linestyles='dashed',
                  label=f'Impact Detection\nLocal mean: {local_mean}\nLocal maxima: {local_maxima}')
        ax.legend(loc='upper right')

    fig.tight_layout()

    if target_name == None:
        target_name = of + '_impact.png'

    else:
        # enforce png
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    plt.savefig(target_name, format='png', transparent=False)
    plt.close()

    # create MgFigure
    data = {
        "FPS": fps,
        "path": self.of,
        "impact times": directogram_times,
        "impact envelopes": impact_envelopes,
    }

    mgf = MgFigure(
        figure=fig,
        figure_type='video.impacts',
        data=data,
        layers=None,
        image=target_name)

    return mgf

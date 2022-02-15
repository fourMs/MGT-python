import cv2
import os
import numpy as np
from numba import jit
import matplotlib.pyplot as plt
from matplotlib import colors

import musicalgestures
from musicalgestures._filter import filter_frame
from musicalgestures._utils import MgProgressbar, MgFigure, convert_to_avi, generate_outfilename

HISTOGRAM_BINS = np.linspace(-np.pi, np.pi, 100)

@jit(nopython=True)
def matrix3D_norm(matrix):
    n, m, o = matrix.shape
    norm = np.zeros((n,m))

    for i in np.arange(n):
        for j in np.arange(m):
            norm[i][j] = np.sqrt(np.sum(np.abs(matrix[i][j]) ** 2)) # Frobenius norm
    return norm

@jit(nopython=True)
def directogram(optical_flow):
    norms = matrix3D_norm(optical_flow)  # norm of the matrix
    # Compute angles for the optical flow of the input frame
    angles = np.arctan2(optical_flow[:, :, 1], optical_flow[:, :, 0])
    # Return the indices of the histogram bins to which each value in the angles array belongs
    angle_indicators = np.digitize(angles, HISTOGRAM_BINS[:-1])
    directogram = np.zeros((len(HISTOGRAM_BINS),))
    # Motion for each angle indicators is created by binning and summing optical flow vectors for every pixel
    for y in range(optical_flow.shape[0]):
        for x in range(optical_flow.shape[1]):
            directogram[angle_indicators[y, x]] += norms[y, x]

    return directogram

def mg_directograms(self, title=None, filtertype='Adaptative', thresh=0.05, kernel_size=5, target_name=None, overwrite=False):
    """
    Compute a directogram to factor the magnitude of motion into different angles.
    Each columun of the directogram is computed as the weighted histogram (HISTOGRAM_BINS) of angles for the optical flow of an input frame.

    Source: Abe Davis -- [Visual Rhythm and Beat](http://www.abedavis.com/files/papers/VisualRhythm_Davis18.pdf) (section 4.1)
    

    Args:
        title (str, optional): Optionally add title to the figure. Defaults to None, which uses 'Directogram' as a title. Defaults to None.
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
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

    pb = MgProgressbar(total=length, prefix='Rendering directogram:')

    directograms = []
    directogram_times = np.zeros((length-1,))
    ret, frame = vidcap.read()
    prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    i = 0

    while vidcap.isOpened():

        ret, frame = vidcap.read()

        if ret == True:
            next_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if filtertype == 'Adaptative':
                next_frame = cv2.adaptiveThreshold(next_frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            else:
                # Frame Thresholding: apply threshold filter and median filter (of `kernel_size`x`kernel_size`) to the frame.
                next_frame = filter_frame(next_frame, filtertype, thresh, kernel_size)

            # Renders a dense optical flow video of the input video file using `cv2.calcOpticalFlowFarneback()`.
            # The description of the matching parameters are taken from the cv2 documentation.
            optical_flow = cv2.calcOpticalFlowFarneback(prev_frame, next_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            directograms.append(directogram(optical_flow))
            directogram_times[i] = len(directograms) / fps
            prev_frame = next_frame

        else:
            pb.progress(length)
            break

        pb.progress(i)
        i += 1

    vidcap.release()

    # Create and save the figure
    fig, ax = plt.subplots(figsize=(12, 4), dpi=300)
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)

    # add title
    if title == None:
        title = os.path.basename(f'Directogram (filter type: {filtertype})')

    fig.suptitle(title, fontsize=16)
    
    ax.imshow(np.array(directograms).T, extent=[directogram_times.min(), directogram_times.max(), 
    HISTOGRAM_BINS.min(), HISTOGRAM_BINS.max()], norm=colors.PowerNorm(gamma=1.0/2.0), aspect='auto')
    
    ax.set_ylabel('Angle [Radians]')
    ax.set_xlabel('Time [Seconds]')

    if target_name == None:
        target_name = of + '_dg.png'

    else:
        # enforce png
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    plt.savefig(target_name, format='png', transparent=False)
    plt.close()

    # Create MgFigure
    data = {
        "FPS": fps,
        "path": self.of,
        "directogram times": directogram_times,
        "directogram": np.array(directograms),
    }

    mgf = MgFigure(
        figure=fig,
        figure_type='video.directogram',
        data=data,
        layers=None,
        image=target_name)

    return mgf

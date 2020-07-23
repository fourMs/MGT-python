import cv2
import os
import numpy as np
from musicalgestures._utils import MgProgressbar


def mg_videograms(self):
    """
    Averages videoframes by axes, and creates two images of the horizontal-axis and vertical-axis stacks.
    In these stacks, a single row or column corresponds to a frame from the source video, and the index
    of the row or column corresponds to the index of the source frame.

    Outputs
    -------
    - `filename`_vgx.png

        A horizontal videogram of the source video.
    - `filename`_vgy.png

        A vertical videogram of the source video.

    Returns
    -------
    - Tuple(str, str)

        A tuple with the string paths to the horizontal and vertical videograms respectively. 
    """

    vidcap = cv2.VideoCapture(self.of+self.fex)
    ret, frame = vidcap.read()

    vgramy = np.zeros([1, self.width, 3])
    vgramx = np.zeros([self.height, 1, 3])

    ii = 0

    pb = MgProgressbar(total=self.length, prefix="Rendering videograms:")

    if self.color == False:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        vgramy = np.zeros([1, self.width])
        vgramx = np.zeros([self.height, 1])

    while(vidcap.isOpened()):
        prev_frame = frame

        ret, frame = vidcap.read()
        if ret == True:

            if self.color == False:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame = np.array(frame)
            frame = frame.astype(np.int32)

            if self.color == True:
                mean_x = np.mean(frame, axis=1).reshape(self.height, 1, 3)
                mean_y = np.mean(frame, axis=0).reshape(1, self.width, 3)
            else:
                mean_x = np.mean(frame, axis=1).reshape(self.height, 1)
                mean_y = np.mean(frame, axis=0).reshape(1, self.width)

            # normalization is independent for each color channel
            for channel in range(mean_x.shape[2]):
                mean_x[:, :, channel] = (mean_x[:, :, channel]-mean_x[:, :, channel].min())/(
                    mean_x[:, :, channel].max()-mean_x[:, :, channel].min())*255.0
                mean_y[:, :, channel] = (mean_y[:, :, channel]-mean_y[:, :, channel].min())/(
                    mean_y[:, :, channel].max()-mean_y[:, :, channel].min())*255.0

            # normalization is calculated considering all values in all channels (color channels are not independent)
            # mean_x = (mean_x-mean_x.min())/(mean_x.max()-mean_x.min())*255.0
            # mean_y = (mean_y-mean_y.min())/(mean_y.max()-mean_y.min())*255.0

            vgramx = np.append(vgramx, mean_x, axis=1)
            vgramy = np.append(vgramy, mean_y, axis=0)

        else:
            pb.progress(self.length)
            break

        pb.progress(ii)
        ii += 1

    if self.color == False:
        # Normalize before converting to uint8 to keep precision
        vgramy = vgramy/vgramy.max()*255
        vgramx = vgramx/vgramx.max()*255
        vgramy = cv2.cvtColor(vgramy.astype(
            np.uint8), cv2.COLOR_GRAY2BGR)
        vgramx = cv2.cvtColor(vgramx.astype(
            np.uint8), cv2.COLOR_GRAY2BGR)

    # vgramy = (vgramy-vgramy.min())/(vgramy.max()-vgramy.min())*255.0
    # vgramx = (vgramx-vgramx.min())/(vgramx.max()-vgramx.min())*255.0
    # vgramy = vgramy.astype(np.uint8)
    # vgramx = vgramx.astype(np.uint8)
    # vgramy = cv2.normalize(vgramy, vgramy, 0, 255, norm_type=cv2.NORM_MINMAX)
    # vgramx = cv2.normalize(vgramx, vgramx, 0, 255, norm_type=cv2.NORM_MINMAX)

    # cv2.normalize(clipped, clipped, 0, 255, norm_type=cv2.NORM_MINMAX)

    cv2.imwrite(self.of+'_vgx.png', vgramx.astype(np.uint8))
    # cv2.imwrite(self.of+'_vgx_dev2.png', vgramy)
    cv2.imwrite(self.of+'_vgy.png', vgramy.astype(np.uint8))
    # cv2.imwrite(self.of+'_vgy_dev2.png', vgramx)

    vidcap.release()

    return (self.of+'_vgx.png', self.of+'_vgy.png')

import cv2
import numpy as np
import os
from ._utils import mg_progressbar, MgImage


def mg_average_image(self, filename='', normalize=True):
    """
    Post-processing tool. Finds and saves an average image of entire video.

        THIS DOC STRING IS COMPLETELY WRONG. WILL FIX IT LATER.

    Parameters
    ----------
    - enhance (float): Takes values between '0' and '1'. Where '0' is no enhancement and '1' scales the pixel 
            values such that the brightest pixel gets the value 255. 

    Usage
    -----
    from _motionaverage import motionaverage
    motionaverage('filename.avi', enhance = 0.5)
    """

    if filename == '':
        filename = self.filename

    of = os.path.splitext(filename)[0]
    video = cv2.VideoCapture(filename)
    ret, frame = video.read()
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    if self.color == False:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    average = frame.astype(np.float)/length
    ii = 0
    while(video.isOpened()):
        ret, frame = video.read()
        if ret == True:
            if self.color == False:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = np.array(frame)
            frame = frame.astype(np.float)
            average += frame/length
        else:
            mg_progressbar(
                length, length, 'Rendering average image:', 'Complete')
            break
        ii += 1
        mg_progressbar(ii, length, 'Rendering average image:', 'Complete')

    if self.color == False:
        average = cv2.cvtColor(average.astype(np.uint8), cv2.COLOR_GRAY2BGR)

    if normalize:
        average = average/np.max(average)*255
        average = average.astype(np.uint8)
        average_hsv = cv2.cvtColor(average, cv2.COLOR_BGR2HSV)
        average_hsv[:, :, 2] = cv2.equalizeHist(average_hsv[:, :, 2])
        average = cv2.cvtColor(average_hsv, cv2.COLOR_HSV2BGR)

    cv2.imwrite(of+'_average.png', average.astype(np.uint8))

    return MgImage(of+'_average.png')

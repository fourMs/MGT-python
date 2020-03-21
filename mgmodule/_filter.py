from scipy.signal import medfilt2d
import cv2
import numpy as np


def filter_frame(motion_frame, filtertype, thresh, kernel_size):
    """
    Applies a filter to an image or videoframe.

    Parameters
    ----------
    - motion_frame : np.array(uint8) 

        Input motion image.
    - filtertype : {'Regular', 'Binary', 'Blob'}

        `Regular` turns all values below `thresh` to 0.
        `Binary` turns all values below `thresh` to 0, above `thresh` to 1.
        `Blob` removes individual pixels with erosion method.
    - thresh : float

        A number in the range of 0 to 1.
        Eliminates pixel values less than given threshold.
    - kernel_size : int

        Size of structuring element.

    Returns
    -------
    - np.array(uint8)

        Filtered frame.
    """
    if filtertype.lower() == 'regular':
        motion_frame = (motion_frame > thresh*255)*motion_frame
        motion_frame = medfilt2d(motion_frame, kernel_size)
    elif filtertype.lower() == 'binary':
        motion_frame = (motion_frame > thresh*255)*255
        motion_frame = medfilt2d(motion_frame.astype(np.uint8), kernel_size)
    elif filtertype.lower() == 'blob':
        motion_frame = cv2.erode(motion_frame, np.ones(
            [kernel_size, kernel_size]), iterations=1)
    return motion_frame

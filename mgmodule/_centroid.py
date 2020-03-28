import cv2
import numpy as np


def centroid(image, width, height):
    """
    Computes the centroid of an image or frame.

    Parameters
    ----------
    - image : np.array(uint8)

        The input image matrix for the centroid estimation function. 
    - width : int

        The pixel width of the input video capture. 
    - height : int

        The pixel height of the input video capture. 

    Returns
    -------
    - np.array(2)

        X and Y coordinates of the centroid of motion.
    - int

        Quantity of motion: How large the change was in pixels.
    """

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    x = np.arange(width)
    y = np.arange(height)
    qom = cv2.sumElems(image)[0]
    mx = np.mean(image, axis=0)
    my = np.mean(image, axis=1)

    if np.sum(mx) != 0 and np.sum(my) != 0:
        comx = x.reshape(1, width)@mx.reshape(width, 1)/np.sum(mx)
        comy = y.reshape(1, height)@my.reshape(height, 1)/np.sum(my)
    else:
        comx = 0
        comy = 0

    com = np.zeros(2)
    com[0] = comx
    # The y-axis is flipped to fit a "normal" coordinate system
    com[1] = height-comy

    return com, int(qom)

import cv2
import numpy as np


def centroid(image, width, height):
    """
    Computes the centroid and quantity of motion in an image or frame.

    Args:
        image (np.array(uint8)): The input image matrix for the centroid estimation function.
        width (int): The pixel width of the input video capture.
        height (int): The pixel height of the input video capture.

    Returns:
        np.array(2): X and Y coordinates of the centroid of motion.
        int: Quantity of motion: How large the change was in pixels.
    """

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    x = np.arange(width)
    y = np.arange(height)
    # Calculates the sum of the pixels in the input image
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

def area(motion_frame, height, width):
    # Area of Motion (AoM)
    aombite = []
    # Convert to gray scale
    gray = cv2.cvtColor(motion_frame, cv2.COLOR_BGR2GRAY)
    # Apply adaptative threshold on the video frame to make differences more visible for contour detection
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 51, 2)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  
    # Get the largest contour to average the area of motion
    if len(contours) != 0:
        largest = contours[0]
        for contour in contours:
            if cv2.contourArea(contour) > cv2.contourArea(largest):
                largest = contour  
        (x, y, w, h) = cv2.boundingRect(largest) 
        # Append and normalize coordinates of the area of motion
        aombite.append([x/width, y/height, (x+w)/width,(y+h)/height])
    else:
        aombite.append([0,0,0,0])

    return aombite
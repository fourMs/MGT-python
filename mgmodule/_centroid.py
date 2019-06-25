import cv2
import numpy as np
def mg_centroid(image, width, height):
    """
    Computes the centroid of an image/frame.
    
    Parameters
    - image (uint8)
    - width/height of image
    
    Returns:
    - Centroid of motion: Where was the maximum change in pixel value
    - Quantity of motion: How large was the change in pixel value
    """

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    x = np.arange(width)
    y = np.arange(height)
    qom = cv2.sumElems(image)[0]
    mx = np.mean(image,axis=0)
    my = np.mean(image,axis=1)

    if np.sum(mx) != 0 and np.sum(my) != 0:
        comx = x.reshape(1,width)@mx.reshape(width,1)/np.sum(mx)
        comy = y.reshape(1,height)@my.reshape(height,1)/np.sum(my)
    else:
        comx = 0
        comy = 0
  
    com = np.zeros(2)
    com[0]=comx
    com[1]=height-comy # The y-axis is flipped to fit a "normal" coordinate system

    return com, qom

from scipy.signal import medfilt2d
import cv2
import numpy as np

def motionfilter(motion_frame, filtertype,thresh,kernel_size):
    """
        Apply a filter to a picture/videoframe
        
        motion_frame (array(uint8)): input motion image
        filtertype (str):
                    ’Regular’, turns all values below thresh to 0,
                    ’Binary’ truns all values below thres to 0, above thres to 1,
                    ’Blob’ removes individual pixels with erosion method.
        thresh (float): for ’Regular’ and ’Binary’ option, thresh is a value of threshold [0,1];
        kernel_size(int): Size of structuring element
        
        return: filtered frame (array(uint8))
    """
    if filtertype == 'Regular':
        motion_frame = (motion_frame>thresh*255)*motion_frame
        motion_frame = medfilt2d(motion_frame, kernel_size)
    elif filtertype == 'Binary':
        motion_frame = (motion_frame>thresh*255)*255
        motion_frame = medfilt2d(motion_frame.astype(np.uint8), kernel_size)
    elif filtertype == 'Blob':
        motion_frame = cv2.erode(motion_frame,np.ones([kernel_size,kernel_size]),iterations=1)
    return motion_frame

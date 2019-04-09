from scipy.signal import medfilt2d
import cv2
import numpy as np

def motionfilter(motion_frame, filtertype,thresh,kernel_size):    
    if filtertype == 'Regular':
        motion_frame = (motion_frame>thresh*255)*motion_frame
        motion_frame = medfilt2d(motion_frame, kernel_size)
    elif filtertype == 'Binary':
        motion_frame = (motion_frame>thresh*255)*255
        motion_frame = medfilt2d(motion_frame, kernel_size)
    elif filtertype == 'Blob':
        motion_frame = cv2.erode(motion_frame,np.ones([kernel_size,kernel_size]),iterations=1)
    return motion_frame
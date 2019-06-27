import sys
import os
sys.path.append('../mgmodule')
sys.path.append('..')
import mgmodule
import cv2

#import any non-module functions you want to use (see documentation) this way:
from _average import average_image

#CREATE MODULE OBJECT: Here is an example call to create an mg Object, using loads of parameters
mg = mgmodule.MgObject('pianist.avi', color=False, crop='auto')
#USE MODULE METHOD: To run the motionvideo analysis, run the function using your object
mg.mg_motionvideo(thresh=0.1)
#USE NON-MODULE FUNCTION, this one can find an average image of any video, here using the mb objects filename
average_image(mg.filename)
mg.mg_motionhistory()

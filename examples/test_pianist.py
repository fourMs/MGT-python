import sys
import os
sys.path.append('../mgmodule')
sys.path.append('..')
import mgmodule
import cv2

#import any non-module functions you want to use (see documentation) this way:
from _average import average_image
from _history import history

#CREATE MODULE OBJECT: Here is an example call to create an mg Object, using loads of parameters
mg = mgmodule.MgObject('pianist.avi', color=False, crop='auto', skip = 2)
#USE MODULE METHOD: To run the motionvideo analysis, run the function using your object
mg.mg_motionvideo(inverted_motionvideo = True, inverted_motiongram = True, thresh=0.1)
#This runs the motion history on the motion video
mg.mg_motionhistory()

#USE NON-MODULE FUNCTION, this one can find an average image of any video, here using the mb objects filename
average_image(mg.of+'_motion'+'.avi', enhance = 1)
average_image(mg.filename)

history(mg.of+'.avi',history_length=25)

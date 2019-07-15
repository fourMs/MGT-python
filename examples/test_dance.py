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
mg = mgmodule.MgObject('dance.avi', starttime = 2, endtime = 10, color = False, contrast = 0, brightness = 0)
#USE MODULE METHOD: To run the motionvideo analysis, run the function using your object
mg.mg_motionvideo(inverted_motionvideo = False, inverted_motiongram = True, thresh=0.1, unit='seconds')
#This runs the motion history on the motion video
mg.mg_motionhistory(history_length=25, thresh=0.01, inverted_motionhistory = False, blur='Average')

#USE NON-MODULE FUNCTION, this one can find an average image of any video, here using the mb objects filename
average_image(mg.of+'_motion'+'.avi', enhance = 1)

history(mg.of+'.avi',history_length=25)

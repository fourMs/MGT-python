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
mg = mgmodule.MgObject('pianist.avi', color=False, crop='auto', skip = 3)
#USE MODULE METHOD: To run the motionvideo analysis, run the function using your object
mg.mg_motionvideo(inverted_motionvideo = True, inverted_motiongram = True, thresh=0.1, blur='Average', normalize=False)
#This runs the motion history on the motion video
mg.mg_motionhistory(history_length=25, thresh=0.1, inverted_motionhistory = True, blur='Average')

#USE NON-MODULE FUNCTION, this one can find an average image of any video, here using the mb objects filename

# Average image of original video
#average_image(mg.filename)

# Average image of pre-processed video
average_image(mg.of+'.avi')

# Average image of motion video
average_image(mg.of+'_motion.avi')

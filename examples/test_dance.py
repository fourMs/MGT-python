import sys
import os
sys.path.append('../mgmodule')
sys.path.append('..')
import mgmodule
import cv2

# CREATE MODULE OBJECT: Here is an example call to create an mg Object, using loads of parameters
mg = mgmodule.MgObject('dance.avi', starttime=2,
                       endtime=20, contrast=100, brightness=50)

# USE MODULE METHOD: To run the motionvideo analysis, run the function using your object
mg.motion(inverted_motionvideo=False, inverted_motiongram=False,
          thresh=0.05, unit='seconds')

# History video
mg.history(history_length=25)
# Motion history video
mg.history(mg.of+'_motion.avi', history_length=25)

# Average image of original video
# mg.average('dance.avi')

# Average image of pre-processed video
mg.average()

# Average image of motion video
mg.average(mg.of+'_motion.avi')

import sys
sys.path.append('../..')

import mgmodule
import cv2

mg = mgmodule.MgObject('dance.avi', starttime = 5, endtime = 10, color = True, brightness = 90, contrast = 90, skip = 5)
#mg.cropvideo()
#mgc = mgmodule.MgObject('dance_cropped.avi')
mg.motionvideo()


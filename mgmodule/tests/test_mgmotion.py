import sys
sys.path.append('../..')

import mgmodule
import cv2


mg = mgmodule.MgObject('dance.avi', starttime = 5, endtime = 10, color = True, brightness = 90, contrast = 90, skip = 1)
mg.cropvideo(crop_movement = 'auto',motion_box_thresh = 0.2, motion_box_margin = 5)
#mgc = mgmodule.MgObject('dance_cropped.avi')





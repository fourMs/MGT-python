import sys
import os
sys.path.append('../..')
sys.path.append('..')

import mgmodule
import cv2
from _history import history
from _constrainNumber import constrainNumber




mg = mgmodule.MgObject('dance.avi', starttime = 5, endtime = 10, color = True, brightness = 90, contrast = 90, skip = 1)
print(constrainNumber(3,4,7))
#mgc = mgmodule.MgObject('dance_cropped.avi')


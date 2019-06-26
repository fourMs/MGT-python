import sys
import os
sys.path.append('../..')
sys.path.append('..')

import mgmodule
import cv2
from _history import history
from _constrainNumber import constrainNumber
from _average import average_image




mg = mgmodule.MgObject('dance.avi', starttime = 2, endtime = 7, color = True, brightness = 90, contrast = 90, skip = 0, crop='auto')

average_image(mg.filename)

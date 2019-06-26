import sys
import os
sys.path.append('../..')
import mgmodule
#from ._history import history
import cv2


mg = mgmodule.MgObject('dance.avi', starttime = 5, endtime = 10, color = True, brightness = 90, contrast = 90, skip = 1)
print(mg.constrainNumber(3,4,7))
#mgc = mgmodule.MgObject('dance_cropped.avi')





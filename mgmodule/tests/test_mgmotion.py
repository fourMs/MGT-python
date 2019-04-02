import sys
sys.path.append('../..')

import mgmodule
import cv2

mg = mgmodule.MgObject('pianist.avi',filtertype = 'Regular', color = True,endtime = 3,thresh=0.3)
print(mg.height,mg.width)
img=cv2.imread('circle.png')
img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

mg.find_motion_box(img,margin = 10)

cv2.imshow('',mg.motion_box)
cv2.waitKey(0)


print(constrainNumber(11,0,10))


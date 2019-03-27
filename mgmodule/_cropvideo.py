import cv2
import os
import numpy as np
from ._videoreader import mg_videoreader

img = np.zeros((512,512,3), np.uint8)
x_start,y_start = -1,-1
x_stop,y_stop = -1,-1
def cropvideo(self):
	vid2crop = mg_videoreader(self.filename,self.starttime,self.endtime,self.skip)[0]
	ret, frame = vid2crop.read()
	cv2.namedWindow('image')
	cv2.setMouseCallback('image',draw_rectangle,param=frame)

	while(1):
		cv2.imshow('image',frame)
		k = cv2.waitKey(1) & 0xFF
		if k == 27:
			break
	cv2.destroyAllWindows()

	of = os.path.splitext(self.filename)[0] 
	fourcc = cv2.VideoWriter_fourcc(*'MJPG')
	out = cv2.VideoWriter(of + '_cropped.avi',fourcc, self.fps, (self.width,self.height))
	ii = 0 

	while (vid2crop.isOpened()):
		if ret:
			ret, frame = vid2crop.read()
			out.write(frame)
		else:
			break
		ii+=1
		print('Processing %s%%' %(int(ii/(self.length-1)*100)), end='\r')


def draw_rectangle(event,x,y,flags,param):
	global x_start,y_start,x_stop,y_stop,drawing, img

	if event == cv2.EVENT_LBUTTONDOWN:
		drawing = True
		x_start,y_start = x,y

	elif event == cv2.EVENT_MOUSEMOVE:
		if drawing == True:
			cv2.rectangle(param,(x_start,y_start),(x,y),(220,220,220),1)


	elif event == cv2.EVENT_LBUTTONUP:
		drawing = False
		x_stop,y_stop = x,y
		cv2.rectangle(param,(x_start,y_start),(x,y),(220,220,220),1)

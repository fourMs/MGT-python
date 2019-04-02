import cv2
import os
import numpy as np
from ._videoreader import mg_videoreader
from ._constrainNumber import constrainNumber

def cropvideo(self):
	global frame_mask,drawing,g_val,x_start,x_stop,y_start,y_stop

	x_start,y_start = -1,-1
	x_stop,y_stop = -1,-1

	drawing = False

	vid2crop = mg_videoreader(self.filename,self.starttime,self.endtime,self.skip)[0]
	ret, frame = vid2crop.read()
	frame_mask = np.zeros(frame.shape)
	name_str = 'Draw rectangle and press "C" to crop'
	cv2.namedWindow(name_str)
	cv2.setMouseCallback(name_str,draw_rectangle,param = frame)
	g_val = 220
	while(1):
		cv2.imshow(name_str,frame*(frame_mask!=g_val)+frame_mask.astype(np.uint8))
		k = cv2.waitKey(1) & 0xFF
		if k == ord('c') or k == ord('C'):
			break
	cv2.destroyAllWindows()


	print(x_start,x_stop,y_start,y_stop)
	if x_stop<x_start:
		temp=x_start
		x_start=x_stop
		x_stop = temp
	if y_stop<y_start:
		temp=y_start
		y_start=y_stop
		y_stop = temp

	of = os.path.splitext(self.filename)[0] 
	fourcc = cv2.VideoWriter_fourcc(*'MJPG')
	out = cv2.VideoWriter(of + '_cropped.avi',fourcc, self.fps, (int(x_stop-x_start),(int(y_stop-y_start))))
	print(self.width)
	ii = 0 
	while (vid2crop.isOpened()):
		if ret:
			frame_temp = frame[y_start:y_stop,x_start:x_stop,:]
			out.write(frame_temp)
			ret, frame = vid2crop.read()
		else:
			break
		ii+=1
		print('Processing %s%%' %(int(ii/(self.length-1)*100)), end='\r')
	vid2crop.release()
	out.release()
	cv2.destroyAllWindows()

def draw_rectangle(event,x,y,flags,param):
	global x_start,y_start,x_stop,y_stop,drawing,frame_mask
	if event == cv2.EVENT_LBUTTONDOWN:
		frame_mask = np.zeros(param.shape)
		drawing = True
		x_start,y_start = x,y

	elif event == cv2.EVENT_MOUSEMOVE:
		if drawing == True:
			frame_mask = np.zeros(param.shape)
			cv2.rectangle(frame_mask,(x_start,y_start),(x,y),(g_val,g_val,g_val),1)


	elif event == cv2.EVENT_LBUTTONUP:
		drawing = False
		x_stop,y_stop = x,y
		cv2.rectangle(frame_mask,(x_start,y_start),(x,y),(g_val,g_val,g_val),1)


def find_motion_box(self,grayimage,margin=0):
	prev_Start = self.width
	prev_Stop = 0 

	the_box = np.zeros([self.height,self.width])
	#----Finding left and right edges
	for i in range(self.height):
		row=grayimage[i,:]
		inds = np.where(row>0)[0]
		if len(inds)>0:
			Start = inds[0]
			if Start<prev_Start:
				le = Start
				prev_Start = Start
			if len(inds)>1:
				Stop = inds[-1]
				if Stop>prev_Stop:
					re = Stop
					prev_Stop = Stop

	# ---- Finding top and bottom edges
	prev_Start = self.height
	prev_Stop = 0 
	for j in range(self.width):
		col=grayimage[:,j]
		inds = np.where(col>0)[0]
		if len(inds)>0:
			Start = inds[0]
			if Start<prev_Start:
				te = Start
				prev_Start = Start
			if len(inds)>1:
				Stop = inds[-1]
				if Stop>prev_Stop:
					be = Stop
					prev_Stop = Stop

	the_box[constrainNumber(te-margin,0,self.height-1),constrainNumber(le-margin,0,self.width-1):constrainNumber(re+margin,0,self.width-1)]=1
	the_box[constrainNumber(te-margin,0,self.height-1):constrainNumber(be+margin,0,self.height-1),constrainNumber(le-margin,0,self.width-1)]=1
	the_box[constrainNumber(be+margin,0,self.height-1),constrainNumber(le-margin,0,self.width-1):constrainNumber(re+margin,0,self.width-1)]=1
	the_box[constrainNumber(te-margin,0,self.height-1):constrainNumber(be+margin,0,self.height-1),constrainNumber(re+margin,0,self.width-1)]=1
	self.motion_box = the_box








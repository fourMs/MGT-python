import cv2
import os
import numpy as np
import time
from ._videoreader import mg_videoreader
from ._constrainNumber import constrainNumber
from ._filter import motionfilter

def cropvideo(self, crop_movement = 'auto', motion_box_thresh = 0.1,motion_box_margin = 1):
	global frame_mask,drawing,g_val,x_start,x_stop,y_start,y_stop
	x_start,y_start = -1,-1
	x_stop,y_stop = -1,-1

	self.motion_box_thresh = motion_box_thresh
	self.motion_box_margin = motion_box_margin
	drawing = False

	[vid2crop, self.length, self.width, self.height, self.fps, self.endtime] = mg_videoreader(self.filename,self.starttime,self.endtime,self.skip)
	ret, frame = vid2crop.read()

	if crop_movement == 'manual':
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
	elif crop_movement == 'auto':
		[x_start,x_stop,y_start,y_stop] = self.find_total_motion_box()

	of = os.path.splitext(self.filename)[0] 
	fourcc = cv2.VideoWriter_fourcc(*'MJPG')
	out = cv2.VideoWriter(of + '_cropped.avi',fourcc, self.fps, (int(x_stop-x_start),(int(y_stop-y_start))))
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

	# Change self.of to the cropped version. self.height and self.width are also changed
	self.of = self.of + '_cropped'
	self.filename = self.of+'.avi'
	self.video, self.length, self.width, self.height, self.fps, self.endtime = mg_videoreader(self.filename, self.starttime, self.endtime, self.skip)




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


def find_motion_box(self,grayimage):
	prev_Start = self.width
	prev_Stop = 0 

	the_box = np.zeros([self.height,self.width])
	#----Finding left and right edges
	le = int(self.width/2)
	re = int(self.width/2)
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
	te = int(self.height/2)
	be = int(self.height/2)
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

	margin = self.motion_box_margin

	x_start = constrainNumber(le-margin,0,self.width-1)
	x_stop = constrainNumber(re+margin,0,self.width-1)
	y_start = constrainNumber(te-margin,0,self.height-1)
	y_stop = constrainNumber(be+margin,0,self.height-1)

	the_box[constrainNumber(te-margin,0,self.height-1),constrainNumber(le-margin,0,self.width-1):constrainNumber(re+margin,0,self.width-1)]=1
	the_box[constrainNumber(te-margin,0,self.height-1):constrainNumber(be+margin,0,self.height-1),constrainNumber(le-margin,0,self.width-1)]=1
	the_box[constrainNumber(be+margin,0,self.height-1),constrainNumber(le-margin,0,self.width-1):constrainNumber(re+margin,0,self.width-1)]=1
	the_box[constrainNumber(te-margin,0,self.height-1):constrainNumber(be+margin,0,self.height-1),constrainNumber(re+margin,0,self.width-1)]=1
	self.motion_box = the_box
	return the_box,x_start,x_stop,y_start,y_stop

def find_total_motion_box(self):
	self.get_video()
	ret, frame = self.video.read()
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	total_box = np.zeros([self.height,self.width])
	while(self.video.isOpened()):
		prev_frame = frame.astype(np.int32)
		ret, frame = self.video.read()
		if ret==True:
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			frame = frame.astype(np.int32)

			motion_frame = (np.abs(frame-prev_frame)).astype(np.uint8)
			motion_frame = motionfilter(motion_frame,'Regular',thresh = self.motion_box_thresh,kernel_size = 3)

			self.find_motion_box(motion_frame)
			total_box = total_box*(self.motion_box==0)+self.motion_box
		else:
			[self.total_motion_box,x_start,x_stop,y_start,y_stop] = self.find_motion_box(total_box)
			break
	return x_start,x_stop,y_start,y_stop








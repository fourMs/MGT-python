import cv2
import os
import numpy as np
import time
from ._constrainNumber import constrainNumber
from ._filter import filter_frame


def mg_cropvideo(fps,width,height, length, of, fex, crop_movement = 'Auto', motion_box_thresh = 0.1, motion_box_margin = 1):

	"""
	Crops the video.

	Parameters:
		- crop_movement: {'Auto','Manual'}
			'Auto' finds the bounding box that contains the total motion in the video.
			Motion threshold is given by motion_box_thresh.
			'Manual' opens up a simple GUI that is used to crop the video manually 
			by looking at the first frame

		- motion_box_thresh: float
			Only meaningful is crop_movement = 'Auto'. Takes floats between 0 and 1, 
			where 0 includes all the motion and 1 includes none
		
		- motion_box_margin: int
			Only meaningful is crop_movement = 'Auto'. Add margin to the bounding box.
	Returns:
		- None
	"""

	global frame_mask,drawing,g_val,x_start,x_stop,y_start,y_stop 
	x_start,y_start = -1,-1
	x_stop,y_stop = -1,-1

	drawing = False


	vid2crop = cv2.VideoCapture(of + fex)
	vid2findbox = cv2.VideoCapture(of + fex)

	ret, frame = vid2crop.read()

	if crop_movement == 'Manual':
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

	
		if x_stop<x_start:
			temp=x_start
			x_start=x_stop
			x_stop = temp
		if y_stop<y_start:
			temp=y_start
			y_start=y_stop
			y_stop = temp
	elif crop_movement == 'Auto' or 'auto':
		[x_start,x_stop,y_start,y_stop] = find_total_motion_box(vid2findbox,width,height,length,motion_box_thresh,motion_box_margin)
	fourcc = cv2.VideoWriter_fourcc(*'MJPG')
	out = cv2.VideoWriter(of + '_crop' + fex,fourcc, fps, (int(x_stop-x_start),(int(y_stop-y_start))))
	ii = 0 
	while (vid2crop.isOpened()):
		if ret:
			frame_temp = frame[y_start:y_stop,x_start:x_stop,:]
			out.write(frame_temp)
			ret, frame = vid2crop.read()
		else:
			print('Cropping video 100%')
			break
			
		ii+=1
		print('Cropping video %s%%' %(int(ii/(length-1)*100)), end='\r')

	vid2crop.release()
	out.release()
	cv2.destroyAllWindows()

	vidcap = cv2.VideoCapture(of + '_crop' + fex)
	width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
	height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
	return vidcap,width,height

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


def find_motion_box(grayimage, width, height, motion_box_margin):
	prev_Start = width
	prev_Stop = 0 

	the_box = np.zeros([height,width])
	#----Finding left and right edges
	le = int(width/2)
	re = int(width/2)
	for i in range(height):
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
	prev_Start = height
	prev_Stop = 0 
	te = int(height/2)
	be = int(height/2)
	for j in range(width):
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

	margin = motion_box_margin

	x_start = constrainNumber(le-margin,0,width-1)
	x_stop = constrainNumber(re+margin,0,width-1)
	y_start = constrainNumber(te-margin,0,height-1)
	y_stop = constrainNumber(be+margin,0,height-1)

	the_box[constrainNumber(te-margin,0,height-1),constrainNumber(le-margin,0,width-1):constrainNumber(re+margin,0,width-1)]=1
	the_box[constrainNumber(te-margin,0,height-1):constrainNumber(be+margin,0,height-1),constrainNumber(le-margin,0,width-1)]=1
	the_box[constrainNumber(be+margin,0,height-1),constrainNumber(le-margin,0,width-1):constrainNumber(re+margin,0,width-1)]=1
	the_box[constrainNumber(te-margin,0,height-1):constrainNumber(be+margin,0,height-1),constrainNumber(re+margin,0,width-1)]=1

	return the_box,x_start,x_stop,y_start,y_stop

def find_total_motion_box(vid2findbox,width,height,length,motion_box_thresh,motion_box_margin):
	total_box = np.zeros([height,width])
	ret, frame = vid2findbox.read()
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	ii=0
	while(vid2findbox.isOpened()):
		prev_frame = frame.astype(np.int32)
		ret, frame = vid2findbox.read()
		if ret==True:
			ii+=1
			print('Finding area of motion %s%%' %(int(ii/(length-1)*100)), end='\r')
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			frame = frame.astype(np.int32)

			motion_frame = (np.abs(frame-prev_frame)).astype(np.uint8)
			motion_frame = filter_frame(motion_frame,'Regular',thresh = motion_box_thresh, kernel_size=5)

			[the_box,x_start,x_stop,y_start,y_stop]=find_motion_box(motion_frame,width,height,motion_box_margin)
			total_box = total_box*(the_box==0)+the_box
		else:
			[total_motion_box,x_start,x_stop,y_start,y_stop] = find_motion_box(total_box,width,height,motion_box_margin)
			print('Finding area of motion 100%')
			break

	return x_start,x_stop,y_start,y_stop








import cv2
import numpy as np
import os

def average_image(filename):

	"""
	Post-processing tool. Finds and saves an average image of entire video.
	
	Usage:
	from _motionaverage import motionaverage
	motionaverage('filename.avi')
	"""

	of = os.path.splitext(filename)[0]
	video = cv2.VideoCapture(filename)
	ret, frame = video.read()
	length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
	average = frame.astype(np.float)/length
	ii = 0
	while(video.isOpened()):
		ret, frame = video.read()
		if ret==True:
			frame = np.array(frame)
			frame = frame.astype(np.float)    
			average += frame/length    
		else:
			break
		ii+=1
		print('Processing %s%%' %(int(ii/(length-1)*100)), end='\r')

	cv2.imwrite(of+'_average.bmp',average.astype(np.uint8))  

import cv2
import numpy as np
import time

def mg_show(self, filename = None):
	"""
	This function simply plays the current vidcap VideoObject. The speed of the video playback 
	might not match the true fps due to non-optimized code. 
	Parameters:
	filename(str): If left empty, the current vidcap object is played. If filename is given,
	this file is played instead"""
	if filename == None:
		filename = self.of+self.fex


	vidcap = cv2.VideoCapture(filename)
	fps = float(vidcap.get(cv2.CAP_PROP_FPS))
	# Check if camera opened successfully
	if (vidcap.isOpened()== False): 
		print("Error opening video stream or file")
	i = int(np.round((1/fps)*1000))
	 
	# Read until video is completed
	while(vidcap.isOpened()):
		# Capture frame-by-frame
		ret, frame = vidcap.read()
		if ret == True:
	 
			# Display the resulting frame
			cv2.imshow('Frame',frame)
	 
			# Press Q on keyboard to  exit
			if cv2.waitKey(i) & 0xFF == ord('q'):
				break
			
		# Break the loop
		else: 
			break
	# When everything done, release the video capture object
	vidcap.release()
	 
	# Closes all the frames
	cv2.destroyAllWindows()

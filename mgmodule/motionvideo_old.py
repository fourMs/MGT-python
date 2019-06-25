import numpy as np
import cv2
from scipy.signal import medfilt2d
import matplotlib.pyplot as plt


def mgmotion(filename,threshold = 0.1):
	cap = cv2.VideoCapture(filename);
	 
	fps = int(cap.get(cv2.CAP_PROP_FPS))
	width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))   
	height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
	length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
	fourcc = cv2.VideoWriter_fourcc(*'MJPG')
	out = cv2.VideoWriter('%s_motion_gray.avi' %filename,fourcc, fps, (width,height))

	frame = np.zeros([height,width])
	ii=0
	gramx = np.array([1,1])
	gramy = np.array([1,1])
	while(cap.isOpened()):
		prev_frame=frame
		ret, frame = cap.read()
		if ret==True:
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			frame = frame.astype(np.int16)
			motion_frame = ((np.abs(frame-prev_frame)>(threshold*255))*frame).astype(np.uint8)
			motion_frame = medfilt2d(motion_frame, kernel_size=5)
			gramx = np.append(gramx,np.mean(motion_frame,axis=0))
			gramy = np.append(gramy,np.mean(motion_frame,axis=1))   
			motion_frame = cv2.cvtColor(motion_frame, cv2.COLOR_GRAY2BGR)
			out.write(motion_frame)
			#cv2.imshow('frame',motion_frame)
			#if cv2.waitKey(1) & 0xFF == ord('q'):
			#	break
		else:
			break
		ii+=1
		print('Processing %s%%' %(int(ii/length*100)), end='\r')

	plt.imshow(gramx,cmap='gray')
	plt.savefig('gramx',dpi=300)
	cap.release()
	out.release()
	cv2.destroyAllWindows()


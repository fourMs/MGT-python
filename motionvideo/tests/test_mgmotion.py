import sys
sys.path.append('../..')
from motionvideo.mgmotion import mg_motion
import cv2
import numpy as np



mg_motion('pianist.avi',endtime = 1)
"""cap = cv2.VideoCapture('pianist.avi');
 
fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))   
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#fourcc = cv2.VideoWriter_fourcc(*'MJPG')
#out = cv2.VideoWriter('pianist_motion_gray.avi',fourcc, fps, (width,height))


frame = np.zeros([height,width])
ii=0
while(cap.isOpened()):
	prev_frame=frame
	ret, frame = cap.read()
	if ret==True:
		com, qom = mg_centroid(frame,width,height,True)
		print(com)
		#out.write(motion_frame)
		cv2.imshow('frame',frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	else:
		break
	ii+=1
	print('Processing %s%%' %(int(ii/length*100)), end='\r')


cap.release()
cv2.destroyAllWindows()"""


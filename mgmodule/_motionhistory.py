import cv2
import os
import numpy as np
from scipy.signal import medfilt2d
from ._centroid import mg_centroid

def motionhistory(self, kernel_size = 5, history_length = 20):
    ret, frame = self.video.read()
    of = os.path.splitext(self.filename)[0] 
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(of + '_motionhistory.avi',fourcc, self.fps, (self.width,self.height))
    
    ii = 0
    history = []
    if self.color == False:
    	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    while(self.video.isOpened()):
        prev_frame = frame
        ret, frame = self.video.read()

        if ret==True:
            if self.blur == 'Average':
                frame = cv2.blur(frame,(10,10)) #The higher these numbers the more blur you get
                    
            if self.color == True:
                frame = frame
            else:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame = np.array(frame)
            frame = frame.astype(np.float64)

            if self.method == 'Diff':
                if self.color == True:
                    motion_frame_rgb = np.zeros([self.height,self.width,3])

                    for i in range(frame.shape[2]):
                        motion_frame = np.abs(frame[:,:,i]-prev_frame[:,:,i])
                        motion_frame = motion_frame.astype(np.float64)
                        if self.filtertype == 'Regular':
                            motion_frame = (motion_frame>self.thresh*255)*motion_frame
                            motion_frame = medfilt2d(motion_frame, kernel_size)
                        elif self.filtertype == 'Binary':
                            motion_frame = (motion_frame>self.thresh*255)*255
                            motion_frame = medfilt2d(motion_frame, kernel_size)
                        elif self.filtertype == 'Blob':
                            motion_frame = cv2.erode(motion_frame,np.ones([kernel_size,kernel_size]),iterations=1)                         
                        motion_frame_rgb[:,:,i] = motion_frame

                    motion_history = motion_frame_rgb

                    motion_history = motion_history/history_length
                    for newframe in history:
                   	        motion_history += newframe/history_length
                    if len(history) > history_length: # or however long history you would like
                        history.pop(0)# pop first frame
                    history.append(motion_frame_rgb)
                    #motion_history = history_length*motion_history
                    motion_history = 0.5*history_length*motion_history.astype(np.uint64) #0.5 to not overload it poor thing
     
                else:
                    motion_frame = np.abs(frame-prev_frame)
                    motion_frame = motion_frame.astype(np.float64)
                    if self.filtertype == 'Regular':
                        motion_frame = (motion_frame>self.thresh*255)*motion_frame
                        motion_frame = medfilt2d(motion_frame, kernel_size)
                    elif self.filtertype == 'Binary':
                        motion_frame = (motion_frame>self.thresh*255)*255
                        motion_frame = medfilt2d(motion_frame, kernel_size)
                    elif self.filtertype == 'Blob':
                        motion_frame = cv2.erode(motion_frame,np.ones([kernel_size,kernel_size]),iterations=1)

                    motion_history = motion_frame
                    motion_history = motion_history/history_length
                    for newframe in history:
                   	        motion_history += newframe/history_length

                    if len(history) > history_length: # or however long history you would like
                        history.pop(0)# pop first frame
                    
                    history.append(motion_frame)
                    motion_history = 0.5*history_length*motion_history.astype(np.uint64)

            if self.color == False: 
                motion_history = cv2.cvtColor(motion_history.astype(np.uint8), cv2.COLOR_GRAY2BGR)
                motion_history_rgb = motion_history
            else: 
                motion_history_rgb = motion_history
            
            out.write(motion_history_rgb.astype(np.uint8))

        else:
            break
        ii+=1
        print('Processing %s%%' %(int(ii/(self.length-1)*100)), end='\r')

import cv2
import os
import numpy as np
from scipy.signal import medfilt2d
from ._centroid import mg_centroid

def motionhistory(self, kernel_size = 5):
    ret, frame = self.video.read()
    #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    of = os.path.splitext(self.filename)[0] 
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(of + '_motionhistory.avi',fourcc, self.fps, (self.width,self.height))
    ii = 0
    history = []
    while(self.video.isOpened()):
        
        ret, frame = self.video.read()
        if ret==True:
            # colorflag right here does not work yet
            #utgangspunktet argb
            
            if self.color == True:
                frame = frame
                prev_frame=frame
            else:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                prev_frame=frame
            #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = np.array(frame)
            frame = frame.astype(np.int32)

            if self.blur == 'Average':
                frame = cv2.blur(frame,(10,10)) #The higher these numbers the more blur you get
            else:
                pass

            if self.method == 'Diff':
                if self.color == True:
                    motion_frame_rgb = np.zeros([self.height,self.width,3])

                    for i in range(frame.shape[2]):
                        motion_frame = np.abs(frame[:,:,i]-prev_frame[:,:,i])
                        motion_frame = motion_frame.astype(np.uint8)
                        #motion_frame = ((motion_frame>(self.thresh*255))*frame).astype(np.uint8)
                        if self.filtertype == 'Regular':
                            motion_frame = (motion_frame>self.thresh*255)*motion_frame
                            motion_frame = medfilt2d(motion_frame, kernel_size)
                        elif self.filtertype == 'Binary':
                            motion_frame = (motion_frame>self.thresh*255)*255
                            motion_frame = medfilt2d(motion_frame, kernel_size)
                        elif self.filtertype == 'Blob':
                            motion_frame = cv2.erode(motion_frame,np.ones([kernel_size,kernel_size]),iterations=1)
                        
                        motion_frame_rgb[:,:,i] = motion_frame
                    gramy = np.append(gramx,np.mean(motion_frame_rgb,axis=0))
                    gramx = np.append(gramy,np.mean(motion_frame_rgb,axis=1))
                   
                else:

                    motion_frame = np.abs(frame-prev_frame)
                    motion_frame = motion_frame.astype(np.float32)
                    #motion_frame = ((motion_frame>(self.thresh*255))*frame).astype(np.uint8)
                    if self.filtertype == 'Regular':
                        motion_frame = (motion_frame>self.thresh*255)*motion_frame
                        motion_frame = medfilt2d(motion_frame, kernel_size)
                    elif self.filtertype == 'Binary':
                        motion_frame = (motion_frame>self.thresh*255)*255
                        motion_frame = medfilt2d(motion_frame, kernel_size)
                    elif self.filtertype == 'Blob':
                        motion_frame = cv2.erode(motion_frame,np.ones([kernel_size,kernel_size]),iterations=1)
                    #gramy = np.append(gramx,np.mean(motion_frame,axis=0))
                    #gramx = np.append(gramy,np.mean(motion_frame,axis=1))  
                    motion_history = motion_frame
                    for newframe in history:
                        motion_history += newframe
                    print(len(history))
                    if len(history) > 5: # or however long history you would like
                        history.pop(0)# pop first frame
                    
                    history.append(motion_frame)
                     
                    motion_history = motion_history.astype(np.uint8)

            if self.color == False: 
                motion_history = cv2.cvtColor(motion_history, cv2.COLOR_GRAY2BGR)
                motion_history_rgb = motion_history
            out.write(motion_history_rgb.astype(np.uint8))
            #combite, qombite = mg_centroid(motion_frame_rgb.astype(np.uint8),self.width,self.height,self.color)
            #if ii == 0:
            #    com = combite.reshape(1,2)
            #    qom = qombite
            #else:
            #    com=np.append(com,combite.reshape(1,2),axis =0)
            #    qom=np.append(qom,qombite)
        else:
            break
        ii+=1
        print('Processing %s%%' %(int(ii/(self.length-1)*100)), end='\r')

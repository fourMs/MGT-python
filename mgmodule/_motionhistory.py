import cv2
import os
import numpy as np
from scipy.signal import medfilt2d
from ._centroid import mg_centroid
from ._filter import motionfilter

def motionhistory(self, history_length = 20, kernel_size = 5, method = 'Diff', filtertype = 'Regular', thresh = 0.001, blur = 'None'):
    """
    Finds the difference in pixel value from one frame to the next in an input video, and saves the difference frame to a history tail. 
    The history frames are summed up and normalized, and added to the current difference frame to show the history of motion. 
    Outputs a video called filename + '_motionhistory.avi'.

    Parameters:
    history_length (int): How many frames will be saved to the history tail.
    kernel_size (int): Size of structuring element.
    method (str): Currently 'Diff' is the only implemented method. 
    filtertype (str): 'Regular', 'Binary', 'Blob' (see function motionfilter) 
	thresh (float): a number in [0,1]. Eliminates pixel values less than given threshold.
    blur (str): 'Average' to apply a blurring filter, 'None' otherwise.
	
    Returns:
    None
    """
    self.method = method
    self.filtertype = filtertype
    self.thresh = thresh
    self.blur = blur

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

            frame = (np.array(frame)).astype(np.float64)

            if self.method == 'Diff':
                if self.color == True:
                    motion_frame_rgb = np.zeros([self.height,self.width,3])
                    for i in range(frame.shape[2]):
                        motion_frame = (np.abs(frame[:,:,i]-prev_frame[:,:,i])).astype(np.float64)
                        motion_frame = motionfilter(motion_frame,self.filtertype,self.thresh,kernel_size)
                        motion_frame_rgb[:,:,i] = motion_frame

                    motion_history = motion_frame_rgb/history_length
                    for newframe in history:
                            motion_history += newframe/history_length
                    if len(history) > history_length: # or however long history you would like
                        history.pop(0)# pop first frame
                    history.append(motion_frame_rgb)
                    motion_history = 0.5*history_length*motion_history.astype(np.uint64) #0.5 to not overload it poor thing

                else:
                    motion_frame = (np.abs(frame-prev_frame)).astype(np.float64)
                    motion_frame = motionfilter(motion_frame,self.filtertype,self.thresh,kernel_size)
                    motion_history = motion_frame/history_length
                    for newframe in history:
                            motion_history += newframe/history_length

                    if len(history) > history_length: # or however long history you would like
                        history.pop(0)# pop first frame
                    
                    history.append(motion_frame)
                    motion_history = 0.5*history_length*motion_history.astype(np.uint64)

            if self.color == False: 
                motion_history_rgb = cv2.cvtColor(motion_history.astype(np.uint8), cv2.COLOR_GRAY2BGR)
            else: 
                motion_history_rgb = motion_history
            
            out.write(motion_history_rgb.astype(np.uint8))

        else:
            break
        ii+=1
        print('Processing %s%%' %(int(ii/(self.length-1)*100)), end='\r')


import cv2
import os
import numpy as np
from scipy.signal import medfilt2d
from ._centroid import mg_centroid
from ._filter import motionfilter

def history(self, history_length = 20, kernel_size = 5, filtertype = 'Regular', thresh = 0.001, blur = 'None'):
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
    self.filtertype = filtertype
    self.thresh = thresh
    self.blur = blur

    ret, frame = self.video.read()
    of = os.path.splitext(self.filename)[0] 
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(of + '_history.avi',fourcc, self.fps, (self.width,self.height))
    
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

            if self.color == True:
                total = frame/history_length
                if len(history) > (history_length): # or however long history you would like
                    history.pop(0)# pop first frame                
                for newframe in history:
                        total += newframe/len(history)

                history.append(frame)
                total = total.astype(np.uint64) #0.5 to not overload it poor thing
                print(frame[10,10,:])





            else:
                history_total = frame/history_length
                for newframe in history:
                        history_total += newframe/history_length
                if len(history) > (history_length-1): # or however long history you would like
                    history.pop(0)# pop first frame
                history.append(frame)
                history_total = history_total.astype(np.uint64)

            if self.color == False: 
                total = cv2.cvtColor(history_total.astype(np.uint8), cv2.COLOR_GRAY2BGR)
            else: 
                total= total
            
            out.write(total.astype(np.uint8))

        else:
            break
        ii+=1
        print('Processing %s%%' %(int(ii/(self.length-1)*100)), end='\r')

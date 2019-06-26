import cv2
import os
import numpy as np

def history(filename,history_length = 10):
    """
    Finds the difference in pixel value from one frame to the next in an input video, and saves the difference frame to a history tail. 
    The history frames are summed up and normalized, and added to the current difference frame to show the history of motion. 
    Outputs a video called filename + '_motionhistory.avi'.

    Parameters:
    history_length (int): How many frames will be saved to the history tail.
    kernel_size (int): Size of structuring element.
    method (str): Currently 'Diff' is the only implemented method. 
    filtertype (str): 'Regular', 'Binary', 'Blob' (see function filter_frame) 
	thresh (float): a number in [0,1]. Eliminates pixel values less than given threshold.
    blur (str): 'Average' to apply a blurring filter, 'None' otherwise.
	
    Returns:
    None
    """
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1] 
    video = cv2.VideoCapture(filename)
    ret, frame = video.read()
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    out = cv2.VideoWriter(of + '_history' + fex ,fourcc, fps, (width,height))

    ii = 0
    history = []

    while(video.isOpened()):
        if ret==True:
            ret,frame = video.read()
            frame = (np.array(frame)).astype(np.float64)
            if len(history)>0:
                history_total = frame/(len(history)+1)  
            else:
                history_total = frame          
            for newframe in history:
                    history_total += newframe/(len(history)+1)
            if len(history) > history_length or len(history) == history_length: # or however long history you would like
                history.pop(0)# pop first frame   
            history.append(frame)
            total = history_total.astype(np.uint64) #0.5 to not overload it poor thing
            
            out.write(total.astype(np.uint8))

        else:
            break
        ii+=1
        print('Processing %s%%' %(int(ii/(length-1)*100)), end='\r')

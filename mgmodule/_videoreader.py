import cv2
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import numpy as np

def mg_videoreader(filename, starttime, endtime, skip, contrast, brightness):
    of = os.path.splitext(filename)[0]
    # Cut out relevant bit of video using starttime and endtime
    if starttime != 0 or endtime != 0:
        trimvideo = ffmpeg_extract_subclip(filename, starttime, endtime, targetname= of +'_trim.avi')
        vidcap = cv2.VideoCapture(of + '_trim.avi')

    # Or just use whole video
    else:
        vidcap = cv2.VideoCapture(filename)

    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # To skip ahead a few frames before the next sample set skip to a value above 0
    count = 0;
    if skip != 0:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_skip.avi',fourcc, int(fps/skip), (width,height))
        success,image = vidcap.read()
        while success: 
            success,image = vidcap.read()
            if not success:
                break
            # on every frame we wish to use

            if (count % skip ==0):
              out.write(image.astype(np.uint8))  
            
            count += 1
        out.release()
        vidcap = cv2.VideoCapture(of + '_skip.avi')

    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    #overwrite the inputvalue for endtime to not cut the video at 0...
    if endtime == 0:
        endtime = length/fps

    count = 0;
    if brightness != 0 or contrast != 0:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_adjust.avi',fourcc, fps, (width,height))
        success,image = vidcap.read()
        while success: 
            success,image = vidcap.read()
            if not success:
                break
            # on every frame we wish to use
            image = np.int16(image)
            image = image * (contrast/127+1) - contrast + brightness
            image = np.clip(image, 0, 255)
            image = np.uint8(image)

            out.write(image.astype(np.uint8))  
            
            count += 1
        out.release()
        vidcap = cv2.VideoCapture(of + '_adjust.avi')

    return vidcap, length, width, height, fps, endtime

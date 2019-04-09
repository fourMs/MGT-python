import cv2
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import numpy as np
from ._videoadjust import contrast_brightness, skip_frames

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
    vidcap, length, fps, width, height = skip_frames(of, vidcap, skip, fps, width, height)

    #overwrite the inputvalue for endtime to not cut the video at 0...
    if endtime == 0:
        endtime = length/fps

    #To apply contrast/brightness before the motion analysis
    vidcap = contrast_brightness(of,vidcap,fps,width,height,contrast,brightness)

    return vidcap, length, width, height, fps, endtime


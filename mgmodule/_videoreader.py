import cv2
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import numpy as np
from ._videoadjust import mg_contrast_brightness, mg_skip_frames
from ._cropvideo import *


def mg_videoreader(filename, starttime = 0, endtime = 0, skip = 0, contrast = 0, brightness = 0, crop = 'none'):

    """
        Reads in a video file, and by input parameters user decide if it: trims the length, skips frames, applies contrast/brightness adjustments and/or crops image width/height.
        
        filename (str): Name of input parameter video file.
        starttime (float): cut the video from this start time (min) to analyze what is relevant.
        endtime (float): cut the video at this end time (min) to analyze what is relevant.
        skip (int): When proceeding to analyze next frame of video, this many frames are skipped.
        contrast (float): apply +/- 100 contrast to video
        brightness (float): apply +/- 100 brightness to video
        crop (str): 'None', 'Auto' or 'Manual' to crop video.
        
        return:
        - vidcap: cv2 video capture of edited video file
        - length, fps, width, height from vidcap
        - of: filename gets updated with what procedures it went through
    """
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    # Cut out relevant bit of video using starttime and endtime
    if starttime != 0 or endtime != 0:
        trimvideo = ffmpeg_extract_subclip(filename, starttime, endtime, targetname= of +'_trim' + fex)
        of = of + '_trim'
        vidcap = cv2.VideoCapture(of+fex)

    # Or just use whole video
    else:
        vidcap = cv2.VideoCapture(of + fex)

    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # To skip ahead a few frames before the next sample set skip to a value above 0
    if skip != 0:
        vidcap, length, fps, width, height = skip_frames(of, fex, vidcap, skip, fps, width, height)
        of = of + '_skip'

    #overwrite the inputvalue for endtime to not cut the video at 0...
    if endtime == 0:
        endtime = length/fps

    #To apply contrast/brightness before the motion analysis
    if contrast != 0 or brightness != 0:
        vidcap = contrast_brightness(of, fex, vidcap,fps,width,height,contrast,brightness)
        of = of + '_cb'

    # Crops video either manually or automatically 
    if crop != 'none':
        [vidcap,width,height] = cropvideo(fps, width, height, length, of, fex, crop, motion_box_thresh = 0.1, motion_box_margin = 1)
        of = of + '_crop'


    return vidcap, length, width, height, fps, endtime, of


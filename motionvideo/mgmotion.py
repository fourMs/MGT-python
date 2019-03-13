 #MGMOTION - Calculate various motion features from a video file
# mgmotion computes a motion video, motiongram, quantity of motion, centroid of
# motion, width of motion, and height of motion from the video file or musical
# gestures data structure. The default method is to use plain frame differencing
# ('Diff'). A more expensive optical flow field can be calculated with the
# 'OpticalFlow' method. The mgmotion founction also provides a color mode, and the
# possibility to convert images with white on black instead of black on white. To
# use these modes, you need to set mode in the command, e.g.,
# mg.video.mode.color = 'On'
# mg.video.mode.convert = 'On'
#
# syntax:
# Call function with filename, method,starttime,endtime,filtertype,threshold
#
# input:
# filename: the name of the video file
# mg: instead of filename, uses a musical gestures data structure
# 'Diff', 'OpticalFlow': indicate the method used to compute the
# motion. 'Diff' method calculates the absolute frame difference between
# two successive frames. 'OpticalFlow' calculates the optical flow field
# filtertype: Binary, Regular, Blob. When choosing Blob, the element
# structure needs to be constructed using function strel
# thresh: threshold [0,1] (default=0.1)
#
# output:
# mg, a musical gestures data structure containing the computed motion
# image, motiongram, qom, com#
# mg = mginitstruct

import numpy as np
import os
import csv
import cv2
from scipy.signal import medfilt2d
from matplotlib import pyplot as plt
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

colorflag = 'true'


class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message


def mg_videoreader(filename, method = 'Diff', filtertype = 'Regular', thresh = 0.1, starttime = 0, endtime = 0, skip = 0):

    # Cut out relevant bit of video using starttime and endtime
    if starttime != 0 or endtime != 0:
        trimvideo = ffmpeg_extract_subclip(filename, starttime, endtime, targetname="trim.avi")
        vidcap = cv2.VideoCapture("trim.avi")

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
        out = cv2.VideoWriter('skip.avi',fourcc, int(fps/skip), (width,height))
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
        vidcap = cv2.VideoCapture("skip.avi")

    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    #overwrite the inputvalue for endtime to not cut the video at 0...
    if endtime == 0:
        endtime = length/fps

    return vidcap, length, width, height, fps, endtime


def mg_centroid(image, width, height, colorflag):
    #mgcentroid computes the centroid of an image/frame.
    if colorflag == 'true':
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    #x = np.linspace(1,width,width); y = np.linspace(1,height,height)
    x = np.arange(width)
    y = np.arange(height)
    qom = cv2.sumElems(image)[0] #deles på width*height
    mx = np.mean(image,axis=0)
    my = np.mean(image,axis=1)
    comx = x.reshape(1,width)@mx.reshape(width,1)/np.sum(mx)
    comy = y.reshape(1,height)@my.reshape(height,1)/np.sum(my)
  
    com = np.zeros(2)
    com[0]=comx
    com[1]=comy

    return com, qom

def mg_motion(filename, method = 'Diff', filtertype = 'Regular', thresh = 0.01, starttime = 0, endtime = 0, blur = 'Average', skip = 5):
    #spatial blur før terskling, dilate,. thresh = neg og over 1. velge hoppstørrelse: antall frames øvre grense.
    ii = 0
    filenametest = 'true'
    for c in filename:
        if c.isalpha() == True or c.isnumeric() == True or c == '.':
            pass
        else: 
            filenametest = 'false'

    if filenametest == 'true':
        if method != 'Diff' and method != 'OpticalFlow':
            msg = 'Please specify a method for motion estimation as str: Diff or OpticalFlow.'
            raise InputError(msg) 

        if filtertype != 'Regular' and filtertype != 'Binary':
            msg = 'Please specify a filter type as str: Regular or Binary'
            raise InputError(msg)

        if blur != 'Average' and filtertype != 'None':
            msg = 'Please specify a blur type as str: Average or None'
            raise InputError(msg)

        if not isinstance(thresh,float) and not isinstance(thresh, int):
            msg = 'Please specify a threshold as a float between 0 and 1.'
            raise InputError(msg)

        if not isinstance(starttime,float) and not isinstance(starttime,int):
            msg = 'Please specify a starttime as a float.'
            raise InputError(msg)

        if not isinstance(endtime,float) and not isinstance(endtime,int):
            msg = 'Please specify a endtime as a float.'
            raise InputError(msg)

        if not isinstance(skip,int):
            msg = 'Please specify a skip as an integer of frames you wish to skip (Max = N frames).'
            raise InputError(msg)        

    else:
        msg = 'Minimum input for this function: filename as a str.'
        raise InputError(msg)



    cap, length, width, height, fps, endtime = mg_videoreader(filename, method, filtertype, thresh, starttime, endtime)

    frame = np.zeros([height,width])
    of = os.path.splitext(filename)[0] 
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(of + '_motion.avi',fourcc, fps, (width,height))
    #f = cap


    gramx = np.array([1,1])
    gramy = np.array([1,1])
    qom = np.array([]) #quantity of motion
    com = np.array([]) #centroid of motion
    #aom = [] #area of motion
    #wom = [] #width of motion
    #hom = [] #height of motion


    ii = 0
    while(cap.isOpened()):

        prev_frame=frame
        ret, frame = cap.read()

        
        if ret==True:
            # colorflag right here does not work yet
            #utgangspunktet argb
            """ 
            if colorflag == 'true':
                frame = frame
            else:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            """
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = frame.astype(np.int16)
            if blur == 'Average':
                frame = cv2.blur(frame,(10,10)) #The higher these numbers the more blur you get
            else:
                pass
            plt.imshow(frame)
            if method == 'Diff':
                motion_frame = np.abs(frame-prev_frame)
                motion_frame = ((motion_frame>(thresh*255))*frame).astype(np.uint8)
                motion_frame = medfilt2d(motion_frame, kernel_size=5)
            elif method == 'OpticalFlow':
                #Optical Flow not implemented yet!!!
                motion_frame = ((np.abs(frame-prev_frame)>(thresh*255))*frame).astype(np.uint8) 

            gramx = np.append(gramx,np.mean(motion_frame,axis=0))
            gramy = np.append(gramy,np.mean(motion_frame,axis=1))   
            motion_frame = cv2.cvtColor(motion_frame, cv2.COLOR_GRAY2BGR)
            out.write(motion_frame)
            combite, qombite = mg_centroid(motion_frame,width,height,colorflag)
            #plt.scatter(combite[0],combite[1])
            print(combite.shape)
            if ii == 0:
                com = combite.reshape(1,2)
                qom = qombite

            else:
                com=np.append(com,combite.reshape(1,2),axis =0)
                qom=np.append(qom,qombite)
            print(qombite)
            #com.append(combite)
            #cv2.imshow('frame',motion_frame)
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #   break
        else:
            break
        ii+=1
        print('Processing %s%%' %(int(ii/length*100)), end='\r')
        
    qom = qom.reshape(len(qom),1)
    np.savetxt('%s_data.csv'%of,np.append(qom,com,axis=1),delimiter = ',')
    cap.release()
    out.release()
    cv2.destroyAllWindows()


mg_motion("dance.avi", endtime = 10, skip = 4)
    

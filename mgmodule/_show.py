import cv2
import numpy as np
import os
from matplotlib import pyplot as plt


def mg_show(self, filename=None, key=None):
    """
    This function simply plays the current vidcap VideoObject. The speed of the video playback 
    might not match the true fps due to non-optimized code. 

    Parameters
    ----------
    - filename : str, optional

        Default is `None`. If `None`, the current video to which the MgObject points is played.
        If filename is given, this file is played instead. 
    - key : {None, 'mgx', 'mgy', 'average', 'plot', 'motion', 'history', 'motionhistory', 'sparse', 'dense'}, optional

        If either of these shorthands is used the method attempts to show the 
        (previously rendered) video file corresponding to the one in the MgObject.
    """

    video_mode = True

    def show_image(ending, title=''):
        video_mode = False
        img = cv2.imread(self.of + ending, 3)
        cv2.imshow(title, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if filename == None:

        if key == None:
            filename = self.of+self.fex
        elif key.lower() == 'mgx':
            show_image('_mgx.png', 'Horizontal Motiongram')
        elif key.lower() == 'mgy':
            show_image('_mgy.png', 'Vertical Motiongram')
        elif key.lower() == 'average':
            show_image('_average.png', 'Average')
        elif key.lower() == 'plot':
            show_image('_motion_com_qom.png',
                       'Centroid and Quantity of Motion')

        elif key.lower() == 'motion':
            if os.path.exists(self.of + '_motion' + self.fex):
                filename = self.of + '_motion' + self.fex
            else:
                print("No motion video found corresponding to",
                      self.of+self.fex, ". Try making one with .motion()")
        elif key.lower() == 'history':
            if os.path.exists(self.of + '_history' + self.fex):
                filename = self.of + '_history' + self.fex
            else:
                print("No history video found corresponding to",
                      self.of+self.fex, ". Try making one with .history()")
        elif key.lower() == 'motionhistory':
            if os.path.exists(self.of + '_motionhistory' + self.fex):
                filename = self.of + '_motionhistory' + self.fex
            else:
                print("No motion history video found corresponding to",
                      self.of+self.fex, ". Try making one with .motionhistory()")
        elif key.lower() == 'sparse':
            if os.path.exists(self.of + '_flow_sparse' + self.fex):
                filename = self.of + '_flow_sparse' + self.fex
            else:
                print("No sparse optical flow video found corresponding to",
                      self.of+self.fex, ". Try making one with .flow.sparse()")
        elif key.lower() == 'dense':
            if os.path.exists(self.of + '_flow_dense' + self.fex):
                filename = self.of + '_flow_dense' + self.fex
            else:
                print("No dense optical flow video found corresponding to",
                      self.of+self.fex, ". Try making one with .flow.dense()")
        else:
            print("Unknown shorthand.\n",
                  "For images, try 'mgx', 'mgy', 'average' or 'plot'.\n",
                  "For videos try 'motion', 'history', 'motionhistory', 'sparse' or 'dense'.\n",
                  "Showing video from the MgObject.")
            filename = self.of+self.fex

    if self.fex == '.png':
        video_mode = False
        show_image('.png')

    if video_mode and (filename != None):
        vidcap = cv2.VideoCapture(filename)
        fps = float(vidcap.get(cv2.CAP_PROP_FPS))
        # Check if camera opened successfully
        if (vidcap.isOpened() == False):
            print("Error opening video stream or file")
        i = int(np.round((1/fps)*1000))

        # Read until video is completed
        while(vidcap.isOpened()):
            # Capture frame-by-frame
            ret, frame = vidcap.read()
            if ret == True:

                # Display the resulting frame
                cv2.imshow('Frame', frame)

                # Press Q on keyboard to  exit
                if cv2.waitKey(i) & 0xFF == ord('q'):
                    break

            # Break the loop
            else:
                break
        # When everything done, release the video capture object
        vidcap.release()

        # Closes all the frames
        cv2.destroyAllWindows()

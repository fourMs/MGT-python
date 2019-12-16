import cv2
import numpy as np
import os


def mg_show(self, filename=None, video=None):
    """

    This function simply plays the current vidcap VideoObject. The speed of the video playback 
    might not match the true fps due to non-optimized code. 

    Parameters:

    - filename(str): If left empty, the current vidcap object is played. If filename is given,
    this file is played instead. If either of the shorthands 'motion', 'history', or 'motionhistory' is used
    the method attempts to show the (previously rendered) video file corresponding to the one in the MgObject.

    """
    if filename == None:
        if video == None:
            filename = self.of+self.fex
        elif video == 'motion':
            if os.path.exists(self.of + '_motion' + self.fex):
                filename = self.of + '_motion' + self.fex
            else:
                print("No motion video found corresponding to",
                      self.of+self.fex, ". Try making one with .motion()")
        elif video == 'history':
            if os.path.exists(self.of + '_history' + self.fex):
                filename = self.of + '_history' + self.fex
            else:
                print("No history video found corresponding to",
                      self.of+self.fex, ". Try making one with .history()")
        elif video == 'motionhistory':
            if os.path.exists(self.of + '_motionhistory' + self.fex):
                filename = self.of + '_motionhistory' + self.fex
            else:
                print("No motion history video found corresponding to",
                      self.of+self.fex, ". Try making one with .motionhistory()")
        else:
            print("Unknown shorthand. Try 'motion', 'history', or 'motionhistory'. Showing video from the MgObject.")
            filename = self.of+self.fex

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

import cv2
import numpy as np
import os
from matplotlib import pyplot as plt
from IPython.display import Image, display


def mg_show(self, filename=None, key=None, mode='windowed', window_width=640, window_height=480, window_title=None):

    def show(file, width=640, height=480, mode='windowed', title='Untitled'):
        if mode.lower() == 'windowed':
            cmd = f'ffplay {file} -x {width} -y {height} -window_title "{title}"'
            os.system(cmd)
        elif mode.lower() == 'notebook':
            video_formats = ['.avi', '.mp4', '.mov', '.mkv', '.mpg',
                             '.mpeg', '.webm', '.ogg', '.ts', '.wmv', '.3gp']
            image_formats = ['.jpg', '.png', '.jpeg', '.tiff', '.gif', '.bmp']
            file_extension = os.path.splitext(file)[1].lower()

            if file_extension in video_formats:
                file_type = 'video'
            elif file_extension in image_formats:
                file_type = 'image'
            # print(f'This is a(n) {file_type} file.')
            if file_type == 'image':
                display(Image(file))
            elif file_type == 'video':
                print('To be implemented...')

        else:
            print(
                f'Unrecognized mode: "{mode}". Try "windowed" or "notebook".')

    if window_title == None:
        window_title = self.filename

    if filename == None:

        if key == None:
            filename = self.filename
            show(file=filename, width=window_width,
                 height=window_height, mode=mode, title=window_title)
        elif key.lower() == 'mgx':
            filename = self.of + '_mgx.png'
            show(file=filename, width=window_width,
                 height=window_height, mode=mode, title=f'Horizontal Motiongram | {filename}')
        elif key.lower() == 'mgy':
            filename = self.of + '_mgy.png'
            show(file=filename, width=window_width,
                 height=window_height, mode=mode, title=f'Vertical Motiongram | {filename}')
        elif key.lower() == 'average':
            filename = self.of + '_average.png'
            show(file=filename, width=window_width,
                 height=window_height, mode=mode, title=f'Average | {filename}')
        elif key.lower() == 'plot':
            filename = self.of + '_motion_com_qom.png'
            show(file=filename, width=window_width,
                 height=window_height, mode=mode, title=f'Centroid and Quantity of Motion | {filename}')

        elif key.lower() == 'motion':
            # motion is always avi
            if os.path.exists(self.of + '_motion.avi'):
                filename = self.of + '_motion.avi'
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Motion | {filename}')
            else:
                print("No motion video found corresponding to",
                      self.of+self.fex, ". Try making one with .motion()")
        elif key.lower() == 'history':
            if os.path.exists(self.of + '_history' + self.fex):
                filename = self.of + '_history' + self.fex
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'History | {filename}')
            else:
                print("No history video found corresponding to",
                      self.of+self.fex, ". Try making one with .history()")
        # since motionhistory() is deprecated this now expects
        # a _motion_history which is a result from .motion().history()
        elif key.lower() == 'motionhistory':
            # motion_history is always avi
            if os.path.exists(self.of + '_motion_history.avi'):
                filename = self.of + '_motion_history.avi'
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Motion History | {filename}')
            else:
                print("No motion history video found corresponding to",
                      self.of+self.fex, ". Try making one with .motionhistory()")
        elif key.lower() == 'sparse':
            # optical flow is always avi
            if os.path.exists(self.of + '_flow_sparse.avi'):
                filename = self.of + '_flow_sparse.avi'
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Sparse Optical Flow | {filename}')
            else:
                print("No sparse optical flow video found corresponding to",
                      self.of+self.fex, ". Try making one with .flow.sparse()")
        elif key.lower() == 'dense':
            # optical flow is always avi
            if os.path.exists(self.of + '_flow_dense.avi'):
                filename = self.of + '_flow_dense.avi'
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Dense Optical Flow | {filename}')
            else:
                print("No dense optical flow video found corresponding to",
                      self.of+self.fex, ". Try making one with .flow.dense()")
        else:
            print("Unknown shorthand.\n",
                  "For images, try 'mgx', 'mgy', 'average' or 'plot'.\n",
                  "For videos try 'motion', 'history', 'motionhistory', 'sparse' or 'dense'.")

    return self


def mg_show_deprecated(self, filename=None, key=None):
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
        # since motionhistory() is deprecated this now expects
        # a _motion_history which is a result from .motion().history()
        elif key.lower() == 'motionhistory':
            if os.path.exists(self.of + '_motion_history' + self.fex):
                filename = self.of + '_motion_history' + self.fex
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

        video_title = os.path.basename(filename)

        # Read until video is completed
        while(vidcap.isOpened()):
            # Capture frame-by-frame
            ret, frame = vidcap.read()
            if ret == True:

                # Display the resulting frame
                cv2.imshow(video_title, frame)

                # Press Q on keyboard to  exit
                # if cv2.waitKey(i) & 0xFF == ord('q'):
                if cv2.waitKey(i) & 0xFF in [27, ord('q'), ord(' ')]:
                    break

            # Break the loop
            else:
                break
        # When everything done, release the video capture object
        vidcap.release()

        # Closes all the frames
        cv2.destroyAllWindows()

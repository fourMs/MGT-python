import cv2
import numpy as np
import os
from matplotlib import pyplot as plt
from IPython.display import Image, Video, display
from base64 import b64encode


def mg_show(self, filename=None, key=None, mode='windowed', window_width=640, window_height=480, window_title=None):
    """
    General method to show an image or video file either in a window, or inline in a jupyter notebook.

    Args:
        filename (str, optional): If given, `mg_show` will show this file instead of what it inherits from its parent object. Defaults to None.
        key (str, optional): If given, `mg_show` will search for file names corresponding to certain processes you have previously rendered on your source. It is meant to be a shortcut, so you don't have to remember the exact name (and path) of eg. a motion video corresponding to your source in your MgObject, but you rather just use `MgObject('path/to/vid.mp4').show(key='motion')`. Accepted values are 'mgx', 'mgy', 'average', 'plot', 'motion', 'history', 'motionhistory', 'sparse', and 'dense'. Defaults to None.
        mode (str, optional): Whether to show things in a separate window or inline in the jupyter notebook. Accepted values are 'windowed' and 'notebook'. Defaults to 'windowed'.
        window_width (int, optional): The width of the window. Defaults to 640.
        window_height (int, optional): The height of the window. Defaults to 480.
        window_title (str, optional): The title of the window. If None, the title of the window will be the file name. Defaults to None.
    """

    def show(file, width=640, height=480, mode='windowed', title='Untitled'):
        """
        Helper function which actually does the "showing".

        Args:
            file (str): Path to the file.
            width (int, optional): The width of the window. Defaults to 640.
            height (int, optional): The height of the window. Defaults to 480.
            mode (str, optional): 'windowed' will use ffplay (in a separate window), while 'notebook' will use Image or Video from IPython.display. Defaults to 'windowed'.
            title (str, optional): The title of the window. Defaults to 'Untitled'.
        """
        if mode.lower() == 'windowed':
            cmd = f'ffplay {file} -x {width} -y {height} -window_title "{title}"'
            # os.system(cmd)
            show_async(cmd)
        elif mode.lower() == 'notebook':
            video_formats = ['.avi', '.mp4', '.mov', '.mkv', '.mpg',
                             '.mpeg', '.webm', '.ogg', '.ts', '.wmv', '.3gp']
            image_formats = ['.jpg', '.png', '.jpeg', '.tiff', '.gif', '.bmp']
            file_extension = os.path.splitext(file)[1].lower()

            if file_extension in video_formats:
                file_type = 'video'
            elif file_extension in image_formats:
                file_type = 'image'
            if file_type == 'image':
                display(Image(file))
            elif file_type == 'video':
                if file_extension not in ['.mp4', '.webm', '.ogg']:
                    from musicalgestures._utils import convert_to_mp4
                    print(
                        'Only mp4, webm and ogg videos are supported in notebook mode.')
                    video_to_display = convert_to_mp4(file)
                else:
                    video_to_display = file

                display(Video(video_to_display, width=800))

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

    else:
        show(file=filename, width=window_width,
             height=window_height, mode=mode, title=window_title)

    return self


def show_async(command):
    """Helper function to show ffplay windows asynchronously"""
    import asyncio

    async def run_cmd(command):
        process = await asyncio.create_subprocess_shell(command)
        await process.communicate()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # if cleanup: 'RuntimeError: There is no current event loop..'
        loop = None

    if loop and loop.is_running():
        tsk = loop.create_task(run_cmd(command))
    else:
        asyncio.run(run_cmd(command))
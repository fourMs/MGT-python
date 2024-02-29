# import cv2
# import numpy as np
import os
from matplotlib import pyplot as plt
from IPython.display import Image, display, HTML
# try:
from IPython.display import Video
# except:
#     from IPython.core.display import Video
from base64 import b64encode
import musicalgestures


def mg_show(self, filename=None, key=None, mode='windowed', window_width=640, window_height=480, window_title=None):
    # def mg_show(self, filename=None, mode='windowed', window_width=640, window_height=480, window_title=None):
    """
    General method to show an image or video file either in a window, or inline in a jupyter notebook.

    Args:
        filename (str, optional): If given, `mg_show` will show this file instead of what it inherits from its parent object. Defaults to None.
        key (str, optional): If given, `mg_show` will search for file names corresponding to certain processes you have previously rendered on your source. It is meant to be a shortcut, so you don't have to remember the exact name (and path) of eg. a motion video corresponding to your source in your MgVideo, but you rather just use `MgVideo('path/to/vid.mp4').show(key='motion')`. Accepted values are 'mgx', 'mgy', 'vgx', 'vgy', 'blend', 'plot', 'motion', 'history', 'motionhistory', 'sparse', and 'dense'. Defaults to None.
        mode (str, optional): Whether to show things in a separate window or inline in the jupyter notebook. Accepted values are 'windowed' and 'notebook'. Defaults to 'windowed'.
        window_width (int, optional): The width of the window. Defaults to 640.
        window_height (int, optional): The height of the window. Defaults to 480.
        window_title (str, optional): The title of the window. If None, the title of the window will be the file name. Defaults to None.
    """

    def show(file, width=640, height=480, mode='windowed', title='Untitled', parent=None):
        """
        Helper function which actually does the "showing".

        Args:
            file (str): Path to the file.
            width (int, optional): The width of the window. Defaults to 640.
            height (int, optional): The height of the window. Defaults to 480.
            mode (str, optional): 'windowed' will use ffplay (in a separate window), while 'notebook' will use Image or Video from IPython.display. Defaults to 'windowed'.
            title (str, optional): The title of the window. Defaults to 'Untitled'.
        """

        # Check's if the environment is a Google Colab document
        if musicalgestures._utils.in_colab():
            mode = 'notebook'

        if mode.lower() == 'windowed':
            # from musicalgestures._utils import wrap_str
            # cmd = f'ffplay {wrap_str(file)} -window_title {wrap_str(title)} -x {width} -y {height}'

            video_to_display = os.path.realpath(file)
            cmd = ' '.join(map(str, ['ffplay', video_to_display, '-window_title', title, '-x', width, '-y', height]))
            show_in_new_process(cmd)            

        elif mode.lower() == 'notebook':
            video_formats = ['.avi', '.mp4', '.mov', '.mkv', '.mpg', '.mpeg', '.webm', '.ogg', '.ts', '.wmv', '.3gp']
            image_formats = ['.jpg', '.png', '.jpeg', '.tiff', '.gif', '.bmp']
            
            of, file_extension = os.path.splitext(file)
            of, file_extension = of.lower(), file_extension.lower()

            if file_extension in video_formats:
                file_type = 'video'
            elif file_extension in image_formats:
                file_type = 'image'
            
            if file_type == 'image':
                display(Image(file))    
            elif file_type == 'video':
                if file_extension not in ['.mp4', '.webm', '.ogg']:
                    keys = parent.__dict__.keys()
                    
                    if "as_mp4" not in keys:
                        print('Only mp4, webm and ogg videos are supported in notebook mode.')
                        video_to_display = musicalgestures._utils.convert_to_mp4(file)
                        # register converted video as_mp4 for parent MgVideo
                        parent.as_mp4 = musicalgestures.MgVideo(video_to_display)
                    else:
                        video_to_display = parent.as_mp4.filename
                else:
                    video_to_display = file

                # check width and height of video, if they are bigger than "appropriate", limit their dimensions
                video_width, video_height = musicalgestures._utils.get_widthheight(video_to_display)
                video_width = video_width if video_width <= width else width
                video_height = video_height if video_height <= height else height

                # if the video is at the same folder as the notebook, we need to use relative path
                # and if it is somewhere else, we need to embed it to make it work (neither absolute nor relative paths seem to work without embedding)
                cwd = os.getcwd().replace('\\', '/')
                file_dir = os.path.dirname(video_to_display).replace('\\', '/')
                                
                def colab_display(video_to_display, video_width, video_height):
                  video_file = open(video_to_display, "r+b").read()
                  video_url = f"data:video/mp4;base64,{b64encode(video_file).decode()}"
                  return HTML(f"""<video width={video_width} height={video_height} controls><source src="{video_url}"></video>""")

                if file_dir == cwd:
                    try:
                        video_to_display = os.path.relpath(video_to_display, os.getcwd()).replace('\\', '/')
                        if musicalgestures._utils.in_colab():
                            display(colab_display(video_to_display, video_width, video_height))
                        else:
                            display(Video(video_to_display,width=video_width, height=video_height))
                    except ValueError:
                        video_to_display = os.path.abspath(video_to_display, os.getcwd()).replace('\\', '/')
                        if musicalgestures._utils.in_colab():
                            display(colab_display(video_to_display, video_width, video_height))
                        else:
                            display(Video(video_to_display, width=video_width, height=video_height))
                else:
                    try:
                        video_to_display = os.path.relpath(video_to_display, os.getcwd()).replace('\\', '/')
                        if musicalgestures._utils.in_colab():
                            display(colab_display(video_to_display, video_width, video_height))
                        else:
                            display(Video(video_to_display, width=video_width, height=video_height))
                    except ValueError:
                        video_to_display = os.path.abspath(video_to_display, os.getcwd()).replace('\\', '/')
                        if musicalgestures._utils.in_colab():
                            display(colab_display(video_to_display, video_width, video_height))
                        else:
                            display(Video(video_to_display, width=video_width,height=video_height))

        else:
            print(f'Unrecognized mode: "{mode}". Try "windowed" or "notebook".')

    if window_title == None:
        window_title = self.filename

    if filename == None:
        keys = self.__dict__.keys()
        if key == None:
            filename = self.filename
            show(file=filename, width=window_width,
                 height=window_height, mode=mode, title=window_title, parent=self)

        elif key.lower() == 'mgx':
            if "motiongram_x" in keys:
                filename = self.motiongram_x.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Horizontal Motiongram | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known horizontal motiongram for this file.")

        elif key.lower() == 'mgy':
            if "motiongram_y" in keys:
                filename = self.motiongram_y.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Vertical Motiongram | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known vertical motiongram for this file.")

        elif key.lower() == 'vgx':
            if "videogram_x" in keys:
                filename = self.videogram_x.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Horizontal Videogram | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known horizontal videogram for this file.")

        elif key.lower() == 'vgy':
            if "videogram_y" in keys:
                filename = self.videogram_y.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Vertical Videogram | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known vertical videogram for this file.")
            
        elif key.lower() == 'ssm':
            if "ssm_fig" in keys:
                filename = self.ssm_fig.image
                if len(filename) == 2:
                    show(file=filename[0], width=window_width, height=window_height, mode=mode, title=f'Horizontal SSM | {filename}', parent=self)
                    show(file=filename[1], width=window_width, height=window_height, mode=mode, title=f'Vertical SSM | {filename}', parent=self)
                else:    
                    show(file=filename, width=window_width, height=window_height, mode=mode, title=f'Self-Similarity Matrix | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known self-smilarity matrix for this file.")

        elif key.lower() == 'blend':
            if "blend_image" in keys:
                filename = self.blend_image.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Blended Image | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known blended image for this file.")
            
        elif key.lower() == 'plot':
            # filename = self.of + '_motion_com_qom.png'
            if "motion_plot" in keys:
                filename = self.motion_plot.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Centroid and Quantity of Motion | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known motion plot for this file.")

        elif key.lower() == 'motion':
            if "motion_video" in keys:
                filename = self.motion_video.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Motion Video | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known motion video for this file.")

        elif key.lower() == 'history':
            if "history_video" in keys:
                filename = self.history_video.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'History Video | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known history video for this file.")

        elif key.lower() == 'motionhistory':
            if "motion_video" in keys:
                motion_video_keys = self.motion_video.__dict__.keys()
                if "history_video" in motion_video_keys:
                    filename = self.motion_vide.history_video.filename
                    show(file=filename, width=window_width,
                         height=window_height, mode=mode, title=f'Motion History Video | {filename}', parent=self)
                else:
                    raise FileNotFoundError(
                        "There is no known motion history video for this file.")
            else:
                raise FileNotFoundError(
                    "There is no known motion video for this file.")

        elif key.lower() == 'sparse':
            if "flow_sparse_video" in keys:
                filename = self.flow_sparse_video.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Sparse Optical Flow Video | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known sparse optial flow video for this file.")

        elif key.lower() == 'dense':
            if "flow_dense_video" in keys:
                filename = self.flow_dense_video.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Dense Optical Flow Video | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known dense optial flow video for this file.")

        elif key.lower() == 'pose':
            if "pose_video" in keys:
                filename = self.pose_video.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Pose Video | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known pose video for this file.")

        elif key.lower() == 'warp':
            if "warp_audiovisual_beats" in keys:
                filename = self.warp_audiovisual_beats.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Warp Audiovisual Video | {filename}', parent=self)
            else:
                raise FileNotFoundError(
                    "There is no known warp audiovisual beats video for this file.")

        elif key.lower() == 'blur':
            if "blur_faces" in keys:
                filename = self.blur_faces.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Blur Faces Video | {filename}', parent=self)

        elif key.lower() == 'subtract':
            if "subtract" in keys:
                filename = self.subtract.filename
                show(file=filename, width=window_width,
                     height=window_height, mode=mode, title=f'Background Subtraction Video | {filename}', parent=self)
            else:
                raise FileNotFoundError("There is no known subtract video for this file.")

        else:
            print("Unknown shorthand.\n",
                  "For images, try 'mgx', 'mgy', 'vgx', 'vgy', 'ssmx','ssmy', 'blend' or 'plot'.\n",
                  "For videos try 'motion', 'history', 'motionhistory', 'sparse', 'dense', 'pose', 'warp', 'blur' or 'subtract'.")

    else:
        show(file=filename, width=window_width,
             height=window_height, mode=mode, title=window_title, parent=self)
    # show(file=filename, width=window_width, height=window_height, mode=mode, title=window_title)

    return self


def show_in_new_process(cmd):
    import subprocess
    import sys

    # import platform
    # from musicalgestures._utils import wrap_str
    # module_path = os.path.realpath(os.path.dirname(musicalgestures.__file__)).replace('\\', '/')

    # the_system = platform.system()
    # pythonkw = "python"
    
    # if the_system != "Windows":
    #     pythonkw += "3"
    # pyfile = wrap_str(module_path + '/_show_window.py')
    # cmd = [pythonkw, pyfile, wrap_str(cmd)]
    
    with open(os.devnull, 'r+b', 0) as DEVNULL:
        process = subprocess.Popen(cmd, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True)
    # time.sleep(1)
    if process.poll():
        sys.exit(process.returncode)

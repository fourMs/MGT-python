class MgProgressbar():
    """
    Calls in a loop to create terminal progress bar.
    """

    def __init__(
            self,
            total=100,
            time_limit=0.5,
            prefix='Progress',
            suffix='Complete',
            decimals=1,
            length=40,
            fill='█'):
        """
        Initialize the MgProgressbar object.

        Args:
            total (int, optional): Total iterations. Defaults to 100.
            time_limit (float, optional): The minimum refresh rate of the progressbar in seconds. Defaults to 0.5.
            prefix (str, optional): Prefix string. Defaults to 'Progress'.
            suffix (str, optional): Suffix string. Defaults to 'Complete'.
            decimals (int, optional): Positive number of decimals in process percent. Defaults to 1.
            length (int, optional): Character length of the status bar. Defaults to 40.
            fill (str, optional): Bar fill character. Defaults to '█'.
        """

        self.total = total - 1
        self.time_limit = time_limit
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.now = self.get_now()
        self.finished = False
        self.could_not_get_terminal_window = False
        self.tw_width = 0
        self.tw_height = 0
        self.display_only_percent = False

    def get_now(self):
        """
        Gets the current time.

        Returns:
            datetime.datetime.timestamp: The current time.
        """
        from datetime import datetime
        return datetime.timestamp(datetime.now())

    def over_time_limit(self):
        """
        Checks if we should redraw the progress bar at this moment.

        Returns:
            bool: True if equal or more time has passed than `self.time_limit` since the last redraw.
        """
        callback_time = self.get_now()
        return callback_time - self.now >= self.time_limit

    def adjust_printlength(self):
        if self.tw_width <= 0:
            return
        elif self.could_not_get_terminal_window:
            return
        else:
            current_length = len(self.prefix) + self.length + \
                self.decimals + len(self.suffix) + 10
            if current_length > self.tw_width:
                diff = current_length - self.tw_width
                if diff < self.length:
                    self.length -= diff
                else:  # remove suffix
                    current_length = current_length - len(self.suffix)
                    diff = current_length - self.tw_width
                    if diff <= 0:
                        self.suffix = ""
                    elif diff < self.length:
                        self.suffix = ""
                        self.length -= diff
                    else:  # remove prefix
                        current_length = current_length - len(self.prefix)
                        diff = current_length - self.tw_width
                        if diff <= 0:
                            self.suffix = ""
                            self.prefix = ""
                        elif diff < self.length:
                            self.suffix = ""
                            self.prefix = ""
                            self.length -= diff
                        else:  # display only percent
                            self.display_only_percent = True

    def progress(self, iteration):
        """
        Progresses the progress bar to the next step.

        Args:
            iteration (float): The current iteration. For example, the 57th out of 100 steps, or 12.3s out of the total 60s.
        """
        if self.finished:
            return
        import sys
        import shutil

        if not self.could_not_get_terminal_window:
            self.tw_width, self.tw_height = shutil.get_terminal_size((0, 0))
            if self.tw_width + self.tw_height == 0:
                self.could_not_get_terminal_window = True
            else:
                self.adjust_printlength()

        capped_iteration = iteration if iteration <= self.total else self.total
        # Print New Line on Complete
        if iteration >= self.total:
            self.finished = True
            percent = ("{0:." + str(self.decimals) + "f}").format(100)
            filledLength = int(round(self.length))
            bar = self.fill * filledLength
            sys.stdout.flush()
            if self.display_only_percent:
                sys.stdout.write('\r%s' % (percent))
            else:
                sys.stdout.write('\r%s |%s| %s%% %s' %
                                 (self.prefix, bar, percent, self.suffix))
            print()
        elif self.over_time_limit():
            self.now = self.get_now()
            percent = ("{0:." + str(self.decimals) + "f}").format(100 *
                                                                  (capped_iteration / float(self.total)))
            filledLength = int(self.length * capped_iteration // self.total)
            bar = self.fill * filledLength + '-' * (self.length - filledLength)
            sys.stdout.flush()
            if self.display_only_percent:
                sys.stdout.write('\r%s' % (percent))
            else:
                sys.stdout.write('\r%s |%s| %s%% %s' %
                                 (self.prefix, bar, percent, self.suffix))
        else:
            return

    def __repr__(self):
        return "MgProgressbar"


def roundup(num, modulo_num):
    """
    Rounds up a number to the next integer multiple of another.

    Args:
        num (int): The number to round up.
        modulo_num (int): The number whose next integer multiple we want.

    Returns:
        int: The rounded-up number.
    """
    num, modulo_num = int(num), int(modulo_num)
    return num - (num % modulo_num) + modulo_num*((num % modulo_num) != 0)


def clamp(num, min_value, max_value):
    """
    Clamps a number between a minimum and maximum value.

    Args:
        num (float): The number to clamp.
        min_value (float): The minimum allowed value.
        max_value (float): The maximum allowed value.

    Returns:
        float: The clamped number.
    """
    return max(min(num, max_value), min_value)


def scale_num(val, in_low, in_high, out_low, out_high):
    """
    Scales a number linearly.

    Args:
        val (float): The value to be scaled.
        in_low (float): Minimum of input range.
        in_high (float): Maximum of input range.
        out_low (float): Minimum of output range.
        out_high (float): Maximum of output range.

    Returns:
        float: The scaled number.
    """

    return ((val - in_low) * (out_high - out_low)) / (in_high - in_low) + out_low


def scale_array(array, out_low, out_high):
    """
    Scales an array linearly.

    Args:
        array (arraylike): The array to be scaled.
        out_low (float): Minimum of output range.
        out_high (float): Maximum of output range.

    Returns:
        arraylike: The scaled array.
    """

    import numpy as np
    minimum, maximum = np.min(array), np.max(array)
    m = (out_high - out_low) / (maximum - minimum)
    b = out_low - m * minimum
    return m * array + b


def get_frame_planecount(frame):
    """
    Gets the planecount (color channel count) of a video frame.

    Args:
        frame (numpy array): A frame extracted by `cv2.VideoCapture().read()`.

    Returns:
        int: The planecount of the input frame, 3 or 1.
    """

    import numpy as np
    return 3 if len(np.array(frame).shape) == 3 else 1


def frame2ms(frame, fps):
    """
    Converts frames to milliseconds.

    Args:
        frame (int): The index of the frame to be converted to milliseconds.
        fps (int): Frames per second.

    Returns:
        int: The rounded millisecond value of the input frame index.
    """

    return round(frame / fps * 1000)


class MgImage():
    """
    Class for handling images in the Musical Gestures Toolbox.
    """

    def __init__(self, filename):
        """
        Initializes the MgImage object.

        Args:
            filename (str): The path to the image file to load.
        """
        self.filename = filename
        import os
        self.of = os.path.splitext(self.filename)[0]
        self.fex = os.path.splitext(self.filename)[1]
    from musicalgestures._show import mg_show as show

    def __repr__(self):
        return f"MgImage('{self.filename}')"


class MgFigure():
    """
    Class for working with figures and plots within the Musical Gestures Toolbox.
    """

    def __init__(self, figure=None, figure_type=None, data=None, layers=None, image=None):
        """
        Initializes the MgFigure object.

        Args:
            figure (matplotlib.pyplot.figure, optional): The internal figure. Defaults to None.
            figure_type (str, optional): A keyword describing the type of the figure, such as "audio.spectrogram", "audio.tempogram", "audio.descriptors", "layers", etc. Defaults to None.
            data (dictionary, optional): The dictionary containing all the necessary variables, lists and (typically) NumPy arrays necessary to rebuild each subplot in the figure. Defaults to None.
            layers (list, optional): This is only relevant if the MgFigure instance is of "layers" type, which indicates that it is a composit of several MgFigures and/or MgImages. In this case the layers list should contain all the child instances (MgFigures, MgImages, or MgLists of these) which are included in this MgFigure and are displayed as subplots. Defaults to None.
            image (str, optional): Path to the image file (the rendered figure). Defaults to None.
        """
        self.figure = figure
        self.figure_type = figure_type
        self.data = data
        self.layers = layers
        self.image = image

    def __repr__(self):
        return f"MgFigure(figure_type='{self.figure_type}')"

    def show(self):
        """
        Shows the internal matplotlib.pyplot.figure.
        """
        return self.figure


def convert_to_avi(filename):
    """
    Converts a video to one with .avi extension using ffmpeg.

    Args:
        filename (str): Path to the input video file to convert.

    Outputs:
        `filename`.avi

    Returns:
        str: The path to the output '.avi' file.
    """

    import os
    of, fex = os.path.splitext(filename)
    if fex == '.avi':
        print(f'{filename} is already in avi container.')
        return filename
    outname = of + '.avi'
    cmds = ['ffmpeg', '-y', '-i', filename, "-c:v", "mjpeg",
            "-q:v", "3", "-c:a", "copy", outname]
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Converting to avi:')
    return outname


def convert_to_mp4(filename):
    """
    Converts a video to one with .mp4 extension using ffmpeg.

    Args:
        filename (str): Path to the input video file to convert.

    Outputs:
        `filename`.mp4

    Returns:
        str: The path to the output '.mp4' file.
    """

    import os
    of, fex = os.path.splitext(filename)
    if fex == '.mp4':
        print(f'{filename} is already in mp4 container.')
        return filename
    outname = of + '.mp4'
    cmds = ['ffmpeg', '-y', '-i', filename,
            "-q:v", "3", "-c:a", "copy", outname]
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Converting to mp4:')
    return outname


def cast_into_avi(filename):
    """
    *Experimental*
    Casts a video into and .avi container using ffmpeg. Much faster than `convert_to_avi`,
    but does not always work well with cv2 or built-in video players.

    Args:
        filename (str): Path to the input video file.

    Outputs:
        `filename`.avi

    Returns:
        str: The path to the output '.avi' file.
    """

    import os
    of = os.path.splitext(filename)[0]
    outname = of + '.avi'
    cmds = ['ffmpeg', '-y', '-i', filename, "-codec copy", outname]
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Casting to avi')
    return outname


def extract_subclip(filename, t1, t2, targetname=None):
    """
    Extracts a section of the video using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        t1 (float): The start of the section to extract in seconds.
        t2 (float): The end of the section to extract in seconds.
        targetname (str, optional): The name for the output file. If None, the name will be \<input name\>SUB\<start time in ms\>_\<end time in ms\>.\<file extension\>. Defaults to None.

    Outputs:
        The extracted section as a video.
    """

    import os
    import numpy as np
    name, ext = os.path.splitext(filename)
    length = get_length(filename)
    start, end = np.clip(t1, 0, length), np.clip(t2, 0, length)
    if start > end:
        end = length

    if not targetname:
        T1, T2 = [int(1000*t) for t in [start, end]]
        targetname = "%sSUB%d_%d.%s" % (name, T1, T2, ext)

    # avoiding ffmpeg glitch if format is not avi:
    if os.path.splitext(filename)[1] != '.avi':
        cmd = ['ffmpeg', "-y",
               "-ss", "%0.2f" % start,
               "-i", filename,
               "-t", "%0.2f" % (end-start),
               "-map", "0", targetname]
    else:
        cmd = ['ffmpeg', "-y",
               "-ss", "%0.2f" % start,
               "-i", filename,
               "-t", "%0.2f" % (end-start),
               "-map", "0", "-codec", "copy", targetname]

    ffmpeg_cmd(cmd, length, pb_prefix='Trimming:')


def rotate_video(filename, angle):
    """
    Rotates a video by an `angle` using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        angle (float): The angle (in degrees) specifying the amount of rotation. Positive values rotate clockwise.

    Outputs:
        `filename`_rot.<file extension>

    Returns:
        str: The path to the rotated video file.
    """

    import os
    import math
    of, fex = os.path.splitext(filename)
    if os.path.isfile(of + '_rot' + fex):
        os.remove(of + '_rot' + fex)

    cmds = ['ffmpeg', '-y', '-i', filename, "-vf",
            f"rotate={math.radians(angle)}", "-q:v", "3", "-c:a", "copy", of + '_rot' + fex]
    ffmpeg_cmd(cmds, get_length(filename),
               pb_prefix=f"Rotating video by {angle} degrees:")
    return of + '_rot', fex


def convert_to_grayscale(filename):
    """
    Converts a video to grayscale using ffmpeg.

    Args:
        filename (str): Path to the input video file.

    Outputs:
        `filename`_gray.<file extension>

    Returns:
        str: The path to the grayscale video file.
    """

    import os
    of, fex = os.path.splitext(filename)

    cmds = ['ffmpeg', '-y', '-i', filename, '-vf',
            'hue=s=0', "-q:v", "3", "-c:a", "copy", of + '_gray' + fex]
    ffmpeg_cmd(cmds, get_length(filename),
               pb_prefix='Converting to grayscale:')
    return of + '_gray', fex


def framediff_ffmpeg(filename, outname=None, color=True):
    """
    Renders a frame difference video from the input using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        outname (str, optional): The name of the output video. If None, the output name will be <input video>_framediff.<file extension>. Defaults to None.
        color (bool, optional): If False, the output will be grayscale. Defaults to True.

    Outputs:
        The frame difference video.

    Returns:
        str: Path to the output video.
    """

    import os
    of, fex = os.path.splitext(filename)

    if outname == None:
        outname = of + '_framediff' + fex
    if color == True:
        pixformat = 'gbrp'
    else:
        pixformat = 'gray'
    cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
           f'format={pixformat},tblend=all_mode=difference', '-q:v', '3', "-c:a", "copy", outname]
    ffmpeg_cmd(cmd, get_length(filename),
               pb_prefix='Rendering frame difference video:')
    return outname


def threshold_ffmpeg(filename, threshold=0.1, outname=None, binary=False):
    """
    Renders a pixel-thresholded video from the input using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        threshold (float, optional): The normalized pixel value to use as the threshold. Pixels below the threshold will turn black. Defaults to 0.1.
        outname (str, optional): The name of the output video. If None, the output name will be <input video>_thresh.<file extension>. Defaults to None.
        binary (bool, optional): If True, the pixels above the threshold will turn white. Defaults to False.

    Outputs:
        The thresholded video.

    Returns:
        str: Path to the output video.
    """

    import os
    import matplotlib
    of, fex = os.path.splitext(filename)

    if outname == None:
        outname = of + '_thresh' + fex

    width, height = get_widthheight(filename)

    thresh_color = matplotlib.colors.to_hex([threshold, threshold, threshold])
    thresh_color = '0x' + thresh_color[1:]

    if binary == False:
        cmd = ['ffmpeg', '-y', '-i', filename, '-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', '-f', 'lavfi',
               '-i', f'color=black,scale={width}:{height}', '-i', filename, '-lavfi', 'format=gbrp,threshold', '-q:v', '3', "-c:a", "copy", outname]
    else:
        cmd = ['ffmpeg', '-y', '-i', filename, '-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', '-f', 'lavfi',
               '-i', f'color=black,scale={width}:{height}', '-f', 'lavfi', '-i', f'color=white,scale={width}:{height}', '-lavfi', 'format=gray,threshold', '-q:v', '3', "-c:a", "copy", outname]

    ffmpeg_cmd(cmd, get_length(filename),
               pb_prefix='Rendering threshold video:')

    return outname


def motionvideo_ffmpeg(
        filename,
        color=True,
        filtertype='regular',
        threshold=0.05,
        blur='none',
        use_median=False,
        kernel_size=5,
        invert=False,
        outname=None):
    """
    Renders a motion video using ffmpeg. 

    Args:
        filename (str): Path to the input video file.
        color (bool, optional): If False the input is converted to grayscale at the start of the process. This can significantly reduce render time. Defaults to True.
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        use_median (bool, optional): If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
        kernel_size (int, optional): Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
        invert (bool, optional): If True, inverts colors of the motion video. Defaults to False.
        outname (str, optional): If None the name of the output video will be <file name>_motion.<file extension>. Defaults to None.

    Outputs:
        The motion video.

    Returns:
        str: Path to the output video.
    """

    import os
    import matplotlib
    of, fex = os.path.splitext(filename)

    cmd = ['ffmpeg', '-y', '-i', filename]
    cmd_filter = ''

    if outname == None:
        outname = of + '_motion' + fex

    cmd_end = ['-q:v', '3', "-c:a", "copy", outname]

    # set color mode
    if color == True:
        pixformat = 'gbrp'
    else:
        pixformat = 'gray'
    cmd_filter += f'format={pixformat},'

    # set blur
    if blur.lower() == 'average':
        cmd_filter += 'avgblur=sizeX=10:sizeY=10,'

    # set frame difference
    if filtertype.lower() == 'regular':
        cmd_filter += 'tblend=all_mode=difference[diff],'
    else:
        cmd_filter += 'tblend=all_mode=difference,'

    width, height = get_widthheight(filename)

    thresh_color = matplotlib.colors.to_hex([threshold, threshold, threshold])
    thresh_color = '0x' + thresh_color[1:]

    # set threshold
    if filtertype.lower() == 'regular':
        cmd += ['-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}',
                '-f', 'lavfi', '-i', f'color=black,scale={width}:{height}']
        cmd_filter += '[0:v][1][2][diff]threshold,'
    elif filtertype.lower() == 'binary':
        cmd += ['-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', '-f', 'lavfi', '-i',
                f'color=black,scale={width}:{height}', '-f', 'lavfi', '-i', f'color=white,scale={width}:{height}']
        cmd_filter += 'threshold,'
    elif filtertype.lower() == 'blob':
        # cmd_filter += 'erosion,' # erosion is always 3x3 so we will hack it with a median filter with percentile=0 which will pick minimum values
        cmd_filter += f'median=radius={kernel_size}:percentile=0,'

    # set median
    if use_median and filtertype.lower() != 'blob':  # makes no sense to median-filter the eroded video
        cmd_filter += f'median=radius={kernel_size},'

    # set invert
    if invert:
        cmd_filter += 'negate'
    else:
        # remove last comma after previous filter
        cmd_filter = cmd_filter[: -1]

    cmd += ['-filter_complex', cmd_filter] + cmd_end

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Rendering motion video:')

    return outname


def motiongrams_ffmpeg(
        filename,
        color=True,
        filtertype='regular',
        threshold=0.05,
        blur='none',
        use_median=False,
        kernel_size=5,
        invert=False):
    """
    Renders horizontal and vertical motiongrams using ffmpeg. 

    Args:
        filename (str): Path to the input video file.
        color (bool, optional): If False the input is converted to grayscale at the start of the process. This can significantly reduce render time. Defaults to True.
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        use_median (bool, optional): If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
        kernel_size (int, optional): Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
        invert (bool, optional): If True, inverts colors of the motiongrams. Defaults to False.

    Outputs:
        `filename`_vgx.png
        `filename`_vgy.png

    Returns:
        str: Path to the output horizontal motiongram (_mgx).
        str: Path to the output vertical motiongram (_mgy).
    """

    import os
    import matplotlib
    of, fex = os.path.splitext(filename)

    cmd = ['ffmpeg', '-y', '-i', filename]
    cmd_filter = ''

    width, height = get_widthheight(filename)
    framecount = get_framecount(filename)

    cmd_end_y = ['-aspect', f'{framecount}:{height}',
                 '-frames', '1', of+'_mgy_ffmpeg.png']
    cmd_end_x = ['-aspect', f'{width}:{framecount}',
                 '-frames', '1', of+'_mgx_ffmpeg.png']

    # set color mode
    if color == True:
        pixformat = 'gbrp'
    else:
        pixformat = 'gray'
    cmd_filter += f'format={pixformat},'

    # set blur
    if blur.lower() == 'average':
        cmd_filter += 'avgblur=sizeX=10:sizeY=10,'

    # set frame difference
    if filtertype.lower() == 'regular':
        cmd_filter += 'tblend=all_mode=difference[diff],'
    else:
        cmd_filter += 'tblend=all_mode=difference,'

    thresh_color = matplotlib.colors.to_hex([threshold, threshold, threshold])
    thresh_color = '0x' + thresh_color[1:]

    # set threshold
    if filtertype.lower() == 'regular':
        cmd += ['-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}',
                '-f', 'lavfi', '-i', f'color=black,scale={width}:{height}']
        cmd_filter += '[0:v][1][2][diff]threshold,'
    elif filtertype.lower() == 'binary':
        cmd += ['-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', '-f', 'lavfi', '-i',
                f'color=black,scale={width}:{height}', '-f', 'lavfi', '-i', f'color=white,scale={width}:{height}']
        cmd_filter += 'threshold,'
    elif filtertype.lower() == 'blob':
        # cmd_filter += 'erosion,' # erosion is always 3x3 so we will hack it with a median filter with percentile=0 which will pick minimum values
        cmd_filter += f'median=radius={kernel_size}:percentile=0,'

    # set median
    if use_median and filtertype.lower() != 'blob':  # makes no sense to median-filter the eroded video
        cmd_filter += f'median=radius={kernel_size},'

    # set invert
    if invert:
        cmd_filter += 'negate,'

    cmd_filter_y = cmd_filter + \
        f'scale=1:{height}:sws_flags=area,normalize,tile={framecount}x1'
    cmd_filter_x = cmd_filter + \
        f'scale={width}:1:sws_flags=area,normalize,tile=1x{framecount}'

    cmd_y = cmd + ['-filter_complex', cmd_filter_y] + cmd_end_y
    cmd_x = cmd + ['-filter_complex', cmd_filter_x] + cmd_end_x

    ffmpeg_cmd(cmd_x, get_length(filename),
               pb_prefix='Rendering horizontal motiongram:', stream=False)
    ffmpeg_cmd(cmd_y, get_length(filename),
               pb_prefix='Rendering vertical motiongram:', stream=False)

    return of+'_mgx.png', of+'_mgy.png'


def crop_ffmpeg(filename, w, h, x, y, outname=None):
    """
    Crops a video using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        w (int): The desired width.
        h (int): The desired height.
        x (int): The horizontal coordinate of the top left pixel of the cropping rectangle.
        y (int): The vertical coordinate of the top left pixel of the cropping rectangle.
        outname (str, optional): The name of the output video. If None, the output name will be <input video>_crop.<file extension>. Defaults to None.

    Outputs:
        The cropped video.

    Returns:
        str: Path to the output video.
    """

    import os

    of, fex = os.path.splitext(filename)

    if outname == None:
        outname = of + '_crop' + fex

    cmd = ['ffmpeg', '-y', '-i', filename, '-vf',
           f'crop={w}:{h}:{x}:{y}', '-q:v', '3', "-c:a", "copy", outname]

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Rendering cropped video:')

    return outname


def extract_wav(filename):
    """
    Extracts audio from video into a .wav file via ffmpeg.

    Args:
        filename (str): Path to the video file from which the audio track shall be extracted.

    Outputs:
        `filename`.wav

    Returns:
        str: The path to the output audio file.
    """

    import os
    of, fex = os.path.splitext(filename)
    if fex in ['.wav', '.WAV']:
        print(f'{filename} is already in .wav container.')
        return filename
    outname = of + '.wav'
    cmds = ' '.join(['ffmpeg', '-y', '-i', wrap_str(filename), "-acodec",
                     "pcm_s16le", wrap_str(outname)])
    os.system(cmds)
    return outname


def get_length(filename):
    """
    Gets the length (in seconds) of a video using moviepy.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        float: The length of the input video file in seconds.
    """

    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(filename)
    duration = float(clip.duration)
    clip.close()
    return duration


def get_framecount(filename):
    """
    Returns the number of frames in a video using moviepy.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        int: The number of frames in the input video file.
    """

    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(filename)
    framecount = int(round(float(clip.duration) * float(clip.fps)))
    clip.close()
    return framecount


def get_fps(filename):
    """
    Gets the FPS (frames per second) value of a video using moviepy.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        float: The FPS value of the input video file.
    """

    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(filename)
    fps = float(clip.fps)
    clip.close()
    return fps


# def get_widthheight(filename):
#     """
#     Gets the width and height of a video using moviepy.

#     Args:
#         filename (str): Path to the video file to measure.

#     Returns:
#         int: The width of the input video file.
#         int: The height of the input video file.
#     """

#     from moviepy.editor import VideoFileClip
#     clip = VideoFileClip(filename)
#     (width, height) = clip.size
#     clip.close()
#     return width, height

class FFprobeError(Exception):
    def __init__(self, message):
        self.message = message


class NoVideoStreamError(FFprobeError):
    pass


def get_widthheight(filename):
    """
    Gets the width and height of a video using FFprobe.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        int: The width of the input video file.
        int: The height of the input video file.
    """
    import subprocess
    command = ['ffprobe', filename]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    try:
        out, err = process.communicate(timeout=10)
    except TimeoutExpired:
        process.kill()
        out, err = process.communicate()

    if err:
        raise FFprobeError(err)
    else:
        if out.splitlines()[-1].find("No such file or directory") != -1:
            raise FileNotFoundError(out.splitlines()[-1])
        else:
            out_array = out.splitlines()
            video_stream = None
            at_line = -1
            while video_stream == None:
                video_stream = out_array[at_line] if out_array[at_line].find(
                    "Video:") != -1 else None
                at_line -= 1
                if at_line < -len(out_array):
                    raise NoVideoStreamError(
                        "No video stream found. (Is this an audio file?)")
            width = int(video_stream.split('x')[-2].split(' ')[-1])
            height = int(video_stream.split(
                'x')[-1].split(',')[0].split(' ')[0])
            return width, height


def get_first_frame_as_image(filename, outname=None, pict_format='.png'):
    """
    Extracts the first frame of a video and saves it as an image using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        outname (str, optional): The name for the output image. If None, the output name will be <input name>`pict_format`. Defaults to None.
        pict_format (str, optional): The format to use for the output image. Defaults to '.png'.

    Outputs:
        The first frame of the input video as an image file.

    Returns:
        str: Path to the output image file.
    """

    import os
    of = os.path.splitext(filename)[0]

    if outname == None:
        outname = of + pict_format

    cmd = ' '.join(['ffmpeg', '-y', '-i', wrap_str(filename),
                    '-frames', '1', wrap_str(outname)])

    os.system(cmd)

    return outname


def get_screen_resolution_scaled():
    """
    Gets the scaled screen resolution. Respects display scaling on high DPI displays.

    Returns:
        int: The scaled width of the screen.
        int: The scaled height of the screen.
    """

    import tkinter as tk

    root = tk.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    width, height = [int(elem) for elem in geometry.split('+')[0].split('x')]
    root.destroy()
    return width, height


def get_screen_video_ratio(filename):
    """
    Gets the screen-to-video ratio. Useful to fit windows on the screen.

    Args:
        filename (str): Path to the input video file.

    Returns:
        int: The smallest ratio (ie. the one to use for scaling the window to fit the screen).
    """

    screen_width, screen_height = get_screen_resolution_scaled()
    video_width, video_height = get_widthheight(filename)

    ratio_x, ratio_y = clamp(screen_width / video_width,
                             0, 1), clamp(screen_height / video_height, 0, 1)

    smallest_ratio = sorted([ratio_x, ratio_y])[0]

    if smallest_ratio < 1:
        smallest_ratio *= 0.9

    return smallest_ratio


def has_audio(filename):
    """
    Checks if video has audio track using moviepy.

    Args:
        filename (str): Path to the video file to check.

    Returns:
        bool: True if `filename` has an audio track, False otherwise.
    """

    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(filename)
    if clip.audio == None:
        clip.close()
        return False
    else:
        clip.close()
        return True


def audio_dilate(filename, dilation_ratio=1):
    """
    Time-stretches or -shrinks (dilates) an audio file using ffmpeg.

    Args:
        filename (str): Path to the audio file to dilate.
        dilation_ratio (float, optional): The source file's length divided by the resulting file's length. Defaults to 1.

    Outputs:
        <file name>_dilated.<file extension>

    Returns:
        str: The path to the output audio file.
    """

    import os
    of, fex = os.path.splitext(filename)
    outname = of + '_dilated' + fex
    cmds = ' '.join(['ffmpeg', '-y', '-i', wrap_str(filename), '-codec:a', 'pcm_s16le',
                     '-filter:a', 'atempo=' + str(dilation_ratio), wrap_str(outname)])
    os.system(cmds)
    return outname


def embed_audio_in_video(source_audio, destination_video, dilation_ratio=1):
    """
    Embeds an audio file as the audio channel of a video file using ffmpeg.

    Args:
        source_audio (str): Path to the audio file to embed.
        destination_video (str): Path to the video file to embed the audio file in.
        dilation_ratio (float, optional): The source file's length divided by the resulting file's length. Defaults to 1.

    Outputs:
        `destination_video` with the embedded audio file.
    """

    import os
    of, fex = os.path.splitext(destination_video)

    # dilate audio file if necessary (ie. when skipping)
    if dilation_ratio != 1:
        audio_to_embed = audio_dilate(
            source_audio, dilation_ratio)  # creates '_dilated.wav'
        dilated = True
    else:
        audio_to_embed = source_audio
        dilated = False

    # embed audio in video
    outname = of + '_w_audio' + fex
    cmds = ' '.join(['ffmpeg', '-y', '-i', wrap_str(destination_video), '-i', wrap_str(audio_to_embed), '-c:v',
                     'copy', '-map', '0:v:0', '-map', '1:a:0', '-shortest', wrap_str(outname)])
    os.system(cmds)  # creates '_w_audio.avi'

    # cleanup:
    # if we needed to create an additional (dilated) audio file, delete it
    if dilated:
        os.remove(audio_to_embed)
    # replace (silent) destination_video with the one with the embedded audio
    os.remove(destination_video)
    os.rename(outname, destination_video)


def ffmpeg_cmd(command, total_time, pb_prefix='Progress', print_cmd=False, stream=True):
    """
    Run an ffmpeg command in a subprocess and show progress using an MgProgressbar.

    Args:
        command (list): The ffmpeg command to execute as a list. Eg. ['ffmpeg', '-y', '-i', 'myVid.mp4', 'myVid.mov']
        total_time (float): The length of the output. Needed mainly for the progress bar.
        pb_prefix (str, optional): The prefix for the progress bar. Defaults to 'Progress'.
        print_cmd (bool, optional): Whether to print the full ffmpeg command to the console before executing it. Good for debugging. Defaults to False.
        stream (bool, optional): Whether to have a continuous output stream or just (the last) one. Defaults to True (continuous stream).

    Raises:
        KeyboardInterrupt: If the user stops the process.
    """
    import subprocess
    pb = MgProgressbar(total=total_time, prefix=pb_prefix)

    if print_cmd:
        print()
        if type(command) == list:
            print(' '.join(command))
        else:
            print(command)
        print()

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    try:
        while True:
            if stream:
                out = process.stdout.readline()
            else:
                out = process.stdout.read()
            if out == '':
                process.wait()
                break
            elif out.startswith('frame='):
                out_list = out.split()
                time_ind = [elem.startswith('time=')
                            for elem in out_list].index(True)
                time_str = out_list[time_ind][5:]
                time_sec = str2sec(time_str)
                pb.progress(time_sec)

        pb.progress(total_time)

    except KeyboardInterrupt:
        try:
            process.terminate()
        except OSError:
            pass
        process.wait()
        raise KeyboardInterrupt


def ffmpeg_cmd_async(command, total_time, pb_prefix='Progress', print_cmd=False, stream=True):
    """
    Run an ffmpeg command in an asynchronous subprocess and show progress using an MgProgressbar.

    Args:
        command (list): The ffmpeg command to execute as a list. Eg. ['ffmpeg', '-y', '-i', 'myVid.mp4', 'myVid.mov']
        total_time (float): The length of the output. Needed mainly for the progress bar.
        pb_prefix (str, optional): The prefix for the progress bar. Defaults to 'Progress'.
        print_cmd (bool, optional): Whether to print the full ffmpeg command to the console before executing it. Good for debugging. Defaults to False.
        stream (bool, optional): Whether to have a continuous output stream or just (the last) one. Defaults to True (continuous stream).

    Raises:
        KeyboardInterrupt: If the user stops the process.
    """
    import asyncio

    pb = MgProgressbar(total=total_time, prefix=pb_prefix)

    if print_cmd:
        print()
        if type(command) == list:
            print(' '.join(command))
        else:
            print(command)
        print()

    async def run_cmd(command, pb):

        process = await asyncio.create_subprocess_shell(' '.join(command), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)

        try:
            while True:
                out = await process.stdout.read()
                if out != None:
                    out = out.decode()
                    if out == '':
                        await process.wait()
                        break
                    elif out.startswith('frame='):
                        out_list = out.split()
                        time_ind = [elem.startswith('time=')
                                    for elem in out_list].index(True)
                        time_str = out_list[time_ind][5:]
                        time_sec = str2sec(time_str)
                        pb.progress(time_sec)

            pb.progress(total_time)

        except KeyboardInterrupt:
            try:
                await process.terminate()
            except OSError:
                pass
            await process.wait()
            raise KeyboardInterrupt

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # if cleanup: 'RuntimeError: There is no current event loop..'
        loop = None

    if loop and loop.is_running():
        tsk = loop.create_task(run_cmd(command, pb))
    else:
        asyncio.run(run_cmd(command, pb))


def str2sec(time_string):
    """
    Converts a time code string into seconds.

    Args:
        time_string (str): The time code to convert. Eg. '01:33:42'.

    Returns:
        float: The time code converted to seconds.
    """
    elems = [float(elem) for elem in time_string.split(':')]
    return elems[0]*3600 + elems[1]*60 + elems[2]


def wrap_str(string, matchers=[" ", "(", ")"]):
    """
    Wraps a string in double quotes if it contains any of `matchers` - by default: space or parentheses.
    Useful when working with shell commands.


    Args:
        string (str): The string to inspect.
        matchers (list, optional): The list of characters to look for in the string. Defaults to [" ", "(", ")"].

    Returns:
        str: The (wrapped) string.
    """

    matchers = [" ", "(", ")"]

    if any(True for char in string if char in matchers) and '"' not in [string[0], string[-1]]:
        return '"' + string + '"'
    else:
        return string


def unwrap_str(string):
    """
    Unwraps a string from double quotes.

    Args:
        string (str): The string to inspect.

    Returns:
        str: The (unwrapped) string.
    """
    if '"' in [string[0], string[-1]]:
        return string[1:-1]
    else:
        return string

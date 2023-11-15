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
            _length_before = self.length
            current_length = len(self.prefix) + self.length + \
                self.decimals + len(self.suffix) + 10

            # if the length of printed line is longer than the terminal window's width
            if current_length > self.tw_width:
                diff = current_length - self.tw_width

                # if the difference is shorter than the progress bar length
                if diff < self.length:
                    self.length -= diff  # shorten the progress bar

                # if the difference is at least as long as the progress bar or longer
                else:  # remove suffix
                    current_length = current_length - \
                        len(self.suffix)  # remove suffix
                    diff = current_length - self.tw_width  # recalculate difference

                    # if the terminal width is long enough without suffix
                    if diff <= 0:
                        self.suffix = ""  # just remove suffix

                    # the terminal window is too short even without suffix
                    # remove suffix and test again
                    else:
                        self.suffix = ""

                        # --- SUFFIX IS REMOVED ---

                        # if the difference is shorter than the progress bar
                        if diff < self.length:
                            self.length -= diff  # shorten progress bar

                        # if the difference is longer than the progress bar, remove prefix
                        else:  # remove prefix
                            current_length = current_length - len(self.prefix)
                            diff = current_length - self.tw_width

                            # if the terminal width is long enough without prefix
                            if diff <= 0:
                                self.prefix = ""  # just remove prefix

                            # the terminal window is too short even without prefix (and suffix)
                            # remove prefix and test again
                            else:
                                self.prefix = ""

                                # --- PREFFIX IS REMOVED ---

                                # if the difference is shorter than the progress bar
                                if diff < self.length:
                                    self.length -= diff  # shorten progress bar

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
                self.adjust_printlength()  # this line cannot be tested :'(

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


def generate_outfilename(requested_name):
    """Returns a unique filepath to avoid overwriting existing files. Increments requested 
    filename if necessary by appending an integer, like "_0" or "_1", etc to the file name.

    Args:
        requested_name (str): Requested file name as path string.

    Returns:
        str: If file at requested_name is not present, then requested_name, else an incremented filename.
    """
    import os
    requested_name = os.path.abspath(requested_name).replace('\\', '/')
    req_of, req_fex = os.path.splitext(requested_name)
    req_of = req_of.replace('\\', '/')
    req_folder = os.path.dirname(requested_name).replace('\\', '/')
    req_of_base = os.path.basename(req_of)
    req_file_base = os.path.basename(requested_name)
    out_increment = 0
    files_in_folder = os.listdir(req_folder)
    # if the target folder is empty, return the requested path
    if len(files_in_folder) == 0:
        return requested_name
    # filter files with same ext
    files_w_same_ext = list(filter(lambda x: os.path.splitext(x)[
                            1] == req_fex, files_in_folder))
    # if there are no files with the same ext
    if len(files_w_same_ext) == 0:
        return requested_name
    # filter for files with same start and ext
    files_w_same_start_ext = list(
        filter(lambda x: x.startswith(req_of_base), files_w_same_ext))
    # if there are no files with the same start and ext
    if len(files_w_same_start_ext) == 0:
        return requested_name
    # check if requested file is already present
    present = None
    try:
        ind = files_w_same_start_ext.index(req_file_base)
        present = True
    except ValueError:
        present = False
    # if requested file is not present
    if not present:
        return requested_name
    # if the original filename is already taken, check if there are incremented filenames
    files_w_increment = list(filter(lambda x: x.startswith(
        req_of_base+"_"), files_w_same_start_ext))
    # if there are no files with increments
    if len(files_w_increment) == 0:
        return f'{req_of}_0{req_fex}'
    # parse increments, discard the ones that are invalid, increment highest
    for file in files_w_increment:
        _of = os.path.splitext(file)[0]
        _only_incr = _of[len(req_of_base)+1:]
        try:
            found_incr = int(_only_incr)
            found_incr = max(0, found_incr)  # clip at 0
            out_increment = max(out_increment, found_incr+1)
        except ValueError:  # if cannot be converted to int
            pass
    # return incremented filename
    return f'{req_of}_{out_increment}{req_fex}'


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


class WrongContainer(Exception):
    def __init__(self, message):
        self.message = message


def pass_if_containers_match(file_1, file_2):
    """Checks if file extensions match between two files. If they do it passes, is they don't it raises WrongContainer exception.

    Args:
        file_1 (str): First file in comparison.
        file_2 (str): Second file in comparison.

    Raises:
        WrongContainer: If file extensions (containers) mismatch.
    """
    import os
    fex_1 = os.path.splitext(file_1)[1].lower()
    fex_2 = os.path.splitext(file_2)[1]. lower()
    if fex_1 != fex_2:
        raise WrongContainer(
            f"Container mismatch: {fex_1} vs {fex_2}; between {file_1} and {file_2}.")


def pass_if_container_is(container, file):
    """Checks if a file's extension matches a desired one. Passes if so, raises WrongContainer if not.

    Args:
        container (str): The container to match.
        file (str): Path to the file to inspect.

    Raises:
        WrongContainer: If the file extension (container) matches the desired one.
    """
    import os
    if os.path.splitext(file)[1].lower() != container.lower():
        raise WrongContainer(
            f"Container should be {container.lower()}, but it is {os.path.splitext(file)[1].lower()} in file {file}.")


def convert(filename, target_name, overwrite=False):
    """
    Converts a video to another format/container using ffmpeg.

    Args:
        filename (str): Path to the input video file to convert.
        target_name (str): Target filename as path.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: The path to the output file.
    """

    import os
    of, fex = os.path.splitext(filename)
    target_of, target_fex = os.path.splitext(target_name)
    if fex.lower() == target_fex.lower():
        print(f'{filename} is already in {fex} container.')
        return filename
    if not overwrite:
        target_name = generate_outfilename(target_name)
    cmds = ['ffmpeg', '-y', '-i', filename,
            "-q:v", "3", target_name]
    ffmpeg_cmd(cmds, get_length(filename),
               pb_prefix=f'Converting to {target_fex}:')
    return target_name


def convert_to_avi(filename, target_name=None, overwrite=False):
    """
    Converts a video to one with .avi extension using ffmpeg.

    Args:
        filename (str): Path to the input video file to convert.
        target_name (str, optional): Target filename as path. Defaults to None (which assumes that the input filename should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: The path to the output '.avi' file.
    """

    import os
    of, fex = os.path.splitext(filename)
    if fex.lower() == '.avi':
        print(f'{filename} is already in avi container.')
        return filename
    if not target_name:
        target_name = of + '.avi'
    if not overwrite:
        target_name = generate_outfilename(target_name)
    pass_if_container_is(".avi", target_name)
    cmds = ['ffmpeg', '-y', '-i', filename, "-c:v", "mjpeg",
            "-q:v", "3", "-c:a", "copy", target_name]
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Converting to avi:')
    return target_name


def convert_to_mp4(filename, target_name=None, overwrite=False):
    """
    Converts a video to one with .mp4 extension using ffmpeg.

    Args:
        filename (str): Path to the input video file to convert.
        target_name (str, optional): Target filename as path. Defaults to None (which assumes that the input filename should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: The path to the output '.mp4' file.
    """

    import os
    of, fex = os.path.splitext(filename)
    if fex.lower() == '.mp4':
        print(f'{filename} is already in mp4 container.')
        return filename
    if not target_name:
        target_name = of + '.mp4'
    if not overwrite:
        target_name = generate_outfilename(target_name)
    pass_if_container_is(".mp4", target_name)
    cmds = ['ffmpeg', '-y', '-i', filename,
            "-q:v", "3", target_name]
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Converting to mp4:')
    return target_name


def convert_to_webm(filename, target_name=None, overwrite=False):
    """
    Converts a video to one with .webm extension using ffmpeg.

    Args:
        filename (str): Path to the input video file to convert.
        target_name (str, optional): Target filename as path. Defaults to None (which assumes that the input filename should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: The path to the output '.webm' file.
    """

    import os
    of, fex = os.path.splitext(filename)
    if fex.lower() == '.webm':
        print(f'{filename} is already in webm container.')
        return filename
    if not target_name:
        target_name = of + '.webm'
    if not overwrite:
        target_name = generate_outfilename(target_name)
    pass_if_container_is(".webm", target_name)
    cmds = ['ffmpeg', '-y', '-i', filename,
            "-q:v", "3", target_name]
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Converting to webm:')
    return target_name


def cast_into_avi(filename, target_name=None, overwrite=False):
    """
    *Experimental*
    Casts a video into and .avi container using ffmpeg. Much faster than `convert_to_avi`,
    but does not always work well with cv2 or built-in video players.

    Args:
        filename (str): Path to the input video file.
        target_name (str, optional): Target filename as path. Defaults to None (which assumes that the input filename should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: The path to the output '.avi' file.
    """

    import os
    of = os.path.splitext(filename)[0]
    if not target_name:
        target_name = of + '.avi'
    if not overwrite:
        target_name = generate_outfilename(target_name)
    pass_if_container_is(".avi", target_name)
    cmds = ['ffmpeg', '-y', '-i', filename, "-codec", "copy", target_name]
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Casting to avi')
    return target_name


def extract_subclip(filename, t1, t2, target_name=None, overwrite=False):
    """
    Extracts a section of the video using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        t1 (float): The start of the section to extract in seconds.
        t2 (float): The end of the section to extract in seconds.
        target_name (str, optional): The name for the output file. If None, the name will be \<input name\>SUB\<start time in ms\>_\<end time in ms\>.\<file extension\>. Defaults to None.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the extracted section as a video.
    """

    import os
    import numpy as np
    name, ext = os.path.splitext(filename)
    length = get_length(filename)
    start, end = np.clip(t1, 0, length), np.clip(t2, 0, length)
    if start > end:
        # end = length
        start, end = end, start

    if not target_name:
        T1, T2 = [int(1000*t) for t in [start, end]]
        target_name = "%sSUB%d_%d.%s" % (name, T1, T2, ext)

    if not overwrite:
        target_name = generate_outfilename(target_name)

    pass_if_containers_match(filename, target_name)

    # avoiding ffmpeg glitch if format is not avi:
    if os.path.splitext(filename)[1] != '.avi':
        cmd = ['ffmpeg', "-y",
               "-ss", "%0.2f" % start,
               "-i", filename,
               "-t", "%0.2f" % (end-start),
               "-max_muxing_queue_size", "9999",
               "-map", "0", target_name]
    else:
        cmd = ['ffmpeg', "-y",
               "-ss", "%0.2f" % start,
               "-i", filename,
               "-t", "%0.2f" % (end-start),
               "-max_muxing_queue_size", "9999",
               "-map", "0", "-codec", "copy", target_name]

    ffmpeg_cmd(cmd, length, pb_prefix='Trimming:')
    return target_name


def rotate_video(filename, angle, target_name=None, overwrite=False):
    """
    Rotates a video by an `angle` using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        angle (float): The angle (in degrees) specifying the amount of rotation. Positive values rotate clockwise.
        target_name (str, optional): Target filename as path. Defaults to None (which assumes that the input filename with the suffix "_rot" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: The path to the rotated video file.
    """

    import os
    import math
    import numpy as np
    of, fex = os.path.splitext(filename)

    if not target_name:
        target_name = of + '_rot' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    pass_if_containers_match(filename, target_name)

    if np.abs(angle) == 90 or np.abs(angle) == 180:
        # Rotate video without encoding for faster computation
        cmds = ['ffmpeg', '-y', '-i', filename, 
                '-metadata:s:v:0', f'rotate={angle}', '-codec', 'copy', target_name]
    else:
        # Rotate video with encoding
        cmds = ['ffmpeg', '-y', '-i', filename, "-vf", 
                f"rotate={math.radians(angle)}", "-q:v", "3", "-c:a", "copy", target_name]
    ffmpeg_cmd(cmds, get_length(filename),
               pb_prefix=f"Rotating video by {angle} degrees:")
    return target_name


def convert_to_grayscale(filename, target_name=None, overwrite=False):
    """
    Converts a video to grayscale using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        target_name (str, optional): Target filename as path. Defaults to None (which assumes that the input filename with the suffix "_gray" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: The path to the grayscale video file.
    """

    import os
    of, fex = os.path.splitext(filename)

    if not target_name:
        target_name = of + '_gray' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    pass_if_containers_match(filename, target_name)

    cmds = ['ffmpeg', '-y', '-i', filename, '-vf',
            'hue=s=0', "-q:v", "3", "-c:a", "copy", target_name]
    ffmpeg_cmd(cmds, get_length(filename),
               pb_prefix='Converting to grayscale:')
    return target_name

def transform_frame(out, height, width, color):
    import numpy as np

    # transform the bytes read into a numpy array
    frame =  np.frombuffer(out, dtype='uint8')
    try:
        if color:
            frame = frame.reshape((height,width,3)) # height, width, channels
        else:
            frame = frame.reshape((height,width)) # height, width
    except ValueError:
        pass
    
    return frame


def framediff_ffmpeg(filename, target_name=None, color=True, overwrite=False):
    """
    Renders a frame difference video from the input using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        target_name (str, optional): The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_framediff" should be used).
        color (bool, optional): If False, the output will be grayscale. Defaults to True.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the output video.
    """

    import os
    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '_framediff' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)
    pass_if_containers_match(filename, target_name)
    if color == True:
        pixformat = 'gbrp'
    else:
        pixformat = 'gray'
    cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
           f'format={pixformat},tblend=all_mode=difference', '-q:v', '3', "-c:a", "copy", target_name]
    ffmpeg_cmd(cmd, get_length(filename),
               pb_prefix='Rendering frame difference video:')
    return target_name


def threshold_ffmpeg(filename, threshold=0.1, target_name=None, binary=False, overwrite=False):
    """
    Renders a pixel-thresholded video from the input using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        threshold (float, optional): The normalized pixel value to use as the threshold. Pixels below the threshold will turn black. Defaults to 0.1.
        target_name (str, optional): The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_thresh" should be used).
        binary (bool, optional): If True, the pixels above the threshold will turn white. Defaults to False.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the output video.
    """

    import os
    import matplotlib
    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '_thresh' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    pass_if_containers_match(filename, target_name)

    width, height = get_widthheight(filename)

    thresh_color = matplotlib.colors.to_hex([threshold, threshold, threshold])
    thresh_color = '0x' + thresh_color[1:]

    if binary == False:
        cmd = ['ffmpeg', '-y', '-i', filename, '-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', '-f', 'lavfi',
               '-i', f'color=black,scale={width}:{height}', '-i', filename, '-lavfi', 'format=gbrp,threshold', '-q:v', '3', "-c:a", "copy", target_name]
    else:
        cmd = ['ffmpeg', '-y', '-i', filename, '-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', '-f', 'lavfi',
               '-i', f'color=black,scale={width}:{height}', '-f', 'lavfi', '-i', f'color=white,scale={width}:{height}', '-lavfi', 'format=gray,threshold', '-q:v', '3', "-c:a", "copy", target_name]

    ffmpeg_cmd(cmd, get_length(filename),
               pb_prefix='Rendering threshold video:')

    return target_name


def motionvideo_ffmpeg(
        filename,
        color=True,
        filtertype='regular',
        threshold=0.05,
        blur='none',
        use_median=False,
        kernel_size=5,
        invert=False,
        target_name=None,
        overwrite=False):
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
        target_name (str, optional): Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the output video.
    """

    import os
    from musicalgestures._filter import filter_frame_ffmpeg

    of, fex = os.path.splitext(filename)

    cmd = ['ffmpeg', '-y', '-i', filename]
    # cmd_filter = ''

    if target_name == None:
        target_name = of + '_motion' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    cmd, cmd_filter = filter_frame_ffmpeg(filename, cmd, color, blur, filtertype, threshold, kernel_size, use_median, invert=invert)
    # remove last comma after previous filter
    cmd_filter = cmd_filter[:-1]

    pass_if_containers_match(filename, target_name)
    cmd_end = ['-q:v', '3', "-c:a", "copy", target_name]
    cmd += ['-filter_complex', cmd_filter] + cmd_end

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Rendering motion video:')

    return target_name


def motiongrams_ffmpeg(
        filename,
        color=True,
        filtertype='regular',
        threshold=0.05,
        blur='none',
        use_median=False,
        kernel_size=5,
        invert=False,
        target_name_x=None,
        target_name_y=None,
        overwrite=False):
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
        target_name_x (str, optional): Target output name for the motiongram on the X axis. Defaults to None (which assumes that the input filename with the suffix "_mgx_ffmpeg" should be used).
        target_name_y (str, optional): Target output name for the motiongram on the Y axis. Defaults to None (which assumes that the input filename with the suffix "_mgy_ffmpeg" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the output horizontal motiongram (_mgx).
        str: Path to the output vertical motiongram (_mgy).
    """

    import os
    from musicalgestures._filter import filter_frame_ffmpeg

    of, fex = os.path.splitext(filename)

    if target_name_x == None:
        target_name_x = of+'_mgx_ffmpeg.png'
    if target_name_y == None:
        target_name_y = of+'_mgy_ffmpeg.png'
    if not overwrite:
        target_name_x = generate_outfilename(target_name_x)
        target_name_y = generate_outfilename(target_name_y)

    pass_if_container_is(".png", target_name_x)
    pass_if_container_is(".png", target_name_y)

    cmd = ['ffmpeg', '-y', '-i', filename]

    width, height = get_widthheight(filename)
    framecount = get_framecount(filename)

    cmd_end_y = ['-aspect', f'{framecount}:{height}', '-frames', '1', target_name_y]
    cmd_end_x = ['-aspect', f'{width}:{framecount}', '-frames', '1', target_name_x]

    cmd, cmd_filter = filter_frame_ffmpeg(filename, cmd, color, blur, filtertype, threshold, kernel_size, use_median, invert=invert)
    cmd_filter += 'atadenoise=s=129,' # apply adaptive temporal averaging denoiser every 129 frames

    cmd_filter_y = cmd_filter + \
        f'scale=1:{height},tile={framecount}x1,normalize=independence=0'
    # f'scale=1:{height}:sws_flags=area,normalize,tile={framecount}x1'
    cmd_filter_x = cmd_filter + \
        f'scale={width}:1,tile=1x{framecount},normalize=independence=0'
    # f'scale={width}:1:sws_flags=area,normalize,tile=1x{framecount}'

    cmd_y = cmd + ['-filter_complex', cmd_filter_y] + cmd_end_y
    cmd_x = cmd + ['-filter_complex', cmd_filter_x] + cmd_end_x

    ffmpeg_cmd(cmd_x, get_length(filename), pb_prefix='Rendering horizontal motiongram:', stream=False)
    ffmpeg_cmd(cmd_y, get_length(filename), pb_prefix='Rendering vertical motiongram:', stream=False)

    return target_name_x, target_name_y


def crop_ffmpeg(filename, w, h, x, y, target_name=None, overwrite=False):
    """
    Crops a video using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        w (int): The desired width.
        h (int): The desired height.
        x (int): The horizontal coordinate of the top left pixel of the cropping rectangle.
        y (int): The vertical coordinate of the top left pixel of the cropping rectangle.
        target_name (str, optional): The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_crop" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the output video.
    """

    import os

    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '_crop' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    pass_if_containers_match(filename, target_name)

    cmd = ['ffmpeg', '-y', '-i', filename, '-vf',
           f'crop={w}:{h}:{x}:{y}', '-q:v', '3', "-c:a", "copy", target_name]

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Rendering cropped video:')

    return target_name


def extract_wav(filename, target_name=None, overwrite=False):
    """
    Extracts audio from video into a .wav file via ffmpeg.

    Args:
        filename (str): Path to the video file from which the audio track shall be extracted.
        target_name (str, optional): The name of the output video. Defaults to None (which assumes that the input filename should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: The path to the output audio file.
    """

    import os
    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '.wav'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    pass_if_container_is(".wav", target_name)

    if fex in ['.wav', '.WAV']:
        print(f'{filename} is already in .wav container.')
        return filename

    cmds = ' '.join(['ffmpeg', '-loglevel', 'quiet', '-y', '-i', wrap_str(filename), "-acodec",
                     "pcm_s16le", wrap_str(target_name)])
    os.system(cmds)
    return target_name


class FFprobeError(Exception):
    def __init__(self, message):
        self.message = message


class NoStreamError(FFprobeError):
    pass


class NoDurationError(FFprobeError):
    pass

def ffprobe(filename):
    """
    Returns info about video/audio file using FFprobe.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        str: decoded FFprobe output (stdout) as one string.
    """
    import subprocess
    command = ['ffprobe', filename]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    try:
        out, err = process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        out, err = process.communicate()

    if err:
        raise FFprobeError(err)
    else:
        if out.splitlines()[-1].find("No such file or directory") != -1:
            raise FileNotFoundError(out.splitlines()[-1])
        else:
            return out

def get_metadata(filename):
    """
    Returns metadata about video/audio/format file using ffprobe.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        str: decoded ffprobe output (stdout) as a list containing three dictionaries for video, audio and format metadata.
    """

    import subprocess
    # Get streams and format information (https://ffmpeg.org/ffprobe.html)
    cmd = ["ffprobe", "-loglevel", "0", "-show_streams", "-show_format", filename]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    try:
        out, err = process.communicate(timeout=10)
        splitted = out.split('\n')
    except subprocess.TimeoutExpired:
        process.kill()
    out, err = process.communicate()
    splitted = out.split('\n')

    metadata = []
    # Retrieve information and export it in a dictionary
    for i, info in enumerate(splitted):
        if info == "[STREAM]" or info == "[SIDE_DATA]" or info == "[FORMAT]":        
            metadata.append(dict())
            i +=1
        elif info == "[/STREAM]" or info == "[/SIDE_DATA]" or info == "[/FORMAT]" or info == "":
            i +=1
        else:
            try:
                key, value = splitted[i].split('=')
                metadata[-1][key] = value
            except ValueError:
                key = splitted[i]
                metadata[-1][key] = ''

    if len(metadata) > 3: 
        # Merge video stream with side data dictionary
        metadata[0] = {**metadata[0], **metadata[1]}
        metadata.pop(1)

    return metadata

def get_widthheight(filename):
    """
    Gets the width and height of a video using FFprobe.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        int: The width of the input video file.
        int: The height of the input video file.
    """
    out = ffprobe(filename)
    out_array = out.splitlines()
    video_stream = None
    at_line = -1
    while video_stream == None:
        video_stream = out_array[at_line] if out_array[at_line].find("Video:") != -1 else None

        if out_array[at_line].find("displaymatrix:") != -1:
            import re
            rotation = [d for d in re.findall("\d+\.\d+", out_array[at_line])]

        at_line -= 1
        if at_line < -len(out_array):
            raise NoStreamError("No video stream found. (Is this a video file?)")

    try:
        if int(float(rotation[0])) == 90:
            # If the video has been rotated for 90°, we need to invert width and height
            width = int(video_stream.split('x')[-1].split(',')[0].split(' ')[0])
            height = int(video_stream.split('x')[-2].split(' ')[-1])
        else:
            width = int(video_stream.split('x')[-2].split(' ')[-1])
            height = int(video_stream.split('x')[-1].split(',')[0].split(' ')[0])
    except:
        width = int(video_stream.split('x')[-2].split(' ')[-1])
        height = int(video_stream.split('x')[-1].split(',')[0].split(' ')[0])

    return width, height


def has_audio(filename):
    """
    Checks if video has audio track using FFprobe.

    Args:
        filename (str): Path to the video file to check.

    Returns:
        bool: True if `filename` has an audio track, False otherwise.
    """
    out = ffprobe(filename)
    out_array = out.splitlines()
    audio_stream = None
    at_line = -1
    while audio_stream == None:
        audio_stream = out_array[at_line] if out_array[at_line].find(
            "Audio:") != -1 else None
        at_line -= 1
        if at_line < -len(out_array):
            break
    if audio_stream == None:
        return False
    else:
        return True


def get_length(filename):
    """
    Gets the length (in seconds) of a video using FFprobe.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        float: The length of the input video file in seconds.
    """
    out = ffprobe(filename)
    out_array = out.splitlines()
    duration = None
    at_line = -1
    while duration == None:
        duration = out_array[at_line] if out_array[at_line].find(
            "Duration:") != -1 else None
        at_line -= 1
        if at_line < -len(out_array):
            raise NoDurationError(
                "Could not get duration.")
    duration_array = duration.split(' ')
    time_string_index = duration_array.index("Duration:") + 1
    time_string = duration_array[time_string_index][:-1]
    elems = [float(elem) for elem in time_string.split(':')]
    return elems[0]*3600 + elems[1]*60 + elems[2]


def get_framecount(filename, fast=True):
    """
    Returns the number of frames in a video using FFprobe.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        int: The number of frames in the input video file.
    """
    import subprocess
    command_query_container = 'ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of default=nokey=1:noprint_wrappers=1'.split(
        ' ')
    command_query_container.append(filename)
    command_count = 'ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of default=nokey=1:noprint_wrappers=1'.split(
        ' ')
    command_count.append(filename)
    command = command_query_container if fast else command_count

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    try:
        out, err = process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        out, err = process.communicate()

    if err:
        raise FFprobeError(err)

    elif out:
        if out.splitlines()[-1].find("No such file or directory") != -1:
            raise FileNotFoundError(out.splitlines()[-1])
        elif out.startswith("N/A"):
            if fast:
                return get_framecount(filename, fast=False)
            else:
                raise FFprobeError(
                    "Could not count frames. (Is this a video file?) If you are working with audio file use MgAudio instead.")
        else:
            return int(out)

    else:
        if fast:
            return get_framecount(filename, fast=False)
        else:
            raise FFprobeError(
                "Could not count frames. (Is this a video file?). If you are working with audio file use MgAudio instead.")


def get_fps(filename):
    """
    Gets the FPS (frames per second) value of a video using FFprobe.

    Args:
        filename (str): Path to the video file to measure.

    Returns:
        float: The FPS value of the input video file.
    """
    out = ffprobe(filename)
    out_array = out.splitlines()
    video_stream = None
    at_line = -1
    while video_stream == None:
        video_stream = out_array[at_line] if out_array[at_line].find(
            "Video:") != -1 else None
        at_line -= 1
        if at_line < -len(out_array):
            raise NoStreamError(
                "No video stream found. (Is this a video file?)")
    video_stream_array = video_stream.split(',')
    fps = None
    at_chunk = -1
    while fps == None:
        fps = float(video_stream_array[at_chunk].split(
            ' ')[-2]) if video_stream_array[at_chunk].split(' ')[-1] == 'fps' else None
        at_chunk -= 1
        if at_chunk < -len(video_stream_array):
            raise FFprobeError("Could not fetch FPS.")
    return fps


def get_first_frame_as_image(filename, target_name=None, pict_format='.png', overwrite=False):
    """
    Extracts the first frame of a video and saves it as an image using ffmpeg.

    Args:
        filename (str): Path to the input video file.
        target_name (str, optional): The name for the output image. Defaults to None (which assumes that the input filename should be used).
        pict_format (str, optional): The format to use for the output image. Defaults to '.png'.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the output image file.
    """

    import os
    of = os.path.splitext(filename)[0]

    if target_name == None:
        target_name = of + pict_format
    if not overwrite:
        target_name = generate_outfilename(target_name)

    pass_if_container_is(pict_format, target_name)

    cmd = ' '.join(['ffmpeg', '-y', '-i', wrap_str(filename),
                    '-frames', '1', wrap_str(target_name)])

    os.system(cmd)

    return target_name


def get_box_video_ratio(filename, box_width=800, box_height=600):
    """
    Gets the box-to-video ratio between an arbitrarily defind box and the video dimensions. Useful to fit windows into a certain area.

    Args:
        filename (str): Path to the input video file.
        box_width (int, optional): The width of the box to fit the video into.
        box_height (int, optional): The height of the box to fit the video into.

    Returns:
        int: The smallest ratio (ie. the one to use for scaling the video window to fit into the box).
    """

    video_width, video_height = get_widthheight(filename)

    ratio_x, ratio_y = clamp(box_width / video_width,
                             0, 1), clamp(box_height / video_height, 0, 1)

    smallest_ratio = sorted([ratio_x, ratio_y])[0]

    if smallest_ratio < 1:
        smallest_ratio *= 0.9

    return smallest_ratio


def audio_dilate(filename, dilation_ratio=1, target_name=None, overwrite=False):
    """
    Time-stretches or -shrinks (dilates) an audio file using ffmpeg.

    Args:
        filename (str): Path to the audio file to dilate.
        dilation_ratio (float, optional): The source file's length divided by the resulting file's length. Defaults to 1.
        target_name (str, optional): The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_dilated" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: The path to the output audio file.
    """

    import os
    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '_dilated' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    pass_if_containers_match(filename, target_name)

    cmds = ' '.join(['ffmpeg', '-loglevel', 'quiet', '-y', '-i', wrap_str(filename), '-codec:a', 'pcm_s16le',
                     '-filter:a', 'atempo=' + str(dilation_ratio), wrap_str(target_name)])
    os.system(cmds)
    return target_name


def embed_audio_in_video(source_audio, destination_video, dilation_ratio=1):
    """
    Embeds an audio file as the audio channel of a video file using ffmpeg.

    Args:
        source_audio (str): Path to the audio file to embed.
        destination_video (str): Path to the video file to embed the audio file in.
        dilation_ratio (float, optional): The source file's length divided by the resulting file's length. Defaults to 1.
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
    cmds = ' '.join(['ffmpeg', '-loglevel', 'quiet', '-y', '-i', wrap_str(destination_video), '-i', wrap_str(audio_to_embed), '-c:v',
                     'copy', '-map', '0:v:0', '-map', '1:a:0', '-shortest', wrap_str(outname)])
    os.system(cmds)  # creates '_w_audio.avi'

    # cleanup:
    # if we needed to create an additional (dilated) audio file, delete it
    if dilated:
        os.remove(audio_to_embed)
    # replace (silent) destination_video with the one with the embedded audio
    os.remove(destination_video)
    os.rename(outname, destination_video)


class FFmpegError(Exception):
    def __init__(self, message):
        self.message = message


def ffmpeg_cmd(command, total_time, pb_prefix='Progress', print_cmd=False, stream=True, pipe=None):
    """
    Run an ffmpeg command in a subprocess and show progress using an MgProgressbar.

    Args:
        command (list): The ffmpeg command to execute as a list. Eg. ['ffmpeg', '-y', '-i', 'myVid.mp4', 'myVid.mov']
        total_time (float): The length of the output. Needed mainly for the progress bar.
        pb_prefix (str, optional): The prefix for the progress bar. Defaults to 'Progress'.
        print_cmd (bool, optional): Whether to print the full ffmpeg command to the console before executing it. Good for debugging. Defaults to False.
        stream (bool, optional): Whether to have a continuous output stream or just (the last) one. Defaults to True (continuous stream).
        pipe (str, optional): Whether to pipe video frames from FFmpeg to numpy array. Possible to read the video frame by frame with pipe='read' or to load video in memory with pipe='load'. Defaults to None.

    Raises:
        KeyboardInterrupt: If the user stops the process.
        FFmpegError: If the ffmpeg process was unsuccessful.
    """
    import subprocess
    pb = MgProgressbar(total=total_time, prefix=pb_prefix)

    # hide banner
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'quiet'] + command[1:]

    if print_cmd:
        if type(command) == list:
            print(' '.join(command))
        else:
            print(command)

    if pipe == 'read':
        # Define ffmpeg command and read frame by frame
        command = command + ['-f', 'image2pipe', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', '-']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=-1)
        return process

    elif pipe == 'load':
        # Define ffmpeg command and load all frames
        command = command + ['-f', 'image2pipe', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', '-']
        process = subprocess.run(command, stdout=subprocess.PIPE, bufsize=-1)
        return process

    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        returncode = None
        all_out = ''

        try:
            while True:
                if stream:
                    out = process.stdout.readline()
                else:
                    out = process.stdout.read()
                all_out += out

                if out == '':
                    process.wait()
                    returncode = process.returncode
                    break

                elif out.startswith('frame='):
                    try:
                        out_list = out.split()
                        time_ind = [elem.startswith('time=') for elem in out_list].index(True)
                        time_str = out_list[time_ind][5:]
                        time_sec = str2sec(time_str)
                        pb.progress(time_sec)
                    except ValueError:
                        # New version of FFmpeg outputs N/A values
                        pass

            if returncode in [None, 0]:
                pb.progress(total_time)
            else:
                raise FFmpegError(all_out)

        except KeyboardInterrupt:
            try:
                process.terminate()
            except OSError:
                pass
            process.wait()
            raise KeyboardInterrupt


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
    Unwraps a string from quotes.

    Args:
        string (str): The string to inspect.

    Returns:
        str: The (unwrapped) string.
    """
    if '"' in [string[0], string[-1]]:
        return string[1:-1]
    elif "'" in [string[0], string[-1]]:
        return string[1:-1]
    else:
        return string


def in_colab():
    """
    Check's if the environment is a Google Colab document.

    Returns:
        bool: True if the environment is a Colab document, otherwise False.
    """
    result = None
    try:
        result = 'google.colab' in str(get_ipython())
    except NameError:
        result = False
    return result

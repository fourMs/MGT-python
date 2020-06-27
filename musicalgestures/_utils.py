class MgProgressbar():
    """
    Calls in a loop to create terminal progress bar.

    Attributes
    ----------
    - total : int, optional

        Default is 1000. Total iterations.
    - time_limit : float, optional

        Default is 0.1. The maximum refresh rate of the progressbar in seconds. 
    - prefix : str, optional

        Default is 'Progress'. Prefix string.
    - suffix : str, optional

        Default is 'Complete'. Suffix string.
    - decimals : int, optional

        Default is 1. Positive number of decimals in percent complete.
    - length : int, optional

        Default is 40. Character length of bar.
    - fill : str, optional

        Default is '█'. Bar fill character.

    Methods
    -------
    - progress(iteration : int)

        Prints the progressbar according to `iteration` which is the 
        0-based step in the number of steps defined by `self.total`. At the 
        last step (where the progressbar shows 100%) `iteration` == `total` - 1. 
    """

    def __init__(
            self,
            total=100,
            time_limit=0.1,
            prefix='Progress',
            suffix='Complete',
            decimals=1,
            length=40,
            fill='█'):

        self.total = total - 1
        self.time_limit = time_limit
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.now = self.get_now()
        self.finished = False

    def get_now(self):
        from datetime import datetime
        return datetime.timestamp(datetime.now())

    def over_time_limit(self):
        callback_time = self.get_now()
        return callback_time - self.now >= self.time_limit

    def progress(self, iteration):
        if self.finished:
            return
        import sys
        capped_iteration = iteration if iteration <= self.total else self.total
        # Print New Line on Complete
        if iteration >= self.total:
            self.finished = True
            percent = ("{0:." + str(self.decimals) + "f}").format(100 *
                                                                  (capped_iteration / float(self.total)))
            filledLength = int(self.length * capped_iteration // self.total)
            bar = self.fill * filledLength + '-' * (self.length - filledLength)
            sys.stdout.flush()
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
            sys.stdout.write('\r%s |%s| %s%% %s' %
                             (self.prefix, bar, percent, self.suffix))
        else:
            return

    def __repr__(self):
        return "MgProgressbar"


def scale_num(val, in_low, in_high, out_low, out_high):
    """
    Scales a number linearly.

    Parameters
    ----------
    - val : int or float

        The value to be scaled.
    - in_low : int or float

        Minimum of input range.
    - in_high : int or float

        Maximum of input range.
    - out_low : int or float

        Minimum of output range.
    - out_high : int or float

        Maximum of output range.

    Returns
    -------
    int or float

        The scaled number.
    """
    return ((val - in_low) * (out_high - out_low)) / (in_high - in_low) + out_low


def scale_array(array, out_low, out_high):
    """
    Scales an array linearly.

    Parameters
    ----------
    - array : arraylike

        The array to be scaled.
    - out_low : int or float

        Minimum of output range.
    - out_high : int or float

        Maximum of output range.

    Returns
    -------
    - arraylike

        The scaled array.
    """
    import numpy as np
    minimum, maximum = np.min(array), np.max(array)
    m = (out_high - out_low) / (maximum - minimum)
    b = out_low - m * minimum
    return m * array + b


def get_frame_planecount(frame):
    """
    Gets the planecount (color channel count) of a video frame.

    Parameters
    ----------
    - frame : numpy array

        A frame extracted by `cv2.VideoCapture().read()`.

    Returns
    -------
    - {3, 1}

        The planecount of the input frame.
    """
    import numpy as np
    return 3 if len(np.array(frame).shape) == 3 else 1


def frame2ms(frame, fps):
    """
    Converts frames to milliseconds.

    Parameters
    ----------
    - frame : int

        The index of the frame to be converted to milliseconds.
    - fps : int

        Frames per second.

    Returns
    -------
    - int

        The rounded millisecond value of the input frame index.
    """
    return round(frame / fps * 1000)


class MgImage():
    """
    Class for handling images in the Motion Gestures Toolbox.

    Attributes
    ----------
    - filename : str

        The path to the image file to be loaded.
    """

    def __init__(self, filename):
        self.filename = filename
        import os
        self.of = os.path.splitext(self.filename)[0]
        self.fex = os.path.splitext(self.filename)[1]
    from musicalgestures._show import mg_show as show

    def __repr__(self):
        return f"MgImage('{self.filename}')"


def convert_to_avi(filename):
    """
    Converts a video to one with .avi extension using ffmpeg.

    Parameters
    ----------
    - filename : str

        Path to the input video file.

    Outputs
    -------
    - `filename`.avi

        The converted video file.

    Returns
    -------
    - str

        The path to the output '.avi' file.
    """
    import os
    of = os.path.splitext(filename)[0]
    #fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, "-c:v",
                     "mjpeg", "-q:v", "3", "-c:a", "copy", of + '.avi'])
    os.system(cmds)
    return of + '.avi'


def cast_into_avi(filename):
    """
    *Experimental*
    Casts a video into and .avi container using ffmpeg. Much faster than `convert_to_avi`,
    but does not always work well with cv2 or built-in video players.

    Parameters
    ----------
    - filename : str

        Path to the input video file.

    Outputs
    -------
    - `filename`.avi

        The converted video file.

    Returns
    -------
    - str

        The path to the output '.avi' file.
    """
    import os
    of = os.path.splitext(filename)[0]
    #fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, "-codec copy", of + '.avi'])
    os.system(cmds)
    return of + '.avi'


def extract_subclip(filename, t1, t2, targetname=None):
    """ Single threaded version of the same function from ffmpeg_tools.
    Makes a new video file playing video file ``filename`` between
        the times ``t1`` and ``t2``. """
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

    cmd = ' '.join(['ffmpeg', "-y",
                    "-ss", "%0.2f" % start,
                    "-i", filename,
                    "-t", "%0.2f" % (end-start),
                    "-map", "0", "-codec copy", targetname])
    # uses os.system instead of subprocess
    os.system(cmd)


def rotate_video(filename, angle):
    """
    Rotates a video by an `angle` using ffmpeg.

    Parameters
    ----------
    - filename : str

        The path to the input video.
    - angle : int or float

        The angle (in degrees) specifying the amount of rotation. Positive values rotate clockwise.

    Outputs
    -------
    - `filename`_rot.avi

        The rotated video file.

    Returns
    -------
    - str

        The path to the output (rotated) video file.
    """
    import os
    import math
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    if os.path.isfile(of + '_rot.avi'):
        os.remove(of + '_rot.avi')
    cmds = ' '.join(['ffmpeg', '-i', filename, "-c:v",
                     "mjpeg", "-q:v", "3", "-vf", f"rotate={math.radians(angle)}", of + '_rot.avi'])
    os.system(cmds)
    return of + '_rot', fex


def convert_to_grayscale(filename):
    """
    Converts a video to grayscale using ffmpeg.

    Parameters
    ----------
    - filename : str

        Path to the video file to be converted to grayscale.

    Outputs
    -------
    - `filename`_gray.avi

    Returns
    -------
    - str

        The path to the output (grayscale) video file.
    """
    import os
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, "-c:v", "mjpeg", "-q:v", "3", '-vf',
                     'hue=s=0', of + '_gray' + fex])
    os.system(cmds)
    return of + '_gray', fex


def extract_wav(filename):
    """
    Extracts audio from video into a .wav file via ffmpeg.

    Parameters
    ----------
    - filename : str

        Path to the video file from which the audio track shall be extracted.

    Outputs
    -------
    - `filename`.wav

    Returns
    -------
    - str

        The path to the output audio file.
    """
    import os
    of = os.path.splitext(filename)[0]
    #fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, "-acodec",
                     "pcm_s16le", of + '.wav'])
    os.system(cmds)
    return of + '.wav'


def get_length(filename):
    """
    Gets the length (s) of a video using moviepy.

    Parameters
    ----------
    - filename : str

        Path to the video file to be measured.

    Returns
    -------
    - float

        The length of the input video file in seconds.
    """
    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(filename)
    duration = float(clip.duration)
    clip.close()
    return duration


def has_audio(filename):
    """
    Gets the length (s) of a video using moviepy.

    Parameters
    ----------
    - filename : str

        Path to the video file to be checked.

    Returns
    -------
    - bool

        `True`if `filename` has an audio track, `False` otherwise.
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

    Parameters
    ----------
    - filename : str

        Path to the audio file to be dilated.
    - dilation_ratio : int or float, optional

        Default is 1. The source file's length divided by the resulting file's length.

    Outputs
    -------
    - `filename`_dilated.wav

    Returns
    -------
    - str

        The path to the output audio file.
    """
    import os
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, '-codec:a', 'pcm_s16le',
                     '-filter:a', 'atempo=' + str(dilation_ratio), of + '_dilated' + fex])
    os.system(cmds)
    return of + '_dilated' + fex


def embed_audio_in_video(source_audio, destination_video, dilation_ratio=1):
    """
    Embeds an audio file as the audio channel of a video file using ffmpeg.

    Parameters
    ----------
    - source_audio : str

        Path to the audio file to be embedded.

    - destination_video : str

        Path to the video file to embed the audio file in.

    Outputs
    -------
    - `destination_video` with the embedded audio file.
    """
    import os
    of = os.path.splitext(destination_video)[0]
    fex = os.path.splitext(destination_video)[1]

    # dilate audio file if necessary (ie. when skipping)
    if dilation_ratio != 1:
        audio_to_embed = audio_dilate(
            source_audio, dilation_ratio)  # creates '_dilated.wav'
        dilated = True
    else:
        audio_to_embed = source_audio
        dilated = False

    # embed audio in video
    cmds = ' '.join(['ffmpeg', '-i', destination_video, '-i', audio_to_embed, '-c:v',
                     'copy', '-map', '0:v:0', '-map', '1:a:0', '-shortest', of + '_w_audio' + fex])
    os.system(cmds)  # creates '_w_audio.avi'

    # cleanup:
    # if we needed to create an additional (dilated) audio file, delete it
    if dilated:
        os.remove(audio_to_embed)
    # replace (silent) destination_video with the one with the embedded audio
    os.remove(destination_video)
    os.rename(of + '_w_audio' + fex, destination_video)


def ffmpeg_cmd(command, total_time, pb_prefix='Progress'):
    import subprocess
    pb = MgProgressbar(total=total_time, prefix=pb_prefix)

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    try:
        while True:
            out = process.stdout.readline()
            if out == '':
                process.wait()
                break
                # process.poll()
                # if process.returncode is not None:
                #     break
            elif out.startswith('frame='):
                out_list = out.split()
                time_ind = [elem.startswith('time=')
                            for elem in out_list].index(True)
                time_str = out_list[time_ind][5:]
                time_sec = str2sec(time_str)
                percent = time_sec / total_time * 100
                pb.progress(time_sec)

        # process.terminate()
        # del process
        pb.progress(total_time)

        # return True

    except KeyboardInterrupt:
        try:
            process.terminate()
        except OSError:
            pass
        process.wait()
        # return False
        raise KeyboardInterrupt


def str2sec(time_string):
    elems = [float(elem) for elem in time_string.split(':')]
    return elems[0]*3600 + elems[1]*60 + elems[2]

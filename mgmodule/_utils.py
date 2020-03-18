def mg_progressbar(iteration, total, prefix='', suffix='', decimals=1, length=40, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar.

    Parameters:
    -----------
    - iteration   - Required  : current iteration (Int)
    - total       - Required  : total iterations (Int)
    - prefix      - Optional  : prefix string (Str)
    - suffix      - Optional  : suffix string (Str)
    - decimals    - Optional  : positive number of decimals in percent complete (Int)
    - length      - Optional  : character length of bar (Int)
    - fill        - Optional  : bar fill character (Str)
    - printEnd    - Optional  : end character (e.g. "\\r", "\\r\\n") (Str)
    """
    import sys

    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    sys.stdout.flush()
    sys.stdout.write('\r%s |%s| %s%% %s' %
                     (prefix, bar, percent, suffix))
    # Print New Line on Complete
    if iteration == total:
        print()


def scale_num(val, in_low, in_high, out_low, out_high):
    """Scale a number linearly.

    Parameters:
    -----------
    - val       - Required  : the value to be scaled
    - in_low    - Required  : minimum of input range
    - in_high   - Required  : maximum of input range
    - out_low   - Required  : minimum of output range
    - out_high  - Required  : maximum of output range
    """
    return ((val - in_low) * (out_high - out_low)) / (in_high - in_low) + out_low


def scale_array(array, out_low, out_high):
    """Scale an array linearly.

    Parameters:
    -----------
    - array     - Required  : the array to be scaled
    - out_low   - Required  : minimum of output range
    - out_high  - Required  : maximum of output range
    """
    minimum, maximum = np.min(array), np.max(array)
    m = (out_high - out_low) / (maximum - minimum)
    b = out_low - m * minimum
    return m * array + b


def get_frame_planecount(frame):
    """Return the planecount of a video frame

    Parameters:
    -----------
    - frame     - Required  : a frame extracted by cv2.VideoCapture().read()
    """
    import numpy as np
    return 3 if len(np.array(frame).shape) == 3 else 1


class MgImage():
    """Class for handling images"""

    def __init__(self, filename):
        self.filename = filename
        import os
        self.of = os.path.splitext(self.filename)[0]
        self.fex = os.path.splitext(self.filename)[1]
    from ._show import mg_show as show

    def __repr__(self):
        return f"MgImage('{self.filename}')"


def convert_to_avi(filename):
    """Convert any video to one with .avi extension using ffmpeg"""
    import os
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, "-c:v",
                     "mjpeg", "-q:v", "3", of + '.avi'])
    os.system(cmds)
    return of + '.avi'


def convert_to_grayscale(filename):
    """Convert a video to grayscale using ffmpeg"""
    import os
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, "-c:v", "mjpeg", "-q:v", "3", '-vf',
                     'hue=s=0', of + '_grayscale' + fex])
    os.system(cmds)
    return of + '_grayscale', fex


def extract_wav(filename):
    """Extract audio from video into a .wav file via ffmpeg"""
    import os
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, "-acodec",
                     "pcm_s16le", of + '.wav'])
    os.system(cmds)
    return of + '.wav'


def get_length(filename):
    """Return the length (s) of a video using ffprobe"""
    import subprocess
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                             'default=noprint_wrappers=1:nokey=1', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)


def audio_dilate(filename, dilation_ratio=1):
    """Time-stretch or -shrink an audio file using ffmpeg"""
    import os
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, '-codec:a', 'pcm_s16le',
                     '-filter:a', 'atempo=' + str(dilation_ratio), of + '_dilated' + fex])
    os.system(cmds)
    return of + '_dilated' + fex


def embed_audio_in_video(source_audio, destination_video, dilation_ratio=1):
    """Embed an audio file as the audio channel of a video file."""
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

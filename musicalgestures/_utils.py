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
            percent = ("{0:." + str(self.decimals) + "f}").format(100)
            filledLength = int(round(self.length))
            bar = self.fill * filledLength
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


def roundup(num, modulo_num):
    num, modulo_num = int(num), int(modulo_num)
    return num - (num % modulo_num) + modulo_num*((num % modulo_num) != 0)


def clamp(num, min_value, max_value):
    return max(min(num, max_value), min_value)


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


class MgList():
    """
    Class for handling lists of MgObjects or MgImages in the Musical Gestures Toolbox.

    Attributes
    ----------
    - objectlist : list

        The list of MgObjects and/or MgImages.
    """

    def __init__(self, objectlist):
        self.objectlist = objectlist
    from musicalgestures._show import mg_show

    def show(self):
        for obj in self.objectlist:
            obj.show()

    def __len__(self):
        return len(self.objectlist)

    def __getitem__(self, key):
        return self.objectlist[key]

    def __setitem__(self, key, value):
        self.objectlist[key] = value

    def __delitem__(sef, key):
        del self.objectlist[key]

    def __iter__(self):
        return iter(self.objectlist)

    def __repr__(self):
        return f"MgList('{self.objectlist}')"

    def as_figure(self, dpi=300):
        import os
        import librosa
        import librosa.display
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg
        import matplotlib
        import numpy as np

        elem_count = 0

        for ind, obj in enumerate(self.objectlist):
            if type(obj) == MgImage:
                # print(ind, 'MgImage')
                elem_count += 1

            elif type(obj) == MgFigure:
                # print(ind, 'MgFigure', obj.figure_type)
                if obj.figure_type == 'audio.tempogram':
                    elem_count += 2
                elif obj.figure_type == 'audio.descriptors':
                    elem_count += 3
                elif obj.figure_type == 'audio.spectrogram':
                    elem_count += 1

            elif type(obj) == MgList:
                pass
                # print(ind, 'MgList')
                # elem_count increments based on the layers and their subplots/images

        print("Total number of subplots:", elem_count)
        fig = plt.figure(dpi=dpi, figsize=(10, 3*elem_count))
        ax = [0 for elem in range(elem_count)]
        index_of_first_plot = None
        plot_counter = 0
        of = None

        for ind, obj in enumerate(self.objectlist):
            if type(obj) == MgImage:
                ax[plot_counter] = fig.add_subplot(
                    elem_count, 1, plot_counter+1)
                ax[plot_counter].imshow(mpimg.imread(obj.filename))
                ax[plot_counter].set_aspect('auto')
                ax[plot_counter].axes.xaxis.set_visible(False)
                ax[plot_counter].axes.yaxis.set_visible(False)

                # add title based on content
                last_tag = os.path.splitext(obj.filename)[0].split('_')[-1]
                if last_tag == 'mgx':
                    ax[plot_counter].set(title='Motiongram X')
                elif last_tag == 'mgy':
                    ax[plot_counter].set(title='Motiongram Y')
                elif last_tag == 'vgx':
                    ax[plot_counter].set(title='Videogram X')
                elif last_tag == 'vgy':
                    ax[plot_counter].set(title='Videogram Y')
                else:
                    ax[plot_counter].set(title=os.path.basename(obj.filename))

                # increment output filename
                if plot_counter == 0:
                    of = os.path.splitext(obj.filename)[0]
                else:
                    of += '_'
                    of += os.path.splitext(obj.filename)[0].split('_')[-1]

                plot_counter += 1

            elif type(obj) == MgFigure:
                first_plot = False
                if index_of_first_plot == None:
                    index_of_first_plot = plot_counter  # 0-based!
                    first_plot = True

                if obj.figure_type == 'audio.tempogram':
                    # increment output filename
                    if plot_counter == 0:
                        of = obj.data['of'] + '_tempogram'
                    else:
                        of += '_tempogram'

                    if first_plot:
                        ax[plot_counter] = fig.add_subplot(
                            elem_count, 1, plot_counter+1)
                    else:
                        ax[plot_counter] = fig.add_subplot(
                            elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])

                    # make plot for onset strength
                    ax[plot_counter].plot(
                        obj.data['times'], obj.data['onset_env'], label='Onset strength')
                    ax[plot_counter].label_outer()
                    ax[plot_counter].legend(frameon=True)
                    plot_counter += 1

                    # make plot for tempogram
                    ax[plot_counter] = fig.add_subplot(
                        elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])
                    librosa.display.specshow(obj.data['tempogram'], sr=obj.data['sr'], hop_length=obj.data['hop_size'],
                                             x_axis='time', y_axis='tempo', cmap='magma', ax=ax[plot_counter])
                    ax[plot_counter].axhline(obj.data['tempo'], color='w', linestyle='--',
                                             alpha=1, label='Estimated tempo={:g}'.format(obj.data['tempo']))
                    ax[plot_counter].legend(loc='upper right')
                    ax[plot_counter].set(title='Tempogram')
                    plot_counter += 1

                elif obj.figure_type == 'audio.descriptors':
                    # increment output filename
                    if plot_counter == 0:
                        of = obj.data['of'] + '_descriptors'
                    else:
                        of += '_descriptors'

                    if first_plot:
                        ax[plot_counter] = fig.add_subplot(
                            elem_count, 1, plot_counter+1)
                    else:
                        ax[plot_counter] = fig.add_subplot(
                            elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])

                    # make plot for rms
                    ax[plot_counter].semilogy(
                        obj.data['times'], obj.data['rms'][0], label='RMS Energy')
                    ax[plot_counter].legend(loc='upper right')
                    plot_counter += 1

                    # make plot for flatness
                    ax[plot_counter] = fig.add_subplot(
                        elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])
                    ax[plot_counter].plot(
                        obj.data['times'], obj.data['flatness'].T, label='Flatness', color='y')
                    ax[plot_counter].legend(loc='upper right')
                    plot_counter += 1

                    # make plot for spectrogram, centroid, bandwidth and rolloff
                    ax[plot_counter] = fig.add_subplot(
                        elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])
                    librosa.display.specshow(librosa.power_to_db(obj.data['S'], ref=np.max, top_db=120), sr=obj.data['sr'],
                                             y_axis='mel', fmax=obj.data['sr']/2, x_axis='time', hop_length=obj.data['hop_size'], ax=ax[plot_counter])
                    # get rid of "default" ticks
                    ax[plot_counter].yaxis.set_minor_locator(
                        matplotlib.ticker.NullLocator())
                    plot_xticks = np.arange(
                        0, obj.data['length']+0.1, obj.data['length']/20)
                    ax[plot_counter].set(xticks=plot_xticks)

                    freq_ticks = [elem*100 for elem in range(10)]
                    freq_ticks = [250]
                    freq = 500
                    while freq < obj.data['sr']/2:
                        freq_ticks.append(freq)
                        freq *= 1.5

                    freq_ticks = [round(elem, -1) for elem in freq_ticks]
                    freq_ticks_labels = [str(round(
                        elem/1000, 1)) + 'k' if elem > 1000 else int(round(elem)) for elem in freq_ticks]

                    ax[plot_counter].set(yticks=(freq_ticks))
                    ax[plot_counter].set(yticklabels=(freq_ticks_labels))

                    ax[plot_counter].fill_between(obj.data['times'], obj.data['cent'][0] - obj.data['spec_bw']
                                                  [0], obj.data['cent'][0] + obj.data['spec_bw'][0], alpha=0.5, label='Centroid +- bandwidth')
                    ax[plot_counter].plot(
                        obj.data['times'], obj.data['cent'].T, label='Centroid', color='y')
                    ax[plot_counter].plot(
                        obj.data['times'], obj.data['rolloff'][0], label='Roll-off frequency (0.99)')
                    ax[plot_counter].plot(
                        obj.data['times'], obj.data['rolloff_min'][0], color='r', label='Roll-off frequency (0.01)')

                    ax[plot_counter].legend(loc='upper right')

                    plot_counter += 1

                elif obj.figure_type == 'audio.spectrogram':
                    # increment output filename
                    if plot_counter == 0:
                        of = obj.data['of'] + '_spectrogram'
                    else:
                        of += '_spectrogram'

                    if first_plot:
                        ax[plot_counter] = fig.add_subplot(
                            elem_count, 1, plot_counter+1)
                    else:
                        ax[plot_counter] = fig.add_subplot(
                            elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])

                    librosa.display.specshow(librosa.power_to_db(obj.data['S'], ref=np.max, top_db=120), sr=obj.data['sr'],
                                             y_axis='mel', fmax=obj.data['sr']/2, x_axis='time', hop_length=obj.data['hop_size'], ax=ax[plot_counter])
                    # get rid of "default" ticks
                    ax[plot_counter].yaxis.set_minor_locator(
                        matplotlib.ticker.NullLocator())
                    plot_xticks = np.arange(
                        0, obj.data['length']+0.1, obj.data['length']/20)
                    ax[plot_counter].set(xticks=plot_xticks)

                    freq_ticks = [elem*100 for elem in range(10)]
                    freq_ticks = [250]
                    freq = 500
                    while freq < obj.data['sr']/2:
                        freq_ticks.append(freq)
                        freq *= 1.5

                    freq_ticks = [round(elem, -1) for elem in freq_ticks]
                    freq_ticks_labels = [str(round(
                        elem/1000, 1)) + 'k' if elem > 1000 else int(round(elem)) for elem in freq_ticks]

                    ax[plot_counter].set(yticks=(freq_ticks))
                    ax[plot_counter].set(yticklabels=(freq_ticks_labels))
                    ax[plot_counter].set(title='Spectrogram')

                    plot_counter += 1

        fig.tight_layout()

        # save figure as png
        plt.savefig(of + '.png', format='png')

        # create MgFigure
        mgf = MgFigure(
            figure=fig,
            figure_type='layers',
            data=None,
            layers=self.objectlist,
            image=of + '.png'
        )

        return mgf


class MgFigure():
    """
    Class for working with figures and plots within the Musical Gestures Toolbox.

    Attributes
    ----------
    - figure : matplotlib.pyplot.figure

        The internal figure.

    - figure_type : str

        A keyword describing the type of the figure, such as "audio.spectrogram", "audio.tempogram",
        "audio.descriptors", "layers", etc.

    - data : dictionary

        The dictionary containing all the necessary variables, lists and (typically) NumPy arrays necessary
        to rebuild each subplot in the figure.

    - layers : list

        This is only relevant if the MgFigure instance is already one of "layers" type, which indicates
        that it is already a composit of several MgFigures and/or MgImages. In this case the layers list
        should contain all the child instances (MgFigures, MgImages, or MgLists of these) which are 
        included in this MgFigure and show as subplots. 

    - image : str

        Path to the image file (the rendered figure).
    """

    def __init__(self, figure=None, figure_type=None, data=None, layers=None, image=None):
        self.figure = figure
        self.figure_type = figure_type
        self.data = data
        self.layers = layers
        self.image = image

    def __repr__(self):
        return f"MgFigure(figure_type='{self.figure_type}')"

    def show(self):
        self.figure.show()


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
    cmds = ['ffmpeg', '-i', filename, "-c:v", "mjpeg",
            "-q:v", "3", "-c:a", "copy", of + '.avi']
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Converting to avi:')
    return of + '.avi'


def convert_to_mp4(filename):
    """
    Converts a video to one with .mp4 extension using ffmpeg.

    Parameters
    ----------
    - filename : str

        Path to the input video file.

    Outputs
    -------
    - `filename`.mp4

        The converted video file.

    Returns
    -------
    - str

        The path to the output '.mp4' file.
    """
    import os
    of = os.path.splitext(filename)[0]
    cmds = ['ffmpeg', '-i', filename, "-q:v", "3", "-c:a", "copy", of + '.mp4']
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Converting to mp4:')
    return of + '.mp4'


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
    cmds = ['ffmpeg', '-i', filename, "-codec copy", of + '.avi']
    ffmpeg_cmd(cmds, get_length(filename), pb_prefix='Casting to avi')
    return of + '.avi'


def extract_subclip(filename, t1, t2, targetname=None):
    """ Makes a new video file playing video file ``filename`` between
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

    ffmpeg_cmd(cmd, length, pb_prefix='Trimming:')


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
    of, fex = os.path.splitext(filename)
    if os.path.isfile(of + '_rot' + fex):
        os.remove(of + '_rot' + fex)
    # cmds = ['ffmpeg', '-i', filename, "-c:v", "mjpeg", "-q:v", "3",
    #         "-vf", f"rotate={math.radians(angle)}", of + '_rot' + fex]
    cmds = ['ffmpeg', '-i', filename, "-vf",
            f"rotate={math.radians(angle)}", "-q:v", "3", "-c:a", "copy", of + '_rot' + fex]
    ffmpeg_cmd(cmds, get_length(filename),
               pb_prefix=f"Rotating video by {angle} degrees:")
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
    of, fex = os.path.splitext(filename)
    # cmds = ['ffmpeg', '-i', filename, "-c:v", "mjpeg",
    #         "-q:v", "3", '-vf', 'hue=s=0', of + '_gray' + fex]
    cmds = ['ffmpeg', '-i', filename, '-vf',
            'hue=s=0', "-q:v", "3", "-c:a", "copy", of + '_gray' + fex]
    ffmpeg_cmd(cmds, get_length(filename),
               pb_prefix='Converting to grayscale:')
    return of + '_gray', fex


def framediff_ffmpeg(filename, outname=None, color=True):

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


def crop_ffmpeg(filename, w, h, x, y, outname=None):

    import os

    of, fex = os.path.splitext(filename)

    if outname == None:
        outname = of + '_crop' + fex

    width, height = get_widthheight(filename)

    cmd = ['ffmpeg', '-y', '-i', filename, '-vf',
           f'crop={w}:{h}:{x}:{y}', '-q:v', '3', "-c:a", "copy", outname]

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Rendering cropped video:')

    return outname


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
    # fex = os.path.splitext(filename)[1]
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


def get_framecount(filename):
    """
    Returns the number of frames of a video using moviepy.

    Parameters
    ----------
    - filename : str

        Path to the video file to be measured.

    Returns
    -------
    - int

        The number of frames in the input video file.
    """
    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(filename)
    framecount = int(round(float(clip.duration) * float(clip.fps)))
    clip.close()
    return framecount


def get_fps(filename):
    """
    Returns the frames per second value of a video using moviepy.

    Parameters
    ----------
    - filename : str

        Path to the video file to be measured.

    Returns
    -------
    - float

        The frames per second value of the input video file.
    """
    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(filename)
    fps = float(clip.fps)
    clip.close()
    return fps


def get_widthheight(filename):
    """
    Returns the width and height (in pixels) of a video using moviepy.

    Parameters
    ----------
    - filename : str

        Path to the video file to be measured.

    Returns
    -------
    - int

        The width and height (in pixels) of the input video file.
    """
    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(filename)
    (width, height) = clip.size
    clip.close()
    return width, height


def get_first_frame_as_image(filename, outname=None, pict_format='.png'):

    import os
    of, fex = os.path.splitext(filename)

    if outname == None:
        outname = of + pict_format

    cmd = ' '.join(['ffmpeg', '-y', '-i', filename, '-frames', '1', outname])

    os.system(cmd)

    return outname


def get_screen_resolution_scaled():

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
            elif out.startswith('frame='):
                out_list = out.split()
                time_ind = [elem.startswith('time=')
                            for elem in out_list].index(True)
                time_str = out_list[time_ind][5:]
                time_sec = str2sec(time_str)
                percent = time_sec / total_time * 100
                pb.progress(time_sec)

        pb.progress(total_time)

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

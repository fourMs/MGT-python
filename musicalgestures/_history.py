import cv2
import os
import numpy as np
from musicalgestures._utils import extract_wav, embed_audio_in_video, MgProgressbar, ffmpeg_cmd, get_length
import musicalgestures


class ParameterError(Exception):
    """Base class for argument errors."""
    pass


def history_ffmpeg(self, filename='', history_length=10, weights=1, normalize=False, norm_strength=1, norm_smooth=0):
    """
    This function  creates a video where each frame is the average of the 
    n previous frames, where n is determined by `history_length`.
    The history frames are summed up and normalized, and added to the 
    current frame to show the history. Uses ffmpeg.

    Parameters
    ----------
    - filename : str, optional

        Path to the input video file. If not specified the video file pointed to by the MgObject is used.
    - history_length : int, optional

        Default is 10. Number of frames to be saved in the history tail.

    - weights: int, float, str, list, optional

        Default is 1. Defines the weight or weights applied to the frames in the history tail. If given as list
        the first element in the list will correspond to the weight of the newest frame in the tail. If given as
        a str - like "3 1.2 1" - it will be automatically converted to a list - like [3, 1.2, 1].

    - normalize: bool, optional

        Default is `False` (no normalization). If `True`, the history video will be normalized. This can be useful
        when processing motion (frame difference) videos.

    - norm_strength: int, float, optional

        Default is 1. Defines the strength of the normalization where 1 represents full strength.

    - norm_smooth: int, optional

        Default is 0 (no smoothing). Defines the number of previous frames to use for temporal smoothing. The input 
        range of each channel is smoothed using a rolling average over the current frame and the `norm_smooth` previous frames.

    Outputs
    -------
    - `filename`_history.avi

    Returns
    -------
    - MgObject 
        A new MgObject pointing to the output '_history' video file.
    """

    if filename == '':
        filename = self.filename

    of, fex = os.path.splitext(filename)

    if type(weights) in [int, float]:
        weights_map = np.ones(history_length)
        weights_map[-1] = weights
        str_weights = ' '.join([str(weight) for weight in weights_map])
    elif type(weights) == list:
        typecheck_list = [type(item) in [int, float] for item in weights]
        if False in typecheck_list:
            raise ParameterError(
                'Found wrong type(s) in the list of weights. Use ints and floats.')
        elif len(weights) > history_length:
            raise ParameterError(
                'history_length must be greater than or equal to the number of weights specified in weights.')
        else:
            weights_map = np.ones(history_length - len(weights))
            weights.reverse()
            weights_map = list(weights_map)
            weights_map += weights
            str_weights = ' '.join([str(weight) for weight in weights_map])
    elif type(weights) == str:
        weights_as_list = weights.split()
        typecheck_list = [type(item) in [int, float]
                          for item in weights_as_list]
        if False in typecheck_list:
            raise ParameterError(
                'Found wrong type(s) in the list of weights. Use ints and floats.')
        elif len(weights) > history_length:
            raise ParameterError(
                'history_length must be greater than or equal to the number of weights specified in weights.')
        else:
            weights_map = np.ones(history_length - len(weights_as_list))
            weights_as_list.reverse()
            weights_map += weights_as_list
            str_weights = ' '.join([str(weight) for weight in weights_map])
    else:
        raise ParameterError(
            'Wrong type used for weights. Use int, float, str, or list.')

    if type(normalize) != bool:
        raise ParameterError(
            'Wrong type used for normalize. Use only bool.')

    if normalize:
        if type(norm_strength) not in [int, float]:
            raise ParameterError(
                'Wrong type used for norm_strength. Use int or float.')
        if type(norm_smooth) != int:
            raise ParameterError(
                'Wrong type used for norm_smooth. Use only int.')

    outname = of + '_history' + fex
    if normalize:
        if norm_smooth != 0:
            cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
                   f'tmix=frames={history_length}:weights={str_weights},normalize=independence=0:strength={norm_strength}:smoothing={norm_smooth}', '-q:v', '3', '-c:a', 'copy', outname]
        else:
            cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
                   f'tmix=frames={history_length}:weights={str_weights},normalize=independence=0:strength={norm_strength}', '-q:v', '3', '-c:a', 'copy', outname]
    else:
        cmd = ['ffmpeg', '-y', '-i', filename, '-vf',
               f'tmix=frames={history_length}:weights={str_weights}', '-q:v', '3', '-c:a', 'copy', outname]

    # success = ffmpeg_cmd(cmd, get_length(filename),
    #                      pb_prefix='Rendering history video:')

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Rendering history video:')

    # if success:
    #     destination_video = self.of + '_history' + self.fex
    #     return musicalgestures.MgObject(destination_video, color=self.color, returned_by_process=True)

    destination_video = self.of + '_history' + self.fex
    return musicalgestures.MgObject(destination_video, color=self.color, returned_by_process=True)

    # else:
    #     pass
    # raise KeyboardInterrupt


def history_cv2(self, filename='', history_length=10, weights=1):
    """
    This function  creates a video where each frame is the average of the 
    n previous frames, where n is determined by `history_length`.
    The history frames are summed up and normalized, and added to the 
    current frame to show the history. Uses cv2.

    Parameters
    ----------
    - filename : str, optional

        Path to the input video file. If not specified the video file pointed to by the MgObject is used.
    - history_length : int, optional

        Default is 10. Number of frames to be saved in the history tail.

    Outputs
    -------
    - `filename`_history.avi

    Returns
    -------
    - MgObject 
        A new MgObject pointing to the output '_history' video file.
    """

    if filename == '':
        filename = self.filename

    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    video = cv2.VideoCapture(filename)
    ret, frame = video.read()
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')

    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    pb = MgProgressbar(total=length, prefix='Rendering history video:')

    out = cv2.VideoWriter(of + '_history' + fex, fourcc, fps, (width, height))

    ii = 0
    history = []
    weights_map = [1 for weight in range(history_length+1)]

    if type(weights) in [int, float]:
        offset = weights - 1
        weights_map[0] = weights
    elif type(weights) == list:
        offset = sum([weight - 1 for weight in weights])
        for ind, weight in enumerate(weights):
            if ind > history_length:
                break
            weights_map[ind] = weight

    denominator = history_length + 1 + offset

    while(video.isOpened()):
        ret, frame = video.read()
        if ret == True:
            if self.color == False:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame = (np.array(frame)).astype(np.float64)

            if len(history) > 0:
                #history_total = frame/(len(history)+1)
                history_total = frame * weights_map[0] / denominator
                # history_total = frame
            else:
                history_total = frame

            for ind, newframe in enumerate(history):
                #history_total += newframe/(len(history)+1)
                history_total += newframe * weights_map[ind+1] / denominator
            # or however long history you would like
            if len(history) >= history_length:
                history.pop(0)  # pop first frame
            history.append(frame)
            # 0.5 to not overload it poor thing
            total = history_total.astype(np.uint64)

            if self.color == False:
                total = cv2.cvtColor(total.astype(
                    np.uint8), cv2.COLOR_GRAY2BGR)
                out.write(total)
            else:
                out.write(total.astype(np.uint8))

        else:
            pb.progress(length)
            # mg_progressbar(
            #     length, length, 'Rendering history video:', 'Complete')
            break

        pb.progress(ii)
        ii += 1
        # mg_progressbar(ii, length+1, 'Rendering history video:', 'Complete')

    out.release()

    destination_video = self.of + '_history' + self.fex

    if self.has_audio:
        source_audio = extract_wav(self.of + self.fex)
        embed_audio_in_video(source_audio, destination_video)
        os.remove(source_audio)

    return musicalgestures.MgObject(destination_video, color=self.color, returned_by_process=True)

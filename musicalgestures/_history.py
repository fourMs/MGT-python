import cv2
import os
import numpy as np
from musicalgestures._utils import extract_wav, embed_audio_in_video, MgProgressbar, ffmpeg_cmd, get_length, generate_outfilename, convert_to_avi
import musicalgestures


class ParameterError(Exception):
    """Base class for argument errors."""
    pass


def history_ffmpeg(self, filename=None, history_length=10, weights=1, normalize=False, norm_strength=1, norm_smooth=0, target_name=None, overwrite=False):
    """
    This function  creates a video where each frame is the average of the N previous frames, where n is determined by `history_length`. The history frames are summed up and normalized, and added to the current frame to show the history. Uses ffmpeg.

    Args:
        filename (str, optional): Path to the input video file. If None, the video file of the MgObject is used. Defaults to None.
        history_length (int, optional): Number of frames to be saved in the history tail. Defaults to 10.
        weights (int, float, list or str, optional): Defines the weight or weights applied to the frames in the history tail. If given as list the first element in the list will correspond to the weight of the newest frame in the tail. If given as a str - like "3 1.2 1" - it will be automatically converted to a list - like [3, 1.2, 1]. Defaults to 1.
        normalize (bool, optional): If True, the history video will be normalized. This can be useful when processing motion (frame difference) videos. Defaults to False.
        norm_strength (int or float, optional): Defines the strength of the normalization where 1 represents full strength. Defaults to 1.
        norm_smooth (int, optional): Defines the number of previous frames to use for temporal smoothing. The input range of each channel is smoothed using a rolling average over the current frame and the `norm_smooth` previous frames. Defaults to 0.
        target_name (str, optional): Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_history" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgObject: A new MgObject pointing to the output video file.
    """

    if filename == None:
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


    if target_name == None:
        target_name = of + '_history' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    if normalize:
        if norm_smooth != 0:
            cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
                   f'tmix=frames={history_length}:weights={str_weights},normalize=independence=0:strength={norm_strength}:smoothing={norm_smooth}', '-q:v', '3', '-c:a', 'copy', target_name]
        else:
            cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
                   f'tmix=frames={history_length}:weights={str_weights},normalize=independence=0:strength={norm_strength}', '-q:v', '3', '-c:a', 'copy', target_name]
    else:
        cmd = ['ffmpeg', '-y', '-i', filename, '-vf',
               f'tmix=frames={history_length}:weights={str_weights}', '-q:v', '3', '-c:a', 'copy', target_name]

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Rendering history video:')

    # save the result as the history_video for parent MgObject
    self.history_video = musicalgestures.MgObject(target_name, color=self.color, returned_by_process=True)

    return self.history_video


def history_cv2(self, filename=None, history_length=10, weights=1, target_name=None, overwrite=False):
    """
    This function  creates a video where each frame is the average of the N previous frames, where n is determined by `history_length`. The history frames are summed up and normalized, and added to the current frame to show the history. Uses cv2.

    Args:
        filename (str, optional): Path to the input video file. If None, the video file of the MgObject is used. Defaults to None.
        history_length (int, optional): Number of frames to be saved in the history tail. Defaults to 10.
        weights (int, float, or list, optional): Defines the weight or weights applied to the frames in the history tail. If given as list the first element in the list will correspond to the weight of the newest frame in the tail. Defaults to 1.
        target_name (str, optional): Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_history" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgObject: A new MgObject pointing to the output video file.
    """

    if filename == None:
        filename = self.filename

    of, fex = os.path.splitext(filename)

    if fex != '.avi':
        # first check if there already is a converted version, if not create one and register it to the parent self
        if "as_avi" not in self.__dict__.keys():
            file_as_avi = convert_to_avi(of + fex, overwrite=overwrite)
            # register it as the avi version for the file
            self.as_avi = musicalgestures.MgObject(file_as_avi)
        # point of and fex to the avi version
        of, fex = self.as_avi.of, self.as_avi.fex
        filename = of + fex
    
    video = cv2.VideoCapture(filename)
    ret, frame = video.read()
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')

    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    pb = MgProgressbar(total=length, prefix='Rendering history video:')

    if target_name == None:
        target_name = of + '_history' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    out = cv2.VideoWriter(target_name, fourcc, fps, (width, height))

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
            break

        pb.progress(ii)
        ii += 1

    out.release()

    destination_video = target_name

    if self.has_audio:
        source_audio = extract_wav(self.of + self.fex)
        embed_audio_in_video(source_audio, destination_video)
        os.remove(source_audio)

    self.history_video = musicalgestures.MgObject(destination_video, color=self.color, returned_by_process=True)

    # return musicalgestures.MgObject(destination_video, color=self.color, returned_by_process=True)
    return self.history_video

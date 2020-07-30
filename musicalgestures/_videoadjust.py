import numpy as np
import cv2
from musicalgestures._utils import scale_num, scale_array, MgProgressbar, get_length, ffmpeg_cmd, has_audio


def mg_contrast_brightness(of, fex, vidcap, fps, length, width, height, contrast, brightness):
    """
    Applies contrast and brightness to a video.

    Parameters
    ----------
    - of : str

        'Only filename' without extension (but with path to the file).
    - fex : str

        File extension.
    - vidcap : 

        cv2 capture of video file, with all frames ready to be read with `vidcap.read()`.
    - fps : int

        The FPS (frames per second) of the input video capture.
    - length : int

        The number of frames in the input video capture.
    - width : int

        The pixel width of the input video capture. 
    - height : int

        The pixel height of the input video capture. 
    - contrast : int or float, optional

        Applies +/- 100 contrast to video.
    - brightness : int or float, optional

        Applies +/- 100 brightness to video.

    Outputs
    -------
    - A video file with the name `of` + '_cb' + `fex`.

    Returns
    -------
    - cv2 video capture of output video file.
    """
    pb = MgProgressbar(
        total=length, prefix='Adjusting contrast and brightness:')
    count = 0
    if brightness != 0 or contrast != 0:
        # keeping values in sensible range
        contrast = np.clip(contrast, -100.0, 100.0)
        brightness = np.clip(brightness, -100.0, 100.0)

        contrast *= 1.27
        brightness *= 2.55

        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_cb' + fex, fourcc, fps, (width, height))
        success, image = vidcap.read()
        while success:
            success, image = vidcap.read()
            if not success:
                pb.progress(length)
                break
            image = np.int16(image) * (contrast/127+1) - contrast + brightness
            image = np.clip(image, 0, 255)
            out.write(image.astype(np.uint8))
            pb.progress(count)
            count += 1
        out.release()
        vidcap = cv2.VideoCapture(of + '_cb' + fex)

    return vidcap


def contrast_brightness_ffmpeg(filename, contrast=0, brightness=0):
    if contrast == 0 and brightness == 0:
        return

    import os
    import numpy as np

    of, fex = os.path.splitext(filename)

    # keeping values in sensible range
    contrast = np.clip(contrast, -100.0, 100.0)
    brightness = np.clip(brightness, -100.0, 100.0)

    # ranges are "handpicked" so that the results are close to the results of mg_contrast_brightness
    if contrast == 0:
        p_saturation, p_contrast, p_brightness = 0, 0, 0
    elif contrast > 0:
        p_saturation = scale_num(contrast, 0, 100, 1, 1.9)
        p_contrast = scale_num(contrast, 0, 100, 1, 2.3)
        p_brightness = scale_num(contrast, 0, 100, 0, 0.04)
    elif contrast < 0:
        p_saturation = scale_num(contrast, 0, -100, 1, 0)
        p_contrast = scale_num(contrast, 0, -100, 1, 0)
        p_brightness = 0

    if brightness != 0:
        p_brightness += brightness / 100

    outname = of + '_cb' + fex

    cmd = ['ffmpeg', '-y', '-i', filename, '-vf',
           f'eq=saturation={p_saturation}:contrast={p_contrast}:brightness={p_brightness}', '-q:v', '3', outname]

    ffmpeg_cmd(cmd, get_length(filename),
               pb_prefix='Adjusting contrast and brightness:')


def mg_skip_frames(of, fex, vidcap, skip, fps, length, width, height):
    """
    Time-shrinks the video by skipping (discarding) every n frames determined by `skip`.

    Parameters
    ----------
    - of : str

        'Only filename' without extension (but with path to the file).
    - fex : str

        File extension.
    - vidcap : 

        cv2 capture of video file, with all frames ready to be read with `vidcap.read()`.
    - skip : int

        Every n frames to discard. `skip=0` keeps all frames, `skip=1` skips every other frame.
    - fps : int

        The FPS (frames per second) of the input video capture.
    - length : int

        The number of frames in the input video capture.
    - width : int

        The pixel width of the input video capture. 
    - height : int

        The pixel height of the input video capture.

    Outputs
    -------
    - A video file with the name `of` + '_skip' + `fex`.

    Returns
    -------
    - videcap :

        cv2 video capture of output video file.
    - length : int

        The number of frames in the output video file.
    - fps : int

        The FPS (frames per second) of the output video file.
    - width : int

        The pixel width of the output video file. 
    - height : int

        The pixel height of the output video file. 
    """
    pb = MgProgressbar(total=length, prefix='Skipping frames:')
    count = 0
    if skip != 0:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_skip' + fex, fourcc,
                              int(fps), (width, height))  # don't change fps, with higher skip values we want shorter videos
        success, image = vidcap.read()
        while success:
            success, image = vidcap.read()
            if not success:
                pb.progress(length)
                break
            # on every frame we wish to use
            if (count % (skip+1) == 0):  # NB if skip=1, we should keep every other frame
                out.write(image.astype(np.uint8))
            pb.progress(count)
            count += 1
        out.release()
        vidcap.release()
        vidcap = cv2.VideoCapture(of + '_skip' + fex)

        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return vidcap, length, fps, width, height


def skip_frames_ffmpeg(filename, skip=0):
    if skip == 0:
        return

    import os

    of, fex = os.path.splitext(filename)

    pts_ratio = 1 / (skip+1)
    atempo_ratio = skip+1

    outname = of + '_skip' + fex

    if has_audio(filename):
        cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v];[0:a]atempo={atempo_ratio}[a]', '-map', '[v]', '-map', '[a]', '-q:v', '3', '-shortest', outname]
    else:
        cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v]', '-map', '[v]', '-q:v', '3', outname]

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Skipping frames:')

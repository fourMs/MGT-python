import numpy as np
import cv2
from musicalgestures._utils import scale_num, scale_array, MgProgressbar, get_length, ffmpeg_cmd, has_audio


def contrast_brightness_ffmpeg(filename, contrast=0, brightness=0):
    """
    Applies contrast and brightness adjustments on the source video using ffmpeg.

    Args:
        filename (str): Path to the video to process.
        contrast (int or float, optional): Increase or decrease contrast. Values range from -100 to 100. Defaults to 0.
        brightness (int or float, optional): Increase or decrease brightness. Values range from -100 to 100. Defaults to 0.

    Outputs:
        `filename`_cb.<file extension>
    """
    if contrast == 0 and brightness == 0:
        return

    import os
    import numpy as np

    of, fex = os.path.splitext(filename)

    # keeping values in sensible range
    contrast = np.clip(contrast, -100.0, 100.0)
    brightness = np.clip(brightness, -100.0, 100.0)

    # ranges are "handpicked" so that the results are close to the results of contrast_brightness_cv2 (deprecated)
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
           f'eq=saturation={p_saturation}:contrast={p_contrast}:brightness={p_brightness}', '-q:v', '3', "-c:a", "copy", outname]

    ffmpeg_cmd(cmd, get_length(filename),
               pb_prefix='Adjusting contrast and brightness:')


def skip_frames_ffmpeg(filename, skip=0):
    """
    Time-shrinks the video by skipping (discarding) every n frames determined by `skip`. To discard half of the frames (ie. double the speed of the video) use `skip=1`.

    Args:
        filename (str): Path to the video to process.
        skip (int, optional): Discard `skip` frames before keeping one. Defaults to 0.

    Outputs:
        `filename`_skip.<file extension>
    """
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

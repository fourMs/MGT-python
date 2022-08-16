import numpy as np
import cv2
import os
import musicalgestures
from musicalgestures._utils import scale_num, scale_array, MgProgressbar, get_length, ffmpeg_cmd, has_audio, generate_outfilename, convert_to_mp4, convert_to_avi


def contrast_brightness_ffmpeg(filename, contrast=0, brightness=0, target_name=None, overwrite=False):
    """
    Applies contrast and brightness adjustments on the source video using ffmpeg.

    Args:
        filename (str): Path to the video to process.
        contrast (int/float, optional): Increase or decrease contrast. Values range from -100 to 100. Defaults to 0.
        brightness (int/float, optional): Increase or decrease brightness. Values range from -100 to 100. Defaults to 0.
        target_name (str, optional): Defaults to None (which assumes that the input filename with the suffix "_cb" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the output video.
    """
    if contrast == 0 and brightness == 0:
        return

    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + '_cb' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

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

    cmd = ['ffmpeg', '-y', '-i', filename, '-vf',
           f'eq=saturation={p_saturation}:contrast={p_contrast}:brightness={p_brightness}', '-q:v', '3', "-c:a", "copy", target_name]

    ffmpeg_cmd(cmd, get_length(filename),
               pb_prefix='Adjusting contrast and brightness:')

    return target_name


def skip_frames_ffmpeg(filename, skip=0, target_name=None, overwrite=False):
    """
    Time-shrinks the video by skipping (discarding) every n frames determined by `skip`. 
    To discard half of the frames (ie. double the speed of the video) use `skip=1`.

    Args:
        filename (str): Path to the video to process.
        skip (int, optional): Discard `skip` frames before keeping one. Defaults to 0.
        target_name (str, optional): Defaults to None (which assumes that the input filename with the suffix "_skip" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the output video.
    """
    if skip == 0:
        return

    of, fex = os.path.splitext(filename)
    fex = '.avi'

    pts_ratio = 1 / (skip+1)
    atempo_ratio = skip+1

    if target_name == None:
        target_name = of + '_skip' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    if has_audio(filename):
        cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v];[0:a]atempo={atempo_ratio}[a]', '-map', '[v]', '-map', '[a]', '-q:v', '3', '-shortest', target_name]
    else:
        cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v]', '-map', '[v]', '-q:v', '3', target_name]

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Skipping frames:')

    return target_name

def fixed_frames_ffmpeg(filename, frames=0, target_name=None, overwrite=False):
    """
    Specify a fixed target number frames to extract from the video. 
    To extract only keyframes from the video, set the parameter keyframes to True.

    Args:
        filename (str): Path to the video to process.
        frames (int), optional): Number frames to extract from the video. If set to -1, it will only extract the keyframes of the video. Defaults to 0.
        target_name (str, optional): Defaults to None (which assumes that the input filename with the suffix "_fixed" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: Path to the output video.
    """
    of, fex = os.path.splitext(filename)

    if fex != '.mp4':
        # Convert video to mp4
        filename = convert_to_mp4(of + fex, overwrite=overwrite)
        of, fex = os.path.splitext(filename)

    if target_name == None:
         target_name = of + '_fixed' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    cap = cv2.VideoCapture(filename)
    nb_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    pts_ratio = frames / nb_frames
    atempo_ratio = 1 / pts_ratio

    if frames == 0:
        return

    # Extract only keyframes
    if frames == -1:
        cmd = ['ffmpeg', '-y', '-discard', 'nokey', '-i', filename, '-c', 'copy', 'temp.264'] 
        ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Extracting keyframes:')
        cmd = ['ffmpeg', '-y', '-r', str(fps), '-i', 'temp.264', '-c', 'copy', target_name]
        ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Encoding temporary video file:') 

        # Remove temporary video file
        os.remove('temp.264')

        return target_name

    if has_audio(filename):
        cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v];[0:a]atempo={atempo_ratio}[a]', '-map', '[v]', '-map', '[a]', '-q:v', '3', '-shortest', target_name]
    else:
        cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v]', '-map', '[v]', '-q:v', '3', target_name]

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Fixing frames:')

    return target_name


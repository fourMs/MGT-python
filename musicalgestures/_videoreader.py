import cv2
import os
import numpy as np
from musicalgestures._videoadjust import skip_frames_ffmpeg, contrast_brightness_ffmpeg
from musicalgestures._cropvideo import *
from musicalgestures._utils import has_audio, convert_to_avi, rotate_video, convert_to_grayscale, extract_subclip, get_length, get_fps, get_framecount


class ReadError(Exception):
    """Base class for file read errors."""
    pass


def mg_videoreader(
        filename,
        starttime=0,
        endtime=0,
        skip=0,
        rotate=0,
        contrast=0,
        brightness=0,
        crop='None',
        color=True,
        keep_all=False,
        returned_by_process=False):
    """
    Reads in a video file, and optionally apply several different processes on it. These include:
    - trimming,
    - skipping,
    - rotating,
    - applying brightness and contrast,
    - cropping,
    - converting to grayscale.

    Args:
        filename (str): Path to the input video file.
        starttime (int or float, optional): Trims the video from this start time (s). Defaults to 0.
        endtime (int or float, optional): Trims the video until this end time (s). Defaults to 0 (which will make the algorithm use the full length of the input video instead).
        skip (int, optional): Time-shrinks the video by skipping (discarding) every n frames determined by `skip`. Defaults to 0.
        rotate (int or float, optional): Rotates the video by a `rotate` degrees. Defaults to 0.
        contrast (int or float, optional): Applies +/- 100 contrast to video. Defaults to 0.
        brightness (int or float, optional): Applies +/- 100 brightness to video. Defaults to 0.
        crop (str, optional): If 'manual', opens a window displaying the first frame of the input video file, where the user can draw a rectangle to which cropping is applied. If 'auto' the cropping function attempts to determine the area of significant motion and applies the cropping to that area. Defaults to 'None'.
        color (bool, optional): If False, converts the video to grayscale and sets every method in grayscale mode. Defaults to True.
        keep_all (bool, optional): If True, preserves an output video file after each used preprocessing stage. Defaults to False.
        returned_by_process (bool, optional): This parameter is only for internal use, do not use it. Defaults to False.

    Outputs:
        A video file with the applied processes. The name of the file will be `filename` + a suffix for each process.

    Returns:
        int: The number of frames in the output video file.
        int: The pixel width of the output video file.
        int: The pixel height of the output video file.
        int: The FPS (frames per second) of the output video file.
        float: The length of the output video file in seconds.
        str: The path to the output video file without its extension. The file name gets a suffix for each used process.
        str: The file extension of the output video file.
        bool: Whether the video has an audio track.
    """

    # Separate filename from file extension
    of, fex = os.path.splitext(filename)

    trimming = False
    skipping = False
    rotating = False
    cbing = False
    cropping = False

    # Cut out relevant bit of video using starttime and endtime
    if starttime != 0 or endtime != 0:
        extract_subclip(filename, starttime, endtime,
                        targetname=of + '_trim' + fex)
        of = of + '_trim'
        trimming = True

    if skip != 0:
        skip_frames_ffmpeg(of + fex, skip)
        if not keep_all and trimming:
            os.remove(of+fex)

        of = of + '_skip'
        skipping = True

    length = get_framecount(of+fex)
    fps = get_fps(of+fex)

    # 0 means full length
    if endtime == 0:
        endtime = length/fps

    if rotate != 0:
        rotate_video(of + fex, rotate)
        if not keep_all and (skipping or trimming):
            os.remove(of + fex)
        of = of + '_rot'
        rotating = True

    # Apply contrast/brightness before the motion analysis
    if contrast != 0 or brightness != 0:
        contrast_brightness_ffmpeg(
            of+fex, contrast=contrast, brightness=brightness)

        if not keep_all and (rotating or skipping or trimming):
            os.remove(of + fex)
        of = of + '_cb'
        cbing = True

    # Crops video either manually or automatically
    if crop.lower() != 'none':
        mg_cropvideo_ffmpeg(of+fex, crop_movement=crop)

        if not keep_all and (cbing or rotating or skipping or trimming):
            os.remove(of + fex)
        of = of + '_crop'
        cropping = True

    if color == False and returned_by_process == False:
        of_gray, fex = convert_to_grayscale(of + fex)
        if not keep_all and (cropping or cbing or rotating or skipping or trimming):
            os.remove(of + fex)
        of = of_gray

    width, height = get_widthheight(of+fex)
    video_has_audio_track = has_audio(of+fex)

    return length, width, height, fps, endtime, of, fex, video_has_audio_track

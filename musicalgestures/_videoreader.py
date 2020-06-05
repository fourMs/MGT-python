import cv2
import os
#from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import numpy as np
from musicalgestures._videoadjust import mg_contrast_brightness, mg_skip_frames
from musicalgestures._cropvideo import *
from musicalgestures._utils import has_audio, convert_to_avi, rotate_video, extract_wav, embed_audio_in_video, convert_to_grayscale, extract_subclip, get_length


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

    Parameters
    ----------
    - filename : str

        Path to the input video file.
    - starttime : int or float, optional

        Trims the video from this start time (s).

    - endtime : int or float, optional

        Trims the video until this end time (s).

    - skip : int, optional

        Time-shrinks the video by skipping (discarding) every n frames determined by `skip`.
    - rotate : int or float, optional

        Rotates the video by a `rotate` degrees.

    - contrast : int or float, optional

        Applies +/- 100 contrast to video.
    - brightness : int or float, optional

        Applies +/- 100 brightness to video.

    - crop : {'none', 'manual', 'auto'}, optional

        If `manual`, opens a window displaying the first frame of the input video file,
        where the user can draw a rectangle to which cropping is applied.
        If `auto` the cropping function attempts to determine the area of significant motion 
        and applies the cropping to that area.

    - color : bool, optional

        Default is `True`. If `False`, converts the video to grayscale and sets every method in grayscale mode.
    - keep_all : bool, optional

        Default is `False`. If `True`, preserves an output video file after each used preprocessing stage.

    Outputs
    -------
    - A video file with the applied processes. The name of the file will be `filename` + a suffix for each process.

    Returns
    -------
    - length : int

        The number of frames in the output video file.

    - width : int

        The pixel width of the output video file. 
    - height : int

        The pixel height of the output video file. 
    - fps : int

        The FPS (frames per second) of the output video file.
    - endtime : float

        The length of the output video file in seconds.

    - of: str

        The path to the output video file without its extension.
        The file name gets a suffix for each used process.
    - fex : str

        The file extension of the output video file.
        Currently it is always 'avi'.
    """
    # Separate filename from file extension
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]

    trimming = False
    skipping = False
    rotating = False
    cbing = False
    cropping = False

    # Cut out relevant bit of video using starttime and endtime
    if starttime != 0 or endtime != 0:
        print("Trimming...", end='')
        extract_subclip(filename, starttime, endtime, targetname=of + '_trim' + fex)
        print(" done.")
        of = of + '_trim'
        trimming = True

    # Convert to avi if the input is not avi - necesarry for cv2 compatibility on all platforms
    if fex != '.avi':
        print("Converting from", fex, "to .avi...")
        convert_to_avi(of + fex)
        fex = '.avi'
        filename = of + fex

    vidcap = cv2.VideoCapture(of + fex)

    # Get props from vidcap
    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

    #test reading
    success, _ = vidcap.read()
    if fps == 0 or length == 0 or not success:
        raise ReadError(f"Could not open {filename}.")

    source_length_s = length / fps
    source_name = of + fex
    new_length_s = source_length_s
    dilation_ratio = 1
    need_to_embed_audio = False
    video_has_audio_track = has_audio(source_name)

    if skip != 0 or contrast != 0 or brightness != 0 or crop.lower() != 'none':
        if video_has_audio_track:
            source_audio = extract_wav(source_name)
            need_to_embed_audio = True

    # To skip ahead a few frames before the next sample set skip to a value above 0
    if skip != 0:
        vidcap, length, fps, width, height = mg_skip_frames(
            of, fex, vidcap, skip, fps, length, width, height)
        if not keep_all and trimming:
            os.remove(of + fex)
        of = of + '_skip'
        skipping = True
        new_length_s = length / fps
        dilation_ratio = source_length_s / new_length_s
        if keep_all:
            vidcap.release()
            if video_has_audio_track:
                embed_audio_in_video(source_audio, of + fex, dilation_ratio)

    # Overwrite the inputvalue for endtime not to cut the video at 0...
    if endtime == 0:
        endtime = length/fps

    if rotate != 0:
        vidcap.release()
        print(f"Rotating video by {rotate} degrees...", end='')
        rotate_video(of + fex, rotate)
        print(" done.")
        if not keep_all and (skipping or trimming):
            os.remove(of + fex)
        of = of + '_rot'
        rotating = True
        if keep_all and video_has_audio_track:
            embed_audio_in_video(source_audio, of + fex, dilation_ratio)

    # Apply contrast/brightness before the motion analysis
    if contrast != 0 or brightness != 0:
        if keep_all or rotating:
            vidcap = cv2.VideoCapture(of + fex)
        vidcap = mg_contrast_brightness(
            of, fex, vidcap, fps, length, width, height, contrast, brightness)
        if not keep_all and (rotating or skipping or trimming):
            os.remove(of + fex)
        of = of + '_cb'
        cbing = True
        if keep_all:
            vidcap.release()
            if video_has_audio_track:
                embed_audio_in_video(source_audio, of + fex, dilation_ratio)

    # Crops video either manually or automatically
    if crop.lower() != 'none':
        if keep_all:
            vidcap = cv2.VideoCapture(of + fex)
        [vidcap, width, height] = mg_cropvideo(
            fps, width, height, length, of, fex, crop, motion_box_thresh=0.1, motion_box_margin=1)
        if not keep_all and (cbing or rotating or skipping or trimming):
            os.remove(of + fex)
        of = of + '_crop'
        cropping = True
        if keep_all:
            vidcap.release()
            if video_has_audio_track:
                embed_audio_in_video(source_audio, of + fex, dilation_ratio)

    if color == False and returned_by_process == False:
        vidcap.release()
        print("Converting to grayscale...", end='')
        of_gray, fex = convert_to_grayscale(of + fex)
        print(" done.")
        if not keep_all and (cropping or cbing or rotating or skipping or trimming):
            os.remove(of + fex)
        of = of_gray

    if color == True or returned_by_process == True:
        vidcap.release()

    if need_to_embed_audio:
        embed_audio_in_video(source_audio, of + fex, dilation_ratio)
        os.remove(source_audio)

    return length, width, height, fps, endtime, of, fex, video_has_audio_track

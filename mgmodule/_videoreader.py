import cv2
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import numpy as np
from ._videoadjust import mg_contrast_brightness, mg_skip_frames
from ._cropvideo import *
from ._utils import convert_to_avi, extract_wav, embed_audio_in_video, convert_to_grayscale


class ReadError(Exception):
    """Base class for other exceptions"""
    pass


def mg_videoreader(filename, starttime=0, endtime=0, skip=0, contrast=0, brightness=0, crop='None', color=True, returned_by_process=False, keep_all=False):
    """
        Reads in a video file, and by input parameters user decide if it: trims the length, skips frames, applies contrast/brightness adjustments and/or crops image width/height.

        Arguments:
        ----------
        - filename (str): Name of input parameter video file.
        - starttime (float): Cut the video from this start time (min) to analyze what is relevant.
        - endtime (float): Cut the video at this end time (min) to analyze what is relevant.
        - skip (int): When proceeding to analyze next frame of video, this many frames are skipped.
        - contrast (float): Apply +/- 100 contrast to video
        - brightness (float): Apply +/- 100 brightness to video
        - crop (str): 'None', 'Auto' or 'Manual' to crop video.
        - keep_all (bool): If False, only the result of the final process in the chain is kept, if True all results are kept.

        Returns:
        --------
        - vidcap: cv2 video capture of edited video file
        - length, fps, width, height from vidcap
        - of: filename gets updated with the procedures it went through
    """
    # Separate filename from file extension
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]

    trimming = False
    skipping = False
    cbing = False
    cropping = False

    if fex != '.avi':
        print("Converting from", fex, "to .avi...")
        convert_to_avi(filename)
        fex = '.avi'
        filename = of + fex

    # Cut out relevant bit of video using starttime and endtime
    if starttime != 0 or endtime != 0:
        trimvideo = ffmpeg_extract_subclip(
            filename, starttime, endtime, targetname=of + '_trim' + fex)
        of = of + '_trim'
        trimming = True
        vidcap = cv2.VideoCapture(of+fex)

    # Or just use whole video
    else:
        vidcap = cv2.VideoCapture(of + fex)

    # Get props from vidcap
    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps == 0:
        raise ReadError(f"Could not open {filename}.")

    source_length_s = length / fps
    source_name = of + fex
    new_length_s = source_length_s
    dilation_ratio = 1
    need_to_embed_audio = False

    if skip != 0 or contrast != 0 or brightness != 0 or crop != 'None':
        source_audio = extract_wav(source_name)
        need_to_embed_audio = True

    # To skip ahead a few frames before the next sample set skip to a value above 0
    if skip != 0:
        vidcap, length, fps, width, height = mg_skip_frames(
            of, fex, vidcap, skip, fps, width, height)
        if not keep_all and trimming:
            os.remove(of + fex)
        of = of + '_skip'
        skipping = True
        new_length_s = length / fps
        dilation_ratio = source_length_s / new_length_s
        if keep_all:
            vidcap.release()
            embed_audio_in_video(source_audio, of + fex, dilation_ratio)

    # Overwrite the inputvalue for endtime not to cut the video at 0...
    if endtime == 0:
        endtime = length/fps

    # Apply contrast/brightness before the motion analysis
    if contrast != 0 or brightness != 0:
        if keep_all:
            vidcap = cv2.VideoCapture(of + fex)
        vidcap = mg_contrast_brightness(
            of, fex, vidcap, fps, length, width, height, contrast, brightness)
        if not keep_all and (skipping or trimming):
            os.remove(of + fex)
        of = of + '_cb'
        cbing = True
        if keep_all:
            vidcap.release()
            embed_audio_in_video(source_audio, of + fex, dilation_ratio)

    # Crops video either manually or automatically
    if crop != 'None':
        if keep_all:
            vidcap = cv2.VideoCapture(of + fex)
        [vidcap, width, height] = mg_cropvideo(
            fps, width, height, length, of, fex, crop, motion_box_thresh=0.1, motion_box_margin=1)
        if not keep_all and (cbing or skipping or trimming):
            os.remove(of + fex)
        of = of + '_crop'
        cropping = True
        if keep_all:
            vidcap.release()
            embed_audio_in_video(source_audio, of + fex, dilation_ratio)

    if color == False and returned_by_process == False:
        vidcap.release()
        print("Converting to grayscale!")
        of_gray, fex = convert_to_grayscale(of + fex)
        print("Now it's grayscale.")
        if not keep_all and (cbing or skipping or trimming or cropping):
            os.remove(of + fex)
        of = of_gray

    if color == True or returned_by_process == True:
        vidcap.release()

    if need_to_embed_audio:
        embed_audio_in_video(source_audio, of + fex, dilation_ratio)
        os.remove(source_audio)

    return length, width, height, fps, endtime, of, fex

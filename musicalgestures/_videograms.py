import cv2
import os
import numpy as np
from musicalgestures._utils import MgProgressbar, MgImage, get_widthheight, get_framecount, get_length, ffmpeg_cmd, generate_outfilename
from musicalgestures._mglist import MgList
from musicalgestures._videoadjust import skip_frames_ffmpeg
import math


def videograms_ffmpeg(self, target_name_x=None, target_name_y=None, overwrite=False):
    """
    Renders horizontal and vertical videograms of the source video using ffmpeg. Averages videoframes by axes, 
    and creates two images of the horizontal-axis and vertical-axis stacks. In these stacks, a single row or 
    column corresponds to a frame from the source video, and the index of the row or column corresponds to 
    the index of the source frame.

    Args:
        target_name_x (str, optional): Target output name for the videogram on the X axis. Defaults to None (which assumes that the input filename with the suffix "_vgx" should be used).
        target_name_y (str, optional): Target output name for the videogram on the Y axis. Defaults to None (which assumes that the input filename with the suffix "_vgy" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgList: An MgList with the MgImage objects referring to the horizontal and vertical videograms respectively. 
    """

    width, height = get_widthheight(self.filename)
    framecount = get_framecount(self.filename)

    def calc_skipfactor(width, height, framecount):
        """
        Helper function to calculate the necessary frame-skipping to avoid integer overflow. This makes sure that we can succesfully create videograms even on many-hours-long videos as well.

        Args:
            width (int): The width of the video.
            height (int): The height of the video.
            framecount (int): The number of frames in the video.

        Returns:
            list(int, int): The necessary dilation factors to apply on the video for the horizontal and vertical videograms, respectively.
        """

        intmax = 2147483647
        skipfactor_x = int(
            math.ceil(framecount*8 / (intmax / (height+128) - 1024)))
        skipfactor_y = int(
            math.ceil(framecount / (intmax / ((width*8)+1024) - 128)))
        return skipfactor_x, skipfactor_y

    testx, testy = calc_skipfactor(width, height, framecount)

    if testx > 1 or testy > 1:
        necessary_skipfactor = max([testx, testy])
        print(f'{os.path.basename(self.filename)} is too large to process. Applying minimal skipping necessary...')

        shortened_file = skip_frames_ffmpeg(self.filename, skip=necessary_skipfactor-1)
        skip_of = os.path.splitext(shortened_file)[0]
        framecount = get_framecount(shortened_file)
        length = get_length(shortened_file)

        if target_name_x == None:
            target_name_x = skip_of+'_vgx.png'
        if target_name_y == None:
            target_name_y = skip_of+'_vgy.png'
        if not overwrite:
            target_name_x = generate_outfilename(target_name_x)
            target_name_y = generate_outfilename(target_name_y)

        cmd = ['ffmpeg', '-y', '-i', shortened_file, '-vf',
               f'scale=1:{height}:sws_flags=area,normalize,tile={framecount}x1', '-aspect', f'{framecount}:{height}', '-frames', '1', target_name_y]
        ffmpeg_cmd(cmd, length, stream=False, pb_prefix="Rendering horizontal videogram:")

        cmd = ['ffmpeg', '-y', '-i', shortened_file, '-vf',
               f'scale={width}:1:sws_flags=area,normalize,tile=1x{framecount}', '-aspect', f'{width}:{framecount}', '-frames', '1', target_name_x]
        ffmpeg_cmd(cmd, length, stream=False, pb_prefix="Rendering vertical videogram:")

        # save results as MgImages at self.video_gram_x and self.video_gram_y for parent MgObject
        self.videogram_x = MgImage(target_name_x)
        self.videogram_y = MgImage(target_name_y)

        # return MgList([MgImage(target_name_x), MgImage(target_name_y)])
        return MgList(self.videogram_x, self.videogram_y)


    else:
        length = get_length(self.filename)

        if target_name_x == None:
            target_name_x = self.of +'_vgx.png'
        if target_name_y == None:
            target_name_y = self.of+'_vgy.png'
        if not overwrite:
            target_name_x = generate_outfilename(target_name_x)
            target_name_y = generate_outfilename(target_name_y)

        cmd = ['ffmpeg', '-y', '-i', self.filename, '-frames', '1', '-vf',
               f'scale=1:{height}:sws_flags=area,normalize,tile={framecount}x1', '-aspect', f'{framecount}:{height}', target_name_y]
        ffmpeg_cmd(cmd, length, stream=False, pb_prefix="Rendering horizontal videogram:")

        cmd = ['ffmpeg', '-y', '-i', self.filename, '-frames', '1', '-vf',
               f'scale={width}:1:sws_flags=area,normalize,tile=1x{framecount}', '-aspect', f'{width}:{framecount}', target_name_x]
        ffmpeg_cmd(cmd, length, stream=False, pb_prefix="Rendering vertical videogram:")

        # save results as MgImages at self.videogram_x and self.videogram_y for parent MgObject
        self.videogram_x = MgImage(target_name_x)
        self.videogram_y = MgImage(target_name_y)

        # return MgList([MgImage(target_name_x), MgImage(target_name_y)])
        return MgList(self.videogram_x, self.videogram_y)

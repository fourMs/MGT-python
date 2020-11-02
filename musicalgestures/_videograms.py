import cv2
import os
import numpy as np
from musicalgestures._utils import MgProgressbar, MgImage, get_widthheight, get_framecount, get_length, ffmpeg_cmd
from musicalgestures._mglist import MgList
from musicalgestures._videoadjust import skip_frames_ffmpeg
import math


def videograms_ffmpeg(self):
    """
    Renders horizontal and vertical videograms of the source video using ffmpeg. Averages videoframes by axes, and creates two images of the horizontal-axis and vertical-axis stacks. In these stacks, a single row or column corresponds to a frame from the source video, and the index of the row or column corresponds to the index of the source frame.

    Outputs:
        `self.filename`_vgx.png
        `self.filename`_vgy.png

    Returns:
        MgList(MgImage, MgImage): An MgList with the MgImage objects referring to the horizontal and vertical videograms respectively. 
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

        skip_frames_ffmpeg(self.filename, skip=necessary_skipfactor-1)

        shortened_file = self.of + '_skip' + self.fex
        framecount = get_framecount(shortened_file)
        length = get_length(shortened_file)

        outname = self.of + '_skip_vgy.png'
        cmd = ['ffmpeg', '-y', '-i', shortened_file, '-frames', '1', '-vf',
               f'scale=1:{height}:sws_flags=area,normalize,tile={framecount}x1', '-aspect', f'{framecount}:{height}', outname]
        ffmpeg_cmd(cmd, length, pb_prefix="Rendering horizontal videogram:")

        outname = self.of + '_skip_vgx.png'
        cmd = ['ffmpeg', '-y', '-i', shortened_file, '-frames', '1', '-vf',
               f'scale={width}:1:sws_flags=area,normalize,tile=1x{framecount}', '-aspect', f'{width}:{framecount}', outname]
        ffmpeg_cmd(cmd, length, pb_prefix="Rendering vertical videogram:")

        return MgList([MgImage(self.of+'_skip_vgx.png'), MgImage(self.of+'_skip_vgy.png')])

    else:
        length = get_length(self.filename)

        outname = self.of + '_vgy.png'
        cmd = ['ffmpeg', '-y', '-i', self.filename, '-frames', '1', '-vf',
               f'scale=1:{height}:sws_flags=area,normalize,tile={framecount}x1', '-aspect', f'{framecount}:{height}', outname]
        ffmpeg_cmd(cmd, length, pb_prefix="Rendering horizontal videogram:")

        outname = self.of + '_vgx.png'
        cmd = ['ffmpeg', '-y', '-i', self.filename, '-frames', '1', '-vf',
               f'scale={width}:1:sws_flags=area,normalize,tile=1x{framecount}', '-aspect', f'{width}:{framecount}', outname]
        ffmpeg_cmd(cmd, length, pb_prefix="Rendering vertical videogram:")

        return MgList([MgImage(self.of+'_vgx.png'), MgImage(self.of+'_vgy.png')])

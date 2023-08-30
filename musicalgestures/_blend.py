import numpy as np
import os, subprocess

from musicalgestures._utils import MgImage, generate_outfilename, get_framecount, get_length, ffmpeg_cmd


def mg_blend_image(self, filename=None, mode='all_mode', component_mode='average', target_name=None, overwrite=False):
    """
    Finds and saves a blended image of an input video file using FFmpeg. 
    The FFmpeg tblend (time blend) filter takes two consecutive frames from one single stream, and outputs the result obtained by blending the new frame on top of the old frame.

    Args:
        filename (str, optional): Path to the input video file. If None, the video file of the MgObject is used. Defaults to None.
        mode (str, optional): Set blend mode for specific pixel component or all pixel components. Accepted options are 'c0_mode', 'c1_mode', c2_mode', 'c3_mode' and 'all_mode'. Defaults to 'all_mode'. 
        component_mode (str, optional): Component mode of the FFmpeg tblend. Available values for component modes can be accessed here: https://ffmpeg.org/ffmpeg-filters.html#blend-1. Defaults to 'average'.
        target_name (str, optional): The name of the output video. Defaults to None (which assumes that the input filename with the component mode suffix should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgImage: A new MgImage pointing to the output image file.
    """

    if filename == None:
        filename = self.filename

    of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of + f'_{component_mode}.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    # Get the number of frames
    frames = get_framecount(filename)
    # Get the number of times all frames can be divided
    divider = int(np.ceil(np.log(frames / 2) / np.log(2)))

    # Set average blur
    if self.blur.lower() == 'average':
        cmd_filter += 'avgblur=sizeX=10:sizeY=10,'

    # Define ffmpeg command
    cmd = ['ffmpeg', '-y', '-i', self.filename]

    cmd_filter = ''
    # set color mode
    if self.color == True:
        pixformat = 'gbrp'
    else:
        pixformat = 'gray'
    cmd_filter += f'format={pixformat},'

    # Set frame blend every two frames
    cmd_filter += f'tblend={mode}={component_mode},framestep=2,' * divider + 'setpts=1*PTS'
    cmd_end = ['-frames:v', '1', target_name]
    cmd += ['-vf', cmd_filter] + cmd_end

    # Run the command using ffmpeg and wait for it to finish
    ffmpeg_cmd(cmd, get_length(self.filename), pb_prefix='Rendering blended image:')
 
    # Save result as the blended image for parent MgObject
    self.blend_image = MgImage(target_name)

    return self.blend_image

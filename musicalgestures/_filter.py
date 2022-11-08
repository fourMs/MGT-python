from scipy.signal import medfilt2d
import cv2
import numpy as np
import matplotlib
from musicalgestures._utils import get_widthheight


def filter_frame(motion_frame, filtertype, thresh, kernel_size):
    """
    Applies a threshold filter and then a median filter (of `kernel_size`x`kernel_size`) to an image or videoframe.

    Args:
        motion_frame (np.array(uint8)): Input motion image.
        filtertype (str): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method.
        thresh (float): A number in the range of 0 to 1. Eliminates pixel values less than given threshold.
        kernel_size (int): Size of structuring element.

    Returns:
        np.array(uint8): The filtered frame.
    """

    if filtertype.lower() == 'regular':
        motion_frame = (motion_frame > thresh*255)*motion_frame
        motion_frame = medfilt2d(motion_frame, kernel_size)
    elif filtertype.lower() == 'binary':
        motion_frame = (motion_frame > thresh*255)*255
        motion_frame = medfilt2d(motion_frame.astype(np.uint8), kernel_size)
    elif filtertype.lower() == 'blob':
        motion_frame = cv2.erode(motion_frame, np.ones([kernel_size, kernel_size]), iterations=1)
    return motion_frame

def filter_frame_ffmpeg(filename, cmd, color, blur, filtertype, threshold, kernel_size, use_median, invert=False):

    cmd_filter = ''

    # set color mode
    if color == True:
        pixformat = 'gbrp'
    else:
        pixformat = 'gray'
    cmd_filter += f'format={pixformat},'

    # set blur
    if blur.lower() == 'average':
        cmd_filter += 'avgblur=sizeX=10:sizeY=10,'

    # set frame difference
    if filtertype.lower() == 'regular':
        cmd_filter += 'tblend=all_mode=difference[diff],'
    else:
        cmd_filter += 'tblend=all_mode=difference,'

    width, height = get_widthheight(filename)

    thresh_color = matplotlib.colors.to_hex([threshold, threshold, threshold])
    thresh_color = '0x' + thresh_color[1:]

    # set threshold
    if filtertype.lower() == 'regular':
        cmd += ['-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}',
                '-f', 'lavfi', '-i', f'color=black,scale={width}:{height}']
        cmd_filter += '[0:v][1][2][diff]threshold,'
    elif filtertype.lower() == 'binary':
        cmd += ['-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', '-f', 'lavfi', '-i',
                f'color=black,scale={width}:{height}', '-f', 'lavfi', '-i', f'color=white,scale={width}:{height}']
        cmd_filter += 'threshold,'
    elif filtertype.lower() == 'blob':
        # cmd_filter += 'erosion,' # erosion is always 3x3 so we will hack it with a median filter with percentile=0 which will pick minimum values
        cmd_filter += f'median=radius={kernel_size}:percentile=0,'

    # set median
    if use_median and filtertype.lower() != 'blob':  # makes no sense to median-filter the eroded video
        cmd_filter += f'median=radius={kernel_size},'

    if invert:
        cmd_filter += 'negate,'
    
    return cmd, cmd_filter
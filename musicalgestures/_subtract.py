
import os
import matplotlib

import musicalgestures
from musicalgestures._utils import generate_outfilename, pass_if_container_is, get_length, ffmpeg_cmd

def mg_subtract(
        self,
        color=True,
        filtertype=None,
        threshold=0.05,
        blur=False,
        curves=0.15,
        use_median=False,
        kernel_size=5,
        bg_img=None,
        bg_color='#000000',
        target_name=None,
        overwrite=False):
    """
    Renders background subtraction using ffmpeg. 

    Args:
        color (bool, optional): If False the input is converted to grayscale at the start of the process. This can significantly reduce render time. Defaults to True.
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        threshold (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (bool, optional): Whether to apply a smartblur ffmpeg filter or not. Defaults to False.
        curves (int, optional): Apply curves and equalisation threshold filter to subtract the background. Ranges from 0 to 1. Defaults to 0.15.
        use_median (bool, optional): If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
        kernel_size (int, optional): Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
        bg_img (str, optional): Path to a background image (.png) that needs to be subtracted from the video. If set to None, it uses an average image of all frames in the video. Defaults to None.
        bg_color (str, optional): Set the background color in the video file in hex value. Defaults to '#000000' (black). 
        target_name (str, optional): Target output name for the motiongram. Defaults to None.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgVideo: A MgVideo as subtract for parent MgVideo
    """

    of, fex = os.path.splitext(self.filename)

    if target_name == None:
        target_name = of + '_subtracted.avi'

    if not overwrite:
        target_name = generate_outfilename(target_name)
    
    width, height = self.width, self.height

    if bg_img == None:
        # Render an average image of the video file for background subtraction
        bg_img = musicalgestures.MgVideo(self.filename).blend(component_mode='average').filename
    else:
        # Check if background image extension is .png or not
        pass_if_container_is(".png", bg_img)

    # Set input/output and background color to white
    cmd = ['ffmpeg', '-y', '-i', bg_img, '-i', self.filename]
    cmd_end = ['-shortest', '-pix_fmt', 'yuv420p', target_name]
    cmd_filter = f'color={bg_color}:size={width}x{height} [matte];[1:0]'

    # Set color mode
    if color == True:
        pixformat = 'gbrp'
    else:
        pixformat = 'gray'

    cmd_filter += f'format={pixformat}, split[mask][video];[0:0][mask]'

    # Set frame difference
    if filtertype is not None:
        if filtertype.lower() == 'regular':
            cmd_filter += 'blend=all_mode=difference[diff],'
        else:
            cmd_filter += 'blend=all_mode=difference,'
    else:
        cmd_filter += 'blend=all_mode=difference,'

    thresh_color = matplotlib.colors.to_hex([threshold, threshold, threshold])
    thresh_color = '0x' + thresh_color[1:]

    # Set threshold
    if filtertype is not None:
        if filtertype.lower() == 'regular':
            cmd += ['-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', 
                    '-f', 'lavfi', '-i', f'color=black,scale={width}:{height}']
            cmd_filter += '[1][diff]threshold,'
        elif filtertype.lower() == 'binary':
            cmd += ['-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', '-f', 'lavfi', '-i',
                    f'color=black,scale={width}:{height}', '-f', 'lavfi', '-i', f'color=white,scale={width}:{height}']
            cmd_filter += ' threshold,'
        elif filtertype.lower() == 'blob':
            # cmd_filter += 'erosion,' # erosion is always 3x3 so we will hack it with a median filter with percentile=0 which will pick minimum values
            cmd_filter += f'median=radius={kernel_size}:percentile=0,'       

    # Set median
    if use_median and filtertype.lower() != 'blob':  # makes no sense to median-filter the eroded video
        cmd_filter += f'median=radius={kernel_size},'

    # Set curves and equalisation filtering to a range of values between 0.1 and 0.9 
    new_curves = (((curves - 0) * (0.8 - 0.1)) / (1 - 0)) + 0.1
    cmd_filter += f"curves=m='0/0 {str(round(new_curves,2))}/0 {str(round(new_curves+0.1,2))}/1 1/1',"
    
    # Set blur
    if blur:
        cmd_filter += 'format=gray,smartblur=1,smartblur=3,'

    cmd_filter += f'format=gray [mask];[matte][video][mask] maskedmerge, format={pixformat}' 
    cmd_filter = ['-filter_complex', cmd_filter]  
    cmd = cmd + cmd_filter + cmd_end

    ffmpeg_cmd(cmd, get_length(self.filename), pb_prefix='Subtracting background:', stream=True)

    # Save subtracted video as subtract for parent MgVideo
    self.subtract = musicalgestures.MgVideo(target_name, color=color, returned_by_process=True)

    return self.subtract

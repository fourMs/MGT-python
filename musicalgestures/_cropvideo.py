import cv2
import os
import numpy as np
import time
import asyncio
from musicalgestures._utils import MgProgressbar, get_length, get_widthheight, get_first_frame_as_image, get_screen_resolution_scaled, get_screen_video_ratio, roundup, crop_ffmpeg, wrap_str, unwrap_str
from musicalgestures._filter import filter_frame


def find_motion_box_ffmpeg(filename, motion_box_thresh=0.1, motion_box_margin=12):
    """
    Helper function to find the area of motion in a video, using ffmpeg.

    Args:
        filename (str): Path to the video file.
        motion_box_thresh (float, optional): Pixel threshold to apply to the video before assessing the area of motion. Defaults to 0.1.
        motion_box_margin (int, optional): Margin (in pixels) to add to the detected motion box. Defaults to 12.

    Raises:
        KeyboardInterrupt: In case we stop the process manually.

    Returns:
        int: The width of the motion box.
        int: The height of the motion box.
        int: The X coordinate of the top left corner of the motion box.
        int: The Y coordinate of the top left corner of the motion box.
    """

    import subprocess
    import os
    import matplotlib
    import numpy as np
    total_time = get_length(filename)
    width, height = get_widthheight(filename)
    crop_str = ''

    thresh_color = matplotlib.colors.to_hex(
        [motion_box_thresh, motion_box_thresh, motion_box_thresh])
    thresh_color = '0x' + thresh_color[1:]

    pb = MgProgressbar(total=total_time, prefix='Finding area of motion:')

    command = ['ffmpeg', '-y', '-i', filename, '-f', 'lavfi', '-i', f'color={thresh_color},scale={width}:{height}', '-f', 'lavfi', '-i', f'color=black,scale={width}:{height}', '-f',
               'lavfi', '-i', f'color=white,scale={width}:{height}', '-lavfi', 'format=gray,tblend=all_mode=difference,threshold,cropdetect=round=2:limit=0:reset=0', '-f', 'null', '/dev/null']

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    try:
        while True:
            out = process.stdout.readline()
            if out == '':
                process.wait()
                break
            else:
                out_list = out.split()
                crop_and_time = sorted(
                    [elem for elem in out_list if elem.startswith('t:') or elem.startswith('crop=')])
                if len(crop_and_time) != 0:
                    crop_str = crop_and_time[0]
                    time_float = float(crop_and_time[1][2:])
                    pb.progress(time_float)

        pb.progress(total_time)

        crop_width, crop_height, crop_x, crop_y = [
            int(elem) for elem in crop_str[5:].split(':')]

        motion_box_margin = roundup(motion_box_margin, 4)

        crop_width = np.clip(crop_width+motion_box_margin, 4, width)
        crop_height = np.clip(crop_height+motion_box_margin, 4, height)
        crop_x = np.clip(crop_x-(motion_box_margin/2), 4, width)
        crop_y = np.clip(crop_y-(motion_box_margin/2), 4, height)

        if crop_x + crop_width > width:
            crop_x = width - crop_width
        else:
            crop_x = np.clip(crop_x, 0, width)
        if crop_y + crop_height > height:
            crop_y = height - crop_height
        else:
            crop_y = np.clip(crop_y, 0, height)

        crop_width, crop_height, crop_x, crop_y = [
            int(elem) for elem in [crop_width, crop_height, crop_x, crop_y]]

        return crop_width, crop_height, crop_x, crop_y

    except KeyboardInterrupt:
        try:
            process.terminate()
        except OSError:
            pass
        process.wait()
        raise KeyboardInterrupt


def mg_cropvideo_ffmpeg(
        filename,
        crop_movement='Auto',
        motion_box_thresh=0.1,
        motion_box_margin=12):
    """
    Crops the video using ffmpeg.

    Args:
        filename (str): Path to the video file.
        crop_movement (str, optional): 'Auto' finds the bounding box that contains the total motion in the video. Motion threshold is given by motion_box_thresh. 'Manual' opens up a simple GUI that is used to crop the video manually by looking at the first frame. Defaults to 'Auto'.
        motion_box_thresh (float, optional): Only meaningful if `crop_movement='Auto'`. Takes floats between 0 and 1, where 0 includes all the motion and 1 includes none. Defaults to 0.1.
        motion_box_margin (int, optional): Only meaningful if `crop_movement='Auto'`. Adds margin to the bounding box. Defaults to 12.

    Returns:
        str: Path to the cropped video.
    """

    global w, h, x, y

    pb = MgProgressbar(total=get_length(filename),
                       prefix='Rendering cropped video:')

    if crop_movement.lower() == 'manual':

        scale_ratio = get_screen_video_ratio(filename)
        width, height = get_widthheight(filename)
        scaled_width, scaled_height = [
            int(elem * scale_ratio) for elem in [width, height]]
        first_frame_as_image = get_first_frame_as_image(
            filename, pict_format='.jpg')

        # Cropping UI moved to another subprocess to avoid cv2.waitKey crashing Python with segmentation fault on Linux in Terminal
        import threading
        x = threading.Thread(target=run_cropping_window, args=(
            first_frame_as_image, scale_ratio, scaled_width, scaled_height))
        # run_cropping_window(first_frame_as_image, scale_ratio, scaled_width, scaled_height)
        x.start()
        x.join()

    elif crop_movement.lower() == 'auto':
        w, h, x, y = find_motion_box_ffmpeg(
            filename, motion_box_thresh=motion_box_thresh, motion_box_margin=motion_box_margin)

    cropped_video = crop_ffmpeg(filename, w, h, x, y)

    if crop_movement.lower() == 'manual':
        cv2.destroyAllWindows()
        os.remove(first_frame_as_image)

    return cropped_video


async def async_subprocess(command):

    global w, h, x, y

    process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await process.communicate()

    # print(f'[{command} exited with {process.returncode}]')
    if stdout:
        res = stdout.decode()
        res_array = res.split(' ')
        res_array_int = [int(elem) for elem in res_array]
        w, h, x, y = res_array_int
        # print(f'[stdout]\n{stdout.decode()}')

    if stderr:
        print(f'[stderr]\n{stderr.decode()}')


def run_cropping_window(imgpath, scale_ratio, scaled_width, scaled_height):

    import platform
    import musicalgestures
    import os
    module_path = os.path.abspath(os.path.dirname(musicalgestures.__file__))
    the_system = platform.system()
    pythonkw = "python"
    if the_system != "Windows":
        pythonkw += "3"
    pyfile = wrap_str(module_path + '/_cropping_window.py')
    imgpath = wrap_str(imgpath)

    command = f'{pythonkw} {pyfile} {imgpath} {scale_ratio} {scaled_width} {scaled_height}'

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # if cleanup: 'RuntimeError: There is no current event loop..'
        loop = None
    if loop and loop.is_running():
        tsk = loop.create_task(async_subprocess(command))
    else:
        asyncio.run(async_subprocess(command))

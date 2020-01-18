import numpy as np
import cv2
from ._utils import mg_progressbar, scale_num, scale_array


def mg_contrast_brightness(of, fex, vidcap, fps, length, width, height, contrast, brightness):
    """
    Edit contrast and brightness of the video.

    Arguments
    ---------
    - of (str): 'Only filename' without extension.
    - fex (str): File extension.
    - vidcap: cv2 capture of video file, with all frames ready to be read with vidcap.read().
    - fps, width, height (int): Properties of vidcap, passed by parent function.
    - contrast (float): Apply +/- 100 contrast to video.
    - brightness (float): Apply +/- 100 brightness to video.

    Returns
    -------
    - cv2 video capture of edited video file.
    """

    count = 0
    if brightness != 0 or contrast != 0:
        # keeping values in sensible range
        contrast = np.clip(contrast, -100.0, 100.0)
        brightness = np.clip(brightness, -100.0, 100.0)

        contrast *= 1.27
        brightness *= 2.55

        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_cb' + fex, fourcc, fps, (width, height))
        success, image = vidcap.read()
        while success:
            success, image = vidcap.read()
            if not success:
                #print('Adjusting contrast/brightness 100%%')
                mg_progressbar(
                    length, length, 'Adjusting contrast and brightness:', 'Complete')
                break
            image = np.int16(image) * (contrast/127+1) - contrast + brightness
            image = np.clip(image, 0, 255)
            out.write(image.astype(np.uint8))
            count += 1
            # print('Adjusting contrast/brightness %s%%' %
            #       (int(count/(length-1)*100)), end='\r')
            mg_progressbar(
                count, length, 'Adjusting contrast and brightness:', 'Complete')
        out.release()
        vidcap = cv2.VideoCapture(of + '_cb' + fex)

    return vidcap


def mg_skip_frames(of, fex, vidcap, skip, fps, width, height):
    """
    Frame skip, convenient for saving time/space in an analysis of less detail looking at big picture movement. Skips the given number of frames, making a compressed version of the input video file.

    Arguments
    ---------
    - of (str): 'Only filename' without extension.
    - fex (str): File extension.
    - vidcap: cv2 capture of video file, with all frames ready to be read with vidcap.read().
    - skip (int): When proceeding to analyze next frame of video, this many frames are skipped.
    - fps, width, height (int): Properties of vidcap, passed by parent function.

    Returns
    -------
    - cv2 video capture of edited video file.
    - length, fps, width, height from this video capture.
    """
    count = 0
    if skip != 0:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_skip' + fex, fourcc,
                              int(fps), (width, height))  # don't change fps, with higher skip values we want shorter videos
        success, image = vidcap.read()
        while success:
            success, image = vidcap.read()
            if not success:
                break
            # on every frame we wish to use
            if (count % (skip+1) == 0):  # NB if skip=1, we should keep every other frame
                out.write(image.astype(np.uint8))

            count += 1
        out.release()
        vidcap = cv2.VideoCapture(of + '_skip' + fex)

        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return vidcap, length, fps, width, height

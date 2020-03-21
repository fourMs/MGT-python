import numpy as np
import cv2
from ._utils import mg_progressbar, scale_num, scale_array


def mg_contrast_brightness(of, fex, vidcap, fps, length, width, height, contrast, brightness):
    """
    Applies contrast and brightness to a video.

    Parameters
    ----------
    - of : str

        'Only filename' without extension (but with path to the file).
    - fex : str

        File extension.
    - vidcap : 

        cv2 capture of video file, with all frames ready to be read with `vidcap.read()`.
    - fps : int

        The FPS (frames per second) of the input video capture.
    - length : int

        The number of frames in the input video capture.
    - width : int

        The pixel width of the input video capture. 
    - height : int

        The pixel height of the input video capture. 
    - contrast : int or float, optional

        Applies +/- 100 contrast to video.
    - brightness : int or float, optional

        Applies +/- 100 brightness to video.

    Outputs
    -------
    - A video file with the name `of` + '_cb' + `fex`.

    Returns
    -------
    - cv2 video capture of output video file.
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
                mg_progressbar(
                    length, length, 'Adjusting contrast and brightness:', 'Complete')
                break
            image = np.int16(image) * (contrast/127+1) - contrast + brightness
            image = np.clip(image, 0, 255)
            out.write(image.astype(np.uint8))
            count += 1
            mg_progressbar(
                count, length, 'Adjusting contrast and brightness:', 'Complete')
        out.release()
        vidcap = cv2.VideoCapture(of + '_cb' + fex)

    return vidcap


def mg_skip_frames(of, fex, vidcap, skip, fps, length, width, height):
    """
    Time-shrinks the video by skipping (discarding) every n frames determined by `skip`.

    Parameters
    ----------
    - of : str

        'Only filename' without extension (but with path to the file).
    - fex : str

        File extension.
    - vidcap : 

        cv2 capture of video file, with all frames ready to be read with `vidcap.read()`.
    - skip : int

        Every n frames to discard. `skip=0` keeps all frames, `skip=1` skips every other frame.
    - fps : int

        The FPS (frames per second) of the input video capture.
    - length : int

        The number of frames in the input video capture.
    - width : int

        The pixel width of the input video capture. 
    - height : int

        The pixel height of the input video capture.

    Outputs
    -------
    - A video file with the name `of` + '_skip' + `fex`.

    Returns
    -------
    - videcap :

        cv2 video capture of output video file.
    - length : int

        The number of frames in the output video file.
    - fps : int

        The FPS (frames per second) of the output video file.
    - width : int

        The pixel width of the output video file. 
    - height : int

        The pixel height of the output video file. 
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
                mg_progressbar(
                    length, length, 'Skipping frames:', 'Complete')
                break
            # on every frame we wish to use
            if (count % (skip+1) == 0):  # NB if skip=1, we should keep every other frame
                out.write(image.astype(np.uint8))
            count += 1
            mg_progressbar(
                count, length, 'Skipping frames:', 'Complete')
        out.release()
        vidcap = cv2.VideoCapture(of + '_skip' + fex)

        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return vidcap, length, fps, width, height

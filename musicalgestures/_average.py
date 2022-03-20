import cv2
import numpy as np
import os

from musicalgestures._utils import MgImage, MgProgressbar, convert_to_avi, generate_outfilename


def mg_average_image(self, filename=None, normalize=True, target_name=None, overwrite=False):
    """
    Finds and saves an average image of an input video file.

    Args:
        filename (str, optional): Path to the input video file. If None, the video file of the MgObject is used. Defaults to None.
        normalize (bool, optional): If True, normalizes pixel values in the output image. Defaults to True.
        target_name (str, optional): The name of the output video. Defaults to None (which assumes that the input filename with the suffix "_average" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgImage: A new MgImage pointing to the output image file.
    """

    if filename == None:
        filename = self.filename

    of, fex = os.path.splitext(filename)

    # Convert to avi if the input is not avi - necesarry for cv2 compatibility on all platforms
    if fex != '.avi':
        filename = convert_to_avi(of + fex, overwrite=overwrite)
        of, fex = os.path.splitext(filename)

    if target_name == None:
        target_name = of+'_average.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    video = cv2.VideoCapture(filename)
    ret, frame = video.read()
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    if self.color == False:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    average = frame.astype(np.float)/length
    pb = MgProgressbar(total=length, prefix='Rendering average image:')
    ii = 0
    while(video.isOpened()):
        ret, frame = video.read()
        if ret == True:
            if self.color == False:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = np.array(frame)
            frame = frame.astype(np.float)
            average += frame/length
        else:
            pb.progress(length)
            break
        pb.progress(ii)
        ii += 1

    if self.color == False:
        average = cv2.cvtColor(average.astype(np.uint8), cv2.COLOR_GRAY2BGR)

    if normalize:
        average = average.astype(np.uint8)
        norm_average = np.zeros_like(average)
        norm_average = cv2.normalize(
            average,  norm_average, 0, 255, cv2.NORM_MINMAX)
        cv2.imwrite(target_name, norm_average.astype(np.uint8))

    else:
        cv2.imwrite(target_name, average.astype(np.uint8))

    # save result as the average_image for parent MgObject
    self.average_image = MgImage(target_name)

    return self.average_image

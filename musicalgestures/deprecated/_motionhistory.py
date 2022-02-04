import cv2
import os
import numpy as np
from scipy.signal import medfilt2d
from musicalgestures._centroid import centroid
from musicalgestures._filter import filter_frame
from musicalgestures._utils import mg_progressbar, extract_wav, embed_audio_in_video
import musicalgestures


def mg_motionhistory(
        self,
        history_length=10,
        kernel_size=5,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        inverted_motionhistory=False):
    """
    Finds the difference in pixel value from one frame to the next in an input video, 
    and saves the difference frame to a history tail. The history frames are summed up 
    and normalized, and added to the current difference frame to show the history of 
    motion. 

    Parameters
    ----------
    - history_length : int, optional

        Default is 10. Number of frames to be saved in the history tail.
    - kernel_size : int, optional

        Default is 5. Size of structuring element.
    - filtertype : {'Regular', 'Binary', 'Blob'}, optional

        `Regular` turns all values below `thresh` to 0.
        `Binary` turns all values below `thresh` to 0, above `thresh` to 1.
        `Blob` removes individual pixels with erosion method.
    - thresh : float, optional

        A number in the range of 0 to 1. Default is 0.05.
        Eliminates pixel values less than given threshold.
    - blur : {'None', 'Average'}, optional

        `Average` to apply a 10px * 10px blurring filter, `None` otherwise.
    - inverted_motionhistory : bool, optional

        Default is `False`. If `True`, inverts colors of the motionhistory video.

    Outputs
    -------
    - `filename`_motionhistory.avi

    Returns
    -------
    - MgVideo

        A new MgVideo pointing to the output '_motionhistory' video file.
    """
    enhancement = 1  # This can be adjusted to higher number to make motion more visible. Use with caution to not make it overflow.
    self.filtertype = filtertype
    self.thresh = thresh
    self.blur = blur

    vidcap = cv2.VideoCapture(self.of+self.fex)
    ret, frame = vidcap.read()
    #of = os.path.splitext(self.filename)[0]
    fex = os.path.splitext(self.filename)[1]
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(self.of + '_motionhistory' + fex,
                          fourcc, self.fps, (self.width, self.height))

    ii = 0
    history = []

    if self.color == False:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    while(vidcap.isOpened()):
        if self.blur.lower() == 'average':
            prev_frame = cv2.blur(frame, (10, 10))
        elif self.blur.lower() == 'none':
            prev_frame = frame

        ret, frame = vidcap.read()

        if ret == True:
            if self.blur.lower() == 'average':
                # The higher these numbers the more blur you get
                frame = cv2.blur(frame, (10, 10))

            if self.color == False:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame = (np.array(frame)).astype(np.float64)

            if self.color == True:
                motion_frame_rgb = np.zeros([self.height, self.width, 3])
                for i in range(frame.shape[2]):
                    motion_frame = (
                        np.abs(frame[:, :, i]-prev_frame[:, :, i])).astype(np.float64)
                    motion_frame = filter_frame(
                        motion_frame, self.filtertype, self.thresh, kernel_size)
                    motion_frame_rgb[:, :, i] = motion_frame

                if len(history) > 0:
                    motion_history = motion_frame_rgb/(len(history)+1)
                else:
                    motion_history = motion_frame_rgb

                for newframe in history:
                    motion_history += newframe/(len(history)+1)
                # or however long history you would like
                if len(history) > history_length or len(history) == history_length:
                    history.pop(0)  # pop first frame
                history.append(motion_frame_rgb)
                motion_history = motion_history.astype(
                    np.uint64)  # 0.5 to not overload it poor thing

            else:  # self.color = False
                motion_frame = (np.abs(frame-prev_frame)
                                ).astype(np.float64)
                motion_frame = filter_frame(
                    motion_frame, self.filtertype, self.thresh, kernel_size)
                if len(history) > 0:
                    motion_history = motion_frame/(len(history)+1)
                else:
                    motion_history = motion_frame

                for newframe in history:
                    motion_history += newframe/(len(history)+1)

                # or however long history you would like
                if len(history) > history_length or len(history) == history_length:
                    history.pop(0)  # pop first frame

                history.append(motion_frame)
                motion_history = motion_history.astype(np.uint64)

            if self.color == False:
                motion_history_rgb = cv2.cvtColor(
                    motion_history.astype(np.uint8), cv2.COLOR_GRAY2BGR)
            else:
                motion_history_rgb = motion_history
            if inverted_motionhistory:
                out.write(cv2.bitwise_not(
                    enhancement*motion_history_rgb.astype(np.uint8)))
            else:
                out.write(enhancement*motion_history_rgb.astype(np.uint8))
        else:
            mg_progressbar(self.length, self.length,
                           'Rendering motion history video:', 'Complete')
            break
        ii += 1
        mg_progressbar(ii, self.length,
                       'Rendering motion history video:', 'Complete')

    out.release()
    source_audio = extract_wav(self.of + self.fex)
    destination_video = self.of + '_motionhistory' + self.fex
    embed_audio_in_video(source_audio, destination_video)
    os.remove(source_audio)

    return musicalgestures.MgVideo(destination_video, color=self.color, returned_by_process=True)

import cv2
import os
import numpy as np
from musicalgestures._utils import extract_wav, embed_audio_in_video, MgProgressbar
import musicalgestures


def history(self, filename='', history_length=10):
    """
    This function  creates a video where each frame is the average of the 
    n previous frames, where n is determined by `history_length`.
    The history frames are summed up and normalized, and added to the 
    current frame to show the history. 

    Parameters
    ----------
    - filename : str, optional

        Path to the input video file. If not specified the video file pointed to by the MgObject is used.
    - history_length : int, optional

        Default is 10. Number of frames to be saved in the history tail.

    Outputs
    -------
    - `filename`_history.avi

    Returns
    -------
    - MgObject 
        A new MgObject pointing to the output '_history' video file.
    """

    if filename == '':
        filename = self.filename

    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    video = cv2.VideoCapture(filename)
    ret, frame = video.read()
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')

    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    pb = MgProgressbar(total=length, prefix='Rendering history video:')

    out = cv2.VideoWriter(of + '_history' + fex, fourcc, fps, (width, height))

    ii = 0
    history = []

    while(video.isOpened()):
        ret, frame = video.read()
        if ret == True:
            if self.color == False:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame = (np.array(frame)).astype(np.float64)

            if len(history) > 0:
                history_total = frame/(len(history)+1)
            else:
                history_total = frame
            for newframe in history:
                history_total += newframe/(len(history)+1)
            # or however long history you would like
            if len(history) > history_length or len(history) == history_length:
                history.pop(0)  # pop first frame
            history.append(frame)
            # 0.5 to not overload it poor thing
            total = history_total.astype(np.uint64)

            if self.color == False:
                total = cv2.cvtColor(total.astype(
                    np.uint8), cv2.COLOR_GRAY2BGR)
                out.write(total)
            else:
                out.write(total.astype(np.uint8))

        else:
            pb.progress(length)
            # mg_progressbar(
            #     length, length, 'Rendering history video:', 'Complete')
            break

        pb.progress(ii)
        ii += 1
        # mg_progressbar(ii, length+1, 'Rendering history video:', 'Complete')

    out.release()
    
    destination_video = self.of + '_history' + self.fex

    if self.has_audio:
        source_audio = extract_wav(self.of + self.fex)
        embed_audio_in_video(source_audio, destination_video)
        os.remove(source_audio)

    return musicalgestures.MgObject(destination_video, color=self.color, returned_by_process=True)

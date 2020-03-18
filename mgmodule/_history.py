import cv2
import os
import numpy as np
from ._utils import mg_progressbar, extract_wav, embed_audio_in_video
import mgmodule


# added self, because this function is now called from an MgObject
def history(self, filename='', history_length=10):
    """
    This function  creates a video where each frame is the average of the n previous frames, where n is determined
    from the history_length parameter.
    The history frames are summed up and normalized, and added to the current frame to show the history. 
    Outputs a video called filename + '_history.avi'.

    Parameters
    ----------
    - filename (str): The video file to process.
    - history_length (int): How many frames will be saved to the history tail.

    Returns
    -------
    - An MgObject loaded with the resulting _history video.
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
            #print('Rendering history 100%')
            mg_progressbar(
                length, length, 'Rendering history video:', 'Complete')
            break
        ii += 1
        #print('Rendering history %s%%' % (int(ii/(length-1)*100)), end='\r')
        mg_progressbar(ii, length+1, 'Rendering history video:', 'Complete')

    out.release()
    source_audio = extract_wav(self.of + self.fex)
    destination_video = self.of + '_history' + self.fex
    embed_audio_in_video(source_audio, destination_video)
    os.remove(source_audio)

    return mgmodule.MgObject(destination_video, color=self.color, returned_by_process=True)

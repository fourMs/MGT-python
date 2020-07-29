import cv2
import os
import numpy as np
from musicalgestures._utils import MgProgressbar, get_widthheight, get_framecount, get_length, ffmpeg_cmd


def mg_videograms(self):
    """
    Usees cv2 as backend. Averages videoframes by axes, and creates two images of the horizontal-axis and vertical-axis stacks.
    In these stacks, a single row or column corresponds to a frame from the source video, and the index
    of the row or column corresponds to the index of the source frame.

    Outputs
    -------
    - `filename`_vgx.png

        A horizontal videogram of the source video.
    - `filename`_vgy.png

        A vertical videogram of the source video.

    Returns
    -------
    - Tuple(str, str)

        A tuple with the string paths to the horizontal and vertical videograms respectively. 
    """

    vidcap = cv2.VideoCapture(self.of+self.fex)
    ret, frame = vidcap.read()

    vgramy = np.zeros([1, self.width, 3])
    vgramx = np.zeros([self.height, 1, 3])

    ii = 0

    pb = MgProgressbar(total=self.length, prefix="Rendering videograms:")

    if self.color == False:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        vgramy = np.zeros([1, self.width])
        vgramx = np.zeros([self.height, 1])

    while(vidcap.isOpened()):
        prev_frame = frame

        ret, frame = vidcap.read()
        if ret == True:

            if self.color == False:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame = np.array(frame)
            frame = frame.astype(np.int32)

            if self.color == True:
                mean_x = np.mean(frame, axis=1).reshape(self.height, 1, 3)
                mean_y = np.mean(frame, axis=0).reshape(1, self.width, 3)
            else:
                mean_x = np.mean(frame, axis=1).reshape(self.height, 1)
                mean_y = np.mean(frame, axis=0).reshape(1, self.width)

            # normalization is independent for each color channel
            for channel in range(mean_x.shape[2]):
                mean_x[:, :, channel] = (mean_x[:, :, channel]-mean_x[:, :, channel].min())/(
                    mean_x[:, :, channel].max()-mean_x[:, :, channel].min())*255.0
                mean_y[:, :, channel] = (mean_y[:, :, channel]-mean_y[:, :, channel].min())/(
                    mean_y[:, :, channel].max()-mean_y[:, :, channel].min())*255.0

            vgramx = np.append(vgramx, mean_x, axis=1)
            vgramy = np.append(vgramy, mean_y, axis=0)

        else:
            pb.progress(self.length)
            break

        pb.progress(ii)
        ii += 1

    if self.color == False:
        # Normalize before converting to uint8 to keep precision
        vgramy = vgramy/vgramy.max()*255
        vgramx = vgramx/vgramx.max()*255
        vgramy = cv2.cvtColor(vgramy.astype(
            np.uint8), cv2.COLOR_GRAY2BGR)
        vgramx = cv2.cvtColor(vgramx.astype(
            np.uint8), cv2.COLOR_GRAY2BGR)

    cv2.imwrite(self.of+'_vgx.png', vgramx.astype(np.uint8))
    cv2.imwrite(self.of+'_vgy.png', vgramy.astype(np.uint8))

    vidcap.release()

    return (self.of+'_vgx.png', self.of+'_vgy.png')


def videograms_ffmpeg(self):
    """
    Usees FFMPEG as backend. Averages videoframes by axes, and creates two images of the horizontal-axis and vertical-axis stacks.
    In these stacks, a single row or column corresponds to a frame from the source video, and the index
    of the row or column corresponds to the index of the source frame.

    Outputs
    -------
    - `filename`_vgx.png

        A horizontal videogram of the source video.
    - `filename`_vgy.png

        A vertical videogram of the source video.

    Returns
    -------
    - Tuple(str, str)

        A tuple with the string paths to the horizontal and vertical videograms respectively. 
    """

    width, height = get_widthheight(self.filename)
    framecount = get_framecount(self.filename)
    length = get_length(self.filename)

    outname = self.of + '_vgx.png'
    cmd = ['ffmpeg', '-y', '-i', self.filename, '-frames', '1', '-vf',
           f'scale=1:{height}:sws_flags=area,normalize,tile={framecount}x1', outname]
    ffmpeg_cmd(cmd, length, pb_prefix="Rendering horizontal videogram:")

    outname = self.of + '_vgy.png'
    cmd = ['ffmpeg', '-y', '-i', self.filename, '-frames', '1', '-vf',
           f'scale={width}:1:sws_flags=area,normalize,tile=1x{framecount}', outname]
    ffmpeg_cmd(cmd, length, pb_prefix="Rendering vertical videogram:")

    return (self.of+'_vgx.png', self.of+'_vgy.png')


def mg_videograms(filename):
    """
    Usees FFMPEG as backend. Same as videograms_ffmpeg, but as a standalone function.
    Averages videoframes by axes, and creates two images of the horizontal-axis and vertical-axis stacks.
    In these stacks, a single row or column corresponds to a frame from the source video, and the index
    of the row or column corresponds to the index of the source frame.

    Outputs
    -------
    - `filename`_vgx.png

        A horizontal videogram of the source video.
    - `filename`_vgy.png

        A vertical videogram of the source video.

    Returns
    -------
    - Tuple(str, str)

        A tuple with the string paths to the horizontal and vertical videograms respectively. 
    """
    import os
    of = os.path.splitext(filename)[0]

    width, height = get_widthheight(filename)
    framecount = get_framecount(filename)
    length = get_length(filename)

    outname = of + '_vgx.png'
    cmd = ['ffmpeg', '-y', '-i', filename, '-frames', '1', '-vf',
           f'scale=1:{height}:sws_flags=area,normalize,tile={framecount}x1', outname]
    ffmpeg_cmd(cmd, length, pb_prefix="Rendering horizontal videogram:")

    outname = of + '_vgy.png'
    cmd = ['ffmpeg', '-y', '-i', filename, '-frames', '1', '-vf',
           f'scale={width}:1:sws_flags=area,normalize,tile=1x{framecount}', outname]
    ffmpeg_cmd(cmd, length, pb_prefix="Rendering vertical videogram:")

    return (of+'_vgx.png', of+'_vgy.png')

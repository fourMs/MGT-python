import cv2
import os
import numpy as np
from mgmodule._utils import mg_progressbar, extract_wav, embed_audio_in_video
import mgmodule


class Flow:
    """
    Class container for the sparse and dense optical flow processes.

    Attributes
    ----------
    - filename : str

        Path to the input video file. Passed by parent MgObject.
    - color : bool

        Set class methods in color or grayscale mode. Passed by parent MgObject.

    Methods
    -------
    - dense()

        Renders a dense optical flow video of the input video file.
    - sparse()

        Renders a sparse optical flow video of the input video file.
    """

    def __init__(self, filename, color):
        self.filename = filename
        self.color = color

    def dense(
            self,
            filename='',
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
            skip_empty=False):
        """
        Renders a dense optical flow video of the input video file using `cv2.calcOpticalFlowFarneback()`.
        For more details about the parameters consult the cv2 documentation.

        Parameters
        ----------
        - filename : str, optional

            Path to the input video file. If not specified the video file pointed to by the MgObject is used.
        - pyr_scale : float, optional

            Default is 0.5.
        - levels : int, optional

            Default is 3.
        - winsize : int, optional

            Default is 15.
        - iterations : int, optional

            Default is 3.
        - poly_n : int, optional

            Default is 5.
        - poly_sigma : float, optional

            Default is 1.2.
        - flags : int, optional

            Default is 0.
        - skip_empty : bool, optional

            Default is `False`. If `True`, repeats previous frame in the output when encounters an empty frame.

        Outputs
        -------
        - `filename`_flow_dense.avi

        Returns
        -------
        - MgObject

            A new MgObject pointing to the output '_flow_dense' video file.
        """

        if filename == '':
            filename = self.filename

        of = os.path.splitext(filename)[0]
        fex = os.path.splitext(filename)[1]
        vidcap = cv2.VideoCapture(filename)
        ret, frame = vidcap.read()
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')

        fps = int(vidcap.get(cv2.CAP_PROP_FPS))
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

        out = cv2.VideoWriter(of + '_flow_dense' + fex,
                              fourcc, fps, (width, height))

        ret, frame1 = vidcap.read()
        prev_frame = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        hsv = np.zeros_like(frame1)
        hsv[..., 1] = 255

        ii = 0

        while(vidcap.isOpened()):
            ret, frame2 = vidcap.read()
            if ret == True:
                next_frame = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

                flow = cv2.calcOpticalFlowFarneback(
                    prev_frame, next_frame, None, pyr_scale, levels, winsize, iterations, poly_n, poly_sigma, flags)

                mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                hsv[..., 0] = ang*180/np.pi/2
                hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
                rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

                if skip_empty:
                    if np.sum(rgb) > 0:
                        out.write(rgb.astype(np.uint8))
                    else:
                        if ii == 0:
                            out.write(rgb.astype(np.uint8))
                        else:
                            out.write(prev_rgb.astype(np.uint8))
                else:
                    out.write(rgb.astype(np.uint8))

                prev_frame = next_frame

                if skip_empty:
                    if np.sum(rgb) > 0:
                        prev_rgb = rgb
                else:
                    prev_rgb = rgb

            else:
                mg_progressbar(
                    length, length, 'Rendering dense optical flow video:', 'Complete')
                break

            ii += 1

            mg_progressbar(
                ii, length+1, 'Rendering dense optical flow video:', 'Complete')

        out.release()
        source_audio = extract_wav(of + fex)
        destination_video = of + '_flow_dense' + fex
        embed_audio_in_video(source_audio, destination_video)
        os.remove(source_audio)

        return mgmodule.MgObject(destination_video, color=self.color, returned_by_process=True)

    def sparse(
            self,
            filename='',
            corner_max_corners=100,
            corner_quality_level=0.3,
            corner_min_distance=7,
            corner_block_size=7,
            of_win_size=(15, 15),
            of_max_level=2,
            of_criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)):
        """
        Renders a sparse optical flow video of the input video file using `cv2.calcOpticalFlowPyrLK()`.
        `cv2.goodFeaturesToTrack()` is used for the corner estimation.
        For more details about the parameters consult the cv2 documentation.

        Parameters
        ----------
        - filename : str, optional

            Path to the input video file. If not specified the video file pointed to by the MgObject is used.
        - corner_max_corners : int, optional

            Default is 100.
        - corner_quality_level : float, optional

            Default is 0.3.
        - corner_min_distance : int, optional

            Default is 7.
        - corner_block_size : int, optional

            Default is 7.
        - of_win_size : tuple (int, int), optional

            Default is (15, 15).
        - of_max_level : int, optional

            Default is 2.
        - of_criteria : optional

            Default is `(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)`.

        Outputs
        -------
        - `filename`_flow_sparse.avi

        Returns
        -------
        - MgObject

            A new MgObject pointing to the output '_flow_sparse' video file.
        """

        if filename == '':
            filename = self.filename

        of = os.path.splitext(filename)[0]
        fex = os.path.splitext(filename)[1]
        vidcap = cv2.VideoCapture(filename)
        ret, frame = vidcap.read()
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')

        fps = int(vidcap.get(cv2.CAP_PROP_FPS))
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

        out = cv2.VideoWriter(of + '_flow_sparse' + fex,
                              fourcc, fps, (width, height))

        # params for ShiTomasi corner detection
        feature_params = dict(maxCorners=corner_max_corners,
                              qualityLevel=corner_quality_level,
                              minDistance=corner_min_distance,
                              blockSize=corner_block_size)

        # Parameters for lucas kanade optical flow
        lk_params = dict(winSize=of_win_size,
                         maxLevel=of_max_level,
                         criteria=of_criteria)

        # Create some random colors
        color = np.random.randint(0, 255, (100, 3))

        # Take first frame and find corners in it
        ret, old_frame = vidcap.read()
        old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
        p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)

        # Create a mask image for drawing purposes
        mask = np.zeros_like(old_frame)

        ii = 0

        while(vidcap.isOpened()):
            ret, frame = vidcap.read()
            if ret == True:
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # calculate optical flow
                p1, st, err = cv2.calcOpticalFlowPyrLK(
                    old_gray, frame_gray, p0, None, **lk_params)

                # Select good points
                good_new = p1[st == 1]
                good_old = p0[st == 1]

                # draw the tracks
                for i, (new, old) in enumerate(zip(good_new, good_old)):
                    a, b = new.ravel()
                    c, d = old.ravel()
                    mask = cv2.line(mask, (a, b), (c, d), color[i].tolist(), 2)

                    if self.color == False:
                        frame = cv2.cvtColor(frame_gray, cv2.COLOR_GRAY2BGR)

                    frame = cv2.circle(
                        frame, (a, b), 5, color[i].tolist(), -1)

                img = cv2.add(frame, mask)

                out.write(img.astype(np.uint8))

                # Now update the previous frame and previous points
                old_gray = frame_gray.copy()
                p0 = good_new.reshape(-1, 1, 2)

            else:
                mg_progressbar(
                    length, length, 'Rendering sparse optical flow video:', 'Complete')
                break

            ii += 1

            mg_progressbar(
                ii, length+1, 'Rendering sparse optical flow video:', 'Complete')

        out.release()
        source_audio = extract_wav(of + fex)
        destination_video = of + '_flow_sparse' + fex
        embed_audio_in_video(source_audio, destination_video)
        os.remove(source_audio)

        return mgmodule.MgObject(destination_video, color=self.color, returned_by_process=True)

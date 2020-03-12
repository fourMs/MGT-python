import cv2
import os
import numpy as np
from scipy.signal import medfilt2d
from ._centroid import centroid
from ._utils import mg_progressbar
from ._filter import filter_frame
import matplotlib.pyplot as plt

import mgmodule


def mg_motionvideo(
        self,
        method='Diff',
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        inverted_motionvideo=False,
        inverted_motiongram=False,
        unit='seconds',
        equalize_motiongram=True,
        save_plot=True,
        save_data=True,
        data_format="csv",
        save_motiongrams=True,
        save_video=True):
    """
    Finds the difference in pixel value from one frame to the next in an input video, and saves the frames into a new video.
    Describes the motion in the recording.
    Outputs a video called filename + '_motion.avi'.

    Parameters
    ----------
    - kernel_size (int): Size of structuring element.
    - method (str): Currently 'Diff' is the only implemented method.
    - filtertype (str): 'Regular', 'Binary', 'Blob' (see function filter_frame)
    - thresh (float): a number in [0,1]. Eliminates pixel values less than given threshold.
    - blur (str): 'Average' to apply a blurring filter, 'None' otherwise.
    - inverted_motiongram (bool): Invert colors of motionvideo
    - inverted_motiongram (bool): Invert colors of motiongram
    - unit (str) = Unit in QoM plot. 'seconds' or 'samples'
    - equalize_motiongram (bool): Converts the motiongram to hsv-color space and flattens the value channel (v).

    Returns
    -------
    - An MgObject loaded with the resulting _motion video.
    """

    if save_plot | save_data | save_motiongrams | save_video:

        self.blur = blur
        self.method = method
        self.thresh = thresh
        self.filtertype = filtertype

        vidcap = cv2.VideoCapture(self.of+self.fex)
        ret, frame = vidcap.read()

        if save_video:
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(self.of + '_motion' + self.fex,
                                  fourcc, self.fps, (self.width, self.height))

        if save_motiongrams:
            gramx = np.zeros([1, self.width, 3])
            gramy = np.zeros([self.height, 1, 3])
        if save_data | save_plot:
            qom = np.array([])  # quantity of motion
            com = np.array([])  # centroid of motion

        ii = 0

        if self.color == False:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if save_motiongrams:
                gramx = np.zeros([1, self.width])
                gramy = np.zeros([self.height, 1])

        while(vidcap.isOpened()):
            if self.blur == 'Average':
                prev_frame = cv2.blur(frame, (10, 10))
            elif self.blur == 'None':
                prev_frame = frame

            ret, frame = vidcap.read()
            if ret == True:
                if self.blur == 'Average':
                    # The higher these numbers the more blur you get
                    frame = cv2.blur(frame, (10, 10))
                elif self.blur == 'None':
                    frame = frame  # No blur

                if self.color == True:
                    frame = frame
                else:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                frame = np.array(frame)
                frame = frame.astype(np.int32)

                if self.method == 'Diff':
                    if self.color == True:
                        motion_frame_rgb = np.zeros(
                            [self.height, self.width, 3])

                        for i in range(frame.shape[2]):
                            motion_frame = (
                                np.abs(frame[:, :, i]-prev_frame[:, :, i])).astype(np.uint8)
                            motion_frame = filter_frame(
                                motion_frame, self.filtertype, self.thresh, kernel_size)
                            motion_frame_rgb[:, :, i] = motion_frame

                        if save_motiongrams:
                            movement_y = np.mean(motion_frame_rgb, axis=1).reshape(
                                self.height, 1, 3)
                            movement_x = np.mean(
                                motion_frame_rgb, axis=0).reshape(1, self.width, 3)
                            gramy = np.append(gramy, movement_y, axis=1)
                            gramx = np.append(gramx, movement_x, axis=0)

                    else:
                        motion_frame = (
                            np.abs(frame-prev_frame)).astype(np.uint8)
                        motion_frame = filter_frame(
                            motion_frame, self.filtertype, self.thresh, kernel_size)

                        if save_motiongrams:
                            movement_y = np.mean(
                                motion_frame, axis=1).reshape(self.height, 1)
                            movement_x = np.mean(
                                motion_frame, axis=0).reshape(1, self.width)
                            gramy = np.append(gramy, movement_y, axis=1)
                            gramx = np.append(gramx, movement_x, axis=0)

                elif self.method == 'OpticalFlow':
                    print('Optical Flow not implemented yet!')

                if self.color == False:
                    motion_frame = cv2.cvtColor(
                        motion_frame, cv2.COLOR_GRAY2BGR)
                    motion_frame_rgb = motion_frame

                if save_video:
                    if inverted_motionvideo:
                        out.write(cv2.bitwise_not(
                            motion_frame_rgb.astype(np.uint8)))
                    else:
                        out.write(motion_frame_rgb.astype(np.uint8))

                if save_plot | save_data:
                    combite, qombite = centroid(motion_frame_rgb.astype(
                        np.uint8), self.width, self.height)
                    if ii == 0:
                        com = combite.reshape(1, 2)
                        qom = qombite
                    else:
                        com = np.append(com, combite.reshape(1, 2), axis=0)
                        qom = np.append(qom, qombite)
            else:

                mg_progressbar(self.length, self.length,
                               pgbar_text, 'Complete')
                break
            ii += 1
            pgbar_text = 'Rendering motion' + ", ".join(np.array(["-video", "-grams", "-plots", "-data"])[
                np.array([save_video, save_motiongrams, save_plot, save_data])])
            mg_progressbar(ii, self.length,
                           pgbar_text, 'Complete')

        if save_motiongrams:
            if self.color == False:
                # Normalize before converting to uint8 to keep precision
                gramx = gramx/gramx.max()*255
                gramy = gramy/gramy.max()*255
                gramx = cv2.cvtColor(gramx.astype(
                    np.uint8), cv2.COLOR_GRAY2BGR)
                gramy = cv2.cvtColor(gramy.astype(
                    np.uint8), cv2.COLOR_GRAY2BGR)

            gramx = (gramx-gramx.min())/(gramx.max()-gramx.min())*255.0
            gramy = (gramy-gramy.min())/(gramy.max()-gramy.min())*255.0

            if equalize_motiongram:
                gramx = gramx.astype(np.uint8)
                gramx_hsv = cv2.cvtColor(gramx, cv2.COLOR_BGR2HSV)
                gramx_hsv[:, :, 2] = cv2.equalizeHist(gramx_hsv[:, :, 2])
                gramx = cv2.cvtColor(gramx_hsv, cv2.COLOR_HSV2BGR)

                gramy = gramy.astype(np.uint8)
                gramy_hsv = cv2.cvtColor(gramy, cv2.COLOR_BGR2HSV)
                gramy_hsv[:, :, 2] = cv2.equalizeHist(gramy_hsv[:, :, 2])
                gramy = cv2.cvtColor(gramy_hsv, cv2.COLOR_HSV2BGR)

            if inverted_motiongram:
                cv2.imwrite(self.of+'_mgx.png',
                            cv2.bitwise_not(gramx.astype(np.uint8)))
                cv2.imwrite(self.of+'_mgy.png',
                            cv2.bitwise_not(gramy.astype(np.uint8)))
            else:
                cv2.imwrite(self.of+'_mgx.png', gramx.astype(np.uint8))
                cv2.imwrite(self.of+'_mgy.png', gramy.astype(np.uint8))

        if save_plot:
            plot_motion_metrics(self.of, self.fps, com, qom,
                                self.width, self.height, unit)

        if save_data:
            save_txt(self.of, com, qom, self.width, self.height, data_format)

        if save_video:
            return mgmodule.MgObject(self.of + '_motion' + self.fex)
        else:
            return mgmodule.MgObject(self.of + self.fex)

    else:
        print("Nothing to render. Exiting...")
        return mgmodule.MgObject(self.of + self.fex)


def plot_motion_metrics(of, fps, com, qom, width, height, unit):
    plt.rc('text', usetex=False)
    plt.rc('font', family='serif')
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(1, 2, 1)
    ax.scatter(com[:, 0]/width, com[:, 1]/height, s=2)
    ax.set_xlim((0, 1))
    ax.set_ylim((0, 1))
    ax.set_xlabel('Pixels normalized')
    ax.set_ylabel('Pixels normalized')
    ax.set_title('Centroid of motion')
    ax = fig.add_subplot(1, 2, 2)
    if unit == 'seconds':
        ax.set_xlabel('Time[seconds]')
    else:
        ax.set_xlabel('Time[samples]')
        fps = 1
    ax.set_ylabel('Pixels normalized')
    ax.set_title('Quantity of motion')
    ax.bar(np.arange(len(qom)-1)/fps, qom[1:]/(width*height))
    plt.savefig('%s_motion_com_qom.png' % of, format='png')


def save_txt(of, com, qom, width, height, data_format):
    def save_single_file(of, com, qom, width, height, data_format):
        if data_format == "tsv":
            np.savetxt(of+'_motion.tsv', np.append(np.append(qom.reshape(qom.shape[0], 1), (com[:, 0]/width).reshape(
                com.shape[0], 1), axis=1), (com[:, 1]/height).reshape(com.shape[0], 1), axis=1), delimiter='\t')
        elif data_format == "csv":
            np.savetxt(of+'_motion.csv', np.append(np.append(qom.reshape(qom.shape[0], 1), (com[:, 0]/width).reshape(
                com.shape[0], 1), axis=1), (com[:, 1]/height).reshape(com.shape[0], 1), axis=1), delimiter=',', fmt='%.15f')
        elif data_format == "txt":
            np.savetxt(of+'_motion.txt', np.append(np.append(qom.reshape(qom.shape[0], 1), (com[:, 0]/width).reshape(
                com.shape[0], 1), axis=1), (com[:, 1]/height).reshape(com.shape[0], 1), axis=1), delimiter=' ', fmt=['%d', '%.15f', '%.15f'])
        elif data_format not in ["tsv", "csv", "txt"]:
            print(
                f"Invalid data format: '{data_format}'.\nFalling back to '.csv'.")

    if type(data_format) == str:
        save_single_file(of, com, qom, width, height, data_format)

    elif type(data_format) == list:
        if all([item in ["csv", "tsv", "txt"] for item in data_format]):
            data_format = list(set(data_format))
            [save_single_file(of, com, qom, width, height, item)
             for item in data_format]
        else:
            print(
                f"Unsupported formats in {data_format}.\nFalling back to '.csv'.")
            save_single_file(of, com, qom, width, height, "csv")

import musicalgestures
import matplotlib.pyplot as plt
import cv2
import os
import numpy as np
import pandas as pd
from scipy.signal import medfilt2d
from musicalgestures._centroid import centroid
from musicalgestures._utils import extract_wav, embed_audio_in_video, frame2ms, MgProgressbar, MgImage, convert_to_avi, get_length, get_widthheight
from musicalgestures._filter import filter_frame
from musicalgestures._mglist import MgList


def mg_motiongrams(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        inverted_motiongram=False,
        equalize_motiongram=True):
    """
    Shortcut for `mg_motion` to only render motiongrams.

    Args:
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        kernel_size (int, optional): Size of structuring element. Defaults to 5.
        inverted_motiongram (bool, optional): If True, inverts colors of the motiongrams. Defaults to False.
        equalize_motiongram (bool, optional): If True, converts the motiongrams to hsv-color space and flattens the value channel (v). Defaults to True.

    Outputs:
        `filename`_mgx.png: A horizontal motiongram of the source video.
        `filename`_mgy.png: A vertical motiongram of the source video.

    Returns:
        MgList(MgImage, MgImage): An MgList pointing to the output motiongram images.
    """

    mg_motion(
        self,
        filtertype=filtertype,
        thresh=thresh,
        blur=blur,
        kernel_size=kernel_size,
        inverted_motiongram=inverted_motiongram,
        equalize_motiongram=equalize_motiongram,
        save_data=False,
        save_motiongrams=True,
        save_plot=False,
        save_video=False)

    return MgList(MgImage(self.of + '_mgx.png'), MgImage(self.of + '_mgy.png'))


def mg_motiondata(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        data_format="csv"):
    """
    Shortcut for `mg_motion` to only render motion data.

    Args:
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        kernel_size (int, optional): Size of structuring element. Defaults to 5.
        data_format (str or list, optional): Specifies format of motion-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.

    Outputs:
        `filename`_motion.`data_format`: A text file containing the quantity of motion and the centroid of motion for each frame in the source video with timecodes in milliseconds. Available formats: csv, tsv, txt.

    Returns:
        str or list: The path(s) to the rendered data file(s).
    """

    mg_motion(
        self,
        filtertype=filtertype,
        thresh=thresh,
        blur=blur,
        kernel_size=kernel_size,
        data_format=data_format,
        save_data=True,
        save_motiongrams=False,
        save_plot=False,
        save_video=False)

    if type(data_format) == list:
        outlist = [self.of + '_motion' + elem for elem in data_format]
        return outlist
    else:
        return self.of + '_motion.' + data_format


def mg_motionplots(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        unit='seconds'):
    """
    Shortcut for `mg_motion` to only render motion plots.

    Args:
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        kernel_size (int, optional): Size of structuring element. Defaults to 5.
        unit (str, optional): Unit in QoM plot. Accepted values are 'seconds' or 'samples'. Defaults to 'seconds'.

    Returns:
        MgImage: An MgImage pointing to the exported image (png) of the motion plots.
    """

    mg_motion(
        self,
        filtertype=filtertype,
        thresh=thresh,
        blur=blur,
        kernel_size=kernel_size,
        unit=unit,
        save_data=False,
        save_motiongrams=False,
        save_plot=True,
        save_video=False)

    return MgImage(self.of + '_motion_com_qom.png')


def mg_motionvideo(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        inverted_motionvideo=False):
    """
    Shortcut for `mg_motion` to only render the motion video.

    Args:
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        kernel_size (int, optional): Size of structuring element. Defaults to 5.
        inverted_motionvideo (bool, optional): If True, inverts colors of the motion video. Defaults to False.

    Outputs:
        `filename`_motion.avi: The motion video.

    Returns:
        MgObject: A new MgObject pointing to the output '_motion' video file.
    """

    return mg_motion(
        self,
        filtertype=filtertype,
        thresh=thresh,
        blur=blur,
        kernel_size=kernel_size,
        inverted_motionvideo=inverted_motionvideo,
        save_data=False,
        save_motiongrams=False,
        save_plot=False,
        save_video=True)


def mg_motion(
        self,
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
    Finds the difference in pixel value from one frame to the next in an input video, and saves the frames into a new video. Describes the motion in the recording.

    Args:
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        kernel_size (int, optional): Size of structuring element. Defaults to 5.
        inverted_motionvideo (bool, optional): If True, inverts colors of the motion video. Defaults to False.
        inverted_motiongram (bool, optional): If True, inverts colors of the motiongrams. Defaults to False.
        unit (str, optional): Unit in QoM plot. Accepted values are 'seconds' or 'samples'. Defaults to 'seconds'.
        equalize_motiongram (bool, optional): If True, converts the motiongrams to hsv-color space and flattens the value channel (v). Defaults to True.
        save_plot (bool, optional): If True, outputs motion-plot. Defaults to True.
        save_data (bool, optional): If True, outputs motion-data. Defaults to True.
        data_format (str or list, optional): Specifies format of motion-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
        save_motiongrams (bool, optional): If True, outputs motiongrams. Defaults to True.
        save_video (bool, optional): If True, outputs the motion video. Defaults to True.

    Outputs:
        `filename`_motion.avi: The motion video.
        `filename`_motion_com_qom.png: A plot describing the centroid of motion and the quantity of motion in the source video.
        `filename`_mgx.png: A horizontal motiongram of the source video.
        `filename`_mgy.png: A vertical motiongram of the source video.
        `filename`_motion.`data_format`: A text file containing the quantity of motion and the centroid of motion for each frame in the source video with timecodes in milliseconds. Available formats: csv, tsv, txt.

    Returns:
        MgObject: A new MgObject pointing to the output '_motion' video file. If `save_video=False`, it returns an MgObject pointing to the input video file.
    """

    if save_plot | save_data | save_motiongrams | save_video:

        # self.blur = blur
        # self.thresh = thresh
        # self.filtertype = filtertype
        of, fex = self.of, self.fex

        # Convert to avi if the input is not avi - necesarry for cv2 compatibility on all platforms
        if fex != '.avi':
            convert_to_avi(of + fex)
            fex = '.avi'
            filename = of + fex

        vidcap = cv2.VideoCapture(of+fex)
        ret, frame = vidcap.read()

        if save_video:
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(of + '_motion' + fex,
                                  fourcc, self.fps, (self.width, self.height))

        if save_motiongrams:
            gramx = np.zeros([1, self.width, 3])
            gramy = np.zeros([self.height, 1, 3])
        if save_data | save_plot:
            time = np.array([])  # time in ms
            qom = np.array([])  # quantity of motion
            com = np.array([])  # centroid of motion

        ii = 0

        pgbar_text = 'Rendering motion' + ", ".join(np.array(["-video", "-grams", "-plots", "-data"])[
            np.array([save_video, save_motiongrams, save_plot, save_data])]) + ":"

        pb = MgProgressbar(total=self.length, prefix=pgbar_text)

        if self.color == False:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if save_motiongrams:
                gramx = np.zeros([1, self.width])
                gramy = np.zeros([self.height, 1])

        while(vidcap.isOpened()):
            if blur.lower() == 'average':
                prev_frame = cv2.blur(frame, (10, 10))
            elif blur.lower() == 'none':
                prev_frame = frame

            ret, frame = vidcap.read()
            if ret == True:
                if blur.lower() == 'average':
                    # The higher these numbers the more blur you get
                    frame = cv2.blur(frame, (10, 10))

                if self.color == False:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                frame = np.array(frame)
                frame = frame.astype(np.int32)

                if self.color == True:
                    motion_frame_rgb = np.zeros(
                        [self.height, self.width, 3])

                    for i in range(frame.shape[2]):
                        motion_frame = (
                            np.abs(frame[:, :, i]-prev_frame[:, :, i])).astype(np.uint8)
                        motion_frame = filter_frame(
                            motion_frame, filtertype, thresh, kernel_size)
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
                        motion_frame, filtertype, thresh, kernel_size)

                    if save_motiongrams:
                        movement_y = np.mean(
                            motion_frame, axis=1).reshape(self.height, 1)
                        movement_x = np.mean(
                            motion_frame, axis=0).reshape(1, self.width)
                        gramy = np.append(gramy, movement_y, axis=1)
                        gramx = np.append(gramx, movement_x, axis=0)

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
                        time = frame2ms(ii, self.fps)
                        com = combite.reshape(1, 2)
                        qom = qombite
                    else:
                        time = np.append(time, frame2ms(ii, self.fps))
                        com = np.append(com, combite.reshape(1, 2), axis=0)
                        qom = np.append(qom, qombite)
            else:
                pb.progress(self.length)
                break

            pb.progress(ii)
            ii += 1

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
                cv2.imwrite(of+'_mgx.png',
                            cv2.bitwise_not(gramx.astype(np.uint8)))
                cv2.imwrite(of+'_mgy.png',
                            cv2.bitwise_not(gramy.astype(np.uint8)))
            else:
                cv2.imwrite(of+'_mgx.png', gramx.astype(np.uint8))
                cv2.imwrite(of+'_mgy.png', gramy.astype(np.uint8))

        if save_data:
            save_txt(of, time, com, qom, self.width,
                     self.height, data_format)

        if save_plot:
            plot_motion_metrics(of, self.fps, com, qom,
                                self.width, self.height, unit)

        vidcap.release()
        if save_video:
            out.release()
            destination_video = of + '_motion' + fex
            if self.has_audio:
                source_audio = extract_wav(of + fex)
                embed_audio_in_video(source_audio, destination_video)
                os.remove(source_audio)
            return musicalgestures.MgObject(destination_video, color=self.color, returned_by_process=True)
        else:
            return musicalgestures.MgObject(of + fex, color=self.color, returned_by_process=True)

    else:
        print("Nothing to render. Exiting...")
        return musicalgestures.MgObject(of + fex, returned_by_process=True)


def plot_motion_metrics(of, fps, com, qom, width, height, unit):
    """
    Helper function to plot the centroid and quantity of motion using matplotlib.
    """
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
    if unit.lower() == 'seconds':
        ax.set_xlabel('Time[seconds]')
    else:
        ax.set_xlabel('Time[samples]')
        fps = 1
    ax.set_ylabel('Pixels normalized')
    ax.set_title('Quantity of motion')
    ax.bar(np.arange(len(qom)-1)/fps, qom[1:]/(width*height))
    plt.savefig('%s_motion_com_qom.png' % of, format='png')


def save_txt(of, time, com, qom, width, height, data_format):
    """
    Helper function to export motion data as textfile(s).
    """
    def save_single_file(of, time, com, qom, width, height, data_format):
        """
        Helper function to export motion data as a textfile using pandas.
        """
        data_format = data_format.lower()
        df = pd.DataFrame({'Time': time, 'Qom': qom, 'ComX': com.transpose()[
                          0]/width, 'ComY': com.transpose()[1]/height})
        if data_format == "tsv":
            with open(of+'_motion.tsv', 'wb') as f:
                f.write(b'Time\tQom\tComX\tComY\n')
                np.savetxt(f, df.values, delimiter='\t',
                           fmt=['%d', '%d', '%.15f', '%.15f'])
        elif data_format == "csv":
            df.to_csv(of+'_motion.csv', index=None)
        elif data_format == "txt":
            with open(of+'_motion.txt', 'wb') as f:
                f.write(b'Time Qom ComX ComY\n')
                np.savetxt(f, df.values, delimiter=' ',
                           fmt=['%d', '%d', '%.15f', '%.15f'])
        elif data_format not in ["tsv", "csv", "txt"]:
            print(
                f"Invalid data format: '{data_format}'.\nFalling back to '.csv'.")

    if type(data_format) == str:
        save_single_file(of, time, com, qom, width, height, data_format)

    elif type(data_format) == list:
        if all([item.lower() in ["csv", "tsv", "txt"] for item in data_format]):
            data_format = list(set(data_format))
            [save_single_file(of, time, com, qom, width, height, item)
             for item in data_format]
        else:
            print(
                f"Unsupported formats in {data_format}.\nFalling back to '.csv'.")
            save_single_file(of, time, com, qom, width, height, "csv")

import musicalgestures
import matplotlib.pyplot as plt
import cv2
import os
import numpy as np
import pandas as pd
from scipy.signal import medfilt2d
from musicalgestures._centroid import centroid
from musicalgestures._utils import extract_wav, embed_audio_in_video, frame2ms, MgProgressbar, MgImage, convert_to_avi, get_length, get_widthheight, motionvideo_ffmpeg, generate_outfilename  # ,motiongrams_ffmpeg
from musicalgestures._filter import filter_frame
from musicalgestures._mglist import MgList


def mg_motiongrams(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        use_median=False,
        kernel_size=5,
        inverted_motiongram=False,
        equalize_motiongram=True,
        target_name_mgx=None,
        target_name_mgy=None,
        overwrite=False):
    """
    Shortcut for `mg_motion` to only render motiongrams.

    Args:
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        use_median (bool, optional): If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
        kernel_size (int, optional): Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
        inverted_motiongram (bool, optional): If True, inverts colors of the motiongrams. Defaults to False.
        equalize_motiongram (bool, optional): If True, converts the motiongrams to hsv-color space and flattens the value channel (v). Defaults to True.
        target_name_mgx (str, optional): Target output name for the vertical motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgx" should be used).
        target_name_mgy (str, optional): Target output name for the horizontal motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgy" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgList: An MgList pointing to the output motiongram images (as MgImages).
    """

    # color-mismatch issue needs to be fixed with this one
    # motiongrams_ffmpeg(
    #     filename=self.filename,
    #     color=self.color,
    #     filtertype=filtertype,
    #     threshold=thresh,
    #     blur=blur,
    #     use_median=use_median,
    #     kernel_size=kernel_size,
    #     invert=inverted_motiongram)

    out_x, out_y = None, None

    if target_name_mgx == None:
        target_name_mgx = self.of + '_mgx.png'
    if target_name_mgy == None:
        target_name_mgy = self.of + '_mgy.png'
    if not overwrite:
        out_x = generate_outfilename(target_name_mgx)
        out_y = generate_outfilename(target_name_mgy)
    else:
        out_x, out_y = target_name_mgx, target_name_mgy

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
        save_video=False,
        target_name_mgx=target_name_mgx,
        target_name_mgy=target_name_mgy,
        overwrite=overwrite)
    # mg_motion also saves the motiongrams as MgImages to self.motiongram_x and self.motiongram_y of the parent MgVideo
    return MgList(MgImage(out_x), MgImage(out_y))


def mg_motiondata(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        data_format="csv",
        target_name=None,
        overwrite=False):
    """
    Shortcut for `mg_motion` to only render motion data.

    Args:
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        kernel_size (int, optional): Size of structuring element. Defaults to 5.
        data_format (str/list, optional): Specifies format of motion-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
        target_name (str, optional): Target output name for the data. Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        str/list: The path(s) to the rendered data file(s).
    """

    out = None

    if type(data_format) == str:
        if target_name == None:
            target_name = self.of + '_motion.' + data_format
        if not overwrite:
            target_name = generate_outfilename(target_name)
        out = target_name

    if type(data_format) == list:
        out = []
        if target_name == None:
            # this csv is just a temporary placeholder, the correct extension is always enforced based on the data_format(s)
            target_name = self.of + '_motion.csv'
        target_name_of = os.path.splitext(target_name)[0]
        for item in data_format:
            if not overwrite:
                tmp_name = generate_outfilename(target_name_of + '.' + item)
                out.append(tmp_name)
            else:
                tmp_name = target_name_of + '.' + item

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
        save_video=False,
        target_name_data=target_name,
        overwrite=overwrite)

    # if type(data_format) == list:
    #     outlist = [self.of + '_motion.' + elem for elem in data_format]
    #     return outlist
    # else:
    #     return self.of + '_motion.' + data_format
    return out


def mg_motionplots(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        unit='seconds',
        title=None,
        target_name=None,
        overwrite=False):
    """
    Shortcut for `mg_motion` to only render motion plots.

    Args:
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        kernel_size (int, optional): Size of structuring element. Defaults to 5.
        unit (str, optional): Unit in QoM plot. Accepted values are 'seconds' or 'samples'. Defaults to 'seconds'.
        title (str, optional): Optionally add title to the plot. Defaults to None, which uses the file name as a title.
        target_name (str, optional): Target output name for the plot. Defaults to None (which assumes that the input filename with the suffix "_motion_com_qom" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgImage: An MgImage pointing to the exported image (png) of the motion plots.
    """

    if target_name == None:
        target_name = self.of + '_motion_com_qom.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

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
        plot_title=title,
        save_video=False,
        target_name_plot=target_name,
        overwrite=overwrite)

    # mg_motion also saves the plot as an MgImage to self.motion_plot of the parent MgVideo
    return MgImage(target_name)


def mg_motionvideo(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        use_median=False,
        kernel_size=5,
        inverted_motionvideo=False,
        target_name=None,
        overwrite=False):
    """
    Shortcut to only render the motion video. Uses musicalgestures._utils.motionvideo_ffmpeg. Note that this does not apply median filter by default. If you need it use `use_median=True`.

    Args:
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. Defaults to 'Regular'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        blur (str, optional): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
        use_median (bool, optional): If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
        kernel_size (int, optional): Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
        inverted_motionvideo (bool, optional): If True, inverts colors of the motion video. Defaults to False.
        target_name (str, optional): Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgVideo: A new MgVideo pointing to the output '_motion' video file.
    """

    motionvideo = motionvideo_ffmpeg(
        filename=self.filename,
        color=self.color,
        filtertype=filtertype,
        threshold=thresh,
        blur=blur,
        use_median=use_median,
        kernel_size=kernel_size,
        invert=inverted_motionvideo,
        target_name=target_name,
        overwrite=overwrite)

    # return musicalgestures.MgVideo(motionvideo, color=self.color, returned_by_process=True)

    # save motion video as motion_video for parent MgVideo
    # we have to do this here since we are not using mg_motion (that would normally save the result itself)
    self.motion_video = musicalgestures.MgVideo(
        motionvideo, color=self.color, returned_by_process=True)
    return self.motion_video

    # return mg_motion(
    #     self,
    #     filtertype=filtertype,
    #     thresh=thresh,
    #     blur=blur,
    #     kernel_size=kernel_size,
    #     inverted_motionvideo=inverted_motionvideo,
    #     save_data=False,
    #     save_motiongrams=False,
    #     save_plot=False,
    #     save_video=True)


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
        plot_title=None,
        save_data=True,
        data_format="csv",
        save_motiongrams=True,
        save_video=True,
        target_name_video=None,
        target_name_plot=None,
        target_name_data=None,
        target_name_mgx=None,
        target_name_mgy=None,
        overwrite=False):
    """
    Finds the difference in pixel value from one frame to the next in an input video, and saves the frames into a new video. 
    Describes the motion in the recording. Outputs: a motion video, a plot describing the centroid of motion and the 
    quantity of motion, horizontal and vertical motiongrams, and a text file containing the quantity of motion and the 
    centroid of motion for each frame with timecodes in milliseconds.

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
        plot_title (str, optional): Optionally add title to the plot. Defaults to None, which uses the file name as a title.
        save_data (bool, optional): If True, outputs motion-data. Defaults to True.
        data_format (str/list, optional): Specifies format of motion-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
        save_motiongrams (bool, optional): If True, outputs motiongrams. Defaults to True.
        save_video (bool, optional): If True, outputs the motion video. Defaults to True.
        target_name_video (str, optional): Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
        target_name_plot (str, optional): Target output name for the plot. Defaults to None (which assumes that the input filename with the suffix "_motion_com_qom" should be used).
        target_name_data (str, optional): Target output name for the data. Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
        target_name_mgx (str, optional): Target output name for the vertical motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgx" should be used).
        target_name_mgy (str, optional): Target output name for the horizontal motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgy" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgVideo: A new MgVideo pointing to the output video file. If `save_video=False`, it returns an MgVideo pointing to the input video file.
    """

    if save_plot | save_data | save_motiongrams | save_video:
        # ignore runtime warnings when dividing by 0
        np.seterr(divide='ignore', invalid='ignore')

        of, fex = self.of, self.fex

        # Convert to avi if the input is not avi - necesarry for cv2 compatibility on all platforms
        if fex != '.avi':
            # first check if there already is a converted version, if not create one and register it to the parent self
            if "as_avi" not in self.__dict__.keys():
                file_as_avi = convert_to_avi(of + fex, overwrite=overwrite)
                # register it as the avi version for the file
                self.as_avi = musicalgestures.MgVideo(file_as_avi)
            # point of and fex to the avi version
            of, fex = self.as_avi.of, self.as_avi.fex

        vidcap = cv2.VideoCapture(of+fex)
        ret, frame = vidcap.read()

        if save_video:
            if target_name_video == None:
                target_name_video = of + '_motion' + fex
            # enforce avi
            else:
                target_name_video = os.path.splitext(
                    target_name_video)[0] + fex
            if not overwrite:
                target_name_video = generate_outfilename(target_name_video)

            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(target_name_video, fourcc,
                                  self.fps, (self.width, self.height))

        if save_motiongrams:
            gramx = np.zeros([1, self.width, 3])
            gramy = np.zeros([self.height, 1, 3])
        if save_data | save_plot:
            time = np.array([]) # time in ms
            aom = np.array([])  # area of motion
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
                    motion_frame = cv2.cvtColor(motion_frame, cv2.COLOR_GRAY2BGR)
                    motion_frame_rgb = motion_frame

                if save_video:
                    if inverted_motionvideo:
                        out.write(cv2.bitwise_not(
                            motion_frame_rgb.astype(np.uint8)))
                    else:
                        out.write(motion_frame_rgb.astype(np.uint8))

                if save_plot | save_data:

                    # Area of Motion (AoM)
                    aombite = []
                    # Convert to gray scale
                    gray= cv2.cvtColor(motion_frame_rgb.astype(np.uint8), cv2.COLOR_BGR2GRAY)
                    # Dilate motion frame to make differences more visible for contour detection
                    dilated = cv2.dilate(gray, np.ones((5,5)), iterations=4)
                    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  
                    # Get the largest contour to average the area of motion
                    if len(contours) > 0:
                        largest = contours[0]
                        for contour in contours:
                            if cv2.contourArea(contour) > cv2.contourArea(largest):
                                largest = contour       
                            (x, y, w, h) = cv2.boundingRect(largest)
                        
                    # Append and normalize coordinates of the area of motion
                    aombite.append([x/self.width, y/self.height, (x+w)/self.width,(y+h)/self.height])

                    # Centroid of Motion (CoM) and Quantity of Motion (QoM)
                    combite, qombite = centroid(motion_frame_rgb.astype(np.uint8), self.width, self.height)
                    if ii == 0:
                        time = frame2ms(ii, self.fps)
                        com = combite.reshape(1, 2)
                        qom = qombite
                        aom = np.array(aombite).reshape(1, 4)
                    else:
                        time = np.append(time, frame2ms(ii, self.fps))
                        com = np.append(com, combite.reshape(1, 2), axis=0)
                        qom = np.append(qom, qombite)
                        aom = np.append(aom, np.array(aombite).reshape(1, 4), axis=0)
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

            if target_name_mgx == None:
                target_name_mgx = of+'_mgx.png'
            if target_name_mgy == None:
                target_name_mgy = of+'_mgy.png'
            if not overwrite:
                target_name_mgx = generate_outfilename(target_name_mgx)
                target_name_mgy = generate_outfilename(target_name_mgy)

            if inverted_motiongram:
                cv2.imwrite(target_name_mgx, cv2.bitwise_not(
                    gramx.astype(np.uint8)))
                cv2.imwrite(target_name_mgy, cv2.bitwise_not(
                    gramy.astype(np.uint8)))
            else:
                cv2.imwrite(target_name_mgx, gramx.astype(np.uint8))
                cv2.imwrite(target_name_mgy, gramy.astype(np.uint8))

            # save rendered motiongrams as MgImages into parent MgVideo
            self.motiongram_x = MgImage(target_name_mgx)
            self.motiongram_y = MgImage(target_name_mgy)

        if save_data:
            save_txt(of, time, aom, com, qom, self.width, self.height, data_format,
                     target_name_data=target_name_data, overwrite=overwrite)

        if save_plot:
            if plot_title == None:
                plot_title = os.path.basename(of + fex)
            # save plot as an MgImage at motion_plot for parent MgVideo
            self.motion_plot = MgImage(plot_motion_metrics(of, self.fps, com, qom, self.width,
                                       self.height, unit, plot_title, target_name_plot=target_name_plot, overwrite=overwrite))

        # resetting numpy warnings for dividing by 0
        np.seterr(divide='warn', invalid='warn')

        vidcap.release()
        if save_video:
            out.release()
            # destination_video = of + '_motion' + fex
            destination_video = target_name_video
            if self.has_audio:
                source_audio = extract_wav(of + fex)
                embed_audio_in_video(source_audio, destination_video)
                os.remove(source_audio)
            # return musicalgestures.MgVideo(destination_video, color=self.color, returned_by_process=True)
            # save rendered motion video as the motion_video of the parent MgVideo
            self.motion_video = musicalgestures.MgVideo(
                destination_video, color=self.color, returned_by_process=True)
            return self.motion_video
        # if we don't save the motion video, just return the MgVideo the motion() was called upon
        else:
            # return musicalgestures.MgVideo(of + fex, color=self.color, returned_by_process=True)
            return self

    # just return the MgVideo the motion() was called upon
    else:
        print("Nothing to render. Exiting...")
        # return musicalgestures.MgVideo(of + fex, returned_by_process=True)
        return self


def plot_motion_metrics(of, fps, com, qom, width, height, unit, title, target_name_plot, overwrite):
    """
    Helper function to plot the centroid and quantity of motion using matplotlib.
    """
    plt.rc('text', usetex=False)
    # plt.rc('font', family='serif')
    fig = plt.figure(figsize=(12, 6))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)
    # add title
    fig.suptitle(title, fontsize=16)
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

    if target_name_plot == None:
        target_name_plot = of + '_motion_com_qom.png'
    else:
        # enforce png
        target_name_plot = os.path.splitext(target_name_plot)[0] + '.png'
    if not overwrite:
        target_name_plot = generate_outfilename(target_name_plot)

    plt.savefig(target_name_plot, format='png', transparent=False)

    return target_name_plot


def save_txt(of, time, aom, com, qom, width, height, data_format, target_name_data, overwrite):
    """
    Helper function to export motion data as textfile(s).
    """
    def save_single_file(of, time, aom, com, qom, width, height, data_format, target_name_data, overwrite):
        """
        Helper function to export motion data as a textfile using pandas.
        """
        data_format = data_format.lower()
        df = pd.DataFrame({'Time': time, 'Qom': qom, 'ComX': com.transpose()[
                          0]/width, 'ComY': com.transpose()[1]/height, 
                          'AomX1': aom.transpose()[0], 'AomY1': aom.transpose()[1], 'AomX2': aom.transpose()[2], 'AomY2': aom.transpose()[3]})

        if data_format == "tsv":

            if target_name_data == None:
                target_name_data = of+'_motion.tsv'
            else:
                # take name, but enforce tsv
                target_name_data = os.path.splitext(target_name_data)[0] + '.tsv'
            if not overwrite:
                target_name_data = generate_outfilename(target_name_data)

            with open(target_name_data, 'wb') as f:
                f.write(b'Time\tQom\tComX\tComY\tAomX1\tAomY1\tAomX2\tAomY2\n')
                np.savetxt(f, df.values, delimiter='\t',fmt=['%d', '%d', '%.15f', '%.15f', '%.15f', '%.15f', '%.15f', '%.15f'])

        elif data_format == "csv":

            if target_name_data == None:
                target_name_data = of+'_motion.csv'
            else:
                # take name, but enforce csv
                target_name_data = os.path.splitext(target_name_data)[0] + '.csv'
            if not overwrite:
                target_name_data = generate_outfilename(target_name_data)

            df.to_csv(target_name_data, index=None)

        elif data_format == "txt":

            if target_name_data == None:
                target_name_data = of+'_motion.txt'
            else:
                # take name, but enforce txt
                target_name_data = os.path.splitext(target_name_data)[0] + '.txt'
            if not overwrite:
                target_name_data = generate_outfilename(target_name_data)

            with open(target_name_data, 'wb') as f:
                f.write(b'Time Qom ComX ComY AomX1 AomY1 AomX2 AomY2\n')
                np.savetxt(f, df.values, delimiter=' ',
                           fmt=['%d', '%d', '%.15f', '%.15f', '%.15f', '%.15f', '%.15f', '%.15f'])

        elif data_format not in ["tsv", "csv", "txt"]:
            print(
                f"Invalid data format: '{data_format}'.\nFalling back to '.csv'.")
            save_single_file(of, time, aom, com, qom, width, height, "csv",
                             target_name_data=target_name_data, overwrite=overwrite)

    if type(data_format) == str:
        save_single_file(of, time, aom, com, qom, width, height, data_format,
                         target_name_data=target_name_data, overwrite=overwrite)

    elif type(data_format) == list:
        if all([item.lower() in ["csv", "tsv", "txt"] for item in data_format]):
            data_format = list(set(data_format))
            [save_single_file(of, time, aom, com, qom, width, height, item, target_name_data=target_name_data, overwrite=overwrite)
             for item in data_format]
        else:
            print(
                f"Unsupported formats in {data_format}.\nFalling back to '.csv'.")
            save_single_file(of, time, aom, com, qom, width, height, "csv",
                             target_name_data=target_name_data, overwrite=overwrite)

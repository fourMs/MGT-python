import musicalgestures
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import cv2
import os
import librosa 
import numpy as np
import pandas as pd
import subprocess, re

from musicalgestures._motionanalysis import centroid, area
from musicalgestures._utils import extract_wav, embed_audio_in_video, frame2ms, ffmpeg_cmd, MgProgressbar, MgFigure, MgImage, motionvideo_ffmpeg, generate_outfilename
from musicalgestures._filter import filter_frame_ffmpeg
from musicalgestures._mglist import MgList



def mg_motion(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        use_median=False,
        unit='seconds',
        atadenoise=False,
        motion_analysis='all',
        inverted_motionvideo=False,
        inverted_motiongram=False,
        equalize_motiongram=False,
        audio_descriptors=False,
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
        use_median (bool, optional): If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
        unit (str, optional): Unit in QoM plot. Accepted values are 'seconds' or 'samples'. Defaults to 'seconds'.
        atadenoise (bool, optional): If True, applies an adaptive temporal averaging denoiser every 129 frames. Defaults to False.
        motion_analysis (str, optional): Specify which motion analysis to process or all. 'AoM' renders the Area of Motion. 'CoM' renders the Centroid of Motion. 'QoM' renders the Quantity of Motion. 'all' renders all the motion analysis available. Defaults to 'all'.
        inverted_motionvideo (bool, optional): If True, inverts colors of the motion video. Defaults to False.
        inverted_motiongram (bool, optional): If True, inverts colors of the motiongrams. Defaults to False.
        equalize_motiongram (bool, optional): If True, converts the motiongrams to hsv-color space and flattens the value channel (v). Defaults to True.
        save_plot (bool, optional): If True, outputs motion-plot. Defaults to True.
        plot_title (str, optional): Optionally add title to the plot. Defaults to None, which uses the file name as a title.
        save_data (bool, optional): If True, outputs motion-data. Defaults to True.
        data_format (str/list, optional): Specifies format of motion-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
        save_motiongrams (bool, optional): If True, outputs motiongrams. Defaults to True.
        save_video (bool, optional): If True, outputs the motion video. Defaults to True.
        target_name_video (str, optional): Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_motion" should be used).
        target_name_plot (str, optional): Target output name for the plot. Defaults to None (which assumes that the input filename with the suffix "_motion_com_aom_qom" should be used).
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

        # Define ffmpeg command start and end
        cmd = ['ffmpeg', '-y', '-i', self.filename]
        # Filter video frames using ffmpeg
        cmd, cmd_filter = filter_frame_ffmpeg(self.filename, cmd, self.color, blur, filtertype, thresh, kernel_size, use_median)
        
        if atadenoise:
            # Apply an adaptive temporal averaging denoiser every 129 frames
            cmd_filter += 'atadenoise=s=129'
        else:
            # Remove last comma after previous filter
            cmd_filter = cmd_filter[: -1]
        cmd += ['-filter_complex', cmd_filter] 

        if save_motiongrams:
            gramx = np.zeros([1, self.width, 3]).astype(np.uint8)
            gramy = np.zeros([self.height, 1, 3]).astype(np.uint8) 

        if save_data | save_plot:      
            time = np.array([]) # time in ms
            aom = np.array([])  # area of motion
            qom = np.array([])  # quantity of motion
            com = np.array([])  # centroid of motion

        if save_video:
            if target_name_video is None:
                target_name_video = of + '_motion' + fex
            # enforce avi
            else:
                target_name_video = os.path.splitext(target_name_video)[0] + fex
            if not overwrite:
                target_name_video = generate_outfilename(target_name_video)

        pgbar_text = 'Rendering motion' + ", ".join(np.array(["-video", "-grams", "-plots", "-data"])[
            np.array([save_video, save_motiongrams, save_plot, save_data])]) + ":" 
        pb = MgProgressbar(total=self.length, prefix=pgbar_text)  

        # Pipe video with FFmpeg for reading frame by frame        
        process = ffmpeg_cmd(cmd, total_time=self.length, pipe='read')
        video_out = None

        i = 0
        while True:
            # Read frame-by-frame
            out = process.stdout.read(self.width*self.height*3)

            if out == b'':
                pb.progress(self.length)
                break

            # Transform the bytes read into a numpy array
            motion_frame = np.frombuffer(out, dtype=np.uint8).reshape([self.height, self.width, 3]) # height, width, channels

            if save_data | save_plot:
                if motion_analysis.lower() == 'aom':
                    # Area of Motion (AoM)
                    aombite = area(motion_frame, self.height, self.width)
                    if i == 0:
                        time = frame2ms(i, self.fps)
                        aom = np.array(aombite).reshape(1, 4)
                    else:
                        time = np.append(time, frame2ms(i, self.fps))
                        aom = np.append(aom, np.array(aombite).reshape(1, 4), axis=0)

                if motion_analysis.lower() == 'com' or motion_analysis.lower() == 'qom':
                    # Centroid of Motion (CoM) and Quantity of Motion (QoM)
                    combite, qombite = centroid(motion_frame, self.width, self.height)
                    if i == 0:
                        time = frame2ms(i, self.fps)
                        com = combite.reshape(1, 2)
                        qom = qombite
                    else:
                        time = np.append(time, frame2ms(i, self.fps))
                        com = np.append(com, combite.reshape(1, 2), axis=0)
                        qom = np.append(qom, qombite)

                if motion_analysis.lower() == 'all':
                    # Area of Motion (AoM)
                    aombite = area(motion_frame, self.height, self.width)                    
                    # Centroid of Motion (CoM) and Quantity of Motion (QoM)
                    combite, qombite = centroid(motion_frame, self.width, self.height)
                    if i == 0:
                        time = frame2ms(i, self.fps)
                        com = combite.reshape(1, 2)
                        qom = qombite
                        aom = np.array(aombite).reshape(1, 4)
                    else:
                        time = np.append(time, frame2ms(i, self.fps))
                        com = np.append(com, combite.reshape(1, 2), axis=0)
                        qom = np.append(qom, qombite)
                        aom = np.append(aom, np.array(aombite).reshape(1, 4), axis=0)

            if save_motiongrams:
                movement_y = np.mean(motion_frame, axis=1).reshape(self.height, 1, 3).astype(np.uint8)
                movement_x = np.mean(motion_frame, axis=0).reshape(1, self.width, 3).astype(np.uint8)

                gramy = np.append(gramy, movement_y, axis=1).astype(np.uint8)
                gramx = np.append(gramx, movement_x, axis=0).astype(np.uint8)

            if save_video:
                if video_out is None:
                    cmd =['ffmpeg', '-y', '-s', '{}x{}'.format(motion_frame.shape[1], motion_frame.shape[0]), 
                        '-r', str(self.fps), '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', 
                        '-i', '-', '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', target_name_video]
                    video_out = ffmpeg_cmd(cmd, total_time=self.length, pipe='write')

                if inverted_motionvideo:
                    video_out.stdin.write(cv2.bitwise_not(motion_frame.astype(np.uint8)))
                else:
                    video_out.stdin.write(motion_frame.astype(np.uint8))
            
            # Flush the buffer
            process.stdout.flush()
            pb.progress(i)
            i += 1

        # Terminate the processes
        video_out.stdin.close()
        video_out.wait()
        process.terminate()

        if save_motiongrams:
            gramx = (gramx-gramx.min())/(gramx.max()-gramx.min())*255.0
            gramy = (gramy-gramy.min())/(gramy.max()-gramy.min())*255.0

            if equalize_motiongram:
                gramx = gramx.astype(np.uint8)
                gramx_hsv = cv2.cvtColor(gramx, cv2.COLOR_RGB2HSV).astype(np.uint8)
                gramx_hsv[:, :, 2] = cv2.equalizeHist(gramx_hsv[:, :, 2]).astype(np.uint8)
                gramx = cv2.cvtColor(gramx_hsv, cv2.COLOR_HSV2RGB).astype(np.uint8)

                gramy = gramy.astype(np.uint8)
                gramy_hsv = cv2.cvtColor(gramy, cv2.COLOR_RGB2HSV).astype(np.uint8)
                gramy_hsv[:, :, 2] = cv2.equalizeHist(gramy_hsv[:, :, 2]).astype(np.uint8)
                gramy = cv2.cvtColor(gramy_hsv, cv2.COLOR_HSV2RGB).astype(np.uint8)

            if target_name_mgx == None:
                target_name_mgx = of + '_mgx.png'
            if target_name_mgy == None:
                target_name_mgy = of + '_mgy.png'
            if not overwrite:
                target_name_mgx = generate_outfilename(target_name_mgx)
                target_name_mgy = generate_outfilename(target_name_mgy)

            if inverted_motiongram:
                cv2.imwrite(target_name_mgx, cv2.bitwise_not(gramx.astype(np.uint8)))
                cv2.imwrite(target_name_mgy, cv2.bitwise_not(gramy.astype(np.uint8)))
            else:
                cv2.imwrite(target_name_mgx, gramx.astype(np.uint8))
                cv2.imwrite(target_name_mgy, gramy.astype(np.uint8))

            # save motiongrams data and convert to grayscale for processing motiongrams Self-Similarity Matrices (SSMs)
            data = (cv2.cvtColor(gramx.astype(np.uint8), cv2.COLOR_RGB2GRAY), cv2.cvtColor(gramy.astype(np.uint8), cv2.COLOR_RGB2GRAY))
            self.ssm_fig = MgFigure(figure=None, figure_type='video.ssm', data=data, layers=None, image=(target_name_mgx, target_name_mgy))

            # save rendered motiongrams as MgImages into parent MgVideo
            self.motiongram_x = MgImage(target_name_mgx)
            self.motiongram_y = MgImage(target_name_mgy)

        if audio_descriptors:
            audio_descriptors = self
            
        if save_data:
            save_txt(of, time, aom, com, qom, motion_analysis, self.width, self.height, 
            data_format=data_format, target_name_data=target_name_data, overwrite=overwrite)

        if save_plot:
            if plot_title == None:
                plot_title = os.path.basename(of + fex)
            # save plot as an MgImage at motion_plot for parent MgVideo
            self.motion_plot = MgImage(save_analysis(of, self.fps, aom, com, qom, motion_analysis, audio_descriptors, self.width,
                                        self.height, unit, plot_title, target_name_plot=target_name_plot, overwrite=overwrite))
                
        # Resetting numpy warnings for dividing by 0
        np.seterr(divide='warn', invalid='warn')

        if save_video:
            # Check if the original video fil has audio
            if self.has_audio:
                source_audio = extract_wav(of + fex)
                embed_audio_in_video(source_audio, target_name_video)
                os.remove(source_audio)
                
            # Save generated musicalgestures video as the video of the parent MgVideo
            self.motion_video = musicalgestures.MgVideo(filename=target_name_video, returned_by_process=True)
            return self.motion_video
        
        else:
            return self

    else:
        # Return the MgVideo the motion() was called upon
        print("Nothing to render. Exiting...")
        return self


def mg_motiongrams(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        use_median=False,
        atadenoise=True,
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
        atadenoise (bool, optional): If True, applies an adaptive temporal averaging denoiser every 129 frames. Defaults to True.
        kernel_size (int, optional): Size of the median filter (if `use_median=True`) or the erosion filter (if `filtertype='blob'`). Defaults to 5.
        inverted_motiongram (bool, optional): If True, inverts colors of the motiongrams. Defaults to False.
        equalize_motiongram (bool, optional): If True, converts the motiongrams to hsv-color space and flattens the value channel (v). Defaults to True.
        target_name_mgx (str, optional): Target output name for the vertical motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgx" should be used).
        target_name_mgy (str, optional): Target output name for the horizontal motiongram. Defaults to None (which assumes that the input filename with the suffix "_mgy" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgList: An MgList pointing to the output motiongram images (as MgImages).
    """

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
        use_median=use_median,
        atadenoise=atadenoise,
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

    # save motion video as motion_video for parent MgVideo
    # we have to do this here since we are not using mg_motion (that would normally save the result itself)
    self.motion_video = musicalgestures.MgVideo(motionvideo, color=self.color, returned_by_process=True)

    return self.motion_video


def mg_motiondata(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        atadenoise=False,
        use_median=False,
        motion_analysis='all',
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
        atadenoise (bool, optional): If True, applies an adaptive temporal averaging denoiser every 129 frames. Defaults to False.
        use_median (bool, optional): If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
        motion_analysis (str, optional): Specify which motion analysis to process or all. 'AoM' renders the Area of Motion. 'CoM' renders the Centroid of Motion. 'QoM' renders the Quantity of Motion. 'all' renders all the motion analysis available. Defaults to 'all'.
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
        use_median=use_median,
        atadenoise=atadenoise,
        motion_analysis=motion_analysis,
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
        use_median=False,
        atadenoise=False,
        motion_analysis='all',
        audio_descriptors=False,
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
        use_median (bool, optional): If True the algorithm applies a median filter on the thresholded frame-difference stream. Defaults to False.
        atadenoise (bool, optional): If True, applies an adaptive temporal averaging denoiser every 129 frames. Defaults to False.
        motion_analysis (str, optional): Specify which motion analysis to process or all. 'AoM' renders the Area of Motion. 'CoM' renders the Centroid of Motion. 'QoM' renders the Quantity of Motion. 'all' renders all the motion analysis available. Defaults to 'all'.
        audio_descriptors (bool, optional): Whether to plot motion plots together with audio descriptors in order to see possible correlations in the data. Deflauts to False.
        unit (str, optional): Unit in QoM plot. Accepted values are 'seconds' or 'samples'. Defaults to 'seconds'.
        title (str, optional): Optionally add title to the plot. Defaults to None, which uses the file name as a title.
        target_name (str, optional): Target output name for the plot. Defaults to None (which assumes that the input filename with the suffix "_motion_com_aom_qom" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgImage: An MgImage pointing to the exported image (png) of the motion plots.
    """

    if target_name == None:
        target_name = self.of + '_motionplots.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    mg_motion(
        self,
        filtertype=filtertype,
        thresh=thresh,
        blur=blur,
        kernel_size=kernel_size,
        use_median=use_median,
        unit=unit,
        atadenoise=atadenoise,
        motion_analysis=motion_analysis,
        audio_descriptors=audio_descriptors,
        save_data=False,
        save_motiongrams=False,
        save_plot=True,
        plot_title=title,
        save_video=False,
        target_name_plot=target_name,
        overwrite=overwrite)

    # mg_motion also saves the plot as an MgImage to self.motion_plot of the parent MgVideo
    return MgImage(target_name)

def mg_motionscore(self):
    # Obtain the average vmaf motion score of a video using FFmpeg
    cmd = ['ffmpeg', '-i', self.filename, '-vf', 'vmafmotion', '-f', 'null', '-']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    out, _ = process.communicate()
    splitted = out.split('\n')

    for index, item in enumerate(splitted):
        if isinstance(item, str) and re.search('VMAF', item):
            vmafmotion = float(re.findall(r'\d+\.\d+', splitted[index].split("] ")[1])[0])
            return print('Average VMAF motion score:', vmafmotion)
    print('VMAF motion score is not available.')


def save_analysis(of, fps, aom, com, qom, motion_analysis, audio_descriptors, width, height, unit, title, target_name_plot, overwrite):
    """
    Helper function to plot the motion data using matplotlib.
    """
    plt.rc('text', usetex=False)
    fig = plt.figure(figsize=(12, 10), dpi=300)
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)
    # add title
    fig.suptitle(title, fontsize=16)

    if motion_analysis.lower() == 'all':
        gs = gridspec.GridSpec(3, 2)
    elif motion_analysis.lower() == 'qom':
        gs = gridspec.GridSpec(2, 2)
    else:
        gs = gridspec.GridSpec(1, 2)

    # Audio descriptors
    if audio_descriptors:
        fig = plt.figure(figsize=(12, 16), dpi=300)
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)
        # add title
        fig.suptitle(title, fontsize=16)
        descriptors = audio_descriptors.audio.descriptors(autoshow=False).data

        if motion_analysis.lower() == 'all':
            gs = gridspec.GridSpec(6, 2)
        elif motion_analysis.lower() == 'qom':
            gs = gridspec.GridSpec(5, 2)
        else:
            gs = gridspec.GridSpec(4, 2)

    # Centroid of motion (CoM)
    if motion_analysis.lower() == 'com':
        ax0 = fig.add_subplot(gs[0, :])
        ax0.scatter(com[:, 0]/width, com[:, 1]/height, s=2)
        ax0.set_xlim((0, 1))
        ax0.set_ylim((0, 1))
        ax0.set_xlabel('Pixels normalized')
        ax0.set_ylabel('Pixels normalized')
        ax0.set_title('Centroid of motion (CoM)')

    # Area of motion (AoM)
    if motion_analysis.lower() == 'aom':
        ax0 = fig.add_subplot(gs[0, :])
        ax0.scatter(aom[:, 0], aom[:, 1], c='C0', s=2)
        ax0.scatter(aom[:, 2], aom[:, 3], c='C0', s=2)
        ax0.set_xlim((0, 1))
        ax0.set_ylim((0, 1))
        ax0.set_xlabel('Pixels normalized')
        ax0.set_ylabel('Pixels normalized')
        ax0.set_title('Area of motion (AoM)')

    # Quantity of motion (QoM)
    def adjacent_values(vals, q1, q3):
        upper_adjacent_value = q3 + (q3 - q1) * 1.5
        upper_adjacent_value = np.clip(upper_adjacent_value, q3, vals[-1])

        lower_adjacent_value = q1 - (q3 - q1) * 1.5
        lower_adjacent_value = np.clip(lower_adjacent_value, vals[0], q1)
        return lower_adjacent_value, upper_adjacent_value

    if motion_analysis.lower() == 'qom':
        ax0 = fig.add_subplot(gs[0, :])
        ax0.set_title('Quantity of motion (QoM)')
        ax0.violinplot([qom[1:]/(max(qom[1:]))], showmeans=False, showmedians=True, showextrema=True, vert=False)

        quartile1, medians, quartile3 = np.percentile([qom[1:]/(max(qom[1:]))], [25, 50, 75], axis=1)
        whiskers = np.array([adjacent_values(sorted_array, q1, q3) for sorted_array, q1, q3 in zip([qom[1:]/(max(qom[1:]))], quartile1, quartile3)])
        whiskers_min, whiskers_max = whiskers[:, 0], whiskers[:, 1]

        inds = np.arange(1, len(medians) + 1)
        ax0.scatter(medians, inds, marker='o', color='white', s=60, zorder=3)
        ax0.hlines(inds, quartile1, quartile3, color='k', linestyle='-', lw=8)
        ax0.hlines(inds, whiskers_min, whiskers_max, color='k', linestyle='-', lw=1)
        ax0.set_xlabel('Pixels normalized')
        ax0.set_yticks([])
        ax0.set_yticklabels([])

        ax1 = fig.add_subplot(gs[1, :])
        if unit.lower() == 'seconds':
            ax1.set_xlabel('Time [seconds]')
        else:
            ax1.set_xlabel('Time [samples]')
            fps = 1
        ax1.set_ylabel('Pixels normalized')
        ax1.bar(np.arange(len(qom)-1)/fps, qom[1:]/(max(qom[1:])))

    # All motion data
    if motion_analysis.lower() == 'all':
        ax0 = fig.add_subplot(gs[0, 0])
        ax0.scatter(com[:, 0]/width, com[:, 1]/height, s=2)
        ax0.set_xlim((0, 1))
        ax0.set_ylim((0, 1))
        ax0.set_xlabel('Pixels normalized')
        ax0.set_ylabel('Pixels normalized')
        ax0.set_title('Centroid of motion (CoM)')

        ax0 = fig.add_subplot(gs[0, 1])
        ax0.scatter(aom[:, 0], aom[:, 1], c='C0', s=2)
        ax0.scatter(aom[:, 2], aom[:, 3], c='C0', s=2)
        ax0.set_xlim((0, 1))
        ax0.set_ylim((0, 1))
        ax0.set_xlabel('Pixels normalized')
        ax0.set_ylabel('Pixels normalized')
        ax0.set_title('Area of motion (AoM)')

        ax1 = fig.add_subplot(gs[1, :])
        ax1.set_title('Quantity of motion (QoM)')
        ax1.violinplot([qom[1:]/(max(qom[1:]))], showmeans=False, showmedians=True, showextrema=True, vert=False)
        quartile1, medians, quartile3 = np.percentile([qom[1:]/(max(qom[1:]))], [25, 50, 75], axis=1)
        whiskers = np.array([adjacent_values(sorted_array, q1, q3) for sorted_array, q1, q3 in zip([qom[1:]/(max(qom[1:]))], quartile1, quartile3)])
        whiskers_min, whiskers_max = whiskers[:, 0], whiskers[:, 1]
        inds = np.arange(1, len(medians) + 1)
        ax1.scatter(medians, inds, marker='o', color='white', s=60, zorder=3)
        ax1.hlines(inds, quartile1, quartile3, color='k', linestyle='-', lw=8)
        ax1.hlines(inds, whiskers_min, whiskers_max, color='k', linestyle='-', lw=1)
        ax1.set_xlabel('Pixels normalized')
        ax1.set_yticks([])
        ax1.set_yticklabels([])

        ax2 = fig.add_subplot(gs[2, :])
        if unit.lower() == 'seconds':
            ax2.set_xlabel('Time [seconds]')
        else:
            ax2.set_xlabel('Time [samples]')
            fps = 1
        ax2.set_ylabel('Pixels normalized')
        ax2.bar(np.arange(len(qom)-1)/fps, qom[1:]/(max(qom[1:])))

    # Plot audio descriptors
    if audio_descriptors:

        freq_ticks = [elem*100 for elem in range(10)]
        freq_ticks = [250]
        freq = 500
        while freq < descriptors['sr']/2:
            freq_ticks.append(freq)
            freq *= 1.5

        freq_ticks = [round(elem, -1) for elem in freq_ticks]
        freq_ticks_labels = [str(round(elem/1000, 1)) + 'k' if elem > 1000 else int(round(elem)) for elem in freq_ticks]

        times = librosa.times_like(descriptors['cent'], sr=descriptors['sr'], n_fft=2048, hop_length=descriptors['hop_size'])

        if unit.lower() == 'samples':
            times = times*descriptors['sr']

        if motion_analysis.lower() == 'all':
            ax3 = fig.add_subplot(gs[3, :], sharex=ax2)
        elif motion_analysis.lower() == 'qom':
            ax3 = fig.add_subplot(gs[2, :])
        else:
            ax3 = fig.add_subplot(gs[1, :])

        ax3.set_title('Audio descriptors')
        ax3.semilogy(times, descriptors['rms'][0], label='RMS Energy')
        ax3.legend(loc='upper right')

        if motion_analysis.lower() == 'all':
            ax4 = fig.add_subplot(gs[4, :], sharex=ax2)
        elif motion_analysis.lower() == 'qom':
            ax4 = fig.add_subplot(gs[3, :])
        else:
            ax4 = fig.add_subplot(gs[2, :])

        ax4.plot(times, descriptors['flatness'].T, label='Flatness', color='y')
        ax4.legend(loc='upper right')

        if motion_analysis.lower() == 'all':
            ax5 = fig.add_subplot(gs[5, :], sharex=ax2)
        elif motion_analysis.lower() == 'qom':
            ax5 = fig.add_subplot(gs[4, :])
        else:
            ax5 = fig.add_subplot(gs[3, :])

        ax5.set_ylabel('Frequency [Hz]')
        ax5.fill_between(times, descriptors['cent'][0] - descriptors['spec_bw'][0], descriptors['cent'][0] + descriptors['spec_bw'][0], alpha=0.5, label='Centroid +- bandwidth')
        ax5.plot(times, descriptors['cent'].T, label='Centroid', color='y')
        ax5.plot(times, descriptors['rolloff'][0], label='Roll-off frequency (0.99)')
        ax5.plot(times, descriptors['rolloff_min'][0], color='r',label='Roll-off frequency (0.01)')
        ax5.legend(loc='upper right')

        if unit.lower() == 'seconds':
            ax5.set_xlabel('Time [seconds]')
        else:
            ax5.set_xlabel('Time [samples]')

    fig.tight_layout()

    if target_name_plot == None:
        target_name_plot = of + '_motionplot.png'
    else:
        # enforce png
        target_name_plot = os.path.splitext(target_name_plot)[0] + '.png'
    if not overwrite:
        target_name_plot = generate_outfilename(target_name_plot)

    plt.savefig(target_name_plot, format='png', transparent=False)
    plt.close()

    return target_name_plot


def save_txt(of, time, aom, com, qom, motion_analysis, width, height, data_format, target_name_data, overwrite):
    """
    Helper function to export motion data as textfile(s).
    """
    def save_single_file(of, time, aom, com, qom, motion_analysis, width, height, data_format, target_name_data, overwrite):
        """
        Helper function to export motion data as a textfile using pandas.
        """
        data_format = data_format.lower()

        if motion_analysis.lower() == 'aom':
            df = pd.DataFrame({'Time': time, 'AomX1': aom.transpose()[0], 'AomY1': aom.transpose()[1], 'AomX2': aom.transpose()[2], 'AomY2': aom.transpose()[3]})
        elif motion_analysis.lower() == 'com':
            df = pd.DataFrame({'Time': time, 'ComX': com.transpose()[0]/width, 'ComY': com.transpose()[1]/height})
        elif motion_analysis.lower() == 'qom':
            df = pd.DataFrame({'Time': time, 'Qom': qom/max(qom)}) 
        elif motion_analysis.lower() == 'all':
            df = pd.DataFrame({'Time': time, 'Qom': qom/max(qom), 'ComX': com.transpose()[0]/width, 'ComY': com.transpose()[1]/height, 
                          'AomX1': aom.transpose()[0], 'AomY1': aom.transpose()[1], 'AomX2': aom.transpose()[2], 'AomY2': aom.transpose()[3]})

        if data_format == "tsv":
            if target_name_data == None:
                target_name_data = of + '_motion.tsv'
            else:
                # take name, but enforce tsv
                target_name_data = os.path.splitext(target_name_data)[0] + '.tsv'
            if not overwrite:
                target_name_data = generate_outfilename(target_name_data)

            if motion_analysis.lower() == 'aom':
                with open(target_name_data, 'wb') as f:
                    f.write(b'Time\tAomX1\tAomY1\tAomX2\tAomY2\n')
                    np.savetxt(f, df.values, delimiter='\t', fmt=['%d', '%.15f', '%.15f', '%.15f', '%.15f'])
            elif motion_analysis.lower() == 'com':
                with open(target_name_data, 'wb') as f:
                    f.write(b'Time\tComX\tComY\n')
                    np.savetxt(f, df.values, delimiter='\t', fmt=['%d', '%.15f', '%.15f'])
            elif motion_analysis.lower() == 'qom':
                with open(target_name_data, 'wb') as f:
                    f.write(b'Time\tQom\n')
                    np.savetxt(f, df.values, delimiter='\t', fmt=['%d', '%d'])
            elif motion_analysis.lower() == 'all':
                with open(target_name_data, 'wb') as f:
                    f.write(b'Time\tQom\tComX\tComY\tAomX1\tAomY1\tAomX2\tAomY2\n')
                    np.savetxt(f, df.values, delimiter='\t', fmt=['%d', '%d', '%.15f', '%.15f', '%.15f', '%.15f', '%.15f', '%.15f'])


        elif data_format == "csv":
            if target_name_data == None:
                target_name_data = of + '_motiondata.csv'
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

            if motion_analysis.lower() == 'aom':
                with open(target_name_data, 'wb') as f:
                    f.write(b'Time AomX1 AomY1 AomX2 AomY2\n')
                    np.savetxt(f, df.values, delimiter=' ', fmt=['%d', '%.15f', '%.15f', '%.15f', '%.15f'])
            elif motion_analysis.lower() == 'com':
                with open(target_name_data, 'wb') as f:
                    f.write(b'Time ComX ComY\n')
                    np.savetxt(f, df.values, delimiter=' ', fmt=['%d', '%.15f', '%.15f'])
            elif motion_analysis.lower() == 'qom':
                with open(target_name_data, 'wb') as f:
                    f.write(b'Time Qom\n')
                    np.savetxt(f, df.values, delimiter=' ', fmt=['%d', '%d'])
            elif motion_analysis.lower() == 'all':
                with open(target_name_data, 'wb') as f:
                    f.write(b'Time Qom ComX ComY AomX1 AomY1 AomX2 AomY2\n')
                    np.savetxt(f, df.values, delimiter=' ', fmt=['%d', '%d', '%.15f', '%.15f', '%.15f', '%.15f', '%.15f', '%.15f'])


        elif data_format not in ["tsv", "csv", "txt"]:
            print(
                f"Invalid data format: '{data_format}'.\nFalling back to '.csv'.")
            save_single_file(of, time, aom, com, qom, width, height, "csv",
                             target_name_data=target_name_data, overwrite=overwrite)

    if type(data_format) == str:
        save_single_file(of, time, aom, com, qom, motion_analysis, width, height, data_format, target_name_data=target_name_data, overwrite=overwrite)

    elif type(data_format) == list:
        if all([item.lower() in ["csv", "tsv", "txt"] for item in data_format]):
            data_format = list(set(data_format))
            [save_single_file(of, time, aom, com, qom, motion_analysis, width, height, item, target_name_data=target_name_data, overwrite=overwrite)
             for item in data_format]
        else:
            print(f"Unsupported formats in {data_format}.\nFalling back to '.csv'.")
            save_single_file(of, time, aom, com, qom, motion_analysis, width, height, "csv", target_name_data=target_name_data, overwrite=overwrite)

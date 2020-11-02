

def mg_progressbar(
        iteration,
        total,
        prefix='',
        suffix='',
        decimals=1,
        length=40,
        fill='█',
        printEnd="\r"):
    """
    Calls in a loop to create terminal progress bar.

    Parameters
    ----------
    - iteration : int

        Current iteration.
    - total : int

        Total iterations.
    - prefix : str, optional

        Prefix string.
    - suffix : str, optional

        Suffix string.
    - decimals : int, optional

        Default is 1. Positive number of decimals in percent complete.
    - length : int, optional

        Default is 40. Character length of bar.
    - fill : str, optional

        Default is '█'. Bar fill character.
    - printEnd : str, optional.

        Default is '\\r'. End of line character.
    """
    import sys

    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    sys.stdout.flush()
    sys.stdout.write('\r%s |%s| %s%% %s' %
                     (prefix, bar, percent, suffix))
    # Print New Line on Complete
    if iteration == total:
        print()


def mg_show_deprecated(self, filename=None, key=None):
    """
    This function simply plays the current vidcap VideoObject. The speed of the video playback 
    might not match the true fps due to non-optimized code. 

    Parameters
    ----------
    - filename : str, optional

        Default is `None`. If `None`, the current video to which the MgObject points is played.
        If filename is given, this file is played instead. 
    - key : {None, 'mgx', 'mgy', 'average', 'plot', 'motion', 'history', 'motionhistory', 'sparse', 'dense'}, optional

        If either of these shorthands is used the method attempts to show the 
        (previously rendered) video file corresponding to the one in the MgObject.
    """

    video_mode = True

    def show_image(ending, title=''):
        video_mode = False
        img = cv2.imread(self.of + ending, 3)
        cv2.imshow(title, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if filename == None:

        if key == None:
            filename = self.of+self.fex
        elif key.lower() == 'mgx':
            show_image('_mgx.png', 'Horizontal Motiongram')
        elif key.lower() == 'mgy':
            show_image('_mgy.png', 'Vertical Motiongram')
        elif key.lower() == 'average':
            show_image('_average.png', 'Average')
        elif key.lower() == 'plot':
            show_image('_motion_com_qom.png',
                       'Centroid and Quantity of Motion')

        elif key.lower() == 'motion':
            if os.path.exists(self.of + '_motion' + self.fex):
                filename = self.of + '_motion' + self.fex
            else:
                print("No motion video found corresponding to",
                      self.of+self.fex, ". Try making one with .motion()")
        elif key.lower() == 'history':
            if os.path.exists(self.of + '_history' + self.fex):
                filename = self.of + '_history' + self.fex
            else:
                print("No history video found corresponding to",
                      self.of+self.fex, ". Try making one with .history()")
        elif key.lower() == 'motionhistory':
            if os.path.exists(self.of + '_motion_history' + self.fex):
                filename = self.of + '_motion_history' + self.fex
            else:
                print("No motion history video found corresponding to",
                      self.of+self.fex, ". Try making one with .motionhistory()")
        elif key.lower() == 'sparse':
            if os.path.exists(self.of + '_flow_sparse' + self.fex):
                filename = self.of + '_flow_sparse' + self.fex
            else:
                print("No sparse optical flow video found corresponding to",
                      self.of+self.fex, ". Try making one with .flow.sparse()")
        elif key.lower() == 'dense':
            if os.path.exists(self.of + '_flow_dense' + self.fex):
                filename = self.of + '_flow_dense' + self.fex
            else:
                print("No dense optical flow video found corresponding to",
                      self.of+self.fex, ". Try making one with .flow.dense()")
        else:
            print("Unknown shorthand.\n",
                  "For images, try 'mgx', 'mgy', 'average' or 'plot'.\n",
                  "For videos try 'motion', 'history', 'motionhistory', 'sparse' or 'dense'.\n",
                  "Showing video from the MgObject.")
            filename = self.of+self.fex

    if self.fex == '.png':
        video_mode = False
        show_image('.png')

    if video_mode and (filename != None):
        vidcap = cv2.VideoCapture(filename)
        fps = float(vidcap.get(cv2.CAP_PROP_FPS))
        # Check if camera opened successfully
        if (vidcap.isOpened() == False):
            print("Error opening video stream or file")
        i = int(np.round((1/fps)*1000))

        video_title = os.path.basename(filename)

        # Read until video is completed
        while(vidcap.isOpened()):
            # Capture frame-by-frame
            ret, frame = vidcap.read()
            if ret == True:

                # Display the resulting frame
                cv2.imshow(video_title, frame)

                # Press Q on keyboard to  exit
                # if cv2.waitKey(i) & 0xFF == ord('q'):
                if cv2.waitKey(i) & 0xFF in [27, ord('q'), ord(' ')]:
                    break

            # Break the loop
            else:
                break
        # When everything done, release the video capture object
        vidcap.release()

        # Closes all the frames
        cv2.destroyAllWindows()


def contrast_brightness_cv2(of, fex, vidcap, fps, length, width, height, contrast, brightness):
    """
    Applies contrast and brightness to a video.

    Parameters
    ----------
    - of : str

        'Only filename' without extension (but with path to the file).
    - fex : str

        File extension.
    - vidcap : 

        cv2 capture of video file, with all frames ready to be read with `vidcap.read()`.
    - fps : int

        The FPS (frames per second) of the input video capture.
    - length : int

        The number of frames in the input video capture.
    - width : int

        The pixel width of the input video capture. 
    - height : int

        The pixel height of the input video capture. 
    - contrast : int or float, optional

        Applies +/- 100 contrast to video.
    - brightness : int or float, optional

        Applies +/- 100 brightness to video.

    Outputs
    -------
    - A video file with the name `of` + '_cb' + `fex`.

    Returns
    -------
    - cv2 video capture of output video file.
    """
    pb = MgProgressbar(
        total=length, prefix='Adjusting contrast and brightness:')
    count = 0
    if brightness != 0 or contrast != 0:
        # keeping values in sensible range
        contrast = np.clip(contrast, -100.0, 100.0)
        brightness = np.clip(brightness, -100.0, 100.0)

        contrast *= 1.27
        brightness *= 2.55

        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_cb' + fex, fourcc, fps, (width, height))
        success, image = vidcap.read()
        while success:
            success, image = vidcap.read()
            if not success:
                pb.progress(length)
                break
            image = np.int16(image) * (contrast/127+1) - contrast + brightness
            image = np.clip(image, 0, 255)
            out.write(image.astype(np.uint8))
            pb.progress(count)
            count += 1
        out.release()
        vidcap = cv2.VideoCapture(of + '_cb' + fex)

    return vidcap


def skip_frames_cv2(of, fex, vidcap, skip, fps, length, width, height):
    """
    Time-shrinks the video by skipping (discarding) every n frames determined by `skip`.

    Parameters
    ----------
    - of : str

        'Only filename' without extension (but with path to the file).
    - fex : str

        File extension.
    - vidcap : 

        cv2 capture of video file, with all frames ready to be read with `vidcap.read()`.
    - skip : int

        Every n frames to discard. `skip=0` keeps all frames, `skip=1` skips every other frame.
    - fps : int

        The FPS (frames per second) of the input video capture.
    - length : int

        The number of frames in the input video capture.
    - width : int

        The pixel width of the input video capture. 
    - height : int

        The pixel height of the input video capture.

    Outputs
    -------
    - A video file with the name `of` + '_skip' + `fex`.

    Returns
    -------
    - videcap :

        cv2 video capture of output video file.
    - length : int

        The number of frames in the output video file.
    - fps : int

        The FPS (frames per second) of the output video file.
    - width : int

        The pixel width of the output video file. 
    - height : int

        The pixel height of the output video file. 
    """
    pb = MgProgressbar(total=length, prefix='Skipping frames:')
    count = 0
    if skip != 0:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_skip' + fex, fourcc,
                              int(fps), (width, height))  # don't change fps, with higher skip values we want shorter videos
        success, image = vidcap.read()
        while success:
            success, image = vidcap.read()
            if not success:
                pb.progress(length)
                break
            # on every frame we wish to use
            if (count % (skip+1) == 0):  # NB if skip=1, we should keep every other frame
                out.write(image.astype(np.uint8))
            pb.progress(count)
            count += 1
        out.release()
        vidcap.release()
        vidcap = cv2.VideoCapture(of + '_skip' + fex)

        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return vidcap, length, fps, width, height


def videograms_cv2(self):
    """
    Uses cv2 as backend. Averages videoframes by axes, and creates two images of the horizontal-axis and vertical-axis stacks.
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
    - list(str, str)

        A tuple with the string paths to the horizontal and vertical videograms respectively. 
    """

    vidcap = cv2.VideoCapture(self.of+self.fex)
    ret, frame = vidcap.read()

    vgramx = np.zeros([1, self.width, 3])
    vgramy = np.zeros([self.height, 1, 3])

    ii = 0

    pb = MgProgressbar(total=self.length, prefix="Rendering videograms:")

    if self.color == False:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        vgramx = np.zeros([1, self.width])
        vgramy = np.zeros([self.height, 1])

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

            vgramy = np.append(vgramy, mean_x, axis=1)
            vgramx = np.append(vgramx, mean_y, axis=0)

        else:
            pb.progress(self.length)
            break

        pb.progress(ii)
        ii += 1

    if self.color == False:
        # Normalize before converting to uint8 to keep precision
        vgramx = vgramx/vgramx.max()*255
        vgramy = vgramy/vgramy.max()*255
        vgramx = cv2.cvtColor(vgramx.astype(
            np.uint8), cv2.COLOR_GRAY2BGR)
        vgramy = cv2.cvtColor(vgramy.astype(
            np.uint8), cv2.COLOR_GRAY2BGR)

    cv2.imwrite(self.of+'_vgy.png', vgramy.astype(np.uint8))
    cv2.imwrite(self.of+'_vgx.png', vgramx.astype(np.uint8))

    vidcap.release()

    return [self.of+'_vgx.png', self.of+'_vgy.png']

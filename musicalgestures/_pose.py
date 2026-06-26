
import cv2
import os
import sys
import numpy as np
import pandas as pd
from musicalgestures._utils import MgProgressbar, convert_to_avi, extract_wav, embed_audio_in_video, roundup, frame2ms, generate_outfilename, in_colab, get_cuda_device_count, cuda_unavailable_reason, ffmpeg_cmd
import musicalgestures
import itertools

# implementation mainly inspired by: https://github.com/spmallick/learnopencv/blob/master/OpenPose/OpenPoseVideo.py

# MediaPipe Pose skeleton connections (pairs of landmark indices)
MEDIAPIPE_POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    (11, 12),
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (15, 17), (15, 19), (15, 21), (17, 19),
    (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24),
    (23, 24),
    (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
    (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
]

# OpenPose marker names per model (order matches the network keypoint indices)
OPENPOSE_NAMES = {
    'coco': ['Nose', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder',
             'Left Elbow', 'Left Wrist', 'Right Hip', 'Right Knee', 'Right Ankle', 'Left Hip',
             'Left Knee', 'Left Ankle', 'Right Eye', 'Left Eye', 'Right Ear', 'Left Ear'],
    'mpi': ['Head', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder',
            'Left Elbow', 'Left Wrist', 'Right Hip', 'Right Knee', 'Right Ankle', 'Left Hip',
            'Left Knee', 'Left Ankle', 'Chest'],
    'body_25': ['Nose', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder',
                'Left Elbow', 'Left Wrist', 'Mid Hip', 'Right Hip', 'Right Knee', 'Right Ankle',
                'Left Hip', 'Left Knee', 'Left Ankle', 'Right Eye', 'Left Eye', 'Right Ear',
                'Left Ear', 'Left Big Toe', 'Left Small Toe', 'Left Heel', 'Right Big Toe',
                'Right Small Toe', 'Right Heel'],
}


import contextlib


@contextlib.contextmanager
def _suppress_native_stderr(active=True):
    """
    Temporarily redirect the process's stderr (fd 2) to /dev/null.

    MediaPipe logs from its C++/GL layer (EGL init, absl INFO/WARNING) go straight to
    the stderr file descriptor and can't be silenced from Python logging. This redirects
    fd 2 around the MediaPipe run so those messages don't clutter notebooks. No-op when
    ``active`` is False (use ``quiet=False`` to see the native logs for debugging).
    """
    if not active:
        yield
        return
    import sys
    sys.stderr.flush()
    devnull = os.open(os.devnull, os.O_WRONLY)
    saved = os.dup(2)
    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(saved, 2)
        os.close(devnull)
        os.close(saved)


def _pose_canvas_and_colors(frame, overlay, background):
    """Return (canvas, line_color, marker_color) in BGR for drawing the pose."""
    if overlay:
        return frame, (0, 255, 255), (0, 0, 255)            # over video: yellow lines, red markers
    if str(background).lower() == 'white':
        return np.full_like(frame, 255), (180, 60, 0), (0, 0, 200)   # white bg: dark blue lines, dark red markers
    return np.zeros_like(frame), (0, 255, 255), (0, 0, 255)  # black bg: yellow lines, red markers


def pose(
        self,
        model='body_25',
        device='gpu',
        threshold=0.1,
        downsampling_factor=2,
        save_data=True,
        data_format='csv',
        save_video=True,
        style='both',
        overlay=True,
        background='black',
        convert=True,
        quiet=True,
        save_average_pose=True,
        save_trajectories=True,
        transparent_trajectories=None,
        target_name_video=None,
        target_name_data=None,
        target_name_average=None,
        target_name_trajectories=None,
        overwrite=False):
    """
    Renders a video with the pose estimation (aka. "keypoint detection" or "skeleton tracking") overlaid on it.
    Outputs the predictions in a text file containing the normalized x and y coordinates of each keypoint
    (default format is csv).

    Supports two backends:

    * **MediaPipe** (``model='mediapipe'``): Uses Google's MediaPipe Pose which detects 33
      landmarks. Runs on CPU, or on GPU via MediaPipe's GPU delegate when ``device='gpu'``
      (with automatic CPU fallback if the delegate is unavailable). Requires the optional
      ``mediapipe`` package (``pip install musicalgestures[pose]``). On first use, the model
      file (~8–28 MB) is downloaded automatically and cached in ``musicalgestures/models/``.
    * **OpenPose** (``model='body_25'``, ``'coco'``, or ``'mpi'``): Uses Caffe-based OpenPose
      models.  Model weights (~200 MB) are downloaded on first use. GPU here requires an
      OpenCV built with CUDA; if unavailable while ``device='gpu'``, ``pose()`` automatically
      switches to the MediaPipe backend (when installed) for GPU acceleration.

    Args:
        model (str, optional): Pose model to use. ``'mediapipe'`` uses MediaPipe Pose (33
            landmarks, model auto-downloaded on first use). ``'body_25'`` loads the OpenPose BODY_25 model
            (25 keypoints), ``'mpi'`` loads the MPII model (15 keypoints), ``'coco'`` loads
            the COCO model (18 keypoints). Defaults to 'body_25'.
        device (str, optional): Compute backend ('cpu' or 'gpu'). For OpenPose models this
            selects the OpenCV DNN backend (GPU needs a CUDA-enabled OpenCV). For MediaPipe
            it selects the inference delegate (GPU delegate with CPU fallback). Defaults to 'gpu'.
        threshold (float, optional): The normalized confidence threshold that decides whether we
            keep or discard a predicted point. Discarded points get substituted with (0, 0) in the
            output data. Defaults to 0.1.
        downsampling_factor (int, optional): Decides how much we downsample the video before we
            pass it to the neural network. Ignored when ``model='mediapipe'``. Defaults to 2.
        save_data (bool, optional): Whether we save the predicted pose data to a file. Defaults to True.
        data_format (str, optional): Specifies format of pose-data. Accepted values are 'csv', 'tsv'
            and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
        save_video (bool, optional): Whether we save the video with the estimated pose overlaid on it.
            Defaults to True.
        style (str, optional): How to draw the pose. `'both'` draws markers (keypoints) connected by
            joint lines (the skeleton); `'markers'` draws only the keypoints; `'skeleton'` draws only
            the connecting joint lines. Defaults to 'both'.
        overlay (bool, optional): If True, draw the pose on top of the original video frames. If False,
            draw it on a plain background instead (a "markers only" video with no video underneath).
            Defaults to True.
        background (str, optional): Background colour used when `overlay=False`: `'black'` (default) or
            `'white'`. On a white background the markers and joint lines are drawn in darker, higher-contrast
            colours. Ignored when `overlay=True`.
        convert (bool, optional): If True (default), non-AVI input is first converted to an all-intra
            MJPEG `.avi` (cached as ``self.as_avi``) for frame-accurate decoding. Set to False to read the
            source file directly — faster and no extra file, suitable when your mp4 decodes reliably.
        quiet (bool, optional): MediaPipe only. If True (default), suppress MediaPipe's native C++/GL
            console logs (EGL init, absl INFO/WARNING, GPU-delegate messages) during inference. Set to
            False to see them for debugging.
        target_name_video (str, optional): Target output name for the video. Defaults to None (which
            assumes that the input filename with the suffix "_pose" should be used).
        save_average_pose (bool, optional): Whether to also render an image of the average pose over
            the whole video, with each marker coloured/labelled by its average quantity of motion
            (px/frame) and labelled with its dominant movement frequency (Hz). A CSV of the per-marker
            statistics is saved alongside it. Defaults to True.
        save_trajectories (bool, optional): Whether to also render an image of every marker's spatial
            trajectory across the whole video. Defaults to True.
        target_name_data (str, optional): Target output name for the data. Defaults to None (which
            assumes that the input filename with the suffix "_pose" should be used).
        target_name_average (str, optional): Target output name for the average-pose image. Defaults
            to None (input filename with the suffix "_pose_average.png").
        target_name_trajectories (str, optional): Target output name for the trajectories image.
            Defaults to None (input filename with the suffix "_pose_trajectories.png").
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically
            increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgVideo: An MgVideo pointing to the output video. The average-pose and trajectories images
            (when rendered) are attached as ``.average_pose`` and ``.trajectories`` (MgImage), and the
            collected keypoints are available on the parent object as ``self.pose_average`` /
            ``self.pose_trajectories``.
    """

    style = str(style).lower()
    if style not in ('both', 'markers', 'skeleton'):
        print(f"Unrecognized style '{style}', falling back to 'both'. Use 'both', 'markers' or 'skeleton'.")
        style = 'both'

    background = str(background).lower()
    if background not in ('black', 'white'):
        print(f"Unrecognized background '{background}', falling back to 'black'. Use 'black' or 'white'.")
        background = 'black'

    # --- MediaPipe backend ---------------------------------------------------
    # Explicit MediaPipe request, or auto-preference: when GPU is requested for an
    # OpenPose model but OpenCV has no CUDA backend, fall back to the (fast, reliable)
    # MediaPipe pose backend instead of CPU OpenPose. We use the CPU delegate here:
    # MediaPipe's GPU delegate is the OpenGL-ES path (the integrated GPU on Linux, not
    # an NVIDIA card) and is fragile, so it is reserved for explicit model='mediapipe',
    # device='gpu' requests.
    use_mediapipe = model.lower() == 'mediapipe'
    mediapipe_device = device
    if not use_mediapipe and device.lower() == 'gpu' and not in_colab() and get_cuda_device_count() <= 0:
        if _mediapipe_available():
            print(
                f"GPU requested but OpenCV has no CUDA backend; switching from '{model}' to the "
                "MediaPipe pose backend (CPU/XNNPACK — fast and reliable).\n  "
                + cuda_unavailable_reason()
            )
            use_mediapipe = True
            mediapipe_device = 'cpu'
        # else: fall through to the OpenPose path, which will warn and use CPU.

    if use_mediapipe:
        return _pose_mediapipe(
            self,
            device=mediapipe_device,
            threshold=threshold,
            save_data=save_data,
            data_format=data_format,
            save_video=save_video,
            style=style,
            overlay=overlay,
            background=background,
            convert=convert,
            quiet=quiet,
            save_average_pose=save_average_pose,
            save_trajectories=save_trajectories,
            transparent_trajectories=transparent_trajectories,
            target_name_video=target_name_video,
            target_name_data=target_name_data,
            target_name_average=target_name_average,
            target_name_trajectories=target_name_trajectories,
            overwrite=overwrite,
        )
    # -------------------------------------------------------------------------

    module_path = os.path.abspath(os.path.dirname(musicalgestures.__file__))

    if model.lower() == 'mpi':
        protoFile = module_path + '/pose/mpi/pose_deploy_linevec_faster_4_stages.prototxt'
        weightsFile = module_path + '/pose/mpi/pose_iter_160000.caffemodel'
        model = 'mpi'
        nPoints = 15
        POSE_PAIRS = [[0, 1], [1, 2], [2, 3], [3, 4], [1, 5], [5, 6], [6, 7], [
            1, 14], [14, 8], [8, 9], [9, 10], [14, 11], [11, 12], [12, 13]]
    elif model.lower() == 'coco':
        protoFile = module_path + '/pose/coco/pose_deploy_linevec.prototxt'
        weightsFile = module_path + '/pose/coco/pose_iter_440000.caffemodel'
        model = 'coco'
        nPoints = 18
        POSE_PAIRS = [[1, 0], [1, 2], [1, 5], [2, 3], [3, 4], [5, 6], [6, 7], [1, 8], [
            8, 9], [9, 10], [1, 11], [11, 12], [12, 13], [0, 14], [0, 15], [14, 16], [15, 17]]
    elif model.lower() == 'body_25':
        protoFile = module_path + '/pose/body_25/pose_deploy.prototxt'
        weightsFile = module_path + '/pose/body_25/pose_iter_584000.caffemodel'
        model = 'body_25'
        nPoints = 25
        POSE_PAIRS = [[1, 8], [1, 2], [1, 5], [2, 3], [3, 4], [5, 6], [6, 7], [8, 9], [9, 10], [10, 11], [8, 12], [12, 13], [
            13, 14], [1, 0], [0, 15], [15, 17], [0, 16], [16, 18], [14, 19], [19, 20], [14, 21], [11, 22], [22, 23], [11, 24]]
    else:
        print(f'Unrecognized model "{model}", switching to default (mpi).')
        protoFile = module_path + '/pose/mpi/pose_deploy_linevec_faster_4_stages.prototxt'
        weightsFile = module_path + '/pose/mpi/pose_iter_160000.caffemodel'
        model = 'mpi'

    # Check if .caffemodel file exists, download if necessary
    if not os.path.exists(weightsFile):
        print('Could not find weights file.')
        # Notebook/nbclient runs cannot satisfy input(), so auto-download in non-interactive mode.
        if not sys.stdin or not sys.stdin.isatty():
            print('Non-interactive session detected. Downloading model weights automatically (~200MB).')
            download_model(model)
        else:
            print('Do you want to download it (~200MB)? (y/n)')
            answer = input()
            if answer.lower() == 'n':
                print('Ok. Exiting...')
                return musicalgestures.MgVideo(self.filename, color=self.color, returned_by_process=True)
            elif answer.lower() == 'y':
                download_model(model)
            else:
                print(f'Unrecognized answer "{answer}". Exiting...')
                return musicalgestures.MgVideo(self.filename, color=self.color, returned_by_process=True)

        if not os.path.exists(weightsFile):
            print('Model weights are still missing after download attempt. Exiting pose() call.')
            return musicalgestures.MgVideo(self.filename, color=self.color, returned_by_process=True)

    # Read the network into Memory
    net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)
    device = device.lower()
    # enforce CPU device in Colab
    if in_colab() and device == 'gpu':
        print('Sorry, OpenCV GPU acceleration is not supported in Colab. Switching to CPU.')
        device = 'cpu'
    elif device == 'gpu':
        if get_cuda_device_count() <= 0:
            print('OpenCV CUDA backend is unavailable. Switching to CPU.\n  ' + cuda_unavailable_reason())
            device = 'cpu'

    if device == "cpu":
        net.setPreferableBackend(cv2.dnn.DNN_TARGET_CPU)
    elif device == "gpu":
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    else:
        print(f'Unrecognized device "{device}", switching to default (cpu).')
        net.setPreferableBackend(cv2.dnn.DNN_TARGET_CPU)

    of, fex = os.path.splitext(self.filename)

    if convert and fex.lower() != '.avi':
        # first check if there already is a converted version, if not create one and register it to the parent self
        if "as_avi" not in self.__dict__.keys():
            file_as_avi = convert_to_avi(of + fex, overwrite=overwrite)
            # register it as the avi version for the file
            self.as_avi = musicalgestures.MgVideo(file_as_avi)
        # point of and fex to the avi version
        of, fex = self.as_avi.of, self.as_avi.fex
        filename = of + fex
    else:
        # use the source file directly (e.g. an mp4 that decodes frame-accurately)
        filename = self.filename

    inWidth = int(roundup(self.width/downsampling_factor, 2))
    inHeight = int(roundup(self.height/downsampling_factor, 2))

    pb = MgProgressbar(total=self.length, prefix='Rendering pose estimation video:')

    if save_video:
        if target_name_video is None:
            target_name_video = of + '_pose' + fex
        # if a target name was given we still enforce the .avi container anyway
        else:
            target_name_video = os.path.splitext(target_name_video)[0] + fex
        if not overwrite:
            target_name_video = generate_outfilename(target_name_video)
            
    # Pipe video with FFmpeg for reading frame by frame
    cmd = ['ffmpeg', '-y', '-i', filename] # define ffmpeg command        
    process = ffmpeg_cmd(cmd, total_time=self.length, pipe='read')
    video_out = None

    ii = 0
    data = []
    # Accumulate the average frame as a background for the average-pose image
    collect_extra = save_average_pose or save_trajectories
    avg_acc = np.zeros((self.height, self.width, 3), dtype=np.float64) if save_average_pose else None
    avg_n = 0

    while True:
        # Read frame-by-frame
        out = process.stdout.read(self.width*self.height*3)

        if out == b'':
            pb.progress(self.length)
            break

        # Transform the bytes read into a numpy array
        frame = np.frombuffer(out, dtype=np.uint8).reshape([self.height, self.width, 3]).copy() # height, width, channels

        if avg_acc is not None:
            avg_acc += frame
            avg_n += 1

        inpBlob = cv2.dnn.blobFromImage(frame, 1.0 / 255, (inWidth, inHeight), (0, 0, 0), swapRB=False, crop=False)
        net.setInput(inpBlob)
        output = net.forward()

        H = output.shape[2]
        W = output.shape[3]
        points = []

        for i in range(nPoints):

            # confidence map of corresponding body's part.
            probMap = output[0, i, :, :]

            # Find global maxima of the probMap.
            minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)

            # Scale the point to fit on the original image
            x = (self.width * point[0]) / W
            y = (self.height * point[1]) / H

            if prob > threshold:
                points.append((int(x), int(y)))

            else:
                points.append(None)

        # Always collect keypoints so the average-pose/trajectories images can be built
        # even when save_data is False (saving to file is gated separately below).
        if save_data or collect_extra:
            time = frame2ms(ii, self.fps)
            points_list = [[list(point)[0]/self.width, list(point)[1]/self.height, ] if point is not None else [
                0, 0] for point in points]
            points_list_flat = itertools.chain.from_iterable(points_list)
            datapoint = [time]
            datapoint += points_list_flat
            data.append(datapoint)

        # Draw on the video frame, or on a plain canvas when overlay is disabled
        canvas, line_color, marker_color = _pose_canvas_and_colors(frame, overlay, background)

        # Joint lines (skeleton)
        if style in ('both', 'skeleton'):
            for pair in POSE_PAIRS:
                partA, partB = pair[0], pair[1]
                if points[partA] and points[partB]:
                    cv2.line(canvas, points[partA], points[partB],
                             line_color, 2, lineType=cv2.LINE_AA)

        # Markers (keypoints)
        if style in ('both', 'markers'):
            for point in points:
                if point is not None:
                    cv2.circle(canvas, point, 4, marker_color, thickness=-1, lineType=cv2.FILLED)

        frame = canvas

        if save_video:
            if video_out is None:
                cmd =['ffmpeg', '-y', '-s', '{}x{}'.format(frame.shape[1], frame.shape[0]), 
                    '-r', str(self.fps), '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', 
                    '-i', '-', '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', target_name_video]
                video_out = ffmpeg_cmd(cmd, total_time=self.length, pipe='write')

            video_out.stdin.write(frame.astype(np.uint8))
            
        # Flush the buffer
        process.stdout.flush()
        pb.progress(ii)
        ii += 1

    # Terminate the processes
    if save_video:
        video_out.stdin.close()
        video_out.wait()
        # Check if the original video fil has audio
        if self.has_audio:
            source_audio = extract_wav(of + fex)
            embed_audio_in_video(source_audio, target_name_video)
            os.remove(source_audio)

    process.terminate()

    def save_txt(of, width, height, model, data, data_format, target_name_data, overwrite):
        """
        Helper function to export pose estimation data as textfile(s).
        """
        def save_single_file(of, width, height, model, data, data_format, target_name_data, overwrite):
            """
            Helper function to export pose estimation data as a textfile using pandas.
            """

            coco_table = ['Nose', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder', 'Left Elbow', 'Left Wrist', 'Right Hip',
                          'Right Knee', 'Right Ankle', 'Left Hip', 'Left Knee', 'Left Ankle', 'Right Eye', 'Left Eye', 'Right Ear', 'Left Ear']
            mpi_table = ['Head', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder', 'Left Elbow',
                         'Left Wrist', 'Right Hip', 'Right Knee', 'Right Ankle', 'Left Hip', 'Left Knee', 'Left Ankle', 'Chest']
            body_25_table = ['Nose', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder', 'Left Elbow', 'Left Wrist', 'Mid Hip', 'Right Hip', 'Right Knee', 'Right Ankle', 'Left Hip',
                             'Left Knee', 'Left Ankle', 'Right Eye', 'Left Eye', 'Right Ear', 'Left Ear', "Left Big Toe", "Left Small Toe", "Left Heel", "Right Big Toe", "Right Small Toe", "Right Heel"]
            headers = ['Time']

            table_to_use = []
            if model.lower() == 'mpi':
                table_to_use = mpi_table
            elif model.lower() == 'coco':
                table_to_use = coco_table
            elif model.lower() == 'body_25':
                table_to_use = body_25_table

            for i in range(len(table_to_use)):
                header_x = table_to_use[i] + ' X'
                header_y = table_to_use[i] + ' Y'
                headers.append(header_x)
                headers.append(header_y)

            data_format = data_format.lower()

            df = pd.DataFrame(data=data, columns=headers)

            if data_format == "tsv":

                if target_name_data is None:
                    target_name_data = of+'_pose.tsv'
                else:
                    # take name, but enforce tsv
                    target_name_data = os.path.splitext(
                        target_name_data)[0] + '.tsv'
                if not overwrite:
                    target_name_data = generate_outfilename(target_name_data)

                with open(target_name_data, 'wb') as f:
                    head_str = ''
                    for head in headers:
                        head_str += head + '\t'
                    head_str += '\n'
                    f.write(head_str.encode())
                    fmt_list = ['%d']
                    fmt_list += ['%.15f' for item in range(
                        len(table_to_use)*2)]
                    np.savetxt(f, df.values, delimiter='\t', fmt=fmt_list)

            elif data_format == "csv":

                if target_name_data is None:
                    target_name_data = of+'_pose.csv'
                else:
                    # take name, but enforce csv
                    target_name_data = os.path.splitext(
                        target_name_data)[0] + '.csv'
                if not overwrite:
                    target_name_data = generate_outfilename(target_name_data)

                df.to_csv(target_name_data, index=None)

            elif data_format == "txt":

                if target_name_data is None:
                    target_name_data = of+'_pose.txt'
                else:
                    # take name, but enforce txt
                    target_name_data = os.path.splitext(
                        target_name_data)[0] + '.txt'
                if not overwrite:
                    target_name_data = generate_outfilename(target_name_data)

                with open(target_name_data, 'wb') as f:
                    head_str = ''
                    for head in headers:
                        head_str += head + ' '
                    head_str += '\n'
                    f.write(head_str.encode())
                    fmt_list = ['%d']
                    fmt_list += ['%.15f' for item in range(
                        len(table_to_use)*2)]
                    np.savetxt(f, df.values, delimiter=' ', fmt=fmt_list)
            elif data_format not in ["tsv", "csv", "txt"]:
                print(
                    f"Invalid data format: '{data_format}'.\nFalling back to '.csv'.")
                save_single_file(of, width, height, model, data, "csv",
                                 target_name_data=target_name_data, overwrite=overwrite)

        if type(data_format) == str:
            save_single_file(of, width, height, model, data, data_format,
                             target_name_data=target_name_data, overwrite=overwrite)

        elif type(data_format) == list:
            if all([item.lower() in ["csv", "tsv", "txt"] for item in data_format]):
                data_format = list(set(data_format))
                [save_single_file(of, width, height, model, data, item, target_name_data=target_name_data, overwrite=overwrite)
                 for item in data_format]
            else:
                print(
                    f"Unsupported formats in {data_format}.\nFalling back to '.csv'.")
                save_single_file(of, width, height, model, data, "csv",
                                 target_name_data=target_name_data, overwrite=overwrite)

    if save_data:
        save_txt(of, self.width, self.height, model, data, data_format,
                 target_name_data=target_name_data, overwrite=overwrite)

    # Render the average-pose and trajectories images from the collected keypoints
    names = OPENPOSE_NAMES.get(model.lower())
    avg_frame = (avg_acc / avg_n).astype(np.uint8) if (avg_acc is not None and avg_n > 0) else None
    average_image, trajectories_image = _render_pose_extras(
        data, names, POSE_PAIRS, self.width, self.height, self.fps,
        avg_frame, of, save_average_pose, save_trajectories,
        target_name_average, target_name_trajectories, overwrite,
        transparent_trajectories=transparent_trajectories, style=style)
    self.pose_average = average_image
    self.pose_trajectories = trajectories_image

    if save_video:
        # save result as pose_video for parent MgVideo
        self.pose_video = musicalgestures.MgVideo(target_name_video, color=self.color, returned_by_process=True)
        self.pose_video.average_pose = average_image
        self.pose_video.trajectories = trajectories_image
        return self.pose_video
    else:
        # otherwise just return the parent MgVideo
        return self


def _render_pose_extras(data, names, connections, width, height, fps, avg_frame, of,
                        save_average_pose, save_trajectories,
                        target_name_average, target_name_trajectories, overwrite,
                        transparent_trajectories=None, style='both'):
    """Render the average-pose and trajectories images from collected keypoints."""
    from musicalgestures._pose_visualize import render_average_pose, render_trajectories
    average_image = None
    trajectories_image = None
    if not data or not names:
        return None, None
    if save_average_pose:
        tn = target_name_average if target_name_average else of + '_pose_average.png'
        average_image = render_average_pose(data, names, connections, width, height, fps,
                                            avg_frame, tn, overwrite, style=style)
    if save_trajectories:
        tn = target_name_trajectories if target_name_trajectories else of + '_pose_trajectories.png'
        # Default: use a transparent background when trajectories are the only image exported,
        # so they can be overlaid on the video later. Explicit override via transparent_trajectories.
        transparent = transparent_trajectories if transparent_trajectories is not None else (not save_average_pose)
        trajectories_image = render_trajectories(data, names, width, height, fps, tn, overwrite,
                                                 transparent=transparent)
    return average_image, trajectories_image


def _mediapipe_available():
    """Returns True if the optional ``mediapipe`` package can be imported."""
    import importlib.util
    return importlib.util.find_spec('mediapipe') is not None


def _pose_mediapipe(
        self,
        device='cpu',
        threshold=0.1,
        save_data=True,
        data_format='csv',
        save_video=True,
        style='both',
        overlay=True,
        background='black',
        convert=True,
        quiet=True,
        save_average_pose=True,
        save_trajectories=True,
        transparent_trajectories=None,
        target_name_video=None,
        target_name_data=None,
        target_name_average=None,
        target_name_trajectories=None,
        overwrite=False):
    """
    Internal helper: run MediaPipe Pose on a video and render/save the output.
    Called by :func:`pose` when ``model='mediapipe'`` (or when GPU is requested and the
    OpenCV CUDA backend is unavailable). ``device`` selects the MediaPipe delegate
    ('gpu' uses the GPU delegate with automatic CPU fallback).
    """
    from musicalgestures._pose_estimator import MediaPipePoseEstimator, MEDIAPIPE_LANDMARK_NAMES

    style = str(style).lower()
    if style not in ('both', 'markers', 'skeleton'):
        style = 'both'
    background = str(background).lower()
    if background not in ('black', 'white'):
        background = 'black'

    of, fex = os.path.splitext(self.filename)

    if convert and fex.lower() != '.avi':
        if "as_avi" not in self.__dict__.keys():
            file_as_avi = convert_to_avi(of + fex, overwrite=overwrite)
            self.as_avi = musicalgestures.MgVideo(file_as_avi)
        of, fex = self.as_avi.of, self.as_avi.fex
        filename = of + fex
    else:
        filename = self.filename

    pb = MgProgressbar(total=self.length, prefix='Rendering MediaPipe pose estimation:')

    if save_video:
        if target_name_video is None:
            target_name_video = of + '_pose' + fex
        else:
            target_name_video = os.path.splitext(target_name_video)[0] + fex
        if not overwrite:
            target_name_video = generate_outfilename(target_name_video)

    # Pipe video with FFmpeg for reading frame by frame
    cmd = ['ffmpeg', '-y', '-i', filename]
    process = ffmpeg_cmd(cmd, total_time=self.length, pipe='read')
    video_out = None

    ii = 0
    data = []
    collect_extra = save_average_pose or save_trajectories
    avg_acc = np.zeros((self.height, self.width, 3), dtype=np.float64) if save_average_pose else None
    avg_n = 0

    estimator = MediaPipePoseEstimator(device=device.lower())

    while True:
        out = process.stdout.read(self.width * self.height * 3)

        if out == b'':
            pb.progress(self.length)
            break

        frame = np.frombuffer(out, dtype=np.uint8).reshape([self.height, self.width, 3]).copy()

        if avg_acc is not None:
            avg_acc += frame
            avg_n += 1

        with _suppress_native_stderr(quiet):
            result = estimator.predict_frame(frame)
        keypoints = result.keypoints  # shape (33, 3): x, y, visibility

        # Collect data row: time + normalised (x, y) for every landmark.
        # Always collected so the average-pose/trajectories images can be built.
        if save_data or collect_extra:
            time_ms = frame2ms(ii, self.fps)
            row = [time_ms]
            for i in range(len(MEDIAPIPE_LANDMARK_NAMES)):
                x, y, vis = keypoints[i]
                if vis >= threshold:
                    row += [float(x), float(y)]
                else:
                    row += [0.0, 0.0]
            data.append(row)

        # Draw on the video frame, or on a plain canvas when overlay is disabled
        canvas, line_color, marker_color = _pose_canvas_and_colors(frame, overlay, background)

        # Joint lines (skeleton)
        if style in ('both', 'skeleton'):
            for (a, b) in MEDIAPIPE_POSE_CONNECTIONS:
                xa, ya, va = keypoints[a]
                xb, yb, vb = keypoints[b]
                if va >= threshold and vb >= threshold:
                    pt_a = (int(xa * self.width), int(ya * self.height))
                    pt_b = (int(xb * self.width), int(yb * self.height))
                    cv2.line(canvas, pt_a, pt_b, line_color, 2, lineType=cv2.LINE_AA)

        # Markers (keypoints)
        if style in ('both', 'markers'):
            for i in range(len(MEDIAPIPE_LANDMARK_NAMES)):
                x, y, vis = keypoints[i]
                if vis >= threshold:
                    pt = (int(x * self.width), int(y * self.height))
                    cv2.circle(canvas, pt, 4, marker_color, thickness=-1, lineType=cv2.FILLED)

        frame = canvas

        if save_video:
            if video_out is None:
                cmd = ['ffmpeg', '-y', '-s', '{}x{}'.format(frame.shape[1], frame.shape[0]),
                       '-r', str(self.fps), '-f', 'rawvideo', '-pix_fmt', 'bgr24',
                       '-vcodec', 'rawvideo', '-i', '-', '-vcodec', 'libx264',
                       '-pix_fmt', 'yuv420p', target_name_video]
                video_out = ffmpeg_cmd(cmd, total_time=self.length, pipe='write')
            video_out.stdin.write(frame.astype(np.uint8))

        process.stdout.flush()
        pb.progress(ii)
        ii += 1

    with _suppress_native_stderr(quiet):
        estimator.close()

    if save_video:
        video_out.stdin.close()
        video_out.wait()
        if self.has_audio:
            source_audio = extract_wav(of + fex)
            embed_audio_in_video(source_audio, target_name_video)
            os.remove(source_audio)

    process.terminate()

    if save_data:
        # Build column headers from landmark names
        headers = ['Time']
        for name in MEDIAPIPE_LANDMARK_NAMES:
            headers.append(name.replace('_', ' ').title() + ' X')
            headers.append(name.replace('_', ' ').title() + ' Y')
        _save_pose_txt(of, data, headers, data_format, target_name_data, overwrite)

    # Render the average-pose and trajectories images from the collected keypoints
    names = [name.replace('_', ' ').title() for name in MEDIAPIPE_LANDMARK_NAMES]
    avg_frame = (avg_acc / avg_n).astype(np.uint8) if (avg_acc is not None and avg_n > 0) else None
    average_image, trajectories_image = _render_pose_extras(
        data, names, MEDIAPIPE_POSE_CONNECTIONS, self.width, self.height, self.fps,
        avg_frame, of, save_average_pose, save_trajectories,
        target_name_average, target_name_trajectories, overwrite,
        transparent_trajectories=transparent_trajectories, style=style)
    self.pose_average = average_image
    self.pose_trajectories = trajectories_image

    if save_video:
        self.pose_video = musicalgestures.MgVideo(target_name_video, color=self.color, returned_by_process=True)
        self.pose_video.average_pose = average_image
        self.pose_video.trajectories = trajectories_image
        return self.pose_video
    else:
        return self


def _save_pose_txt(of, data, headers, data_format, target_name_data, overwrite):
    """Save pose data to one or more text files (csv / tsv / txt)."""

    def _save_single(data_format):
        ext = '.' + data_format.lower()
        if target_name_data is None:
            out_path = of + '_pose' + ext
        else:
            out_path = os.path.splitext(target_name_data)[0] + ext
        if not overwrite:
            out_path = generate_outfilename(out_path)

        df = pd.DataFrame(data=data, columns=headers)

        if data_format.lower() == 'csv':
            df.to_csv(out_path, index=None)
        elif data_format.lower() in ('tsv', 'txt'):
            delimiter = '\t' if data_format.lower() == 'tsv' else ' '
            with open(out_path, 'wb') as f:
                head_str = delimiter.join(headers) + '\n'
                f.write(head_str.encode())
                fmt_list = ['%d'] + ['%.15f'] * (len(headers) - 1)
                np.savetxt(f, df.values, delimiter=delimiter, fmt=fmt_list)
        else:
            print(f"Invalid data format: '{data_format}'.\nFalling back to '.csv'.")
            _save_single('csv')

    if isinstance(data_format, str):
        _save_single(data_format)
    elif isinstance(data_format, list):
        valid = [f for f in data_format if f.lower() in ('csv', 'tsv', 'txt')]
        if len(valid) != len(data_format):
            invalid = [f for f in data_format if f.lower() not in ('csv', 'tsv', 'txt')]
            print(f"Unsupported formats {invalid}.\nFalling back to '.csv'.")
            _save_single('csv')
        else:
            for fmt in list(set(valid)):
                _save_single(fmt)


def download_model(modeltype):
    """
    Helper function to automatically download model (.caffemodel) files.
    """
    import platform
    import subprocess
    import os
    import musicalgestures

    module_path = os.path.abspath(os.path.dirname(musicalgestures.__file__))

    batch, shell, shell_colab = '_remote.bat', '_remote.sh', '_remote_colab.sh'

    the_system = platform.system()

    pb_prefix = ''
    mpi_script = module_path + '/pose/getMPI'
    coco_script = module_path + '/pose/getCOCO'
    body_25_script = module_path + '/pose/getBODY_25'
    wget_win = musicalgestures._utils.wrap_str(
        module_path + '/3rdparty/windows/wget/wget.exe')
    target_folder_mpi = musicalgestures._utils.wrap_str(
        module_path + '/pose/mpi')
    target_folder_coco = musicalgestures._utils.wrap_str(
        module_path + '/pose/coco')
    target_folder_body_25 = musicalgestures._utils.wrap_str(
        module_path + '/pose/body_25')

    if the_system == 'Windows':
        mpi_script += batch
        coco_script += batch
        body_25_script += batch
    elif in_colab():
        mpi_script += shell_colab
        coco_script += shell_colab
        body_25_script += shell_colab
    else:
        mpi_script += shell
        coco_script += shell
        body_25_script += shell

    if modeltype.lower() == 'mpi':
        command = musicalgestures._utils.wrap_str(mpi_script)
        if the_system == 'Windows':
            command += f' {wget_win} {target_folder_mpi}'
        else:
            command = 'bash ' + command
            command += f' {target_folder_mpi}'
        pb_prefix = 'Downloading MPI model:'
    elif modeltype.lower() == 'coco':
        command = coco_script
        if the_system == 'Windows':
            command += f' {wget_win} {target_folder_coco}'
        else:
            command = 'bash ' + command
            command += f' {target_folder_coco}'
        pb_prefix = 'Downloading COCO model:'
    elif modeltype.lower() == 'body_25':
        command = body_25_script
        if the_system == 'Windows':
            command += f' {wget_win} {target_folder_body_25}'
        else:
            command = 'bash ' + command
            command += f' {target_folder_body_25}'
        pb_prefix = 'Downloading BODY_25 model:'

    pb = MgProgressbar(total=100, prefix=pb_prefix)

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

    try:
        i = 0
        while True:
            out = process.stdout.readline()
            if out == '':
                process.wait()
                break
            elif out.find('%') != -1:
                percentage_place = out.find('%')
                percent = out[percentage_place-2:percentage_place]
                pb.progress(float(percent))
            # else:
            #     print(out)

    except KeyboardInterrupt:
        try:
            process.terminate()
        except OSError:
            pass
        process.wait()
        raise KeyboardInterrupt

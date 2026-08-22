from __future__ import annotations

import cv2
import os
import sys
import numpy as np
import pandas as pd
from musicalgestures._utils import MgProgressbar, convert_to_avi, extract_wav, embed_audio_in_video, roundup, frame2ms, generate_outfilename, in_colab, get_cuda_device_count, cuda_unavailable_reason, ffmpeg_cmd
import musicalgestures
import itertools
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # for the -> "MgFigure" return annotations on the pose_* methods
    from musicalgestures._utils import MgFigure

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

from musicalgestures._exceptions import MgDependencyError


def caffe_supported() -> bool:
    """Can this OpenCV build load a Caffe model?

    OpenCV 5.0 removed the Caffe importer: ``cv2.dnn.readNetFromCaffe`` no
    longer exists, and ``cv2.dnn.readNet`` raises rather than falling back.
    The OpenPose backends here (BODY_25, COCO, MPI) are Caffe models, so they
    cannot run on such a build at all. MediaPipe is unaffected.
    """
    return hasattr(cv2.dnn, 'readNetFromCaffe')


def _require_caffe_support():
    """Raise a message naming the cause and the ways out, or return."""
    if caffe_supported():
        return
    raise MgDependencyError(
        f"The OpenPose backends (body_25, coco, mpi) are Caffe models, and "
        f"this OpenCV ({cv2.__version__}) has no Caffe importer -- it was "
        f"removed in OpenCV 5.0. Either use MGT's other pose backend, "
        f"`pose(model='mediapipe')`, which needs `pip install mediapipe` and "
        f"gives 33 landmarks rather than BODY_25's 25; or install OpenCV 4 "
        f"(`pip install 'opencv-python<5'`) to keep the OpenPose skeletons. "
        f"The two are not interchangeable: the landmark sets differ, so "
        f"switching backend changes what the columns mean."
    )


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


def _draw_marker_trails(canvas, trail, color):
    """Draw each marker's path over the buffered recent frames (a fading history trail).

    trail: a sequence of (n_points, 2) pixel-coordinate arrays (np.nan = missing).
    """
    if trail is None or len(trail) < 2:
        return
    arr = np.asarray(trail, dtype=float)   # (F, n, 2)
    F, n, _ = arr.shape
    for j in range(n):
        track = arr[:, j, :]
        for f in range(1, F):
            p0, p1 = track[f - 1], track[f]
            if not (np.isnan(p0).any() or np.isnan(p1).any()):
                cv2.line(canvas, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])),
                         color, 1, lineType=cv2.LINE_AA)


def _pose_canvas_and_colors(frame, overlay, background):
    """Return (canvas, line_color, marker_color) in BGR for drawing the pose."""
    if overlay:
        return frame, (0, 255, 255), (0, 0, 255)            # over video: yellow lines, red markers
    if str(background).lower() == 'white':
        return np.full_like(frame, 255), (0, 0, 0), (0, 0, 0)   # white bg: black skeleton + markers (inverted)
    return np.zeros_like(frame), (0, 255, 255), (0, 0, 255)  # black bg: yellow lines, red markers


def pose(
        self,
        model: str = 'mediapipe',
        device: str = 'gpu',
        threshold: float = 0.1,
        downsampling_factor: int = 2,
        use_cache: bool = True,
        save_data: bool = True,
        data_format: str | list = 'csv',
        save_video: bool = True,
        style: str = 'both',
        overlay: bool = True,
        background: str = 'black',
        convert: bool | None = None,
        quiet: bool = True,
        marker_history: int = 0,
        save_average_pose: bool = True,
        save_trajectories: bool = True,
        transparent_trajectories: bool | None = None,
        trajectory_background: str | None = None,
        trajectory_labels: bool = False,
        target_name_video: str | None = None,
        target_name_data: str | None = None,
        target_name_average: str | None = None,
        target_name_trajectories: str | None = None,
        overwrite: bool = True) -> "musicalgestures.MgVideo":
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
        model (str, optional): Pose model to use. ``'mediapipe'`` (default) uses MediaPipe Pose (33
            landmarks with depth + visibility, model auto-downloaded on first use); it is fast on plain
            CPU, needs no CUDA build, and is best for single-person analysis. ``'body_25'`` loads the
            OpenPose BODY_25 model (25 keypoints), ``'mpi'`` loads the MPII model (15 keypoints),
            ``'coco'`` loads the COCO model (18 keypoints). The OpenPose models support multi-person
            scenes but are slow without a CUDA-enabled OpenCV build. Defaults to 'mediapipe'.
        device (str, optional): Compute backend ('cpu' or 'gpu'). For OpenPose models this
            selects the OpenCV DNN backend (GPU needs a CUDA-enabled OpenCV). For MediaPipe
            it selects the inference delegate (GPU delegate with CPU fallback). Defaults to 'gpu'.
        threshold (float, optional): The normalized confidence threshold that decides whether we
            keep or discard a predicted point. Discarded points get substituted with (0, 0) in the
            output data. Defaults to 0.1.
        downsampling_factor (int, optional): Decides how much we downsample the video before we
            pass it to the neural network. Ignored when ``model='mediapipe'``. Defaults to 2.
        use_cache (bool, optional): If True (default), reuse keypoints from a previous pose() run on
            this object (same model/threshold) to re-render a different `style`/`overlay`/`background`
            without re-running the network — e.g. run `style='markers'` then `style='skeleton'` fast.
            Defaults to True.
        save_data (bool, optional): Whether we save the predicted pose data to a file. Defaults to True.
        data_format (str, optional): Specifies format of pose-data. Accepted values are 'csv', 'tsv',
            'txt' and 'c3d' (motion-capture format; requires the optional ``c3d`` package). For multiple
            output formats, use a list, e.g. ['csv', 'c3d']. Defaults to 'csv'.
        save_video (bool, optional): Whether we save the video with the estimated pose overlaid on it.
            Defaults to True.
        style (str, optional): How to draw the pose. `'both'` draws markers (keypoints) connected by
            joint lines (the skeleton); `'markers'` draws only the keypoints; `'skeleton'` draws only
            the connecting joint lines. Defaults to 'both'.
        overlay (bool, optional): If True, draw the pose on top of the original video frames. If False,
            draw it on a plain background instead (a "markers only" video with no video underneath).
            Defaults to True.
        background (str, optional): Background colour used when `overlay=False`: `'black'` (default) or
            `'white'`. With `'white'` the skeleton and markers are drawn in black (an inverted, print-friendly
            look). With `'black'` they are drawn in bright colours. Ignored when `overlay=True`.
        marker_history (int, optional): If greater than 0, draw a motion trail for every marker by joining its
            positions over the last `marker_history` frames. Defaults to 0 (no trails). Works in all rendering
            paths (OpenPose, MediaPipe, and cached re-render).
        convert (bool, optional): Whether non-AVI input is first converted to an all-intra MJPEG `.avi`
            (cached as ``self.as_avi``) for frame-accurate decoding. Defaults to None ("auto"): the
            MediaPipe backend reads the source file directly (it decodes sequentially through an FFmpeg
            pipe and needs no intra-frame AVI), while the OpenPose backend converts. Pass True/False to
            force the behaviour.
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
        trajectory_labels (bool, optional): Whether to annotate the trajectories image with each
            marker's name. Defaults to False (cleaner image).
        trajectory_background (str, optional): Background of the trajectories PNG: ``'black'``,
            ``'white'``, or ``'transparent'`` (for overlaying on the video). Defaults to None
            ("auto"): transparent when the trajectories image is the only one exported, else black.
            Takes precedence over the legacy ``transparent_trajectories`` flag.
        target_name_data (str, optional): Target output name for the data. Defaults to None (which
            assumes that the input filename with the suffix "_pose" should be used).
        target_name_average (str, optional): Target output name for the average-pose image. Defaults
            to None (input filename with the suffix "_pose_average.png").
        target_name_trajectories (str, optional): Target output name for the trajectories image.
            Defaults to None (input filename with the suffix "_pose_trajectories.png").
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically
            increment target filenames to avoid overwriting. Defaults to True.

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

    # MediaPipe is an optional dependency (the `[pose]` extra). If it was selected (it is the
    # default backend) but isn't installed, fall back to the OpenPose BODY_25 model — it runs on
    # the always-present OpenCV DNN and auto-downloads its weights — so pose() works on a bare
    # `pip install musicalgestures`.
    #
    # That fallback assumed OpenCV could always load a Caffe model, which
    # stopped being true in OpenCV 5.0. Where it is not true there is nowhere
    # to fall back *to*, and announcing a fallback that then fails on the
    # backend it fell back to is worse than saying so plainly.
    if use_mediapipe and not _mediapipe_available():
        if not caffe_supported():
            raise MgDependencyError(
                f"pose() needs MediaPipe on this machine. The default backend "
                f"is not installed, and the OpenPose fallback cannot run "
                f"either: its models are Caffe, and OpenCV {cv2.__version__} "
                f"dropped the Caffe importer in 5.0. Install it with "
                f"`pip install musicalgestures[pose]`, or install OpenCV 4 "
                f"(`pip install 'opencv-python<5'`) to use the OpenPose "
                f"skeletons instead."
            )
        print("MediaPipe is not installed; falling back to the OpenPose 'body_25' backend. "
              "Install MediaPipe for the default backend with: pip install musicalgestures[pose]")
        use_mediapipe = False
        if model.lower() == 'mediapipe':
            model = 'body_25'

    # Resolve the "auto" convert default: MediaPipe reads the source directly through an
    # FFmpeg pipe and needs no all-intra AVI; OpenPose keeps the frame-accurate conversion.
    if convert is None:
        convert = not use_mediapipe

    # --- Reuse cached keypoints (skip re-inference) --------------------------
    # If a previous pose() run on this object used the same model/threshold, re-render
    # from the stored keypoints with the new style/overlay/background instead of running
    # the (expensive) network again.
    effective_model = 'mediapipe' if use_mediapipe else model.lower()
    cache = getattr(self, '_pose_keypoints', None)
    if use_cache and cache is not None \
            and cache.get('model') == effective_model \
            and cache.get('threshold') == threshold \
            and cache.get('downsampling_factor') == (None if use_mediapipe else downsampling_factor):
        return _rerender_pose_from_cache(
            self, style=style, overlay=overlay, background=background,
            save_data=save_data, data_format=data_format, save_video=save_video,
            save_average_pose=save_average_pose, save_trajectories=save_trajectories,
            transparent_trajectories=transparent_trajectories,
            trajectory_background=trajectory_background, trajectory_labels=trajectory_labels,
            marker_history=marker_history,
            target_name_video=target_name_video, target_name_data=target_name_data,
            target_name_average=target_name_average, target_name_trajectories=target_name_trajectories,
            overwrite=overwrite)

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
            marker_history=marker_history,
            save_average_pose=save_average_pose,
            save_trajectories=save_trajectories,
            transparent_trajectories=transparent_trajectories,
            trajectory_background=trajectory_background,
            trajectory_labels=trajectory_labels,
            target_name_video=target_name_video,
            target_name_data=target_name_data,
            target_name_average=target_name_average,
            target_name_trajectories=target_name_trajectories,
            overwrite=overwrite,
        )
    # -------------------------------------------------------------------------

    # The OpenPose backends are Caffe models, and OpenCV removed its Caffe
    # importer in 5.0 -- `readNetFromCaffe` is gone and `readNet` refuses the
    # format outright. Checked here, before the weights are looked for, so an
    # incompatible environment is not discovered after a 200 MB download and
    # a full decode; the failure used to surface as `AttributeError: module
    # 'cv2.dnn' has no attribute 'readNetFromCaffe'` from deep inside the run.
    #
    # Not silently switched to MediaPipe. Its 33 landmarks are a different
    # skeleton from BODY_25's, COCO's or MPI's, so a substituted backend would
    # return data that looks like what was asked for and is not.
    _require_caffe_support()

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
    # Write the result in the original container so we don't produce an .avi that then has
    # to be converted to .mp4; the AVI is only an intermediate for frame-accurate decoding.
    output_fex = fex

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
            target_name_video = of + '_pose' + output_fex
        else:
            target_name_video = os.path.splitext(target_name_video)[0] + output_fex
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
    from collections import deque
    _trail = deque(maxlen=int(marker_history)) if marker_history and marker_history > 0 else None

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

        # Always collect keypoints so the average-pose/trajectories images and the
        # keypoint cache (for fast re-rendering) are available; file-writing is gated below.
        time = frame2ms(ii, self.fps)
        points_list = [[list(point)[0]/self.width, list(point)[1]/self.height, ] if point is not None else [
            0, 0] for point in points]
        points_list_flat = itertools.chain.from_iterable(points_list)
        datapoint = [time]
        datapoint += points_list_flat
        data.append(datapoint)

        # Draw on the video frame, or on a plain canvas when overlay is disabled
        canvas, line_color, marker_color = _pose_canvas_and_colors(frame, overlay, background)

        # Marker history trails (last N frames)
        if _trail is not None:
            _trail.append([[p[0], p[1]] if p is not None else [np.nan, np.nan] for p in points])
            _draw_marker_trails(canvas, _trail, marker_color)

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
        text_format = _handle_c3d(of, data, OPENPOSE_NAMES.get(model.lower()), self.fps,
                                  self.width, self.height, data_format, target_name_data, overwrite)
        if text_format is not None:
            save_txt(of, self.width, self.height, model, data, text_format,
                     target_name_data=target_name_data, overwrite=overwrite)

    # Render the average-pose and trajectories images from the collected keypoints
    names = OPENPOSE_NAMES.get(model.lower())
    # Cache keypoints so a later pose() call can re-render a different style without re-inference
    self._pose_keypoints = {
        'model': model.lower(), 'threshold': threshold, 'downsampling_factor': downsampling_factor,
        'names': names, 'connections': POSE_PAIRS, 'data': data,
        'width': self.width, 'height': self.height, 'fps': self.fps,
        'filename': filename, 'of': of, 'fex': fex, 'output_fex': output_fex,
        'has_audio': self.has_audio,
    }
    avg_frame = np.rint(avg_acc / avg_n).astype(np.uint8) if (avg_acc is not None and avg_n > 0) else None
    average_image, trajectories_image = _render_pose_extras(
        data, names, POSE_PAIRS, self.width, self.height, self.fps,
        avg_frame, of, save_average_pose, save_trajectories,
        target_name_average, target_name_trajectories, overwrite,
        transparent_trajectories=transparent_trajectories,
        trajectory_background=trajectory_background,
        trajectory_labels=trajectory_labels, style=style, background=background)
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
                        transparent_trajectories=None, trajectory_background=None,
                        trajectory_labels=False, style='both', background='black'):
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
        # Resolve the trajectories background. Explicit trajectory_background wins; then the
        # legacy transparent_trajectories flag; then follow the pose `background` ('white' is
        # always honoured); otherwise auto: transparent when trajectories are the only image
        # exported (so they can overlay the video later), else the pose background.
        if trajectory_background is not None:
            bg = trajectory_background
        elif transparent_trajectories is True:
            bg = 'transparent'
        elif transparent_trajectories is False:
            bg = background
        elif str(background).lower() == 'white':
            bg = 'white'
        elif not save_average_pose:
            bg = 'transparent'
        else:
            bg = 'black'
        trajectories_image = render_trajectories(data, names, width, height, fps, tn, overwrite,
                                                 background=bg, labels=trajectory_labels)
    return average_image, trajectories_image


def _rerender_pose_from_cache(self, style='both', overlay=True, background='black',
                              save_data=True, data_format='csv', save_video=True,
                              save_average_pose=True, save_trajectories=True,
                              transparent_trajectories=None, trajectory_background=None,
                              trajectory_labels=False,
                              marker_history=0, target_name_video=None,
                              target_name_data=None, target_name_average=None,
                              target_name_trajectories=None, overwrite=True):
    """Re-render the pose outputs from cached keypoints (no network inference)."""
    c = self._pose_keypoints
    data, names, connections = c['data'], c['names'], c['connections']
    width, height, fps = c['width'], c['height'], c['fps']
    filename, of, fex = c['filename'], c['of'], c['fex']
    output_fex = c.get('output_fex', fex)
    n_points = len(names)

    style = str(style).lower()
    if style not in ('both', 'markers', 'skeleton'):
        style = 'both'
    background = str(background).lower()
    if background not in ('black', 'white'):
        background = 'black'

    print('Reusing cached pose keypoints (no re-inference).')

    if save_video:
        if target_name_video is None:
            target_name_video = of + '_pose' + output_fex
        else:
            target_name_video = os.path.splitext(target_name_video)[0] + output_fex
        if not overwrite:
            target_name_video = generate_outfilename(target_name_video)

    need_frames = overlay or save_average_pose
    process = None
    if need_frames:
        process = ffmpeg_cmd(['ffmpeg', '-y', '-i', filename],
                             total_time=self.length / self.fps if self.fps else 0, pipe='read')
    avg_acc = np.zeros((height, width, 3), dtype=np.float64) if save_average_pose else None
    avg_n = 0
    video_out = None
    frame_bytes = width * height * 3
    from collections import deque
    _trail = deque(maxlen=int(marker_history)) if marker_history and marker_history > 0 else None
    pb = MgProgressbar(total=len(data), prefix='Re-rendering pose (cached):')

    for ii, row in enumerate(data):
        src_frame = None
        if process is not None:
            buf = process.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            src_frame = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3).copy()
            if avg_acc is not None:
                avg_acc += src_frame
                avg_n += 1

        base = src_frame if (overlay and src_frame is not None) else np.zeros((height, width, 3), np.uint8)
        canvas, line_color, marker_color = _pose_canvas_and_colors(base, overlay, background)

        coords = row[1:1 + 2 * n_points]
        pts = [(coords[2 * j], coords[2 * j + 1]) for j in range(n_points)]
        if _trail is not None:
            _trail.append([[x * width, y * height] if (x or y) else [np.nan, np.nan] for x, y in pts])
            _draw_marker_trails(canvas, _trail, marker_color)
        if style in ('both', 'skeleton'):
            for a, b in connections:
                if a < n_points and b < n_points:
                    xa, ya = pts[a]
                    xb, yb = pts[b]
                    if (xa or ya) and (xb or yb):
                        cv2.line(canvas, (int(xa * width), int(ya * height)),
                                 (int(xb * width), int(yb * height)), line_color, 2, lineType=cv2.LINE_AA)
        if style in ('both', 'markers'):
            for x, y in pts:
                if x or y:
                    cv2.circle(canvas, (int(x * width), int(y * height)), 4, marker_color,
                               thickness=-1, lineType=cv2.FILLED)

        if save_video:
            if video_out is None:
                cmd = ['ffmpeg', '-y', '-s', '{}x{}'.format(width, height), '-r', str(fps),
                       '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', '-i', '-',
                       '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', target_name_video]
                video_out = ffmpeg_cmd(cmd, total_time=self.length / self.fps if self.fps else 0, pipe='write')
            video_out.stdin.write(canvas.astype(np.uint8).tobytes())
        pb.progress(ii + 1)
    pb.progress(len(data))

    if process is not None:
        process.terminate()
    if save_video and video_out is not None:
        video_out.stdin.close()
        video_out.wait()
        if c.get('has_audio'):
            source_audio = extract_wav(of + fex)
            embed_audio_in_video(source_audio, target_name_video)
            os.remove(source_audio)

    if save_data:
        headers = ['Time']
        for nm in names:
            headers.append(f'{nm} X')
            headers.append(f'{nm} Y')
        text_format = _handle_c3d(of, data, names, fps, width, height, data_format, target_name_data, overwrite)
        if text_format is not None:
            _save_pose_txt(of, data, headers, text_format, target_name_data, overwrite)

    avg_frame = np.rint(avg_acc / avg_n).astype(np.uint8) if (avg_acc is not None and avg_n > 0) else None
    average_image, trajectories_image = _render_pose_extras(
        data, names, connections, width, height, fps, avg_frame, of,
        save_average_pose, save_trajectories, target_name_average, target_name_trajectories,
        overwrite, transparent_trajectories=transparent_trajectories,
        trajectory_background=trajectory_background,
        trajectory_labels=trajectory_labels, style=style, background=background)
    self.pose_average = average_image
    self.pose_trajectories = trajectories_image

    if save_video:
        self.pose_video = musicalgestures.MgVideo(target_name_video, color=self.color, returned_by_process=True)
        self.pose_video.average_pose = average_image
        self.pose_video.trajectories = trajectories_image
        return self.pose_video
    return self


def _ensure_pose_keypoints(self, **pose_kwargs):
    """Make sure ``self._pose_keypoints`` exists; if not, run pose() (without writing the video
    or the summary images) to populate it. Extra kwargs are forwarded to pose()."""
    if getattr(self, '_pose_keypoints', None) is None:
        pose_kwargs.setdefault('save_video', False)
        pose_kwargs.setdefault('save_average_pose', False)
        pose_kwargs.setdefault('save_trajectories', False)
        self.pose(**pose_kwargs)
    return self._pose_keypoints


def mg_pose_waterfall(self, style: str = 'trajectories', n_samples: int = 40, markers: list | None = None, color_by: str | None = None,
                      cmap: str = 'hsv', dpi: int = 200, elev: float = 20, azim: float = -60, lw: float = 1.0, axes: bool = True, crop: bool = False,
                      target_name: str | None = None, overwrite: bool = True, **pose_kwargs) -> "MgFigure":
    """
    Render a 3D spatio-temporal waterfall of the pose, cascading along the time (depth) axis —
    a pose-based counterpart to ``silhouette_waterfall()``. Uses cached pose keypoints from a
    previous ``pose()`` call when available; otherwise it runs pose estimation first (extra
    keyword arguments such as ``model``/``device``/``downsampling_factor`` are forwarded to
    ``pose()``).

    Args:
        style (str, optional): What to draw. ``'trajectories'`` (default) draws each marker's
            continuous path through (x, time, y); ``'markers'`` scatters the markers at
            ``n_samples`` time slices; ``'skeleton'`` draws the skeleton joint lines at each
            time slice; ``'both'`` draws markers + skeleton.
        n_samples (int, optional): Number of time slices for the marker/skeleton styles.
            Defaults to 40 (ignored for ``'trajectories'``).
        markers (list, optional): Subset of marker names or indices to draw. Defaults to all.
        color_by (str, optional): ``'marker'`` or ``'time'``. Defaults to None ("auto"):
            'marker' for trajectories, 'time' for the slice styles.
        cmap (str, optional): Matplotlib colormap. Defaults to 'hsv'.
        dpi (int, optional): Output DPI. Defaults to 200.
        elev (float, optional): 3D elevation angle. Defaults to 20.
        azim (float, optional): 3D azimuth angle. Defaults to -60.
        lw (float, optional): Line width. Defaults to 1.0.
        axes (bool, optional): Draw the axes and tick labels. Set to False for a clean render
            with all axes and text removed. Defaults to True.
        crop (bool, optional): Tighten the spatial limits to the marker extent and trim the
            surrounding whitespace, so the figure shows mostly the data. Defaults to False.
        target_name (str, optional): Output name. Defaults to None ("_pose_waterfall.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.
        **pose_kwargs: Forwarded to ``pose()`` if keypoints have to be computed.

    Returns:
        MgFigure: the 3D waterfall figure, or None if there are too few frames.
    """
    from musicalgestures._pose_visualize import render_pose_waterfall

    _ensure_pose_keypoints(self, **pose_kwargs)

    c = self._pose_keypoints
    if target_name is None:
        target_name = c['of'] + '_pose_waterfall.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'

    mgf = render_pose_waterfall(
        c['data'], c['names'], c['width'], c['height'], c['fps'], target_name,
        overwrite=overwrite, style=style, connections=c.get('connections'),
        n_samples=n_samples, markers=markers, color_by=color_by, cmap=cmap,
        dpi=dpi, elev=elev, azim=azim, lw=lw, axes=axes, crop=crop)
    self.pose_waterfall_figure = mgf
    return mgf


def mg_pose_segments(self, segments: list | None = None, n_bins: int = 36, cmap: str = 'viridis', dpi: int = 200, ncols: int = 6,
                     target_name: str | None = None, overwrite: bool = True, **pose_kwargs) -> "MgFigure":
    """
    Circular (polar) motion plots and statistics for each body segment.

    A *segment* is the bone between two connected joints (e.g. shoulder–elbow). For every segment
    this computes its per-frame orientation angle and draws a polar rose histogram of the angle
    distribution with the mean-direction resultant vector, annotated with circular statistics
    (mean angle, resultant length R, and range of motion). A CSV of the per-segment statistics —
    mean angle, R, circular std, range of motion, and mean angular speed — is saved alongside the
    image. Uses cached pose keypoints from a previous ``pose()`` call when available; otherwise it
    runs pose estimation first (``model``/``device``/… are forwarded to ``pose()``).

    Args:
        segments (list, optional): Subset of connections as ``(a, b)`` joint-index tuples.
            Defaults to all skeleton connections.
        n_bins (int, optional): Number of angular bins per rose. Defaults to 36 (10° bins).
        cmap (str, optional): Matplotlib colormap for the bars. Defaults to 'viridis'.
        dpi (int, optional): Output DPI. Defaults to 200.
        ncols (int, optional): Columns in the subplot grid. Defaults to 6.
        target_name (str, optional): Output name. Defaults to None ("_pose_segments.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.
        **pose_kwargs: Forwarded to ``pose()`` if keypoints have to be computed.

    Returns:
        MgFigure: the grid of circular plots (per-segment stats in ``.data['stats']``), or None.
    """
    from musicalgestures._pose_visualize import render_segment_circular

    _ensure_pose_keypoints(self, **pose_kwargs)

    c = self._pose_keypoints
    if target_name is None:
        target_name = c['of'] + '_pose_segments.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'

    mgf = render_segment_circular(
        c['data'], c['names'], c.get('connections'), c['width'], c['height'], c['fps'],
        target_name, overwrite=overwrite, segments=segments, n_bins=n_bins, cmap=cmap,
        dpi=dpi, ncols=ncols)
    self.pose_segments_figure = mgf
    return mgf


def mg_pose_center(self, save_data: bool = True, dpi: int = 200, target_name: str | None = None, overwrite: bool = True, **pose_kwargs) -> "MgFigure":
    """
    Centre the pose data on its global centroid — a 2D port of the MoCap Toolbox ``mccenter``.

    A single offset per coordinate (the mean of the per-marker temporal means, missing detections
    ignored) is subtracted from every marker so the overall spatiotemporal centroid sits at the
    origin (0, 0). This removes the performer's absolute position in the frame, leaving relative
    posture/movement — useful before comparing or further analysing trajectories. Plots the centred
    marker trajectories and (by default) saves a CSV of the centred coordinates. Uses cached pose
    keypoints when available, otherwise runs ``pose()`` first (``**pose_kwargs`` are forwarded).

    Args:
        save_data (bool, optional): Save a CSV of the centred coordinates. Defaults to True.
        dpi (int, optional): Output DPI. Defaults to 200.
        target_name (str, optional): Output name. Defaults to None ("_pose_centered.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.
        **pose_kwargs: Forwarded to ``pose()`` if keypoints have to be computed.

    Returns:
        MgFigure: the centred-trajectories figure; ``.data['coords']`` holds the (T, n, 2) centred
        coordinates and ``.data['offset']`` the removed centroid. None if there are too few frames.
    """
    from musicalgestures._pose_visualize import render_pose_center

    _ensure_pose_keypoints(self, **pose_kwargs)

    c = self._pose_keypoints
    if target_name is None:
        target_name = c['of'] + '_pose_centered.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'

    mgf = render_pose_center(c['data'], c['names'], c['width'], c['height'], target_name,
                             overwrite=overwrite, dpi=dpi)
    if mgf is not None and save_data:
        try:
            import pandas as pd
            coords = mgf.data['coords']            # (T, n, 2)
            times = mgf.data['times']
            cols = {'Time': np.round(times * 1000.0, 3)}
            for i, name in enumerate(c['names']):
                cols[f'{name} X'] = coords[:, i, 0]
                cols[f'{name} Y'] = coords[:, i, 1]
            pd.DataFrame(cols).to_csv(os.path.splitext(target_name)[0] + '.csv', index=False)
        except Exception as e:
            print(f'Warning: could not save CSV: {e}')
    self.pose_centered_figure = mgf
    return mgf


def mg_pose_distance(self, dpi: int = 200, target_name: str | None = None, overwrite: bool = True, **pose_kwargs) -> "MgFigure":
    """
    Per-marker distance travelled and the average across markers — a 2D port of the MoCap Toolbox
    ``mccumdist``.

    Sums each marker's frame-to-frame Euclidean displacement (in pixels) and accumulates it over
    time. The figure shows the per-marker cumulative-distance curves and a ranked bar chart of the
    total distance per marker with the across-marker average marked; a CSV of the totals (plus the
    average) is saved. Uses cached pose keypoints when available, otherwise runs ``pose()`` first
    (``**pose_kwargs`` are forwarded).

    Args:
        dpi (int, optional): Output DPI. Defaults to 200.
        target_name (str, optional): Output name. Defaults to None ("_pose_distance.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.
        **pose_kwargs: Forwarded to ``pose()`` if keypoints have to be computed.

    Returns:
        MgFigure: ``.data['total']`` (per-marker totals), ``.data['average']`` (mean total), and
        ``.data['cumulative']`` (per-marker cumulative curves). None if there are too few frames.
    """
    from musicalgestures._pose_visualize import render_pose_distance

    _ensure_pose_keypoints(self, **pose_kwargs)

    c = self._pose_keypoints
    if target_name is None:
        target_name = c['of'] + '_pose_distance.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'

    mgf = render_pose_distance(c['data'], c['names'], c['width'], c['height'], c['fps'],
                               target_name, overwrite=overwrite, dpi=dpi)
    self.pose_distance_figure = mgf
    return mgf


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
        convert=None,
        quiet=True,
        marker_history=0,
        save_average_pose=True,
        save_trajectories=True,
        transparent_trajectories=None,
        trajectory_background=None,
        trajectory_labels=False,
        target_name_video=None,
        target_name_data=None,
        target_name_average=None,
        target_name_trajectories=None,
        overwrite=True):
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
    # Write the result in the original container (no avi→mp4 round-trip); any AVI is only an
    # intermediate for frame-accurate decoding.
    output_fex = fex

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
            target_name_video = of + '_pose' + output_fex
        else:
            target_name_video = os.path.splitext(target_name_video)[0] + output_fex
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
    from collections import deque
    _trail = deque(maxlen=int(marker_history)) if marker_history and marker_history > 0 else None

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
        # Always collected so the images and the keypoint cache are available.
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

        # Marker history trails (last N frames)
        if _trail is not None:
            _trail.append([[float(x) * self.width, float(y) * self.height] if v >= threshold
                           else [np.nan, np.nan] for x, y, v in keypoints])
            _draw_marker_trails(canvas, _trail, marker_color)

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
        c3d_names = [name.replace('_', ' ').title() for name in MEDIAPIPE_LANDMARK_NAMES]
        text_format = _handle_c3d(of, data, c3d_names, self.fps, self.width, self.height,
                                  data_format, target_name_data, overwrite)
        if text_format is not None:
            _save_pose_txt(of, data, headers, text_format, target_name_data, overwrite)

    # Render the average-pose and trajectories images from the collected keypoints
    names = [name.replace('_', ' ').title() for name in MEDIAPIPE_LANDMARK_NAMES]
    # Cache keypoints so a later pose() call can re-render a different style without re-inference
    self._pose_keypoints = {
        'model': 'mediapipe', 'threshold': threshold, 'downsampling_factor': None,
        'names': names, 'connections': MEDIAPIPE_POSE_CONNECTIONS, 'data': data,
        'width': self.width, 'height': self.height, 'fps': self.fps,
        'filename': filename, 'of': of, 'fex': fex, 'output_fex': output_fex,
        'has_audio': self.has_audio,
    }
    avg_frame = np.rint(avg_acc / avg_n).astype(np.uint8) if (avg_acc is not None and avg_n > 0) else None
    average_image, trajectories_image = _render_pose_extras(
        data, names, MEDIAPIPE_POSE_CONNECTIONS, self.width, self.height, self.fps,
        avg_frame, of, save_average_pose, save_trajectories,
        target_name_average, target_name_trajectories, overwrite,
        transparent_trajectories=transparent_trajectories,
        trajectory_background=trajectory_background,
        trajectory_labels=trajectory_labels, style=style, background=background)
    self.pose_average = average_image
    self.pose_trajectories = trajectories_image

    if save_video:
        self.pose_video = musicalgestures.MgVideo(target_name_video, color=self.color, returned_by_process=True)
        self.pose_video.average_pose = average_image
        self.pose_video.trajectories = trajectories_image
        return self.pose_video
    else:
        return self


def _save_pose_c3d(of, data, names, fps, width, height, target_name_data=None, overwrite=True):
    """
    Save pose keypoints to a C3D motion-capture file.

    Each landmark becomes a 3D point (x, y, z=0) in pixel coordinates; frames with a
    missing detection (0,0) are flagged invalid (residual = -1). Requires the optional
    ``c3d`` package (``pip install c3d``).
    """
    try:
        import c3d
    except ImportError as exc:
        from musicalgestures._utils import MgError
        raise MgError("Saving pose data as C3D requires the 'c3d' package. "
                      "Install it with: pip install c3d") from exc

    out_path = (of + '_pose.c3d') if target_name_data is None else (os.path.splitext(target_name_data)[0] + '.c3d')
    if not overwrite:
        out_path = generate_outfilename(out_path)

    n_points = len(names)
    writer = c3d.Writer(point_rate=float(fps))
    for row in data:
        coords = np.asarray(row[1:1 + 2 * n_points], dtype=np.float32)
        points = np.zeros((n_points, 5), dtype=np.float32)
        for j in range(n_points):
            x, y = coords[2 * j], coords[2 * j + 1]
            if x == 0 and y == 0:           # missing detection
                points[j] = [0, 0, 0, -1, 0]
            else:
                points[j] = [x * width, y * height, 0.0, 0.0, 0]
        writer.add_frames([(points, np.zeros((0, 1), dtype=np.float32))])

    writer.set_point_labels(names)
    with open(out_path, 'wb') as h:
        writer.write(h)
    return out_path


def _handle_c3d(of, data, names, fps, width, height, data_format, target_name_data, overwrite):
    """Save a .c3d file if 'c3d' is among the requested formats; return the remaining
    (text) formats to be handled by the text saver, or None if there are none."""
    formats = list(data_format) if isinstance(data_format, (list, tuple)) else [data_format]
    if any(str(f).lower() == 'c3d' for f in formats):
        _save_pose_c3d(of, data, names, fps, width, height, target_name_data, overwrite)
    text = [f for f in formats if str(f).lower() != 'c3d']
    if not text:
        return None
    return text if isinstance(data_format, (list, tuple)) else text[0]


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


def download_model(modeltype: str):
    """
    Download the OpenPose Caffe weights (.caffemodel) for the given model type into the package's
    ``pose/`` folder.

    Uses Python's ``urllib`` directly (cross-platform, no external ``wget`` / shell scripts /
    bundled binary). The ``.prototxt`` configs ship with the package; only the large weights file
    is fetched.

    Returns the downloaded file path on success, or ``None`` if download attempts fail.
    """
    import os
    import ssl
    import urllib.request
    import urllib.error
    import musicalgestures

    module_path = os.path.abspath(os.path.dirname(musicalgestures.__file__))
    base = ("https://www.uio.no/ritmo/english/research/labs/fourms/software/"
            "musicalgesturestoolbox/mgt-python/pose-models/")
    # model key -> (url, local folder, filename)
    models = {
        'mpi':     (base + 'mpi/pose_iter_160000.caffemodel',   'mpi',     'pose_iter_160000.caffemodel'),
        'coco':    (base + 'coco/pose_iter_440000.caffemodel',  'coco',    'pose_iter_440000.caffemodel'),
        'body_25': (base + 'body25/pose_iter_584000.caffemodel', 'body_25', 'pose_iter_584000.caffemodel'),
    }
    key = modeltype.lower()
    if key not in models:
        raise ValueError(f"Unknown pose model '{modeltype}'. Choose from {sorted(models)}.")

    url, folder, fname = models[key]
    target_folder = os.path.join(module_path, 'pose', folder)
    os.makedirs(target_folder, exist_ok=True)
    target_path = os.path.join(target_folder, fname)

    pb = MgProgressbar(total=100, prefix=f'Downloading {key.upper()} model:')

    def _hook(block_num, block_size, total_size):
        if total_size > 0:
            pb.progress(min(100.0, block_num * block_size * 100.0 / total_size))

    try:
        urllib.request.urlretrieve(url, target_path, _hook)
    except urllib.error.URLError as initial_download_error:
        # Fall back to a lenient TLS context (mirrors the previous scripts' --no-check-certificate).
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        urllib.request.install_opener(opener)
        try:
            urllib.request.urlretrieve(url, target_path, _hook)
        except urllib.error.URLError as retry_download_error:
            print(f"Could not download pose model from {url}.")
            print(f"  Initial download attempt failed with: {initial_download_error}")
            print(f"  Retry with lenient TLS failed with: {retry_download_error}")
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except OSError as cleanup_error:
                    print(f"Could not remove incomplete model file {target_path}: {cleanup_error}")
            return None
        finally:
            urllib.request.install_opener(urllib.request.build_opener())  # reset to default opener
    pb.progress(100)
    return target_path

from __future__ import annotations

import os
import warnings
import numpy as np
from typing import Union, List
from musicalgestures._input_test import mg_input_test
from musicalgestures._videoreader import mg_videoreader
from musicalgestures._flow import Flow
from musicalgestures._audio import MgAudio
import musicalgestures
from musicalgestures._utils import (
    convert,
    convert_to_mp4,
    get_framecount,
    ffmpeg_cmd,
    merge_videos,
    extract_frame,
    deprecated_alias,
    MgImage,
    MgFigure
)


class MgVideo(MgAudio):
    """
    This is the class for working with video files in the Musical Gestures Toolbox. It inherites from the class MgAudio for working with audio files as well.
    There is a set of preprocessing tools you can use when you load a video, such as:
    - trimming: to extract a section of the video,
    - skipping: to shrink the video by skipping N frames after keeping one,
    - rotating: to rotate the video by N degrees,
    - applying brightness and contrast
    - cropping: to crop the video either automatically (by assessing the area of motion) or manually with a pop-up user interface,
    - converting to grayscale

    These preprocesses will apply upon creating the MgVideo. Further processes are available as class methods.
    """

    def __init__(
        self,
        filename: Union[str, List[str]],
        array=None,
        fps: float | None = None,
        path: str | None = None,
        # Video parameters
        filtertype: str = "Regular",
        threshold: float = 0.05,
        starttime: float = 0,
        endtime: float = 0,
        blur: str = "None",
        skip: int = 0,
        frames: int = 0,
        rotate: float = 0,
        color: bool = True,
        contrast: float = 0,
        brightness: float = 0,
        crop: str = "None",
        keep_all: bool = False,
        returned_by_process: bool = False,
        # Audio parameters
        sr: int = 22050,
        n_fft: int = 2048,
        hop_length: int = 512,
    ):
        """
        Initializes Musical Gestures data structure from a video file, and applies preprocesses if desired.

        Args:
            filename (Union[str, List[str]]): Path to the video file. If input is a list, will merge all videos into one.
            array (np.ndarray, optional): Generates an MgVideo object from a video array. Defaults to None.
            fps (float, optional): The frequency at which consecutive images from the video array are captured or displayed. Defaults to None.
            path (str, optional): Path to save the output video file generated from a video array. Defaults to None.
            filtertype (str, optional): The `filtertype` parameter for the `motion()` method. `Regular` turns all values below `threshold` to 0. `Binary` turns all values below `threshold` to 0, above `threshold` to 1. `Blob` removes individual pixels with erosion method. Defaults to 'Regular'.
            threshold (float, optional): The `threshold` parameter for the `motion()` method. Eliminates pixel values less than given threshold. A number in the range of 0 to 1. Defaults to 0.05.
            starttime (int or float, optional): Trims the video from this start time (s). Defaults to 0.
            endtime (int or float, optional): Trims the video until this end time (s). Defaults to 0 (which means the full length).
            blur (str, optional): The `blur` parameter for the `motion()` method. 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise. Defaults to 'None'.
            skip (int, optional): Time-shrinks the video by skipping (discarding) every n frames determined by `skip`. Defaults to 0.
            frames (int, optional): Specify a fixed target number of frames to extract from the video. Defaults to 0.
            rotate (int, optional): Rotates the video by a `rotate` degrees. Defaults to 0.
            color (bool, optional): If False, converts the video to grayscale and sets every method in grayscale mode. Defaults to True.
            contrast (int, optional): Applies +/- 100 contrast to video. Defaults to 0.
            brightness (int, optional): Applies +/- 100 brightness to video. Defaults to 0.
            crop (str, optional): If 'manual', opens a window displaying the first frame of the input video file, where the user can draw a rectangle to which cropping is applied. If 'auto' the cropping function attempts to determine the area of significant motion and applies the cropping to that area. Defaults to 'None'.
            keep_all (bool, optional): If True, preserves an output video file after each used preprocessing stage. Defaults to False.
            returned_by_process (bool, optional): This parameter is only for internal use, do not use it. Defaults to False.

            sr (int, optional): Sampling rate of the audio file. Defaults to 22050.
            n_fft (int, optional): Length of the FFT window. Defaults to 2048.
            hop_length (int, optional): Number of samples between successive frames. Defaults to 512.
        """

        # if filename is a list, merge all videos into one
        if isinstance(filename, list):
            self.filename = merge_videos(filename)
        else:
            self.filename = filename

        self.array = array
        # The ARGUMENT is optional: it is the rate an array is encoded at, and a file
        # carries its own. The ATTRIBUTE is not, because `get_video()` below reads the
        # true rate from the file and overwrites this, so by the end of `__init__` it is
        # always a number. 0.0 stands for "not given yet" over the few lines before that
        # happens, and the from-array branch below tests it for truth rather than for
        # None, which rejects an explicit `fps=0` --- not a frame rate anything can use.
        self.fps: float = fps if fps is not None else 0.0
        self.path = path
        # Name of file without extension (only-filename)
        self.of = os.path.splitext(self.filename)[0]
        self.fex = os.path.splitext(self.filename)[1]
        # Video parameters
        self.color = color
        self.starttime = starttime
        self.endtime = endtime
        self.skip = skip
        self.frames = frames
        self.filtertype = filtertype
        self.threshold = threshold
        self.blur = blur
        self.contrast = contrast
        self.brightness = brightness
        self.crop = crop
        self.rotate = rotate
        self.keep_all = keep_all
        self.has_audio = None
        self.returned_by_process = returned_by_process
        # Audio parameters
        self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length

        # Check input and if FFmpeg is properly installed
        self.test_input()

        if self.array is not None and not self.fps:
            # Without a rate there is nothing to encode the array at, so the write below
            # never happens and the read after it fails with "no such file" --- blaming
            # the output for a missing argument. Both before and after this attribute
            # stopped being Optional, so say what is actually wrong.
            raise ValueError(
                "fps= is required when MgVideo is given an array: an array carries no frame "
                "rate of its own, so there is nothing to encode it at.")

        if self.array is not None and self.fps:
            self.from_numpy(self.array, self.fps)
        elif fps is not None:
            # `fps` is the rate an ARRAY is encoded at. For a file input `get_video()` below reads
            # the rate from the file and overwrites this unconditionally, so the argument does
            # nothing --- and code written on the belief that it had set the rate would be wrong
            # with nothing in any output to show it. Say so rather than let it pass in silence.
            warnings.warn(
                "fps= is ignored when MgVideo is given a file: the rate is read from the file "
                "itself, so this argument has no effect. Use resample(fps=...) to change a "
                "file's rate, which returns a new MgVideo that has re-read it.",
                UserWarning, stacklevel=2)

        self.get_video()
        self.flow = Flow(self, self.filename, self.color, self.has_audio)

    # Results stashed by the analysis methods.
    #
    # These are declarations, not assignments: a bare annotation tells a type
    # checker the attribute exists and what it holds, while leaving it absent
    # from the instance until a method sets it. `show(key=...)` decides what a
    # video has by looking in `self.__dict__`, so giving any of these a value
    # here would make every video claim every result. See issue #346.
    _avg_frame_cache: tuple[str, np.ndarray]
    _pose_keypoints: dict
    as_avi: "musicalgestures.MgVideo"
    as_mp4: "musicalgestures.MgVideo"
    average_pose: MgImage
    blend_image: MgImage
    blur_faces_video: "musicalgestures.MgVideo"
    body_audio_coupling_figure: MgFigure
    dynamics_coupling_figure: MgFigure
    eulerian_video: "musicalgestures.MgVideo"
    flow_dense_video: "musicalgestures.MgVideo"
    flow_sparse_video: "musicalgestures.MgVideo"
    frameaverage_cv2_image: MgImage
    frameaverage_image: MgImage
    heatmap_image: MgImage
    history_video: "musicalgestures.MgVideo"
    mhi_image: MgImage
    motion_video: "musicalgestures.MgVideo"
    motiondescriptors_figure: MgFigure
    actions: list
    postures: list
    motion_plot_image: MgImage
    motiongram_y_image: MgImage
    motiongram_x_image: MgImage
    motionvectors_video: "musicalgestures.MgVideo"
    motionvectorhistory_image: MgImage
    motionvectorgrams_images: "musicalgestures.MgList"
    motionvectorwaterfall_figure: MgFigure
    motionvectoroverview_figure: MgFigure
    motionscape_figure: MgFigure
    posegram_figure: MgFigure
    posegram_spatial_figure: MgFigure
    posegrams_images: "musicalgestures.MgList"
    movement_beat_statistics_figure: MgFigure
    phase_synchrony_figure: MgFigure
    pose_average_image: MgImage
    pose_centered_figure: MgFigure
    pose_distance_figure: MgFigure
    pose_segments_figure: MgFigure
    pose_trajectories_image: MgImage
    pose_video: "musicalgestures.MgVideo"
    pose_waterfall_figure: MgFigure
    silhouette_waterfall_figure: MgFigure
    sonomotiongram_audio: MgAudio
    spacetime_volume_figure: MgFigure
    ssm_combined_image: MgImage
    stroboscope_image: MgImage
    multishot_image: MgImage
    pose_timeline_figure: MgFigure
    plate_image: MgImage
    structure_comparison_figure: MgFigure
    subtract_video: "musicalgestures.MgVideo"
    tempo_similarity_figure: MgFigure
    trajectories: MgImage
    videogram_y_image: MgImage
    videogram_x_image: MgImage
    warp_video: "musicalgestures.MgVideo"

    def motion_mp(self, *args, **kwargs):
        """Retired. Use :meth:`motion` instead.

        This rendered a motion video across several processes, coordinating them
        with a socket server and an argparse child process. It raised on its first
        call --- two fields were read as one between the parent and the workers,
        and behind that failure it called `save_txt` and `save_analysis` with
        arguments in the wrong positions --- so it produced nothing for anyone who
        tried it. See issue #370.

        `motion()` does the same work in one process and is tested.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "motion_mp() has been retired: it raised on its first call and produced "
            "nothing (see issue #370). Use motion(), which does the same work in one "
            "process.")

    # Retired names, kept working for one release. See issue #346.
    motion_plot = deprecated_alias("motion_plot", "motion_plot_image")
    motiongram_x = deprecated_alias("motiongram_x", "motiongram_x_image")
    motiongram_y = deprecated_alias("motiongram_y", "motiongram_y_image")
    #: The picture-named attributes, retired in favour of the axis each gram keeps:
    #: x is the tall picture, y the wide one.
    motiongram_vertical_image = deprecated_alias(
        "motiongram_vertical_image", "motiongram_x_image")
    motiongram_horizontal_image = deprecated_alias(
        "motiongram_horizontal_image", "motiongram_y_image")
    movement_beat_statistics = deprecated_alias(
        "movement_beat_statistics", "movement_beat_statistics_figure")
    pose_average = deprecated_alias("pose_average", "pose_average_image")
    pose_trajectories = deprecated_alias("pose_trajectories", "pose_trajectories_image")
    ssm_combined = deprecated_alias("ssm_combined", "ssm_combined_image")
    videogram_x = deprecated_alias("videogram_x", "videogram_x_image")
    videogram_y = deprecated_alias("videogram_y", "videogram_y_image")
    videogram_vertical_image = deprecated_alias(
        "videogram_vertical_image", "videogram_x_image")
    videogram_horizontal_image = deprecated_alias(
        "videogram_horizontal_image", "videogram_y_image")

    # Methods are bound by importing the implementing function at class scope. mypy calls this
    # "Unsupported class scoped import" and it is the toolbox's central idiom, so the ignores
    # below are permanent rather than a backlog item. Issue #350.
    from musicalgestures._motionvideo import mg_motion as motion  # type: ignore[misc]
    from musicalgestures._motionvideo import mg_motiongrams as motiongrams  # type: ignore[misc]
    from musicalgestures._motionvideo import mg_motiondata as motiondata  # type: ignore[misc]
    from musicalgestures._motionvideo import mg_motionplots as motionplots  # type: ignore[misc]
    from musicalgestures._motionvideo import mg_motionvideo as motionvideo  # type: ignore[misc]
    from musicalgestures._motionvideo import mg_motionscore as motionscore  # type: ignore[misc]
    from musicalgestures._subtract import mg_subtract as subtract  # type: ignore[misc]
    from musicalgestures._ssm import mg_ssm as ssm  # type: ignore[misc]
    from musicalgestures._videograms import videograms_ffmpeg as videograms  # type: ignore[misc]
    from musicalgestures._directograms import mg_directograms as directograms  # type: ignore[misc]
    from musicalgestures._warp import (  # type: ignore[misc]
        mg_warp_audiovisual_beats as warp_audiovisual_beats,
    )
    from musicalgestures._blurfaces import mg_blurfaces as blur_faces  # type: ignore[misc]
    from musicalgestures._impacts import mg_impacts as impacts  # type: ignore[misc]
    from musicalgestures._grid import mg_grid as grid  # type: ignore[misc]
    from musicalgestures._actions import mg_actions as actions_from_motion  # type: ignore[misc]
    from musicalgestures._postures import mg_postures as postures_from_pose  # type: ignore[misc]
    from musicalgestures._videoadjust import mg_resample as resample  # type: ignore[misc]
    from musicalgestures._motionvideo import save_analysis  # type: ignore[misc]

    # from musicalgestures._cropvideo import mg_cropvideo, find_motion_box, find_total_motion_box
    from musicalgestures._show import mg_show as show  # type: ignore[misc]
    from musicalgestures._info import mg_info as info  # type: ignore[misc]
    from musicalgestures._history import history_ffmpeg as history  # type: ignore[misc]
    from musicalgestures._history import history_cv2  # type: ignore[misc]
    from musicalgestures._blend import mg_blend_image as blend  # type: ignore[misc]
    from musicalgestures._frameaverage import (  # type: ignore[misc]
        mg_pixelarray as pixelarray,
        mg_pixelarray_cv2 as pixelarray_cv2,
        mg_pixelarray_stats as pixelarray_stats
    )
    from musicalgestures._heatmap import mg_heatmap as heatmap  # type: ignore[misc]
    from musicalgestures._motiontempo import mg_motiontempo as motiontempo  # type: ignore[misc]
    from musicalgestures._motionvectors import (  # type: ignore[misc]
        mg_motionvectors as motionvectors,
        mg_motionvectordata as motionvectordata,
        mg_motionvectorhistory as motionvectorhistory,
        mg_motionvectorgrams as motionvectorgrams,
        mg_motionvectorwaterfall as motionvectorwaterfall,
        mg_motionvectoroverview as motionvectoroverview,
        mg_motionscape as motionscape,
    )
    from musicalgestures._posetimeline import (  # type: ignore[misc]
        mg_pose_timeline as pose_timeline,
    )
    from musicalgestures._multishot import (  # type: ignore[misc]
        mg_multishot as multishot,
        mg_plate as plate,
    )
    from musicalgestures._zoomview import mg_zoompage as zoompage  # type: ignore[misc]
    from musicalgestures._eulerian import mg_eulerian as eulerian  # type: ignore[misc]
    from musicalgestures._sonification import mg_sonomotiongram as sonomotiongram  # type: ignore[misc]
    from musicalgestures._spacetime import (  # type: ignore[misc]
        mg_stroboscope as stroboscope,
        mg_silhouette_waterfall as silhouette_waterfall,
        mg_motionhistory as motionhistory,
        mg_spacetime_volume as spacetime_volume,
    )
    # Overrides the inherited audio beat_statistics with a source-aware version
    # (source='audio' delegates to the audio analysis; source='motion' uses movement onsets).
    from musicalgestures._movementbeats import mg_beat_statistics as beat_statistics  # type: ignore[misc]
    from musicalgestures._movementbeats import mg_tempo_similarity as tempo_similarity  # type: ignore[misc]
    from musicalgestures._motiondescriptors import mg_motiondescriptors as motiondescriptors  # type: ignore[misc]
    from musicalgestures._audio_video import (  # type: ignore[misc]
        mg_phase_synchrony as phase_synchrony,
        mg_structure_comparison as structure_comparison,
        mg_body_audio_coupling as body_audio_coupling,
        mg_dynamics_coupling as dynamics_coupling,
    )
    from musicalgestures._pose import pose  # type: ignore[misc]
    from musicalgestures._pose import mg_pose_waterfall as pose_waterfall  # type: ignore[misc]
    from musicalgestures._pose import mg_pose_segments as pose_segments  # type: ignore[misc]
    from musicalgestures._pose import mg_pose_center as pose_center  # type: ignore[misc]
    from musicalgestures._pose import mg_pose_distance as pose_distance  # type: ignore[misc]
    from musicalgestures._posegram import (  # type: ignore[misc]
        mg_posegram as posegram,
        mg_posegram_spatial as posegram_spatial,
        mg_posegrams as posegrams,
    )

    def __repr__(self) -> str:
        w, h = getattr(self, 'width', None), getattr(self, 'height', None)
        size = f"{w}x{h}" if w and h else "?x?"
        fps = getattr(self, 'fps', None)
        fps_str = f"{fps:g}fps" if fps else "?fps"
        frames = getattr(self, 'length', None)
        frames_str = f"{int(frames)} frames" if frames else "? frames"
        return (f"MgVideo('{self.filename}', {frames_str}, {fps_str}, {size}, "
                f"audio={getattr(self, 'has_audio', None)})")

    @property
    def n_frames(self) -> int:
        """Number of frames in the video (an alias for the frame-count ``length``)."""
        return int(self.length)

    @property
    def duration(self) -> float:
        """Video duration in **seconds** (``length / fps``).

        Note ``self.length`` is the frame *count* for an MgVideo (it is the duration in
        seconds for an MgAudio); use this property when you want seconds.
        """
        return self.length / self.fps if self.fps else 0.0

    def average(self, **kwargs):
        """
        Backward compatibility alias for blend(component_mode='average').
        Creates an average image of all frames in the video.
        
        Args:
            **kwargs: Additional arguments passed to blend method.
                     Note: 'normalize' parameter is accepted for backward compatibility but ignored.
        
        Returns:
            MgImage: A new MgImage pointing to the output average image file.
        """
        # Strip parameters that were documented in older API versions but aren't
        # supported by the underlying blend implementation.
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ('normalize', 'method')}
        return self.blend(component_mode='average', **filtered_kwargs)

    def test_input(self):
        """Gives feedback to user if initialization from input went wrong."""
        mg_input_test(
            self.filename,
            self.array,
            self.fps,
            self.filtertype,
            self.threshold,
            self.starttime,
            self.endtime,
            self.blur,
            self.skip,
            self.frames,
        )

    def get_video(self):
        """Creates a video attribute to the Musical Gestures object with the given correct settings.

        NB: For an ``MgVideo``, ``self.length`` is the number of **frames** (from
        ``get_framecount``), whereas for ``MgAudio`` ``self.length`` is the duration in
        **seconds**. To get the video duration in seconds use ``self.length / self.fps``.
        """
        # Bake any display-rotation flag into the pixels so every reader (FFmpeg pipe,
        # OpenCV, filters) agrees on orientation and no process comes out rotated.
        from musicalgestures._utils import normalize_rotation
        oriented = normalize_rotation(self.filename)
        if oriented != self.filename:
            self.filename = oriented
            self.of, self.fex = os.path.splitext(self.filename)

        (
            self.length,
            self.width,
            self.height,
            self.fps,
            self.endtime,
            self.of,
            self.fex,
            self.has_audio,
        ) = mg_videoreader(
            filename=self.filename,
            starttime=self.starttime,
            endtime=self.endtime,
            skip=self.skip,
            frames=self.frames,
            rotate=self.rotate,
            contrast=self.contrast,
            brightness=self.brightness,
            crop=self.crop,
            color=self.color,
            returned_by_process=self.returned_by_process,
            keep_all=self.keep_all,
        )

        # Convert eventual low-resolution video or image
        video_formats = [
            ".avi",
            ".mp4",
            ".mov",
            ".mkv",
            ".mpg",
            ".mpeg",
            ".webm",
            ".ogg",
            ".ts",
            ".wmv",
            ".3gp",
            ".360",
        ]
        if self.fex not in video_formats:
            # Check if it is an image file
            if get_framecount(self.filename) == 1:
                image_formats = [
                    ".gif",
                    ".jpeg",
                    ".jpg",
                    ".jfif",
                    ".pjpeg",
                    ".png",
                    ".svg",
                    ".webp",
                    ".avif",
                    ".apng",
                ]
                if self.fex not in image_formats:
                    # Create one converted version and register it to the MgVideo
                    filename = convert(
                        self.of + self.fex, self.of + self.fex + ".png", overwrite=True
                    )
                    # point of and fex to the png version
                    self.of, self.fex = os.path.splitext(filename)
                else:
                    # update filename after the processes
                    self.filename = self.of + self.fex
            else:
                # Create one converted version and register it to the MgVideo
                filename = convert_to_mp4(self.of + self.fex, overwrite=True)
                # point of and fex to the mp4 version
                self.of, self.fex = os.path.splitext(filename)
        else:
            # Update filename after the processes
            self.filename = self.of + self.fex

        # Check if there is audio in the video file
        if self.has_audio:
            self.audio = MgAudio(self.filename, self.sr, self.n_fft, self.hop_length)
        else:
            self.audio = None

    def numpy(self):
        """
        Read all video frames into a numpy array using FFmpeg.

        Returns:
            tuple: A tuple ``(array, fps)`` where ``array`` is a ``numpy.ndarray``
                of shape ``(N, H, W, 3)`` in BGR format (uint8) containing all N
                frames, and ``fps`` is the frame rate of the video.
        """
        # Define ffmpeg command and load all the video frames in memory
        cmd = ["ffmpeg", "-y", "-i", self.filename]
        process = ffmpeg_cmd(cmd, total_time=self.length, pipe="load")
        # Convert bytes to numpy array
        array = np.frombuffer(process.stdout, dtype=np.uint8).reshape(
            -1, self.height, self.width, 3
        )

        return array, self.fps

    def from_numpy(self, array: np.ndarray, fps: float, target_name: str | None = None) -> None:
        """
        Writes a numpy array of video frames to a video file using FFmpeg.

        After writing, updates ``self.filename``, ``self.of``, and ``self.fex`` to
        reflect the actual output path so that subsequent operations on this object
        refer to the newly created file.

        Args:
            array (np.ndarray): Video frames array with shape (N, H, W, 3) in BGR format.
            fps (float): Frames per second for the output video.
            target_name (str, optional): Full path for the output file. If None, uses
                ``self.path/self.filename`` (or just ``self.filename`` if path is None).
                Defaults to None.
        """
        if target_name is not None:
            write_path = os.path.splitext(target_name)[0] + self.fex
        elif self.path is not None:
            write_path = os.path.join(self.path, self.filename)
        else:
            write_path = self.filename

        process = None
        for frame in array:
            if process is None:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-s",
                    "{}x{}".format(frame.shape[1], frame.shape[0]),
                    "-r",
                    str(fps),
                    "-f",
                    "rawvideo",
                    "-pix_fmt",
                    "bgr24",
                    "-vcodec",
                    "rawvideo",
                    "-i",
                    "-",
                    "-vcodec",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    write_path,
                ]
                process = ffmpeg_cmd(cmd, total_time=array.shape[0], pipe="write")
            process.stdin.write(frame.astype(np.uint8))
        # the loop opens the process on its first frame, so this only holds for a non-empty array
        assert process is not None, "no frames were written: the array is empty"
        process.stdin.close()
        process.wait()

        # Update self.filename to the actual written path so that get_video() can find the file
        self.filename = write_path
        self.of, self.fex = os.path.splitext(write_path)

    def extract_frame(self, **kwargs):
        """
        Extracts a frame from the video at a given time.
        see _utils.extract_frame for details.

        Keyword Args:
            frame (int): The frame number to extract.
            time (str): The time in HH:MM:ss.ms where to extract the frame from.
            target_name (str, optional): The name for the output file. If None, the name will be <input name>FRAME<frame number>.<file extension>. Defaults to None.
            overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

        Returns:
            MgImage: An MgImage object referring to the extracted frame.
        """
        return MgImage(extract_frame(self.filename, **kwargs))

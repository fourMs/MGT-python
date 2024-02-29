import os
import numpy as np
from enum import Enum
from musicalgestures._input_test import mg_input_test
from musicalgestures._videoreader import mg_videoreader
from musicalgestures._flow import Flow
from musicalgestures._audio import MgAudio 
from musicalgestures._utils import  MgFigure, MgImage, convert, convert_to_mp4, get_framecount, ffmpeg_cmd, get_length, generate_outfilename
from musicalgestures._mglist import MgList

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
            filename,
            array=None,
            fps=None,
            path=None,
            # Video parameters
            filtertype='Regular',
            thresh=0.05,
            starttime=0,
            endtime=0,
            blur='None',
            skip=0,
            frames=0,
            rotate=0,
            color=True,
            contrast=0,
            brightness=0,
            crop='None',
            keep_all=False,
            returned_by_process=False,
            # Audio parameters
            sr=22050,
            n_fft=2048, 
            hop_length=512,
            ):
        """
        Initializes Musical Gestures data structure from a video file, and applies preprocesses if desired.

        Args:
            filename (str): Path to the video file.
            array (np.ndarray, optional): Generates an MgVideo object from a video array. Defauts to None.
            fps (float, optional): The frequency at which consecutive images from the video array are captured or displayed. Defauts to None.
            path (str, optional): Path to save the output video file generated from a video array. Defaults to None.
            filtertype (str, optional): The `filtertype` parameter for the `motion()` method. `Regular` turns all values below `thresh` to 0. `Binary` turns all values below `thresh` to 0, above `thresh` to 1. `Blob` removes individual pixels with erosion method. Defaults to 'Regular'.
            thresh (float, optional): The `thresh` parameter for the `motion()` method. Eliminates pixel values less than given threshold. A number in the range of 0 to 1. Defaults to 0.05.
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

        self.filename = filename
        self.array = array
        self.fps = fps
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
        self.thresh = thresh
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

        if all(arg is not None for arg in [self.array, self.fps]):
            self.from_numpy(self.array, self.fps)
        
        self.get_video()
        self.flow = Flow(self, self.filename, self.color, self.has_audio)

    from musicalgestures._motionvideo import mg_motion as motion
    from musicalgestures._motionvideo import mg_motiongrams as motiongrams
    from musicalgestures._motionvideo import mg_motiondata as motiondata
    from musicalgestures._motionvideo import mg_motionplots as motionplots
    from musicalgestures._motionvideo import mg_motionvideo as motionvideo
    from musicalgestures._motionvideo import mg_motionscore as motionscore
    from musicalgestures._motionvideo_mp_run import mg_motion_mp as motion_mp
    from musicalgestures._subtract import mg_subtract as subtract
    from musicalgestures._ssm import mg_ssm as ssm
    from musicalgestures._videograms import videograms_ffmpeg as videograms
    from musicalgestures._directograms import mg_directograms as directograms
    from musicalgestures._warp import mg_warp_audiovisual_beats as warp_audiovisual_beats
    from musicalgestures._blurfaces import mg_blurfaces as blur_faces
    from musicalgestures._impacts import mg_impacts as impacts
    from musicalgestures._grid import mg_grid as grid
    from musicalgestures._motionvideo import save_analysis
    # from musicalgestures._cropvideo import mg_cropvideo, find_motion_box, find_total_motion_box
    from musicalgestures._show import mg_show as show
    from musicalgestures._info import mg_info as info
    from musicalgestures._history import history_ffmpeg as history
    from musicalgestures._history import history_cv2
    from musicalgestures._blend import mg_blend_image as blend
    from musicalgestures._pose import pose

    def test_input(self):
        """Gives feedback to user if initialization from input went wrong."""
        mg_input_test(self.filename, self.array, self.fps, self.filtertype, self.thresh, self.starttime, self.endtime, self.blur, self.skip, self.frames)

    def get_video(self):
        """Creates a video attribute to the Musical Gestures object with the given correct settings."""
        self.length, self.width, self.height, self.fps, self.endtime, self.of, self.fex, self.has_audio = mg_videoreader(
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
        keep_all=self.keep_all)

        # Convert eventual low-resolution video or image
        video_formats = ['.avi', '.mp4', '.mov', '.mkv', '.mpg', '.mpeg', '.webm', '.ogg', '.ts', '.wmv', '.3gp']
        if self.fex not in video_formats:
            # Check if it is an image file
            if get_framecount(self.filename) == 1: 
                image_formats = ['.gif', '.jpeg', '.jpg', '.jfif', '.pjpeg', '.png', '.svg', '.webp', '.avif', '.apng']
                if self.fex not in image_formats:
                    # Create one converted version and register it to the MgVideo 
                    filename = convert(self.of + self.fex, self.of + self.fex + '.png', overwrite=True)
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

    def __repr__(self):
        return f"MgVideo('{self.filename}')"

    def numpy(self):
        "Pipe all video frames from FFmpeg to numpy array"

        # Define ffmpeg command and load all the video frames in memory
        cmd = ['ffmpeg', '-y', '-i', self.filename]
        process = ffmpeg_cmd(cmd, total_time=self.length, pipe='load')
        # Convert bytes to numpy array
        array = np.frombuffer(process.stdout, dtype=np.uint8).reshape(-1, self.height, self.width, 3)

        return array, self.fps
    
    def from_numpy(self, array, fps, target_name=None):
        if target_name is not None:
            self.filename = os.path.splitext(target_name)[0] + self.fex

        if self.path is not None:
            target_name = os.path.join(self.path, self.filename)
        else:
            target_name = self.filename

        process = None
        for frame in array:
            if process is None:
                cmd =['ffmpeg', '-y', '-s', '{}x{}'.format(frame.shape[1], frame.shape[0]), 
                      '-r', str(fps), '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', 
                      '-i', '-', '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', target_name]
                process = ffmpeg_cmd(cmd, total_time=array.shape[0], pipe='write')
            process.stdin.write(frame.astype(np.uint8))
        process.stdin.close()
        process.wait()

        return


class Examples:
    def __init__(self):
        module_path = os.path.realpath(
            os.path.dirname(__file__)).replace("\\", "/")
        # module_path = os.path.abspath(os.path.dirname(__file__))
        self.dance = module_path + "/examples/dancer.avi"
        self.pianist = module_path + "/examples/pianist.avi"
        self.notebook = module_path + "/MusicalGesturesToolbox.ipynb"

examples = Examples()


class Projection(Enum):
    """
    same as https://ffmpeg.org/ffmpeg-filters.html#v360.
    """

    e = 0
    equirect = 1
    c3x2 = 2
    c6x1 = 3
    c1x6 = 4
    eac = 5  # Equi-Angular Cubemap.
    flat = 6
    gnomonic = 7
    rectilinear = 8  # Regular video.
    dfisheye = 9  # Dual fisheye.
    barrel = 10
    fb = 11
    barrelsplit = 12  # Facebook’s 360 formats.
    sg = 13  # Stereographic format.
    mercator = 14  # Mercator format.
    ball = 15  # Ball format, gives significant distortion toward the back.
    hammer = 16  # Hammer-Aitoff map projection format.
    sinusoidal = 17  # Sinusoidal map projection format.
    fisheye = 18  # Fisheye projection.
    pannini = 19  # Pannini projection.
    cylindrical = 20  # Cylindrical projection.
    perspective = 21  # Perspective projection. (output only)
    tetrahedron = 22  # Tetrahedron projection.
    tsp = 23  # Truncated square pyramid projection.
    he = 24
    hequirect = 25  # Half equirectangular projection.
    equisolid = 26  # Equisolid format.
    og = 27  # Orthographic format.
    octahedron = 28  # Octahedron projection.
    cylindricalea = 29

    def __str__(self):
        return self.name


# TODO: add settings for cameras and files
CAMERA = {
    "gopro max": {},
    "insta360 x3": {},
    "garmin virb 360": {},
    "ricoh theta xs00": {},
}


class Mg360Video(MgVideo):
    """
    Class for 360 videos.
    """

    def __init__(
        self,
        filename: str,
        projection: str,
        camera: str = None,
        **kwargs,
    ):
        """
        Args:
            filename (str): Path to the video file.
            projection (str): Projection type.
            camera (str): Camera type.
        """
        super().__init__(filename, **kwargs)
        self.filename = os.path.abspath(self.filename)

        try:
            self.projection = Projection[projection.lower()]
        except KeyError:
            raise ValueError(
                f"Projection type '{projection}' not recognized. See `Projection` for available options."
            )

        if camera is None:
            self.camera = None
        elif camera.lower() in CAMERA:
            self.camera = CAMERA[camera.lower()]
        else:
            raise Warning(f"Camera type '{camera}' not recognized.")

    def convert_projection(self, target_projection: Projection|str, options: dict[str, str] = None):
        """
        Convert the video to a different projection.
        Args:
            target_projection (Projection): Target projection.
            options (dict[str, str], optional): Options for the conversion. Defaults to None.
        """
        if target_projection == self.projection:
            return
        else:
            output_name = generate_outfilename(f"{self.filename.split('.')[0]}_{target_projection}.mp4")
            # convert str to Projection
            if isinstance(target_projection, str):
                try:
                    target_projection = Projection[target_projection.lower()]
                except KeyError:
                    raise ValueError(
                        f"Projection type '{target_projection}' not recognized. See `Projection` for available options."
                    )
            # parse options
            if options:
                options = "".join([f"{k}={v}:" for k, v in options])
                cmds = [
                    "ffmpeg",
                    "-i",
                    self.filename,
                    "-vf",
                    f"v360={self.projection}:{target_projection}:{options}",
                    output_name,
                ]
            else:
                cmds = [
                    "ffmpeg",
                    "-i",
                    self.filename,
                    "-vf",
                    f"v360={self.projection}:{target_projection}",
                    output_name,
                ]

            # execute conversion
            ffmpeg_cmd(
                cmds,
                get_length(self.filename),
                pb_prefix=f"Converting projection to {target_projection}:",
            )
            self.filename = output_name

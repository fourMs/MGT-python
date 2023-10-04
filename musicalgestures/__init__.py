import os
from musicalgestures._input_test import mg_input_test
from musicalgestures._videoreader import mg_videoreader
from musicalgestures._flow import Flow
from musicalgestures._audio import MgAudio 
from musicalgestures._utils import get_metadata, convert, convert_to_mp4, get_framecount


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
        
        self.test_input()
        self.get_video()
        self.info()
        self.flow = Flow(self, self.filename, self.color, self.has_audio)

    from musicalgestures._motionvideo import mg_motion as motion
    from musicalgestures._motionvideo_mp_run import mg_motion_mp as motion_mp
    from musicalgestures._motionvideo import mg_motiongrams as motiongrams
    from musicalgestures._motionvideo import mg_motiondata as motiondata
    from musicalgestures._motionvideo import mg_motionplots as motionplots
    from musicalgestures._motionvideo import mg_motionvideo as motionvideo
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
    from musicalgestures._history import history_ffmpeg as history
    from musicalgestures._history import history_cv2
    from musicalgestures._blend import mg_blend_image as blend
    from musicalgestures._pose import pose

    def test_input(self):
        """Gives feedback to user if initialization from input went wrong."""
        mg_input_test(self.filename, self.filtertype, self.thresh, self.starttime, self.endtime, self.blur, self.skip, self.frames)

    def info(self, type='video'):
        """Retrieves the information related to video, audio and format."""
        info = get_metadata(self.filename)

        if type == 'video':
            return info[0]
        elif type == 'audio':
            return info[1]
        elif type == 'format':
            return info[2]
        else:
            return info

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
            # update filename after the processes
            self.filename = self.of + self.fex

        # Check if there is audio in the video file
        if self.has_audio:
            self.audio = MgAudio(self.filename, self.sr, self.n_fft, self.hop_length)

    def __repr__(self):
        return f"MgVideo('{self.filename}')"
    
    ########## HACK TO REMOVE IN THE FUTURE ##########
    def average(self, filename=None, normalize=True, target_name=None, overwrite=False):
        print("From musicalgestures v1.3.0, the function `average` is no longer available. Use the function `blend(component_mode='average')` instead. More information can be found in the documentation: https://github.com/fourMs/MGT-python/wiki/4-%E2%80%90-Video%E2%80%90based-Processes#blend")
        return self.blend(component_mode='average')
    ##################################################


class Examples:
    def __init__(self):
        module_path = os.path.realpath(
            os.path.dirname(__file__)).replace("\\", "/")
        # module_path = os.path.abspath(os.path.dirname(__file__))
        self.dance = module_path + "/dancer.avi"
        self.pianist = module_path + "/examples/pianist.avi"
        self.notebook = module_path + "/MusicalGesturesToolbox.ipynb"

examples = Examples()
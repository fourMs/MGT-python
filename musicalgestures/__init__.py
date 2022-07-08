import os
from musicalgestures._input_test import mg_input_test
from musicalgestures._videoreader import mg_videoreader
from musicalgestures._flow import Flow
from musicalgestures._audio import Audio
from musicalgestures._mglist import MgList
from musicalgestures._utils import MgImage, MgFigure, metadata

class MgVideo:
    """
    This is the class for working with video files in the Musical Gestures Toolbox.
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
            filtertype='Regular',
            thresh=0.05,
            starttime=0,
            endtime=0,
            blur='None',
            skip=0,
            rotate=0,
            color=True,
            contrast=0,
            brightness=0,
            crop='None',
            keep_all=False,
            returned_by_process=False):
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
            rotate (int, optional): Rotates the video by a `rotate` degrees. Defaults to 0.
            color (bool, optional): If False, converts the video to grayscale and sets every method in grayscale mode. Defaults to True.
            contrast (int, optional): Applies +/- 100 contrast to video. Defaults to 0.
            brightness (int, optional): Applies +/- 100 brightness to video. Defaults to 0.
            crop (str, optional): If 'manual', opens a window displaying the first frame of the input video file, where the user can draw a rectangle to which cropping is applied. If 'auto' the cropping function attempts to determine the area of significant motion and applies the cropping to that area. Defaults to 'None'. 
            keep_all (bool, optional): If True, preserves an output video file after each used preprocessing stage. Defaults to False.
            returned_by_process (bool, optional): This parameter is only for internal use, do not use it. Defaults to False.
        """

        self.filename = filename
        # name of file without extension (only-filename)
        self.of = os.path.splitext(self.filename)[0]
        # file extension
        self.fex = os.path.splitext(self.filename)[1]
        self.color = color
        self.starttime = starttime
        self.endtime = endtime
        self.skip = skip
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
        self.test_input()
        self.get_video()
        self.flow = Flow(self, self.filename, self.color, self.has_audio)
        self.audio = Audio(self.filename)

    from musicalgestures._motionvideo import mg_motion as motion
    from musicalgestures._motionvideo_mp_run import mg_motion_mp as motion_mp
    from musicalgestures._motionvideo import mg_motiongrams as motiongrams
    from musicalgestures._motionvideo import mg_motiondata as motiondata
    from musicalgestures._motionvideo import mg_motionplots as motionplots
    from musicalgestures._motionvideo import mg_motionvideo as motionvideo
    from musicalgestures._videograms import videograms_ffmpeg as videograms
    from musicalgestures._directograms import mg_directograms as directograms
    from musicalgestures._warp import mg_warp_audiovisual_beats as warp_audiovisual_beats
    from musicalgestures._blurfaces import mg_blurfaces as blur_faces
    from musicalgestures._impacts import mg_impacts as impacts
    from musicalgestures._grid import mg_grid as grid
    from musicalgestures._audio import mg_audio_spectrogram
    from musicalgestures._audio import mg_audio_descriptors
    from musicalgestures._motionvideo import plot_motion_metrics
    # from musicalgestures._cropvideo import mg_cropvideo, find_motion_box, find_total_motion_box
    from musicalgestures._show import mg_show as show
    from musicalgestures._history import history_ffmpeg as history
    from musicalgestures._history import history_cv2
    from musicalgestures._average import mg_average_image as average
    from musicalgestures._pose import pose

    def test_input(self):
        """Gives feedback to user if initialization from input went wrong."""
        mg_input_test(self.filename, self.filtertype, self.thresh, self.starttime, self.endtime, self.blur, self.skip)

    def info(self, type='video'):
        """Retrieves the information related to video, audio and format."""
        video, audio, format = metadata(self.filename)
        if type == 'video':
            return video
        elif type == 'audio':
            return audio
        elif type == 'format':
            return format
        else:
            return video, audio, format

    def get_video(self):
        """Creates a video attribute to the Musical Gestures object with the given correct settings."""
        self.length, self.width, self.height, self.fps, self.endtime, self.of, self.fex, self.has_audio = mg_videoreader(
            filename=self.filename,
            starttime=self.starttime,
            endtime=self.endtime,
            skip=self.skip,
            rotate=self.rotate,
            contrast=self.contrast,
            brightness=self.brightness,
            crop=self.crop,
            color=self.color,
            returned_by_process=self.returned_by_process,
            keep_all=self.keep_all)

        # update filename after the processes
        self.filename = self.of + self.fex

    def __repr__(self):
        return f"MgVideo('{self.filename}')"


class Examples:
    def __init__(self):
        module_path = os.path.realpath(
            os.path.dirname(__file__)).replace("\\", "/")
        # module_path = os.path.abspath(os.path.dirname(__file__))
        self.dance = module_path + "/dance.avi"
        self.pianist = module_path + "/examples/pianist.avi"
        self.notebook = module_path + "/MusicalGesturesToolbox.ipynb"

examples = Examples()

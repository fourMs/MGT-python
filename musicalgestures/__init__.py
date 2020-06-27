import os
from musicalgestures._input_test import mg_input_test
from musicalgestures._videoreader import mg_videoreader
from musicalgestures._flow import Flow


class MgObject:
    """ 
    Initializes Musical Gestures data structure from a video file.

    Attributes
    ----------
    - filename : str

        Path to the video file.
    - filtertype : {'Regular', 'Binary', 'Blob'}, optional

        The `filtertype` parameter for the `motion()` method.
        `Regular` turns all values below `thresh` to 0.
        `Binary` turns all values below `thresh` to 0, above `thresh` to 1.
        `Blob` removes individual pixels with erosion method.

    - thresh : float, optional

        The `thresh` parameter for the `motion()` method.
        A number in the range of 0 to 1. Default is 0.05.
        Eliminates pixel values less than given threshold.
    - starttime : int or float, optional

        Trims the video from this start time (s).
    - endtime : int or float, optional

        Trims the video until this end time (s).
    - blur : {'None', 'Average'}, optional

        The `blur` parameter for the `motion()` method.
        `Average` to apply a 10px * 10px blurring filter, `None` otherwise.
    - skip : int, optional

        Time-shrinks the video by skipping (discarding) every n frames determined by `skip`.
    - rotate : int or float, optional

        Rotates the video by a `rotate` degrees.
    - color : bool, optional

        Default is `True`. If `False`, converts the video to grayscale and sets every method in grayscale mode.
    - contrast : int or float, optional

        Applies +/- 100 contrast to video.
    - brightness : int or float, optional

        Applies +/- 100 brightness to video.
    - crop : {'none', 'manual', 'auto'}, optional

        If `manual`, opens a window displaying the first frame of the input video file,
        where the user can draw a rectangle to which cropping is applied.
        If `auto` the cropping function attempts to determine the area of significant motion 
        and applies the cropping to that area.

    - keep_all : bool, optional

        Default is `False`. If `True`, preserves an output video file after each used preprocessing stage.
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
        self.flow = Flow(self.filename, self.color, self.has_audio)

    from musicalgestures._motionvideo import mg_motionvideo as motion
    from musicalgestures._motionvideo import plot_motion_metrics
    from musicalgestures._cropvideo import mg_cropvideo, find_motion_box, find_total_motion_box
    # from musicalgestures._motionhistory import mg_motionhistory as motionhistory
    from musicalgestures._show import mg_show as show
    # from musicalgestures._history import history
    from musicalgestures._history import history_ffmpeg as history
    from musicalgestures._average import mg_average_image as average

    def test_input(self):
        """ Gives feedback to user if initialization from input went wrong. """
        mg_input_test(self.filename, self.filtertype,
                      self.thresh, self.starttime, self.endtime, self.blur, self.skip)

    def get_video(self):
        """ Creates a video attribute to the Musical Gestures object with the given correct settings. """
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
        return f"MgObject('{self.filename}')"

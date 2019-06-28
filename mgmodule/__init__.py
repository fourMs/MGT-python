import os
from ._input_test import mg_input_test
from ._videoreader import mg_videoreader
from ._constrainNumber import constrainNumber
class MgObject:
    """ 
    Initializes Musical Gestures data structure from a given parameter video file.

    Parameters:
    filename (str): Name of input parameter video file.
    method (str): Currently 'Diff' is the only implemented method. 
    filtertype (str): 'Regular', 'Binary', 'Blob' (see function filterframe).
    thresh (float): a number in [0,1]. Eliminates pixel values less than given threshold.
    starttime (float): cut the video from this start time (min) to analyze what is relevant.
    endtime (float): cut the video at this end time (min) to analyze what is relevant.
    blur (str): 'Average' to apply a blurring filter, 'None' otherwise.
    skip (int): When proceeding to analyze next frame of video, this many frames are skipped.
    color (bool): True does the analysis in RGB, False in grayscale. 
    contrast (float): apply +/- 100 contrast to video
    brightness (float): apply +/- 100 brightness to video
    crop (str): 'none', 'manual', 'auto' to select cropping of relevant video frame size
    """

    def __init__(self, filename, method = 'Diff', filtertype = 'Regular', thresh = 0.0001, starttime = 0, endtime = 0, blur = 'None', skip = 0, color = True, contrast = 0, brightness = 0, crop = 'None'):

        self.filename = filename
        self.of = os.path.splitext(self.filename)[0] 
        self.fex = os.path.splitext(self.filename)[1] 
        self.color = color
        self.method = method
        self.starttime = starttime
        self.endtime = endtime
        self.skip = skip
        self.filtertype = filtertype
        self.thresh = thresh
        self.blur = blur
        self.contrast = contrast
        self.brightness = brightness
        self.crop = crop
        self.test_input()
        self.get_video()

    
    from ._motionvideo import mg_motionvideo, plot_motion_metrics
    from ._cropvideo import mg_cropvideo, find_motion_box, find_total_motion_box
    from ._motionhistory import mg_motionhistory
    from ._show import mg_show

    def test_input(self):
        """ Gives feedback to user if initialization from input went wrong. """
        mg_input_test(self.filename, self.method, self.filtertype, self.thresh, self.starttime, self.endtime, self.blur, self.skip)

    def get_video(self):
        """ Creates a video attribute to the Musical Gestures object with the given correct settings. """
        self.video, self.length, self.width, self.height, self.fps, self.endtime, self.of = mg_videoreader(self.filename, self.starttime, self.endtime, self.skip, self.contrast, self.brightness, self.crop)

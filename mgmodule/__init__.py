import os
from ._input_test import input_test
from ._videoreader import mg_videoreader
from ._constrainNumber import constrainNumber
class MgObject:

    def __init__(self, filename, method = 'Diff', filtertype = 'Regular', thresh = 0.0001, starttime = 0, endtime = 0, blur = 'None', skip = 0, color = True, contrast = 0, brightness = 0):
        self.filename = filename
        self.of = os.path.splitext(self.filename)[0] 
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
        self.test_input()

    
    from ._motionvideo import motionvideo, plot_motion_metrics
    from ._cropvideo import cropvideo, find_motion_box, find_total_motion_box
    from ._motionhistory import motionhistory

    def test_input(self):
        input_test(self.filename, self.method, self.filtertype, self.thresh, self.starttime, self.endtime, self.blur, self.skip)

    def get_video(self):
        self.video, self.length, self.width, self.height, self.fps, self.endtime = mg_videoreader(self.filename, self.starttime, self.endtime, self.skip, self.contrast, self.brightness)

from ._input_test import input_test
from ._videoreader import mg_videoreader

class MgObject:

    def __init__(self, filename, method = 'Diff', filtertype = 'Regular', thresh = 0.0001, starttime = 0, endtime = 5, blur = 'Average', skip = 0, color = True):
        self.filename = filename
        self.color = color
        self.method = method
        self.starttime = starttime
        self.endtime = endtime
        self.skip = skip
        self.filtertype = filtertype
        self.thresh = thresh
        self.blur = blur
        self.test_input()
        self.get_video()
    
    from ._motionvideo import motionvideo, plot_motion_metrics
    from ._cropvideo import cropvideo

    def test_input(self):
        input_test(self.filename, self.method, self.filtertype, self.thresh, self.starttime, self.endtime, self.blur, self.skip)

    def get_video(self):
        self.video, self.length, self.width, self.height, self.fps, self.endtime = mg_videoreader(self.filename, self.starttime, self.endtime, self.skip)

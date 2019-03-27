import numpy as np
import os
import csv
import cv2
from scipy.signal import medfilt2d
from matplotlib import pyplot as plt
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from ._input_test import input_test
from ._videoreader import mg_videoreader

class MgObject:

    def __init__(self, filename, method = 'Diff', filtertype = 'Regular', thresh = 0.0001, starttime = 0, endtime = 0, blur = 'Average', skip = 0, color = True):
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
    from ._videoreader import mg_videoreader
    from ._input_test import input_test, Error, InputError
    from ._centroid import mg_centroid


    def test_input(self):
        input_test(self.filename, self.method, self.filtertype, self.thresh, self.starttime, self.endtime, self.blur, self.skip)

    def get_video(self):
        self.video, self.length, self.width, self.height, self.fps, self.endtime = mg_videoreader(self.filename, self.starttime, self.endtime, self.skip)

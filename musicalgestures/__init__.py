import os
from musicalgestures._input_test import mg_input_test
from musicalgestures._videoreader import mg_videoreader
from musicalgestures._flow import Flow
from musicalgestures._audio import MgAudio
from musicalgestures._video import MgVideo
from musicalgestures._360video import Mg360Video
from musicalgestures._utils import (
    MgFigure,
    MgImage,
    convert,
    convert_to_mp4,
    get_framecount,
    ffmpeg_cmd,
    get_length,
    generate_outfilename,
)
from musicalgestures._mglist import MgList


class Examples:
    def __init__(self):
        module_path = os.path.realpath(os.path.dirname(__file__)).replace("\\", "/")
        # module_path = os.path.abspath(os.path.dirname(__file__))
        self.dance = module_path + "/examples/dancer.avi"
        self.pianist = module_path + "/examples/pianist.avi"
        self.notebook = module_path + "/MusicalGesturesToolbox.ipynb"


examples = Examples()

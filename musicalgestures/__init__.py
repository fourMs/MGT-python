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
    get_cuda_device_count,
    show_progress,
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

# --- Modern additions (v1.4.0) ---
from musicalgestures._enums import (
    FilterType,
    BlurType,
    CropMode,
    PoseModel,
    PoseDevice,
    DataFormat,
)
from musicalgestures._exceptions import (
    MgError,
    MgInputError,
    MgProcessingError,
    MgIOError,
    MgDependencyError,
)
from musicalgestures._logging import set_log_level
from musicalgestures._features import MgFeatures
from musicalgestures._stream import MgVideoReader
from musicalgestures._pipeline import MgPipeline, MgStep
from musicalgestures._dataset import MgDataset, MgCorpus, MediaItem
from musicalgestures._pose_estimator import (
    PoseEstimator,
    PoseEstimatorResult,
    MediaPipePoseEstimator,
    OpenPosePoseEstimator,
    get_pose_estimator,
)

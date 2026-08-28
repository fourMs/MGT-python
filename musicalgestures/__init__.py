import os

# Single source of truth for the package version: pyproject.toml reads
# this attribute rather than carrying its own copy. Two static copies
# drift the moment a bump touches one of them, which is how ambiscape
# shipped three releases misreporting themselves and musiscape one.
__version__ = "1.22.0"
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
    cuda_build_available,
    cuda_unavailable_reason,
    show_progress,
)
from musicalgestures._mglist import MgList


class Examples:
    """Paths to the sample media shipped with the package, as `musicalgestures.examples`.

    `examples.dance` and `examples.pianist` are the two short videos the documentation and the
    tests use, and `examples.notebook` is the tutorial notebook. They are absolute paths resolved
    from the installed package, so they work from any working directory.
    """

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
from musicalgestures._contactsheet import mg_contact_sheet as contact_sheet
from musicalgestures._stream import MgVideoReader
from musicalgestures._pipeline import MgPipeline, MgStep
from musicalgestures._dataset import MgDataset, MgCorpus, MediaItem
from musicalgestures._pose_estimator import (
    PoseEstimator,
    PoseEstimatorResult,
    MediaPipePoseEstimator,
    OpenPosePoseEstimator,
    get_pose_estimator,
    get_pose_model_path,
)
from musicalgestures._analysis import (
    smooth,
    bandpass,
    dominant_frequency,
    circular_stats,
    rayleigh_test,
    synchrony,
)

# --- Sound--motion signal methods (ro / stillstanding / cymbal / Westney studies) ---
from musicalgestures._peaks import pick_peaks
from musicalgestures._laughter import laughter_score, laughter_segments
from musicalgestures._coaccentuation import (
    co_accentuation,
    co_accentuation_curve,
)
from musicalgestures._views import (
    filmstrip,
    concordance,
    tier_map,
    structure_map,
)
from musicalgestures._zoomview import zoomable_page
from musicalgestures._plate import (
    room_plate,
    occupancy_track,
    restless_map,
    restless_regions,
    plate_spread,
)
from musicalgestures._multishot import (
    multishot,
    choose_spaced,
    body_mask,
)
from musicalgestures._posetimeline import (
    pose_timeline,
    normalise_poses,
    region_angles,
)
from musicalgestures._noisefloor import (
    noise_floor,
    frame_difference_floor,
    motion_vector_floor,
)
from musicalgestures._pulse import (
    Cycle,
    group_strokes,
    segment_cycles,
    cycle_table,
    fit_accelerando,
    motion_onsets,
)
from musicalgestures._qom import (
    band_limited_qom,
    accel_to_speed,
    group_qom,
    pose_qom,
    body_scale,
    normalized_qom,
    grid_qom,
    envelope,
    bin_series,
)
from musicalgestures._alignment import (
    xcorr_lag,
    envelope_lag,
    per_cycle_motion_delta,
    anchor_and_match,
    offset_stats,
    sliding_correlation,
    envelope_agreement,
    locate_probe,
    align_by_audio,
    envelope_from_audio,
)
from musicalgestures._audiofeatures import (
    rms_envelope,
    spectral_flux,
    spectral_flux_onsets,
    energy_onsets,
    t60_backward_decay,
    attack_spectral_centroid,
)
from musicalgestures._motionanalysis import motiongram_data
from musicalgestures._anglegram import anglegram_data, load_aem
from musicalgestures._posture import (
    cop_sway_metrics,
    confidence_ellipse_area,
    convex_hull_area,
    stabilogram_diffusion,
    dfa,
    sample_entropy,
    spectral_edges,
    sway_texture,
    sway_orientation,
    axial_rayleigh,
    spatial_extent,
    principal_axis_projection,
)
from musicalgestures._physio import (
    respiration_rate,
    spectral_band_fractions,
)
# NOTE: musicalgestures._mocap also defines `dominant_frequency` (a Welch-peak
# variant from the Westney study). To avoid shadowing the pre-existing
# `_analysis.dominant_frequency` exported above, it is intentionally NOT
# re-exported here; reach it as `musicalgestures._mocap.dominant_frequency`.
from musicalgestures._mocap import (
    read_qtm_tsv,
    compare_modality_envelopes,
)
# Landmark-trajectory pose tools. extract_pose_landmarks needs the optional
# mediapipe package ([pose] extra) but imports it lazily, so this is safe
# without it; the other helpers are numpy-only.
from musicalgestures._posetools import (
    extract_pose_landmarks,
    midpoint,
    limb_speed_from_landmarks,
    impact_events,
    fuse_pose_views,
)

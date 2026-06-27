import os
import musicalgestures
from musicalgestures._utils import generate_outfilename, get_length, ffmpeg_cmd


def mg_motionvectors(self, target_name=None, overwrite=True):
    """
    Renders a video visualising the motion vectors encoded in the input video.

    Inter-frame codecs (MPEG-1/2/4, H.264, H.265, …) store motion vectors that describe
    how macroblocks move between frames. This method uses FFmpeg's ``codecview`` filter
    (with ``-flags2 +export_mvs``) to draw those vectors as arrows on top of the video,
    giving a quick, decoder-level view of motion without any re-computation.

    NB: Only codecs that actually carry motion vectors will show arrows. Intra-only
    formats (e.g. MJPEG, common in ``.avi`` files) have none — convert to an inter-frame
    codec first (e.g. via ``show(mode='notebook')`` which makes an mp4, or any mp4/h264
    source) to see motion vectors.

    Args:
        target_name (str, optional): Target output name for the video. Defaults to None
            (which uses the input filename with the suffix "_motionvectors").
        overwrite (bool, optional): Whether to allow overwriting existing files or to
            automatically increment the target filename. Defaults to False.

    Returns:
        MgVideo: An MgVideo pointing to the rendered motion-vector video.
    """
    of, fex = os.path.splitext(self.filename)

    if target_name is None:
        target_name = of + '_motionvectors' + fex
    else:
        target_name = os.path.splitext(target_name)[0] + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    # -flags2 +export_mvs must precede -i so the decoder exports motion vectors;
    # codecview then draws them (pf=P-frame forward, bf/bb=B-frame forward/backward).
    cmd = [
        'ffmpeg', '-y', '-flags2', '+export_mvs', '-i', self.filename,
        '-vf', 'codecview=mv=pf+bf+bb', '-q:v', '3', target_name,
    ]
    ffmpeg_cmd(cmd, get_length(self.filename), pb_prefix='Rendering motion vectors:')

    self.motionvectors_video = musicalgestures.MgVideo(
        target_name, color=self.color, returned_by_process=True)
    return self.motionvectors_video

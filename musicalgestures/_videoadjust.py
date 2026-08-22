import numpy as np
import cv2
import os
from musicalgestures._utils import scale_num, get_length, ffmpeg_cmd, has_audio, generate_outfilename, convert_to_mp4


def contrast_brightness_ffmpeg(filename, contrast=0, brightness=0, target_name=None, overwrite=True):
    """
    Applies contrast and brightness adjustments on the source video using ffmpeg.

    Args:
        filename (str): Path to the video to process.
        contrast (int/float, optional): Increase or decrease contrast. Values range from -100 to 100. Defaults to 0.
        brightness (int/float, optional): Increase or decrease brightness. Values range from -100 to 100. Defaults to 0.
        target_name (str, optional): Defaults to None (which assumes that the input filename with the suffix "_cb" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

    Returns:
        str: Path to the output video.
    """
    if contrast == 0 and brightness == 0:
        return

    of, fex = os.path.splitext(filename)

    if target_name is None:
        target_name = of + '_cb' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    # keeping values in sensible range
    contrast = np.clip(contrast, -100.0, 100.0)
    brightness = np.clip(brightness, -100.0, 100.0)

    # ranges are "handpicked" so that the results are close to the results of contrast_brightness_cv2 (deprecated)
    if contrast == 0:
        p_saturation, p_contrast, p_brightness = 0, 0, 0
    elif contrast > 0:
        p_saturation = scale_num(contrast, 0, 100, 1, 1.9)
        p_contrast = scale_num(contrast, 0, 100, 1, 2.3)
        p_brightness = scale_num(contrast, 0, 100, 0, 0.04)
    elif contrast < 0:
        p_saturation = scale_num(contrast, 0, -100, 1, 0)
        p_contrast = scale_num(contrast, 0, -100, 1, 0)
        p_brightness = 0

    if brightness != 0:
        p_brightness += brightness / 100

    cmd = ['ffmpeg', '-y', '-i', filename, '-vf',
           f'eq=saturation={p_saturation}:contrast={p_contrast}:brightness={p_brightness}', '-q:v', '3', "-c:a", "copy", target_name]

    ffmpeg_cmd(cmd, get_length(filename),
               pb_prefix='Adjusting contrast and brightness:')

    return target_name


def _build_atempo_chain(ratio):
    """Build a chained atempo filter string for ratios outside FFmpeg's per-filter [0.5, 100.0] limit."""
    parts = []
    while ratio > 100.0:
        parts.append('atempo=100.0')
        ratio /= 100.0
    while ratio < 0.5:
        parts.append('atempo=0.5')
        ratio /= 0.5
    parts.append(f'atempo={ratio:.6g}')
    return ','.join(parts)


def _safe_output_name(path):
    """Return path with colons removed from the basename (colons break FFmpeg output on some systems)."""
    return os.path.join(os.path.dirname(path), os.path.basename(path).replace(':', '_'))


def skip_frames_ffmpeg(filename, skip=0, target_name=None, overwrite=True):
    """
    Time-shrinks the video by skipping (discarding) every n frames determined by `skip`.
    To discard half of the frames (ie. double the speed of the video) use `skip=1`.

    Args:
        filename (str): Path to the video to process.
        skip (int, optional): Discard `skip` frames before keeping one. Defaults to 0.
        target_name (str, optional): Defaults to None (which assumes that the input filename with the suffix "_skip" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

    Returns:
        str: Path to the output video.
    """
    if skip == 0:
        return

    of, fex = os.path.splitext(filename)
    fex = '.avi'

    pts_ratio = 1 / (skip+1)
    atempo_ratio = skip+1

    if target_name is None:
        target_name = _safe_output_name(of + '_skip' + fex)
    else:
        target_name = _safe_output_name(target_name)
    if not overwrite:
        target_name = generate_outfilename(target_name)

    # original duration of the file is stored in the -metadata title variable
    if has_audio(filename):
        # atempo only accepts values in [0.5, 100.0] per filter; chain multiple for large ratios
        atempo_chain = _build_atempo_chain(atempo_ratio)
        cmd = ['ffmpeg', '-y', '-i', filename, '-metadata', f'title={get_length(filename)}', '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v];[0:a]{atempo_chain}[a]', '-map', '[v]', '-map', '[a]', '-q:v', '3', '-shortest', target_name]
    else:
        cmd = ['ffmpeg', '-y', '-i', filename, '-metadata', f'title={get_length(filename)}', '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v]', '-map', '[v]', '-q:v', '3', target_name]

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Skipping frames:')

    return target_name

def fixed_frames_ffmpeg(filename, frames=0, target_name=None, overwrite=True):
    """
    Specify a fixed target number frames to extract from the video. 
    To extract only keyframes from the video, set the parameter keyframes to True.

    Args:
        filename (str): Path to the video to process.
        frames (int), optional): Number frames to extract from the video. If set to -1, it will only extract the keyframes of the video. Defaults to 0.
        target_name (str, optional): Defaults to None (which assumes that the input filename with the suffix "_fixed" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to True.

    Returns:
        str: Path to the output video.
    """
    of, fex = os.path.splitext(filename)

    if fex != '.mp4':
        # Convert video to mp4
        filename = convert_to_mp4(of + fex, overwrite=overwrite)
        of, fex = os.path.splitext(filename)

    if target_name is None:
         target_name = of + '_fixed' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)

    cap = cv2.VideoCapture(filename)
    nb_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))

    pts_ratio = frames / nb_frames
    atempo_ratio = 1 / pts_ratio

    if frames == 0:
        return

    # Extract only keyframes
    if frames == -1:
        cmd = ['ffmpeg', '-y', '-discard', 'nokey', '-i', filename, '-c', 'copy', 'temp.h264'] 
        ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Extracting keyframes:')
        cmd = ['ffmpeg', '-y', '-r', str(fps), '-f', 'h264', '-i', 'temp.h264', '-c', 'copy', target_name]
        ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Encoding temporary video file:') 
        # Remove temporary h264 video file
        os.remove('temp.h264')

        return target_name

    if has_audio(filename):
        atempo_chain = _build_atempo_chain(atempo_ratio)
        cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v];[0:a]{atempo_chain}[a]', '-map', '[v]', '-map', '[a]', '-q:v', '3', '-shortest', target_name]
    else:
        cmd = ['ffmpeg', '-y', '-i', filename, '-filter_complex',
               f'[0:v]setpts={pts_ratio}*PTS[v]', '-map', '[v]', '-q:v', '3', target_name]

    ffmpeg_cmd(cmd, get_length(filename), pb_prefix='Fixing frames:')

    return target_name


def mg_resample(self, fps=None, speed=None, skip=None, target_name=None, overwrite=True) -> "musicalgestures.MgVideo":
    """
    Resample the (already loaded) video and return a **new** MgVideo, leaving the original
    object untouched.

    Three independent, combinable operations:

    * ``fps``: retime to a target frame rate using FFmpeg's ``fps`` filter — **duration-preserving**
      (frames are dropped/duplicated to hit the rate), e.g. 30 → 25 fps.
    * ``speed``: change playback speed by a factor (>1 faster/shorter, <1 slower/longer); the video
      is retimed with ``setpts`` and the audio with ``atempo`` so they stay in sync.
    * ``skip``: integer frame decimation — discard ``skip`` frames for every one kept (this also
      shortens/speeds up the clip), matching the loader's ``skip`` parameter.

    When more than one is given they are applied in order: ``skip`` → ``speed``/``fps``.

    Args:
        fps (float, optional): Target frame rate (duration-preserving). Defaults to None.
        speed (float, optional): Playback-speed factor. Defaults to None.
        skip (int, optional): Discard ``skip`` frames for every one kept. Defaults to None.
        target_name (str, optional): Output name. Defaults to None (input filename + "_resampled").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.

    Returns:
        MgVideo: a new MgVideo pointing to the resampled file.
    """
    import musicalgestures

    if fps is None and speed is None and not skip:
        raise ValueError("Provide at least one of fps, speed, or skip.")
    if speed is not None and speed <= 0:
        raise ValueError("speed must be a positive factor (e.g. 2.0 = twice as fast).")
    if fps is not None and fps <= 0:
        raise ValueError("fps must be a positive number.")

    source = self.filename

    # 1) Integer frame decimation (also speeds up) — reuse the tested helper.
    if skip:
        source = skip_frames_ffmpeg(source, int(skip), overwrite=overwrite)

    # 2) Speed and/or frame-rate retime in a single FFmpeg pass.
    final = source
    if speed is not None or fps is not None:
        of, fex = os.path.splitext(source)
        if target_name is None:
            out = of + '_resampled' + fex
        else:
            out = os.path.splitext(target_name)[0] + fex
        if not overwrite:
            out = generate_outfilename(out)

        vfilters = []
        if speed is not None and speed != 1:
            vfilters.append(f'setpts=PTS/{speed:.6g}')
        if fps is not None:
            vfilters.append(f'fps={fps:.6g}')
        vf = ','.join(vfilters)

        if speed is not None and speed != 1 and has_audio(source):
            # Retime audio too so it stays in sync with the sped-up/slowed-down video.
            atempo_chain = _build_atempo_chain(speed)
            cmd = ['ffmpeg', '-y', '-i', source, '-filter_complex',
                   f'[0:v]{vf}[v];[0:a]{atempo_chain}[a]', '-map', '[v]', '-map', '[a]',
                   '-q:v', '3', '-shortest', out]
        else:
            # fps-only (or no audio): -vf retimes the video and passes audio through unchanged.
            cmd = ['ffmpeg', '-y', '-i', source, '-vf', vf, '-q:v', '3', out]

        ffmpeg_cmd(cmd, get_length(source), pb_prefix='Resampling:')
        final = out

    return musicalgestures.MgVideo(final, color=self.color, returned_by_process=True)


from __future__ import annotations

import os
from musicalgestures._utils import MgImage, get_widthheight, get_framecount, get_length, ffmpeg_cmd, generate_outfilename, resolve_filename
from musicalgestures._mglist import MgList
from musicalgestures._videoadjust import skip_frames_ffmpeg
import math


def videograms_ffmpeg(
    self,
    target_name_x: str | None = None,
    target_name_y: str | None = None,
    overwrite: bool = True,
    mode: str = "average",
    line_x: int | None = None,
    line_y: int | None = None,
) -> "MgList":
    """
    Renders horizontal and vertical videograms of the source video using ffmpeg.
    By default, videoframes are averaged by axes. Alternatively, ``mode='slit'``
    samples a single column and row per frame (photo-finish style) and stacks
    those over time.

    Args:
        target_name_x (str, optional): Target output name for the vertical videogram (the x-axis collapse). Defaults to None (which assumes that the input filename with the suffix "_vgv" should be used).
        target_name_y (str, optional): Target output name for the horizontal videogram (the y-axis collapse). Defaults to None (which assumes that the input filename with the suffix "_vgh" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.
        mode (str, optional): Either ``'average'`` (default) or ``'slit'``.
            ``'slit'`` uses one column/row line per frame instead of averaging.
        line_x (int, optional): Source x-position (column index) used in slit
            mode for the vertical videogram. Defaults to the center column.
        line_y (int, optional): Source y-position (row index) used in slit mode
            for the horizontal videogram. Defaults to the center row.

    Returns:
        MgList: An MgList with the MgImage objects referring to the vertical and horizontal videograms respectively. 
    """

    width, height = get_widthheight(self.filename)
    framecount = get_framecount(self.filename)
    mode = mode.lower()

    if mode not in ["average", "slit"]:
        raise ValueError("mode must be 'average' or 'slit'.")

    def _resolve_line(line: int | None, max_size: int, name: str, default: int) -> int:
        if line is None:
            return default
        if isinstance(line, bool) or not isinstance(line, int):
            raise ValueError(f"{name} must be an integer in the range [0, {max_size - 1}].")
        if line < 0 or line >= max_size:
            raise ValueError(f"{name} must be an integer in the range [0, {max_size - 1}].")
        return line

    slit_x = width // 2
    slit_y = height // 2
    if mode == "slit":
        slit_x = _resolve_line(line_x, width, "line_x", width // 2)
        slit_y = _resolve_line(line_y, height, "line_y", height // 2)

    def calc_skipfactor(width, height, framecount):
        """
        Helper function to calculate the necessary frame-skipping to avoid integer overflow. This makes sure that we can succesfully create videograms even on many-hours-long videos as well.

        Args:
            width (int): The width of the video.
            height (int): The height of the video.
            framecount (int): The number of frames in the video.

        Returns:
            list(int, int): The necessary dilation factors to apply on the video for the horizontal and vertical videograms, respectively.
        """

        intmax = 2147483647
        skipfactor_x = int(
            math.ceil(framecount*8 / (intmax / (height+128) - 1024)))
        skipfactor_y = int(
            math.ceil(framecount / (intmax / ((width*8)+1024) - 128)))
        return skipfactor_x, skipfactor_y

    testx, testy = calc_skipfactor(width, height, framecount)

    if mode == "average":
        suffix_x, suffix_y = "_vgv.png", "_vgh.png"
    else:
        suffix_x, suffix_y = "_vgv_slit.png", "_vgh_slit.png"

    def _filters(framecount: int) -> tuple[str, str]:
        if mode == "average":
            return (
                f"scale=1:{height}:sws_flags=area,normalize,tile={framecount}x1",
                f"scale={width}:1:sws_flags=area,normalize,tile=1x{framecount}",
            )
        return (
            f"format=rgb24,crop=1:{height}:{slit_x}:0,normalize,tile={framecount}x1",
            f"format=rgb24,crop={width}:1:0:{slit_y},normalize,tile=1x{framecount}",
        )

    if testx > 1 or testy > 1:
        necessary_skipfactor = max([testx, testy])
        print(f'{os.path.basename(self.filename)} is too large to process. Applying minimal skipping necessary...')

        shortened_file = skip_frames_ffmpeg(self.filename, skip=necessary_skipfactor-1)
        skip_of = os.path.splitext(shortened_file)[0]
        framecount = get_framecount(shortened_file)
        length = get_length(shortened_file)
        vf_y, vf_x = _filters(framecount)

        target_name_x = resolve_filename(skip_of, suffix_x, target_name_x, overwrite)
        target_name_y = resolve_filename(skip_of, suffix_y, target_name_y, overwrite)

        cmd = ['ffmpeg', '-y', '-i', shortened_file, '-vf',
               vf_y, '-aspect', f'{framecount}:{height}', '-frames', '1', target_name_y]
        ffmpeg_cmd(cmd, length, stream=False, pb_prefix="Rendering horizontal videogram:")

        cmd = ['ffmpeg', '-y', '-i', shortened_file, '-vf',
               vf_x, '-aspect', f'{width}:{framecount}', '-frames', '1', target_name_x]
        ffmpeg_cmd(cmd, length, stream=False, pb_prefix="Rendering vertical videogram:")

        # save results as MgImages at self.video_gram_x and self.video_gram_y for parent MgObject
        self.videogram_x = MgImage(target_name_x)
        self.videogram_y = MgImage(target_name_y)

        # return MgList([MgImage(target_name_x), MgImage(target_name_y)])
        return MgList(self.videogram_x, self.videogram_y)


    else:
        length = get_length(self.filename)
        vf_y, vf_x = _filters(framecount)

        target_name_x = resolve_filename(self.of, suffix_x, target_name_x, overwrite)
        target_name_y = resolve_filename(self.of, suffix_y, target_name_y, overwrite)

        cmd = ['ffmpeg', '-y', '-i', self.filename, '-frames', '1', '-vf',
               vf_y, '-aspect', f'{framecount}:{height}', target_name_y]
        ffmpeg_cmd(cmd, length, stream=False, pb_prefix="Rendering horizontal videogram:")

        cmd = ['ffmpeg', '-y', '-i', self.filename, '-frames', '1', '-vf',
               vf_x, '-aspect', f'{width}:{framecount}', target_name_x]
        ffmpeg_cmd(cmd, length, stream=False, pb_prefix="Rendering vertical videogram:")

        # save results as MgImages at self.videogram_x and self.videogram_y for parent MgObject
        self.videogram_x = MgImage(target_name_x)
        self.videogram_y = MgImage(target_name_y)

        # return MgList([MgImage(target_name_x), MgImage(target_name_y)])
        return MgList(self.videogram_x, self.videogram_y)

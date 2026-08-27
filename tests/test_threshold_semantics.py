"""`threshold` must discard small differences, and must mean the same thing everywhere.

Both halves of that were broken. `filter_frame_ffmpeg` passed the *original video* as
ffmpeg's threshold input rather than the frame difference, so the parameter masked dark
parts of the picture and let every small difference through wherever the picture was
bright --- the opposite of the documented "discards small pixel differences, which removes
sensor noise". Meanwhile the numpy `filter_frame` did discard small differences, so the
same argument meant one thing in `mg_motion` and another in `_impacts`.

These tests use a clip whose answer is known by construction: a uniform change of a known
size, over regions of known brightness. That is the only way to tell the two behaviours
apart, since on ordinary footage both produce a plausible-looking motion image.
"""
import numpy as np
import pytest

from musicalgestures._filter import filter_frame


def _synthetic_pair(tmp_path, change, bright=200, dark=5, size=64):
    """Two frames differing by `change` everywhere, over a bright half and a dark half."""
    import subprocess

    from PIL import Image

    for i in range(2):
        a = np.zeros((size, size, 3), np.uint8)
        a[:, :size // 2] = bright
        a[:, size // 2:] = dark
        a = np.clip(a.astype(int) + (change if i else 0), 0, 255).astype(np.uint8)
        Image.fromarray(a).save(tmp_path / f"f{i:02d}.png")
    out = str(tmp_path / "pair.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "5",
                    "-i", str(tmp_path / "f%02d.png"), "-c:v", "libx264", "-qp", "0",
                    "-pix_fmt", "yuv444p", out], check=True)
    return out


def _motion_frame(video, threshold=0.05):
    """The motion frame MGT's ffmpeg path produces, as greyscale."""
    import subprocess

    import cv2

    from musicalgestures._filter import filter_frame_ffmpeg
    from musicalgestures._utils import get_widthheight

    w, h = get_widthheight(video)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", video]
    cmd, chain = filter_frame_ffmpeg(video, cmd, True, "None", "Regular", threshold, 5,
                                     False)
    cmd += ["-filter_complex", chain[:-1], "-f", "image2pipe", "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = w * h * 3
    frames = [cv2.cvtColor(
        np.frombuffer(raw[i * n:(i + 1) * n], np.uint8).reshape(h, w, 3),
        cv2.COLOR_BGR2GRAY) for i in range(len(raw) // n)]
    return frames[-1]


class Test_it_discards_small_differences:
    def test_a_change_below_the_threshold_is_discarded_even_where_the_picture_is_bright(
            self, tmp_path):
        """The failing case. A 3-level change is far below a threshold of 12.75 and must
        go, whether it sits on a bright part of the picture or a dark one."""
        motion = _motion_frame(_synthetic_pair(tmp_path, change=3))
        bright_half = motion[:, :motion.shape[1] // 2]
        assert bright_half.mean() < 1.0

    def test_a_change_above_the_threshold_survives(self, tmp_path):
        motion = _motion_frame(_synthetic_pair(tmp_path, change=40))
        bright_half = motion[:, :motion.shape[1] // 2]
        assert bright_half.mean() > 30


class Test_the_two_paths_agree:
    """The same argument has to mean the same thing in `mg_motion` and in `_impacts`."""

    @pytest.mark.parametrize("change", [3, 20, 40])
    def test_ffmpeg_path_matches_the_numpy_path(self, tmp_path, change):
        motion = _motion_frame(_synthetic_pair(tmp_path, change=change))
        # What filter_frame would make of the same difference, without its median filter.
        raw_difference = np.full_like(motion, change)
        expected = (raw_difference > 0.05 * 255) * raw_difference
        assert abs(float(motion.mean()) - float(expected.mean())) < 0.6

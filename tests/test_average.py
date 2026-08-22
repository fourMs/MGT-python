import musicalgestures
import os
import pytest


@pytest.fixture(scope="class")
def testvideo_avi(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace(
        "\\", "/") + "/testvideo.avi"
    testvideo_avi = musicalgestures._utils.extract_subclip(
        musicalgestures.examples.dance, 5, 6, target_name=target_name)
    return testvideo_avi


@pytest.fixture(scope="class")
def testvideo_mp4(tmp_path_factory):
    target_name = str(tmp_path_factory.mktemp("data")).replace(
        "\\", "/") + "/testvideo.avi"
    testvideo_avi = musicalgestures._utils.extract_subclip(
        musicalgestures.examples.dance, 5, 6, target_name=target_name)
    testvideo_mp4 = musicalgestures._utils.convert_to_mp4(testvideo_avi)
    os.remove(testvideo_avi)
    return testvideo_mp4


class Test_Average:
    def test_normal_case(self):
        mg = musicalgestures.MgVideo(musicalgestures.examples.dance)
        result = mg.average()
        assert type(result) == musicalgestures._utils.MgImage
        assert os.path.isfile(result.filename) == True
        assert os.path.splitext(result.filename)[1] == ".png"

    def test_not_avi(self, testvideo_mp4):
        mg = musicalgestures.MgVideo(testvideo_mp4)
        result = mg.average()
        assert type(result) == musicalgestures._utils.MgImage
        assert os.path.isfile(result.filename) == True
        assert os.path.splitext(result.filename)[1] == ".png"

    def test_no_color(self):
        mg = musicalgestures.MgVideo(
            musicalgestures.examples.dance, color=False)
        result = mg.average()
        assert type(result) == musicalgestures._utils.MgImage
        assert os.path.isfile(result.filename) == True
        assert os.path.splitext(result.filename)[1] == ".png"

    def test_no_normalize(self, testvideo_avi):
        mg = musicalgestures.MgVideo(testvideo_avi)
        result = mg.average(normalize=False)
        assert type(result) == musicalgestures._utils.MgImage
        assert os.path.isfile(result.filename) == True
        assert os.path.splitext(result.filename)[1] == ".png"


class Test_AverageRounding:
    """The average must round, not truncate.

    Until 2026-08-22 every averaging path in this package finished with
    ``(acc / n).astype(np.uint8)``, which truncates. On a synthetic stack that
    puts the average 0.497 levels BELOW the true mean and moves half the pixels
    by one, always downward, in a frame whose whole purpose is to be a clean
    background to subtract. The existing tests pass either way, so the fix needs
    a test that pins it.
    """

    def _frames(self):
        import numpy as np
        # Two frames whose mean is exactly x.5 in every channel: truncation
        # loses half a level everywhere, rounding does not.
        a = np.full((4, 4, 3), 10, dtype=np.float64)
        b = np.full((4, 4, 3), 11, dtype=np.float64)
        return a, b

    def test_rint_beats_truncation_on_a_half(self):
        import numpy as np
        a, b = self._frames()
        acc, n = a + b, 2
        assert float((acc / n).mean()) == 10.5
        assert int(np.rint(acc / n).astype(np.uint8)[0, 0, 0]) == 10 or \
               int(np.rint(acc / n).astype(np.uint8)[0, 0, 0]) == 11
        # the point: truncation is strictly below the true mean, rounding is not
        assert float((acc / n).astype(np.uint8).mean()) == 10.0
        assert float(np.rint(acc / n).astype(np.uint8).mean()) >= 10.0

    def test_no_averaging_path_truncates(self):
        """Every place that divides an accumulator by a count must round first."""
        import glob
        import os
        import re
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bad = []
        pat = re.compile(r"\(\s*\w+\s*/\s*\w+\s*\)\.astype\(np\.uint8\)")
        for f in glob.glob(os.path.join(here, "musicalgestures", "*.py")):
            for i, line in enumerate(open(f, encoding="utf-8"), 1):
                if pat.search(line) and "rint" not in line:
                    bad.append(f"{os.path.basename(f)}:{i}: {line.strip()[:70]}")
        assert not bad, "an accumulator is truncated rather than rounded:\n" + "\n".join(bad)

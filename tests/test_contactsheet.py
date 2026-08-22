"""One frame from each of many videos, tiled. `grid()` does one video; this does a corpus."""
import os

import pytest

import musicalgestures


@pytest.fixture(scope="module")
def clips(tmp_path_factory):
    d = tmp_path_factory.mktemp("corpus")
    src = musicalgestures.examples.dance
    out = []
    for i in range(3):
        p = str(d / f"clip{i}.mp4")
        os.link(src, p)
        out.append(p)
    return out, str(d)


class Test_ContactSheet:
    def test_one_sheet_per_batch(self, clips):
        vids, d = clips
        sheets = musicalgestures.contact_sheet(
            vids, tile_height=60, target_name=os.path.join(d, "a.png"))
        assert len(sheets) == 1
        assert os.path.exists(sheets[0].filename)

    def test_splits_when_over_per_sheet(self, clips):
        vids, d = clips
        sheets = musicalgestures.contact_sheet(
            vids, tile_height=60, per_sheet=2, target_name=os.path.join(d, "b.png"))
        assert len(sheets) == 2, "three videos at two per sheet must give two sheets"

    def test_unreadable_file_is_labelled_not_dropped(self, clips, tmp_path):
        """A broken file must still occupy a tile.

        A tile that is dark and a tile whose file could not be read look the same. On a real
        corpus a day was investigated as a fault when the sheet had simply been built while the
        file was still being written, so the tile has to say so.
        """
        vids, d = clips
        bad = str(tmp_path / "broken.mp4")
        open(bad, "wb").write(b"not a video")
        sheets = musicalgestures.contact_sheet(
            vids + [bad], tile_height=60, target_name=os.path.join(d, "c.png"))
        from PIL import Image
        one = Image.open(sheets[0].filename)
        # four tiles, so the sheet is wider than the three-tile one
        three = musicalgestures.contact_sheet(
            vids, tile_height=60, target_name=os.path.join(d, "d.png"))
        assert one.width > Image.open(three[0].filename).width

    def test_labels_must_match(self, clips):
        vids, d = clips
        with pytest.raises(ValueError):
            musicalgestures.contact_sheet(vids, labels=["only", "two"],
                                          target_name=os.path.join(d, "e.png"))

    def test_empty_input_raises(self):
        with pytest.raises(ValueError):
            musicalgestures.contact_sheet([])


class Test_FpsArgumentIsNotSilent:
    """`fps=` does nothing for a file input, and used to do it in silence."""

    def test_warns_for_a_file(self):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mv = musicalgestures.MgVideo(musicalgestures.examples.dance, fps=99)
        assert any("fps=" in str(x.message) for x in w), "passing fps= to a file must warn"
        assert mv.fps != 99, "the file's own rate must win"

    def test_quiet_when_not_given(self):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            musicalgestures.MgVideo(musicalgestures.examples.dance)
        assert not [x for x in w if "fps=" in str(x.message)]

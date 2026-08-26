"""Reading ELAN's tab/comma export, which is how collaborators' annotations arrive.

MGT already reads `.eaf`. This reads the other thing ELAN produces, and the one people
actually send: File > Export > Tab-delimited text, saved as CSV. It arrives with a
`#file:///...` provenance line above the header, several redundant time columns, and one
column per tier with the tier's annotations in it.

The awkward parts, each of which has a test:

- Times appear three ways --- `hh:mm:ss.ms`, seconds, and PAL timecode. Only the seconds
  column is read, because the other two are derived and PAL assumes 25 fps.
- Blank cells are the normal state. A row exists for every span on ANY tier, so a row
  carrying a segmentation but no laughter has an empty laughter cell, and turning that
  into a zero-length annotation would invent data.
- ELAN appends its internal annotation id, as in `Searching for material [a491]`. The id
  identifies the annotation across exports and is worth keeping, but it is not the label.
"""
import pytest

from musicalgestures._elan import read_elan_csv

EXPORT = '''"#file:///D:/x/Session.mp4 -- offset: 0, duration: 00:05:00.000 / 300.000 / 300000, ms per sample: 40.0",,,,,,,,,,
"Begin Time - hh:mm:ss.ms","Begin Time - ss.msec","Begin Time - PAL","End Time - hh:mm:ss.ms","End Time - ss.msec","End Time - PAL","Duration - hh:mm:ss.ms","Duration - ss.msec","Duration - PAL","Laughter","Segmentation"
00:00:00.000,0.0,00:00:00:00,00:00:10.000,10.0,00:00:10:00,00:00:10.000,10.0,00:00:10:00,,"Searching for material  [a491]"
00:00:10.000,10.0,00:00:10:00,00:00:14.500,14.5,00:00:14:12,00:00:04.500,4.5,00:00:04:12,"Together, contagious, ENJOYMENT [a1]","Searching for material  [a491]"
00:00:20.000,20.0,00:00:20:00,00:00:30.000,30.0,00:00:30:00,00:00:10.000,10.0,00:00:10:00,,"Repeating from top [a492]"
'''


@pytest.fixture
def export(tmp_path):
    p = tmp_path / "export.csv"
    p.write_text(EXPORT, encoding="utf8")
    return p


def test_each_annotation_column_becomes_its_own_level(export):
    h = read_elan_csv(export)
    assert set(h.levels) == {"Laughter", "Segmentation"}


def test_times_come_from_the_seconds_column(export):
    h = read_elan_csv(export)
    laugh = h.levels["Laughter"]
    assert len(laugh) == 1
    assert laugh[0].start == pytest.approx(10.0)
    assert laugh[0].end == pytest.approx(14.5)


def test_blank_cells_do_not_become_annotations(export):
    """Two of the three rows have no laughter. Inventing spans for them would be data."""
    h = read_elan_csv(export)
    assert len(h.levels["Laughter"]) == 1
    assert len(h.levels["Segmentation"]) == 3


def test_the_elan_annotation_id_is_separated_from_the_label(export):
    h = read_elan_csv(export)
    seg = h.levels["Segmentation"][0]
    assert seg.labels["Segmentation"] == "Searching for material"
    assert seg.features["elan_id"] == "a491"


def test_the_provenance_line_records_the_file_it_was_annotated_against(export):
    """The single most important fact in the export, for this project.

    Finn Upham's annotations of this corpus are on cut, re-encoded videos of different
    duration from ours. Reading the spans without reading WHICH FILE they describe is
    how annotations silently land on the wrong timeline.
    """
    h = read_elan_csv(export)
    assert h.levels["Segmentation"][0].features["source_file"].endswith("Session.mp4")
    assert h.levels["Segmentation"][0].features["source_duration_s"] == pytest.approx(300.0)


def test_source_is_recorded_so_pooled_spans_can_be_told_apart(export):
    h = read_elan_csv(export)
    assert h.levels["Laughter"][0].source == "elan"


def test_a_media_path_containing_spaces_is_not_truncated(tmp_path):
    """Found on real data, where the truncation was silent.

    Finn Upham's exports name `F:/HYBRID Dance DATA for processing/.../CoLocated_...mp4`.
    A reader that stops the path at the first space records the source as `HYBRID` and
    loses exactly the fact --- which file these times belong to --- that the provenance
    line exists to carry. The duration still parsed, so nothing looked wrong.
    """
    p = tmp_path / "spaced.csv"
    p.write_text(
        '"#file:///F:/HYBRID Dance DATA/Video/CoLocated_Cut_25fps.mp4 -- offset: 0, '
        'duration: 00:56:22.360 / 3382.360 / 3382360, ms per sample: 40.0",,,,,,,,,,\n'
        '"Begin Time - hh:mm:ss.ms","Begin Time - ss.msec","Begin Time - PAL",'
        '"End Time - hh:mm:ss.ms","End Time - ss.msec","End Time - PAL",'
        '"Duration - hh:mm:ss.ms","Duration - ss.msec","Duration - PAL","Segmentation"\n'
        '00:00:00.000,0.0,00:00:00:00,00:00:10.000,10.0,00:00:10:00,'
        '00:00:10.000,10.0,00:00:10:00,"Searching [a1]"\n',
        encoding="utf8")
    h = read_elan_csv(p)
    src = h.levels["Segmentation"][0].features["source_file"]
    assert src.endswith("CoLocated_Cut_25fps.mp4")
    assert "HYBRID Dance DATA" in src

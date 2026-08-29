"""A self-contained zoomable page: the one thing the original goal asked for and never got.

The stated aim for this corpus included "the ability to zoom from the whole session down to
a single action". What existed was three printed scales over a thirteen-level pyramid that
could support any scale. This closes that.

Self-contained matters: the page has to work from a folder somebody was sent, with no
server and no network, or it is not a deliverable. So the data is embedded, and the amount
embedded is a decision with a right answer --- enough to zoom usefully, not so much that the
file will not open. That decision is what is tested here.
"""
import numpy as np
import pytest

from musicalgestures._zoomview import decimate_minmax_pairs, embed_budget


def test_decimation_keeps_both_extremes_of_each_bucket():
    """A brief spike is exactly what zooming out must not lose; a mean would remove it."""
    x = np.zeros(100)
    x[7] = 5.0
    x[8] = -3.0
    lo, hi = decimate_minmax_pairs(x, 10)
    assert hi[0] == pytest.approx(5.0)
    assert lo[0] == pytest.approx(-3.0)


def test_decimation_returns_the_requested_number_of_buckets():
    lo, hi = decimate_minmax_pairs(np.arange(1000, dtype=float), 250)
    assert len(lo) == len(hi) == 250


def test_a_series_shorter_than_the_bucket_count_is_returned_whole():
    """Asking for more detail than exists must not invent any."""
    lo, hi = decimate_minmax_pairs(np.array([1.0, 2.0, 3.0]), 100)
    assert len(lo) == 3
    assert list(hi) == [1.0, 2.0, 3.0]


def test_an_empty_series_gives_empty_output_rather_than_an_error():
    lo, hi = decimate_minmax_pairs(np.array([]), 10)
    assert len(lo) == 0


def test_the_budget_gives_finer_resolution_for_a_shorter_recording():
    coarse = embed_budget(duration_s=9000.0, max_points=8000)
    fine = embed_budget(duration_s=600.0, max_points=8000)
    assert fine["seconds_per_point"] < coarse["seconds_per_point"]


def test_the_budget_never_promises_more_points_than_asked_for():
    b = embed_budget(duration_s=9000.0, max_points=4000)
    assert b["n_points"] <= 4000


def test_the_budget_reports_the_finest_resolution_the_page_can_show():
    """A page that cannot resolve a one-second gesture should say so, not imply it can."""
    b = embed_budget(duration_s=9513.6, max_points=8000)
    assert b["seconds_per_point"] == pytest.approx(9513.6 / 8000, rel=1e-6)
    assert "seconds_per_point" in b and b["seconds_per_point"] > 0


def _analysis(tmp_path, frames=500, fps=50.0):
    """The least an analysis directory needs for a page: a track and its metadata."""
    import json

    d = tmp_path / "analysis"
    d.mkdir()
    np.asarray(np.random.rand(frames), np.float32).tofile(d / "qom.f4")
    (d / "tracks.json").write_text(json.dumps(
        {"frames": frames, "fps": fps, "qom": "qom.f4",
         "videogram_v": "videogram_v.u1", "videogram_h": "videogram_h.u1",
         "width": 64, "height": 36}))
    return d


def _payload(path):
    import json
    from pathlib import Path

    html = Path(path).read_text()
    return json.loads(html.split("const D = ", 1)[1].split(";\nconst", 1)[0])


def test_the_page_carries_every_video_representation_it_is_given(tmp_path):
    """`video=` names the strips: each is embedded, and the page can switch."""
    from musicalgestures._zoomview import zoomable_page

    reps = {"videogram": np.random.rand(36, 500),
            "motiongram": np.random.rand(36, 500)}
    out = zoomable_page(_analysis(tmp_path), 10.0, tmp_path / "z.html", video=reps)
    payload = _payload(out)
    assert [v["name"] for v in payload["video"]] == ["videogram", "motiongram"]
    assert all(len(v["png"]) > 100 for v in payload["video"])


def test_audio_strips_are_embedded_when_an_audio_file_is_given(tmp_path):
    """`audio=` adds a band with a waveform and a spectrogram to switch between."""
    import soundfile as sf

    from musicalgestures._zoomview import zoomable_page

    sr = 8000
    t = np.arange(sr * 4) / sr
    sf.write(tmp_path / "a.wav",
             (0.5 * np.sin(2 * np.pi * 220 * t)).astype(np.float32), sr)
    out = zoomable_page(_analysis(tmp_path), 4.0, tmp_path / "z.html",
                        video={"videogram": np.random.rand(36, 200)},
                        audio=tmp_path / "a.wav")
    payload = _payload(out)
    assert payload["audio"] is not None
    assert len(payload["audio"]["waveLo"]) == len(payload["audio"]["waveHi"])
    assert len(payload["audio"]["waveLo"]) > 100
    assert len(payload["audio"]["spectrogram"]) > 100


def test_without_the_new_arguments_the_page_still_has_one_videogram_strip(tmp_path):
    """The default page is unchanged in kind: one video strip from the pyramid."""
    from musicalgestures._zoomview import zoomable_page

    d = _analysis(tmp_path)
    #: A base-level pyramid file is enough for read_columns.
    np.random.randint(0, 255, (500, 36), dtype=np.uint8).tofile(d / "videogram_v.u1")
    out = zoomable_page(d, 10.0, tmp_path / "z.html")
    payload = _payload(out)
    assert [v["name"] for v in payload["video"]] == ["videogram"]
    assert payload["audio"] is None


def test_a_player_is_embedded_when_a_video_file_is_named(tmp_path):
    """`player=` puts a video element above the strips, referencing the file by its
    RELATIVE name: the page stays serverless, needing only the folder it ships in."""
    from musicalgestures._zoomview import zoomable_page

    out = zoomable_page(_analysis(tmp_path), 10.0, tmp_path / "z.html",
                        video={"videogram": np.random.rand(36, 200)},
                        player="session_proxy.mp4")
    html = (tmp_path / "z.html").read_text()
    assert "<video" in html
    assert _payload(out)["player"] == "session_proxy.mp4"


def test_without_a_player_no_video_element_ships(tmp_path):
    from musicalgestures._zoomview import zoomable_page

    out = zoomable_page(_analysis(tmp_path), 10.0, tmp_path / "z.html",
                        video={"videogram": np.random.rand(36, 200)})
    assert "<video" not in (tmp_path / "z.html").read_text()
    assert _payload(out)["player"] is None


def test_the_page_is_reachable_as_a_method_on_any_video(tmp_path):
    """`MgVideo.zoompage()` generalises the page: extraction, strip, player and
    output all derive from the video itself, cached beside it like every analysis."""
    import musicalgestures
    from _synth import moving_block_video

    clip = moving_block_video(tmp_path / "walk.mp4", dx=4, frames=50)
    out = musicalgestures.MgVideo(clip).zoompage()
    out = str(out)
    assert out.endswith("_zoom.html")
    payload = _payload(out)
    assert len(payload["video"]) >= 1
    assert payload["player"] == "walk.mp4"
    #: The synthetic clip has no audio stream, and a missing band is not an error.
    assert payload["audio"] is None


def test_a_start_offset_pages_a_slice_of_the_session(tmp_path):
    """`start_s` pages a time range: the track is sliced and tier spans land in page time."""
    import json as _json

    from musicalgestures._actions import Action
    from musicalgestures._hierarchy import Hierarchy
    from musicalgestures._zoomview import zoomable_page

    d = tmp_path / "analysis"
    d.mkdir()
    qom = np.zeros(500, np.float32)
    qom[250:] = 1.0                        # silent first 5 s, loud last 5 s, at 50 fps
    qom.tofile(d / "qom.f4")
    (d / "tracks.json").write_text(_json.dumps(
        {"frames": 500, "fps": 50.0, "qom": "qom.f4"}))
    h = Hierarchy(levels={"structure": [Action(start=2.0, end=7.0, source="test"),
                                        Action(start=0.5, end=1.0, source="test")]})
    out = zoomable_page(d, 5.0, tmp_path / "z.html", hierarchy=h,
                        video={"g": np.random.rand(8, 100)}, start_s=5.0)
    p = _payload(out)
    assert p["duration"] == 5.0
    #: The silent half lies before the page's range, so nothing on the page is quiet.
    assert min(p["lo"]) == 1.0
    #: 2--7 s on the session clock crosses the page's start: clipped and shifted to
    #: page time. The 0.5--1 s span lies wholly outside and is dropped.
    assert p["tiers"][0]["spans"] == [[0.0, 2.0]]

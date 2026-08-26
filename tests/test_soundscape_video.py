"""Giving a video the soundscape vocabulary.

`soundscape_features` took an ambiscape session folder --- several WAVs on one clock ---
which is the right input when somebody recorded a place on purpose. It is the wrong input
when what you have is a video, which is what this toolbox is for, and every recording in
the corpus this was written against is one.

ambiscape opens a single file as a one-take session, so the adapter is short. What has a
right answer, and is tested here, is the decision: does this path need its audio pulling
out first, is it already a sound file, or is it a session folder to pass straight through.
Getting that wrong silently is how a video ends up analysed as a folder of one.
"""
from pathlib import Path

import pytest

from musicalgestures._soundscape import audio_source_for


def test_a_video_needs_its_audio_extracted(tmp_path):
    v = tmp_path / "session.mp4"
    v.write_bytes(b"")
    kind, target = audio_source_for(v)
    assert kind == "extract"
    assert Path(target).suffix == ".wav"
    assert Path(target).stem.startswith("session")


def test_a_wav_is_used_where_it_lies(tmp_path):
    w = tmp_path / "already.wav"
    w.write_bytes(b"")
    kind, target = audio_source_for(w)
    assert kind == "file"
    assert Path(target) == w


def test_a_directory_is_a_session_and_is_passed_through(tmp_path):
    kind, target = audio_source_for(tmp_path)
    assert kind == "session"
    assert Path(target) == tmp_path


def test_two_containers_with_one_stem_get_different_extractions(tmp_path):
    """The collision that can actually happen, and the one my first test missed.

    `clip.mov` and `clip.mp4` beside each other are two recordings. Naming the extraction
    by swapping the suffix gives both of them `clip.wav`, so the second run silently
    analyses the first one's audio. Written first as "the target differs from the source",
    which every naming scheme satisfies, with an `or True` in it that could never fail.
    """
    a = tmp_path / "clip.mov"
    b = tmp_path / "clip.mp4"
    a.write_bytes(b"")
    b.write_bytes(b"")
    _, ta = audio_source_for(a)
    _, tb = audio_source_for(b)
    assert Path(ta) != Path(tb)
    assert Path(ta) != a and Path(tb) != b


def test_an_explicit_audio_path_wins(tmp_path):
    """The caller may already have the audio, and re-extracting it is waste."""
    v = tmp_path / "session.mp4"
    v.write_bytes(b"")
    mine = tmp_path / "mine.wav"
    mine.write_bytes(b"")
    kind, target = audio_source_for(v, audio=mine)
    assert kind == "file"
    assert Path(target) == mine


def test_a_missing_path_is_an_error_not_a_guess(tmp_path):
    with pytest.raises(FileNotFoundError):
        audio_source_for(tmp_path / "nothing_here.mp4")


def test_an_unknown_extension_is_refused_rather_than_assumed_to_be_video(tmp_path):
    """Handing ffmpeg a .docx and letting it fail is a worse error message than this."""
    p = tmp_path / "notes.docx"
    p.write_bytes(b"")
    with pytest.raises(ValueError):
        audio_source_for(p)

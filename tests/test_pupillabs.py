"""Pupil Labs Neon export: reading, alignment to a video's clock, frame table, events, rates, gazegram."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from musicalgestures._pupillabs import (
    DEFAULT_SCENE_SIZE, EyeEvent, eye_events, eyetracking_rates, gazegram, pupil_to_frames, read_pupil_export,
)

START = 1_700_000_000_000_000_000  # ns
REC_S = 20.0
FPS = 25.0


@pytest.fixture
def export(tmp_path):
    """A 20 s synthetic export: gaze sweeping left to right, one blink, two fixations, one saccade."""
    t = np.arange(0, REC_S, 0.005)  # 200 Hz
    ns = (START + (t * 1e9).astype(np.int64)).astype(np.int64)
    x = 100 + 1400 * t / REC_S  # sweeps across the 1600 px scene
    y = np.full_like(t, 600.0)
    az = -30 + 60 * t / REC_S
    el = np.zeros_like(t)
    blink = (t >= 7.0) & (t < 7.3)
    fix1 = (t >= 2.0) & (t < 2.5)
    fix2 = (t >= 12.0) & (t < 13.0)
    sac = (t >= 2.5) & (t < 2.55)
    gaze = pd.DataFrame({
        "section id": "s", "recording id": "r", "timestamp [ns]": ns,
        "gaze x [px]": x, "gaze y [px]": y, "worn": 1.0,
        "fixation id": np.where(fix1, 1, np.where(fix2, 2, np.nan)),
        "blink id": np.where(blink, 1, np.nan), "azimuth [deg]": az, "elevation [deg]": el,
    })
    gaze.to_csv(tmp_path / "gaze.csv", index=False)
    eye = pd.DataFrame({"section id": "s", "recording id": "r", "timestamp [ns]": ns,
                        "pupil diameter left [mm]": np.where(blink, 0.5, 3.0),
                        "pupil diameter right [mm]": np.where(blink, 0.5, 3.2)})
    eye.to_csv(tmp_path / "3d_eye_states.csv", index=False)
    ti = np.arange(0, REC_S, 0.01)
    imu = pd.DataFrame({"section id": "s", "recording id": "r", "timestamp [ns]": (START + (ti * 1e9).astype(np.int64)),
                        "gyro x [deg/s]": np.where(ti > 15, 30.0, 0.0), "gyro y [deg/s]": 0.0, "gyro z [deg/s]": np.where(ti > 15, 40.0, 0.0),
                        "acceleration x [g]": 0.0, "acceleration y [g]": -1.0, "acceleration z [g]": 0.0,
                        "roll [deg]": 0.0, "pitch [deg]": -10.0, "yaw [deg]": 90.0})
    imu.to_csv(tmp_path / "imu.csv", index=False)

    def spans(name, rows):
        pd.DataFrame(rows).to_csv(tmp_path / f"{name}.csv", index=False)

    spans("fixations", [{"section id": "s", "recording id": "r", "fixation id": 1, "start timestamp [ns]": START + int(2.0e9), "end timestamp [ns]": START + int(2.5e9), "duration [ms]": 500, "fixation x [px]": 240.0, "fixation y [px]": 600.0},
                        {"section id": "s", "recording id": "r", "fixation id": 2, "start timestamp [ns]": START + int(12.0e9), "end timestamp [ns]": START + int(13.0e9), "duration [ms]": 1000, "fixation x [px]": 940.0, "fixation y [px]": 600.0}])
    spans("saccades", [{"section id": "s", "recording id": "r", "saccade id": 1, "start timestamp [ns]": START + int(2.5e9), "end timestamp [ns]": START + int(2.55e9), "duration [ms]": 50, "amplitude [px]": 30.0, "amplitude [deg]": 2.0, "mean velocity [px/s]": 600.0, "peak velocity [px/s]": 900.0}])
    spans("blinks", [{"section id": "s", "recording id": "r", "blink id": 1, "start timestamp [ns]": START + int(7.0e9), "end timestamp [ns]": START + int(7.3e9), "duration [ms]": 300}])
    pd.DataFrame([{"recording id": "r", "timestamp [ns]": START, "name": "recording.begin", "type": "recording"},
                  {"recording id": "r", "timestamp [ns]": START + int(5.0e9), "name": "Music begins", "type": "cloud"},
                  {"recording id": "r", "timestamp [ns]": START + int(REC_S * 1e9), "name": "recording.end", "type": "recording"}]).to_csv(tmp_path / "events.csv", index=False)
    json.dump({"start_time": START, "duration": int(REC_S * 1e9), "wearer_name": "Test", "gaze_frequency": 200}, open(tmp_path / "info.json", "w"))
    return tmp_path


def test_read_export_tables_and_events(export):
    rec = read_pupil_export(export)
    assert rec.start_ns == START and rec.duration_s == REC_S and rec.wearer == "Test"
    assert rec.events["Music begins"] == 5.0 and rec.events["recording.begin"] == 0.0
    assert rec.scene_size == DEFAULT_SCENE_SIZE
    assert rec.gaze is not None and abs(rec.gaze.t.iloc[-1] - (REC_S - 0.005)) < 1e-6
    assert rec.fixations is not None and rec.fixations.t0.tolist() == [2.0, 12.0]


def test_read_export_requires_info(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_pupil_export(tmp_path)


def test_partial_export_is_still_read(tmp_path):
    json.dump({"start_time": START, "duration": int(1e9)}, open(tmp_path / "info.json", "w"))
    rec = read_pupil_export(tmp_path)
    assert rec.gaze is None and rec.imu is None and rec.events == {}
    frames = pupil_to_frames(rec, FPS)
    assert list(frames.columns) == ["frame", "time"] and len(frames) == 25


def test_offset_by_event_name_and_unknown_name(export):
    rec = read_pupil_export(export)
    assert rec.offset_of("Music begins") == 5.0 and rec.offset_of(3.25) == 3.25
    with pytest.raises(KeyError):
        rec.offset_of("Music starts")


def test_frames_aligned_to_event(export):
    rec = read_pupil_export(export)
    frames = pupil_to_frames(rec, FPS, start="Music begins", duration_s=10.0)
    assert len(frames) == 250
    # the video's first frame is at recording second 5, where the sweep is at 100 + 1400 * 5/20 = 450 px
    assert abs(frames.gaze_x.iloc[0] - 450) < 5
    # a frame per 0.04 s holds 8 gaze samples; velocity of the sweep is 3 deg/s
    assert abs(np.nanmedian(frames.gaze_vel) - 3.0) < 0.2
    # fixation 2 (recording 12-13 s) is at video 7-8 s
    on = frames[frames.fixation == 1]
    assert abs(on.time.min() - 7.0) < 0.05 and abs(on.time.max() - 8.0) < 0.05 and set(on.fixation_id) == {2}


def test_blink_masks_gaze_and_pupil(export):
    rec = read_pupil_export(export)
    frames = pupil_to_frames(rec, FPS, start=0.0, blink_pad_frames=2)
    inblink = frames[(frames.time >= 7.0) & (frames.time + 1 / FPS <= 7.3)]  # frames wholly inside the blink
    assert (inblink.blink == 1).all() and inblink.gaze_x.isna().all() and inblink.gaze_vel.isna().all()
    # the 0.5 mm blink values never reach the pupil series: masked and interpolated from the 3.0/3.2 neighbours
    assert frames.pupil_left.min() > 2.9 and abs(frames.pupil_mean.iloc[100] - 3.1) < 1e-6
    assert frames.pupil_mean.notna().all()


def test_head_imu_per_frame(export):
    rec = read_pupil_export(export)
    frames = pupil_to_frames(rec, FPS)
    assert abs(frames.head_gyro[frames.time < 15].max()) < 1e-6
    assert abs(frames.head_gyro[frames.time > 15.5].median() - 50.0) < 1e-6  # sqrt(30^2 + 40^2)
    assert abs(frames.head_acc.median()) < 1e-6 and frames.head_yaw.median() == 90.0


def test_events_on_video_clock_and_clipping(export):
    rec = read_pupil_export(export)
    fx = eye_events(rec, "fixation", start="Music begins", duration_s=10.0)
    assert [e.id for e in fx] == [2] and fx[0].start == 7.0 and fx[0].end == 8.0 and fx[0].features["duration [ms]"] == 1000.0
    # a video ending mid-fixation keeps the clipped part
    fx = eye_events(rec, "fixation", start=0.0, duration_s=12.5)
    assert fx[-1].id == 2 and fx[-1].end == 12.5
    assert eye_events(rec, "blink", start=10.0) == []
    assert isinstance(fx[0], EyeEvent) and fx[0].duration == 0.5


def test_rates_count_onsets_once(export):
    rec = read_pupil_export(export)
    frames = pupil_to_frames(rec, FPS)
    rates = eyetracking_rates(frames, FPS, bin_s=1.0)
    assert rates.loc[2.0, "fixation_rate"] == 1.0 and rates.loc[12.0, "fixation_rate"] == 1.0
    assert rates.fixation_rate.sum() == 2.0 and rates.blink_rate.sum() == 1.0 and rates.saccade_rate.sum() == 1.0
    assert rates.loc[7.0, "blink_rate"] == 1.0
    # a 70 px/s linear sweep within a 1 s bin: std of |x - mean| around 10 px
    assert 5 < rates.gaze_dispersion.dropna().median() < 15


def test_gazegram_shape_and_position(export):
    rec = read_pupil_export(export)
    frames = pupil_to_frames(rec, FPS)
    gx = gazegram(frames, "x", bins=16, bin_s=1.0)
    assert gx.shape == (16, 20)
    # the sweep moves from row 1 (100 px) to row 15 (1500 px) across the 20 bins
    assert gx[:, 0].argmax() == 1 and gx[:, -1].argmax() >= 14
    assert np.allclose(gx.max(axis=0), 1.0)
    gy = gazegram(frames, "y", bins=12)
    assert gy.shape[0] == 12 and (gy.argmax(axis=0) == 6).all()  # y = 600 of 1200 -> middle row
    with pytest.raises(KeyError):
        gazegram(frames.drop(columns=["gaze_x"]), "x")


def test_mgvideo_wrappers(export, tmp_path_factory):
    """The bound methods resolve output names beside the video and keep results on it."""
    import os
    import musicalgestures
    from musicalgestures._utils import extract_subclip
    target = os.path.join(str(tmp_path_factory.mktemp("clip")), "clip.avi")
    clip = extract_subclip(musicalgestures.examples.dance, 5, 7, target_name=target)
    v = musicalgestures.MgVideo(clip)
    frames = v.eyetracking(export, start="Music begins")
    assert len(frames) == v.length and os.path.exists(v.of + "_eyetracking.csv")
    grams = v.gazegrams()
    assert os.path.exists(v.of + "_ggx.png") and os.path.exists(v.of + "_ggy.png") and len(grams) == 2
    fig = v.eyetracking_timeline()
    assert os.path.exists(v.of + "_eyetracking.png") and "rates" in fig.data

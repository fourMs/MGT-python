"""Read Pupil Labs Neon exports and put gaze, pupil and head motion on the video's clock.

Neon glasses record a scene camera, an eye camera, gaze at 200 Hz, pupil size, blinks,
fixations, saccades and an inertial unit, and Pupil Cloud exports all of it as CSV files
with one column of absolute UTC nanosecond timestamps. None of that is on the clock of any
video the toolbox will analyse: the scene video starts a little after the recording (its
first frame carries its own timestamp), a cut made for analysis starts later still, and
the eye data run at their own rates. This module does the alignment once, so that gaze
velocity, pupil diameter, blink rate and head rotation can sit in the same frame-indexed
table as quantity of motion and be correlated, segmented and drawn with the same tools.

**The clock is the important thing.** Every Cloud export carries `info.json` with the
recording's `start_time` in nanoseconds; `events.csv` names moments on that clock
(`recording.begin`, and whatever the wearer's companion marked --- "Music begins"); and
the scene camera's frame times are in `world_timestamps.csv`. A video cut from the scene
recording is placed on the recording clock by naming the event it starts at, or by giving
its offset in seconds. Times in the exported frame table then count from the video's own
first frame, which is what every other MGT result does.

Two things the data do not say, and this module does not pretend they do:

- Gaze during a blink is the tracker's guess, so gaze position and velocity are set to
  missing for frames inside a blink, and pupil diameter is masked a few frames either
  side (the lids occlude the pupil before the detector reports a blink) and interpolated.
- The Cloud face detector reports faces in the scene image. On abstract painting it
  fired on the painting more often than on people (see the 2024 live-painting analysis
  this was written for), so face detections are read but not interpreted here; deciding
  what a face box means is the caller's job.

What is computed per frame: gaze position (scene pixels, and azimuth/elevation in
degrees), gaze angular velocity in degrees per second from consecutive 200 Hz samples on
the sphere, `worn`, fixation/saccade/blink flags with the export's ids, pupil diameter left,
right and mean, head gyroscope magnitude (deg/s), dynamic acceleration (|a| - 1 g, in g)
and roll/pitch/yaw. Per-second rates (fixations, saccades and blinks per second, mean
fixation duration, mean saccade amplitude, gaze dispersion) come from
:func:`eyetracking_rates`. A *gazegram* --- a histogram of gaze position per time bin,
drawn as an image with time across --- is the gaze counterpart of a motiongram, and lines
up with one when both are drawn on the same width.

Only `pandas` and `numpy` are needed; both are already hard dependencies.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from musicalgestures._mglist import MgList
from musicalgestures._utils import MgFigure, MgImage, resolve_filename

__all__ = [
    "PupilRecording",
    "EyeEvent",
    "read_pupil_export",
    "pupil_to_frames",
    "eye_events",
    "eyetracking_rates",
    "gazegram",
]

#: Columns read from gaze.csv. Cloud exports name them with units in brackets.
_GAZE_COLS = ["timestamp [ns]", "gaze x [px]", "gaze y [px]", "worn", "fixation id",
              "blink id", "azimuth [deg]", "elevation [deg]"]
_EYE_COLS = ["timestamp [ns]", "pupil diameter left [mm]", "pupil diameter right [mm]"]
_IMU_COLS = ["timestamp [ns]", "gyro x [deg/s]", "gyro y [deg/s]", "gyro z [deg/s]",
             "acceleration x [g]", "acceleration y [g]", "acceleration z [g]",
             "roll [deg]", "pitch [deg]", "yaw [deg]"]

#: Neon's scene camera resolution, used when the export has no scene_camera.json.
DEFAULT_SCENE_SIZE = (1600, 1200)


@dataclass
class EyeEvent:
    """One fixation, saccade or blink, in seconds on the video's clock.

    Attributes:
        kind (str): ``"fixation"``, ``"saccade"`` or ``"blink"``.
        start (float): Start, in seconds from the video's first frame.
        end (float): End, in seconds.
        id (int): The export's own id, so an event can be traced back to the CSV.
        features (dict): What the export said about it: duration in ms, position for a
            fixation, amplitude and velocities for a saccade.
    """
    kind: str
    start: float
    end: float
    id: int = -1
    features: dict = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class PupilRecording:
    """A Pupil Cloud export, read but not yet aligned to any video.

    Attributes:
        folder (Path): Where it was read from.
        start_ns (int): Recording start on the absolute nanosecond clock, from info.json.
        duration_s (float): Recording length in seconds, from info.json.
        events (dict): Event name to seconds after `start_ns`, from events.csv. Names are
            not unique in principle; the first occurrence wins and all are kept in
            `events_all`.
        events_all (pandas.DataFrame): Every row of events.csv, with a `t` column in
            seconds after `start_ns`.
        scene_size (tuple): Scene camera (width, height) in pixels.
        gaze, eye_states, imu, fixations, saccades, blinks, world_timestamps
            (pandas.DataFrame or None): The tables, each with a `t` column in seconds
            after `start_ns`. Missing files give None rather than an error, because a
            partial export (gaze only, no IMU) is still worth aligning.
        wearer (str): The wearer's name from info.json, if any.
    """
    folder: Path
    start_ns: int
    duration_s: float
    events: dict
    events_all: pd.DataFrame
    scene_size: tuple
    gaze: pd.DataFrame | None = None
    eye_states: pd.DataFrame | None = None
    imu: pd.DataFrame | None = None
    fixations: pd.DataFrame | None = None
    saccades: pd.DataFrame | None = None
    blinks: pd.DataFrame | None = None
    world_timestamps: pd.DataFrame | None = None
    wearer: str = ""

    def offset_of(self, start) -> float:
        """Seconds after the recording start at which a video begins.

        Args:
            start (str | float): An event name from events.csv, or seconds.

        Returns:
            float: The offset in seconds.

        Raises:
            KeyError: when `start` is a name the export does not contain --- listing the
                names it does, since a typo in "Music begins" should not silently
                become an offset of zero.
        """
        if isinstance(start, str):
            if start not in self.events:
                raise KeyError(f"no event {start!r} in events.csv; the export has "
                               f"{sorted(self.events)}")
            return float(self.events[start])
        return float(start)


def _read(folder: Path, name: str, usecols=None) -> pd.DataFrame | None:
    p = folder / name
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p, usecols=usecols)
    except ValueError:
        df = pd.read_csv(p)  # an older export without some optional column
    return df


def _seconds(df: pd.DataFrame | None, start_ns: int, col: str = "timestamp [ns]",
             out: str = "t") -> pd.DataFrame | None:
    """Add a column of seconds after `start_ns` to a table with nanosecond stamps."""
    if df is None or col not in df:
        return df
    df[out] = (df[col].astype(np.int64) - np.int64(start_ns)) / 1e9
    return df


def read_pupil_export(folder) -> PupilRecording:
    """Read a Pupil Cloud "Timeseries Data" export folder.

    Args:
        folder (str | Path): The folder holding info.json, events.csv, gaze.csv and the
            other tables. Only info.json is required.

    Returns:
        PupilRecording: The tables with seconds-after-start columns added.

    Raises:
        FileNotFoundError: when the folder has no info.json, because without the start
            time nothing can be placed on a clock.
    """
    folder = Path(folder)
    info_p = folder / "info.json"
    if not info_p.exists():
        raise FileNotFoundError(f"{folder} has no info.json; is this a Pupil Cloud export?")
    info = json.load(open(info_p))
    start_ns = int(info["start_time"])
    duration_s = float(info.get("duration", 0)) / 1e9
    events: dict = {}
    events_all = _read(folder, "events.csv")
    if events_all is None:
        events_all = pd.DataFrame(columns=["name", "t"])
    else:
        events_all["t"] = (events_all["timestamp [ns]"].astype(np.int64) - np.int64(start_ns)) / 1e9
        for _, r in events_all.iterrows():
            events.setdefault(str(r["name"]), float(r["t"]))
    scene_size: tuple[int, int] = DEFAULT_SCENE_SIZE
    cam_p = folder / "scene_camera.json"
    if cam_p.exists():
        cam = json.load(open(cam_p))
        K = np.asarray(cam.get("camera_matrix", []), dtype=float)
        if K.shape == (3, 3) and abs(2 * K[0, 2] - DEFAULT_SCENE_SIZE[0]) < 100:
            # principal point sits near the image centre; the resolution itself is not
            # in the file, so keep the default unless the export says otherwise
            scene_size = (int(round(2 * K[0, 2])), int(round(2 * K[1, 2])))
    rec = PupilRecording(folder=folder, start_ns=start_ns, duration_s=duration_s, events=events,
                         events_all=events_all, scene_size=scene_size,
                         wearer=str(info.get("wearer_name", "")))
    rec.gaze = _seconds(_read(folder, "gaze.csv", _GAZE_COLS), start_ns)
    rec.eye_states = _seconds(_read(folder, "3d_eye_states.csv", _EYE_COLS), start_ns)
    rec.imu = _seconds(_read(folder, "imu.csv", _IMU_COLS), start_ns)
    rec.world_timestamps = _seconds(_read(folder, "world_timestamps.csv"), start_ns)
    for name in ("fixations", "saccades", "blinks"):
        df = _read(folder, f"{name}.csv")
        if df is not None:
            df = _seconds(df, start_ns, "start timestamp [ns]", "t0")
            df = _seconds(df, start_ns, "end timestamp [ns]", "t1")
        setattr(rec, name, df)
    return rec


def _angular_velocity(az_deg: np.ndarray, el_deg: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Great-circle speed between consecutive gaze samples, deg/s; NaN where undefined."""
    az, el = np.deg2rad(az_deg), np.deg2rad(el_deg)
    dt = np.diff(t)
    dt = np.where(dt > 0, dt, np.nan)
    cosang = (np.sin(el[:-1]) * np.sin(el[1:])
              + np.cos(el[:-1]) * np.cos(el[1:]) * np.cos(az[1:] - az[:-1]))
    ang = np.arccos(np.clip(cosang, -1.0, 1.0))
    vel: np.ndarray = np.asarray(np.r_[np.nan, np.rad2deg(ang) / dt], dtype=float)
    return vel


def _flag(n: int, fps: float, spans: pd.DataFrame | None, id_col: str | None,
          duration_s: float) -> tuple[np.ndarray, np.ndarray]:
    """Frame flags (0/1) and ids (-1 where none) for spans with t0/t1 in video seconds."""
    flag: np.ndarray = np.zeros(n, dtype=np.int8)
    ids: np.ndarray = np.full(n, -1, dtype=np.int64)
    if spans is None or len(spans) == 0:
        return flag, ids
    t0s = spans["t0"].values.astype(float)
    t1s = spans["t1"].values.astype(float)
    idv = spans[id_col].values if id_col is not None else None
    for k in range(len(spans)):
        t0, t1 = t0s[k], t1s[k]
        if t1 < 0 or t0 > duration_s:
            continue
        a = int(np.clip(np.floor(max(t0, 0.0) * fps), 0, n - 1))
        b = int(np.clip(np.floor(min(t1, duration_s) * fps), 0, n - 1))
        flag[a:b + 1] = 1
        if idv is not None:
            ids[a:b + 1] = int(idv[k])
    return flag, ids


def _shift_spans(df: pd.DataFrame | None, offset: float) -> pd.DataFrame | None:
    if df is None:
        return None
    out = df.copy()
    out["t0"] = out["t0"] - offset
    out["t1"] = out["t1"] - offset
    return out


def pupil_to_frames(rec: PupilRecording, fps: float, start=0.0,
                    duration_s: float | None = None,
                    blink_pad_frames: int = 3) -> pd.DataFrame:
    """Resample a recording onto the frames of a video that starts at `start`.

    Each 200 Hz stream is binned to frames (median for positions and pupil size, mean for
    velocities and IMU magnitudes), event spans become per-frame flags, and pupil size is
    masked around blinks and interpolated. Frames with no sample keep NaN, which is the
    honest value for a gap: interpolating gaze across a dropped second would invent a
    fixation nobody made.

    Args:
        rec (PupilRecording): As returned by :func:`read_pupil_export`.
        fps (float): The video's frame rate.
        start (str | float): Where the video begins on the recording clock, as an event
            name from events.csv or as seconds after the recording start. Defaults to
            0.0, the recording start.
        duration_s (float, optional): Length of the video. Defaults to the rest of the
            recording.
        blink_pad_frames (int): Frames masked either side of a blink before the pupil
            series is interpolated. Defaults to 3.

    Returns:
        pandas.DataFrame: One row per frame with `frame`, `time` (s from the video's first
        frame), `gaze_x`, `gaze_y` (scene px), `gaze_az`, `gaze_el` (deg), `gaze_vel`
        (deg/s), `worn`, `fixation`, `fixation_id`, `saccade`, `saccade_id`, `blink`,
        `blink_id`, `pupil_left`, `pupil_right`, `pupil_mean` (mm), `head_gyro` (deg/s),
        `head_acc` (g, dynamic), `head_roll`, `head_pitch`, `head_yaw` (deg). Columns whose
        source table is missing from the export are absent, not zero.
    """
    offset = rec.offset_of(start)
    if duration_s is None:
        duration_s = max(rec.duration_s - offset, 0.0)
    n = int(np.floor(duration_s * fps))
    if n <= 0:
        raise ValueError("the video would hold no frames: check `start` and `duration_s`")
    frames = np.arange(n)
    out = pd.DataFrame({"frame": frames, "time": frames / fps})

    def frame_of(t):
        return np.clip(np.floor(np.asarray(t, dtype=float) * fps).astype(int), 0, n - 1)

    if rec.gaze is not None:
        g = rec.gaze.copy()
        g["tv"] = g["t"] - offset
        g = g[(g.tv >= 0) & (g.tv < duration_s)]
        if len(g):
            g = g.sort_values("tv")
            g["vel"] = _angular_velocity(g["azimuth [deg]"].values, g["elevation [deg]"].values,
                                         g["tv"].values)
            if "blink id" in g:
                inblink = g["blink id"].notna()
                g.loc[inblink, ["gaze x [px]", "gaze y [px]", "vel"]] = np.nan
            g["f"] = frame_of(g.tv)
            agg = g.groupby("f").agg(gaze_x=("gaze x [px]", "median"), gaze_y=("gaze y [px]", "median"),
                                     gaze_az=("azimuth [deg]", "median"), gaze_el=("elevation [deg]", "median"),
                                     gaze_vel=("vel", "mean"), worn=("worn", "max"))
            out = out.join(agg, on="frame")
    if rec.eye_states is not None:
        e = rec.eye_states.copy()
        e["tv"] = e["t"] - offset
        e = e[(e.tv >= 0) & (e.tv < duration_s)]
        if len(e):
            e["f"] = frame_of(e.tv)
            agg = e.groupby("f").agg(pupil_left=("pupil diameter left [mm]", "median"),
                                     pupil_right=("pupil diameter right [mm]", "median"))
            out = out.join(agg, on="frame")
            out["pupil_mean"] = out[["pupil_left", "pupil_right"]].mean(axis=1)
    for name, id_name in (("fixations", "fixation id"), ("saccades", "saccade id"), ("blinks", "blink id")):
        spans = _shift_spans(getattr(rec, name), offset)
        key = name[:-1]
        id_col: str | None = id_name
        if spans is not None and id_name not in spans:
            id_col = None
        flag, ids = _flag(n, fps, spans, id_col, duration_s)
        if spans is not None:
            out[key] = flag
            out[f"{key}_id"] = ids
    if "blink" in out and "pupil_mean" in out:
        m = out["blink"].values.astype(bool)
        if blink_pad_frames > 0:
            k = np.ones(2 * blink_pad_frames + 1)
            m = np.convolve(m.astype(float), k, "same") > 0
        for c in ("pupil_left", "pupil_right", "pupil_mean"):
            s = out[c].copy()
            s[m] = np.nan
            out[c] = s.interpolate(limit_direction="both")
    if rec.imu is not None:
        im = rec.imu.copy()
        im["tv"] = im["t"] - offset
        im = im[(im.tv >= 0) & (im.tv < duration_s)]
        if len(im):
            im["f"] = frame_of(im.tv)
            im["gyro_mag"] = np.sqrt(im["gyro x [deg/s]"] ** 2 + im["gyro y [deg/s]"] ** 2 + im["gyro z [deg/s]"] ** 2)
            acc = np.sqrt(im["acceleration x [g]"] ** 2 + im["acceleration y [g]"] ** 2 + im["acceleration z [g]"] ** 2)
            im["acc_dyn"] = (acc - 1.0).abs()
            agg = im.groupby("f").agg(head_gyro=("gyro_mag", "mean"), head_acc=("acc_dyn", "mean"),
                                      head_roll=("roll [deg]", "median"), head_pitch=("pitch [deg]", "median"),
                                      head_yaw=("yaw [deg]", "median"))
            out = out.join(agg, on="frame")
    return out


def eye_events(rec: PupilRecording, kind: str, start=0.0,
               duration_s: float | None = None) -> list[EyeEvent]:
    """The fixations, saccades or blinks that fall inside a video, on its clock.

    Args:
        rec (PupilRecording): The export.
        kind (str): ``"fixation"``, ``"saccade"`` or ``"blink"``.
        start (str | float): Event name or seconds, as in :func:`pupil_to_frames`.
        duration_s (float, optional): Length of the video; defaults to the rest of the
            recording.

    Returns:
        list: :class:`EyeEvent` in order of start. Events straddling the video's edges
        are kept, clipped to the video, because a blink that began a frame before the
        cut still happened in it.
    """
    table = {"fixation": rec.fixations, "saccade": rec.saccades, "blink": rec.blinks}[kind]
    if table is None:
        return []
    offset = rec.offset_of(start)
    if duration_s is None:
        duration_s = max(rec.duration_s - offset, 0.0)
    id_col = f"{kind} id"
    keep = [c for c in table.columns if c not in ("section id", "recording id", "start timestamp [ns]",
                                                 "end timestamp [ns]", "t0", "t1", id_col)]
    out = []
    for _, row in table.sort_values("t0").iterrows():
        t0, t1 = float(row["t0"]) - offset, float(row["t1"]) - offset
        if t1 < 0 or t0 > duration_s:
            continue
        feats = {}
        for c in keep:
            v = row[c]
            if isinstance(v, (int, float, np.floating, np.integer)):
                feats[c] = None if pd.isna(v) else float(v)
            else:
                feats[c] = v
        out.append(EyeEvent(kind=kind, start=max(t0, 0.0), end=min(t1, duration_s),
                            id=int(row[id_col]) if id_col in table else -1, features=feats))
    return out


def eyetracking_rates(frames: pd.DataFrame, fps: float, bin_s: float = 1.0) -> pd.DataFrame:
    """Per-bin rates and means from a frame table: events per second, pupil, gaze spread.

    Rates count event *onsets* (a fixation that spans two bins is counted once, where it
    began), which is what "fixations per second" means. Gaze dispersion is the standard
    deviation of the gaze position around the bin's mean, in scene pixels.

    Args:
        frames (pandas.DataFrame): From :func:`pupil_to_frames`.
        fps (float): The frame rate the table was made at.
        bin_s (float): Bin length in seconds. Defaults to 1.0.

    Returns:
        pandas.DataFrame: Indexed by bin start time, with whichever of `fixation_rate`,
        `saccade_rate`, `blink_rate`, `pupil_mean`, `gaze_vel`, `gaze_x`, `gaze_y`,
        `gaze_dispersion`, `head_gyro` the table supports.
    """
    b = (frames["time"].values // bin_s).astype(int)
    df = frames.assign(_bin=b)
    agg = {}
    for c in ("pupil_mean", "pupil_left", "pupil_right", "gaze_vel", "gaze_x", "gaze_y", "head_gyro",
              "head_acc", "head_yaw", "head_pitch", "worn"):
        if c in df:
            agg[c] = (c, "mean")
    out = df.groupby("_bin").agg(**agg) if agg else pd.DataFrame(index=np.unique(b))
    for key in ("fixation", "saccade", "blink"):
        idc = f"{key}_id"
        if idc in df:
            ids = df[idc].values
            onset = np.r_[ids[0] >= 0, (ids[1:] != ids[:-1]) & (ids[1:] >= 0)]
            out[f"{key}_rate"] = pd.Series(np.bincount(b[onset], minlength=b.max() + 1) / bin_s).reindex(out.index).fillna(0.0)
    if "gaze_x" in df and "gaze_y" in df:
        def disp(d):
            x, y = d["gaze_x"].values, d["gaze_y"].values
            if np.isnan(x).all():
                return np.nan
            return float(np.nanstd(np.hypot(x - np.nanmean(x), y - np.nanmean(y))))
        out["gaze_dispersion"] = df.groupby("_bin").apply(disp, include_groups=False)
    out.index = out.index * bin_s
    out.index.name = "time"
    return out


def gazegram(frames: pd.DataFrame, axis: str = "y", size: int | None = None,
             bin_s: float = 1.0, bins: int = 120, normalise: bool = True) -> np.ndarray:
    """Histogram of gaze position per time bin, as an image with time across.

    The gaze counterpart of a motiongram: where the motiongram's rows say where in the
    picture pixels changed, the gazegram's rows say where in the picture the wearer
    looked. Drawn at the same width the two line up.

    Args:
        frames (pandas.DataFrame): From :func:`pupil_to_frames`.
        axis (str): ``"x"`` (rows are horizontal scene position) or ``"y"`` (vertical).
            Defaults to ``"y"``.
        size (int, optional): Scene extent along that axis in pixels; defaults to Neon's
            1600 x 1200 scene camera.
        bin_s (float): Time bin in seconds. Defaults to 1.0.
        bins (int): Rows in the image. Defaults to 120.
        normalise (bool): Divide each column by its maximum, so a bin with few samples
            still shows where they were. Defaults to True.

    Returns:
        numpy.ndarray: `(bins, n_bins_time)` with row 0 at position 0 (top of the scene
        for ``"y"``, left for ``"x"``).
    """
    col = f"gaze_{axis}"
    if col not in frames:
        raise KeyError(f"frame table has no {col}; was gaze.csv in the export?")
    if size is None:
        size = DEFAULT_SCENE_SIZE[0] if axis == "x" else DEFAULT_SCENE_SIZE[1]
    v = frames[col].values
    tb = (frames["time"].values // bin_s).astype(int)
    img = np.zeros((bins, tb.max() + 1))
    ok = ~np.isnan(v)
    rows = np.clip((v[ok] / size * bins).astype(int), 0, bins - 1)
    np.add.at(img, (rows, tb[ok]), 1)
    if normalise:
        img = img / (img.max(axis=0, keepdims=True) + 1e-9)
    out: np.ndarray = np.asarray(img)
    return out


# ---------------------------------------------------------------------------------------
# MgVideo-bound wrappers
# ---------------------------------------------------------------------------------------

def mg_eyetracking(self, export_dir, start=0.0, blink_pad_frames: int = 3,
                   save_data: bool = True, target_name: str | None = None,
                   overwrite: bool = True) -> pd.DataFrame:
    """Align a Pupil Labs export to this video and keep the frame table on it.

    Args:
        export_dir (str | Path): The Pupil Cloud export folder.
        start (str | float): Where this video begins on the recording clock: an event
            name from events.csv (``"Music begins"``) or seconds after the recording
            start. Defaults to 0.0.
        blink_pad_frames (int): See :func:`pupil_to_frames`. Defaults to 3.
        save_data (bool): Write the table as CSV beside the video. Defaults to True.
        target_name (str, optional): Output path. Defaults to ``"_eyetracking.csv"``
            beside the video.
        overwrite (bool): Overwrite or auto-increment. Defaults to True.

    Returns:
        pandas.DataFrame: The frame table, also stored as `self.eyetracking`; the
        recording as `self.pupil_recording`.
    """
    rec = read_pupil_export(export_dir)
    frames = pupil_to_frames(rec, float(self.fps), start=start, duration_s=float(self.duration),
                             blink_pad_frames=blink_pad_frames)
    self.pupil_recording = rec
    self.eyetracking = frames
    if save_data:
        path = resolve_filename(self.of, "_eyetracking.csv", target_name, overwrite)
        frames.to_csv(path, index=False, float_format="%.4f")
        self.eyetracking_data = path
    return frames


def _require_frames(self) -> pd.DataFrame:
    frames = getattr(self, "eyetracking", None)
    if frames is None:
        raise ValueError("run eyetracking(export_dir, start=...) first, so the export is aligned to this video")
    return frames


def mg_gazegrams(self, bins: int = 120, bin_s: float = 1.0, colormap: str = "magma",
                 target_name_x: str | None = None, target_name_y: str | None = None,
                 overwrite: bool = True) -> MgList:
    """Write the horizontal and vertical gazegrams of an aligned export as images.

    Oriented like the motiongrams: the `_ggy` image has time across and vertical scene
    position down; the `_ggx` image has time down and horizontal position across.

    Args:
        bins (int): Position bins. Defaults to 120.
        bin_s (float): Time bin in seconds. Defaults to 1.0.
        colormap (str): Matplotlib colormap. Defaults to ``"magma"``.
        target_name_x (str, optional): Path for the horizontal-position gazegram.
        target_name_y (str, optional): Path for the vertical-position gazegram.
        overwrite (bool): Overwrite or auto-increment. Defaults to True.

    Returns:
        MgList: `MgImage` for the x and y gazegrams, also stored as `self.gazegram_x_image`
        and `self.gazegram_y_image`.
    """
    import matplotlib
    frames = _require_frames(self)
    rec = getattr(self, "pupil_recording", None)
    w, h = rec.scene_size if rec is not None else DEFAULT_SCENE_SIZE
    cmap = matplotlib.colormaps[colormap]
    gy = gazegram(frames, "y", h, bin_s, bins)
    gx = gazegram(frames, "x", w, bin_s, bins)
    py = resolve_filename(self.of, "_ggy.png", target_name_y, overwrite)
    px = resolve_filename(self.of, "_ggx.png", target_name_x, overwrite)
    matplotlib.image.imsave(py, gy, cmap=cmap)
    matplotlib.image.imsave(px, gx.T, cmap=cmap)
    self.gazegram_y_image = MgImage(py)
    self.gazegram_x_image = MgImage(px)
    return MgList(self.gazegram_x_image, self.gazegram_y_image)


def mg_eyetracking_timeline(self, bin_s: float = 1.0, dpi: int = 120, title: str | None = None,
                            target_name: str | None = None, overwrite: bool = True) -> MgFigure:
    """Draw gaze velocity, event rates, pupil size and head rotation over the video.

    Args:
        bin_s (float): Bin for the rates. Defaults to 1.0.
        dpi (int): Figure resolution. Defaults to 120.
        title (str, optional): Figure title. Defaults to the video's name.
        target_name (str, optional): Output path. Defaults to ``"_eyetracking.png"``.
        overwrite (bool): Overwrite or auto-increment. Defaults to True.

    Returns:
        MgFigure: With the per-bin table in `.data["rates"]`; also stored as
        `self.eyetracking_figure`.
    """
    import matplotlib.pyplot as plt
    frames = _require_frames(self)
    rates = eyetracking_rates(frames, float(self.fps), bin_s)
    panels = [c for c in ("gaze_vel", "fixation_rate", "blink_rate", "pupil_mean", "head_gyro") if c in rates]
    fig, axs = plt.subplots(len(panels), 1, figsize=(16, 1.8 * len(panels) + 1), sharex=True, squeeze=False, dpi=dpi)
    labels = {"gaze_vel": "gaze velocity (deg/s)", "fixation_rate": "fixations / s", "blink_rate": "blinks / s",
              "pupil_mean": "pupil (mm)", "head_gyro": "head rotation (deg/s)"}
    for ax, c in zip(axs[:, 0], panels):
        ax.plot(rates.index.values, rates[c].values, lw=0.7)
        ax.set_ylabel(labels[c], fontsize=8)
    axs[-1, 0].set_xlabel("time (s)")
    axs[0, 0].set_title(title or f"{os.path.basename(self.of)}: eye tracking and head motion")
    fig.tight_layout()
    path = resolve_filename(self.of, "_eyetracking.png", target_name, overwrite)
    fig.savefig(path)
    plt.close(fig)
    result = MgFigure(figure=fig, figure_type="video.eyetracking",
                      data={"rates": rates}, layers=None, image=path)
    self.eyetracking_figure = result
    return result

"""Tests for the TRC, C3D and FreeMoCap readers in musicalgestures._mocap.

Ground truth without vendor files: the TRC fixtures are written in-test from the
documented five-line header format, and the C3D files are written by ezc3d itself
(create, write, read back), so read_c3d is tested against the library's own output
rather than hand-crafted binary bytes. The FreeMoCap fixtures rebuild the recording
folder layout verified in the FreeMoCap source (output_data/*_body_3d_xyz.npy plus
the timestamp records under synchronized_videos/timestamps/). Tests feed reader
output through compare_modality_envelopes to hold the readers to the read_qtm_tsv
contract.
"""
import json

import numpy as np
import pytest

from musicalgestures import read_trc, read_c3d, read_freemocap, compare_modality_envelopes
from musicalgestures._posetools import MEDIAPIPE_LANDMARK_NAMES

try:
    import ezc3d
    HAVE_EZC3D = True
except ImportError:
    HAVE_EZC3D = False

needs_ezc3d = pytest.mark.skipif(not HAVE_EZC3D, reason="optional ezc3d package not installed")


def _trc_text(units="mm", scale=1.0):
    """A minimal TRC file per the documented format: 2 markers, 4 frames, 120 Hz.

    Frame 3 has a blank-cell gap for HAND; frame 4 an exact-zero triple for HEAD.
    """
    rows = [
        ["PathFileType", "4", "(X/Y/Z)", "trial.trc"],
        ["DataRate", "CameraRate", "NumFrames", "NumMarkers", "Units",
         "OrigDataRate", "OrigDataStartFrame", "OrigNumFrames"],
        ["120.0", "120.0", "4", "2", units, "120.0", "1", "4"],
        ["Frame#", "Time", "HEAD", "", "", "HAND", "", ""],
        ["", "", "X1", "Y1", "Z1", "X2", "Y2", "Z2"],
    ]

    def n(v):
        return f"{v * scale:.6f}"

    rows += [
        ["1", "0.000000", n(1.0), n(2.0), n(3.0), n(10.0), n(11.0), n(12.0)],
        ["2", "0.008333", n(1.1), n(2.1), n(3.1), n(10.1), n(11.1), n(12.1)],
        ["3", "0.016667", n(1.2), n(2.2), n(3.2), "", "", ""],
        ["4", "0.025000", "0", "0", "0", n(10.3), n(11.3), n(12.3)],
    ]
    return "\n".join("\t".join(r) for r in rows) + "\n"


class TestReadTrc:
    def test_parses_fixture(self, tmp_path):
        p = tmp_path / "trial.trc"
        p.write_text(_trc_text())
        names, data, fs = read_trc(str(p))
        assert names == ["HEAD", "HAND"]
        assert fs == 120.0
        assert data.shape == (4, 2, 3)
        assert np.allclose(data[0, 0], [1.0, 2.0, 3.0])
        assert np.allclose(data[0, 1], [10.0, 11.0, 12.0])
        assert np.allclose(data[1, 0], [1.1, 2.1, 3.1])

    def test_blank_cells_become_nan(self, tmp_path):
        p = tmp_path / "trial.trc"
        p.write_text(_trc_text())
        _, data, _ = read_trc(str(p))
        # frame 3, HAND marker was blank cells -> NaN; HEAD intact
        assert np.all(np.isnan(data[2, 1]))
        assert np.allclose(data[2, 0], [1.2, 2.2, 3.2])

    def test_zero_triples_become_nan(self, tmp_path):
        p = tmp_path / "trial.trc"
        p.write_text(_trc_text())
        _, data, _ = read_trc(str(p))
        # frame 4, HEAD marker was an exact-zero triple -> NaN; HAND intact
        assert np.all(np.isnan(data[3, 0]))
        assert np.allclose(data[3, 1], [10.3, 11.3, 12.3])

    def test_metres_convert_to_millimetres(self, tmp_path):
        p = tmp_path / "metres.trc"
        # the same trajectories expressed in metres must come back in millimetres
        p.write_text(_trc_text(units="m", scale=0.001))
        names, data, fs = read_trc(str(p))
        assert names == ["HEAD", "HAND"]
        assert np.allclose(data[0, 0], [1.0, 2.0, 3.0])
        assert np.allclose(data[1, 1], [10.1, 11.1, 12.1])

    def test_no_data_raises(self, tmp_path):
        p = tmp_path / "empty.trc"
        p.write_text("PathFileType\t4\t(X/Y/Z)\tempty.trc\n")
        with pytest.raises(ValueError):
            read_trc(str(p))


def _write_c3d(path, points, labels, rate, units=None, residuals=None):
    """Write a C3D file through ezc3d's own API. points is (F, M, 3)."""
    c = ezc3d.c3d()
    F, M, _ = points.shape
    c["parameters"]["POINT"]["RATE"]["value"] = [float(rate)]
    c["parameters"]["POINT"]["LABELS"]["value"] = list(labels)
    if units is not None:
        c.add_parameter("POINT", "UNITS", [units])
    pts = np.ones((4, M, F))
    pts[:3] = points.transpose(2, 1, 0)
    c["data"]["points"] = pts
    if residuals is not None:
        c["data"]["meta_points"] = {
            "residuals": residuals.reshape(1, M, F),
            "camera_masks": np.zeros((7, M, F), dtype=bool),
        }
    c.write(str(path))


@needs_ezc3d
class TestReadC3d:
    def test_round_trip(self, tmp_path):
        rng = np.random.default_rng(0)
        points = rng.normal(scale=500.0, size=(10, 3, 3))
        p = tmp_path / "trial.c3d"
        _write_c3d(p, points, ["HEAD", "HAND", "FOOT"], rate=200.0, units="mm")
        names, data, fs = read_c3d(str(p))
        assert names == ["HEAD", "HAND", "FOOT"]
        assert fs == 200.0
        assert data.shape == (10, 3, 3)
        assert np.allclose(data, points, atol=1e-3)

    def test_nan_points_stay_nan(self, tmp_path):
        points = np.ones((5, 2, 3))
        points[2, 0] = np.nan  # first marker missing at frame 2
        p = tmp_path / "gaps.c3d"
        _write_c3d(p, points, ["A", "B"], rate=100.0, units="mm")
        _, data, _ = read_c3d(str(p))
        assert np.all(np.isnan(data[2, 0]))
        assert np.allclose(data[2, 1], [1.0, 1.0, 1.0])

    def test_negative_residual_becomes_nan(self, tmp_path):
        points = np.ones((4, 1, 3))
        residuals = np.zeros((1, 4))  # (M, F)
        residuals[0, 1] = -1.0  # frame 1 flagged invalid the C3D way
        p = tmp_path / "residual.c3d"
        _write_c3d(p, points, ["A"], rate=100.0, units="mm",
                   residuals=residuals)
        _, data, _ = read_c3d(str(p))
        assert np.all(np.isnan(data[1, 0]))
        assert np.allclose(data[0, 0], [1.0, 1.0, 1.0])

    def test_metres_convert_to_millimetres(self, tmp_path):
        points = np.full((3, 1, 3), 0.5)  # half a metre on every axis
        p = tmp_path / "metres.c3d"
        _write_c3d(p, points, ["A"], rate=100.0, units="m")
        _, data, _ = read_c3d(str(p))
        assert np.allclose(data, 500.0, atol=1e-3)

    def test_no_units_parameter_passes_through(self, tmp_path):
        points = np.full((3, 1, 3), 7.0)
        p = tmp_path / "nounits.c3d"
        _write_c3d(p, points, ["A"], rate=100.0, units=None)
        _, data, _ = read_c3d(str(p))
        assert np.allclose(data, 7.0, atol=1e-3)


def _freemocap_recording(root, data, detector="mediapipe", fs=None, fs_source="stats_json"):
    """Build a synthetic FreeMoCap recording folder in the verified v1 layout.

    data is (F, M, 3) and lands in output_data/{detector}_body_3d_xyz.npy. fs, when
    given, is recorded under synchronized_videos/timestamps/ either as skellycam's
    *_stats.json (framerate_stats.median), as the per-frame
    from_previous.framerate.hz column of a *timestamps.csv, or as per-camera
    nanosecond-timestamp .npy arrays.
    """
    recording = root / "session"
    output_data = recording / "output_data"
    output_data.mkdir(parents=True)
    np.save(str(output_data / f"{detector}_body_3d_xyz.npy"), data)

    if fs is not None:
        timestamps = recording / "synchronized_videos" / "timestamps"
        timestamps.mkdir(parents=True)
        if fs_source == "stats_json":
            (timestamps / "Camera_000_stats.json").write_text(
                json.dumps({"framerate_stats": {"median": fs}})
            )
        elif fs_source == "csv":
            rows = ["recording_frame_number,from_previous.framerate.hz"]
            rows.append("0,")  # first frame has no previous frame
            rows += [f"{i},{fs}" for i in range(1, 12)]
            (timestamps / "Camera_000_timestamps.csv").write_text("\n".join(rows) + "\n")
        elif fs_source == "npy":
            period_ns = 1e9 / fs
            stamps = np.arange(len(data)) * period_ns + 3.0e12
            np.save(str(timestamps / "Camera_000_timestamps.npy"), stamps)
        else:
            raise ValueError(fs_source)
    return recording


class TestReadFreemocap:
    def _body_data(self, F=5, M=33):
        rng = np.random.default_rng(1)
        data = rng.normal(scale=400.0, size=(F, M, 3))
        data[2, 7] = np.nan  # a landmark FreeMoCap could not triangulate
        return data

    def test_reads_recording_folder(self, tmp_path):
        body = self._body_data()
        recording = _freemocap_recording(tmp_path, body, fs=29.87)
        names, data, fs = read_freemocap(str(recording))
        assert names == list(MEDIAPIPE_LANDMARK_NAMES)
        assert len(names) == 33
        assert data.shape == (5, 33, 3)
        assert fs == 29.87
        # millimetres pass through unconverted, NaN gaps stay NaN
        ok = ~np.isnan(body)
        assert np.allclose(data[ok], body[ok])
        assert np.all(np.isnan(data[2, 7]))

    def test_fs_from_timestamps_csv(self, tmp_path):
        recording = _freemocap_recording(tmp_path, self._body_data(), fs=59.94, fs_source="csv")
        _, _, fs = read_freemocap(str(recording))
        assert fs == pytest.approx(59.94)

    def test_fs_from_nanosecond_timestamp_npy(self, tmp_path):
        recording = _freemocap_recording(tmp_path, self._body_data(), fs=30.0, fs_source="npy")
        _, _, fs = read_freemocap(str(recording))
        assert fs == pytest.approx(30.0, rel=1e-6)

    def test_no_timestamps_gives_none_with_warning(self, tmp_path):
        recording = _freemocap_recording(tmp_path, self._body_data(), fs=None)
        with pytest.warns(UserWarning, match="timestamp"):
            _, _, fs = read_freemocap(str(recording))
        assert fs is None

    def test_direct_npy_file_convenience(self, tmp_path):
        body = self._body_data()
        recording = _freemocap_recording(tmp_path, body, fs=29.87)
        npy = recording / "output_data" / "mediapipe_body_3d_xyz.npy"
        names, data, fs = read_freemocap(str(npy))
        assert names == list(MEDIAPIPE_LANDMARK_NAMES)
        assert data.shape == (5, 33, 3)
        # the recording folder is found from the file's position, so fs still resolves
        assert fs == 29.87

    def test_standalone_npy_file_has_no_fs(self, tmp_path):
        body = self._body_data()
        p = tmp_path / "mediapipe_body_3d_xyz.npy"
        np.save(str(p), body)
        with pytest.warns(UserWarning, match="timestamp"):
            names, data, fs = read_freemocap(str(p))
        assert names == list(MEDIAPIPE_LANDMARK_NAMES)
        assert fs is None

    def test_other_tracker_gets_generic_names(self, tmp_path):
        recording = _freemocap_recording(
            tmp_path, self._body_data(M=26), detector="rtmpose", fs=30.0
        )
        with pytest.warns(UserWarning, match="generic"):
            names, data, _ = read_freemocap(str(recording))
        assert names == [f"landmark_{i}" for i in range(26)]
        assert data.shape == (5, 26, 3)

    def test_empty_folder_raises_naming_expected_files(self, tmp_path):
        empty = tmp_path / "not_a_recording"
        empty.mkdir()
        with pytest.raises(ValueError, match="mediapipe_body_3d_xyz.npy"):
            read_freemocap(str(empty))


class TestFeedsDownstream:
    def test_trc_output_feeds_compare_modality_envelopes(self, tmp_path):
        # ten seconds of sinusoidal motion at 120 Hz, written as TRC, read back,
        # reduced to a per-frame motion envelope, and correlated with itself.
        fs = 120.0
        F = int(10 * fs)
        t = np.arange(F) / fs
        # a growing amplitude keeps the per-second envelope non-constant, so the
        # correlation is defined rather than the documented NaN for a flat envelope
        x = 10.0 * (1.0 + t) * np.sin(2 * np.pi * 0.5 * t)
        rows = [
            ["PathFileType", "4", "(X/Y/Z)", "long.trc"],
            ["DataRate", "CameraRate", "NumFrames", "NumMarkers", "Units",
             "OrigDataRate", "OrigDataStartFrame", "OrigNumFrames"],
            ["120.0", "120.0", str(F), "1", "mm", "120.0", "1", str(F)],
            ["Frame#", "Time", "HEAD", "", ""],
            ["", "", "X1", "Y1", "Z1"],
        ]
        for i in range(F):
            rows.append([str(i + 1), f"{t[i]:.6f}",
                         f"{x[i]:.6f}", "0.500000", "1.000000"])
        p = tmp_path / "long.trc"
        p.write_text("\n".join("\t".join(r) for r in rows) + "\n")

        names, data, fs_read = read_trc(str(p))
        assert names == ["HEAD"]
        assert fs_read == fs
        # per-frame motion envelope: summed marker displacement between frames
        env = np.nansum(np.linalg.norm(np.diff(data, axis=0), axis=2), axis=1)
        out = compare_modality_envelopes(env, env, fs_read, fs_read)
        assert out["n"] >= 9
        assert out["r"] == pytest.approx(1.0, abs=1e-9)

    def test_freemocap_output_feeds_compare_modality_envelopes(self, tmp_path):
        # ten seconds of sinusoidal motion at 30 Hz over the 33-landmark body,
        # written into a synthetic recording folder, read back, reduced to a
        # per-frame motion envelope, and correlated with itself.
        fs = 30.0
        F = int(10 * fs)
        t = np.arange(F) / fs
        body = np.zeros((F, 33, 3))
        body[:, :, 0] = (10.0 * (1.0 + t) * np.sin(2 * np.pi * 0.5 * t))[:, None]
        recording = _freemocap_recording(tmp_path, body, fs=fs)

        names, data, fs_read = read_freemocap(str(recording))
        assert names == list(MEDIAPIPE_LANDMARK_NAMES)
        assert fs_read == fs
        env = np.nansum(np.linalg.norm(np.diff(data, axis=0), axis=2), axis=1)
        out = compare_modality_envelopes(env, env, fs_read, fs_read)
        assert out["n"] >= 9
        assert out["r"] == pytest.approx(1.0, abs=1e-9)

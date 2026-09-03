"""Tests for the TRC and C3D readers in musicalgestures._mocap.

Ground truth without vendor files: the TRC fixtures are written in-test from the
documented five-line header format, and the C3D files are written by ezc3d itself
(create, write, read back), so read_c3d is tested against the library's own output
rather than hand-crafted binary bytes. One test feeds a reader's output through
compare_modality_envelopes to hold the readers to the read_qtm_tsv contract.
"""
import numpy as np
import pytest

from musicalgestures import read_trc, read_c3d, compare_modality_envelopes

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

"""Tests for musicalgestures._mocap (QTM TSV loader + cross-modality utils).

Synthetic ground truth: an in-test QTM TSV string fixture exercises the
loader (marker names, autodetected data start, zeros->NaN); known-lag
envelopes exercise the per-second correlation; a synthetic oscillation
exercises the dominant-frequency estimator.
"""
import numpy as np
import pytest

from musicalgestures import read_qtm_tsv, compare_modality_envelopes
from musicalgestures._mocap import dominant_frequency


QTM_TSV = "\t".join([
    "NO_OF_FRAMES", "4"]) + "\n" + \
    "\t".join(["NO_OF_MARKERS", "2"]) + "\n" + \
    "\t".join(["FREQUENCY", "100"]) + "\n" + \
    "\t".join(["MARKER_NAMES", "HEAD", "HAND"]) + "\n" + \
    "0\t0.0\t1.0\t2.0\t3.0\t10.0\t11.0\t12.0\n" + \
    "1\t0.01\t1.1\t2.1\t3.1\t10.1\t11.1\t12.1\n" + \
    "2\t0.02\t0.0\t0.0\t0.0\t10.2\t11.2\t12.2\n" + \
    "3\t0.03\t1.3\t2.3\t3.3\t10.3\t11.3\t12.3\n"


class TestReadQtmTsv:
    def test_parses_fixture(self, tmp_path):
        p = tmp_path / "trial.tsv"
        p.write_text(QTM_TSV)
        names, data, fs = read_qtm_tsv(str(p))
        assert names == ["HEAD", "HAND"]
        assert fs == 100.0
        assert data.shape == (4, 2, 3)
        # first frame, HEAD marker
        assert np.allclose(data[0, 0], [1.0, 2.0, 3.0])
        assert np.allclose(data[0, 1], [10.0, 11.0, 12.0])

    def test_zero_triples_become_nan(self, tmp_path):
        p = tmp_path / "trial.tsv"
        p.write_text(QTM_TSV)
        _, data, _ = read_qtm_tsv(str(p))
        # frame 2, HEAD marker was all zeros -> NaN
        assert np.all(np.isnan(data[2, 0]))
        # HAND marker at frame 2 is intact
        assert np.allclose(data[2, 1], [10.2, 11.2, 12.2])

    def test_latin1_fallback(self, tmp_path):
        p = tmp_path / "trial.tsv"
        # a latin-1 byte (0xB5 = micro sign) in a comment-ish header line
        content = QTM_TSV.replace("HEAD", "HE\xb5D")
        p.write_bytes(content.encode("latin-1"))
        names, data, fs = read_qtm_tsv(str(p))
        assert names[0] == "HE\xb5D"
        assert data.shape == (4, 2, 3)

    def test_no_header_infers_markers(self, tmp_path):
        p = tmp_path / "bare.tsv"
        # no MARKER_NAMES, pure 6-column (2 marker) numeric block
        p.write_text("1.0\t2.0\t3.0\t4.0\t5.0\t6.0\n"
                     "1.1\t2.1\t3.1\t4.1\t5.1\t6.1\n"
                     "1.2\t2.2\t3.2\t4.2\t5.2\t6.2\n")
        names, data, fs = read_qtm_tsv(str(p))
        assert names == []
        assert data.shape == (3, 2, 3)
        assert fs is None


class TestCompareModalityEnvelopes:
    def test_identical_envelopes_correlate_perfectly(self):
        rng = np.random.default_rng(0)
        # 60 s of a slow envelope, sampled at two different rates
        secs = 60
        base = np.abs(np.sin(np.linspace(0, 6 * np.pi, secs))) + \
            0.1 * rng.standard_normal(secs)
        fs_a, fs_b = 30.0, 100.0
        env_a = np.repeat(base, int(fs_a))
        env_b = np.repeat(base, int(fs_b))
        out = compare_modality_envelopes(env_a, env_b, fs_a, fs_b)
        assert out["r"] == pytest.approx(1.0, abs=1e-6)
        assert out["n"] == secs

    def test_uncorrelated_envelopes_low_r(self):
        rng = np.random.default_rng(1)
        fs = 30.0
        env_a = np.repeat(rng.standard_normal(60), int(fs))
        env_b = np.repeat(rng.standard_normal(60), int(fs))
        out = compare_modality_envelopes(env_a, env_b, fs, fs)
        assert abs(out["r"]) < 0.4

    def test_constant_envelope_returns_nan(self):
        env_a = np.ones(600)
        env_b = np.repeat(np.arange(20.0), 30)
        out = compare_modality_envelopes(env_a, env_b, 30.0, 30.0)
        assert np.isnan(out["r"])


class TestDominantFrequency:
    def test_recovers_oscillation(self):
        fs = 50.0
        t = np.arange(0, 60, 1 / fs)
        x = np.sin(2 * np.pi * 1.5 * t)
        assert dominant_frequency(x, fs, band=(0.3, 4.0)) == \
            pytest.approx(1.5, abs=0.1)

    def test_band_excludes_out_of_band_peak(self):
        fs = 50.0
        t = np.arange(0, 60, 1 / fs)
        # dominant tone at 6 Hz, weak tone at 1 Hz; band (0.3,4) should
        # return ~1 Hz, not 6 Hz.
        x = np.sin(2 * np.pi * 6.0 * t) + 0.3 * np.sin(2 * np.pi * 1.0 * t)
        assert dominant_frequency(x, fs, band=(0.3, 4.0)) == \
            pytest.approx(1.0, abs=0.2)

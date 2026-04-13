"""Unit tests for musicalgestures._ssm helper functions.

These tests cover the pure-Python/NumPy helpers that do not require FFmpeg or
a real video file, so they run in every environment including CI without
additional system dependencies.
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy import signal

from musicalgestures._ssm import smooth_downsample_feature_sequence, slow_dot


# ---------------------------------------------------------------------------
# smooth_downsample_feature_sequence
# ---------------------------------------------------------------------------

class TestSmoothDownsampleFeatureSequence:
    """Tests for smooth_downsample_feature_sequence."""

    def _make_X(self, n_features=3, n_frames=100):
        rng = np.random.default_rng(0)
        return rng.random((n_features, n_frames)).astype(np.float64)

    # --- output shape -------------------------------------------------------

    def test_output_shape_default_params(self):
        X = self._make_X(n_features=4, n_frames=100)
        X_smooth, sr_feat, _ = smooth_downsample_feature_sequence(X, sr=10)
        # with down_sampling=10: columns become ceil/floor of 100/10 = 10
        assert X_smooth.shape[0] == 4
        assert X_smooth.shape[1] == len(range(0, 100, 10))

    def test_output_shape_custom_downsampling(self):
        X = self._make_X(n_features=2, n_frames=50)
        X_smooth, _, _ = smooth_downsample_feature_sequence(X, sr=5, down_sampling=5)
        assert X_smooth.shape == (2, len(range(0, 50, 5)))

    def test_output_shape_single_feature(self):
        X = self._make_X(n_features=1, n_frames=80)
        X_smooth, _, _ = smooth_downsample_feature_sequence(X, sr=8, down_sampling=4)
        assert X_smooth.shape[0] == 1
        assert X_smooth.shape[1] == len(range(0, 80, 4))

    # --- sampling rate ------------------------------------------------------

    def test_sampling_rate_reduced(self):
        _, sr_feat, _ = smooth_downsample_feature_sequence(
            self._make_X(), sr=100, down_sampling=10
        )
        assert sr_feat == pytest.approx(10.0)

    def test_sampling_rate_custom(self):
        _, sr_feat, _ = smooth_downsample_feature_sequence(
            self._make_X(), sr=60, down_sampling=4
        )
        assert sr_feat == pytest.approx(15.0)

    def test_sampling_rate_no_downsampling(self):
        _, sr_feat, _ = smooth_downsample_feature_sequence(
            self._make_X(), sr=30, down_sampling=1
        )
        assert sr_feat == pytest.approx(30.0)

    # --- smoothing effect ---------------------------------------------------

    def test_constant_signal_unchanged_by_smoothing(self):
        """A constant-valued feature sequence should remain constant after smoothing."""
        X = np.ones((2, 100))
        X_smooth, _, _ = smooth_downsample_feature_sequence(
            X, sr=10, filt_len=11, down_sampling=1, w_type='boxcar'
        )
        # Interior samples should be very close to 1.0 (edge effects excluded)
        interior = X_smooth[:, 20:-20]
        np.testing.assert_allclose(interior, 1.0, atol=1e-10)

    def test_smoothing_reduces_variance(self):
        """Smoothing should reduce the variance of a noisy signal."""
        rng = np.random.default_rng(42)
        X = rng.random((1, 500))
        X_smooth, _, _ = smooth_downsample_feature_sequence(
            X, sr=50, filt_len=41, down_sampling=1
        )
        assert X_smooth.var() < X.var()

    # --- formatter ----------------------------------------------------------

    def test_formatter_is_callable(self):
        _, _, formatter = smooth_downsample_feature_sequence(
            self._make_X(), sr=10
        )
        # FuncFormatter wraps our inner function; calling it should return a string
        result = formatter(5.0, 0)
        assert isinstance(result, str)

    def test_formatter_output_value(self):
        _, _, formatter = smooth_downsample_feature_sequence(
            self._make_X(), sr=10
        )
        # The inner function multiplies x by the default down_sampling (10)
        # and rounds to 1 decimal place. With a float input, round() returns
        # a float, so str(round(3.5 * 10, 1)) == "35.0".
        assert formatter(3.5, 0) == str(round(3.5 * 10, 1))

    # --- window types -------------------------------------------------------

    def test_different_window_types_produce_output(self):
        X = self._make_X(n_features=2, n_frames=80)
        for w in ('boxcar', 'hann', 'hamming', 'blackman'):
            X_smooth, sr_feat, _ = smooth_downsample_feature_sequence(
                X, sr=10, w_type=w
            )
            assert X_smooth.shape[0] == 2
            assert sr_feat == pytest.approx(1.0)

    # --- dtype / value range ------------------------------------------------

    def test_output_is_float(self):
        X = self._make_X()
        X_smooth, _, _ = smooth_downsample_feature_sequence(X, sr=10)
        assert np.issubdtype(X_smooth.dtype, np.floating)


# ---------------------------------------------------------------------------
# slow_dot
# ---------------------------------------------------------------------------

class TestSlowDot:
    """Tests for slow_dot (low-memory dot product wrapper)."""

    # --- correctness --------------------------------------------------------

    def test_result_matches_numpy_dot(self):
        rng = np.random.default_rng(7)
        X = rng.random((10, 20))
        Y = rng.random((20, 15))
        S = slow_dot(X, Y, length=10)
        np.testing.assert_allclose(S, np.dot(X, Y), atol=1e-12)

    def test_square_identity_matrix(self):
        n = 8
        X = np.eye(n)
        S = slow_dot(X, X, length=n)
        np.testing.assert_allclose(S, np.eye(n), atol=1e-12)

    def test_result_shape(self):
        rng = np.random.default_rng(11)
        m, k, n = 5, 12, 7
        X = rng.random((m, k))
        Y = rng.random((k, n))
        S = slow_dot(X, Y, length=m)
        assert S.shape == (m, n)

    def test_single_row(self):
        X = np.array([[1.0, 2.0, 3.0]])
        Y = np.array([[4.0], [5.0], [6.0]])
        S = slow_dot(X, Y, length=1)
        assert S.shape == (1, 1)
        assert S[0, 0] == pytest.approx(32.0)

    def test_zero_matrices(self):
        X = np.zeros((6, 10))
        Y = np.zeros((10, 6))
        S = slow_dot(X, Y, length=6)
        np.testing.assert_array_equal(S, np.zeros((6, 6)))

    # --- self-similarity matrix properties ---------------------------------

    def test_ssm_symmetry(self):
        """X @ X.T should be symmetric (a common SSM construction)."""
        rng = np.random.default_rng(99)
        X = rng.random((15, 8))
        S = slow_dot(X, X.T, length=15)
        np.testing.assert_allclose(S, S.T, atol=1e-12)

    def test_ssm_diagonal_is_max(self):
        """In an SSM built from normalised rows, diagonal >= off-diagonal."""
        rng = np.random.default_rng(3)
        X = rng.random((10, 5))
        # Normalise rows
        norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-8
        X_norm = X / norms
        S = slow_dot(X_norm, X_norm.T, length=10)
        diag = np.diag(S)
        for i in range(len(diag)):
            assert diag[i] >= S[i, :].max() - 1e-10

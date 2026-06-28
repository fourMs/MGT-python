"""Regression tests for the lazily-JIT-compiled numba kernels (issue #349).

`import numba` is deferred (it pulls in LLVM and costs ~0.13s of `import musicalgestures`).
Each module compiles its kernels on first use via `_ensure_numba()`. The directogram case is
the tricky one: the jitted `directogram` calls the jitted `matrix3D_norm`, so the inner kernel
must already be a numba Dispatcher in the module namespace when the outer one is compiled. These
tests pin that behaviour so the deferral can't silently regress to a broken nested-jit state.
"""
from __future__ import annotations

import sys
import subprocess

import numpy as np


def test_numba_not_imported_at_package_import():
    """The whole point of the deferral: importing the package must not pull in numba."""
    code = "import sys, musicalgestures; print('numba' in sys.modules)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False", f"numba was imported at package import:\n{out.stdout}"


def test_directogram_nested_jit():
    """directogram() calls matrix3D_norm() — both must end up as real numba Dispatchers."""
    from musicalgestures import _directograms

    _directograms._ensure_numba()
    assert type(_directograms.matrix3D_norm).__name__ == "CPUDispatcher"
    assert type(_directograms.directogram).__name__ == "CPUDispatcher"

    # matrix3D_norm is the per-pixel Frobenius norm over the channel axis.
    flow = np.random.default_rng(0).random((6, 7, 2)).astype(np.float64)
    norm = _directograms.matrix3D_norm(flow)
    np.testing.assert_allclose(norm, np.sqrt(np.sum(np.abs(flow) ** 2, axis=2)), rtol=1e-6)

    dg = _directograms.directogram(flow)
    assert dg.shape == (len(_directograms.HISTOGRAM_BINS),)
    assert np.all(np.isfinite(dg))

    _directograms._ensure_numba()  # idempotent — must not recompile / error


def test_impacts_and_warp_kernels_compile():
    from musicalgestures import _impacts, _warp

    _impacts._ensure_numba()
    assert type(_impacts.impact_detection).__name__ == "CPUDispatcher"

    _warp._ensure_numba()
    assert type(_warp.beats_diff).__name__ == "CPUDispatcher"
    # beats_diff returns inter-beat gaps padded with the head and tail distances.
    beats = np.array([2, 5, 9], dtype=np.int64)
    media = np.zeros((20,), dtype=np.float64)
    out = _warp.beats_diff(beats, media)
    np.testing.assert_array_equal(out, np.array([2, 3, 4, 11]))

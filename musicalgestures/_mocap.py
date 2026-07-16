"""
Motion-capture I/O and cross-modality utilities.

Pure numpy/scipy helpers ported from the "still standing" and
Westney-comparisons studies:

* :func:`read_qtm_tsv` -- a single robust reader for Qualisys Track Manager
  (QTM) TSV exports, consolidating the four/five near-duplicate loaders that
  were copy-pasted across the study scripts.
* :func:`compare_modality_envelopes` -- resample two motion envelopes onto a
  common per-second grid and correlate them (e.g. video-pose vs mocap
  validation).
* :func:`dominant_frequency` -- the dominant spectral peak of a signal within
  a band, via Welch.

.. note::
   :func:`compare_modality_envelopes` deliberately takes *precomputed* 1-D
   motion envelopes rather than computing quantity-of-motion internally, so
   this module stays independent of the QoM machinery. The natural producer
   of such envelopes is ``musicalgestures._qom.band_limited_qom`` followed by
   a per-second binning (``envelope`` / ``bin_series``), arriving in a
   sibling PR.

Source: still standing study and Westney-comparisons study (Jensenius).
"""

import numpy as np


def read_qtm_tsv(path):
    """
    Read a Qualisys Track Manager (QTM) TSV motion-capture export.

    Consolidates the several near-duplicate loaders used across the studies
    into one robust reader. It locates the ``MARKER_NAMES`` header row to
    recover marker labels, autodetects where the numeric data block starts
    (the first row whose first field parses as a float), drops a trailing
    all-empty column produced by a trailing tab, converts exact-zero XYZ
    triples (Qualisys gap fills) to ``NaN``, and falls back from UTF-8 to
    latin-1 encoding. When a ``FREQUENCY`` header field is present the frame
    rate is returned as well.

    Source: still standing study and Westney-comparisons study (Jensenius) --
    unifies the ``load_qtm`` variants in the balance/dynamics/circular/
    spatial-range reports and the latin-1 variant in ``compare_mp_mocap``.

    Args:
        path (str): Path to the ``.tsv`` file.

    Returns:
        tuple: ``(marker_names, data, fs)`` where ``marker_names`` is a list
            of ``M`` strings (empty if no header was found), ``data`` is a
            float array of shape ``(T, M, 3)`` with gaps as ``NaN``, and
            ``fs`` is the frame rate in Hz or ``None`` if not derivable from
            the header.
    """
    import io

    def _read_lines(enc):
        with io.open(path, encoding=enc) as fh:
            return fh.readlines()

    try:
        lines = _read_lines("utf-8")
    except (UnicodeDecodeError, UnicodeError):
        lines = _read_lines("latin-1")

    marker_names = []
    fs = None
    data_start = None
    for i, ln in enumerate(lines):
        parts = ln.rstrip("\n").split("\t")
        key = parts[0].strip().upper()
        if key == "MARKER_NAMES":
            marker_names = [p.strip() for p in parts[1:] if p.strip()]
            continue
        if key == "FREQUENCY" and len(parts) > 1:
            try:
                fs = float(parts[1])
            except ValueError:
                pass
            continue
        # first row whose leading field is numeric marks the data block
        try:
            float(parts[0])
            data_start = i
            break
        except ValueError:
            continue

    if data_start is None:
        raise ValueError(f"No numeric data block found in {path!r}")

    rows = []
    for ln in lines[data_start:]:
        parts = ln.rstrip("\n").split("\t")
        try:
            rows.append([float(p) for p in parts if p != ""])
        except ValueError:
            continue
    if not rows:
        raise ValueError(f"No parseable data rows in {path!r}")

    ncol = min(len(r) for r in rows)
    arr = np.array([r[:ncol] for r in rows], dtype=float)

    # A QTM data row may carry a leading time/frame column(s); the marker
    # block is the trailing 3*M columns. Prefer the marker count from the
    # header; otherwise infer the largest multiple of 3.
    if marker_names:
        M = len(marker_names)
    else:
        M = ncol // 3
    offset = arr.shape[1] - 3 * M
    if offset < 0:
        # header lists more markers than columns present; fall back
        M = arr.shape[1] // 3
        offset = arr.shape[1] - 3 * M
        marker_names = marker_names[:M]
    block = arr[:, offset:offset + 3 * M]
    data = block.reshape(block.shape[0], M, 3)

    # exact-zero triples are Qualisys gap fills -> NaN
    gap = np.all(data == 0, axis=2)
    data[gap] = np.nan

    return marker_names, data, fs


def dominant_frequency(x, fs, band=(0.3, 4.0)):
    """
    Dominant frequency of a signal within a band, via a Welch spectrum.

    Returns the frequency of the largest Welch power-spectral-density peak
    inside ``band`` -- e.g. the dominant oscillation rate of a body-part
    speed or vertical-position signal.

    Source: Westney-comparisons study (Jensenius), extended motion-feature
    analysis (motion dominant frequency of vertical trunk position).

    Args:
        x (np.ndarray): 1-D input signal.
        fs (float): Sampling rate in Hz.
        band (tuple, optional): ``(low, high)`` search band in Hz. Defaults
            to ``(0.3, 4.0)``.

    Returns:
        float: The dominant frequency in Hz, or ``nan`` if the band is empty.
    """
    from scipy.signal import welch

    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 8:
        return np.nan
    lo, hi = band
    f, P = welch(x - x.mean(), fs, nperseg=min(2048, len(x)))
    mask = (f >= lo) & (f <= hi)
    if not mask.any():
        return np.nan
    return float(f[mask][np.argmax(P[mask])])


def compare_modality_envelopes(env_a, env_b, fs_a, fs_b):
    """
    Correlate two motion envelopes after resampling to a common grid.

    Resamples both 1-D envelopes onto a shared one-sample-per-second grid
    (by averaging within each second), truncates to the common length, and
    returns the Pearson correlation -- the video-vs-mocap (or view-vs-view)
    agreement measure. Both inputs are treated as already-computed motion
    envelopes (e.g. per-frame band-limited quantity-of-motion), keeping this
    function decoupled from the QoM computation itself. The per-second binning
    uses an integer-rounded step, so non-integer frame rates (e.g. 29.97 fps)
    drift slightly over long signals; this function is intended for validation
    rather than precise alignment.

    Source: still standing / Westney-comparisons study (Jensenius),
    MediaPipe-vs-mocap validation (``compare_mp_mocap``).

    Args:
        env_a (np.ndarray): First 1-D motion envelope.
        env_b (np.ndarray): Second 1-D motion envelope.
        fs_a (float): Sampling rate of ``env_a`` in Hz.
        fs_b (float): Sampling rate of ``env_b`` in Hz.

    Returns:
        dict: ``{"r", "n"}`` where ``r`` is the Pearson correlation of the
            two per-second envelopes and ``n`` the number of common seconds
            (``r`` is ``nan`` if fewer than three overlapping seconds or if
            either resampled envelope is constant).
    """
    def _per_second(env, fs):
        env = np.asarray(env, dtype=float)
        nsec = int(len(env) / fs)
        if nsec < 1:
            return np.array([])
        step = int(round(fs))
        step = max(step, 1)
        return np.array([np.nanmean(env[i * step:(i + 1) * step])
                         for i in range(nsec)])

    a = _per_second(env_a, fs_a)
    b = _per_second(env_b, fs_b)
    n = min(len(a), len(b))
    if n < 3:
        return dict(r=np.nan, n=n)
    a = a[:n]
    b = b[:n]
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3 or a[ok].std() == 0 or b[ok].std() == 0:
        return dict(r=np.nan, n=int(ok.sum()))
    r = float(np.corrcoef(a[ok], b[ok])[0, 1])
    return dict(r=r, n=int(ok.sum()))

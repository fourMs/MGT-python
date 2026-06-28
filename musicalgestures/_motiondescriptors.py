from __future__ import annotations

import os
import numpy as np
import matplotlib.pyplot as plt

from musicalgestures._movementbeats import _movement_qom
from musicalgestures._utils import MgFigure, resolve_filename, generate_outfilename


def _sparc(speed: np.ndarray, fs: float, fc: float = 10.0, amp_th: float = 0.05,
           padlevel: int = 4) -> float:
    """Spectral arc length (SPARC) smoothness metric of a speed profile.

    SPARC is a dimensionless, well-validated movement-smoothness measure (Balasubramanian et al.,
    *IEEE TBME* 2015): the arc length of the normalised Fourier magnitude spectrum of the speed
    profile, restricted to its meaningful low-frequency band. Smoother movements have less
    high-frequency content and therefore a *less negative* SPARC; jerky movements are more
    negative. Returns NaN when the signal is too short or silent.
    """
    speed = np.asarray(speed, dtype=float)
    if speed.size < 2 or not np.any(speed):
        return float('nan')
    n = speed.size
    nfft = int(2 ** (np.ceil(np.log2(n)) + padlevel))
    f = np.arange(0, fs, fs / nfft)
    mag = np.abs(np.fft.fft(speed, nfft))
    if mag.max() == 0:
        return float('nan')
    mag = mag / mag.max()
    # Keep the low-frequency band up to the cutoff fc...
    in_band = np.where(f <= fc)[0]
    f_sel, mag_sel = f[in_band], mag[in_band]
    # ...then trim to the contiguous span whose magnitude exceeds the adaptive amplitude threshold.
    above = np.where(mag_sel >= amp_th)[0]
    if above.size < 2:
        return float('nan')
    band = slice(above[0], above[-1] + 1)
    f_sel, mag_sel = f_sel[band], mag_sel[band]
    df = np.diff(f_sel) / (f_sel[-1] - f_sel[0])
    dmag = np.diff(mag_sel)
    return float(-np.sum(np.sqrt(df ** 2 + dmag ** 2)))


def _motion_entropy(qom: np.ndarray, bins: int = 50) -> float:
    """Normalised Shannon entropy (0–1) of the quantity-of-motion magnitude distribution.

    The QoM values are binned into a probability distribution and its Shannon entropy is
    normalised by ``log2(bins)``. Low values mean the motion magnitude stays concentrated (steady
    or still); high values mean it is spread across many levels (varied, complex motion).
    """
    q = np.asarray(qom, dtype=float)
    if q.size == 0 or q.max() <= 0:
        return 0.0
    hist, _ = np.histogram(q, bins=bins, range=(0.0, float(q.max())))
    total = hist.sum()
    if total == 0:
        return 0.0
    p = hist[hist > 0] / total
    entropy = -np.sum(p * np.log2(p)) / np.log2(bins)
    return float(min(1.0, max(0.0, entropy)))  # clamp tiny float overshoot into [0, 1]


def _qom_spectrum(qom: np.ndarray, fps: float, window: str = 'hann') -> tuple[np.ndarray, np.ndarray]:
    """One-sided power spectrum of the (DC-removed, windowed) quantity-of-motion signal.

    A Hann window is applied by default to suppress spectral leakage from the finite, non-periodic
    QoM segment (the windowing question raised in #210); pass ``window='none'`` for a rectangular
    window. Returns ``(frequencies_hz, power)``.
    """
    q = np.asarray(qom, dtype=float)
    q = q - q.mean()  # remove DC so the 0 Hz bin doesn't dominate
    n = q.size
    if n < 2:
        return np.zeros(0), np.zeros(0)
    if str(window).lower() in ('none', 'rect', 'boxcar', 'rectangular'):
        w = np.ones(n)
    else:
        w = np.hanning(n)
    spec = np.fft.rfft(q * w)
    power = np.abs(spec) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0 / fps)
    return freqs, power


def mg_motiondescriptors(self, window: str = 'hann', entropy_bins: int = 50,
                         save_data: bool = True, save_plot: bool = True,
                         data_format: str = 'csv', target_name: str | None = None,
                         overwrite: bool = True) -> "MgFigure":
    """Scalar movement descriptors derived from the quantity-of-motion (QoM) signal.

    Computes a compact set of higher-level descriptors that summarise *how* something moves,
    complementing the per-frame motion data from :func:`motion`:

    - **motion_energy** — mean squared QoM; the overall amount of movement.
    - **motion_smoothness** — SPARC (spectral arc length) of the QoM profile; a dimensionless,
      validated smoothness metric (less negative = smoother, more negative = jerkier).
    - **motion_entropy** — normalised (0–1) Shannon entropy of the QoM magnitude distribution;
      the complexity/variedness of the motion.
    - **spectral descriptors** of the QoM signal (Hann-windowed by default): the **dominant
      frequency** (Hz, the main movement-rhythm rate) and the **spectral centroid** (Hz, the
      "centre of mass" of the movement spectrum).

    Args:
        window (str, optional): FFT window for the spectral descriptors — 'hann' (default,
            recommended to reduce leakage) or 'none' for a rectangular window.
        entropy_bins (int, optional): Number of histogram bins for the entropy estimate. Defaults to 50.
        save_data (bool, optional): Save the descriptors to a data file. Defaults to True.
        save_plot (bool, optional): Save the figure (QoM time series + power spectrum). Defaults to True.
        data_format (str, optional): Data file format: 'csv', 'tsv' or 'txt'. Defaults to 'csv'.
        target_name (str, optional): Output image name. Defaults to None (``<name>_motiondescriptors.png``).
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.

    Returns:
        MgFigure: figure whose ``.data`` holds the scalar descriptors and the spectrum arrays
        (``frequencies``, ``power``), or None if there are too few frames.
    """
    qom, fps = _movement_qom(self)
    if qom.size < 4:
        print('Not enough frames to compute motion descriptors.')
        return None

    motion_energy = float(np.mean(qom ** 2))
    motion_smoothness = _sparc(qom, fps)
    motion_entropy = _motion_entropy(qom, bins=entropy_bins)
    freqs, power = _qom_spectrum(qom, fps, window=window)

    if power.size > 1 and power[1:].any():
        dominant_freq = float(freqs[1 + int(np.argmax(power[1:]))])  # skip the 0 Hz bin
    else:
        dominant_freq = 0.0
    spectral_centroid = float(np.sum(freqs * power) / np.sum(power)) if power.sum() > 0 else 0.0

    d = {
        'of': self.of,
        'fps': fps,
        'n_frames': int(qom.size),
        'motion_energy': motion_energy,
        'motion_smoothness': motion_smoothness,
        'motion_entropy': motion_entropy,
        'dominant_freq': dominant_freq,
        'spectral_centroid': spectral_centroid,
        'window': window,
        'qom': qom,
        'frequencies': freqs,
        'power': power,
    }

    if save_data:
        _save_descriptors(self.of, d, data_format, overwrite)

    target_name = resolve_filename(self.of, '_motiondescriptors.png', target_name, overwrite)

    times = np.arange(qom.size) / fps
    fig, (ax_q, ax_s) = plt.subplots(2, 1, figsize=(12, 7), dpi=300)
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)

    ax_q.plot(times, qom, color='#1f77b4', lw=1.0)
    ax_q.fill_between(times, qom, color='#1f77b4', alpha=0.15)
    ax_q.set(xlabel='Time (s)', ylabel='Quantity of motion', title='Quantity of motion over time')
    ax_q.margins(x=0)

    # Power spectrum up to a sensible movement band (10 Hz), dominant frequency marked.
    band = freqs <= 10.0 if freqs.size else slice(None)
    ax_s.plot(freqs[band], power[band], color='#d62728', lw=1.0)
    ax_s.fill_between(freqs[band], power[band], color='#d62728', alpha=0.15)
    if dominant_freq > 0:
        ax_s.axvline(dominant_freq, color='#333333', ls='--', lw=1.0,
                     label=f'dominant {dominant_freq:.2f} Hz')
        ax_s.legend()
    ax_s.set(xlabel='Frequency (Hz)', ylabel='Power',
             title=f'QoM power spectrum ({window} window)')
    ax_s.margins(x=0)

    summary = (f'energy = {motion_energy:.3g}    smoothness (SPARC) = {motion_smoothness:.3f}    '
               f'entropy = {motion_entropy:.3f}    spectral centroid = {spectral_centroid:.2f} Hz')
    fig.suptitle(summary, fontsize=11, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    if save_plot:
        plt.savefig(target_name, format='png', transparent=False)
    plt.close(fig)

    mgf = MgFigure(figure=fig, figure_type='video.motiondescriptors', data=d, layers=None,
                   image=target_name if save_plot else None)
    self.motiondescriptors_figure = mgf
    return mgf


def _save_descriptors(of: str, d: dict, data_format: str, overwrite: bool) -> None:
    """Write the scalar descriptors to a key/value data file (one descriptor per row)."""
    formats = data_format if isinstance(data_format, list) else [data_format]
    keys = ['fps', 'n_frames', 'motion_energy', 'motion_smoothness', 'motion_entropy',
            'dominant_freq', 'spectral_centroid', 'window']
    for fmt in formats:
        sep = '\t' if fmt in ('tsv', 'txt') else ','
        ext = '.tsv' if fmt == 'tsv' else ('.txt' if fmt == 'txt' else '.csv')
        out = of + '_motiondescriptors' + ext
        if not overwrite:
            out = generate_outfilename(out)
        with open(out, 'w') as f:
            f.write(f'descriptor{sep}value\n')
            for k in keys:
                f.write(f'{k}{sep}{d[k]}\n')

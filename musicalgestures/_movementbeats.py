"""
Movement-based beat statistics: detect rhythmic onsets in a video's quantity of motion
and compute the same circular timing statistics as the audio ``beat_statistics()``.

This lets ``MgVideo.beat_statistics(source='motion')`` reveal how consistent the *movement*
rhythm is, analogous to the audio version.
"""

import os
import numpy as np
import cv2
import matplotlib
import matplotlib.pyplot as plt
from musicalgestures._utils import MgFigure, MgProgressbar, generate_outfilename


def _movement_qom(self):
    """Return (qom, fps): the per-frame quantity of motion (mean absolute frame difference)."""
    cap = cv2.VideoCapture(self.filename)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or self.fps
    qom = []
    prev = None
    pb = MgProgressbar(total=max(total, 1), prefix='Detecting movement beats:')
    n = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
            if prev is not None:
                qom.append(float(np.abs(gray - prev).mean()))
            prev = gray
            n += 1
            pb.progress(n)
    finally:
        cap.release()
    pb.progress(max(total, 1))
    return np.asarray(qom, dtype=float), fps


def mg_beat_statistics(self, source='audio', n_bins=32, cmap='YlOrRd', dpi=300,
                       autoshow=True, title=None, target_name=None, overwrite=True,
                       fmin=0.2, fmax=8.0):
    """
    Circular statistics of beat-timing consistency, from the **audio** or from the **movement**.

    Fits an ideal isochronous beat grid to the detected beats and visualises how each beat
    deviates from it (a polar phase histogram with the mean resultant vector, plus a
    millisecond-deviation time series), revealing whether the rhythm rushes, drags, or stays
    steady. Requires at least four detected beats.

    Args:
        source (str, optional): `'audio'` (default) analyses the audio track (same as
            `MgAudio.beat_statistics`); `'motion'` detects rhythmic onsets in the video's
            quantity of motion and analyses the **movement** rhythm.
        n_bins (int, optional): Bins in the polar phase histogram. Defaults to 32.
        cmap (str, optional): Colormap for the polar histogram. Defaults to 'YlOrRd'.
        dpi (int, optional): Output DPI. Defaults to 300.
        autoshow (bool, optional): Kept for API parity (display is via show()). Defaults to True.
        title (str, optional): Optional figure title; use 'filename' for the file name. Defaults to None.
        target_name (str, optional): Output image name. Defaults to None.
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.
        fmin (float, optional): Lowest movement-onset rate to consider (Hz), 'motion' only. Defaults to 0.2.
        fmax (float, optional): Highest movement-onset rate to consider (Hz), 'motion' only. Defaults to 8.0.

    Returns:
        MgFigure: figure with the beat statistics in ``.data``, or None if too few beats.
    """
    source = str(source).lower()
    if source == 'audio':
        # Delegate to the inherited audio implementation (operates on the audio track)
        from musicalgestures._audio import MgAudio
        return MgAudio.beat_statistics(self, n_bins=n_bins, cmap=cmap, dpi=dpi,
                                       autoshow=autoshow, title=title,
                                       target_name=target_name, overwrite=overwrite)
    if source != 'motion':
        raise ValueError("source must be 'audio' or 'motion'.")

    from musicalgestures._analysis import circular_stats, rayleigh_test
    import librosa

    qom, fps = _movement_qom(self)
    if len(qom) < 8:
        print('Not enough frames to detect movement beats.')
        return

    # Detect movement onsets ("beats") as peaks in the quantity-of-motion envelope.
    beat_times = librosa.onset.onset_detect(
        onset_envelope=qom, sr=fps, hop_length=1, units='time', backtrack=False)
    # Keep onsets within the plausible movement-rate band via inter-onset interval
    if len(beat_times) >= 2:
        ibi_all = np.diff(beat_times)
        keep = (ibi_all >= 1.0 / fmax) & (ibi_all <= 1.0 / fmin)
        beat_times = np.concatenate([beat_times[:1], beat_times[1:][keep]])

    if len(beat_times) < 4:
        print('Not enough movement beats detected for circular statistics (need at least 4).')
        return

    # Circular grid statistics (same model as the audio version)
    k = np.arange(len(beat_times))
    T_fit, t0_fit = np.polyfit(k, beat_times, 1)
    deviations_s = beat_times - (t0_fit + k * T_fit)
    beat_phases = (deviations_s / T_fit) * 2 * np.pi % (2 * np.pi)
    R_beat, mu_beat = circular_stats(beat_phases)
    _, p_rayleigh = rayleigh_test(beat_phases)
    ibi = np.diff(beat_times)
    beat_regularity = float(1.0 - ibi.std() / ibi.mean()) if len(ibi) and ibi.mean() > 0 else 0.0
    tempo = 60.0 / T_fit if T_fit > 0 else 0.0

    d = {
        'source': 'motion',
        'fps': fps,
        'of': self.of,
        'tempo': tempo,
        'beat_times': beat_times,
        'ibi': ibi,
        'beat_regularity': beat_regularity,
        'beat_phases': beat_phases,
        'deviations_s': deviations_s,
        'R_beat': R_beat,
        'mu_beat': mu_beat,
        'T_fit': T_fit,
        't0_fit': t0_fit,
        'p_rayleigh': p_rayleigh,
        'qom': qom,
    }

    if target_name is None:
        target_name = self.of + '_movement_beatstats.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    deviations_ms = deviations_s * 1000
    R, mu = R_beat, mu_beat

    fig = plt.figure(figsize=(14, 6), dpi=dpi)
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)

    # Polar histogram of movement-beat phases
    ax_p = fig.add_subplot(121, projection='polar')
    bin_edges = np.linspace(0, 2 * np.pi, n_bins + 1)
    counts, _ = np.histogram(beat_phases, bins=bin_edges)
    theta_c = (bin_edges[:-1] + bin_edges[1:]) / 2
    norm_c = counts / (counts.max() + 1e-9)
    ax_p.bar(theta_c, counts, width=2 * np.pi / n_bins * 0.88,
             color=matplotlib.colormaps[cmap](norm_c), alpha=0.85,
             edgecolor='white', linewidth=0.3)
    if counts.max() > 0:
        ax_p.annotate('', xy=(np.radians(mu), R * counts.max()), xytext=(0, 0),
                      arrowprops=dict(arrowstyle='-|>', color='#333333', lw=2.0, mutation_scale=16))
    ax_p.set_xticks([0, np.pi / 2, np.pi, 3 * np.pi / 2])
    ax_p.set_xticklabels(['on beat', '1/4 late', '1/2', '1/4 early'], fontsize=8)
    ax_p.set_title(f'Movement-beat phase deviation\nR = {R:.3f}   μ = {mu:.1f}°   p = {p_rayleigh:.4f}', fontsize=10)

    # Time series of deviations
    ax_t = fig.add_subplot(122)
    sc = ax_t.scatter(beat_times, deviations_ms, c=beat_times, cmap='plasma', s=18, alpha=0.8)
    ax_t.axhline(0, color='#888888', lw=1.0, ls='--', alpha=0.7)
    ax_t.axhline(float(deviations_ms.mean()), color='#1f77b4', lw=1.2, ls=':',
                 label=f'mean {float(deviations_ms.mean()):.1f} ms')
    ax_t.set(xlabel='Time (s)', ylabel='Deviation from ideal grid (ms)', title='Movement-beat timing deviation')
    ax_t.legend()
    cb = fig.colorbar(sc, ax=ax_t)
    cb.set_label('Time (s)')

    if title is None:
        title = ''
    if title == 'filename':
        title = os.path.basename(self.filename)
    fig.suptitle(f'{title}   Movement tempo: {tempo:.1f} BPM   σ = {float(deviations_ms.std()):.1f} ms'.strip(),
                 fontsize=13, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(target_name, format='png', transparent=False)
    plt.close(fig)

    mgf = MgFigure(figure=fig, figure_type='video.beat_statistics', data=d, layers=None, image=target_name)
    self.movement_beat_statistics = mgf
    return mgf

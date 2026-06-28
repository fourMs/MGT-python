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
from musicalgestures._utils import MgFigure, MgProgressbar, generate_outfilename, resolve_filename


def _movement_qom(self):
    """Return (qom, fps): the per-frame quantity of motion (mean absolute frame difference).

    The result is cached on the MgVideo (keyed by filename) so that calling several
    movement/audio-movement analyses in a row does not re-decode the video each time.
    """
    cache = getattr(self, '_qom_cache', None)
    if cache is not None and cache[0] == self.filename:
        return cache[1], cache[2]
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
    qom = np.asarray(qom, dtype=float)
    self._qom_cache = (self.filename, qom, fps)
    return qom, fps


def mg_beat_statistics(self, source='motion', n_bins=32, cmap='YlOrRd', dpi=300,
                       autoshow=True, title=None, target_name=None, overwrite=True,
                       fmin=0.2, fmax=8.0):
    """
    Circular statistics of beat-timing consistency, from the **audio** or from the **movement**.

    Fits an ideal isochronous beat grid to the detected beats and visualises how each beat
    deviates from it (a polar phase histogram with the mean resultant vector, plus a
    millisecond-deviation time series), revealing whether the rhythm rushes, drags, or stays
    steady. Requires at least four detected beats.

    Args:
        source (str, optional): `'motion'` (default) detects rhythmic onsets in the video's
            quantity of motion and analyses the **movement** rhythm; `'audio'` analyses the
            audio track instead (same as `MgAudio.beat_statistics` / `video.audio.beat_statistics`).
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

    target_name = resolve_filename(self.of, '_movement_beatstats.png', target_name, overwrite)

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


def _nearest_harmonic_ratio(ratio):
    """Return (nearest_simple_ratio, label) for a tempo ratio (e.g. 2.02 -> (2.0, '2:1'))."""
    candidates = {1/3: '1:3', 1/2: '1:2', 2/3: '2:3', 1.0: '1:1',
                  3/2: '3:2', 2.0: '2:1', 3.0: '3:1'}
    best = min(candidates, key=lambda c: abs(np.log2(ratio / c)) if ratio > 0 else np.inf)
    return best, candidates[best]


def mg_tempo_similarity(self, dpi=300, autoshow=True, title=None, target_name=None, overwrite=True):
    """
    Compare the **audio** tempo/rhythm with the **movement** tempo/rhythm and report how similar
    they are.

    Estimates the tempo of the audio track (from its onset-strength envelope) and of the movement
    (from the quantity-of-motion envelope), then aligns the two normalised envelopes and
    cross-correlates them to measure rhythmic agreement. The figure shows the two envelopes
    overlaid and their cross-correlation; the report (also saved as a CSV) lists the audio tempo,
    movement tempo, their ratio and nearest harmonic relationship, the peak cross-correlation, and
    the lag (s) at which the movement best aligns with the audio.

    Args:
        dpi (int, optional): Output DPI. Defaults to 300.
        autoshow (bool, optional): Kept for API parity (display via show()). Defaults to True.
        title (str, optional): Optional figure title; 'filename' uses the file name. Defaults to None.
        target_name (str, optional): Output image name. Defaults to None ("_tempo_similarity.png").
        overwrite (bool, optional): Overwrite or auto-increment the filename. Defaults to True.

    Returns:
        MgFigure: the report figure (metrics in ``.data``), or None if the video has no audio.
    """
    import librosa
    from musicalgestures._utils import has_audio

    if not has_audio(self.filename):
        print('The video has no audio track — cannot compare audio and movement tempo.')
        return None

    target_name = resolve_filename(self.of, '_tempo_similarity.png', target_name, overwrite)

    # --- Audio envelope + tempo ---
    y, sr = self._load()
    hop = self.hop_length
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    audio_tempo = float(np.atleast_1d(librosa.beat.tempo(onset_envelope=oenv, sr=sr, hop_length=hop))[0])
    a_t = librosa.times_like(oenv, sr=sr, hop_length=hop)

    # --- Movement envelope + tempo ---
    qom, fps = _movement_qom(self)
    if len(qom) < 4:
        print('Not enough frames to estimate movement tempo.')
        return None
    motion_tempo = float(np.atleast_1d(librosa.beat.tempo(onset_envelope=qom, sr=fps, hop_length=1))[0])
    m_t = np.arange(len(qom)) / max(fps, 1e-9)

    # --- Resample both onto a common time grid and cross-correlate ---
    fs = 50.0  # Hz
    dur = min(a_t[-1] if len(a_t) else 0, m_t[-1] if len(m_t) else 0)
    if dur <= 0:
        print('Audio and movement do not overlap in time.')
        return None
    t = np.arange(0, dur, 1.0 / fs)
    a = np.interp(t, a_t, oenv)
    m = np.interp(t, m_t, qom)
    a = (a - a.mean()) / (a.std() + 1e-9)
    m = (m - m.mean()) / (m.std() + 1e-9)
    xcorr = np.correlate(m, a, mode='full') / len(t)
    lags = np.arange(-len(t) + 1, len(t)) / fs
    peak_i = int(np.argmax(xcorr))
    peak_lag = float(lags[peak_i])
    peak_corr = float(xcorr[peak_i])
    zero_corr = float(xcorr[len(t) - 1])  # correlation at zero lag

    ratio = motion_tempo / audio_tempo if audio_tempo > 0 else 0.0
    harm, harm_label = _nearest_harmonic_ratio(ratio) if ratio > 0 else (0.0, 'n/a')
    tempo_agreement = float(max(0.0, 1.0 - abs(np.log2(ratio / harm)))) if (ratio > 0 and harm > 0) else 0.0

    # --- Figure ---
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), dpi=dpi)
    fig.patch.set_facecolor('white')
    if title == 'filename':
        title = os.path.basename(self.filename)
    fig.suptitle(title or 'Audio–movement tempo similarity', fontsize=14)

    axes[0].plot(t, a, color='#1f77b4', lw=0.9, label=f'Audio onset (tempo {audio_tempo:.1f} BPM)')
    axes[0].plot(t, m, color='#d62728', lw=0.9, alpha=0.8, label=f'Movement QoM (tempo {motion_tempo:.1f} BPM)')
    axes[0].set_xlabel('Time (s)')
    axes[0].set_ylabel('Normalised envelope')
    axes[0].legend(loc='upper right', fontsize=8)
    axes[0].set_title('Audio onset strength vs. quantity of motion', fontsize=10)

    axes[1].plot(lags, xcorr, color='#2ca02c', lw=0.9)
    axes[1].axvline(peak_lag, color='crimson', ls='--', lw=1,
                    label=f'peak r={peak_corr:.2f} @ {peak_lag:+.2f}s')
    axes[1].axvline(0, color='#888888', ls=':', lw=0.8)
    axes[1].set_xlabel('Lag (s)  — movement relative to audio')
    axes[1].set_ylabel('Cross-correlation')
    axes[1].legend(loc='upper right', fontsize=8)
    axes[1].set_title(
        f'Tempo ratio {ratio:.2f} (≈ {harm_label})  |  agreement {tempo_agreement:.2f}  |  '
        f'zero-lag r={zero_corr:.2f}', fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(target_name, format='png', transparent=False)
    plt.close(fig)

    d = {
        'audio_tempo_bpm': round(audio_tempo, 2),
        'motion_tempo_bpm': round(motion_tempo, 2),
        'tempo_ratio': round(ratio, 3),
        'nearest_harmonic': harm_label,
        'tempo_agreement': round(tempo_agreement, 3),
        'peak_crosscorr': round(peak_corr, 3),
        'peak_lag_s': round(peak_lag, 3),
        'zero_lag_crosscorr': round(zero_corr, 3),
        'fps': fps, 'sr': sr,
    }
    try:
        import pandas as pd
        pd.DataFrame([d]).to_csv(os.path.splitext(target_name)[0] + '.csv', index=False)
    except Exception as e:
        print(f'Warning: could not save CSV: {e}')

    mgf = MgFigure(figure=fig, figure_type='video.tempo_similarity', data=d, layers=None, image=target_name)
    self.tempo_similarity_figure = mgf
    return mgf

"""
Audio–movement comparison reports for a single performer: tools to reveal how a dancer's
movement relates to the sound — phase synchrony, structural similarity, per-body-part coupling,
and energy/dynamics coupling.

All functions are bound as ``MgVideo`` methods and return an ``MgFigure`` (with the numeric
results in ``.data``); most also save a CSV next to the image.
"""

import os
import numpy as np
import cv2
import matplotlib
import matplotlib.pyplot as plt
from musicalgestures._utils import MgFigure, generate_outfilename, resolve_filename, has_audio


def _audio_env(self, kind='onset'):
    """Return (env, times, sr): the audio onset-strength ('onset') or loudness ('rms') envelope.

    Cached on the MgVideo (keyed by filename + kind) so repeated audio–movement analyses reuse it.
    """
    import librosa
    cache = getattr(self, '_audio_env_cache', {})
    key = (self.filename, kind)
    if key in cache:
        return cache[key]
    y, sr = self._load()
    hop = self.hop_length
    if kind == 'rms':
        env = librosa.feature.rms(y=y, hop_length=hop)[0]
    else:
        env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    t = librosa.times_like(env, sr=sr, hop_length=hop)
    result = (np.asarray(env, dtype=float), np.asarray(t, dtype=float), sr)
    cache[key] = result
    self._audio_env_cache = cache
    return result


def _common_grid(t_a, a, t_m, m, fs=50.0):
    """Resample two (time, value) series onto a shared uniform grid spanning their overlap."""
    dur = min(t_a[-1] if len(t_a) else 0, t_m[-1] if len(t_m) else 0)
    if dur <= 0:
        return None, None, None
    t = np.arange(0, dur, 1.0 / fs)
    return t, np.interp(t, t_a, a), np.interp(t, t_m, m)


def _z(x):
    x = np.asarray(x, dtype=float)
    return (x - x.mean()) / (x.std() + 1e-9)


def _safe_corr(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.std() < 1e-9 or b.std() < 1e-9 or len(a) < 2:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


# ---------------------------------------------------------------------------
# 1) Phase synchrony (phase-locking value)
# ---------------------------------------------------------------------------
def mg_phase_synchrony(self, fmin=0.5, fmax=4.0, fs=50.0, n_bins=36, dpi=300,
                       autoshow=True, title=None, target_name=None, overwrite=True) -> "MgFigure":
    """
    Quantify how phase-locked the movement is to the audio rhythm.

    Both the audio onset-strength envelope and the movement quantity-of-motion envelope are
    band-pass filtered to the tempo band [``fmin``, ``fmax``] Hz, and their instantaneous phases
    (via the Hilbert transform) are compared. The **phase-locking value** (PLV, 0–1) summarises the
    consistency of the audio↔movement phase difference; a polar histogram shows its distribution.

    Returns an MgFigure (metrics in ``.data``), or None if the video has no audio.
    """
    from scipy.signal import butter, filtfilt, hilbert
    from musicalgestures._movementbeats import _movement_qom

    if not has_audio(self.filename):
        print('The video has no audio track.')
        return None

    target_name = resolve_filename(self.of, '_phase_synchrony.png', target_name, overwrite)

    oenv, t_a, sr = _audio_env(self, 'onset')
    qom, fps = _movement_qom(self)
    t_m = np.arange(len(qom)) / max(fps, 1e-9)
    t, a, m = _common_grid(t_a, oenv, t_m, qom, fs)
    if t is None or len(t) < 8:
        print('Audio and movement do not overlap enough in time.')
        return None

    ny = fs / 2.0
    b, aa = butter(2, [max(fmin, 0.01) / ny, min(fmax, ny - 0.01) / ny], btype='band')
    af = filtfilt(b, aa, _z(a))
    mf = filtfilt(b, aa, _z(m))
    pa = np.angle(hilbert(af))
    pm = np.angle(hilbert(mf))
    dphi = pm - pa
    z = np.exp(1j * dphi)
    plv = float(np.abs(np.mean(z)))
    mean_dphi = float(np.degrees(np.angle(np.mean(z))))

    fig = plt.figure(figsize=(12, 5), dpi=dpi)
    fig.patch.set_facecolor('white')
    if title == 'filename':
        title = os.path.basename(self.filename)
    fig.suptitle(title or 'Audio–movement phase synchrony', fontsize=14)

    ax1 = fig.add_subplot(1, 2, 1)
    ax1.plot(t, af, color='#1f77b4', lw=0.8, label='Audio (band-passed)')
    ax1.plot(t, mf, color='#d62728', lw=0.8, alpha=0.8, label='Movement (band-passed)')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amplitude')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.set_title(f'Tempo band {fmin}–{fmax} Hz', fontsize=10)

    ax2 = fig.add_subplot(1, 2, 2, projection='polar')
    counts, edges = np.histogram(dphi, bins=np.linspace(-np.pi, np.pi, n_bins + 1))
    centers = edges[:-1] + np.diff(edges) / 2
    cmax = counts.max() if counts.max() > 0 else 1
    ax2.bar(centers, counts, width=np.diff(edges), bottom=0.0,
            color=matplotlib.colormaps['viridis'](counts / cmax), alpha=0.85, edgecolor='none')
    ax2.plot([np.radians(mean_dphi), np.radians(mean_dphi)], [0, plv * cmax],
             color='crimson', lw=2, zorder=5)
    ax2.set_yticklabels([])
    ax2.set_title(f'Phase difference (movement − audio)\nPLV = {plv:.2f}, mean Δφ = {mean_dphi:.0f}°',
                  fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(target_name, format='png', transparent=False)
    plt.close(fig)

    d = {'plv': round(plv, 3), 'mean_phase_diff_deg': round(mean_dphi, 1),
         'fmin': fmin, 'fmax': fmax, 'fps': fps, 'sr': sr}
    mgf = MgFigure(figure=fig, figure_type='video.phase_synchrony', data=d, layers=None, image=target_name)
    self.phase_synchrony_figure = mgf
    return mgf


# ---------------------------------------------------------------------------
# 2) Structural similarity: audio SSM vs motion SSM + difference
# ---------------------------------------------------------------------------
def _ssm_from_features(feat):
    """Cosine self-similarity matrix from a (T, d) feature array, normalised to [0, 1]."""
    feat = np.asarray(feat, dtype=float)
    norm = np.linalg.norm(feat, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    unit = feat / norm
    ssm = unit @ unit.T
    lo, hi = np.nanmin(ssm), np.nanmax(ssm)
    return (ssm - lo) / (hi - lo) if hi > lo else ssm


def mg_structure_comparison(self, n=200, dpi=300, cmap='magma', autoshow=True,
                            title=None, target_name=None, overwrite=True) -> "MgFigure":
    """
    Compare the temporal **structure** of the audio with that of the movement.

    Builds a self-similarity matrix (SSM) of the audio (from MFCC frames) and of the video
    (from low-resolution frame appearance), resampled to the same ``n`` time points, and shows
    them side by side with their absolute **difference map** — bright regions in the difference
    are where the musical structure and the movement structure diverge.

    Returns an MgFigure (mean structural agreement in ``.data``), or None if the video has no audio.
    """
    import librosa

    if not has_audio(self.filename):
        print('The video has no audio track.')
        return None

    target_name = resolve_filename(self.of, '_structure_comparison.png', target_name, overwrite)

    # Audio feature matrix (MFCC) → resample to n columns
    y, sr = self._load()
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20, hop_length=self.hop_length)  # (20, Ta)
    idx_a = np.linspace(0, mfcc.shape[1] - 1, n).astype(int)
    audio_feat = mfcc[:, idx_a].T  # (n, 20)

    # Motion feature: low-res grayscale frame appearance at n evenly spaced frames
    cap = cv2.VideoCapture(self.filename)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    want = set(np.linspace(0, total - 1, min(n, total)).astype(int).tolist())
    feats, i = [], 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if i in want:
            small = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (32, 32)).astype(np.float32)
            feats.append(small.ravel())
        i += 1
    cap.release()
    motion_feat = np.array(feats) if feats else np.zeros((n, 1024))
    # Match lengths (resample motion rows to n)
    if motion_feat.shape[0] != n and motion_feat.shape[0] > 1:
        ridx = np.linspace(0, motion_feat.shape[0] - 1, n).astype(int)
        motion_feat = motion_feat[ridx]

    ssm_audio = _ssm_from_features(audio_feat)
    ssm_motion = _ssm_from_features(motion_feat)
    k = min(ssm_audio.shape[0], ssm_motion.shape[0])
    ssm_audio, ssm_motion = ssm_audio[:k, :k], ssm_motion[:k, :k]
    diff = np.abs(ssm_audio - ssm_motion)
    agreement = float(1.0 - diff.mean())

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=dpi)
    fig.patch.set_facecolor('white')
    if title == 'filename':
        title = os.path.basename(self.filename)
    fig.suptitle(title or 'Audio vs movement structural similarity', fontsize=14)
    for ax, mat, ttl, cm in zip(axes, [ssm_audio, ssm_motion, diff],
                                ['Audio SSM (MFCC)', 'Movement SSM (appearance)',
                                 f'|difference|  (agreement {agreement:.2f})'],
                                [cmap, cmap, 'inferno']):
        im = ax.imshow(mat, origin='lower', cmap=cm, aspect='equal')
        ax.set_title(ttl, fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(target_name, format='png', transparent=False)
    plt.close(fig)

    d = {'structural_agreement': round(agreement, 3), 'n': int(k), 'sr': sr}
    mgf = MgFigure(figure=fig, figure_type='video.structure_comparison', data=d, layers=None, image=target_name)
    self.structure_comparison_figure = mgf
    return mgf


# ---------------------------------------------------------------------------
# 3) Per-body-part audio coupling
# ---------------------------------------------------------------------------
def mg_body_audio_coupling(self, dpi=300, cmap='coolwarm', dot_size=260, autoshow=True,
                           title=None, target_name=None, overwrite=True, **pose_kwargs) -> "MgFigure":
    """
    Map which body parts are most rhythmically coupled to the music.

    For every pose marker the per-frame speed is correlated with the audio onset-strength
    envelope (sampled at the video frame rate). The result is shown as a body map — the average
    pose with each marker coloured by its correlation — plus a sorted bar chart, and a CSV of the
    per-marker correlations. Uses cached pose keypoints when available, otherwise runs ``pose()``
    first (``**pose_kwargs`` are forwarded).

    Returns an MgFigure (per-marker correlations in ``.data``), or None if the video has no audio.
    """
    from musicalgestures._pose_visualize import _positions_from_data

    if not has_audio(self.filename):
        print('The video has no audio track.')
        return None

    if getattr(self, '_pose_keypoints', None) is None:
        pose_kwargs.setdefault('save_video', False)
        pose_kwargs.setdefault('save_average_pose', False)
        pose_kwargs.setdefault('save_trajectories', False)
        self.pose(**pose_kwargs)
    c = self._pose_keypoints
    names, connections = c['names'], c.get('connections') or []
    width, height, fps = c['width'], c['height'], c['fps']

    target_name = resolve_filename(c['of'], '_body_audio_coupling.png', target_name, overwrite)

    coords, _ = _positions_from_data(c['data'], len(names))  # (T, n, 2) normalised
    px = coords * np.array([width, height])
    speed = np.sqrt((np.diff(px, axis=0) ** 2).sum(axis=2))   # (T-1, n) px/frame

    # Audio onset envelope sampled at the video frame times (length T), then aligned to speed.
    oenv, t_a, sr = _audio_env(self, 'onset')
    t_frames = np.arange(coords.shape[0]) / max(fps, 1e-9)
    aud_per_frame = np.interp(t_frames, t_a, oenv)[1:]  # align to diff length

    corrs = np.array([_safe_corr(np.nan_to_num(speed[:, i]), aud_per_frame) for i in range(len(names))])

    mean_px = np.nanmean(px, axis=0)
    vmax = float(np.nanmax(np.abs(corrs))) if np.isfinite(corrs).any() else 1.0
    vmax = max(vmax, 1e-6)
    cmap_obj = matplotlib.colormaps[cmap]
    norm = matplotlib.colors.Normalize(vmin=-vmax, vmax=vmax)

    fig, (axb, axbar) = plt.subplots(1, 2, figsize=(14, 7), dpi=dpi,
                                     gridspec_kw={'width_ratios': [1, 1]})
    fig.patch.set_facecolor('white')
    if title == 'filename':
        title = os.path.basename(self.filename)
    fig.suptitle(title or 'Per-body-part coupling to the music', fontsize=14)

    # Body map
    for a, b in connections:
        if a < len(names) and b < len(names) and not (np.isnan(mean_px[a]).any() or np.isnan(mean_px[b]).any()):
            axb.plot([mean_px[a, 0], mean_px[b, 0]], [mean_px[a, 1], mean_px[b, 1]],
                     color='#bbbbbb', lw=2, zorder=1)
    for i in range(len(names)):
        if not np.isnan(mean_px[i]).any():
            axb.scatter(mean_px[i, 0], mean_px[i, 1], s=dot_size, c=[cmap_obj(norm(corrs[i]))],
                        edgecolors='black', linewidths=0.6, zorder=2)
    axb.set_xlim(0, width); axb.set_ylim(height, 0); axb.set_aspect('equal'); axb.axis('off')
    axb.set_title('Body map (marker colour = correlation of speed with audio)', fontsize=10)
    fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap_obj), ax=axb,
                 fraction=0.046, pad=0.04, label='Pearson r')

    # Sorted bar chart
    order = np.argsort(corrs)
    axbar.barh(np.arange(len(names)), corrs[order],
               color=[cmap_obj(norm(corrs[o])) for o in order])
    axbar.set_yticks(np.arange(len(names)))
    axbar.set_yticklabels([names[o] for o in order], fontsize=5)
    axbar.axvline(0, color='#888888', lw=0.8)
    axbar.set_xlabel('Correlation of marker speed with audio onset (Pearson r)')
    axbar.set_title('Per-marker coupling, ranked', fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(target_name, format='png', transparent=False)
    plt.close(fig)

    stats = [{'Marker': names[i], 'Correlation': round(float(corrs[i]), 3)} for i in range(len(names))]
    try:
        import pandas as pd
        pd.DataFrame(stats).to_csv(os.path.splitext(target_name)[0] + '.csv', index=False)
    except Exception as e:
        print(f'Warning: could not save CSV: {e}')

    d = {'correlations': stats, 'mean_abs_correlation': round(float(np.nanmean(np.abs(corrs))), 3),
         'fps': fps, 'sr': sr}
    mgf = MgFigure(figure=fig, figure_type='video.body_audio_coupling', data=d, layers=None, image=target_name)
    self.body_audio_coupling_figure = mgf
    return mgf


# ---------------------------------------------------------------------------
# 4) Energy / dynamics coupling
# ---------------------------------------------------------------------------
def mg_dynamics_coupling(self, fs=50.0, max_lag=2.0, dpi=300, autoshow=True,
                         title=None, target_name=None, overwrite=True) -> "MgFigure":
    """
    Compare audio **loudness** with movement **quantity** — does the dancer move more when the
    music is louder?

    Aligns the audio RMS-loudness envelope with the quantity-of-motion envelope and reports their
    correlation (at zero lag and at the best lag within ``max_lag`` seconds). The figure overlays
    the two normalised envelopes and shows a scatter of loudness vs. motion.

    Returns an MgFigure (metrics in ``.data``), or None if the video has no audio.
    """
    from musicalgestures._movementbeats import _movement_qom

    if not has_audio(self.filename):
        print('The video has no audio track.')
        return None

    target_name = resolve_filename(self.of, '_dynamics_coupling.png', target_name, overwrite)

    rms, t_a, sr = _audio_env(self, 'rms')
    qom, fps = _movement_qom(self)
    t_m = np.arange(len(qom)) / max(fps, 1e-9)
    t, a, m = _common_grid(t_a, rms, t_m, qom, fs)
    if t is None or len(t) < 8:
        print('Audio and movement do not overlap enough in time.')
        return None
    az, mz = _z(a), _z(m)

    zero_r = _safe_corr(az, mz)
    # Best lag within +/- max_lag seconds
    max_shift = int(max_lag * fs)
    best_r, best_lag = zero_r, 0.0
    for s in range(-max_shift, max_shift + 1):
        if s < 0:
            r = _safe_corr(az[-s:], mz[:len(mz) + s])
        elif s > 0:
            r = _safe_corr(az[:len(az) - s], mz[s:])
        else:
            r = zero_r
        if r > best_r:
            best_r, best_lag = r, s / fs

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=dpi,
                                   gridspec_kw={'width_ratios': [2, 1]})
    fig.patch.set_facecolor('white')
    if title == 'filename':
        title = os.path.basename(self.filename)
    fig.suptitle(title or 'Audio loudness vs. movement quantity', fontsize=14)

    ax1.plot(t, az, color='#1f77b4', lw=0.9, label='Audio loudness (RMS)')
    ax1.plot(t, mz, color='#d62728', lw=0.9, alpha=0.8, label='Quantity of motion')
    ax1.set_xlabel('Time (s)'); ax1.set_ylabel('Normalised')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.set_title(f'Zero-lag r = {zero_r:.2f}   |   best r = {best_r:.2f} @ {best_lag:+.2f}s',
                  fontsize=10)

    ax2.scatter(az, mz, s=4, alpha=0.3, color='#444444')
    ax2.set_xlabel('Audio loudness (z)'); ax2.set_ylabel('Quantity of motion (z)')
    ax2.set_title('Loudness vs. motion', fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(target_name, format='png', transparent=False)
    plt.close(fig)

    d = {'zero_lag_corr': round(zero_r, 3), 'best_corr': round(best_r, 3),
         'best_lag_s': round(best_lag, 3), 'fps': fps, 'sr': sr}
    mgf = MgFigure(figure=fig, figure_type='video.dynamics_coupling', data=d, layers=None, image=target_name)
    self.dynamics_coupling_figure = mgf
    return mgf

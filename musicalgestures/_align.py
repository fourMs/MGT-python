"""Locating one recording inside another by sound.

Two recordings of one event share content even when they share nothing else: a second
camera in another room hearing the far end through a speaker, or a cut and re-encoded
copy of the same session. Their loudness envelopes can be correlated, and the lag that
matches them is the offset between their clocks.

**Probes, not one whole-file correlation.** A file named `Cut` may be one contiguous
excerpt or several pieces spliced together, and a single correlation cannot tell you
which. Several short windows located independently can: consistent offsets mean a
contiguous excerpt, and jumps mean internal edits --- the jumps being the edit list.

**The summary is the offset that RECURS, not the median.** A median assumes most probes
are right. Matching a recording made with clip microphones against one made with a room
microphone, most probes match nothing and land anywhere, and the middle of a list
containing nonsense is nonsense. The modal cluster is the answer, and how many probes
joined it is the confidence.

**A probe that matches nothing must say so.** Every cross-correlation has a maximum; the
maximum of noise is still a maximum, and reporting it as an offset is how an annotation
lands silently on the wrong timeline.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import fftconvolve

__all__ = ["locate_probe", "align_by_audio", "envelope_from_audio"]


def envelope_from_audio(samples, sr: float, hop_s: float = 0.05):
    """A loudness envelope: peak absolute amplitude per hop.

    Peak rather than mean, because a brief transient is exactly what makes two recordings
    of one event recognisable to each other, and a mean removes it.

    Args:
        samples: Audio, one dimension. Stereo is mixed to mono by the caller.
        sr (float): Sample rate of `samples`.
        hop_s (float): Hop length in seconds. Defaults to 0.05, a 20 Hz envelope.

    Returns:
        tuple: The envelope, and its sampling rate in frames per second.
    """
    y = np.asarray(samples, dtype=float).ravel()
    hop = max(1, int(round(hop_s * sr)))
    n = (len(y) // hop) * hop
    if n == 0:
        return np.zeros(0), sr / hop
    return np.abs(y[:n]).reshape(-1, hop).max(axis=1), sr / hop


def locate_probe(probe, reference):
    """Where `probe` best matches inside `reference`, and how well.

    The correlation is normalised over the actual overlap at every position, so a
    position where only a few samples overlap cannot score better than one where they all
    do --- an unnormalised correlation picks exactly such a position and reports a
    perfect match.

    Args:
        probe: The shorter series to locate.
        reference: The longer series to search.

    Returns:
        tuple: Index of the best position and its Pearson r, or ``(None, -1.0)`` when the
        probe has no variance to match with or is longer than the reference.
    """
    p = np.asarray(probe, dtype=float).ravel()
    s = np.asarray(reference, dtype=float).ravel()
    m, n = len(p), len(s)
    if m < 2 or n < m:
        return None, -1.0
    pc = p - p.mean()
    sd_p = pc.std()
    if sd_p == 0:
        return None, -1.0

    ones = np.ones(m)
    s_sum = fftconvolve(s, ones, mode="valid")
    s_sq = fftconvolve(s ** 2, ones, mode="valid")
    mean_s = s_sum / m
    var_s = np.maximum(s_sq / m - mean_s ** 2, 1e-12)
    num = fftconvolve(s, pc[::-1], mode="valid")
    r = num / (m * np.sqrt(var_s) * sd_p)
    best = int(np.argmax(r))
    return best, float(r[best])


def align_by_audio(cut, reference, fs: float, n_probes: int = 12,
                   probe_s: float = 30.0, min_r: float = 0.45,
                   tolerance_s: float = 0.5):
    """The offset at which `cut` sits inside `reference`, from several probes.

    Args:
        cut: Envelope of the shorter recording.
        reference: Envelope of the longer one.
        fs (float): Sampling rate of both envelopes, in frames per second.
        n_probes (int): How many windows to locate independently. Defaults to 12.
        probe_s (float): Length of each window in seconds. Defaults to 30.0.
        min_r (float): Correlation below which a probe is treated as no match rather
            than as a weak one. Defaults to 0.45.
        tolerance_s (float): How close two probe offsets must be to count as the same.
            Defaults to 0.5.

    Returns:
        tuple: ``(offset_s, mean_r, n_agreeing, n_probes)``. `offset_s` is None when no
        cluster of probes agrees, which is the correct answer for two recordings that
        have nothing in common. Add `offset_s` to a time in `cut` to get the time in
        `reference`.
    """
    c = np.asarray(cut, dtype=float).ravel()
    s = np.asarray(reference, dtype=float).ravel()
    m = int(round(probe_s * fs))
    if m < 2 or len(c) < m or len(s) < m:
        return None, 0.0, 0, 0

    starts = np.linspace(0, max(0, len(c) - m), max(1, n_probes)).astype(int)
    found = []
    for st in starts:
        pos, r = locate_probe(c[st:st + m], s)
        if pos is not None and r >= min_r:
            found.append(((pos - st) / fs, r))
    if not found:
        return None, 0.0, 0, len(starts)

    #: Cluster the offsets and take the largest cluster, not the median: probes that
    #: matched nothing are scattered, and they must not drag the answer.
    found.sort(key=lambda t: t[0])
    clusters, cur = [], [found[0]]
    for off, r in found[1:]:
        if off - cur[-1][0] <= tolerance_s:
            cur.append((off, r))
        else:
            clusters.append(cur)
            cur = [(off, r)]
    clusters.append(cur)
    best = max(clusters, key=len)
    offs = [o for o, _ in best]
    rs = [r for _, r in best]
    return float(np.mean(offs)), float(np.mean(rs)), len(best), len(starts)

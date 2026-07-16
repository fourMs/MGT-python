"""Synthetic ground-truth generators for the sound--motion analysis tests.

Adapted from the ro study's test synthesizer (Jensenius): accelerating
double-stroke pulse trains with known cycle starts, click/burst audio
rendering, and simple helpers for click trains and decaying tones.
No media fixtures are needed: every test signal is generated here.
"""
import numpy as np

SR = 22050


def click(sr=SR, f=180.0, dur=0.03):
    """A short decaying sine click."""
    t = np.arange(int(dur * sr)) / sr
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 60)).astype("float32")


def shout_burst(sr=SR, dur=0.3, f0=300.0):
    """Vowel-like harmonic stack (300-2700 Hz), like a crowd shout."""
    t = np.arange(int(dur * sr)) / sr
    y = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 10))
    y = y / np.abs(y).max()
    return (0.8 * y * np.hanning(len(t))).astype("float32")


def ro_times(ioi0=2.0, t_double=12.0, n_cycles=15, stroke_gap=0.25,
             shout_frac=0.5, gap_shrink=0.0):
    """Ground-truth event times (no audio) for an accelerating ro sequence:
    IOI(t) = ioi0 * 2**(-(t - 1.0) / t_double); each cycle is a double drum
    stroke plus one shout at shout_frac * current IOI. gap_shrink linearly
    shrinks the stroke gap to (1 - gap_shrink) * stroke_gap by the last cycle.
    gt['stroke_gap'] stays the initial gap for backward compatibility."""
    starts, t = [], 1.0
    for _ in range(n_cycles):
        starts.append(t)
        t += ioi0 * 2 ** (-(t - 1.0) / t_double)
    gt = {"starts": starts, "strokes": [], "shouts": [],
          "stroke_gap": stroke_gap}
    for k, s in enumerate(starts):
        ioi_here = ioi0 * 2 ** (-(s - 1.0) / t_double)
        frac = k / max(1, n_cycles - 1)
        gap_here = stroke_gap * (1.0 - gap_shrink * frac)
        gt["strokes"] += [s, s + gap_here]
        gt["shouts"].append(s + shout_frac * ioi_here)
    return gt


def make_ro(ioi0=2.0, t_double=12.0, n_cycles=15, stroke_gap=0.25,
            shout_frac=0.5, sr=SR, gap_shrink=0.0):
    """Render ro_times() to audio: click per stroke, vowel burst per shout."""
    gt = ro_times(ioi0, t_double, n_cycles, stroke_gap, shout_frac, gap_shrink)
    total = gt["starts"][-1] + 2.0
    y = np.zeros(int(total * sr), "float32")
    c, b = click(sr), shout_burst(sr)
    for st in gt["strokes"]:
        i0 = int(st * sr)
        y[i0:i0 + len(c)] += c
    for sh in gt["shouts"]:
        i0 = int(sh * sr)
        y[i0:i0 + len(b)] += b
    return y / max(1e-9, np.abs(y).max()), gt


def click_train(times, sr=SR, tail=0.5, **click_kw):
    """Render a click at each time (s); returns the waveform."""
    times = np.asarray(times, float)
    c = click(sr, **click_kw)
    y = np.zeros(int((times.max() + tail) * sr), "float32")
    for t in times:
        i0 = int(t * sr)
        y[i0:i0 + len(c)] += c
    return y / max(1e-9, np.abs(y).max())


def decaying_tone(t60, sr=SR, f=440.0, dur=None, onset=0.05):
    """A tone with an exact exponential decay of the given T60 (s)."""
    if dur is None:
        dur = onset + 0.8 * t60
    n = int(dur * sr)
    t = np.arange(n) / sr
    envelope = np.where(t < onset, t / onset, 10 ** (-3 * (t - onset) / t60))
    return (np.sin(2 * np.pi * f * t) * envelope).astype("float32")

"""Where laughter is in a recording, and nothing else about it.

Split the way `_voice` is split, and for the same reason: the model wrapper has no right
answer and cannot run in CI, so it is kept as thin as it can be, and the part with a right
answer is a separate function that is tested.

**Six classes, not one.** AudioSet splits laughter into `Laughter`, `Baby laughter`,
`Giggle`, `Snicker`, `Belly laugh` and `Chuckle, chortle`. Taking only the one called
`Laughter` silently discards the giggling and chuckling that a rehearsal is mostly made of.

**Why a tagger here, when `_voice` argues against one.** `_voice` rejected PANNs for
speech because a clip-level tag answers "is there speech in this minute", which is not the
question, and because dancers breathing came back as `Snort`, `Gasp`, `Animal` and `Horse`.
Both objections were about minute-long clips. Run at a two-second window on the six
laughter classes and measured against Finn Upham's 79 hand-coded annotations of this
project's corpus, it reaches **ROC AUC 0.823 against a loudness baseline's 0.741, and 91
per cent precision in the top 5 per cent of windows**. That is why laughter ships as
proposals a person confirms, and why speech does not ship from a tagger at all.

**What this does not claim.** It says where laughter probably is. It does not say who
laughed, why, or whether it was shared --- all of which a human coded for the corpus this
was validated on, and none of which is recoverable from a clip-level score.

Span assembly is `_voice.spans_from_probabilities`, not a second copy: it already closes
short gaps before dropping short bursts, and the order matters.
"""
from __future__ import annotations

import numpy as np

from musicalgestures._voice import spans_from_probabilities

__all__ = ["LAUGHTER_CLASSES", "laughter_score", "laughter_segments"]

#: AudioSet indices: Laughter, Baby laughter, Giggle, Snicker, Belly laugh,
#: Chuckle/chortle. Contiguous in the ontology, but written out rather than as a range so
#: that a change to the ontology fails loudly instead of shifting silently.
LAUGHTER_CLASSES = (16, 17, 18, 19, 20, 21)

#: PANNs' AudioSet head. A different width means a different model, and then these indices
#: point at something other than laughter.
_N_CLASSES = 527


def laughter_score(clipwise_output) -> np.ndarray:
    """One laughter score per clip, from a PANNs clipwise output.

    The strongest laughter class, not their sum. A sum lets six lukewarm classes outvote
    one confident class, and the six are not independent: a real belly laugh raises
    `Laughter` and `Belly laugh` together, and adding them counts the same event twice.

    Args:
        clipwise_output: Array of shape (n_clips, 527), as PANNs `AudioTagging.inference`
            returns.

    Returns:
        np.ndarray: One score per clip, in [0, 1].

    Raises:
        ValueError: If the second dimension is not 527.
    """
    a = np.asarray(clipwise_output, dtype=float)
    if a.ndim != 2 or a.shape[1] != _N_CLASSES:
        raise ValueError(
            f"expected a PANNs clipwise output of shape (n, {_N_CLASSES}), got {a.shape}")
    return a[:, list(LAUGHTER_CLASSES)].max(axis=1)


def laughter_segments(audio, sr: int = 32000, win_s: float = 2.0, hop_s: float = 1.0,
                      threshold: float = 0.5, min_laughter_s: float = 0.5,
                      min_silence_s: float = 0.5, device: str = "cpu",
                      checkpoint_path=None):
    """Spans where laughter is likely, for a person to confirm or delete.

    PANNs is an optional dependency, loaded here and nowhere else so that importing this
    module costs nothing.

    Args:
        audio: Mono audio, one dimension, sampled at `sr`.
        sr (int): Sample rate. PANNs wants 32000. Defaults to 32000.
        win_s (float): Analysis window in seconds. Defaults to 2.0, at which the detector
            was validated. Longer windows were what made the earlier probe on this corpus
            useless.
        hop_s (float): Step between windows. Defaults to 1.0.
        threshold (float): Score above which a window counts as laughter. Defaults to 0.5.
            Raise it for proposals somebody has to review: at the corpus's top 5 per cent
            the precision was 0.91, at the top 10 per cent it was 0.71.
        min_laughter_s (float): Spans shorter than this are dropped. Defaults to 0.5.
        min_silence_s (float): Gaps shorter than this are closed first. Defaults to 0.5.
        device (str): ``"cpu"`` or ``"cuda"``. Defaults to ``"cpu"``.
        checkpoint_path: Passed to PANNs, or None for its default.

    Returns:
        list: Actions with `source="laughter"`, each carrying its peak score in
        `features["score"]` so a reviewer can sort by confidence rather than trusting a
        threshold somebody else chose.
    """
    try:
        from panns_inference import AudioTagging
    except ImportError as exc:                                   # pragma: no cover
        raise ImportError(
            "laughter_segments needs panns-inference. Install with "
            "`pip install panns-inference`, or call laughter_score yourself on a "
            "clipwise output you already have.") from exc

    y = np.asarray(audio, dtype=np.float32).ravel()
    win, hop = int(win_s * sr), int(hop_s * sr)
    n_win = max(0, 1 + (len(y) - win) // hop)
    if n_win == 0:
        return []

    tagger = AudioTagging(checkpoint_path=checkpoint_path, device=device)
    scores = np.zeros(n_win)
    for i in range(0, n_win, 64):
        batch = np.stack([y[j * hop: j * hop + win]
                          for j in range(i, min(i + 64, n_win))])
        clipwise, _ = tagger.inference(batch)
        scores[i:i + len(batch)] = laughter_score(clipwise)

    spans = spans_from_probabilities(scores, hop_s=hop_s, threshold=threshold,
                                     min_speech_s=min_laughter_s,
                                     min_silence_s=min_silence_s, source="laughter")
    #: The window's own length is not in the hop grid, so a span ends one window late.
    for a in spans:
        a.end = min(a.end + (win_s - hop_s), len(y) / sr)
        i0, i1 = int(a.start / hop_s), max(1, int(a.end / hop_s))
        a.features["score"] = round(float(scores[i0:i1].max()), 4)
    return spans

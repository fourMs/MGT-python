"""Where speech is in a recording, and nothing else about it.

This module decides WHERE someone is speaking. It does not transcribe, and it does not
identify anyone --- both are separate decisions with separate consequences, and putting
them in one function is how a detector quietly becomes a diariser.

**Why a detector and not a tagger.** A screening probe on this corpus put PANNs and
silero-vad on the same 60 s and they disagreed: the tagger returned `Speech 0.86` for a
minute holding 1.6 s of speech, along with `Snort`, `Gasp`, `Animal` and `Horse` for
dancers breathing. A clip-level tag answers "is there speech in this minute", which is
not the question. So the detector decides where speech is, the tagger decides whether
there is music, and their disagreements are recorded rather than resolved silently.

**Why the assembly is a separate function.** `spans_from_probabilities` has a right
answer and is tested; the model wrapper has neither and is kept as thin as it can be.
"""
from __future__ import annotations

import numpy as np

from musicalgestures._actions import Action

__all__ = ["spans_from_probabilities", "speech_segments"]


def spans_from_probabilities(probs, hop_s: float, threshold: float = 0.5,
                             min_speech_s: float = 0.25,
                             min_silence_s: float = 0.5,
                             source: str = "vad") -> list[Action]:
    """Turn a per-frame speech probability into spans.

    **Silences are closed before short spans are dropped, in that order.** A single
    utterance with a breath in the middle would otherwise be discarded as two
    fragments rather than kept as one --- the same ordering `segment_actions` uses,
    and for the same reason.

    Args:
        probs: Speech probability per frame, one dimension.
        hop_s (float): Seconds per frame of `probs`.
        threshold (float): Probability counting as speech. Defaults to 0.5.
        min_speech_s (float): Spans shorter than this are dropped. Defaults to 0.25.
        min_silence_s (float): Gaps shorter than this are closed. Defaults to 0.5.
        source (str): Recorded on each Action. Defaults to "vad".

    Returns:
        list: The speech spans found, in time order. Empty for silence, which is the
        correct answer for a recording with no speech rather than an error.
    """
    p = np.asarray(probs, float).ravel()
    if p.size == 0 or hop_s <= 0:
        return []

    active = (p >= threshold).astype(np.int8)
    #: Pad both ends so a span running to the final sample still closes. Without this
    #: an utterance at the end of a recording is silently lost.
    edges = np.diff(np.concatenate(([0], active, [0])))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)

    spans = [[float(a) * hop_s, float(b) * hop_s] for a, b in zip(starts, ends)]
    if not spans:
        return []

    merged = [spans[0]]
    for s, e in spans[1:]:
        if s - merged[-1][1] < min_silence_s:
            merged[-1][1] = e
        else:
            merged.append([s, e])

    return [Action(start=s, end=e, source=source)
            for s, e in merged if e - s >= min_speech_s]


def speech_segments(audio, sr: int = 16000, threshold: float = 0.5,
                    min_speech_s: float = 0.25, min_silence_s: float = 0.5,
                    source: str = "vad") -> list[Action]:
    """Speech spans in an audio file or array, via silero-vad.

    silero-vad is an optional dependency. It is loaded here and nowhere else, so a
    machine without it can still import everything that does not detect speech.

    Args:
        audio: Path to an audio file, or a one-dimensional array already at `sr`.
        sr (int): Sample rate. silero-vad wants 16000. Defaults to 16000.
        threshold (float): Probability counting as speech.
        min_speech_s (float): Spans shorter than this are dropped.
        min_silence_s (float): Gaps shorter than this are closed.
        source (str): Recorded on each Action.

    Returns:
        list: Speech spans, in seconds on the audio's own clock.
    """
    try:
        import torch
    except ImportError as exc:                                   # pragma: no cover
        raise ImportError(
            "speech_segments needs torch and silero-vad. Install with "
            "`pip install torch silero-vad`, or call spans_from_probabilities "
            "directly if you already have a probability track.") from exc

    if isinstance(audio, (str, bytes)) or hasattr(audio, "__fspath__"):
        import librosa
        wav, sr = librosa.load(str(audio), sr=sr, mono=True)
    else:
        wav = np.asarray(audio, dtype=np.float32).ravel()
    wav = np.ascontiguousarray(wav, dtype=np.float32)

    model, _ = torch.hub.load("snakers4/silero-vad", "silero_vad", trust_repo=True)
    #: silero-vad consumes fixed windows: 512 samples at 16 kHz. The hop is therefore
    #: known exactly and is not something to infer from the output length.
    win = 512 if sr == 16000 else 256
    n = (len(wav) // win) * win
    probs = []
    with torch.no_grad():
        for i in range(0, n, win):
            probs.append(float(model(torch.from_numpy(wav[i:i + win]), sr).item()))

    return spans_from_probabilities(np.array(probs), hop_s=win / sr,
                                    threshold=threshold, min_speech_s=min_speech_s,
                                    min_silence_s=min_silence_s, source=source)

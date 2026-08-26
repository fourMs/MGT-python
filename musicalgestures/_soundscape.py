"""Bridge to ambiscape: soundscape features on the MGT time base.

MGT owns pixels, ambiscape owns samples; this adapter is the one crossing point. It runs
(or reuses) ambiscape's cached feature extraction and returns the 1 Hz series as an
MgFeatures container whose metadata carries the absolute start time, so motion and audio
series join on the wall clock. Requires ``pip install "musicalgestures[soundscape]"``.

**A video is a valid input.** The original adapter took an ambiscape session folder ---
several WAVs on one clock --- which is right when somebody recorded a place on purpose and
wrong when what you have is a video, which is what this toolbox is for. ambiscape opens a
single file as a one-take session, so a video needs only its audio pulling out first.

The part with a right answer is which of the three a path is, and `audio_source_for` is
that decision on its own so it can be tested without ffmpeg or ambiscape present. Getting
it wrong silently is how a video ends up analysed as a folder containing one thing.
"""
import datetime as dt
from pathlib import Path

import numpy as np

from musicalgestures._features import MgFeatures


#: Containers ffmpeg will be asked to pull audio out of. Anything else is refused rather
#: than handed to ffmpeg to fail on, because "unsupported extension .docx" is a better
#: error than whatever ffmpeg says about it.
_VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm", ".mpg", ".mpeg",
                   ".mts", ".m2ts", ".wmv", ".flv"}
_AUDIO_SUFFIXES = {".wav", ".flac", ".aif", ".aiff", ".mp3", ".m4a", ".ogg"}


def audio_source_for(source, audio=None):
    """What kind of input this is, and what to hand ambiscape.

    Args:
        source: a directory (an ambiscape session), a sound file, or a video.
        audio: a sound file to use instead of extracting one. The caller often already
            has it, and extracting it again is waste.

    Returns:
        tuple: ``(kind, path)`` where kind is ``"session"``, ``"file"`` or ``"extract"``.
        For ``"extract"`` the path is where the audio should be written; it does not
        exist yet, and it is deliberately not the source's own name with the suffix
        swapped, so a source that is already a sound file cannot be overwritten by its
        own extraction.

    Raises:
        FileNotFoundError: if `source` does not exist.
        ValueError: if it is a file of a kind this cannot open.
    """
    from pathlib import Path as _P

    src = _P(source)
    if not src.exists():
        raise FileNotFoundError(f"{src} does not exist")
    if audio is not None:
        return "file", _P(audio)
    if src.is_dir():
        return "session", src
    suffix = src.suffix.lower()
    if suffix in _AUDIO_SUFFIXES:
        return "file", src
    if suffix in _VIDEO_SUFFIXES:
        #: The container goes in the name. Two recordings called clip.mov and clip.mp4
        #: beside each other would otherwise both extract to clip.wav, and the second
        #: run would silently analyse the first one's audio.
        return "extract", src.with_name(f"{src.stem}{suffix[1:]}_soundscape.wav")
    raise ValueError(
        f"{src.name}: cannot take soundscape features from a {suffix or 'suffixless'} "
        f"file. Give a video, a sound file, or an ambiscape session folder.")


def soundscape_features(source, features_dir=None, audio=None,
                        sr: int = 48000) -> MgFeatures:
    """Soundscape features as an MgFeatures (1 Hz, wall-clocked).

    Args:
        source: an ambiscape session folder, a sound file, or **a video**, whose audio is
            extracted once and reused.
        features_dir: cache directory for ambiscape's .npz features
            (default: ``<source>/analysis/features`` for a folder, or beside the audio).
        audio: a sound file to use instead of extracting one from `source`.
        sr (int): Sample rate for the extraction. Defaults to 48000, which is what
            ambiscape's band measures expect; downsampling first would move the noise
            floor it reports.
    """
    import subprocess
    try:
        import ambiscape as asc
        from ambiscape import features as afeat
    except ImportError as e:
        raise ImportError(
            "ambiscape is required: pip install "
            "'musicalgestures[soundscape]'") from e

    kind, path = audio_source_for(source, audio=audio)
    if kind == "extract" and not path.exists():
        #: Once. A second call finds the file and skips this, which matters when the
        #: source is a two-hour recording on an external drive.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(Path(source)),
                        "-vn", "-ac", "1", "-ar", str(sr), str(path)], check=True)

    if kind == "session":
        sess = asc.open_session(path)
        out = Path(features_dir) if features_dir else path / "analysis" / "features"
    else:
        sess = asc.open_recording(str(path))
        out = Path(features_dir) if features_dir else path.parent / "features"
    npz = afeat.extract_session(sess, out, verbose=False)
    F = afeat.load_features(sorted(Path(p) for p in npz))

    level_db = 20 * np.log10(np.asarray(F["rms_w"], float) + 1e-12)
    day0_midnight = dt.datetime.combine(sess.day0, dt.time())
    return MgFeatures(
        {"aud_level_db": level_db},
        times=np.asarray(F["t"], float),
        sr=1.0,
        source=str(path),
        metadata={"start_datetime": day0_midnight.isoformat(),
                  "tool": "ambiscape"},
    )


def merge_into_summary(features: MgFeatures, summary_json,
                       prefix: str = "mot_"):
    """Fold feature medians/IQRs into an analysis summary.json.

    The mirror of ambiscape's ``vision --merge`` (which uses ``vis_``):
    each feature contributes ``<prefix><name>_median`` and
    ``<prefix><name>_iqr`` so one summary file describes the whole
    audio-visual session. Existing keys are preserved.
    """
    import json

    summary_json = Path(summary_json)
    doc = json.loads(summary_json.read_text()) \
        if summary_json.exists() else {}
    for name in features.feature_names:
        x = np.asarray(features[name], dtype=float)
        q25, q50, q75 = np.nanpercentile(x, [25, 50, 75])
        doc[f"{prefix}{name}_median"] = round(float(q50), 4)
        doc[f"{prefix}{name}_iqr"] = round(float(q75 - q25), 4)
    summary_json.write_text(json.dumps(doc, indent=2))
    return summary_json

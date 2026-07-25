"""Bridge to ambiscape: soundscape features on the MGT time base.

MGT owns pixels, ambiscape owns samples; this adapter is the one crossing
point. It runs (or reuses) ambiscape's cached feature extraction for a
session folder and returns the 1 Hz series as an MgFeatures container whose
metadata carries the absolute start time, so motion and audio series join
on the wall clock. Requires ``pip install "musicalgestures[soundscape]"``.
"""
import datetime as dt
from pathlib import Path

import numpy as np

from musicalgestures._features import MgFeatures


def soundscape_features(session_folder, features_dir=None) -> MgFeatures:
    """ambiscape session features as an MgFeatures (1 Hz, wall-clocked).

    Args:
        session_folder: an ambiscape session folder (WAVs on one clock).
        features_dir: cache directory for ambiscape's .npz features
            (default: ``<session_folder>/analysis/features``).
    """
    try:
        import ambiscape as asc
        from ambiscape import features as afeat
    except ImportError as e:
        raise ImportError(
            "ambiscape is required: pip install "
            "'musicalgestures[soundscape]'") from e

    session_folder = Path(session_folder)
    sess = asc.open_session(session_folder)
    out = Path(features_dir) if features_dir else \
        session_folder / "analysis" / "features"
    npz = sorted(out.glob("*.npz")) or \
        afeat.extract_session(sess, out, verbose=False)
    F = afeat.load_features(sorted(Path(p) for p in npz))

    level_db = 20 * np.log10(np.asarray(F["rms_w"], float) + 1e-12)
    day0_midnight = dt.datetime.combine(sess.day0, dt.time())
    return MgFeatures(
        {"aud_level_db": level_db},
        times=np.asarray(F["t"], float),
        sr=1.0,
        source=str(session_folder),
        metadata={"start_datetime": day0_midnight.isoformat(),
                  "tool": "ambiscape"},
    )

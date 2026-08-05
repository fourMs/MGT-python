# Soundscape

> Auto-generated documentation for [musicalgestures._soundscape](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_soundscape.py) module.

Bridge to ambiscape: soundscape features on the MGT time base.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Soundscape
    - [merge_into_summary](#merge_into_summary)
    - [soundscape_features](#soundscape_features)

MGT owns pixels, ambiscape owns samples; this adapter is the one crossing
point. It runs (or reuses) ambiscape's cached feature extraction for a
session folder and returns the 1 Hz series as an MgFeatures container whose
metadata carries the absolute start time, so motion and audio series join
on the wall clock. Requires ``pip install "musicalgestures[soundscape]"``.

## merge_into_summary

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_soundscape.py#L52)

```python
def merge_into_summary(
    features: MgFeatures,
    summary_json,
    prefix: str = 'mot_',
):
```

Fold feature medians/IQRs into an analysis summary.json.

The mirror of ambiscape's ``vision --merge`` (which uses ``vis_``):
each feature contributes ``<prefix><name>_median`` and
``<prefix><name>_iqr`` so one summary file describes the whole
audio-visual session. Existing keys are preserved.

#### See also

- [MgFeatures](_features.md#mgfeatures)

## soundscape_features

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_soundscape.py#L17)

```python
def soundscape_features(session_folder, features_dir=None) -> MgFeatures:
```

ambiscape session features as an MgFeatures (1 Hz, wall-clocked).

#### Arguments

- `session_folder` - an ambiscape session folder (WAVs on one clock).
- `features_dir` - cache directory for ambiscape's .npz features
    - `(default` - ``<session_folder>/analysis/features``).

#### See also

- [MgFeatures](_features.md#mgfeatures)

# Sync

> Auto-generated documentation for [musicalgestures._sync](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_sync.py) module.

Align recordings from different devices by their transient envelopes.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Sync
    - [align_recordings](#align_recordings)

One session, many gadgets, every clock slightly wrong: this estimates the
start-time offset between two recordings of the same scene from the
cross-correlation of their band-passed onset envelopes. Use the result to
fill ambiscape's ``calibration.json`` ``clock_offsets_s`` or to trim video
against a separate audio recorder.

## align_recordings

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_sync.py#L40)

```python
def align_recordings(
    file_a,
    file_b,
    band=(200.0, 4000.0),
    env_fs=200,
    max_lag_s=None,
):
```

Offset between two recordings of the same scene.

Returns ``{"lag_s": s, "peak": p}`` where ``lag_s`` is positive when
*file_b starts after file_a*. ``peak`` is the normalized correlation
peak; below ~0.3 the alignment is unreliable (little shared audio).
``max_lag_s`` restricts the search when a rough offset is known.

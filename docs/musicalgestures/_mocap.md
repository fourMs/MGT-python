# Mocap

> Auto-generated documentation for [musicalgestures._mocap](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mocap.py) module.

Motion-capture I/O and cross-modality utilities.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Mocap
    - [compare_modality_envelopes](#compare_modality_envelopes)
    - [dominant_frequency](#dominant_frequency)
    - [read_qtm_tsv](#read_qtm_tsv)

Pure numpy/scipy helpers ported from the "still standing" and
Westney-comparisons studies:

* :func:`read_qtm_tsv` -- a single robust reader for Qualisys Track Manager
  (QTM) TSV exports, consolidating the four/five near-duplicate loaders that
  were copy-pasted across the study scripts.
* :func:`compare_modality_envelopes` -- resample two motion envelopes onto a
  common per-second grid and correlate them (e.g. video-pose vs mocap
  validation).
* :func:`dominant_frequency` -- the dominant spectral peak of a signal within
  a band, via Welch.

#### Notes

:func:`compare_modality_envelopes` deliberately takes *precomputed* 1-D
motion envelopes rather than computing quantity-of-motion internally, so
this module stays independent of the QoM machinery. The natural producer
of such envelopes is [band_limited_qom](_qom.md#band_limited_qom) followed by
a per-second binning (``envelope`` / ``bin_series``), arriving in a
sibling PR.

Source: still standing study and Westney-comparisons study (Jensenius).

## compare_modality_envelopes

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mocap.py#L164)

```python
def compare_modality_envelopes(env_a, env_b, fs_a, fs_b):
```

Correlate two motion envelopes after resampling to a common grid.

Resamples both 1-D envelopes onto a shared one-sample-per-second grid
(by averaging within each second), truncates to the common length, and
returns the Pearson correlation -- the video-vs-mocap (or view-vs-view)
agreement measure. Both inputs are treated as already-computed motion
envelopes (e.g. per-frame band-limited quantity-of-motion), keeping this
function decoupled from the QoM computation itself. The per-second binning
uses an integer-rounded step, so non-integer frame rates (e.g. 29.97 fps)
drift slightly over long signals; this function is intended for validation
rather than precise alignment.

Source: still standing / Westney-comparisons study (Jensenius),
MediaPipe-vs-mocap validation (``compare_mp_mocap``).

#### Arguments

- `env_a` *np.ndarray* - First 1-D motion envelope.
- `env_b` *np.ndarray* - Second 1-D motion envelope.
- `fs_a` *float* - Sampling rate of ``env_a`` in Hz.
- `fs_b` *float* - Sampling rate of ``env_b`` in Hz.

#### Returns

- `dict` - ``{"r", "n"}`` where ``r`` is the Pearson correlation of the
    two per-second envelopes and ``n`` the number of common seconds
    (``r`` is ``nan`` if fewer than three overlapping seconds or if
    either resampled envelope is constant).

## dominant_frequency

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mocap.py#L130)

```python
def dominant_frequency(x, fs, band=(0.3, 4.0)):
```

Dominant frequency of a signal within a band, via a Welch spectrum.

Returns the frequency of the largest Welch power-spectral-density peak
inside ``band`` -- e.g. the dominant oscillation rate of a body-part
speed or vertical-position signal.

Source: Westney-comparisons study (Jensenius), extended motion-feature
analysis (motion dominant frequency of vertical trunk position).

#### Arguments

- `x` *np.ndarray* - 1-D input signal.
- `fs` *float* - Sampling rate in Hz.
- `band` *tuple, optional* - ``(low, high)`` search band in Hz. Defaults
    to ``(0.3, 4.0)``.

#### Returns

- `float` - The dominant frequency in Hz, or ``nan`` if the band is empty.

## read_qtm_tsv

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_mocap.py#L30)

```python
def read_qtm_tsv(path):
```

Read a Qualisys Track Manager (QTM) TSV motion-capture export.

Consolidates the several near-duplicate loaders used across the studies
into one robust reader. It locates the ``MARKER_NAMES`` header row to
recover marker labels, autodetects where the numeric data block starts
(the first row whose first field parses as a float), drops a trailing
all-empty column produced by a trailing tab, converts exact-zero XYZ
triples (Qualisys gap fills) to ``NaN``, and falls back from UTF-8 to
latin-1 encoding. When a ``FREQUENCY`` header field is present the frame
rate is returned as well.

Source: still standing study and Westney-comparisons study (Jensenius) --
unifies the ``load_qtm`` variants in the balance/dynamics/circular/
spatial-range reports and the latin-1 variant in ``compare_mp_mocap``.

#### Arguments

- `path` *str* - Path to the ``.tsv`` file.

#### Returns

- `tuple` - ``(marker_names, data, fs)`` where ``marker_names`` is a list
    of ``M`` strings (empty if no header was found), ``data`` is a
    float array of shape ``(T, M, 3)`` with gaps as ``NaN``, and
    ``fs`` is the frame rate in Hz or ``None`` if not derivable from
    the header.

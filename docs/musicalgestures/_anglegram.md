# Anglegram

> Auto-generated documentation for [musicalgestures._anglegram](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_anglegram.py) module.

Directional (azimuthal) analysis of 360 video.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Anglegram
    - [anglegram_data](#anglegram_data)
    - [load_aem](#load_aem)
    - [mg_aem_overlay](#mg_aem_overlay)
    - [mg_anglegram](#mg_anglegram)

Implements the visual *anglegram* — a time x azimuth heat map of visual
motion energy — and the Audio Energy Map (AEM) overlay, after Jinyue Guo's
PhD work in the AMBIENT project (RITMO, University of Oslo) and his ambiviz
toolbox (https://github.com/fisheggg/ambiviz). On an equirectangular frame
the horizontal pixel axis *is* the azimuth axis, so collapsing the
inter-frame difference over image rows yields motion energy per azimuth —
the visual counterpart of the audio anglegram that the sister toolbox
ambiscape computes from ambisonic recordings. Rendering both with the same
axes makes sound and motion directly comparable ("ambiscape owns the
samples, MGT owns the pixels": audio-side data enters only through files,
never through an ambiscape import).

Azimuth convention: ambisonics (ambiscape/ambiviz) measure azimuth in
degrees counterclockwise from front, so +90 is to the *left* of the camera.
An equirectangular frame centred on the front direction has the scene's
left half in the left half of the image, i.e. image x *decreases* with
ambisonic azimuth. The default ``azimuth_convention="ambisonics"`` performs
this flip so the anglegram y-axis matches ambiscape's;
``azimuth_convention="image"`` keeps azimuth increasing with image x
(-180 at the left edge, +180 at the right). Whether the flip is *correct*
for a given recording additionally depends on the camera-to-microphone
mounting; verify with a clap from a known direction.

## anglegram_data

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_anglegram.py#L41)

```python
def anglegram_data(
    frames,
    n_bins: int | None = None,
    frame_diff: bool = True,
    latitude_weighting: bool = True,
    normalize: bool = True,
    azimuth_convention: str = 'ambisonics',
):
```

Compute a visual anglegram as plain numpy arrays from a stack of
grayscale equirectangular frames: motion energy per azimuth bin over
time. This is the numpy-level counterpart of `Mg360Video.anglegram`
(like `motiongram_data` is for `MgVideo.motiongrams`); use it when the
frames are already in memory and the anglegram is wanted as data.

#### Arguments

- `frames` *np.ndarray* - Grayscale equirectangular frames of shape (T, H, W),
    full 360 degrees of longitude across the width.
- `n_bins` *int, optional* - Number of azimuth bins. Defaults to None, which
    keeps one bin per pixel column (W bins).
- `frame_diff` *bool, optional* - If True, collapse absolute inter-frame
    differences (motion); if False, collapse the frames themselves.
    Defaults to True.
- `latitude_weighting` *bool, optional* - If True, weight image rows by the
    cosine of their latitude before collapsing, compensating the polar
    oversampling of the equirectangular projection (a pixel near the
    pole covers far less solid angle than one at the equator).
    Defaults to True.
- `normalize` *bool, optional* - If True, scale the result to [0, 1] by its
    maximum. Defaults to True.
- `azimuth_convention` *str, optional* - "ambisonics" (counterclockwise from
    front, +90 = left; matches ambiscape) or "image" (azimuth increases
    with image x). See the module docstring. Defaults to "ambisonics".

#### Returns

- `np.ndarray` - The anglegram, of shape (n_bins, T-1) (T when `frame_diff`
    is False). Time runs along the second axis.
- `np.ndarray` - Azimuth bin centers in degrees, ascending, in (-180, 180).

## load_aem

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_anglegram.py#L223)

```python
def load_aem(filename: str):
```

Load an azimuthal Audio Energy Map (AEM) from a delimited text file, the
file interface through which audio-side analyses (typically ambiscape
exports) reach MGT — ambiscape is never imported.

Expected format: CSV or TSV (delimiter sniffed from the header line) with
a header row naming at least these three columns, in any order and case:

- time: `time`, `t`, or `time_s` — seconds from the start of the video.
- azimuth: `azimuth`, `az`, or `azimuth_deg` — degrees in (-180, 180],
  ambisonic convention (counterclockwise from front, +90 = left).
- energy: `energy`, `power`, `level`, or `level_db` — non-negative linear
  energy, except `level_db` which is in dB and converted to linear power
  (10^(dB/10)) on load.

The rows are samples in long format, one (time, azimuth, energy) triple
per row. They may be sparse (e.g. one dominant azimuth per second, as in
ambiscape's per-second pseudo-intensity features) or a dense time-azimuth
grid (a full AEM collapsed over elevation); [mg_aem_overlay](#mg_aem_overlay) bins them
onto its own grid either way. Extra columns are ignored.

#### Arguments

- `filename` *str* - Path to the CSV/TSV file.

#### Returns

- `dict` - {"time": np.ndarray, "azimuth": np.ndarray, "energy": np.ndarray},
    equal-length 1D arrays (linear energy).

## mg_aem_overlay

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_anglegram.py#L293)

```python
def mg_aem_overlay(
    self,
    aem_file: str,
    on: str = 'video',
    n_bins: int = 72,
    strip_height: float = 0.15,
    cmap: str = 'magma',
    alpha: float = 0.6,
    time_bin: float = 1.0,
    title: str | None = None,
    target_name: str | None = None,
    overwrite: bool = True,
    azimuth_convention: str = 'ambisonics',
):
```

Overlay an azimuthal Audio Energy Map (AEM, after Guo's ambiviz) on the
equirectangular video or on the visual anglegram, so where the *sound*
energy comes from can be read against where the *pixels* move. The audio
side enters through a file only (see [load_aem](#load_aem) for the expected CSV/TSV
format, typically exported from ambiscape) — ambiscape is not imported.

With `on='video'`, a translucent heat strip is rendered along the bottom
of every frame: horizontal position is azimuth (aligned with the
equirectangular longitude axis under the chosen convention), color is the
audio energy at that azimuth around that time. With `on='anglegram'`, the
visual anglegram is drawn and the binned AEM is overlaid on the same
time/azimuth axes as translucent filled contours.

#### Arguments

- `aem_file` *str* - Path to the AEM CSV/TSV file (see [load_aem](#load_aem)).
- `on` *str, optional* - 'video' or 'anglegram'. Defaults to 'video'.
- `n_bins` *int, optional* - Azimuth bins for the AEM grid. Defaults to 72
    (5-degree bins — ambisonic localisation is far coarser than pixels).
- `strip_height` *float, optional* - Height of the heat strip as a fraction
    of the frame height (only for `on='video'`). Defaults to 0.15.
- `cmap` *str, optional* - Matplotlib colormap for the audio energy.
    Defaults to 'magma'.
- `alpha` *float, optional* - Maximum opacity of the overlay in [0, 1].
    Defaults to 0.6.
- `time_bin` *float, optional* - Width of the AEM time bins in seconds.
    Defaults to 1.0 (ambiscape's native rate).
- `title` *str, optional* - Figure title (only for `on='anglegram'`).
    Defaults to None.
- `target_name` *str, optional* - Target output name. Defaults to None
    (input filename + "_aem.mp4" or "_anglegram_aem.png").
- `overwrite` *bool, optional* - Whether to allow overwriting existing files
    or to automatically increment target filenames. Defaults to True.
- `azimuth_convention` *str, optional* - "ambisonics" (default) or "image";
    must match how the anglegram/video is read. See module docstring.

#### Returns

- `MgVideo` - For `on='video'`, a new MgVideo of the overlaid video
    (original audio is muxed back in when present).
- `MgFigure` - For `on='anglegram'`, the combined figure
    (`figure_type='video.anglegram_aem'`).

## mg_anglegram

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_anglegram.py#L106)

```python
def mg_anglegram(
    self,
    n_bins: int = 360,
    latitude_weighting: bool = True,
    title: str | None = None,
    cmap: str = 'inferno',
    target_name: str | None = None,
    overwrite: bool = True,
    azimuth_convention: str = 'ambisonics',
) -> 'MgFigure':
```

Render the visual anglegram of an equirectangular 360 video: a time x
azimuth heat map of visual motion energy, after Guo's ambiviz. Each
column of the equirectangular inter-frame difference is collapsed
(latitude-weighted mean over image rows) into motion energy at one
azimuth, so horizontal position in the scene becomes readable as
direction. The y-axis matches the audio anglegram of the sister toolbox
ambiscape, making the two directly comparable side by side.

The video is streamed frame by frame (downscaled to `n_bins` columns
with area interpolation), so memory use is independent of duration.

#### Arguments

- `n_bins` *int, optional* - Number of azimuth bins (also the horizontal
    downscaling target). Defaults to 360 (one-degree bins).
- `latitude_weighting` *bool, optional* - Weight image rows by cos(latitude)
    to compensate the polar oversampling of the equirectangular
    projection. Defaults to True.
- `title` *str, optional* - Optionally add a title to the figure. Defaults
    to None, which uses "Anglegram (visual motion)".
- `cmap` *str, optional* - Matplotlib colormap name. Defaults to 'inferno'.
- `target_name` *str, optional* - Target output name for the figure. Defaults
    to None (which uses the input filename with the suffix "_anglegram.png").
- `overwrite` *bool, optional* - Whether to allow overwriting existing files
    or to automatically increment target filenames. Defaults to True.
- `azimuth_convention` *str, optional* - "ambisonics" (default; +90 = left,
    matches ambiscape) or "image" (azimuth increases with image x).
    See the module docstring on why this may need verifying per rig.

#### Returns

- `MgFigure` - An MgFigure object referring to the figure and its data
    (`data['anglegram']` of shape (n_bins, T-1), `data['azimuth']`,
    `data['times']`).

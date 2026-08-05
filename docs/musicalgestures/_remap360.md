# Remap360

> Auto-generated documentation for [musicalgestures._remap360](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_remap360.py) module.

Remap-table flattening for legacy 360 formats.

- [Mgt-python](../README.md#mgt-python) / [Modules](../MODULES.md#mgt-python-modules) / [Musicalgestures](index.md#musicalgestures) / Remap360
    - [flatten_gopro360](#flatten_gopro360)
    - [flatten_theta360](#flatten_theta360)
    - [gopro360_dual_fisheye_average](#gopro360_dual_fisheye_average)
    - [gopro360_to_dual_fisheye](#gopro360_to_dual_fisheye)
    - [gopro_maps](#gopro_maps)
    - [probe_gopro360](#probe_gopro360)
    - [theta_maps](#theta_maps)
    - [write_remap_pgm](#write_remap_pgm)

GoPro MAX/MAX2 .360 files store the sphere as two strips of a custom
equi-angular cubemap (EAC) that stock ffmpeg cannot unwrap; legacy Ricoh
Theta S files store two 90-degree-rotated fisheye circles in one 16:9
frame. Both become plain equirectangular through the same machinery:
numpy-generated remap tables (16-bit PGM) driving ffmpeg's `remap` filter,
with a feathered `maskedmerge` blend across the unstitched seams — the
same two-pass pattern as `stitch_dual_fisheye` in `_360video`.

The GoPro mapping is a port of Paul Bourke's max2sphere reference
(paulbourke.net/panorama/gopromax2sphere/). MAX2-resolution files are
handled by proportional template scaling and are experimental until
validated against a real recording.

#### Attributes

- `GOPRO_TEMPLATES` - (track_w, track_h) -> (centerwidth, sidewidth, blendwidth); the last 32
  (resp. 16) columns of each strip are unused padding in the real files: `{(4096, 1344): (1376, 1344, 32), (2272, 736): (768, 736, 16)}`

## flatten_gopro360

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_remap360.py#L439)

```python
def flatten_gopro360(
    path,
    target_name=None,
    width=None,
    height=None,
    crf=21,
    preset='fast',
    print_cmd=False,
):
```

Flatten a GoPro MAX/MAX2 .360 (or chunk-merged .mkv) to equirect.

vstacks the two EAC strips, runs two `remap` passes (left/right seam
samples) and blends the unstitched zones with `maskedmerge`. The best
audio stream (most channels — the ambisonic PCM track on a MAX) is
carried over as AAC. Files that are not exact GoPro templates (e.g.
MAX2) use proportionally scaled geometry and are experimental.

Geometry is validated against synthetic fixtures and the max2sphere
reference; strip order/orientation against real camera files is still
unverified.

## flatten_theta360

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_remap360.py#L532)

```python
def flatten_theta360(
    path,
    target_name=None,
    width=1920,
    height=960,
    fov_deg=191.5,
    roll_deg=(90.0, -90.0),
    crf=21,
    preset='fast',
    print_cmd=False,
):
```

Flatten a legacy Ricoh Theta S dual-fisheye MP4 to equirectangular.

Explicit invocation only: a 16:9 MP4 is not identifiable as a Theta
file by probing. Audio (mono on the Theta S) is passed through as AAC.

The 191.5-degree/±90-degree defaults are validated only against
synthetic fixtures; a real Theta S recording may need fov_deg/roll_deg
fine-tuning.

## gopro360_dual_fisheye_average

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_remap360.py#L283)

```python
def gopro360_dual_fisheye_average(
    path,
    target_name=None,
    fov=180.0,
    size=704,
    fps=2.0,
    transparent=True,
    print_cmd=False,
):
```

The time-average of a .360 as one dual-fisheye image, without writing a video first.

For a recording of somebody standing still this is the useful still: whatever held position
resolves, whatever moved smears, and a single frame cannot show either. Returns the path to a
PNG, RGBA with the area outside each circle transparent when `transparent` is set.

`fps` decimates before averaging. The mean of a stationary scene converges long before every
frame is used -- a few hundred samples is plenty -- and decoding 4K equi-angular cubemap frames
is the whole cost of this operation, so sampling at 2 Hz rather than 30 does the same job for a
fifteenth of the work. Pass `fps=None` to average every frame.

Frames are accumulated in float64 from a raw pipe rather than written out and re-read. An 8-bit
running mean over a few hundred frames loses roughly a bit of precision at the point where the
averaging is meant to be revealing motion smaller than a pixel.

`path` may be several files. GoPro splits a recording into chapters, and averaging each chapter
separately and combining the means weighted by frame count is arithmetically identical to
averaging their concatenation -- while skipping the concatenation, which for a full session is
an 8 GB lossless copy written and read back before any useful work starts.

See [gopro360_to_dual_fisheye](#gopro360_to_dual_fisheye) for what `fov` means and why it has to be recorded.

## gopro360_to_dual_fisheye

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_remap360.py#L369)

```python
def gopro360_to_dual_fisheye(
    path,
    target_name=None,
    fov=180.0,
    size=704,
    circular=True,
    crf=21,
    preset='fast',
    print_cmd=False,
):
```

Convert a GoPro MAX .360 to side-by-side fisheye circles, front then back.

The output is `2*size` by `size`: two inscribed circles of `size` pixels, the layout GoPro's
own LRV proxies use and what most dual-fisheye viewers expect.

`fov` is the angular width each circle covers, and it is a parameter to set deliberately rather
than leave at a default. At 180 degrees a circle holds exactly a hemisphere and the two together
hold the sphere with nothing to spare. Above 180 each holds more than a hemisphere, the pair
overlap, and a given real-world direction lands closer to the centre of the circle --- at 195
degrees by a factor of 180/195, about eight per cent at the rim. Two renders at different `fov`
have identical pixel dimensions and are not comparable as measurements, so anything measuring
direction or angular size in the result must record which was used.

Why this is not `v360=input=eac` on the strips. GoPro's `.360` is a custom equi-angular cubemap
that stock ffmpeg cannot unwrap: pointing `v360` at one 4096x1344 strip, or at the two stacked,
yields a plausible-looking frame with scrambled corners rather than an error. The sphere is
recovered here with the same remap tables [flatten_gopro360](#flatten_gopro360) uses, and only then projected.

`circular` masks everything outside the inscribed circle to black, which is the convention for
dual-fisheye files and what GoPro's own proxies look like. Without it `v360` fills the square
out to the corners, and those corners hold real image content at an angle wider than `fov` --
harmless to look at, wrong to measure, and enough to make two otherwise identical renders
disagree about where the image ends.

Geometry is validated against synthetic fixtures and the max2sphere reference; strip
order/orientation against real camera files is still unverified, as for [flatten_gopro360](#flatten_gopro360).

## gopro_maps

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_remap360.py#L98)

```python
def gopro_maps(
    track_w,
    track_h,
    centerwidth,
    sidewidth,
    blendwidth,
    out_w,
    out_h,
):
```

Equirect -> vstacked GoPro strips: dual sample maps + blend alpha.

Port of max2sphere's FindFaceUV/GetColour (Paul Bourke). Returns
(xmapL, ymapL, xmapR, ymapR, alpha): two source-coordinate maps into
the double-height stacked frame (strip 1 on top) and the weight of the
R sample (nonzero only in the unstitched seam zones of the four side
faces).

## probe_gopro360

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_remap360.py#L34)

```python
def probe_gopro360(path):
```

Stream inventory + strip geometry of a GoPro two-strip container.

Works on original .360 files and on chunk-merged .mkv copies. Returns
{"video": [{index,width,height} x2], "audio": [{index,codec,channels}],
"centerwidth", "sidewidth", "blendwidth", "experimental"}. Raises
ValueError naming what was found when the file does not match the
two-strip pattern.

## theta_maps

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_remap360.py#L479)

```python
def theta_maps(
    in_w,
    in_h,
    out_w,
    out_h,
    fov_deg=191.5,
    roll_deg=(90.0, -90.0),
):
```

Equirect -> Ricoh Theta S rotated dual-fisheye source coordinates.

Legacy Theta S videos hold two fisheye circles side by side, each
rotated 90 degrees in plane, in a 16:9 frame whose bottom band is
unused. Front lens = left circle (axis +y), back = right (axis -y);
equidistant fisheye model. Returns dual maps + seam-blend alpha like
[gopro_maps](#gopro_maps). fov_deg and roll_deg are tunable against a real file.

## write_remap_pgm

[[find in source code]](https://github.com/fourMs/MGT-python/blob/master/musicalgestures/_remap360.py#L78)

```python
def write_remap_pgm(xmap, ymap, tmpdir):
```

Write x/y remap tables as 16-bit binary PGMs for ffmpeg's remap.

Values are integer source-pixel coordinates; 16-bit PGM payloads are
big-endian per the Netpbm spec.

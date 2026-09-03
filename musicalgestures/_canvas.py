"""What is on the canvas, and how it grows: the painting as a time series.

A video of a painter contains two moving things: the painter, and the painting. Every other
module in the toolbox follows the first. This one follows the second, from a video --- or a
crop --- that frames the canvas: it reduces each second to one frame in which the painter's hand
has been removed by a temporal median (paint stays, a moving hand does not), and measures that
frame.

Per second: **painted share** (pixels that differ from the first seconds by more than a CIELAB
distance), a **monotone coverage** that ignores the dips occlusion causes (running lower
quantile, then cumulative maximum), **chromatic share** (saturated pixels), the **hue
histogram** whose columns make a *colourgram* --- the painting's own gram, time across, hue
down --- the **warm and cool** shares of it, **edge density** as a measure of structural detail,
and the **composition**: where the paint's mass sits, how far its left and right halves mirror
each other, and how its edges are oriented. Per minute: the dominant colours, by k-means on the
chromatic pixels.

None of this knows what the painting is *of*. It knows when paint arrived, what colour it was,
whether it added detail or covered it, and where on the surface it went, which is what a
correlation with the music can use. On the live-painting session this was written for, the
palette hardly changed across three takes while edge density rose under a leading pianist and
fell under a leading painter; the numbers said so before anyone looked.

The frame the canvas occupies should be fixed. A moving head camera needs rectification first,
which is a harder problem and not solved here.
"""
from __future__ import annotations

import os

import numpy as np

from musicalgestures._utils import MgFigure, MgImage, resolve_filename

__all__ = ["painting_content", "composition", "mg_painting"]


def composition(frame_bgr: np.ndarray, reference_lab: np.ndarray | None = None,
                paint_threshold: float = 18.0) -> dict:
    """Where the paint sits on a canvas frame, and how its structure is oriented.

    Args:
        frame_bgr: One canvas frame (BGR, uint8).
        reference_lab: The blank canvas in CIELAB (int32); when given, "paint" is what differs
            from it, otherwise every chromatic or dark pixel counts.
        paint_threshold (float): CIELAB distance that counts as paint. Defaults to 18.

    Returns:
        dict: ``mass_x``, ``mass_y`` (centre of paint, 0–1 of width/height), ``spread_x``,
        ``spread_y`` (its standard deviation, 0–1), ``symmetry_lr`` (correlation of the paint
        mask with its mirror image, 1 = symmetric), ``edge_density`` (Canny edges per pixel),
        ``edge_orientation`` (12-bin histogram of gradient orientation over edge pixels, 0–180°),
        ``anisotropy`` (how far the orientation histogram departs from flat, 0–1).
    """
    import cv2
    h, w = frame_bgr.shape[:2]
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.int32)
    if reference_lab is not None:
        mask = np.sqrt(((lab - reference_lab) ** 2).sum(-1)) > paint_threshold
    else:
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = (hsv[..., 1] > 60) | (hsv[..., 2] < 110)
    ys, xs = np.nonzero(mask)
    if len(xs) < 10:
        mass = dict(mass_x=np.nan, mass_y=np.nan, spread_x=np.nan, spread_y=np.nan, symmetry_lr=np.nan)
    else:
        m = mask.astype(float)
        mirror = m[:, ::-1]
        sym = float(np.corrcoef(m.ravel(), mirror.ravel())[0, 1]) if m.std() > 0 else np.nan
        mass = dict(mass_x=float(xs.mean() / w), mass_y=float(ys.mean() / h), spread_x=float(xs.std() / w),
                    spread_y=float(ys.std() / h), symmetry_lr=sym)
    grey = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(grey, 60, 140) > 0
    gx = cv2.Sobel(grey.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(grey.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
    ang = (np.degrees(np.arctan2(gy, gx)) % 180.0)[edges]
    hist = np.histogram(ang, bins=12, range=(0, 180))[0].astype(float)
    hist = hist / (hist.sum() + 1e-9)
    aniso = float(np.abs(hist - 1 / 12).sum() / 2)
    return {**mass, "edge_density": float(edges.mean()), "edge_orientation": hist, "anisotropy": aniso}


def painting_content(video, fps_sample: float | None = None, reference_s: float = 5.0, width: int = 200,
                     paint_threshold: float = 18.0, chroma_threshold: float = 0.25, hue_bins: int = 36,
                     palette_every_s: float = 60.0, n_colours: int = 5, warm=((0, 60), (330, 360)),
                     cool=((160, 260),)) -> dict:
    """Measure a canvas video second by second.

    Args:
        video: Path to a video framing the canvas (a fixed crop works best).
        fps_sample (float, optional): Unused placeholder for API symmetry; one measurement per
            second is always produced from the median of that second's frames.
        reference_s (float): Seconds at the start taken as the blank (or initial) canvas.
        width (int): Working width in pixels. Defaults to 200.
        paint_threshold (float): CIELAB distance from the reference counting as paint.
        chroma_threshold (float): HSV saturation (0–1) above which a pixel is chromatic.
        hue_bins (int): Bins of the hue histogram. Defaults to 36 (10° each).
        palette_every_s (float): Interval of the dominant-colour palette. Defaults to 60 s.
        n_colours (int): Colours per palette entry. Defaults to 5.
        warm, cool: Hue ranges in degrees counted as warm and cool.

    Returns:
        dict: ``t`` (bin centres), ``painted``, ``coverage`` (monotone), ``chromatic``,
        ``saturation``, ``brightness``, ``warm``, ``cool``, ``edge_density``, ``hue_hist``
        (hue_bins, n) sharing of chromatic pixels per hue, ``composition`` (dict of per-second
        arrays from :func:`composition`), ``palette`` (list of ``{"t", "colours": [(r, g, b,
        share), ...]}``), ``frames`` (the per-second median frames, BGR, for montages).
    """
    import cv2
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    per = max(int(round(fps)), 1)
    buf, secs = [], []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        h, w = fr.shape[:2]
        s = width / max(w, 1)
        buf.append(cv2.resize(fr, (max(int(w * s) // 2 * 2, 2), max(int(h * s) // 2 * 2, 2))))
        if len(buf) >= per:
            secs.append(np.median(np.array(buf), axis=0).astype(np.uint8))
            buf = []
    cap.release()
    if buf:
        secs.append(np.median(np.array(buf), axis=0).astype(np.uint8))
    secs = np.array(secs)
    n = len(secs)
    if n == 0:
        raise ValueError(f"{video} yielded no frames")
    hsv = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in secs])
    H = hsv[..., 0].astype(float) * 2.0
    S = hsv[..., 1] / 255.0
    V = hsv[..., 2] / 255.0
    lab = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.int32) for f in secs])
    ref = np.median(lab[:max(int(reference_s), 1)], axis=0).astype(np.int32)
    painted = (np.sqrt(((lab - ref) ** 2).sum(-1)) > paint_threshold).mean(axis=(1, 2))
    q = np.array([np.quantile(painted[max(0, i - 7):i + 8], 0.1) for i in range(n)])
    coverage = np.maximum.accumulate(q)
    chromatic_mask = S > chroma_threshold
    hist = np.zeros((hue_bins, n))
    for i in range(n):
        hh = H[i][chromatic_mask[i]]
        if len(hh):
            hist[:, i] = np.histogram(hh, bins=hue_bins, range=(0, 360))[0] / chromatic_mask[i].size
    centres = (np.arange(hue_bins) + 0.5) * 360.0 / hue_bins
    in_ranges = lambda ranges: np.array([any(lo <= c < hi for lo, hi in ranges) for c in centres])  # noqa: E731
    warm_share = hist[in_ranges(warm)].sum(0)
    cool_share = hist[in_ranges(cool)].sum(0)
    comp = [composition(f, ref, paint_threshold) for f in secs]
    comp_arrays = {k: np.array([c[k] for c in comp]) for k in ("mass_x", "mass_y", "spread_x", "spread_y", "symmetry_lr", "edge_density", "anisotropy")}
    comp_arrays["edge_orientation"] = np.array([c["edge_orientation"] for c in comp]).T
    palette = []
    for m in range(0, n, max(int(palette_every_s), 1)):
        j = min(m + int(palette_every_s) - 1, n - 1)
        px = secs[j].reshape(-1, 3).astype(np.float32)
        msk = chromatic_mask[j].reshape(-1)
        px = px[msk] if msk.sum() > 200 else px
        if len(px) < 50:
            continue
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(px, min(n_colours, len(px)), None, crit, 3, cv2.KMEANS_PP_CENTERS)
        share = np.bincount(labels.ravel(), minlength=len(centers)) / len(labels)
        cols = [(int(centers[k][2]), int(centers[k][1]), int(centers[k][0]), float(share[k])) for k in np.argsort(share)[::-1]]
        palette.append({"t": float(j + 0.5), "colours": cols})
    return {
        "t": np.arange(n) + 0.5, "painted": painted, "coverage": coverage, "chromatic": chromatic_mask.mean(axis=(1, 2)),
        "saturation": S.mean(axis=(1, 2)), "brightness": V.mean(axis=(1, 2)), "warm": warm_share, "cool": cool_share,
        "edge_density": comp_arrays["edge_density"], "hue_hist": hist, "hue_centres": centres,
        "composition": comp_arrays, "palette": palette, "frames": secs,
    }


def colourgram_image(content: dict, gamma: float = 0.5) -> np.ndarray:
    """The colourgram as an RGB image (hue down, time across), coloured by hue, bright by share."""
    import matplotlib
    hist = content["hue_hist"]
    hue_rgb = matplotlib.colormaps["hsv"](np.linspace(0, 1, hist.shape[0]))[:, :3]
    hn = hist / (hist.max() + 1e-9)
    img: np.ndarray = np.clip((hn ** gamma)[:, :, None] * hue_rgb[:, None, :], 0, 1)
    return img[::-1]


def mg_painting(self, reference_s: float = 5.0, width: int = 200, dpi: int = 110, title: str | None = None,
                save_data: bool = True, target_name: str | None = None, target_name_data: str | None = None,
                target_name_colourgram: str | None = None, overwrite: bool = True) -> MgFigure:
    """Measure the painting in this video (the video should frame the canvas) and draw it.

    Args:
        reference_s (float): Seconds at the start taken as the initial canvas. Defaults to 5.
        width (int): Working width in pixels. Defaults to 200.
        dpi (int): Figure resolution.
        title (str, optional): Figure title.
        save_data (bool): Write the per-second table as CSV. Defaults to True.
        target_name (str, optional): Figure path. Defaults to ``"_painting.png"`` beside the video.
        target_name_data (str, optional): CSV path. Defaults to ``"_painting.csv"``.
        target_name_colourgram (str, optional): Raw colourgram path. Defaults to ``"_colourgram.png"``.
        overwrite (bool): Overwrite or auto-increment. Defaults to True.

    Returns:
        MgFigure: With the content dict in ``.data``; also stored as ``self.painting_figure``,
        the colourgram as ``self.colourgram_image`` and the table as ``self.painting``.
    """
    import matplotlib
    import matplotlib.pyplot as plt
    content = painting_content(self.filename, reference_s=reference_s, width=width)
    t = content["t"]
    img = colourgram_image(content)
    cg = resolve_filename(self.of, "_colourgram.png", target_name_colourgram, overwrite)
    matplotlib.image.imsave(cg, img)
    self.colourgram_image = MgImage(cg)
    fig, axs = plt.subplots(3, 1, figsize=(16, 8), sharex=True, dpi=dpi, gridspec_kw={"height_ratios": [2, 1.2, 1.2]})
    axs[0].imshow(img, aspect="auto", extent=[0, t[-1] + 0.5, 0, 360], interpolation="nearest")
    axs[0].set_ylabel("hue (°)"); axs[0].set_title(title or f"{os.path.basename(self.of)}: colourgram and painting content")
    axs[1].plot(t, content["coverage"], lw=1.5, label="coverage (monotone)"); axs[1].plot(t, content["painted"], lw=.5, alpha=.4, label="painted share")
    axs[1].plot(t, content["chromatic"], lw=1.2, label="chromatic share"); axs[1].plot(t, content["edge_density"] * 5, lw=1.2, label="edge density (x5)")
    axs[1].set_ylim(0, 1); axs[1].legend(fontsize=8, ncol=4); axs[1].set_ylabel("fraction")
    axs[2].plot(t, content["warm"], lw=1.2, color="#D9534F", label="warm hues"); axs[2].plot(t, content["cool"], lw=1.2, color="#3B6FB6", label="cool hues")
    axs[2].plot(t, content["saturation"], lw=1, color="grey", label="mean saturation"); axs[2].plot(t, content["composition"]["mass_y"], lw=1, color="black", ls="--", label="paint centre (y, 0 = top)")
    axs[2].legend(fontsize=8, ncol=4); axs[2].set_ylabel("fraction"); axs[2].set_xlabel("time (s)")
    fig.tight_layout()
    path = resolve_filename(self.of, "_painting.png", target_name, overwrite)
    fig.savefig(path); plt.close(fig)
    if save_data:
        import pandas as pd
        df = pd.DataFrame({"time": t, **{k: content[k] for k in ("painted", "coverage", "chromatic", "saturation", "brightness", "warm", "cool", "edge_density")},
                           **{k: content["composition"][k] for k in ("mass_x", "mass_y", "spread_x", "spread_y", "symmetry_lr", "anisotropy")}})
        for k in range(content["hue_hist"].shape[0]):
            df[f"hue_{int(content['hue_centres'][k] - 5):03d}"] = content["hue_hist"][k]
        dp = resolve_filename(self.of, "_painting.csv", target_name_data, overwrite)
        df.to_csv(dp, index=False, float_format="%.4f")
        self.painting = df
    result = MgFigure(figure=fig, figure_type="video.painting", data={k: v for k, v in content.items() if k != "frames"}, layers=None, image=path)
    self.painting_figure = result
    return result

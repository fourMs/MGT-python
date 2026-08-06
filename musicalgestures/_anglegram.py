"""Directional (azimuthal) analysis of 360 video.

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
"""
from __future__ import annotations

import csv
import os

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

from musicalgestures._utils import (MgFigure, MgProgressbar, ffmpeg_cmd,
                                    get_length, has_audio, resolve_filename)
from musicalgestures._motionanalysis import motiongram_data


def anglegram_data(frames, n_bins: int | None = None, frame_diff: bool = True,
                   latitude_weighting: bool = True, normalize: bool = True,
                   azimuth_convention: str = "ambisonics"):
    """
    Compute a visual anglegram as plain numpy arrays from a stack of
    grayscale equirectangular frames: motion energy per azimuth bin over
    time. This is the numpy-level counterpart of `Mg360Video.anglegram`
    (like `motiongram_data` is for `MgVideo.motiongrams`); use it when the
    frames are already in memory and the anglegram is wanted as data.

    Args:
        frames (np.ndarray): Grayscale equirectangular frames of shape (T, H, W),
            full 360 degrees of longitude across the width.
        n_bins (int, optional): Number of azimuth bins. Defaults to None, which
            keeps one bin per pixel column (W bins).
        frame_diff (bool, optional): If True, collapse absolute inter-frame
            differences (motion); if False, collapse the frames themselves.
            Defaults to True.
        latitude_weighting (bool, optional): If True, weight image rows by the
            cosine of their latitude before collapsing, compensating the polar
            oversampling of the equirectangular projection (a pixel near the
            pole covers far less solid angle than one at the equator).
            Defaults to True.
        normalize (bool, optional): If True, scale the result to [0, 1] by its
            maximum. Defaults to True.
        azimuth_convention (str, optional): "ambisonics" (counterclockwise from
            front, +90 = left; matches ambiscape) or "image" (azimuth increases
            with image x). See the module docstring. Defaults to "ambisonics".

    Returns:
        np.ndarray: The anglegram, of shape (n_bins, T-1) (T when `frame_diff`
            is False). Time runs along the second axis.
        np.ndarray: Azimuth bin centers in degrees, ascending, in (-180, 180).
    """
    frames = np.asarray(frames, dtype=np.float32)
    if frames.ndim != 3:
        raise ValueError("anglegram_data expects frames of shape (T, H, W)")
    if azimuth_convention not in ("ambisonics", "image"):
        raise ValueError("azimuth_convention must be 'ambisonics' or 'image'")
    T, H, W = frames.shape
    if latitude_weighting:
        lat = (0.5 - (np.arange(H) + 0.5) / H) * np.pi   # +pi/2 top .. -pi/2
        w = np.cos(lat).astype(np.float32)
        frames = frames * (w / w.mean())[None, :, None]
    gram = motiongram_data(frames, orientation="horizontal",
                           frame_diff=frame_diff, normalize=False)  # (W, T')
    if n_bins is not None and n_bins != W:
        if W % n_bins == 0:
            gram = gram.reshape(n_bins, W // n_bins, -1).mean(axis=1)
        else:
            idx = (np.arange(W) * n_bins) // W
            out = np.zeros((n_bins, gram.shape[1]), dtype=gram.dtype)
            cnt = np.bincount(idx, minlength=n_bins).astype(gram.dtype)
            np.add.at(out, idx, gram)
            gram = out / cnt[:, None]
    nb = gram.shape[0]
    az = (np.arange(nb) + 0.5) / nb * 360.0 - 180.0      # image convention
    if azimuth_convention == "ambisonics":
        az = -az[::-1]
        gram = gram[::-1]
    if normalize:
        gram = gram / (gram.max() + 1e-12)
    return gram, az


def mg_anglegram(self, n_bins: int = 360, latitude_weighting: bool = True,
                 title: str | None = None, cmap: str = 'inferno',
                 target_name: str | None = None, overwrite: bool = True,
                 azimuth_convention: str = "ambisonics") -> "MgFigure":
    """
    Render the visual anglegram of an equirectangular 360 video: a time x
    azimuth heat map of visual motion energy, after Guo's ambiviz. Each
    column of the equirectangular inter-frame difference is collapsed
    (latitude-weighted mean over image rows) into motion energy at one
    azimuth, so horizontal position in the scene becomes readable as
    direction. The y-axis matches the audio anglegram of the sister toolbox
    ambiscape, making the two directly comparable side by side.

    The video is streamed frame by frame (downscaled to `n_bins` columns
    with area interpolation), so memory use is independent of duration.

    Args:
        n_bins (int, optional): Number of azimuth bins (also the horizontal
            downscaling target). Defaults to 360 (one-degree bins).
        latitude_weighting (bool, optional): Weight image rows by cos(latitude)
            to compensate the polar oversampling of the equirectangular
            projection. Defaults to True.
        title (str, optional): Optionally add a title to the figure. Defaults
            to None, which uses "Anglegram (visual motion)".
        cmap (str, optional): Matplotlib colormap name. Defaults to 'inferno'.
        target_name (str, optional): Target output name for the figure. Defaults
            to None (which uses the input filename with the suffix "_anglegram.png").
        overwrite (bool, optional): Whether to allow overwriting existing files
            or to automatically increment target filenames. Defaults to True.
        azimuth_convention (str, optional): "ambisonics" (default; +90 = left,
            matches ambiscape) or "image" (azimuth increases with image x).
            See the module docstring on why this may need verifying per rig.

    Returns:
        MgFigure: An MgFigure object referring to the figure and its data
            (`data['anglegram']` of shape (n_bins, T-1), `data['azimuth']`,
            `data['times']`).
    """
    from musicalgestures._360video import Projection
    if getattr(self, "projection", Projection.equirect) != Projection.equirect:
        raise ValueError(
            f"anglegram requires an equirectangular video, got projection "
            f"'{self.projection}'. Run convert_projection('equirect') first.")

    vidcap = cv2.VideoCapture(self.filename)
    fps = vidcap.get(cv2.CAP_PROP_FPS) or self.fps
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ds_h = min(height, 256)      # collapse target; keeps latitudes resolved

    if latitude_weighting:
        lat = (0.5 - (np.arange(ds_h) + 0.5) / ds_h) * np.pi
        row_w = np.cos(lat).astype(np.float32)
        row_w /= row_w.mean()
    else:
        row_w = np.ones(ds_h, dtype=np.float32)

    pb = MgProgressbar(total=length, prefix='Rendering anglegram:')
    columns, prev = [], None
    i = 0
    while vidcap.isOpened():
        ret, frame = vidcap.read()
        if not ret:
            pb.progress(length)
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (n_bins, ds_h),
                           interpolation=cv2.INTER_AREA).astype(np.float32)
        if prev is not None:
            diff = np.abs(small - prev)
            columns.append(row_w @ diff / ds_h)       # (n_bins,)
        prev = small
        pb.progress(i)
        i += 1
    vidcap.release()

    gram = np.array(columns).T                        # (n_bins, T-1)
    gram = gram / (gram.max() + 1e-12)
    az = (np.arange(n_bins) + 0.5) / n_bins * 360.0 - 180.0
    if azimuth_convention == "ambisonics":
        az = -az[::-1]
        gram = gram[::-1]
    elif azimuth_convention != "image":
        raise ValueError("azimuth_convention must be 'ambisonics' or 'image'")
    times = (np.arange(gram.shape[1]) + 1) / fps

    fig, ax = plt.subplots(figsize=(12, 4), dpi=300)
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)
    if title is None:
        title = 'Anglegram (visual motion)'
    fig.suptitle(title, fontsize=16)
    ax.imshow(gram, extent=[0, times[-1] if len(times) else 1, az[0] - 180.0 / n_bins,
                            az[-1] + 180.0 / n_bins],
              origin='lower', norm=colors.PowerNorm(gamma=1.0 / 2.0),
              aspect='auto', cmap=cmap)
    ax.set_yticks([-180, -90, 0, 90, 180])
    ax.set_ylabel('Azimuth [Degrees]')
    ax.set_xlabel('Time [Seconds]')

    target_name = resolve_filename(self.of, '_anglegram.png', target_name, overwrite)
    plt.savefig(target_name, format='png', transparent=False)
    plt.close()

    data = {
        "FPS": fps,
        "path": self.of,
        "times": times,
        "azimuth": az,
        "anglegram": gram,
        "azimuth_convention": azimuth_convention,
    }
    mgf = MgFigure(figure=fig, figure_type='video.anglegram', data=data,
                   layers=None, image=target_name)
    return mgf


def load_aem(filename: str):
    """
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
    grid (a full AEM collapsed over elevation); `mg_aem_overlay` bins them
    onto its own grid either way. Extra columns are ignored.

    Args:
        filename (str): Path to the CSV/TSV file.

    Returns:
        dict: {"time": np.ndarray, "azimuth": np.ndarray, "energy": np.ndarray},
            equal-length 1D arrays (linear energy).
    """
    aliases = {"time": ("time", "t", "time_s"),
               "azimuth": ("azimuth", "az", "azimuth_deg"),
               "energy": ("energy", "power", "level", "level_db")}
    with open(filename, newline='') as f:
        head = f.readline()
        delim = '\t' if head.count('\t') >= head.count(',') else ','
        header = [c.strip().lower() for c in head.strip().split(delim)]
        cols = {}
        for key, names in aliases.items():
            for name in names:
                if name in header:
                    cols[key] = (header.index(name), name)
                    break
            if key not in cols:
                raise ValueError(
                    f"AEM file {filename} has no '{key}' column "
                    f"(accepted names: {names}); header was {header}")
        rows = [r for r in csv.reader(f, delimiter=delim) if r and any(r)]
    out = {}
    for key, (idx, name) in cols.items():
        out[key] = np.array([float(r[idx]) for r in rows])
        if key == "energy" and name == "level_db":
            out[key] = 10.0 ** (out[key] / 10.0)
    return out


def _bin_aem(aem: dict, t_edges: np.ndarray, az_edges: np.ndarray) -> np.ndarray:
    """Accumulate long-format AEM samples onto a (n_az, n_t) grid by summing
    energy into the enclosing (azimuth, time) cell. Samples outside the time
    range are dropped; azimuths are wrapped into (-180, 180]."""
    t, az, e = aem["time"], aem["azimuth"], aem["energy"]
    az = ((np.asarray(az) + 180.0) % 360.0) - 180.0
    n_t, n_az = len(t_edges) - 1, len(az_edges) - 1
    keep = (t >= t_edges[0]) & (t < t_edges[-1])
    ti = np.clip(np.searchsorted(t_edges, t[keep], side='right') - 1, 0, n_t - 1)
    ai = np.clip(np.searchsorted(az_edges, az[keep], side='right') - 1, 0, n_az - 1)
    H = np.zeros((n_az, n_t))
    np.add.at(H, (ai, ti), e[keep])
    return H


def mg_aem_overlay(self, aem_file: str, on: str = 'video',
                   n_bins: int = 72, strip_height: float = 0.15,
                   cmap: str = 'magma', alpha: float = 0.6,
                   time_bin: float = 1.0, title: str | None = None,
                   target_name: str | None = None, overwrite: bool = True,
                   azimuth_convention: str = "ambisonics"):
    """
    Overlay an azimuthal Audio Energy Map (AEM, after Guo's ambiviz) on the
    equirectangular video or on the visual anglegram, so where the *sound*
    energy comes from can be read against where the *pixels* move. The audio
    side enters through a file only (see `load_aem` for the expected CSV/TSV
    format, typically exported from ambiscape) — ambiscape is not imported.

    With `on='video'`, a translucent heat strip is rendered along the bottom
    of every frame: horizontal position is azimuth (aligned with the
    equirectangular longitude axis under the chosen convention), color is the
    audio energy at that azimuth around that time. With `on='anglegram'`, the
    visual anglegram is drawn and the binned AEM is overlaid on the same
    time/azimuth axes as translucent filled contours.

    Args:
        aem_file (str): Path to the AEM CSV/TSV file (see `load_aem`).
        on (str, optional): 'video' or 'anglegram'. Defaults to 'video'.
        n_bins (int, optional): Azimuth bins for the AEM grid. Defaults to 72
            (5-degree bins — ambisonic localisation is far coarser than pixels).
        strip_height (float, optional): Height of the heat strip as a fraction
            of the frame height (only for `on='video'`). Defaults to 0.15.
        cmap (str, optional): Matplotlib colormap for the audio energy.
            Defaults to 'magma'.
        alpha (float, optional): Maximum opacity of the overlay in [0, 1].
            Defaults to 0.6.
        time_bin (float, optional): Width of the AEM time bins in seconds.
            Defaults to 1.0 (ambiscape's native rate).
        title (str, optional): Figure title (only for `on='anglegram'`).
            Defaults to None.
        target_name (str, optional): Target output name. Defaults to None
            (input filename + "_aem.mp4" or "_anglegram_aem.png").
        overwrite (bool, optional): Whether to allow overwriting existing files
            or to automatically increment target filenames. Defaults to True.
        azimuth_convention (str, optional): "ambisonics" (default) or "image";
            must match how the anglegram/video is read. See module docstring.

    Returns:
        MgVideo: For `on='video'`, a new MgVideo of the overlaid video
            (original audio is muxed back in when present).
        MgFigure: For `on='anglegram'`, the combined figure
            (`figure_type='video.anglegram_aem'`).
    """
    aem = load_aem(aem_file)
    az_edges = np.linspace(-180.0, 180.0, n_bins + 1)
    duration = get_length(self.filename)
    n_t = max(1, int(np.ceil(duration / time_bin)))
    t_edges = np.arange(n_t + 1) * time_bin
    H = _bin_aem(aem, t_edges, az_edges)               # (n_az, n_t), ambisonic az
    H = H / (H.max() + 1e-12)

    if on == 'anglegram':
        mgf = self.anglegram(azimuth_convention=azimuth_convention,
                             overwrite=overwrite)
        fig, ax = plt.subplots(figsize=(12, 4), dpi=300)
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)
        gram, az, times = (mgf.data['anglegram'], mgf.data['azimuth'],
                          mgf.data['times'])
        ax.imshow(gram, extent=[0, times[-1], az[0], az[-1]], origin='lower',
                  norm=colors.PowerNorm(gamma=1.0 / 2.0), aspect='auto',
                  cmap='gray')
        az_plot = az_edges if azimuth_convention == "ambisonics" else -az_edges[::-1]
        Hp = H if azimuth_convention == "ambisonics" else H[::-1]
        tc = (t_edges[:-1] + t_edges[1:]) / 2
        ac = (az_plot[:-1] + az_plot[1:]) / 2
        ax.contourf(tc, ac, Hp, levels=np.linspace(0.05, 1.0, 8),
                    cmap=cmap, alpha=alpha)
        ax.set_yticks([-180, -90, 0, 90, 180])
        ax.set_ylabel('Azimuth [Degrees]')
        ax.set_xlabel('Time [Seconds]')
        fig.suptitle(title or 'Anglegram (visual motion, gray) + AEM (audio, color)',
                     fontsize=16)
        target_name = resolve_filename(self.of, '_anglegram_aem.png',
                                       target_name, overwrite)
        plt.savefig(target_name, format='png', transparent=False)
        plt.close()
        data = dict(mgf.data)
        data.update({"aem": H, "aem_time_edges": t_edges,
                     "aem_azimuth_edges": az_edges})
        return MgFigure(figure=fig, figure_type='video.anglegram_aem',
                        data=data, layers=None, image=target_name)

    elif on == 'video':
        target_name = resolve_filename(self.of, '_aem.mp4', target_name, overwrite)

        vidcap = cv2.VideoCapture(self.filename)
        fps = vidcap.get(cv2.CAP_PROP_FPS) or self.fps
        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        strip_px = max(2, int(round(height * strip_height)))

        # precompute one BGR strip row + alpha row per time bin:
        # image x = azimuth; ambisonic azimuth decreases with x (flip), image
        # convention increases with x
        colormap = plt.get_cmap(cmap)
        xs = (np.arange(width) + 0.5) / width * 360.0 - 180.0   # image az
        az_of_x = -xs if azimuth_convention == "ambisonics" else xs
        xi = np.clip(np.searchsorted(az_edges, az_of_x, side='right') - 1,
                     0, n_bins - 1)
        strip_rgba = colormap(H[xi, :].T)                       # (n_t, W, 4)
        strip_bgr = (strip_rgba[:, :, 2::-1] * 255).astype(np.float32)
        strip_alpha = (alpha * H[xi, :].T).astype(np.float32)[:, :, None]

        cmd = ['ffmpeg', '-y', '-s', f'{width}x{height}', '-r', str(fps),
               '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo',
               '-i', '-', '-i', self.filename, '-map', '0:v']
        if has_audio(self.filename):
            cmd += ['-map', '1:a:0', '-c:a', 'aac']
        cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-shortest',
                target_name]
        process = ffmpeg_cmd(cmd, total_time=length, pipe='write')

        pb = MgProgressbar(total=length, prefix='Rendering AEM overlay:')
        i = 0
        while vidcap.isOpened():
            ret, frame = vidcap.read()
            if not ret:
                pb.progress(length)
                break
            ti = min(int(i / fps / time_bin), n_t - 1)
            band = frame[height - strip_px:, :, :].astype(np.float32)
            a = strip_alpha[ti]
            band = band * (1 - a) + strip_bgr[ti] * a
            frame[height - strip_px:, :, :] = band.astype(np.uint8)
            process.stdin.write(frame.astype(np.uint8).tobytes())
            pb.progress(i)
            i += 1
        vidcap.release()
        process.stdin.close()
        process.wait()

        from musicalgestures._video import MgVideo
        return MgVideo(target_name, returned_by_process=True)

    else:
        raise ValueError("on must be 'video' or 'anglegram'")

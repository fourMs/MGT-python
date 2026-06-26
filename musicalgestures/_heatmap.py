import numpy as np
import os
import cv2
import matplotlib
from musicalgestures._utils import MgImage, MgProgressbar, generate_outfilename


def mg_heatmap(
        self,
        colormap='inferno',
        overlay=True,
        alpha=0.75,
        background_dim=0.4,
        blur=0,
        normalize=True,
        gamma=0.5,
        target_name=None,
        overwrite=False):
    """
    Renders a motion heatmap showing which parts of the video change the most.

    The function accumulates the absolute pixel difference between consecutive frames
    over the whole video, producing a single image where bright/hot regions mark areas
    of frequent or large change and dark/cool regions mark areas that stay still. When
    ``overlay`` is True the heat is composited on top of a dimmed average frame, so the
    activity is shown in the spatial context of the scene.

    Args:
        colormap (str, optional): Any matplotlib colormap name used to colour the heat
            (e.g. 'inferno', 'jet', 'viridis', 'hot', 'magma'). Defaults to 'inferno'.
        overlay (bool, optional): If True, composite the heatmap over a dimmed grayscale
            average frame so the motion is shown in context. If False, render the bare
            heatmap on a black background. Defaults to True.
        alpha (float, optional): Maximum opacity of the heat overlay in [0, 1]. Hotter
            pixels are more opaque. Only used when ``overlay=True``. Defaults to 0.75.
        background_dim (float, optional): Brightness multiplier for the average-frame
            background in [0, 1]. Lower values make the heat stand out more. Only used
            when ``overlay=True``. Defaults to 0.4.
        blur (int, optional): Radius of an optional Gaussian smoothing applied to the
            accumulated motion (0 disables). Gives a smoother, less speckled heatmap.
            Defaults to 0.
        normalize (bool, optional): If True, scale the accumulated motion so the most
            active pixel maps to the top of the colormap. Defaults to True.
        gamma (float, optional): Gamma applied to the normalised heat before colouring.
            Values < 1 boost faint motion so subtle activity is visible; 1.0 is linear.
            Defaults to 0.5.
        target_name (str, optional): The name of the output image. Defaults to None
            (which uses the input filename with the suffix "_heatmap.png").
        overwrite (bool, optional): Whether to allow overwriting existing files or to
            automatically increment the target filename to avoid overwriting.
            Defaults to False.

    Returns:
        MgImage: A new MgImage pointing to the output heatmap image file.
    """

    if target_name is None:
        target_name = f"{self.of}_heatmap.png"
    else:
        # enforce png
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    cap = cv2.VideoCapture(self.filename)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    accum = np.zeros((height, width), dtype=np.float64)      # accumulated motion
    bg_accum = np.zeros((height, width, 3), dtype=np.float64)  # for the average frame (RGB)
    prev_gray = None
    n = 0

    pb = MgProgressbar(total=total_frames, prefix='Rendering motion heatmap:')

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            bg_accum += frame[..., ::-1].astype(np.float64)  # BGR -> RGB
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
            if prev_gray is not None:
                accum += np.abs(gray - prev_gray)
            prev_gray = gray
            n += 1
            pb.progress(n)
    finally:
        cap.release()

    pb.progress(total_frames)

    if n == 0:
        raise RuntimeError(f"Could not read any frames from {self.filename}.")

    avg_frame = (bg_accum / n).astype(np.uint8)

    # Optional smoothing of the accumulated motion
    if blur and blur > 0:
        k = int(blur) * 2 + 1
        accum = cv2.GaussianBlur(accum, (k, k), 0)

    # Normalise to [0, 1]
    if normalize and accum.max() > 0:
        heat = accum / accum.max()
    else:
        heat = np.clip(accum, 0, 1)

    # Gamma boost so subtle motion stays visible
    if gamma and gamma != 1.0:
        heat = np.power(heat, gamma)

    # Colour-map the heat (RGB, uint8)
    cmap = matplotlib.colormaps[colormap]
    heat_rgb = (cmap(heat)[..., :3] * 255).astype(np.float64)

    if overlay:
        # Dimmed grayscale average frame as background
        gray_bg = cv2.cvtColor(avg_frame, cv2.COLOR_RGB2GRAY)
        gray_bg3 = np.stack([gray_bg] * 3, axis=-1).astype(np.float64) * background_dim
        # Hotter pixels are more opaque
        a = (heat[..., None] * alpha)
        out = gray_bg3 * (1 - a) + heat_rgb * a
    else:
        out = heat_rgb

    out = np.clip(out, 0, 255).astype(np.uint8)

    # cv2 writes BGR
    cv2.imwrite(target_name, out[..., ::-1])

    # NB: store under a non-shadowing attribute so the heatmap() method stays callable
    self.heatmap_image = MgImage(target_name)
    return self.heatmap_image

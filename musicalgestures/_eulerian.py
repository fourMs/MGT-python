import os
import numpy as np
import cv2
import musicalgestures
from musicalgestures._utils import MgProgressbar, generate_outfilename, resolve_filename, ffmpeg_cmd


# ---------------------------------------------------------------------------
# Pyramid helpers
# ---------------------------------------------------------------------------

def _gaussian_top(frame, levels):
    """Return the top (smallest) level of a Gaussian pyramid."""
    out = frame
    for _ in range(levels):
        out = cv2.pyrDown(out)
    return out


def _laplacian_pyramid(frame, levels):
    """Return a Laplacian pyramid as a list: [lap_0, ..., lap_{levels-1}, gaussian_residual]."""
    gauss = [frame]
    for _ in range(levels):
        gauss.append(cv2.pyrDown(gauss[-1]))
    pyr = []
    for i in range(levels):
        up = cv2.pyrUp(gauss[i + 1], dstsize=(gauss[i].shape[1], gauss[i].shape[0]))
        pyr.append(gauss[i] - up)
    pyr.append(gauss[-1])
    return pyr


def _reconstruct_from_laplacian(pyr):
    """Collapse a Laplacian pyramid (as produced by _laplacian_pyramid) back to an image."""
    out = pyr[-1]
    for lap in reversed(pyr[:-1]):
        out = cv2.pyrUp(out, dstsize=(lap.shape[1], lap.shape[0])) + lap
    return out


def _ideal_bandpass(stack, fps, freq_low, freq_high):
    """Zero out temporal frequencies outside [freq_low, freq_high] via FFT along axis 0."""
    fft = np.fft.fft(stack, axis=0)
    frequencies = np.fft.fftfreq(stack.shape[0], d=1.0 / fps)
    mask = (np.abs(frequencies) >= freq_low) & (np.abs(frequencies) <= freq_high)
    fft[~mask] = 0
    return np.real(np.fft.ifft(fft, axis=0))


# ---------------------------------------------------------------------------
# Main method
# ---------------------------------------------------------------------------

def mg_eulerian(
        self,
        mode='color',
        freq_low=0.83,
        freq_high=1.0,
        amplification=50,
        levels=4,
        chroma_attenuation=1.0,
        lambda_cutoff=16,
        target_name=None,
        overwrite=True) -> "musicalgestures.MgVideo":
    """
    Applies Eulerian Video Magnification (EVM) to reveal subtle changes in a video.

    EVM amplifies small temporal variations that are normally invisible. Two modes are
    available:

    * ``mode='color'`` — amplifies subtle **colour** changes (e.g. blood flow / pulse,
      breathing). Uses a Gaussian pyramid and an ideal (FFT) temporal band-pass filter.
      Processed in two passes so only a small down-sampled stack is held in memory.
    * ``mode='motion'`` — amplifies subtle **motion**. Uses a Laplacian pyramid with a
      streaming IIR temporal band-pass filter and spatial-wavelength attenuation, so it
      runs frame-by-frame with low memory use.

    Based on Wu et al., "Eulerian Video Magnification for Revealing Subtle Changes in the
    World" (SIGGRAPH 2012).

    Args:
        mode (str, optional): 'color' or 'motion'. Defaults to 'color'.
        freq_low (float, optional): Lower temporal cutoff in Hz. Defaults to 0.83 (~50 bpm).
        freq_high (float, optional): Upper temporal cutoff in Hz. Defaults to 1.0 (~60 bpm).
        amplification (float, optional): Amplification factor (alpha). Defaults to 50.
        levels (int, optional): Number of spatial pyramid levels. Defaults to 4.
        chroma_attenuation (float, optional): Chrominance attenuation in [0, 1] (color mode).
            Lower values reduce colour artefacts. Defaults to 1.0.
        lambda_cutoff (float, optional): Spatial wavelength cutoff for amplitude attenuation
            (motion mode). Defaults to 16.
        target_name (str, optional): Target output name. Defaults to None (input filename with
            the suffix "_evm").
        overwrite (bool, optional): Whether to allow overwriting or auto-increment the filename.
            Defaults to True.

    Returns:
        MgVideo: An MgVideo pointing to the magnified output video.
    """
    of, fex = os.path.splitext(self.filename)
    target_name = resolve_filename(of, '_evm' + fex, target_name, overwrite)

    mode = mode.lower()
    width, height, fps = self.width, self.height, self.fps
    # NB: for MgVideo, self.length is the frame count, not seconds.
    n_frames = self.length
    duration_s = self.length / fps if fps else 0

    def _open_reader():
        cmd = ['ffmpeg', '-y', '-i', self.filename]
        return ffmpeg_cmd(cmd, total_time=duration_s, pipe='read')

    def _open_writer():
        cmd = ['ffmpeg', '-y', '-s', f'{width}x{height}', '-r', str(fps), '-f', 'rawvideo',
               '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', '-i', '-',
               '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', target_name]
        return ffmpeg_cmd(cmd, total_time=duration_s, pipe='write')

    frame_bytes = width * height * 3

    if mode == 'color':
        # ---- Pass 1: collect the small Gaussian level for every frame ----
        pb = MgProgressbar(total=n_frames * 2, prefix='EVM (color):')
        process = _open_reader()
        small_stack = []
        i = 0
        while True:
            buf = process.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            frame = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3).astype(np.float32)
            small_stack.append(_gaussian_top(frame, levels))
            i += 1
            pb.progress(i)

        if len(small_stack) < 2:
            raise RuntimeError(f"Not enough frames in {self.filename} for EVM.")

        stack = np.stack(small_stack, axis=0)
        del small_stack

        # Temporal band-pass + amplification
        filtered = _ideal_bandpass(stack, fps, freq_low, freq_high)
        filtered[..., 0] *= amplification                       # B
        filtered[..., 1] *= amplification * chroma_attenuation  # G
        filtered[..., 2] *= amplification * chroma_attenuation  # R
        del stack

        # ---- Pass 2: add upsampled magnified signal back, write out ----
        process = _open_reader()
        writer = _open_writer()
        i = 0
        while True:
            buf = process.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            frame = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3).astype(np.float32)
            mag = cv2.resize(filtered[i], (width, height))
            out = np.clip(frame + mag, 0, 255).astype(np.uint8)
            writer.stdin.write(out.tobytes())
            i += 1
            pb.progress(n_frames + i)
        writer.stdin.close()
        writer.wait()
        pb.progress(n_frames * 2)

    elif mode == 'motion':
        # ---- Streaming Laplacian-pyramid IIR band-pass ----
        pb = MgProgressbar(total=n_frames, prefix='EVM (motion):')
        process = _open_reader()
        writer = _open_writer()

        lowpass1 = None
        lowpass2 = None
        # IIR cutoffs derived from the requested band
        r1 = freq_high * 2.0 / fps
        r2 = freq_low * 2.0 / fps
        exaggeration = 2.0
        i = 0
        while True:
            buf = process.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            frame = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3).astype(np.float32)
            pyr = _laplacian_pyramid(frame, levels)

            if lowpass1 is None:
                lowpass1 = [lvl.copy() for lvl in pyr]
                lowpass2 = [lvl.copy() for lvl in pyr]
                filtered = [np.zeros_like(lvl) for lvl in pyr]
            else:
                for k in range(len(pyr)):
                    lowpass1[k] = (1 - r1) * lowpass1[k] + r1 * pyr[k]
                    lowpass2[k] = (1 - r2) * lowpass2[k] + r2 * pyr[k]
                    filtered[k] = lowpass1[k] - lowpass2[k]

            # Spatial-wavelength dependent amplification (attenuate top & bottom levels)
            delta = lambda_cutoff / 8.0 / (1.0 + amplification)
            lambda_repr = (width ** 2 + height ** 2) ** 0.5 / 3.0
            amplified = []
            for k in range(len(pyr)):
                if k == 0 or k == len(pyr) - 1:
                    amplified.append(np.zeros_like(pyr[k]))
                else:
                    curr_alpha = lambda_repr / delta / 8.0 - 1.0
                    curr_alpha *= exaggeration
                    alpha_k = min(amplification, max(0.0, curr_alpha))
                    amplified.append(pyr[k] + filtered[k] * alpha_k)
                lambda_repr /= 2.0
            # Keep the residual (bottom) and finest (top) unamplified for stability
            amplified[-1] = pyr[-1]
            amplified[0] = pyr[0]

            out = _reconstruct_from_laplacian(amplified)
            out = np.clip(out, 0, 255).astype(np.uint8)
            writer.stdin.write(out.tobytes())
            i += 1
            pb.progress(i)

        writer.stdin.close()
        writer.wait()
        pb.progress(n_frames)

    else:
        raise ValueError(f"Unknown mode '{mode}'. Use 'color' or 'motion'.")

    self.eulerian_video = musicalgestures.MgVideo(target_name, color=self.color, returned_by_process=True)
    return self.eulerian_video

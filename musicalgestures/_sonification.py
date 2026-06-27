import os
import numpy as np
import cv2
import musicalgestures
from musicalgestures._utils import MgProgressbar, generate_outfilename, ffmpeg_cmd


def mg_sonomotiongram(
        self,
        sonogram='vertical',
        n_fft=2048,
        sr=22050,
        n_iter=32,
        flip=True,
        normalize=True,
        target_name=None,
        overwrite=True):
    """
    Creates a *sonomotiongram*: a sonification of the video's motiongram.

    The motiongram (a time–space image of where motion happens) is treated as a magnitude
    spectrogram — spatial position maps to frequency, motion intensity to amplitude — and
    converted back to audio with an inverse STFT (Griffin–Lim phase estimation). The result
    lets you *hear* the motion. Based on Jensenius, "Some video abstraction techniques for
    displaying body movement in analysis and performance" / sonomotiongrams (SMC 2013).

    Args:
        sonogram (str, optional): Which motiongram to sonify: 'vertical' (motion across the
            vertical axis) or 'horizontal'. Defaults to 'vertical'.
        n_fft (int, optional): FFT size; sets the number of frequency bins (n_fft//2+1) the
            motiongram rows are mapped onto. Defaults to 2048.
        sr (int, optional): Sample rate of the rendered audio. Defaults to 22050.
        n_iter (int, optional): Griffin–Lim iterations for phase estimation (higher = cleaner,
            slower). Defaults to 32.
        flip (bool, optional): If True, map the top of the image to high frequencies (usually
            more intuitive). Defaults to True.
        normalize (bool, optional): Normalise the rendered audio to peak 1.0. Defaults to True.
        target_name (str, optional): Output audio filename. Defaults to None (input filename
            with the suffix "_sono_<sonogram>.wav").
        overwrite (bool, optional): Whether to allow overwriting or auto-increment the filename.
            Defaults to True.

    Returns:
        MgAudio: An MgAudio pointing to the rendered sonification (WAV).
    """
    import librosa

    sonogram = sonogram.lower()
    if sonogram not in ('vertical', 'horizontal'):
        raise ValueError("sonogram must be 'vertical' or 'horizontal'.")

    if target_name is None:
        target_name = f"{self.of}_sono_{sonogram}.wav"
    else:
        target_name = os.path.splitext(target_name)[0] + '.wav'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    width, height, fps = self.width, self.height, self.fps
    # NB: for MgVideo, self.length is the frame count, not seconds.
    duration_s = self.length / fps if fps else 0
    frame_bytes = width * height * 3

    # --- Build the motiongram (magnitude over time) from frame differences ---
    cmd = ['ffmpeg', '-y', '-i', self.filename]
    process = ffmpeg_cmd(cmd, total_time=duration_s, pipe='read')
    pb = MgProgressbar(total=self.length, prefix='Building motiongram for sonification:')

    columns = []
    prev_gray = None
    n = 0
    while True:
        buf = process.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        frame = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev_gray is not None:
            motion = np.abs(gray - prev_gray)
            if sonogram == 'vertical':
                columns.append(motion.mean(axis=1))   # length H (vertical position)
            else:
                columns.append(motion.mean(axis=0))   # length W (horizontal position)
        prev_gray = gray
        n += 1
        pb.progress(n)
    pb.progress(self.length)

    if len(columns) < 2:
        raise RuntimeError(f"Not enough frames in {self.filename} to build a sonomotiongram.")

    gram = np.stack(columns, axis=1)  # shape (space, time)
    if flip:
        gram = gram[::-1, :]

    # --- Treat the motiongram as a magnitude spectrogram and invert it ---
    n_freq = n_fft // 2 + 1
    n_time = gram.shape[1]
    # Map spatial rows -> frequency bins
    mag = cv2.resize(gram.astype(np.float32), (n_time, n_freq), interpolation=cv2.INTER_LINEAR)

    # Scale magnitudes to a useful range
    if mag.max() > 0:
        mag = mag / mag.max()

    # Choose hop so the audio duration matches the video duration
    total_samples = int(sr * duration_s)
    hop_length = max(1, total_samples // n_time)

    y = librosa.griffinlim(mag, n_iter=n_iter, hop_length=hop_length, win_length=n_fft, n_fft=n_fft)

    if normalize:
        peak = np.max(np.abs(y))
        if peak > 0:
            y = y / peak

    # Write the WAV
    try:
        import soundfile as sf
        sf.write(target_name, y.astype(np.float32), sr)
    except Exception:
        from scipy.io import wavfile
        wavfile.write(target_name, sr, (y * 32767).astype(np.int16))

    self.sonomotiongram = musicalgestures.MgAudio(target_name, sr=sr)
    return self.sonomotiongram

import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
from musicalgestures._utils import MgFigure, MgProgressbar, generate_outfilename


def mg_motiontempo(self, fmin=0.2, fmax=8.0, dpi=300, autoshow=True, title=None, target_name=None, overwrite=False):
    """
    Estimates the dominant movement tempo of a video from its quantity of motion.

    A quantity-of-motion (QoM) signal is computed as the mean absolute difference
    between consecutive frames. Its dominant periodicity within ``[fmin, fmax]`` is
    found with an FFT and reported both in Hz and in beats per minute (BPM), giving a
    simple estimate of the overall movement tempo (e.g. step rate of a dancer).

    Args:
        fmin (float, optional): Lowest movement frequency to consider (Hz). Defaults to 0.2.
        fmax (float, optional): Highest movement frequency to consider (Hz). Defaults to 8.0.
        dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
        autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
        title (str, optional): Optionally add a title to the figure. Use 'filename' for the file name. Defaults to None.
        target_name (str, optional): The name of the output image. Defaults to None
            (which uses the input filename with the suffix "_motiontempo.png").
        overwrite (bool, optional): Whether to allow overwriting existing files or to
            automatically increment the target filename. Defaults to False.

    Returns:
        MgFigure: An MgFigure object. Numeric results are available in ``.data``:
            'tempo_bpm', 'dominant_frequency', 'qom', 'times', 'freqs', 'spectrum', 'fps'.
    """
    from musicalgestures._analysis import dominant_frequency

    if target_name is None:
        target_name = self.of + '_motiontempo.png'
    else:
        target_name = os.path.splitext(target_name)[0] + '.png'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    cap = cv2.VideoCapture(self.filename)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or self.fps

    qom = []
    prev_gray = None
    pb = MgProgressbar(total=total_frames, prefix='Computing movement tempo:')
    n = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
            if prev_gray is not None:
                qom.append(float(np.abs(gray - prev_gray).mean()))
            prev_gray = gray
            n += 1
            pb.progress(n)
    finally:
        cap.release()
    pb.progress(total_frames)

    qom = np.asarray(qom, dtype=float)
    if len(qom) < 4:
        raise RuntimeError(f"Not enough frames in {self.filename} to estimate movement tempo.")

    times = np.arange(len(qom)) / fps

    # Dominant movement frequency and its spectrum within [fmin, fmax]
    dom_freq = dominant_frequency(qom, fps, fmin=fmin, fmax=fmax)
    tempo_bpm = dom_freq * 60.0

    freqs = np.fft.rfftfreq(len(qom), d=1.0 / fps)
    spectrum = np.abs(np.fft.rfft(qom - qom.mean()))

    fig, ax = plt.subplots(nrows=2, figsize=(12, 6), dpi=dpi)
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1)

    if title is None:
        title = ''
    if title == 'filename':
        title = os.path.basename(self.filename)
    fig.suptitle(title, fontsize=16)

    ax[0].plot(times, qom, color='#1f77b4', lw=0.8)
    ax[0].set(title='Quantity of motion', xlabel='Time (s)', ylabel='QoM')
    ax[0].set_xlim(0, times[-1] if len(times) else 1)

    mask = (freqs >= fmin) & (freqs <= fmax)
    ax[1].plot(freqs[mask], spectrum[mask], color='#ff7f0e', lw=0.9)
    if dom_freq > 0:
        ax[1].axvline(dom_freq, color='r', ls='--',
                      label=f'{dom_freq:.2f} Hz = {tempo_bpm:.1f} BPM')
        ax[1].legend()
    ax[1].set(title='Movement spectrum', xlabel='Frequency (Hz)', ylabel='Magnitude')
    ax[1].set_xlim(fmin, fmax)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(target_name, format='png', transparent=False)
    plt.close(fig)

    data = {
        'tempo_bpm': tempo_bpm,
        'dominant_frequency': dom_freq,
        'qom': qom,
        'times': times,
        'freqs': freqs,
        'spectrum': spectrum,
        'fps': fps,
    }

    mgf = MgFigure(
        figure=fig,
        figure_type='video.motiontempo',
        data=data,
        layers=None,
        image=target_name)

    return mgf

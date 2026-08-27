"""Synthetic ground-truth generators for the sound--motion analysis tests.

Adapted from the ro study's test synthesizer (Jensenius): accelerating
double-stroke pulse trains with known cycle starts, click/burst audio
rendering, and simple helpers for click trains and decaying tones.
No media fixtures are needed: every test signal is generated here.
"""
import numpy as np

SR = 22050


def click(sr=SR, f=180.0, dur=0.03):
    """A short decaying sine click."""
    t = np.arange(int(dur * sr)) / sr
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 60)).astype("float32")


def shout_burst(sr=SR, dur=0.3, f0=300.0):
    """Vowel-like harmonic stack (300-2700 Hz), like a crowd shout."""
    t = np.arange(int(dur * sr)) / sr
    y = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 10))
    y = y / np.abs(y).max()
    return (0.8 * y * np.hanning(len(t))).astype("float32")


def ro_times(ioi0=2.0, t_double=12.0, n_cycles=15, stroke_gap=0.25,
             shout_frac=0.5, gap_shrink=0.0):
    """Ground-truth event times (no audio) for an accelerating ro sequence:
    IOI(t) = ioi0 * 2**(-(t - 1.0) / t_double); each cycle is a double drum
    stroke plus one shout at shout_frac * current IOI. gap_shrink linearly
    shrinks the stroke gap to (1 - gap_shrink) * stroke_gap by the last cycle.
    gt['stroke_gap'] stays the initial gap for backward compatibility."""
    starts, t = [], 1.0
    for _ in range(n_cycles):
        starts.append(t)
        t += ioi0 * 2 ** (-(t - 1.0) / t_double)
    gt = {"starts": starts, "strokes": [], "shouts": [],
          "stroke_gap": stroke_gap}
    for k, s in enumerate(starts):
        ioi_here = ioi0 * 2 ** (-(s - 1.0) / t_double)
        frac = k / max(1, n_cycles - 1)
        gap_here = stroke_gap * (1.0 - gap_shrink * frac)
        gt["strokes"] += [s, s + gap_here]
        gt["shouts"].append(s + shout_frac * ioi_here)
    return gt


def make_ro(ioi0=2.0, t_double=12.0, n_cycles=15, stroke_gap=0.25,
            shout_frac=0.5, sr=SR, gap_shrink=0.0):
    """Render ro_times() to audio: click per stroke, vowel burst per shout."""
    gt = ro_times(ioi0, t_double, n_cycles, stroke_gap, shout_frac, gap_shrink)
    total = gt["starts"][-1] + 2.0
    y = np.zeros(int(total * sr), "float32")
    c, b = click(sr), shout_burst(sr)
    for st in gt["strokes"]:
        i0 = int(st * sr)
        y[i0:i0 + len(c)] += c
    for sh in gt["shouts"]:
        i0 = int(sh * sr)
        y[i0:i0 + len(b)] += b
    return y / max(1e-9, np.abs(y).max()), gt


def click_train(times, sr=SR, tail=0.5, **click_kw):
    """Render a click at each time (s); returns the waveform."""
    times = np.asarray(times, float)
    c = click(sr, **click_kw)
    y = np.zeros(int((times.max() + tail) * sr), "float32")
    for t in times:
        i0 = int(t * sr)
        y[i0:i0 + len(c)] += c
    return y / max(1e-9, np.abs(y).max())


def decaying_tone(t60, sr=SR, f=440.0, dur=None, onset=0.05):
    """A tone with an exact exponential decay of the given T60 (s)."""
    if dur is None:
        dur = onset + 0.8 * t60
    n = int(dur * sr)
    t = np.arange(n) / sr
    envelope = np.where(t < onset, t / onset, 10 ** (-3 * (t - onset) / t60))
    return (np.sin(2 * np.pi * f * t) * envelope).astype("float32")


def moving_block_video(path, dx=4, dy=0, frames=40, size=(320, 240), block=48,
                       fps=25, noise=0):
    """An H.264 clip of one textured block translating by an exact (dx, dy) per frame.

    Motion vectors are a claim about displacement, so testing them needs footage whose
    displacement is known rather than a clip of somebody dancing. The block is textured
    rather than flat because a uniform square gives the encoder no reason to prefer the
    true displacement to any other, and a flat block's vectors are arbitrary.

    The background is textured and static, which is not decoration. Over a uniformly flat
    background every candidate vector predicts a block equally well, so the encoder picks
    whichever is cheapest to code --- the one its neighbours used --- and the moving
    block's vector propagates across the empty part of the frame. On a flat background
    the vectors below spread from the block all the way to the bottom edge. Real rooms
    have detail, and so does this one.

    Encoded with the same H.264 settings a real recording would use, since the vectors
    under test are the encoder's own decisions and an all-intra file has none.
    """
    import subprocess
    import numpy as np

    W, H = size
    rng = np.random.default_rng(0)
    texture = rng.integers(0, 255, size=(block, block), dtype=np.uint8)
    background = rng.integers(48, 160, size=(H, W), dtype=np.uint8)
    #: Centre the whole trajectory rather than starting at a corner, so the block is in
    #: shot for every frame whichever way it travels. Starting at a fixed corner let a
    #: leftward-moving block leave the frame a quarter of the way in, and the frames it
    #: was absent for read as no motion and dragged the measured displacement to zero.
    x0 = (W - block) // 2 - dx * frames // 2
    y0 = (H - block) // 2 - dy * frames // 2
    raw = bytearray()
    for i in range(frames):
        frame = background.copy()
        if noise:
            frame = np.clip(frame.astype(np.int16)
                            + rng.integers(-noise, noise + 1, (H, W)), 0, 255
                            ).astype(np.uint8)
        x = x0 + dx * i
        y = y0 + dy * i
        if 0 <= x <= W - block and 0 <= y <= H - block:
            frame[y:y + block, x:x + block] = texture
        raw += frame.tobytes()

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "pipe:0",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "12", str(path)],
        input=bytes(raw), check=True)
    return str(path)


def intra_only_video(path, frames=12, size=(160, 120), fps=25):
    """An all-intra clip, which carries no motion vectors at all."""
    import subprocess
    import numpy as np

    W, H = size
    rng = np.random.default_rng(1)
    raw = b"".join(rng.integers(0, 255, (H, W), dtype=np.uint8).tobytes()
                   for _ in range(frames))
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "pipe:0",
         "-c:v", "mjpeg", str(path)],
        input=raw, check=True)
    return str(path)


def oscillating_block_video(path, amplitude=40, period=12, frames=96, size=(320, 240),
                            block=48, fps=25):
    """A block that goes back and forth, so its direction cancels but its motion does not.

    The counterpart to `moving_block_video`: both leave the same amount of movement in
    the same place, and only one of them has a consistent direction. Anything claiming to
    measure directional coherence has to tell them apart.
    """
    import subprocess
    import numpy as np

    W, H = size
    rng = np.random.default_rng(0)
    texture = rng.integers(0, 255, size=(block, block), dtype=np.uint8)
    background = rng.integers(48, 160, size=(H, W), dtype=np.uint8)
    x0, y0 = (W - block) // 2, (H - block) // 2
    raw = bytearray()
    for i in range(frames):
        frame = background.copy()
        x = int(x0 + amplitude * np.sin(2 * np.pi * i / period))
        x = max(0, min(W - block, x))
        frame[y0:y0 + block, x:x + block] = texture
        raw += frame.tobytes()
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "pipe:0",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "12", str(path)],
        input=bytes(raw), check=True)
    return str(path)

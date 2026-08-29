"""One self-contained page that zooms from a whole session down to a single action.

The stated aim for this toolbox's dance corpus included "the ability to zoom from the whole
session down to a single action, and preparation for manual annotation". What existed was
three printed scales over a thirteen-level pyramid that could have supported any scale.
This closes that gap, and it is the only interactive thing in the toolbox.

**Self-contained, or it is not a deliverable.** The page has to work from a folder somebody
was emailed, with no server and no network. So the videogram is embedded as an image and
the motion envelope and the annotations as numbers, and the page reads nothing at runtime.

**How much to embed is a decision with a right answer.** Too little and the page cannot
resolve the gestures it exists to show; too much and it will not open. `embed_budget` makes
that trade explicit and the page states the resolution it actually achieved, so nobody
mistakes a smooth curve for a still moment.

**Min and max per bucket, never a mean.** The same rule as every other figure here: a brief
movement is what an overview exists to find, and a mean is what removes it.
"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import numpy as np

__all__ = ["decimate_minmax_pairs", "embed_budget", "zoomable_page"]


def decimate_minmax_pairs(x, n_buckets: int):
    """The lowest and highest value in each of `n_buckets` equal slices.

    Both extremes, because a single brief spike is exactly what a zoomed-out view must not
    lose, and any average removes it.

    Args:
        x: The series.
        n_buckets (int): How many buckets to reduce it to.

    Returns:
        tuple: (lows, highs). A series shorter than `n_buckets` is returned unchanged in
        both, since asking for more detail than exists must not invent any.
    """
    a = np.asarray(x, dtype=float).ravel()
    if len(a) == 0:
        return np.zeros(0), np.zeros(0)
    n = max(1, int(n_buckets))
    if len(a) <= n:
        return a.copy(), a.copy()
    edges: np.ndarray = np.linspace(0, len(a), n + 1).astype(int)
    lo = np.empty(n)
    hi = np.empty(n)
    for i in range(n):
        seg = a[edges[i]:max(edges[i] + 1, edges[i + 1])]
        lo[i], hi[i] = seg.min(), seg.max()
    return lo, hi


def embed_budget(duration_s: float, max_points: int = 8000) -> dict:
    """How many points to embed, and what resolution that buys.

    Args:
        duration_s (float): Length of the recording.
        max_points (int): Ceiling on embedded points. Defaults to 8000, which is a few
            hundred kilobytes of JSON and about 1.2 s per point on a two-hour recording.

    Returns:
        dict: `n_points` and `seconds_per_point`, the second being what the page must
        state: a viewer who zooms past it is looking at interpolation, not data.
    """
    n = max(1, int(max_points))
    return {"n_points": n, "seconds_per_point": float(duration_s) / n}


def _array_png(X, cmap="magma", origin="lower"):
    """A (rows, time) array as a base64 PNG, for the page to scale."""
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt

    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[None, :]
    if X.shape[0] > X.shape[1]:
        X = X.T                                   # rows are the spatial axis
    fig = plt.figure(figsize=(X.shape[1] / 100, max(1.0, X.shape[0] / 100)), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.axis("off")
    ax.imshow(X, aspect="auto", cmap=cmap, origin=origin)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _videogram_png(analysis_dir, duration_s, width, which="videogram_v", start_s=0.0):
    """The cached videogram as a base64 PNG, for the page to scale."""
    from musicalgestures._tracks import read_columns

    cols, _ = read_columns(analysis_dir, start_s, start_s + duration_s,
                           max_columns=width, which=which)
    return _array_png(cols)


def _audio_strips(audio, n_points, width):
    """The audio as the page's two representations: waveform pairs and a spectrogram.

    The waveform keeps the min and max of the signed signal per bucket, normalised to
    [-1, 1], for the same reason the motion envelope does: a single transient is what a
    zoomed-out view must not lose. The spectrogram is a log-mel image, low frequencies
    at the bottom, on the same clock as everything else.
    """
    import librosa

    wave, sr = librosa.load(str(audio), sr=8000, mono=True)
    lo, hi = decimate_minmax_pairs(wave, n_points)
    scale = max(float(np.abs(lo).max(initial=0.0)),
                float(np.abs(hi).max(initial=0.0)), 1e-9)
    hop = max(1, len(wave) // max(width, 1))
    mel = librosa.feature.melspectrogram(y=wave, sr=sr, n_mels=96, hop_length=hop)
    db = librosa.power_to_db(mel, ref=np.max)
    low, high = float(db.min()), float(db.max())
    shaded = (db - low) / max(high - low, 1e-9)
    return {"waveLo": [round(v / scale, 4) for v in lo.tolist()],
            "waveHi": [round(v / scale, 4) for v in hi.tolist()],
            "spectrogram": _array_png(shaded, cmap="magma")}


def zoomable_page(analysis_dir, duration_s: float, out, hierarchy=None,
                  max_points: int = 8000, videogram_width: int = 3000,
                  title: str = "session", which: str = "videogram_v",
                  video=None, audio=None, player=None, start_s: float = 0.0):
    """Write a self-contained HTML page that zooms from the whole session to one action.

    Args:
        analysis_dir: Directory holding the cached pyramid and `tracks.json`.
        duration_s (float): Length of the recording.
        out: Path to write. Everything is embedded; nothing else is needed beside it.
        hierarchy: A `Hierarchy` whose levels become tier bands, or None.
        max_points (int): Ceiling on embedded envelope points.
        videogram_width (int): Width in pixels of the embedded strips.
        title (str): Shown on the page.
        which (str): Which pyramid to embed when `video` is not given.
        video (dict, optional): Named video strips, label to a (rows, time) array ---
            for example a videogram and a motiongram --- embedded in order, with the
            page offering a switch when there is more than one. None keeps the cached
            pyramid as the single strip.
        audio (optional): Path to an audio (or video) file. When given, the page gains
            an audio band that switches between a waveform and a log-mel spectrogram,
            on the same clock as everything else.
        start_s (float): Where in the session the page begins, in seconds. The page
            then covers `start_s` to `start_s + duration_s`: the cached track is
            sliced, and `hierarchy` spans --- given on the session clock --- are
            clipped to the range and shifted onto the page's own clock, so one
            section of a long recording can be paged and analysed on its own.
            Strips passed via `video` and the `audio` file are the caller's to
            slice, since only the caller knows their time base. Defaults to 0.
        player (str, optional): RELATIVE name of a video file to play above the
            strips --- for example the proxy that ships in the same folder as the
            page. Clicking the timeline seeks the video, and a playhead runs across
            every band during playback. A relative name on purpose: the page stays
            serverless and needs only the folder it ships in, and it degrades to the
            strips alone when the file is not beside it.

    Returns:
        Path: The file written.
    """
    from musicalgestures._tracks import read_columns

    budget = embed_budget(duration_s, max_points)
    meta = json.loads((Path(analysis_dir) / "tracks.json").read_text())
    fps, n_frames = float(meta["fps"]), int(meta["frames"])
    qom = np.asarray(np.memmap(Path(analysis_dir) / meta["qom"], dtype=np.float32,
                               mode="r", shape=(n_frames,)), dtype=float)
    a = min(n_frames, int(round(start_s * fps)))
    b = min(n_frames, int(round((start_s + duration_s) * fps)))
    qom = qom[a:b]
    lo, hi = decimate_minmax_pairs(qom, budget["n_points"])
    scale = float(hi.max()) or 1.0

    tiers = []
    if hierarchy is not None:
        for name, spans in hierarchy.levels.items():
            kept = []
            for span in spans:
                s = max(float(span.start), start_s)
                e = min(float(span.end), start_s + duration_s)
                if e > s:
                    kept.append([round(s - start_s, 2), round(e - start_s, 2)])
            tiers.append({"name": name, "spans": kept})

    if video:
        strips = [{"name": str(name), "png": _array_png(arr)}
                  for name, arr in video.items()]
    else:
        strips = [{"name": "videogram",
                   "png": _videogram_png(analysis_dir, duration_s,
                                         videogram_width, which, start_s)}]

    payload = {
        "title": title,
        "duration": duration_s,
        "secondsPerPoint": budget["seconds_per_point"],
        "lo": [round(v / scale, 4) for v in lo.tolist()],
        "hi": [round(v / scale, 4) for v in hi.tolist()],
        "tiers": tiers,
        "video": strips,
        "audio": (_audio_strips(audio, budget["n_points"], videogram_width)
                  if audio is not None else None),
        "player": str(player) if player is not None else None,
    }
    player_markup = ('<div id="pwrap"><video id="v" controls '
                     'preload="metadata"></video></div>' if player else "")
    html = (_TEMPLATE.replace("__DATA__", json.dumps(payload))
                     .replace("__TITLE__", str(title))
                     .replace("__PLAYER__", player_markup))
    out = Path(out)
    out.write_text(html, encoding="utf8")
    return out


#: Kept as one string rather than a separate asset, because a page that needs a file beside
#: it is not self-contained and this one is meant to be emailed.
#:
#: TWO DESIGN CHOICES, both deliberate rather than omissions. The page commits to a dark
#: ground because the thing it exists to show --- a videogram on the magma colormap --- is a
#: dark image, and a light ground would put it in a bright frame it fights. Background and
#: every colour are painted explicitly so the page holds wherever it is embedded. And the
#: type is a system stack rather than a linked webfont, because a webfont needs the network
#: and this page has to work from a folder somebody was emailed.
_TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
 :root{--bg:#12121a;--fg:#e8e8ee;--dim:#8a8a99;--hl:#d95f02}
 body{margin:0;background:var(--bg);color:var(--fg);
      font:13px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
      font-variant-numeric:tabular-nums}
 canvas:focus-visible{outline:2px solid var(--hl);outline-offset:2px}
 @media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
 header{padding:10px 14px;border-bottom:1px solid #2a2a36}
 h1{font-size:15px;margin:0 0 2px}
 .dim{color:var(--dim);font-size:12px}
 #ctl{padding:6px 14px 0;display:flex;gap:18px;flex-wrap:wrap}
 #ctl .grp{display:flex;gap:4px;align-items:center}
 #ctl .lbl{color:var(--dim);font-size:11px;margin-right:2px}
 #ctl button{background:#23232e;color:var(--dim);border:1px solid #2a2a36;
             border-radius:3px;padding:2px 9px;font-size:11px;cursor:pointer}
 #ctl button.on{color:var(--fg);border-color:var(--hl)}
 #wrap{padding:8px 14px 20px}
 canvas{width:100%;display:block;cursor:crosshair;border-radius:4px}
 #pwrap{margin-bottom:8px}
 video{width:100%;max-height:340px;background:#000;border-radius:4px;display:block}
 #hint{margin-top:8px}
 kbd{background:#23232e;border-radius:3px;padding:1px 5px;font-size:11px}
</style>
<header>
 <h1 id="ttl"></h1>
 <div class="dim" id="sub"></div>
</header>
<div id="ctl"></div>
<div id="wrap">__PLAYER__<canvas id="c" tabindex="0"></canvas>
 <div class="dim" id="hint">Scroll to zoom, drag to pan, <kbd>0</kbd> to reset.
  Below the finest resolution the page shows interpolation, not data.</div>
</div>
<script>
const D = __DATA__;
const c = document.getElementById('c'), ctx = c.getContext('2d');
const vimgs = D.video.map(v => {
  const i = new Image(); i.src = 'data:image/png;base64,' + v.png;
  i.onload = () => draw(); return i;
});
let simg = null;
if (D.audio){
  simg = new Image(); simg.src = 'data:image/png;base64,' + D.audio.spectrogram;
  simg.onload = () => draw();
}
let vsel = 0, amode = 'waveform';
let t0 = 0, t1 = D.duration, drag = null;
const v = document.getElementById('v');
if (v && D.player){
  v.src = D.player;
  v.addEventListener('timeupdate', () => draw());
  v.addEventListener('error', () => { v.parentElement.hidden = true; draw(); });
  let raf = null;
  const tick = () => { draw(); if (!v.paused) raf = requestAnimationFrame(tick); };
  v.addEventListener('play', () => { raf = requestAnimationFrame(tick); });
  v.addEventListener('pause', () => cancelAnimationFrame(raf));
}
document.getElementById('ttl').textContent = D.title;
document.getElementById('sub').textContent =
  D.duration.toFixed(0) + ' s, ' + D.tiers.length + ' tiers, finest resolution '
  + D.secondsPerPoint.toFixed(2) + ' s per point';

// switches, only where there is a choice to make
const ctl = document.getElementById('ctl');
function group(label, names, get, set){
  const g = document.createElement('div'); g.className = 'grp';
  const l = document.createElement('span'); l.className = 'lbl';
  l.textContent = label; g.appendChild(l);
  const buttons = names.map((n, i) => {
    const b = document.createElement('button'); b.textContent = n;
    b.onclick = () => { set(i); buttons.forEach((x, j) =>
      x.classList.toggle('on', j === get())); draw(); };
    g.appendChild(b); return b;
  });
  buttons[get()].classList.add('on');
  ctl.appendChild(g);
}
if (D.video.length > 1)
  group('video', D.video.map(v => v.name), () => vsel, i => vsel = i);
if (D.audio)
  group('audio', ['waveform', 'spectrogram'],
        () => amode === 'waveform' ? 0 : 1,
        i => amode = i === 0 ? 'waveform' : 'spectrogram');

const VG = 150, AUD = D.audio ? 110 : 0, ENV = 110, TIER = 17;
function layout(){
  const dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth, h = VG + AUD + ENV + D.tiers.length * TIER + 34;
  c.width = w * dpr; c.height = h * dpr; c.style.height = h + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return {w, h};
}
const x2t = (x, w) => t0 + (x / w) * (t1 - t0);
const t2x = (t, w) => ((t - t0) / (t1 - t0)) * w;

function cropped(image, y, height, w){
  if (!image || !image.complete || !image.naturalWidth) return;
  const sx = (t0 / D.duration) * image.naturalWidth;
  const sw = ((t1 - t0) / D.duration) * image.naturalWidth;
  ctx.drawImage(image, sx, 0, Math.max(1, sw), image.naturalHeight, 0, y, w, height);
}

function bucketed(lo, hi, x, w){
  const n = hi.length, spp = D.duration / n;
  const ta = x2t(x, w), tb = x2t(x + 1, w);
  let a = Math.floor(ta / spp), b = Math.ceil(tb / spp);
  a = Math.max(0, Math.min(n - 1, a)); b = Math.max(a + 1, Math.min(n, b));
  let mn = 1e9, mx = -1e9;
  for (let i = a; i < b; i++){ if (lo[i] < mn) mn = lo[i]; if (hi[i] > mx) mx = hi[i]; }
  return mx < mn ? null : [mn, mx];
}

function draw(){
  const {w} = layout();
  ctx.clearRect(0, 0, w, 1e4);
  // the chosen video strip, cropped to the visible range
  cropped(vimgs[vsel], 0, VG, w);
  // the audio band: signed waveform, or the spectrogram on the same clock
  if (D.audio){
    if (amode === 'spectrogram'){
      cropped(simg, VG, AUD, w);
    } else {
      const mid = VG + AUD / 2, half = AUD / 2 - 2;
      ctx.fillStyle = '#9ee8c1';
      for (let x = 0; x < w; x++){
        const p = bucketed(D.audio.waveLo, D.audio.waveHi, x, w);
        if (!p) continue;
        const y0 = mid - p[1] * half, y1 = mid - p[0] * half;
        ctx.fillRect(x, y0, 1, Math.max(1, y1 - y0));
      }
    }
  }
  // motion envelope, min and max per column
  ctx.fillStyle = '#9ecbff';
  for (let x = 0; x < w; x++){
    const p = bucketed(D.lo, D.hi, x, w);
    if (!p) continue;
    const y0 = VG + AUD + ENV - p[1] * ENV, y1 = VG + AUD + ENV - p[0] * ENV;
    ctx.fillRect(x, y0, 1, Math.max(1, y1 - y0));
  }
  // tiers
  D.tiers.forEach((tr, i) => {
    const y = VG + AUD + ENV + i * TIER + 3;
    ctx.fillStyle = '#8a8a99'; ctx.font = '10px sans-serif';
    ctx.fillText(tr.name, 4, y + 9);
    ctx.fillStyle = 'rgba(217,95,2,.85)';
    for (const [s, e] of tr.spans){
      if (e < t0 || s > t1) continue;
      const xa = t2x(Math.max(s, t0), w), xb = t2x(Math.min(e, t1), w);
      ctx.fillRect(xa, y, Math.max(1.5, xb - xa), TIER - 6);
    }
  });
  // axis
  const yb = VG + AUD + ENV + D.tiers.length * TIER + 16;
  ctx.strokeStyle = '#2a2a36'; ctx.fillStyle = '#8a8a99'; ctx.font = '11px sans-serif';
  const span = t1 - t0, step = Math.pow(10, Math.floor(Math.log10(span / 6)));
  const nice = [1, 2, 5, 10].map(m => m * step).find(v => span / v <= 8) || step;
  for (let t = Math.ceil(t0 / nice) * nice; t <= t1; t += nice){
    const x = t2x(t, w);
    ctx.beginPath(); ctx.moveTo(x, yb - 8); ctx.lineTo(x, yb - 3); ctx.stroke();
    const m = Math.floor(t / 60), s = Math.floor(t % 60);
    ctx.fillText(nice < 1 ? t.toFixed(1) + 's' : m + ':' + String(s).padStart(2, '0'), x + 2, yb + 8);
  }
  // the playhead, across every band, while the video is in view
  if (v && D.player && !v.parentElement.hidden){
    const pt = v.currentTime;
    if (pt >= t0 && pt <= t1){
      const x = t2x(pt, w);
      ctx.strokeStyle = '#ffffff'; ctx.globalAlpha = 0.8;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, yb - 10); ctx.stroke();
      ctx.globalAlpha = 1;
    }
  }
  // a warning, not a silent lie, when zoomed past the data
  if (span / w < D.secondsPerPoint){
    ctx.fillStyle = '#d95f02';
    ctx.fillText('zoomed past the embedded resolution - this is interpolation', 6, VG + 14);
  }
}
c.addEventListener('wheel', e => {
  e.preventDefault();
  const w = c.clientWidth, t = x2t(e.offsetX, w), k = Math.exp(e.deltaY * 0.0015);
  let a = t - (t - t0) * k, b = t + (t1 - t) * k;
  if (b - a < 0.5) { const m = (a + b) / 2; a = m - 0.25; b = m + 0.25; }
  t0 = Math.max(0, a); t1 = Math.min(D.duration, b); draw();
}, {passive: false});
c.addEventListener('mousedown', e => drag = {x: e.offsetX, t0, t1, moved: false});
addEventListener('mouseup', e => {
  // a press that never panned is a seek
  if (drag && !drag.moved && v && D.player && !v.parentElement.hidden){
    v.currentTime = x2t(drag.x, c.clientWidth);
    draw();
  }
  drag = null;
});
addEventListener('mousemove', e => {
  if (!drag) return;
  if (Math.abs(e.offsetX - drag.x) > 4) drag.moved = true;
  if (!drag.moved) return;
  const w = c.clientWidth, dt = ((e.offsetX - drag.x) / w) * (drag.t1 - drag.t0);
  let a = drag.t0 - dt, b = drag.t1 - dt;
  if (a < 0){ b -= a; a = 0; } if (b > D.duration){ a -= b - D.duration; b = D.duration; }
  t0 = Math.max(0, a); t1 = Math.min(D.duration, b); draw();
});
addEventListener('keydown', e => { if (e.key === '0'){ t0 = 0; t1 = D.duration; draw(); } });
addEventListener('resize', draw);
draw();
</script>
"""


def mg_zoompage(self, target_name=None, overwrite: bool = True,
                max_points: int = 8000, which: str = "videogram_v"):
    """The zoomable page for this recording, in one call, as a method.

    Everything derives from the video itself. The motion track and gram come from
    `extract_tracks`, computed on first call and cached beside the video like every
    other analysis; the audio band comes from the video's own soundtrack when it has
    one; and the player is the video, referenced by its bare name, so the page works
    from the folder the two share and needs no server.

    Args:
        target_name (str, optional): Output path. Defaults to "_zoom.html" beside
            the video.
        overwrite (bool, optional): Overwrite or auto-increment. Defaults to True.
        max_points (int): Ceiling on embedded envelope points.
        which (str): Which cached gram to embed as the strip.

    Returns:
        Path: The file written.
    """
    import os
    import subprocess

    from musicalgestures._tracks import extract_tracks
    from musicalgestures._utils import resolve_filename

    of, _ = os.path.splitext(self.filename)
    target = resolve_filename(of, "_zoom.html", target_name, overwrite)

    analysis = Path(self.filename).parent / "analysis" / Path(of).name
    if not (analysis / "tracks.json").exists():
        extract_tracks(self.filename, progress=False)
    meta = json.loads((analysis / "tracks.json").read_text())
    duration = int(meta["frames"]) / float(meta["fps"])

    #: The audio band only when the file carries sound; a silent clip gets a page
    #: without one rather than an error.
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", self.filename],
        capture_output=True, text=True)
    has_audio = "audio" in probe.stdout

    return zoomable_page(
        analysis, duration, target, max_points=max_points, which=which,
        audio=self.filename if has_audio else None,
        player=os.path.basename(self.filename),
        title=Path(of).name)

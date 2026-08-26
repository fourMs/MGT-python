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


def _videogram_png(analysis_dir, duration_s, width, which="videogram_v"):
    """The videogram as a base64 PNG, for the page to scale."""
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt

    from musicalgestures._tracks import read_columns

    cols, _ = read_columns(analysis_dir, 0.0, duration_s, max_columns=width, which=which)
    X = np.asarray(cols, dtype=float)
    if X.ndim == 1:
        X = X[None, :]
    if X.shape[0] > X.shape[1]:
        X = X.T                                   # rows are the spatial axis
    fig = plt.figure(figsize=(X.shape[1] / 100, max(1.0, X.shape[0] / 100)), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.axis("off")
    ax.imshow(X, aspect="auto", cmap="magma", origin="lower")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def zoomable_page(analysis_dir, duration_s: float, out, hierarchy=None,
                  max_points: int = 8000, videogram_width: int = 3000,
                  title: str = "session", which: str = "videogram_v"):
    """Write a self-contained HTML page that zooms from the whole session to one action.

    Args:
        analysis_dir: Directory holding the cached pyramid and `tracks.json`.
        duration_s (float): Length of the recording.
        out: Path to write. Everything is embedded; nothing else is needed beside it.
        hierarchy: A `Hierarchy` whose levels become tier bands, or None.
        max_points (int): Ceiling on embedded envelope points.
        videogram_width (int): Width in pixels of the embedded videogram.
        title (str): Shown on the page.
        which (str): Which pyramid to embed.

    Returns:
        Path: The file written.
    """
    from musicalgestures._tracks import read_columns

    budget = embed_budget(duration_s, max_points)
    meta = json.loads((Path(analysis_dir) / "tracks.json").read_text())
    fps, n_frames = float(meta["fps"]), int(meta["frames"])
    qom = np.asarray(np.memmap(Path(analysis_dir) / meta["qom"], dtype=np.float32,
                               mode="r", shape=(n_frames,)), dtype=float)
    lo, hi = decimate_minmax_pairs(qom, budget["n_points"])
    scale = float(hi.max()) or 1.0

    tiers = []
    if hierarchy is not None:
        for name, spans in hierarchy.levels.items():
            tiers.append({"name": name,
                          "spans": [[round(a.start, 2), round(a.end, 2)] for a in spans]})

    payload = {
        "title": title,
        "duration": duration_s,
        "secondsPerPoint": budget["seconds_per_point"],
        "lo": [round(v / scale, 4) for v in lo.tolist()],
        "hi": [round(v / scale, 4) for v in hi.tolist()],
        "tiers": tiers,
        "videogram": _videogram_png(analysis_dir, duration_s, videogram_width, which),
    }
    html = (_TEMPLATE.replace("__DATA__", json.dumps(payload))
                     .replace("__TITLE__", str(title)))
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
 #wrap{padding:8px 14px 20px}
 canvas{width:100%;display:block;cursor:crosshair;border-radius:4px}
 #hint{margin-top:8px}
 kbd{background:#23232e;border-radius:3px;padding:1px 5px;font-size:11px}
</style>
<header>
 <h1 id="ttl"></h1>
 <div class="dim" id="sub"></div>
</header>
<div id="wrap"><canvas id="c" tabindex="0"></canvas>
 <div class="dim" id="hint">Scroll to zoom, drag to pan, <kbd>0</kbd> to reset.
  Below the finest resolution the page shows interpolation, not data.</div>
</div>
<script>
const D = __DATA__;
const c = document.getElementById('c'), ctx = c.getContext('2d');
const img = new Image(); img.src = 'data:image/png;base64,' + D.videogram;
let t0 = 0, t1 = D.duration, drag = null;
document.getElementById('ttl').textContent = D.title;
document.getElementById('sub').textContent =
  D.duration.toFixed(0) + ' s, ' + D.tiers.length + ' tiers, finest resolution '
  + D.secondsPerPoint.toFixed(2) + ' s per point';

const VG = 150, ENV = 110, TIER = 17;
function layout(){
  const dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth, h = VG + ENV + D.tiers.length * TIER + 34;
  c.width = w * dpr; c.height = h * dpr; c.style.height = h + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return {w, h};
}
const x2t = (x, w) => t0 + (x / w) * (t1 - t0);
const t2x = (t, w) => ((t - t0) / (t1 - t0)) * w;

function draw(){
  const {w} = layout();
  ctx.clearRect(0, 0, w, 1e4);
  // videogram, cropped to the visible range
  if (img.complete && img.naturalWidth){
    const sx = (t0 / D.duration) * img.naturalWidth;
    const sw = ((t1 - t0) / D.duration) * img.naturalWidth;
    ctx.drawImage(img, sx, 0, Math.max(1, sw), img.naturalHeight, 0, 0, w, VG);
  }
  // motion envelope, min and max per column
  const n = D.hi.length, spp = D.duration / n;
  ctx.fillStyle = '#9ecbff';
  for (let x = 0; x < w; x++){
    const ta = x2t(x, w), tb = x2t(x + 1, w);
    let a = Math.floor(ta / spp), b = Math.ceil(tb / spp);
    a = Math.max(0, Math.min(n - 1, a)); b = Math.max(a + 1, Math.min(n, b));
    let mn = 1e9, mx = -1e9;
    for (let i = a; i < b; i++){ if (D.lo[i] < mn) mn = D.lo[i]; if (D.hi[i] > mx) mx = D.hi[i]; }
    if (mx < mn) continue;
    const y0 = VG + ENV - mx * ENV, y1 = VG + ENV - mn * ENV;
    ctx.fillRect(x, y0, 1, Math.max(1, y1 - y0));
  }
  // tiers
  D.tiers.forEach((tr, i) => {
    const y = VG + ENV + i * TIER + 3;
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
  const yb = VG + ENV + D.tiers.length * TIER + 16;
  ctx.strokeStyle = '#2a2a36'; ctx.fillStyle = '#8a8a99'; ctx.font = '11px sans-serif';
  const span = t1 - t0, step = Math.pow(10, Math.floor(Math.log10(span / 6)));
  const nice = [1, 2, 5, 10].map(m => m * step).find(v => span / v <= 8) || step;
  for (let t = Math.ceil(t0 / nice) * nice; t <= t1; t += nice){
    const x = t2x(t, w);
    ctx.beginPath(); ctx.moveTo(x, yb - 8); ctx.lineTo(x, yb - 3); ctx.stroke();
    const m = Math.floor(t / 60), s = Math.floor(t % 60);
    ctx.fillText(nice < 1 ? t.toFixed(1) + 's' : m + ':' + String(s).padStart(2, '0'), x + 2, yb + 8);
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
c.addEventListener('mousedown', e => drag = {x: e.offsetX, t0, t1});
addEventListener('mouseup', () => drag = null);
addEventListener('mousemove', e => {
  if (!drag) return;
  const w = c.clientWidth, dt = ((e.offsetX - drag.x) / w) * (drag.t1 - drag.t0);
  let a = drag.t0 - dt, b = drag.t1 - dt;
  if (a < 0){ b -= a; a = 0; } if (b > D.duration){ a -= b - D.duration; b = D.duration; }
  t0 = Math.max(0, a); t1 = Math.min(D.duration, b); draw();
});
addEventListener('keydown', e => { if (e.key === '0'){ t0 = 0; t1 = D.duration; draw(); } });
addEventListener('resize', draw);
img.onload = draw; draw();
</script>
"""

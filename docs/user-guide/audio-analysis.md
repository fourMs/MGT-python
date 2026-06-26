# Audio Analysis

Audio analysis methods are available on both `MgVideo` (via `mv.audio`) and `MgAudio` (for audio-only files). All methods return an `MgFigure` and save a PNG alongside the source file.

```python
import musicalgestures as mg

# From a video file
mv = mg.MgVideo('/path/to/video.avi')
audio = mv.audio

# Or load an audio file directly
audio = mg.MgAudio('/path/to/audio.mp3')
```

---

## Waveform

A waveform plots audio amplitude over time. It gives a quick overview of loudness and silence.

```python
waveform = audio.waveform()
waveform.show()
```

Pass `raw=True` to skip librosa post-processing and plot the raw sample values:

```python
waveform = audio.waveform(raw=True)
```

### Coloured waveform

Set `colored=True` to render a frequency-coloured waveform (amplitude envelope with colour representing spectral centroid, in the style of freesound.org):

```python
colored = audio.waveform(colored=True)
colored = audio.waveform(colored=True, cmap='jet')
```

Any Matplotlib colormap name is accepted for `cmap`.

---

## Spectrogram

A mel spectrogram plots frequency content over time and is more informative than a waveform for most audio.

```python
spectrogram = audio.spectrogram()
spectrogram.show()
spectrogram = audio.spectrogram(raw=True)
```

---

## Tempogram

A tempogram estimates tempo by analysing onset strength over time using FFT, giving a view of rhythmic periodicity.

```python
tempogram = audio.tempogram()
tempogram.show()
```

---

## Harmonic Percussive Source Separation (HPSS)

HPSS uses median filtering to separate the harmonic and percussive components of the audio. An optional residual component captures sounds between the two.

```python
hpss_fig = audio.hpss()
hpss_fig = audio.hpss(residual=True)
hpss_fig.show()
```

---

## Chromagram

A chromagram maps audio energy onto the 12 pitch classes (C, C#, D, …, B) over time. It is useful for analysing harmony, chord progressions, and key.

```python
chroma = audio.chromagram()
chroma.show()
```

Three algorithms are available via `chroma_type`:

| `chroma_type` | Algorithm | Best for |
|---|---|---|
| `'cqt'` (default) | Constant-Q Transform | Music with low-frequency content |
| `'stft'` | Short-Time Fourier Transform | Fast computation |
| `'cens'` | Chroma Energy Normalised Statistics | Robustness to timbre and dynamics |

```python
chroma_cqt  = audio.chromagram(chroma_type='cqt')
chroma_stft = audio.chromagram(chroma_type='stft')
chroma_cens = audio.chromagram(chroma_type='cens')
```

You can also control normalisation and colormap:

```python
chroma = audio.chromagram(norm=2, cmap='viridis')   # L2 norm, viridis colormap
chroma = audio.chromagram(norm=None)                 # no normalisation
```

The `chroma` array (shape `12 × frames`) is available in the returned `MgFigure`:

```python
mgf = audio.chromagram()
chroma_data = mgf.data['chroma']   # numpy array, shape (12, n_frames)
```

---

## MFCC

Mel-frequency cepstral coefficients compactly describe the spectral envelope (timbre) over time and are widely used as audio features.

```python
mfcc = audio.mfcc()
mfcc = audio.mfcc(n_mfcc=20)
mfcc.show()

coeffs = audio.mfcc(autoshow=False).data['mfcc']   # numpy array (n_mfcc, frames)
```

---

## Tempo and beat tracking

`tempo()` estimates the tempo and beat positions and renders the waveform with beat markers. Numeric results are in the returned figure's `.data`:

```python
t = audio.tempo()
t.show()

print(t.data['tempo'])            # BPM
print(t.data['beat_times'])       # beat positions (s)
print(t.data['beat_regularity'])  # 1.0 = perfectly even beats
```

Available `.data` keys: `tempo`, `beat_times`, `ibi` (inter-beat intervals), `beat_regularity`, `beat_phases`, `deviations_s`, `R_beat`, `mu_beat`, `T_fit`, `t0_fit`, `p_rayleigh`.

---

## Beat statistics (timing consistency)

`beat_statistics()` fits an ideal isochronous grid to the detected beats and visualises how each beat deviates from it — a polar phase histogram plus a millisecond-deviation time series. This shows whether a performer rushes, drags, or keeps steady time. Requires at least four detected beats.

```python
stats = audio.beat_statistics()
stats.show()
```

The polar plot shows the mean resultant vector length `R` (concentration of timing) and a Rayleigh-test p-value (`p` small = significantly consistent timing).

---

## Self-Similarity Matrix (SSM)

Audio SSMs compare feature frames against each other to reveal repeating structure (verse/chorus, loops, etc.). Supported features are `'spectrogram'`, `'chromagram'`, and `'tempogram'`.

```python
spectrossm = audio.ssm(features='spectrogram')
chromassm  = audio.ssm(features='chromagram', cmap='magma', norm=2)
spectrossm.show()
```

SSMs can also be computed on visual features from `MgVideo` — see [Video Analysis](video-analysis.md#self-similarity-matrix-ssm).

---

## Audio descriptors

`descriptors()` plots five spectral features over time in a single figure:

- RMS energy (perceived loudness)
- Spectral flatness (noisiness vs. tonality)
- Spectral centroid (brightness)
- Spectral bandwidth (frequency spread)
- Spectral rolloff (at 1% and 99% of total energy)

```python
descriptors = audio.descriptors()
descriptors.show()
```

Set `save_data=True` to also write the per-frame descriptor time series to disk (csv/tsv/txt), mirroring `motiondata`:

```python
audio.descriptors(save_data=True, data_format='csv')   # or 'tsv' / 'txt' / ['csv','txt']
# writes <name>_descriptors.csv with columns:
# Time, RMS, Centroid, Bandwidth, Rolloff, RolloffMin, Flatness
```

Descriptors can be overlaid on motion plots by passing `audio_descriptors=True` to `motionplots()`:

```python
mv.motionplots(audio_descriptors=True)
```

---

## Signal-analysis utilities

The `musicalgestures` package exposes general-purpose helpers for analysing rhythm and periodicity in any 1-D signal (audio onset envelopes, quantity-of-motion curves, body-part speeds):

```python
import musicalgestures as mg

mg.smooth(x, w=5)                                  # moving-average smoothing
mg.bandpass(signal, lo, hi, fs)                    # zero-phase Butterworth band-pass
mg.dominant_frequency(signal, fps, fmin, fmax)     # FFT peak within a band (Hz)
mg.circular_stats(phases)                          # (R, mean_angle_deg)
mg.rayleigh_test(phases)                           # (Z, p) non-uniformity test
mg.synchrony(sig_a, sig_b, times_a, times_b)       # Pearson r after align + normalise
```

For example, to quantify audio–motion synchrony, correlate the audio onset strength against the video's quantity of motion:

```python
import pandas as pd, os
mv = mg.MgVideo('dance.avi')
motion_video = mv.motion()

csv = os.path.splitext(motion_video.filename)[0].replace('_motion', '_motiondata') + '.csv'
qom = pd.read_csv(csv)
onset = mv.audio.tempo(autoshow=False).data   # or compute an onset envelope

r = mg.synchrony(qom['Qom'].values, mv.audio.numpy())
print(f"audio-motion correlation: {r:.3f}")
```

---

## Custom titles

All methods accept a `title` argument:

```python
spectrogram = audio.spectrogram(title='My Video - Spectrogram')
tempogram   = audio.tempogram(title='My Video - Tempogram')
descriptors = audio.descriptors(title='My Video - Spectral Descriptors')
```

---

## Next steps

- [Working with Results](results.md) — combine audio and video figures into stacked plots
- [Video Analysis](video-analysis.md) — motion, optical flow, and SSMs on visual data
- [API Reference](../musicalgestures/_audio.md) — complete audio method signatures

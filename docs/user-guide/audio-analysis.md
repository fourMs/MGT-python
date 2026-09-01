# Audio Analysis

Task reference for the audio methods on `MgVideo.audio` and `MgAudio`. Each method returns an `MgFigure` and saves a PNG alongside the source file, and all accept a `title` argument. For the full tutorial, read in order, see [chapter 9 of the wiki](https://github.com/fourMs/MGT-python/wiki/9-%E2%80%90-Audio%E2%80%90based-Processes).

```python
import musicalgestures as mg

audio = mg.MgVideo('/path/to/video.avi').audio   # from a video
audio = mg.MgAudio('/path/to/audio.mp3')         # or an audio file directly
```

## Waveform

```python
audio.waveform().show()
audio.waveform(raw=True)                    # raw sample values
audio.waveform(colored=True, cmap='jet')    # spectral-centroid colouring
```

Amplitude over time. `colored=True` draws the envelope coloured by spectral centroid; any Matplotlib colormap name works for `cmap`.

## Spectrogram

```python
audio.spectrogram().show()
audio.spectrogram(raw=True)
```

Mel spectrogram of frequency content over time.

## MFCC

```python
audio.mfcc(n_mfcc=20).show()
coeffs = audio.mfcc(autoshow=False).data['mfcc']   # numpy array (n_mfcc, frames)
```

Mel-frequency cepstral coefficients (timbre). The coefficient matrix is in the figure's `.data`.

## Chromagram

```python
audio.chromagram().show()
audio.chromagram(chroma_type='stft', norm=2, cmap='viridis')
chroma_data = audio.chromagram().data['chroma']    # shape (12, n_frames)
```

Energy on the 12 pitch classes over time. `chroma_type` selects the algorithm: `'cqt'` (default, good for low frequencies), `'stft'` (fast), `'cens'` (robust to timbre and dynamics). `norm=None` disables normalisation.

## HPSS

```python
audio.hpss(residual=True).show()
```

Harmonic Percussive Source Separation via median filtering; `residual=True` adds a third component between the two.

## Tempogram

```python
audio.tempogram().show()
audio.tempogram(onset_strength=False)   # single panel, no onset-strength strip
```

Rhythmic periodicity from onset strength, with the estimated tempo in the plot title (e.g. `estimated tempo = 112.3 BPM`).

## Tempo and beat tracking

```python
t = audio.tempo()
print(t.data['tempo'], t.data['beat_times'], t.data['beat_regularity'])
```

Waveform with beat markers; numbers live in `.data`. Keys: `tempo`, `beat_times`, `ibi`, `beat_regularity`, `beat_phases`, `deviations_s`, `R_beat`, `mu_beat`, `T_fit`, `t0_fit`, `p_rayleigh`.

## Beat statistics

```python
audio.beat_statistics().show()          # always the audio track
mv.beat_statistics(source='audio')      # on MgVideo the default is source='motion'
```

Circular statistics of beat-timing consistency (polar phase histogram, `R`, Rayleigh p-value); needs at least four detected beats. On `MgVideo` the default `source='motion'` analyses the movement rhythm, not the audio.

## Self-Similarity Matrix (SSM)

```python
audio.ssm(features='spectrogram').show()
audio.ssm(features='chromagram', cmap='magma', norm=2)
```

Repeating structure from `'spectrogram'`, `'chromagram'`, or `'tempogram'` features. For SSMs on visual features see [Video Analysis](video-analysis.md#self-similarity-matrix-ssm).

## Audio descriptors

```python
audio.descriptors().show()
audio.descriptors(save_data=True, data_format='csv')   # <name>_descriptors.csv
mv.motionplots(audio_descriptors=True)                 # overlay on motion plots
```

RMS energy, spectral flatness, centroid, bandwidth, and rolloff over time in one figure. `save_data=True` writes the per-frame time series with columns Time, RMS, Centroid, Bandwidth, Rolloff, RolloffMin, Flatness.

## Audio–motion comparison

`tempo_similarity()`, `phase_synchrony()`, `structure_comparison()`, `body_audio_coupling()`, and `dynamics_coupling()` compare the sound with the motion of the same performer. They live on `MgVideo`, since they need both tracks; see [Audio-Video Processing & Analysis](audio-video.md).

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

`dominant_frequency` and `bandpass` take the sampling rate as an argument and cannot check it
against anything, since they never see the file. Pass `mv.fps` rather than a literal: on a
29.97 fps clip with a true 2.00 Hz movement rhythm, passing 20 returns 1.33 Hz and passing 15
returns 1.00 Hz, both of them plausible tempi. See
[the frame rate](loading.md#the-frame-rate-and-what-it-costs-to-be-wrong-about-it).

`dominant_frequency` also reports the largest FFT bin in `[fmin, fmax]` whether or not there is
a peak there. On a spectrum that falls steeply with frequency the largest bin is near `fmin`
whatever the movement was doing, so the answer tracks the band you chose rather than the body,
and it does not have to land on `fmin` to be doing that. `micromotion.spectral_peak` returns NaN
in that case and `micromotion.band_edge_sweep` tests an answer already in hand by moving the band
edge and seeing whether the answer follows.

## Further

- [Chapter 9 of the wiki](https://github.com/fourMs/MGT-python/wiki/9-%E2%80%90-Audio%E2%80%90based-Processes)—the full audio tutorial
- [Working with Results](results.md)—combine audio and video figures into stacked plots
- [API: MgAudio](../musicalgestures/_audio.md)—complete audio method signatures
- [API: audio features](../musicalgestures/_audiofeatures.md)—descriptor and feature internals

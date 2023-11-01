import math
import numpy as np
import matplotlib.pyplot as plt

import cv2
import librosa
import soundfile as sf
from musicalgestures._utils import convert


def min_max_level(filename):
    audio_file = sf.SoundFile(filename, 'r')
    samples = audio_file.read()

    # Convert to mono by selecting left channel only
    if audio_file.channels > 1:
        samples = samples[:,0] 

    min_level = min(samples)       
    max_level = max(samples)

    audio_file.close()
    return min_level, max_level

class MgAudioProcessor(object):
    def __init__(
            self, 
            filename, 
            n_fft,
            fmin, 
            fmax=None, 
            window_function=np.hanning
            ): 

        """
        The MgAudioProcessor class inherits from the MgAudio class for processing chunks of audio and calculating the spectral centroid 
        and the peak samples in each chunk of audio.

        Adapted from https://github.com/endolith/freesound-thumbnailer/blob/master/processing.py

        Args:
            filename (str): Path to the audio file. 
            n_fft (int, optional): Length of the FFT window.
            fmin (int): Minimum frequency for computing spectral centroid. 
            fmax (int): Maximum frequency for computing spectral centroid. Defaults to None.
            window_function (int, optional): Type of window to apply on chunks of audio. Defaults to np.hanning.
        """
        try: # check if it is an audio file or convert it to .wav format
            self.audio_file = sf.SoundFile(filename, 'r')
        except RuntimeError:
            filename = convert(filename, filename + '.wav')
            self.audio_file = sf.SoundFile(filename, 'r')

        self.n_fft = n_fft
        
        self.fmin = fmin
        if fmax == None:
            self.fmax = self.audio_file.samplerate // 2
        else:
            fmax = self.fmax
        
        self.fmin_log = math.log10(self.fmin)
        self.fmax_log = math.log10(self.fmax)
        self.clip = lambda val, low, high: min(high, max(low, val))
        
        self.window = window_function(self.n_fft)
        # Get the minimum and maximum audio levels
        self.min_level, self.max_level = min_max_level(filename)

    def read_samples(self, start, size, resize_if_less=False):
        """ 
        Read size samples starting at start, if resize_if_less is True and less than size
        samples are read, resize the array to size and fill with zeros 
        """
        
        # Number of zeros to add to start and end of the buffer
        add_to_start = 0
        add_to_end = 0
        
        if start < 0:
            # First FFT window starts centered around zero
            if size + start <= 0:
                return np.zeros(size) if resize_if_less else np.array([])
            else:
                self.audio_file.seek(0)
                add_to_start = -start # remember: start is negative!
                to_read = size + start

                if to_read > self.audio_file.frames:
                    add_to_end = to_read - self.audio_file.frames
                    to_read = self.audio_file.frames
        else:            
            self.audio_file.seek(int(start))
        
            to_read = size
            if start + to_read >= self.audio_file.frames:
                to_read = self.audio_file.frames - start
                add_to_end = size - to_read
        
        try:            
            samples = self.audio_file.read(int(to_read))
        except RuntimeError: # this can happen for wave files with broken headers
            return np.zeros(size) if resize_if_less else np.zeros(2)

        # Convert to mono by selecting left channel only
        if self.audio_file.channels > 1:
            samples = samples[:,0]

        if resize_if_less and (add_to_start > 0 or add_to_end > 0):
            if add_to_start > 0:   
                samples = np.concatenate((np.zeros(int(add_to_start)), samples))
            if add_to_end > 0:
                samples = np.resize(samples, size)
                samples[int(size - add_to_end):] = 0
                
        return samples
    
    def spectral_centroid(self, seek_point):
        """ 
        Starting at seek_point to read n_fft samples and calculate the spectral centroid 
        """
        
        samples = self.read_samples(seek_point - self.n_fft // 2, self.n_fft, True) * self.window
        # Compute spectral centroid
        spectral_centroid = librosa.feature.spectral_centroid(y=samples, sr=self.audio_file.samplerate, n_fft=self.n_fft)[0].sum()
        # Clip spectral centroid to desired frequency range
        clip_centroid = math.log10(self.clip(spectral_centroid, self.fmin, self.fmax))
        # Scale desired frequency range from 0 to 1
        spectral_centroid = (clip_centroid - self.fmin_log) / (self.fmax_log - self.fmin_log)
        
        return (spectral_centroid)


    def peaks(self, start_seek, end_seek, block_size=1024):
        """ 
        Read all samples between start_seek and end_seek, then find the minimum and maximum peak
        in that range. Returns that pair in the order they were found. So if min was found first,
        it returns (min, max) else the other way around. 
        """
        
        min_index, max_index, min_value, max_value = -1, -1, 1, -1 
    
        if end_seek > self.audio_file.frames:
            end_seek = self.audio_file.frames
    
        if block_size > end_seek - start_seek:
            block_size = end_seek - start_seek
        
        for i in range(start_seek, end_seek, block_size):
            samples = self.read_samples(i, block_size)
    
            local_max_index = np.argmax(samples)
            local_max_value = samples[local_max_index]
    
            if local_max_value > max_value:
                max_value = local_max_value
                max_index = local_max_index
    
            local_min_index = np.argmin(samples)
            local_min_value = samples[local_min_index]
            
            if local_min_value < min_value:
                min_value = local_min_value
                min_index = local_min_index
    
        return (min_value, max_value) if min_index < max_index else (max_value, min_value)

class MgWaveformImage(object):
    def __init__(self, image_width=2500, image_height=500, cmap='freesound'):

        """
        Given peaks and spectral centroids from the MgAudioProcessor class, the MgWaveformImage class will construct
        a wavefile image using OpenCV.

        Adapted from https://github.com/endolith/freesound-thumbnailer/blob/master/processing.py

        Args:
            image_width (int, optional): Number of pixels for the image width. Defaults to 2500.
            image_height (int, optional): Number of pixels for the image height. Defaults to 500.
            cmap (str, optional): Colormap used for coloring the waveform, all colormaps included with matplotlib can be used. Defaults to 'freesound'.
        """
        if cmap == 'freesound': # create original freesound colormap 
            colors = [(50,0,200),(0,220,80),(255,224,0),(255,70,0)]
            self.color_lookup = self.interpolate_colors(colors)
        else: # use colormaps included with matplotlib
            colors = plt.get_cmap(cmap)
            colors = colors(np.arange(256))[...,:3]
            self.color_lookup = colors * 255

        self.image = np.zeros((image_height, image_width, 3))
        self.image_width = image_width
        self.image_height = image_height
        
    def draw_peaks(self, x, peaks, spectral_centroid):
        """ 
        Draw 2 peaks at x using the spectral_centroid for color 
        """

        y1 = int(self.image_height * 0.5 - peaks[0] * (self.image_height) * 0.5)
        y2 = int(self.image_height * 0.5 - peaks[1] * (self.image_height) * 0.5)
        
        line_color = self.color_lookup[int(spectral_centroid * 255)] 
        cv2.line(self.image, (x, y1), (x, y2), line_color)
        
    def interpolate_colors(self, colors, flat=False, num_colors=256):
        """ 
        Given a list of colors, create a larger list of colors linearly interpolating
        the first one. If flatten is True a list of numbers will be returned. If
        False, a list of (r,g,b) tuples. num_colors is the number of colors wanted
        in the final list 
        """

        cmap = []
        for i in range(num_colors):
            index = (i * (len(colors) - 1)) / (num_colors - 1.0) 
            index_int = int(index)
            alpha = index - float(index_int)

            if alpha > 0:
                r = (1.0 - alpha) * colors[index_int][0] + alpha * colors[index_int + 1][0]
                g = (1.0 - alpha) * colors[index_int][1] + alpha * colors[index_int + 1][1]
                b = (1.0 - alpha) * colors[index_int][2] + alpha * colors[index_int + 1][2]
            else:
                r = (1.0 - alpha) * colors[index_int][0]
                g = (1.0 - alpha) * colors[index_int][1]
                b = (1.0 - alpha) * colors[index_int][2]

            if flat:
                cmap.extend((int(r), int(g), int(b)))
            else:
                cmap.append((int(r), int(g), int(b)))

        return cmap
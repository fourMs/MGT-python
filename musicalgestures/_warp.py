import cv2
import os
import numpy as np
import librosa
import soundfile as sf
import subprocess
from numba import jit

import musicalgestures
from musicalgestures._directograms import mg_directograms
from musicalgestures._impacts import impact_envelope
from musicalgestures._utils import MgProgressbar, generate_outfilename, wrap_str

@jit(nopython=True)
def beats_diff(beats, media):
    beat = beats[0]
    diff = np.append(beat, np.diff(beats))
    beats_diff = np.append(diff, media.shape[0] - beats[-1])
    return beats_diff

def mg_warp_audiovisual_beats(self, audio_file, speed=(0.5,2), data=None, filtertype='Adaptative', thresh=0.05, kernel_size=5, target_name=None, overwrite=False):
    """
    Warp audio beats with visual beats (patterns of motion that can be shifted in time to control visual rhythm).
    Visual beats are warped after computing a directogram which factors the magnitude of motion in the video into different angles.

    Source: Abe Davis -- [Visual Rhythm and Beat](http://www.abedavis.com/files/papers/VisualRhythm_Davis18.pdf) (section 5)

    Args:
        audio_file (str): Path to the audio file.
        speed (tuple, optional): Speed's change between the audiovisual beats which can be adjusted to slow down or speed up the visual rhythms. Defaults to (0.5,2).
        data (array_like, optional): Computed directogram data can be added separately to avoid the directogram processing time (which can be quite long). Defaults to None.
        filtertype (str, optional): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method. 'Adaptative' perform adaptative threshold as the weighted sum of 11 neighborhood pixels where weights are a Gaussian window. Defaults to 'Adaptative'.
        thresh (float, optional): Eliminates pixel values less than given threshold. Ranges from 0 to 1. Defaults to 0.05.
        kernel_size (int, optional): Size of structuring element. Defaults to 5.
        target_name (str, optional): Target output name for the directogram. Defaults to None (which assumes that the input filename with the suffix "_dg" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgVideo: A MgVideo as warping_audiovisual_beats for parent MgVideo
    """

    # COMPUTE DIRECTOGRAMS ------------------------------------------------------------------------------------------------------

    if data is None:
        directogram = mg_directograms(self, title=None, filtertype=filtertype, thresh=thresh, kernel_size=kernel_size, target_name=target_name, overwrite=overwrite)
        directograms = directogram.data['directogram']
        fps = directogram.data['FPS']

    else:
        directograms = data
        vidcap = cv2.VideoCapture(self.filename)
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))

    # COMPUTE AUDIO AND VISUAL BEATS --------------------------------------------------------------------------------------------

    pb = MgProgressbar(total=130, prefix='Warping audiovisual beats:')
    pb.progress(0)
    signal, sr = librosa.load(audio_file, mono=True)
    pb.progress(5)

    # Compute onset and impact envelopes
    onset_envelopes = librosa.onset.onset_strength(signal, sr=sr)
    pb.progress(10)
    impact_envelopes = impact_envelope(directograms)
    pb.progress(15)

    # Compute beats with librosa
    pb.progress(20)
    audio_beats = librosa.beat.beat_track(onset_envelope=onset_envelopes,sr=sr, hop_length=512, trim=False, units='samples')
    pb.progress(25)
    visual_beats = librosa.beat.beat_track(onset_envelope=impact_envelopes,sr=fps, hop_length=1.0, trim=False, units='samples')

    # WARP AUDIO AND VISUAL BEATS -----------------------------------------------------------------------------------------------

    audio_differences = beats_diff(audio_beats[1], signal)
    pb.progress(30)
    visual_differences = beats_diff(visual_beats[1], np.ndarray.flatten(directograms))
    pb.progress(35)

    # Asserting if the arrays have equal shape and elements
    assert np.array_equal(audio_beats[1], np.cumsum(audio_differences[:-1]))
    assert np.array_equal(visual_beats[1], np.cumsum(visual_differences[:-1]))

    pb.progress(40)
    audio_diff_size = audio_differences.size
    audio_differences_sync = []
    visual_differences_sync = []

    # Loop through each audio and visual beat difference index
    pb.progress(45)
    audio_index, visual_index = 0, 0
    audio_diff = audio_differences[audio_index]
    visual_diff = visual_differences[visual_index]

    pb.progress(50)
    while True:

        # Convert beat differences to time
        audio_time = audio_diff / sr
        visual_time = visual_diff / fps

        speed_change = visual_time / audio_time

        # If the visual beat difference is too short, we check the next index
        if speed_change < speed[0]:
            visual_index += 1
            if visual_index == visual_differences.shape[0]:
                break
            visual_diff = visual_differences[visual_index]

        # If the audio beat difference is too short, we check the next index
        elif speed[1] < speed_change:   
            audio_index += 1
            # Iterate continuously over the audio indexes until visual indexes reach the size of the visual differences array
            audio_diff += audio_differences[audio_index % audio_diff_size]

        else:
            audio_index += 1
            visual_index += 1
            audio_differences_sync.append(audio_diff)
            visual_differences_sync.append(visual_diff)
            if visual_index == visual_differences.shape[0]:
                break
            audio_diff = audio_differences[audio_index % audio_diff_size]
            visual_diff = visual_differences[visual_index]

    pb.progress(55)
    audio_beats_sync = np.cumsum(audio_differences_sync[:-1])
    pb.progress(60)
    visual_beats_sync = np.cumsum(visual_differences_sync[:-1])
       
    # RENDER AUDIOVISUAL BEATS --------------------------------------------------------------------------------------------------
    pb.progress(65)
    of, fex = os.path.splitext(self.filename)

    if target_name == None:
        target_name = of + '_warped.avi'
    else:
        # enforce avi
        target_name = os.path.splitext(target_name)[0] + '.avi'
    if not overwrite:
        target_name = generate_outfilename(target_name)

    pb.progress(70)
    new_length = audio_beats_sync[-1] + 1
    extended_file_name = f'{audio_file[:-4]}_{new_length}.wav'

    pb.progress(75)
    if not os.path.isfile(extended_file_name):
        data, sample_rate = librosa.load(audio_file, mono=True)
        old_length = data.shape[0]
        tail = new_length - old_length * (new_length // old_length)
        extended_data = np.hstack(tuple([data] * (new_length // old_length) + [data[:tail]]))
        sf.write(extended_file_name, extended_data, sample_rate)
        
    pb.progress(80)
    if os.path.isfile(target_name):
        os.remove(target_name)

    pb.progress(85)        
    temp_file_name = of + '_temp.avi'
    filename = of + '.avi'

    pb.progress(90)
    vidcap = cv2.VideoCapture(filename)
    ret, frame = vidcap.read()
    pb.progress(95)
    output_stream = cv2.VideoWriter(temp_file_name, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame.shape[1], frame.shape[0]))

    pb.progress(100)
    if ret == True:

        # Iterate through each output frame until the final beat is reached
        last_audio_beat, last_visual_beat = 0, 0
        input_frame_index = 0

        for audio_beat, visual_beat in zip(audio_beats_sync, visual_beats_sync):
            # Output time range
            audio_start_time = last_audio_beat / sr
            audio_end_time = audio_beat / sr
            # Input time range
            visual_start_time = last_visual_beat / fps
            visual_end_time = visual_beat / fps
            # Conversion multiplier
            multiplier = (visual_end_time - visual_start_time) / (audio_end_time - audio_start_time)

            # Iterate through every output frame in the current beat range
            output_start_index = int(np.ceil(audio_start_time * fps))
            output_end_index = int(np.floor(audio_end_time * fps))

            for output_index in range(output_start_index, output_end_index + 1):

                output_time = output_index / fps
                input_time = (output_time - audio_start_time) * multiplier + visual_start_time
                input_index = round(input_time * fps)

                while input_frame_index < input_index:
                    ret, frame = vidcap.read()
                    input_frame_index += 1
                output_stream.write(frame)

            last_audio_beat, last_visual_beat = audio_beat, visual_beat

    # Close visual stream
    pb.progress(105)
    output_stream.release()
    pb.progress(110)
    vidcap.release()

    audio_file = extended_file_name

    pb.progress(115)
    cmd = f'ffmpeg -i {temp_file_name} -i {audio_file} -c:v copy -c:a aac -strict experimental -t {visual_beats_sync[-1] / fps} {wrap_str(target_name)}'
    
    pb.progress(120)
    subprocess.check_call(cmd, shell=True) 
    pb.progress(125)   
    os.remove(temp_file_name)
    pb.progress(130)

    # save warped video as warping_audiovisual_beats for parent MgVideo
    # we have to do this here since we are not using mg_warping_audiovisual_beats (that would normally save the result itself)
    self.warp_audiovisual_beats = musicalgestures.MgVideo(target_name, color=self.color, returned_by_process=True)

    return self.warp_audiovisual_beats
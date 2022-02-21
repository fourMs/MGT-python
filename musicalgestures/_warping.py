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

def mg_warping_audiovisual_beats(self, audio_file, speed=(0.5,2), data=None, filtertype='Adaptative', thresh=0.05, kernel_size=5, target_name=None, overwrite=False):

    # COMPUTE DIRECTOGRAMS ------------------------------------------------------------------------------------------------------

    if data is None:
        directogram = mg_directograms(self, title=None, filtertype=filtertype, thresh=thresh, kernel_size=kernel_size, target_name=target_name, overwrite=overwrite)
        directograms = directogram.data['directogram']
        fps = directogram.data['FPS']

    else:
        directograms = data
        vidcap = cv2.VideoCapture(self.filename)
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))

    # COMPUTE VISUAL AND AUDIO BEATS --------------------------------------------------------------------------------------------

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
    video_beats = librosa.beat.beat_track(onset_envelope=impact_envelopes,sr=fps, hop_length=1.0, trim=False, units='samples')

    # WARP VISUAL AND AUDIO BEATS -----------------------------------------------------------------------------------------------

    audio_differences = beats_diff(audio_beats[1], signal)
    pb.progress(30)
    video_differences = beats_diff(video_beats[1], np.ndarray.flatten(directograms))
    pb.progress(35)

    # Asserting if the arrays have equal shape and elements
    assert np.array_equal(audio_beats[1], np.cumsum(audio_differences[:-1]))
    assert np.array_equal(video_beats[1], np.cumsum(video_differences[:-1]))

    pb.progress(40)
    audio_diff_size = audio_differences.size
    audio_differences_sync = []
    video_differences_sync = []

    # Loop through each audio and video beat difference index
    pb.progress(45)
    audio_index, video_index = 0, 0
    audio_diff = audio_differences[audio_index]
    video_diff = video_differences[video_index]

    pb.progress(50)
    while True:

        # Converting beat differences to time
        video_time = video_diff / fps
        audio_time = audio_diff / sr

        speed_change = video_time / audio_time

        # If the video beat difference is too short, we check the next index
        if speed_change < speed[0]:
            video_index += 1
            if video_index == video_differences.shape[0]:
                break
            video_diff = video_differences[video_index]

        # If the audio beat difference is too short, we check the next index
        elif speed[1] < speed_change:   
            audio_index += 1
            # Iterate continuously over the audio indexes until video indexes reach the size of the video differences array
            audio_diff += audio_differences[audio_index % audio_diff_size]

        else:
            audio_index += 1
            video_index += 1
            audio_differences_sync.append(audio_diff)
            video_differences_sync.append(video_diff)

            if video_index == video_differences.shape[0]:
                break
            audio_diff = audio_differences[audio_index % audio_diff_size]
            video_diff = video_differences[video_index]

    pb.progress(55)
    audio_beats_sync = np.cumsum(audio_differences_sync[:-1])
    pb.progress(60)
    video_beats_sync = np.cumsum(video_differences_sync[:-1])
       
    # CONVERT VIDEO AND AUDIO ---------------------------------------------------------------------------------------------------
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
        last_audio_beat, last_video_beat = 0, 0
        input_frame_index = 0

        for audio_beat, video_beat in zip(audio_beats_sync, video_beats_sync):
            # Output time range
            audio_start_time = last_audio_beat / sr
            audio_end_time = audio_beat / sr
            # Input time range
            video_start_time = last_video_beat / fps
            video_end_time = video_beat / fps
            # Conversion multiplier
            multiplier = (video_end_time - video_start_time) / (audio_end_time - audio_start_time)

            # Iterate through every output frame in the current beat range
            output_start_index = int(np.ceil(audio_start_time * fps))
            output_end_index = int(np.floor(audio_end_time * fps))

            for output_index in range(output_start_index, output_end_index + 1):

                output_time = output_index / fps
                input_time = (output_time - audio_start_time) * multiplier + video_start_time
                input_index = round(input_time * fps)

                while input_frame_index < input_index:
                    ret, frame = vidcap.read()
                    input_frame_index += 1
                output_stream.write(frame)

            last_audio_beat, last_video_beat = audio_beat, video_beat

    # Close video stream
    pb.progress(105)
    output_stream.release()
    pb.progress(110)
    vidcap.release()

    audio_file = extended_file_name

    pb.progress(115)
    cmd = f'ffmpeg -i {temp_file_name} -i {audio_file} -c:v copy -c:a aac -strict experimental -t {video_beats_sync[-1] / fps} {wrap_str(target_name)}'
    
    pb.progress(120)
    subprocess.check_call(cmd, shell=True) 
    pb.progress(125)   
    os.remove(temp_file_name)
    pb.progress(130)

    # save motion video as warping_audiovisual_beats for parent MgVideo
    # we have to do this here since we are not using mg_warping_audiovisual_beats (that would normally save the result itself)
    self.warping_audiovisual_beats = musicalgestures.MgVideo(target_name, color=self.color, returned_by_process=True)

    return self.warping_audiovisual_beats
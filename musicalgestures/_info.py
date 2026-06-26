import os, subprocess
import pandas as pd
from matplotlib import pyplot as plt

from musicalgestures._utils import convert_to_mp4, get_framecount


def mg_info(self, type=None, autoshow=True, overwrite=False):
    """
    Returns info about video/audio/format file using ffprobe.

    Args:
        type (str, optional): Type of information to retrieve. Possible choices are 'summary', 'audio', 'video', 'format' or 'frame'. Defaults to None (which gives info about video, audio and format).
            - 'summary': prints a human-readable table of key video properties (resolution, fps, frame count, duration, color mode, audio) and returns a dict.
            - 'audio' / 'video' / 'format': returns the matching ffprobe stream as a pandas DataFrame row.
            - 'frame': renders a bar chart of I/P/B frame sizes and returns a DataFrame.
            - None: returns a DataFrame with all ffprobe stream and format metadata.
        autoshow (bool, optional): Whether to show the I/P/B frames figure automatically. Defaults to True. NB: The type argument needs to be set to 'frame'.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        dict or pandas.DataFrame: dict when type='summary', DataFrame otherwise.
    """

    if type == 'summary':
        framecount = get_framecount(self.filename)

        h = int(self.length // 3600)
        m = int((self.length % 3600) // 60)
        s = self.length % 60
        duration_str = f"{h}:{m:02d}:{s:05.2f}" if h else f"{m}:{s:05.2f}"

        filesize = os.path.getsize(self.filename)
        if filesize >= 1_000_000:
            size_str = f"{filesize / 1_000_000:.1f} MB"
        elif filesize >= 1_000:
            size_str = f"{filesize / 1_000:.1f} KB"
        else:
            size_str = f"{filesize} B"

        # Query codec/profile details from ffprobe
        v = _probe_stream(self.filename, 'v')
        a = _probe_stream(self.filename, 'a')

        video_codec = v.get('codec_name')
        video_profile = v.get('profile')
        pix_fmt = v.get('pix_fmt')
        color_space = v.get('color_space')
        color_profile = ', '.join(x for x in (pix_fmt, color_space) if x and x != 'unknown') or None

        audio_codec = a.get('codec_name')
        audio_sr = a.get('sample_rate')
        audio_br = a.get('bit_rate')
        audio_sr_str = f"{int(audio_sr):,} Hz" if audio_sr and audio_sr.isdigit() else None
        audio_br_str = f"{int(audio_br) // 1000} kbps" if audio_br and audio_br.isdigit() else None

        info_dict = {
            'filename':       os.path.basename(self.filename),
            'width':          self.width,
            'height':         self.height,
            'fps':            self.fps,
            'frames':         framecount,
            'duration':       round(self.length, 3),
            'color':          self.color,
            'video_codec':    video_codec,
            'video_profile':  video_profile,
            'pixel_format':   pix_fmt,
            'color_space':    color_space,
            'has_audio':      bool(self.has_audio),
            'audio_codec':    audio_codec,
            'audio_sample_rate': int(audio_sr) if audio_sr and audio_sr.isdigit() else None,
            'audio_bit_rate': int(audio_br) if audio_br and audio_br.isdigit() else None,
            'filesize':       filesize,
        }

        col = 14
        print(f"{'File:':<{col}} {os.path.basename(self.filename)}")
        print(f"{'Resolution:':<{col}} {self.width} × {self.height} px")
        print(f"{'Frames:':<{col}} {framecount}  @  {self.fps:g} fps")
        print(f"{'Duration:':<{col}} {duration_str}  ({self.length:.3f} s)")
        print(f"{'Color:':<{col}} {'color' if self.color else 'grayscale'}")
        codec_str = video_codec or 'unknown'
        if video_profile:
            codec_str += f" ({video_profile})"
        print(f"{'Video codec:':<{col}} {codec_str}")
        if color_profile:
            print(f"{'Color profile:':<{col}} {color_profile}")
        if self.has_audio:
            audio_str = audio_codec or 'unknown'
            extras = ', '.join(x for x in (audio_sr_str, audio_br_str) if x)
            if extras:
                audio_str += f" ({extras})"
            print(f"{'Audio:':<{col}} {audio_str}")
        else:
            print(f"{'Audio:':<{col}} no")
        print(f"{'File size:':<{col}} {size_str}")

        return info_dict

    # Get streams and format information (https://ffmpeg.org/ffprobe.html)
    cmd = ["ffprobe", "-hide_banner", "-loglevel", "quiet", "-show_streams", "-show_format", self.filename]
    if type == 'frame':
        if self.fex != '.mp4':
            # Convert video file to mp4 
            self.filename = convert_to_mp4(self.of + self.fex, overwrite=overwrite)
            self.of, self.fex = os.path.splitext(self.filename)
        cmd = ["ffprobe", "-hide_banner", "-loglevel", "quiet", "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pkt_size, pict_type", self.filename]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    try:
        out, _ = process.communicate(timeout=10)
        splitted = out.split('\n')
    except subprocess.TimeoutExpired:
        process.kill()
    out, err = process.communicate()
    splitted = out.split('\n')

    frame = []
    
    # Retrieve information and export it in a dictionary
    if type == 'frame':
        current_frame = {}
        for line in [i for i in splitted if i not in ('[SIDE_DATA]', '[/SIDE_DATA]', '')]:
            if line == '[/FRAME]':
                frame.append(current_frame)
                current_frame = {}
            elif line != '[FRAME]':
                pair = line.split('=')
                current_frame[pair[0]] = pair[1]
            else:
                pass

        ipb_frames = {
                      'frame index': range(len(frame)),
                      'size (bytes)': [int(f['pkt_size']) for f in frame],
                      'type': [f['pict_type'] for f in frame]
                      }
        
        df = pd.DataFrame.from_dict(ipb_frames)

        if autoshow:
            fig, ax = plt.subplots(figsize=(12,4), dpi=300)
            fig.patch.set_facecolor('white') # make sure background is white
            fig.patch.set_alpha(1)

            for i, (label, series) in enumerate(df.groupby('type')):
                plot_frames(series, label, index=i)

            # Get handles and labels
            handles, labels = plt.gca().get_legend_handles_labels()
            order = [1,2,0] # specify order of items in legend       
            # Add legend to plot
            ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order]) 
            ax.set_xlabel('Frame index')
            ax.set_ylabel('Size (bytes)')
            fig.tight_layout()
        else:
            return df

    else:
        for i, info in enumerate(splitted):
            if info == "[STREAM]" or info == "[SIDE_DATA]" or info == "[FORMAT]":        
                frame.append(dict())
                i +=1
            elif info == "[/STREAM]" or info == "[/SIDE_DATA]" or info == "[/FORMAT]" or info == "":
                i +=1
            else:
                try:
                    key, value = splitted[i].split('=')
                    frame[-1][key] = value
                except ValueError:
                    key = splitted[i]
                    frame[-1][key] = ''

        if len(frame) > 3: 
            # Merge video stream with side data dictionary
            frame[0] = {**frame[0], **frame[1]}
            frame.pop(1)

        # Create a pandas dataframe
        df = pd.DataFrame.from_dict(frame)

        df.insert(0, 'codec_type', df.pop('codec_type')) # move codec type column
        df.pop('index') # remove index column
        df = df[df.codec_type.notna()] # remove rows with nan values in codec_type column

        if type is not None:
            return df[df.codec_type == type]
        else:
            return df


def _probe_stream(filename, stream_type):
    """
    Query ffprobe for the first stream of a given type and return its entries as a dict.

    Args:
        filename (str): Path to the media file.
        stream_type (str): 'v' for video or 'a' for audio.

    Returns:
        dict: key/value pairs from the ffprobe stream output (empty if no such stream).
    """
    cmd = ["ffprobe", "-hide_banner", "-loglevel", "quiet", "-select_streams",
           f"{stream_type}:0", "-show_entries",
           "stream=codec_name,profile,pix_fmt,color_space,sample_rate,bit_rate",
           "-of", "default=noprint_wrappers=1", filename]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        out, _ = process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        return {}
    except Exception:
        return {}

    result = {}
    for line in out.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            if value not in ('', 'N/A', 'unknown'):
                result[key] = value
    return result


def plot_frames(df, label, color_list=['#636EFA','#00CC96','#EF553B'], index=0):
    xs = df['frame index']
    ys = df['size (bytes)']
    # Plot the bar plot
    plt.bar(xs, ys, label=label + '-Frames', width=1, color=color_list[index])
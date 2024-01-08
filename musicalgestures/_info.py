import os, subprocess
import pandas as pd
from matplotlib import pyplot as plt

from musicalgestures._utils import convert_to_mp4


def mg_info(self, type=None, autoshow=True, overwrite=False):
    """
    Returns info about video/audio/format file using ffprobe.

    Args:
        type (str, optional): Type of information to retrieve. Possible choice are 'audio', 'video', 'format' or 'frame'. Defaults to None (which gives info about video, audio and format).
        autoshow (bool, optional): Whether to show the I/P/B frames figure automatically. Defaults to True. NB: The type argument needs to be set to 'frame'.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filename to avoid overwriting. Defaults to False.

    Returns:
        str: decoded ffprobe output (stdout) as a list containing three dictionaries for video, audio and format metadata.
    """

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


def plot_frames(df, label, color_list=['#636EFA','#00CC96','#EF553B'], index=0):
    xs = df['frame index']
    ys = df['size (bytes)']
    # Plot the bar plot
    plt.bar(xs, ys, label=label + '-Frames', width=1, color=color_list[index])
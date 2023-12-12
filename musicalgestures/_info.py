import subprocess
import pandas as pd
from matplotlib import pyplot as plt


def mg_info(self, type=None, plot=True):
    """
    Returns info about video/audio/format file using ffprobe.

    Args:
        type (str, optional): Type of information to retrieve. Possible choice are 'audio', 'video', 'format' or 'frame'. Defaults to None (which gives info about video, audio and format).
        plot (bool, optional): Whether to plot the I/P/B frames of the video file or not. The type argument needs to be set to 'frame'. Defaults to True.

    Returns:
        str: decoded ffprobe output (stdout) as a list containing three dictionaries for video, audio and format metadata.
    """

    # Get streams and format information (https://ffmpeg.org/ffprobe.html)
    cmd = ["ffprobe", "-hide_banner", "-loglevel", "quiet", "-show_streams", "-show_format", self.filename]
    if type == 'frame':
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

        if plot:
            fig, ax = plt.subplots(figsize=(12,4), dpi=300)
            for i, (label, series) in enumerate(df.groupby('type')):
                plot_frames(series, label, index=i)
            ax.legend(title='Frame')
            ax.set_xlabel('Frame index')
            ax.set_ylabel('Size (bytes)')
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

        # Rename codec type column
        df["codec_type"] = ['video', 'audio', 'format']
        column = df.pop('codec_type')
        df.insert(0, column.name, column)
        df.pop('index') # remove index column

        if type is not None:
            return df[df["codec_type"] == type]
        else:
            return df


def plot_frames(df, label, color_list=['#636EFA','#00CC96','#EF553B'], index=0):
    xs = df['frame index']
    ys = df['size (bytes)']
    # Plot the bar plot
    plt.bar(xs, ys, label=label, width=1, color=color_list[index])
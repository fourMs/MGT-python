import os
import cv2
import numpy as np
from musicalgestures._utils import MgImage, generate_outfilename, resolve_filename, ffmpeg_cmd, get_length

def mg_grid(self, height=300, rows=3, columns=3, padding=0, margin=0, target_name=None, overwrite=True, return_array=False):
    """
    Generates frame strip video preview using ffmpeg.

    Args:
        height (int, optional): Frame height, width is adjusted automatically to keep the correct aspect ratio. Defaults to 300.
        rows (int, optional): Number of rows of the grid. Defaults to 3.
        columns (int, optional): Number of columns of the grid. Defaults to 3.
        padding (int, optional): Padding size between the frames. Defaults to 0.
        margin (int, optional): Margin size for the grid. Defaults to 0.
        target_name ([type], optional): Target output name for the grid image. Defaults to None.
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to True.
        return_array (bool, optional): Whether to return an array of not. If set to False the function writes the grid image to disk. Defaults to False.

    Returns:
        MgImage: An MgImage object referring to the internal grid image.
    """

    of, fex = os.path.splitext(self.filename)
    target_name = resolve_filename(of, '_grid.png', target_name, overwrite)

    # Get the number of frames
    cap = cv2.VideoCapture(self.filename)
    nb_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    nth_frame = int(nb_frames / (rows*columns))

    # Define the grid specifications
    width = int((float(self.width) / self.height) * height)
    grid = rf"select=not(mod(n\,{nth_frame})),scale={width}:{height},tile={columns}x{rows}:padding={padding}:margin={margin}"

    # Declare the ffmpeg commands
    if return_array:
        cmd = ['ffmpeg', '-y', '-i', self.filename, '-frames', '1', '-q:v', '0', '-vf', grid]
        process = ffmpeg_cmd(cmd, get_length(self.filename), pb_prefix='Rendering video frame grid:', pipe='load')

        # Convert bytes to array and convert from BGR to RGB
        array = np.frombuffer(process.stdout, dtype=np.uint8).reshape([height*rows, int(width*columns), 3])[...,::-1] 

        return array
    else:
        cmd = ['ffmpeg', '-i', self.filename, '-y', '-frames', '1', '-q:v', '0', '-vf', grid, target_name]
        ffmpeg_cmd(cmd, get_length(self.filename), pb_prefix='Rendering video frame grid:')
        # Initialize the MgImage object
        img = MgImage(target_name)

        return img